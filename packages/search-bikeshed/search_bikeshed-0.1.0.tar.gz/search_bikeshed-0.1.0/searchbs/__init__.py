#!/usr/bin/env python3
"""
search-bs: index + search Bikeshed (.bs) source documents from URLs.

Key feature:
  - "index" only updates the local index if the URL content changed, using:
      * ETag / Last-Modified conditional requests when available
      * content hash fallback

Examples:

  ./search-bs.py index https://github.com/webmachinelearning/webnn/blob/main/index.bs --name webnn
  ./search-bs.py search --name webnn "MLTensor"
  ./search-bs.py search --name webnn "graph builder" --json
  ./search-bs.py docs
"""

import argparse
import dataclasses
import hashlib
import json
import os
import re
import sqlite3
import sys
import textwrap
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional


APP_DIR = Path(os.environ.get("BIKESEARCH_HOME", Path.home() / ".cache" / "search-bs"))
DB_PATH = APP_DIR / "search-bs.sqlite3"
CONFIG_DIR = Path.home() / ".config" / "search-bs"
SOURCES_CONFIG = CONFIG_DIR / "sources.json"

DEFAULT_MAX_RESULTS = 20


def die(msg: str, code: int = 2) -> None:
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(code)


def ensure_dirs() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_url(s: str) -> bool:
    try:
        u = urllib.parse.urlparse(s)
        return u.scheme in ("http", "https") and bool(u.netloc)
    except Exception:
        return False


def github_blob_to_raw(url: str) -> str:
    """
    Convert:
      https://github.com/<org>/<repo>/blob/<branch>/path/index.bs
    to:
      https://raw.githubusercontent.com/<org>/<repo>/<branch>/path/index.bs
    """
    u = urllib.parse.urlparse(url)
    if u.netloc != "github.com":
        return url
    parts = u.path.strip("/").split("/")
    if len(parts) >= 5 and parts[2] == "blob":
        org, repo, _, branch = parts[:4]
        rest = parts[4:]
        raw_path = "/".join([org, repo, branch] + rest)
        return f"https://raw.githubusercontent.com/{raw_path}"
    return url


def http_get(
    url: str,
    timeout_s: int = 30,
    etag: Optional[str] = None,
    last_modified: Optional[str] = None,
) -> tuple[int, dict, bytes]:
    """
    Returns: (status_code, headers_lower, body_bytes)

    Uses conditional headers if etag/last_modified are provided.
    """
    headers = {
        "User-Agent": "search-bs/0.2",
        "Accept": "text/plain,text/*;q=0.9,*/*;q=0.1",
    }
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified

    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            body = resp.read()
            # Normalize headers to lowercase keys
            hdrs = {k.lower(): v for k, v in dict(resp.headers).items()}
            return (resp.status, hdrs, body)
    except urllib.error.HTTPError as e:
        # HTTPError is also a response (e.g. 304)
        hdrs = {k.lower(): v for k, v in dict(e.headers).items()}
        body = e.read() if hasattr(e, "read") else b""
        return (e.code, hdrs, body)


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")


def iter_lines_with_context(text: str):
    """
    Yields (lineno_1_based, line_text, current_heading)
    best-effort "current heading" based on Markdown headings.
    """
    current_heading: Optional[str] = None
    for i, line in enumerate(text.splitlines(), start=1):
        m = _HEADING_RE.match(line)
        if m:
            current_heading = re.sub(r"\s+", " ", m.group(2)).strip()
        yield (i, line, current_heading)


def short_title_from_text(text: str) -> str:
    for line in text.splitlines()[:300]:
        if line.startswith("Title:"):
            return line.split("Title:", 1)[1].strip()[:200]
    for line in text.splitlines()[:300]:
        m = _HEADING_RE.match(line)
        if m:
            return m.group(2).strip()[:200]
    return "Untitled"


