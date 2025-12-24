# search-bs

Index and search Bikeshed (.bs) source documents from URLs with efficient change detection.

## Features

- **Efficient change detection**: Only re-indexes when content actually changes
  - Uses HTTP conditional requests (ETag, Last-Modified)
  - Falls back to SHA256 content hashing
- **Full-text search**: Powered by SQLite FTS5 with BM25 ranking
- **Context-aware search**: Show N lines around each match with `--around` flag
- **Exact line retrieval**: Pull specific line ranges for agent consumption
- **Batch indexing**: Index multiple documents from a config file with `--all`
- **Markdown context**: Tracks current heading for each search result
- **GitHub integration**: Automatically converts GitHub blob URLs to raw URLs
- **JSON output**: Machine-readable output for all commands

## Installation

```bash
pip install search-bikeshed
```

Or install from source:

```bash
git clone https://github.com/tarekziade/search-bikeshed
cd search-bs
pip install -e .
```

## Usage

### Index a document

```bash
# Index from a URL
search-bs index https://github.com/webmachinelearning/webnn/blob/main/index.bs --name webnn

# GitHub blob URLs are automatically converted to raw URLs
search-bs index https://raw.githubusercontent.com/w3c/webrtc-pc/main/webrtc.bs --name webrtc

# Index all documents from config file
search-bs index --all
```

### Batch indexing with config file

Create a config file at `~/.config/search-bs/sources.json`:

```json
[
  {
    "name": "webnn",
    "url": "https://github.com/webmachinelearning/webnn/blob/main/index.bs"
  },
  {
    "name": "webrtc",
    "url": "https://raw.githubusercontent.com/w3c/webrtc-pc/main/webrtc.bs"
  }
]
```

Then index all at once:

```bash
search-bs index --all
```

### Search indexed documents

```bash
# Basic search
search-bs search --name webnn "MLTensor"

# Phrase search
search-bs search --name webnn "graph builder"

# Search with context lines (show 3 lines around each match)
search-bs search --name webnn "MLContext" --around 3

# With JSON output
search-bs search --name webnn "MLContext" --json

# Show URLs in results
search-bs search --name webnn "operator" --show-url --max-results 10
```

### Get exact line ranges

Retrieve specific line ranges from indexed documents (useful for agents):

```bash
# Get 40 lines starting from line 1234
search-bs get --name webnn --line 1234 --count 40

# JSON output
search-bs get --name webnn --line 1234 --count 40 --json
```

### List indexed documents

```bash
# Human-readable list
search-bs docs

# JSON output
search-bs docs --json
```

## How it works

1. **Indexing**: Fetches .bs files from URLs and indexes them line-by-line with heading context
2. **Change detection**: Uses HTTP conditional requests and content hashing to skip unchanged documents
3. **Search**: Uses SQLite FTS5 full-text search with BM25 ranking for relevance

## Data storage

By default, the index is stored in `~/.cache/search-bs/search-bs.sqlite3`

You can override this location with the `BIKESEARCH_HOME` environment variable:

```bash
export BIKESEARCH_HOME=/custom/path
search-bs index ...
```

## Requirements

- Python 3.8 or later
- SQLite 3 with FTS5 support (included in Python 3.6+)
- No external dependencies (stdlib only)

## License

MIT
