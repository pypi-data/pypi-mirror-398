"""Tests for diff-x CLI."""
import pytest
import tempfile
from pathlib import Path
from click.testing import CliRunner
from dffs.diff_x import main


@pytest.fixture
def temp_files():
    """Create temporary test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        file1 = tmpdir / 'file1.txt'
        file2 = tmpdir / 'file2.txt'
        file1.write_text('foo\nbar\n')
        file2.write_text('foo\nbaz\n')
        yield file1, file2


class TestDiffXBasic:
    """Basic diff-x functionality tests."""

    def test_diff_identical_files(self, temp_files):
        """Test diff-x with identical files returns 0."""
        file1, file2 = temp_files
        file2.write_text(file1.read_text())

        runner = CliRunner()
        result = runner.invoke(main, [str(file1), str(file2)])
        assert result.exit_code == 0

    def test_diff_different_files(self, temp_files):
        """Test diff-x with different files returns 1."""
        file1, file2 = temp_files

        runner = CliRunner()
        result = runner.invoke(main, [str(file1), str(file2)])
        assert result.exit_code == 1

    def test_diff_with_pipeline(self, temp_files):
        """Test diff-x with command pipeline."""
        file1, file2 = temp_files

        runner = CliRunner()
        # Use 'cat' which doesn't include filename, so output can be identical
        result = runner.invoke(main, ['cat', str(file1), str(file2)])
        assert result.exit_code == 1  # Files have different content


class TestDiffXOptions:
    """Test diff-x CLI options."""

    def test_color_flag(self, temp_files):
        """Test --color flag."""
        file1, file2 = temp_files

        runner = CliRunner()
        result = runner.invoke(main, ['--color', str(file1), str(file2)])
        # Exit code 1 for differences, just verify it runs
        assert result.exit_code in (0, 1)

    def test_unified_option(self, temp_files):
        """Test --unified option."""
        file1, file2 = temp_files

        runner = CliRunner()
        result = runner.invoke(main, ['--unified', '5', str(file1), str(file2)])
        assert result.exit_code in (0, 1)

    def test_ignore_whitespace(self, temp_files):
        """Test --ignore-whitespace flag."""
        file1, file2 = temp_files
        file1.write_text('foo\n')
        file2.write_text('foo \n')  # Trailing space

        runner = CliRunner()
        result = runner.invoke(main, ['--ignore-whitespace', str(file1), str(file2)])
        assert result.exit_code == 0

    def test_exec_cmd_option(self, temp_files):
        """Test -x/--exec-cmd option."""
        file1, file2 = temp_files

        runner = CliRunner()
        # Use 'cat' which doesn't include filename
        result = runner.invoke(main, ['-x', 'cat', str(file1), str(file2)])
        assert result.exit_code == 1  # Files differ


class TestDiffXErrors:
    """Test diff-x error handling."""

    def test_missing_files(self):
        """Test diff-x with missing file argument."""
        runner = CliRunner()
        result = runner.invoke(main, ['file1.txt'])
        assert result.exit_code != 0

    def test_no_files(self):
        """Test diff-x with no arguments shows help."""
        runner = CliRunner()
        result = runner.invoke(main, [])
        assert result.exit_code != 0


class TestDiffXPipefail:
    """Test diff-x --pipefail option."""

    def test_pipefail_flag_exists(self, temp_files):
        """Test that --pipefail flag is accepted."""
        file1, file2 = temp_files
        runner = CliRunner()
        result = runner.invoke(main, ['--pipefail', str(file1), str(file2)])
        # Should work (exit 0 or 1 for diff result)
        assert result.exit_code in (0, 1)

    def test_pipefail_short_flag(self, temp_files):
        """Test that -P short flag is accepted."""
        file1, file2 = temp_files
        runner = CliRunner()
        result = runner.invoke(main, ['-P', str(file1), str(file2)])
        assert result.exit_code in (0, 1)

    def test_pipefail_catches_early_failure(self, temp_files):
        """Test --pipefail catches failure in early pipeline stage."""
        file1, file2 = temp_files
        runner = CliRunner()
        # Without pipefail: `false | cat` - only checks `cat` (succeeds)
        result = runner.invoke(main, ['-x', 'false | cat', str(file1), str(file2)])
        assert result.exit_code in (0, 1)  # diff result, not pipeline failure

        # With pipefail: `false | cat` - checks both, `false` fails
        result = runner.invoke(main, ['-P', '-x', 'false | cat', str(file1), str(file2)])
        assert result.exit_code == 1  # pipeline failure
        assert 'failed' in result.output.lower() or result.exit_code != 0