SCHEMA_SQL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS docs (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  url TEXT NOT NULL,
  title TEXT NOT NULL,
  indexed_at REAL NOT NULL,
  etag TEXT,
  last_modified TEXT,
  content_hash TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS lines_fts
USING fts5(
  doc_name,
  url,
  title,
  heading,
  lineno UNINDEXED,
  line,
  tokenize = 'unicode61'
);
"""


def connect_db() -> sqlite3.Connection:
    ensure_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.executescript(SCHEMA_SQL)
    return conn


def get_doc_meta(conn: sqlite3.Connection, name: str) -> Optional[dict]:
    cur = conn.execute(
        "SELECT url, title, etag, last_modified, content_hash, indexed_at FROM docs WHERE name = ?",
        (name,),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {
        "url": row[0],
        "title": row[1],
        "etag": row[2],
        "last_modified": row[3],
        "content_hash": row[4],
        "indexed_at": row[5],
    }


def clear_doc(conn: sqlite3.Connection, name: str) -> None:
    conn.execute("DELETE FROM docs WHERE name = ?", (name,))
    conn.execute("DELETE FROM lines_fts WHERE doc_name = ?", (name,))


def index_url_if_changed(conn: sqlite3.Connection, name: str, url_in: str) -> dict:
    if not is_url(url_in):
        die("This version only supports indexing from a URL to a .bs file.")

    url = github_blob_to_raw(url_in)

    old = get_doc_meta(conn, name)
    old_etag = old["etag"] if old else None
    old_lm = old["last_modified"] if old else None
    old_hash = old["content_hash"] if old else None
    old_url = old["url"] if old else None

    # If name exists but URL differs, treat as changed and reindex.
    url_changed = old_url is not None and old_url != url

    status, headers, body = http_get(url, etag=old_etag, last_modified=old_lm)

    # Not modified via conditional request
    if status == 304 and not url_changed:
        return {
            "name": name,
            "url": url,
            "updated": False,
            "reason": "not_modified_304",
            "title": old["title"] if old else "Untitled",
        }

    if status < 200 or status >= 300:
        die(f"HTTP {status} fetching {url}")

    new_hash = sha256_bytes(body)

    # Hash says unchanged
    if (old_hash is not None) and (new_hash == old_hash) and (not url_changed):
        # Even if headers changed, content didn't.
        return {
            "name": name,
            "url": url,
            "updated": False,
            "reason": "same_content_hash",
            "title": old["title"] if old else "Untitled",
        }

    text = body.decode("utf-8", errors="replace")
    title = short_title_from_text(text)
    etag = headers.get("etag")
    last_modified = headers.get("last-modified")

    # Rebuild index for this doc
    clear_doc(conn, name)
    conn.execute(
        "INSERT INTO docs(name, url, title, indexed_at, etag, last_modified, content_hash) VALUES (?,?,?,?,?,?,?)",
        (name, url, title, time.time(), etag, last_modified, new_hash),
    )

    rows = []
    for lineno, line, heading in iter_lines_with_context(text):
        norm_line = line.rstrip("\n")
        if len(norm_line) > 5000:
            norm_line = norm_line[:5000] + " …[truncated]"
        rows.append((name, url, title, heading or "", lineno, norm_line))

    conn.executemany(
        "INSERT INTO lines_fts(doc_name, url, title, heading, lineno, line) VALUES (?,?,?,?,?,?)",
        rows,
    )
    conn.commit()

    return {
        "name": name,
        "url": url,
        "updated": True,
        "reason": "content_changed",
        "title": title,
        "lines_indexed": len(rows),
        "etag": etag,
        "last_modified": last_modified,
        "content_hash": new_hash,
    }


@dataclasses.dataclass
class SearchHit:
    doc_name: str
    url: str
    title: str
    heading: str
    lineno: int
    line: str
    snippet: str
    rank: float
    context: list[tuple[int, str]] = dataclasses.field(default_factory=list)


def get_lines_by_range(
    conn: sqlite3.Connection, name: str, start_line: int, end_line: int
) -> list[tuple[int, str]]:
    """
    Get lines from a document by line number range.
    Returns list of (lineno, line_text) tuples.
    """
    sql = """
    SELECT lineno, line
    FROM lines_fts
    WHERE doc_name = ? AND lineno >= ? AND lineno <= ?
    ORDER BY lineno
    """
    cur = conn.execute(sql, (name, start_line, end_line))
    return [(int(row[0]), row[1]) for row in cur.fetchall()]


def search_doc(
    conn: sqlite3.Connection, name: str, query: str, max_results: int
) -> list[SearchHit]:
    sql = """
    SELECT
      doc_name, url, title, heading, lineno, line,
      snippet(lines_fts, 5, '[', ']', '…', 20) AS snip,
      bm25(lines_fts) AS rank
    FROM lines_fts
    WHERE doc_name = ? AND lines_fts MATCH ?
    ORDER BY rank
    LIMIT ?;
    """
    try:
        cur = conn.execute(sql, (name, query, max_results))
    except sqlite3.OperationalError:
        safe = '"' + query.replace('"', '""') + '"'
        cur = conn.execute(sql, (name, safe, max_results))

    hits: list[SearchHit] = []
    for row in cur.fetchall():
        hits.append(
            SearchHit(
                doc_name=row[0],
                url=row[1],
                title=row[2],
                heading=row[3],
                lineno=int(row[4]),
                line=row[5],
                snippet=row[6],
                rank=float(row[7]),
            )
        )
    return hits


def list_docs(conn: sqlite3.Connection) -> list[dict]:
    cur = conn.execute(
        "SELECT name, url, title, indexed_at, etag, last_modified FROM docs ORDER BY name"
    )
    out = []
    for row in cur.fetchall():
        out.append(
            {
                "name": row[0],
                "url": row[1],
                "title": row[2],
                "indexed_at": row[3],
                "etag": row[4],
                "last_modified": row[5],
            }
        )
    return out


def load_sources_config() -> list[dict]:
    """Load sources from config file."""
    if not SOURCES_CONFIG.exists():
        die(f"Config file not found: {SOURCES_CONFIG}\nCreate it with: [{{'name': 'webnn', 'url': 'https://...'}}]")

    try:
        with open(SOURCES_CONFIG, "r", encoding="utf-8") as f:
            sources = json.load(f)
        if not isinstance(sources, list):
            die(f"Config file must contain a JSON array of {{name, url}} objects")
        for src in sources:
            if not isinstance(src, dict) or "name" not in src or "url" not in src:
                die(f"Each source must have 'name' and 'url' fields: {src}")
        return sources
    except json.JSONDecodeError as e:
        die(f"Invalid JSON in config file {SOURCES_CONFIG}: {e}")


def cmd_index(args: argparse.Namespace) -> None:
    conn = connect_db()

    # Handle --all flag
    if args.index_all:
        sources = load_sources_config()
        results = []
        for src in sources:
            info = index_url_if_changed(conn, src["name"], src["url"])
            results.append(info)
            if not args.json:
                if info.get("updated"):
                    print(f"Updated index for '{info['name']}'")
                    print(f"  title: {info['title']}")
                    print(f"  url: {info['url']}")
                    print(f"  lines: {info.get('lines_indexed', 0)}")
                else:
                    print(f"No update needed for '{info['name']}' ({info.get('reason')})")

        if args.json:
            print(json.dumps({"results": results}, indent=2, ensure_ascii=False))
        return

    # Single document indexing
    if not args.url or not args.name:
        die("Either use --all or provide both URL and --name")

    info = index_url_if_changed(conn, args.name, args.url)
    if args.json:
        print(json.dumps(info, indent=2, ensure_ascii=False))
        return

    if info.get("updated"):
        print(f"Updated index for '{info['name']}'")
        print(f"  title: {info['title']}")
        print(f"  url: {info['url']}")
        print(f"  lines: {info.get('lines_indexed', 0)}")
        if info.get("etag"):
            print(f"  etag: {info['etag']}")
        if info.get("last_modified"):
            print(f"  last-modified: {info['last_modified']}")
    else:
        print(f"No update needed for '{info['name']}' ({info.get('reason')})")
        print(f"  url: {info['url']}")
        print(f"  title: {info.get('title', '')}")


def cmd_search(args: argparse.Namespace) -> None:
    conn = connect_db()
    hits = search_doc(conn, args.name, args.query, args.max_results)

    # Fetch context lines if --around is specified
    if args.around > 0:
        for h in hits:
            start = max(1, h.lineno - args.around)
            end = h.lineno + args.around
            context = get_lines_by_range(conn, args.name, start, end)
            h.context = context
    else:
        for h in hits:
            h.context = []

    if args.json:
        results = []
        for h in hits:
            result = {
                "doc": h.doc_name,
                "title": h.title,
                "url": h.url,
                "heading": h.heading,
                "lineno": h.lineno,
                "line": h.line,
                "snippet": h.snippet,
                "rank": h.rank,
            }
            if args.around > 0:
                result["context"] = [{"lineno": ln, "line": txt} for ln, txt in h.context]
            results.append(result)

        print(
            json.dumps(
                {
                    "name": args.name,
                    "query": args.query,
                    "count": len(hits),
                    "results": results,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if not hits:
        print(f"No matches in '{args.name}'.")
        return

    for idx, h in enumerate(hits, start=1):
        heading = f"## {h.heading}" if h.heading else "(no heading context)"
        print(f"\n[{idx}] {h.title}")
        print(f"    {heading}")
        print(f"    line {h.lineno}: {h.line}")
        print(f"    match: {h.snippet}")
        if args.show_url:
            print(f"    url: {h.url}")
        if args.around > 0 and h.context:
            print(f"    context ({args.around} lines around):")
            for ln, txt in h.context:
                marker = ">>>" if ln == h.lineno else "   "
                print(f"      {marker} {ln}: {txt}")


def cmd_docs(args: argparse.Namespace) -> None:
    conn = connect_db()
    docs = list_docs(conn)
    if args.json:
        print(
            json.dumps({"count": len(docs), "docs": docs}, indent=2, ensure_ascii=False)
        )
        return

    if not docs:
        print("No indexed documents yet. Run: search-bs index <url> --name <name>")
        return

    for d in docs:
        t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(d["indexed_at"]))
        print(f"- {d['name']}: {d['title']}  ({t})")
        print(f"  {d['url']}")
        if d.get("etag"):
            print(f"  etag: {d['etag']}")
        if d.get("last_modified"):
            print(f"  last-modified: {d['last_modified']}")


def cmd_get(args: argparse.Namespace) -> None:
    """Get exact line range from an indexed document."""
    conn = connect_db()

    # Verify document exists
    meta = get_doc_meta(conn, args.name)
    if not meta:
        die(f"Document '{args.name}' not found. Use 'search-bs docs' to list indexed documents.")

    start_line = args.line
    end_line = args.line + args.count - 1

    lines = get_lines_by_range(conn, args.name, start_line, end_line)

    if args.json:
        print(
            json.dumps(
                {
                    "name": args.name,
                    "title": meta["title"],
                    "url": meta["url"],
                    "start_line": start_line,
                    "count": args.count,
                    "lines": [{"lineno": ln, "line": txt} for ln, txt in lines],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if not lines:
        print(f"No lines found in range {start_line}-{end_line} for '{args.name}'")
        return

    print(f"Document: {meta['title']}")
    print(f"Lines {start_line}-{end_line}:\n")
    for ln, txt in lines:
        print(f"{ln}: {txt}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="search-bs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """\
            search-bs: index + search Bikeshed (.bs) source files from URLs, with change detection.

            Tip: GitHub 'blob' URLs are accepted; they will be converted to raw URLs automatically.
            """
        ),
    )
    p.add_argument("--json", action="store_true", help="machine-readable JSON output")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_index = sub.add_parser("index", help="fetch a .bs URL and index it if changed")
    p_index.add_argument("url", nargs="?", help="URL to a .bs file (GitHub blob URL accepted)")
    p_index.add_argument(
        "--name", help="document name to store in the index"
    )
    p_index.add_argument(
        "--all", dest="index_all", action="store_true",
        help="index all documents from config file (~/.config/search-bs/sources.json)"
    )
    p_index.set_defaults(func=cmd_index)

    p_search = sub.add_parser("search", help="search an indexed spec")
    p_search.add_argument(
        "--name", required=True, help="document name (previously indexed)"
    )
    p_search.add_argument("query", help="FTS query (supports quotes and operators)")
    p_search.add_argument("--max-results", type=int, default=DEFAULT_MAX_RESULTS)
    p_search.add_argument("--show-url", action="store_true", help="print URL per hit")
    p_search.add_argument(
        "--around", type=int, default=0,
        help="show N lines of context around each match"
    )
    p_search.set_defaults(func=cmd_search)

    p_docs = sub.add_parser("docs", help="list indexed documents")
    p_docs.set_defaults(func=cmd_docs)

    p_get = sub.add_parser("get", help="get exact line range from a document")
    p_get.add_argument("--name", required=True, help="document name")
    p_get.add_argument("--line", type=int, required=True, help="starting line number")
    p_get.add_argument("--count", type=int, default=40, help="number of lines to retrieve (default: 40)")
    p_get.set_defaults(func=cmd_get)

    return p


def main(argv: Optional[list[str]] = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
