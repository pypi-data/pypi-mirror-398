import pathlib
from unittest.mock import patch
import pytest
from pysearch_mcp.mcp import run_search_mcp, INDEX, mcp


class TestRunSearchMcp:
    """Tests for run_search_mcp function."""

    @patch.object(mcp, "run")
    def test_run_search_mcp_with_default_parameters(self, mock_mcp_run):
        """Test run_search_mcp with all default parameters."""
        run_search_mcp()

        assert INDEX.search_index_paths == []
        assert INDEX.venv_paths == []
        assert INDEX.venv_search_patterns == []
        assert INDEX.store_venv_index is False
        assert INDEX.update_venv_index is False
        mock_mcp_run.assert_called_once()

    @patch.object(mcp, "run")
    def test_run_search_mcp_with_search_index_paths(self, mock_mcp_run):
        """Test run_search_mcp with search index paths."""
        search_paths = [
            pathlib.Path("/path/to/index1"),
            pathlib.Path("/path/to/index2"),
        ]

        run_search_mcp(search_index_paths=search_paths)

        assert INDEX.search_index_paths == search_paths
        mock_mcp_run.assert_called_once()

    @patch.object(mcp, "run")
    def test_run_search_mcp_with_venv_paths(self, mock_mcp_run):
        """Test run_search_mcp with virtual environment paths."""
        venv_paths = [pathlib.Path("/path/to/venv1"), pathlib.Path("/path/to/venv2")]

        run_search_mcp(venv_paths=venv_paths)

        assert INDEX.venv_paths == venv_paths
        mock_mcp_run.assert_called_once()

    @patch.object(mcp, "run")
    def test_run_search_mcp_with_venv_search_patterns(self, mock_mcp_run):
        """Test run_search_mcp with search patterns."""
        patterns = ["*.py", "*.txt", "my_*"]

        run_search_mcp(venv_search_patterns=patterns)

        assert INDEX.venv_search_patterns == patterns
        mock_mcp_run.assert_called_once()

    @patch.object(mcp, "run")
    def test_run_search_mcp_with_store_venv_index_true(self, mock_mcp_run):
        """Test run_search_mcp with store_venv_index enabled."""
        run_search_mcp(store_venv_index=True)

        assert INDEX.store_venv_index is True
        mock_mcp_run.assert_called_once()

    @patch.object(mcp, "run")
    def test_run_search_mcp_with_update_venv_index_true(self, mock_mcp_run):
        """Test run_search_mcp with update_venv_index enabled."""
        run_search_mcp(update_venv_index=True)

        assert INDEX.update_venv_index is True
        mock_mcp_run.assert_called_once()

    @patch.object(mcp, "run")
    def test_run_search_mcp_with_all_parameters(self, mock_mcp_run):
        """Test run_search_mcp with all parameters set."""
        search_paths = [pathlib.Path("/path/to/index")]
        venv_paths = [pathlib.Path("/path/to/venv")]
        patterns = ["my_*"]

        run_search_mcp(
            search_index_paths=search_paths,
            venv_paths=venv_paths,
            venv_search_patterns=patterns,
            store_venv_index=True,
            update_venv_index=True,
        )

        assert INDEX.search_index_paths == search_paths
        assert INDEX.venv_paths == venv_paths
        assert INDEX.venv_search_patterns == patterns
        assert INDEX.store_venv_index is True
        assert INDEX.update_venv_index is True
        mock_mcp_run.assert_called_once()

    @patch.object(mcp, "run")
    def test_run_search_mcp_calls_mcp_run(self, mock_mcp_run):
        """Test that run_search_mcp calls mcp.run()."""
        run_search_mcp()

        mock_mcp_run.assert_called_once_with()

    @patch.object(mcp, "run", side_effect=Exception("Server error"))
    def test_run_search_mcp_propagates_exceptions(self, mock_mcp_run):
        """Test that exceptions from mcp.run() are propagated."""
        with pytest.raises(Exception, match="Server error"):
            run_search_mcp()
