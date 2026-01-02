# pysearch_mcp

This repo contains a mcp server that should improve the search of python code and examples.

For this, it creates a search index based on **lunr**, and a mcp server based on **fastmcp**.

To retrieve input, it can read from:
- existing lunr search indexes, e.g. from existing **mkdocs** documentation
- code of virtual environments (narrow the package search with search patterns)

## Usage

### Terminal

To call the mcp server, you can use:

```sh
# module call
uv pip install pysearch_mcp
python -m pysearch_mcp

# script call
uv pip install pysearch_mcp
pysearch_mcp

# uvx tool
uvx pysearch_mcp@0.1.0
```

### VS Code

Use one of the methods mentioned above with the given args in mcp.json of vscode.

```json
{
  "servers": {
      "pysearch_mcp": {
        "type": "stdio",
        "command": "uvx",
        "args": [
          " pysearch_mcp@0.1.0", // pin the version in production
          "--venv-paths", ".venv",  // list one or more venvs
          "--venv-search-patterns", "pysearch*", // limit to a list of patterns to avoid loading all packages to the index
          "--search-index-paths", "tests/repo/search/search_index.json" // add additional search indexes
        ],
      }
  },
  "inputs": []
}
```

In Agent mode, use:

```promt
#py_search <my_search_query>

Example:
With #pysearch

How do i use function xyz
```

