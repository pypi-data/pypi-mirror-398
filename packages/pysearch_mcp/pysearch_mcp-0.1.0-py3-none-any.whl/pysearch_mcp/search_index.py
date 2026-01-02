import pathlib

from typing import List, Dict, Any
import threading
import json

import logging
from lunr import lunr, tokenizer

"""
Structure from mkdocs lunr index:
docs = [{"location":"xyz","title":"xyz","text":"xyz" }]
Each document is a dict containing location, title, text fields.
The documents are stored in a docs list.

For now, we ommit the configuration part of mkdocs lunr index, and just read the documents.

For storage, we follow the mkdocs lunr convention to store in search/search_index.json
"""

logger = logging.getLogger("py_search.search_index")


# set stop words to improve search quality of lunr.py by adding .() to the separator chars
tokenizer.SEPARATOR_CHARS = " \t\n\r\f\v\xa0-.()"


class SearchIndex:
    """A tiny search index using lunr by either reading an existing search index, or
    creating a new index and storing it in root."""

    def __init__(self):
        self.documents = []
        self.search_index_paths = []
        self.venv_paths = []
        self.venv_search_patterns = []
        self._lunr = None
        self._lock = threading.Lock()
        self.store_venv_index = False
        self.update_venv_index = False

    @property
    def lunr_search(self):
        self._lock.acquire()
        if self._lunr is None:
            self.build()
        self._lock.release()
        return self._lunr

    def build(self):
        logger.debug("Building search index...")
        for index_path in self.search_index_paths:
            docs = self.read_index(index_path)
            self.documents.extend(docs)

        for venv_path in self.venv_paths:
            docs = self.create_index(venv_path, self.venv_search_patterns)
            self.documents.extend(docs)

        logger.debug(f"Total documents in index: {len(self.documents)}")
        logger.debug("Initializing lunr index...")

        self._lunr = lunr(
            ref="location",
            fields=["title", "text"],
            documents=self.documents,
        )

    def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        logger.debug(f"Searching for query: {query} with max_results: {max_results}")
        results = self.lunr_search.search(query)
        output = []
        for res in results[:max_results]:
            loc = res["ref"]
            score = res["score"]
            # Find the document
            doc = next((d for d in self.documents if d["location"] == loc), None)
            if doc:
                output.append(
                    {
                        "location": loc,
                        "score": score,
                        "text": doc["text"],
                    }
                )
        logger.debug(f"Search results: {output}")
        return output

    def read_index(self, index_path: pathlib.Path) -> list:
        """Read an existing indexs document section and make the path"""
        logger.debug(f"Reading search index from: {index_path.as_posix()}")
        if not index_path.exists():
            logger.debug(f"Index path {index_path.as_posix()} does not exist.")
            return []
        with index_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        docs = data.get("docs", [])

        def replace_location(doc):
            """Assuming location is relative to search/search_index.json parent"""
            doc["location"] = index_path.parent.parent.joinpath(
                doc["location"]
            ).as_posix()
            return doc

        docs = [replace_location(doc) for doc in docs]
        logger.debug(f"Read {len(docs)} documents from index at {index_path}")
        return docs

    def create_index(self, venv_root: pathlib.Path, search_patterns: List[str]) -> None:
        """
        Create a new index from the given venv root and site prefixes.
        This assumes the venv contains its packages under lib/site-packages
        To focus only on the relevant packages, we add a list of search patterns to get folders in site-packages.
        """
        # For simplicity, we only index .py files under Lib/site-packages with given prefixes
        site_packages = venv_root / "lib" / "site-packages"

        search_index_path = venv_root / "search" / "search_index.json"

        if search_index_path.exists() and not self.update_venv_index:
            logger.debug(
                f"Venv search index found at {search_index_path.as_posix()}, reading existing index."
            )
            return self.read_index(search_index_path)

        files = []
        folders = []

        logger.debug(
            f"Creating search index from venv at: {venv_root} with patterns: {search_patterns}"
        )

        import fnmatch

        # Allow wildcard patterns for folder matching
        if site_packages.exists() and site_packages.is_dir():
            for folder in site_packages.iterdir():
                if folder.is_dir():
                    for pattern in search_patterns:
                        # Try fnmatch (wildcards), then regex
                        if fnmatch.fnmatch(folder.name, pattern):
                            folders.append(folder)
                            break

        for folder in folders:
            for file_path in folder.rglob("*.py"):
                files.append(file_path)

        docs = []
        for file_path in files:
            try:
                content = file_path.read_text(encoding="utf-8")
                docs.append(
                    {
                        "location": file_path.as_posix(),
                        "title": file_path.name,
                        "text": content,
                    }
                )
            except Exception:
                continue  # Skip files that can't be read

        logger.debug(f"Created {len(docs)} documents from venv at {venv_root}")

        if self.store_venv_index:
            self.store_index(search_index_path, docs)

        return docs

    def store_index(self, index_path: pathlib.Path, docs: list) -> None:
        """Store the current index to the given path."""
        logger.debug(f"Storing search index to: {index_path.as_posix()}")
        data = {
            "docs": docs,
        }
        index_path.parent.mkdir(parents=True, exist_ok=True)
        with index_path.open("w", encoding="utf-8") as f:
            json.dump(data, f)
        logger.debug(f"Stored {len(docs)} documents to index at {index_path}")
