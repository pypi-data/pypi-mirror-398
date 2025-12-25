"""Tests for utility functions."""
import pytest
from pathlib import Path
from dffs.utils import get_git_root, get_dir_path, _format_exit_code


class TestGitHelpers:
    """Test cases for Git helper functions."""

    def test_get_git_root(self):
        """Test get_git_root returns a valid path."""
        root = get_git_root()
        assert root
        assert Path(root).exists()
        assert Path(root, '.git').exists()

    def test_get_git_root_cached(self):
        """Test get_git_root uses cache."""
        root1 = get_git_root()
        root2 = get_git_root()
        assert root1 is root2  # Same object due to @cache

    def test_get_dir_path(self):
        """Test get_dir_path returns relative path from git root."""
        dir_path = get_dir_path()
        assert isinstance(dir_path, str)
        # Should not start with / (it's relative)
        assert not dir_path.startswith('/')

    def test_get_dir_path_cached(self):
        """Test get_dir_path uses cache."""
        path1 = get_dir_path()
        path2 = get_dir_path()
        assert path1 is path2  # Same object due to @cache


class TestFormatExitCode:
    """Test cases for _format_exit_code helper."""

    def test_normal_exit_codes(self):
        """Test formatting of normal (non-signal) exit codes."""
        assert _format_exit_code(0) == "0"
        assert _format_exit_code(1) == "1"
        assert _format_exit_code(2) == "2"
        assert _format_exit_code(127) == "127"
        assert _format_exit_code(128) == "128"

    def test_negative_signal_codes(self):
        """Test Python subprocess style negative signal codes."""
        assert _format_exit_code(-1) == "SIGHUP"
        assert _format_exit_code(-2) == "SIGINT"
        assert _format_exit_code(-9) == "SIGKILL"
        assert _format_exit_code(-13) == "SIGPIPE"
        assert _format_exit_code(-15) == "SIGTERM"
        # Unknown signal
        assert _format_exit_code(-99) == "signal 99"

    def test_shell_convention_signal_codes(self):
        """Test shell convention 128+signal exit codes."""
        assert _format_exit_code(129) == "129 (SIGHUP)"
        assert _format_exit_code(130) == "130 (SIGINT)"
        assert _format_exit_code(137) == "137 (SIGKILL)"
        assert _format_exit_code(141) == "141 (SIGPIPE)"
        assert _format_exit_code(143) == "143 (SIGTERM)"
        # Unknown signal
        assert _format_exit_code(227) == "227 (signal 99)"
