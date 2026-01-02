from mcp.server.fastmcp import FastMCP
import pathlib
import argparse
import logging

from pysearch_mcp.search_index import SearchIndex

# Initialize FastMCP server
logger = logging.getLogger("py_search.mcp_server")
formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
mcp = FastMCP("venv-mcp")

INDEX = SearchIndex()


@mcp.tool()
def py_search(query: str, max_results: int = 10):
    """
    Search private python code and python documentation.
    Will perform a full text search over the indexed documents and return the most relevant results.

    Args:
        query (str): The search query string. Use space separated keywords of sentences. Do not use ()
        max_results (int, optional): Maximum number of results to return. Defaults to 10.

    Returns a list of {location, score, text} objects, for example:
    result = [{"location": "location1", "score": 0.75, "text": "some text"}, {"location": "location2", "score": 0.5, "text": "some other text"}]

    Iterate over all results to find the relevant information.
    """
    logger.debug(f"py_search called with query: {query}, max_results: {max_results}")
    return INDEX.search(query, max_results)


def init_logging(file_path: pathlib.Path, level=logging.DEBUG):  # pragma: no cover
    """
    Initialize logging configuration for the application.

    Sets up logging to both a file and the console with a specified logging level.
    The log file is cleared before writing new logs.

    Args:
        file_path (pathlib.Path): Path to the log file where logs will be written.
        level (int, optional): Logging level to set for the root logger.
            Defaults to logging.DEBUG.

    Returns:
        None

    Note:
        This function configures the root logger and adds two handlers:
        - FileHandler: Writes logs to the specified file with UTF-8 encoding
        - StreamHandler: Outputs logs to the console
        Both handlers use the module-level 'formatter' object.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    file_path.write_text("", encoding="utf-8")  # Clear existing log file
    file_handler = logging.FileHandler(file_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)


# direct usage entrypoint
def main():  # pragma: no cover
    """
    Entry point for the venv MCP (Model Context Protocol) server.
    Parses command-line arguments to configure and launch a search server that indexes
    Python virtual environments and search index files. The server allows querying
    Python packages and modules within specified virtual environments.
    Command-line Arguments:
        --venv-paths: List of root directories containing virtual environments to index.
            Default: ["./tests/venv"]
        --search-index-paths: List of paths to pre-built search index JSON files to load.
            Default: ["./tests/repo/search/search_index.json"]
        --venv-search-patterns: List of prefixes to filter which packages to index from
            site-packages. Only top-level packages starting with these prefixes are indexed.
            Default: ["my_*"]
        --store-venv-index: Flag to persist the generated venv index to disk.
        --update-venv-index: Flag to force regeneration of the venv index on disk.
        --log_file_path: Path where log files should be written.
            Default: "./py_search_mcp_server.log"
    The function initializes logging, logs the startup configuration, and invokes
    the main search MCP server with the parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Run venv mcp server")

    parser.add_argument(
        "--venv-paths",
        nargs="*",
        default=["./tests/venv"],
        help="Root directories of virtual environments to index",
    )
    parser.add_argument(
        "--search-index-paths",
        nargs="*",
        default=["./tests/repo/search/search_index.json"],
        help="Paths to search index JSON files to load on startup",
    )
    parser.add_argument(
        "--venv-search-patterns",
        nargs="*",
        default=["my_*"],
        help=(
            "List of prefixes. Only search folders within Lib/site-packages "
            "whose top-level name starts with one of these prefixes. "
            "Provide multiple values separated by space."
        ),
    )
    parser.add_argument(
        "--store-venv-index", action="store_true", help="Store venv index to disk"
    )
    parser.add_argument(
        "--update-venv-index",
        action="store_true",
        help="Force update venv index on disk",
    )
    parser.add_argument(
        "--log_file_path",
        type=pathlib.Path,
        default=pathlib.Path("./py_search_mcp_server.log"),
        help="Path to log file",
    )
    args = parser.parse_args()
    args.log_file_path = args.log_file_path.resolve()

    init_logging(args.log_file_path, level=logging.INFO)

    logger.info("Starting venv mcp server")
    logger.info(f"Venv paths: {args.venv_paths}")
    logger.info(f"Venv search patterns: {args.venv_search_patterns}")
    logger.info(f"Search index paths: {args.search_index_paths}")
    logger.info(f"Log file path: {args.log_file_path}")
    logger.info(f"Store venv index: {args.store_venv_index}")
    logger.info(f"Update venv index: {args.update_venv_index}")

    run_search_mcp(
        search_index_paths=[pathlib.Path(p) for p in args.search_index_paths],
        venv_paths=[pathlib.Path(p) for p in args.venv_paths],
        venv_search_patterns=args.venv_search_patterns,
        store_venv_index=args.store_venv_index,
        update_venv_index=args.update_venv_index,
    )


def run_search_mcp(
    search_index_paths: list[pathlib.Path] = [],
    venv_paths: list[pathlib.Path] = [],
    venv_search_patterns: list[str] = [],
    store_venv_index: bool = False,
    update_venv_index: bool = False,
):
    """
    Run the Model Context Protocol (MCP) search server with specified configuration.
    This function initializes the global INDEX with search parameters and starts the MCP server.
    It configures paths for search indices, virtual environments, and related settings before
    launching the server.
    Args:
        search_index_paths (list[pathlib.Path], optional): List of paths to existing search index
            directories. Defaults to an empty list.
        venv_paths (list[pathlib.Path], optional): List of paths to virtual environment directories
            to be indexed. Defaults to an empty list.
        venv_search_patterns (list[str], optional): List of glob patterns to filter files within
            virtual environments for indexing. Defaults to an empty list.
        store_venv_index (bool, optional): Whether to persist the virtual environment index to disk.
            Defaults to False.
        update_venv_index (bool, optional): Whether to update existing virtual environment indices.
            Defaults to False.
    Returns:
        None: This function runs the MCP server and doesn't return a value.
    Example:
        >>> run_search_mcp(
        ...     search_index_paths=[Path("/path/to/index")],
        ...     venv_paths=[Path("/path/to/venv")],
        ...     venv_search_patterns=["*.py"],
        ...     store_venv_index=True
        ... )
    """
    INDEX.search_index_paths = search_index_paths
    INDEX.venv_paths = venv_paths
    INDEX.venv_search_patterns = venv_search_patterns
    INDEX.store_venv_index = store_venv_index
    INDEX.update_venv_index = update_venv_index

    mcp.run()


if __name__ == "__main__":
    main()
