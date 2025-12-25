"""Tests for comm-x CLI."""
import pytest
import tempfile
from pathlib import Path
from click.testing import CliRunner
from dffs.comm_x import main


@pytest.fixture
def temp_files():
    """Create temporary test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        file1 = tmpdir / 'file1.txt'
        file2 = tmpdir / 'file2.txt'
        file1.write_text('a\nb\nc\n')
        file2.write_text('b\nc\nd\n')
        yield file1, file2


class TestCommXBasic:
    """Basic comm-x functionality tests."""

    def test_comm_default(self, temp_files):
        """Test comm-x with default options."""
        file1, file2 = temp_files

        runner = CliRunner()
        result = runner.invoke(main, [str(file1), str(file2)])
        assert result.exit_code == 0
        # Output should have 3 columns

    def test_comm_identical_files(self, temp_files):
        """Test comm-x with identical files."""
        file1, file2 = temp_files
        file2.write_text(file1.read_text())

        runner = CliRunner()
        result = runner.invoke(main, [str(file1), str(file2)])
        assert result.exit_code == 0


class TestCommXOptions:
    """Test comm-x CLI options."""

    def test_exclude_1(self, temp_files):
        """Test -1/--exclude-1 flag."""
        file1, file2 = temp_files

        runner = CliRunner()
        result = runner.invoke(main, ['-1', str(file1), str(file2)])
        assert result.exit_code == 0

    def test_exclude_2(self, temp_files):
        """Test -2/--exclude-2 flag."""
        file1, file2 = temp_files

        runner = CliRunner()
        result = runner.invoke(main, ['-2', str(file1), str(file2)])
        assert result.exit_code == 0

    def test_exclude_3(self, temp_files):
        """Test -3/--exclude-3 flag."""
        file1, file2 = temp_files

        runner = CliRunner()
        result = runner.invoke(main, ['-3', str(file1), str(file2)])
        assert result.exit_code == 0

    def test_all_excludes(self, temp_files):
        """Test all exclude flags together."""
        file1, file2 = temp_files

        runner = CliRunner()
        result = runner.invoke(main, ['-1', '-2', '-3', str(file1), str(file2)])
        assert result.exit_code == 0

    def test_case_insensitive(self, temp_files):
        """Test -i/--case-insensitive flag."""
        file1, file2 = temp_files
        file1.write_text('FOO\n')
        file2.write_text('foo\n')

        runner = CliRunner()
        result = runner.invoke(main, ['-i', str(file1), str(file2)])
        assert result.exit_code == 0

    def test_exec_cmd_option(self, temp_files):
        """Test -x/--exec-cmd option."""
        file1, file2 = temp_files

        runner = CliRunner()
        result = runner.invoke(main, ['-x', 'sort', str(file1), str(file2)])
        assert result.exit_code == 0


class TestCommXPipelines:
    """Test comm-x with command pipelines."""

    def test_comm_with_pipeline(self, temp_files):
        """Test comm-x with command pipeline."""
        file1, file2 = temp_files

        runner = CliRunner()
        result = runner.invoke(main, ['sort', str(file1), str(file2)])
        assert result.exit_code == 0

    def test_comm_multi_stage_pipeline(self, temp_files):
        """Test comm-x with multi-stage pipeline."""
        file1, file2 = temp_files

        runner = CliRunner()
        result = runner.invoke(main, ['cat', 'sort', str(file1), str(file2)])
        assert result.exit_code == 0


class TestCommXErrors:
    """Test comm-x error handling."""

    def test_missing_files(self):
        """Test comm-x with missing file argument."""
        runner = CliRunner()
        result = runner.invoke(main, ['file1.txt'])
        assert result.exit_code != 0

    def test_no_files(self):
        """Test comm-x with no arguments shows help."""
        runner = CliRunner()
        result = runner.invoke(main, [])
        assert result.exit_code != 0
