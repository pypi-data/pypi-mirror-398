import pathlib
import unittest
from unittest.mock import mock_open, MagicMock
import json

from pysearch_mcp.search_index import SearchIndex


class TestSearchIndex(unittest.TestCase):
    def test_read_index(self):
        index_path = pathlib.Path(__file__).parent / "repo/search/search_index.json"

        docs = SearchIndex().read_index(index_path)

        self.assertEqual(len(docs), 17)
        self.assertEqual(
            docs[0]["location"], index_path.parent.parent.joinpath("myfile").as_posix()
        )

    def test_create_index(self):
        test_venv_path = pathlib.Path(__file__).parent / "venv"
        search_patterns = ["my_*"]

        docs = SearchIndex().create_index(test_venv_path, search_patterns)

        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["title"], "some_src.py")

    def test_search(self):
        index = SearchIndex()
        index.venv_paths = [pathlib.Path(__file__).parent / "venv"]
        index.venv_search_patterns = ["my_*"]
        index.search_index_paths = [
            pathlib.Path(__file__).parent / "repo/search/search_index.json"
        ]

        results = index.search("bli")

        self.assertEqual(results[0]["text"], "blabla bli")
        self.assertEqual(results[1]["text"], 'print(" bli ")')

    def test_store_index(self):
        index = SearchIndex()
        docs = [
            {"location": "test.py", "title": "test", "text": "test content"},
            {"location": "test2.py", "title": "test2", "text": "test content 2"},
        ]

        mock_file = mock_open()
        mock_path = MagicMock(spec=pathlib.Path)
        mock_path.parent.mkdir = MagicMock()
        mock_path.open = mock_file

        index.store_index(mock_path, docs)

        # Verify parent directory was created
        mock_path.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)

        # Verify file was opened and written
        mock_file.assert_called_once_with("w", encoding="utf-8")
        handle = mock_file()
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)
        data = json.loads(written_content)

        self.assertEqual(len(data["docs"]), 2)
        self.assertEqual(data["docs"][0]["location"], "test.py")
        self.assertEqual(data["docs"][1]["title"], "test2")

    def test_store_index_creates_parent_directories(self):
        index = SearchIndex()
        docs = [{"location": "test.py", "title": "test", "text": "content"}]

        mock_path = MagicMock(spec=pathlib.Path)
        mock_path.parent.mkdir = MagicMock()
        mock_path.open = mock_open()

        index.store_index(mock_path, docs)

        # Verify parent.mkdir was called with correct arguments
        mock_path.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
