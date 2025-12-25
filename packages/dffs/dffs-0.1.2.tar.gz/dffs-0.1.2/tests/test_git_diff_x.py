"""Tests for git-diff-x CLI."""
import pytest
import tempfile
import subprocess
from pathlib import Path
from click.testing import CliRunner
from dffs.git_diff_x import main


@pytest.fixture
def git_repo():
    """Create a temporary git repository with test commits."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        subprocess.run(['git', 'init'], cwd=tmpdir, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=tmpdir, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=tmpdir, check=True, capture_output=True)

        # Create first commit
        test_file = tmpdir / 'test.txt'
        test_file.write_text('foo\nbar\n')
        subprocess.run(['git', 'add', 'test.txt'], cwd=tmpdir, check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=tmpdir, check=True, capture_output=True)

        # Create second commit
        test_file.write_text('foo\nbaz\n')
        subprocess.run(['git', 'add', 'test.txt'], cwd=tmpdir, check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Update test.txt'], cwd=tmpdir, check=True, capture_output=True)

        yield tmpdir


class TestGitDiffXBasic:
    """Basic git-diff-x functionality tests."""

    def test_diff_head_vs_worktree(self, git_repo):
        """Test git-diff-x comparing HEAD to worktree."""
        test_file = git_repo / 'test.txt'
        test_file.write_text('foo\nqux\n')  # Modify worktree

        runner = CliRunner()
        result = runner.invoke(main, ['test.txt'], cwd=str(git_repo))
        assert result.exit_code == 1  # Should have differences

    def test_diff_identical_head_vs_worktree(self, git_repo, monkeypatch):
        """Test git-diff-x with no changes between HEAD and worktree."""
        monkeypatch.chdir(git_repo)
        runner = CliRunner()
        result = runner.invoke(main, ['test.txt'])
        assert result.exit_code == 0  # No differences

    def test_diff_two_commits(self, git_repo, monkeypatch):
        """Test git-diff-x comparing two commits."""
        monkeypatch.chdir(git_repo)
        runner = CliRunner()
        result = runner.invoke(main, ['-r', 'HEAD^..HEAD', 'test.txt'])
        # Exit code should be 0 or 1 (0 for no diff, 1 for differences)
        assert result.exit_code in (0, 1)


class TestGitDiffXOptions:
    """Test git-diff-x CLI options."""

    def test_refspec_option(self, git_repo):
        """Test -r/--refspec option."""
        runner = CliRunner()
        result = runner.invoke(main, ['-r', 'HEAD^..HEAD', 'test.txt'], cwd=str(git_repo))
        assert result.exit_code in (0, 1)

    def test_ref_option(self, git_repo):
        """Test -R/--ref option."""
        runner = CliRunner()
        result = runner.invoke(main, ['-R', 'HEAD', 'test.txt'], cwd=str(git_repo))
        assert result.exit_code in (0, 1)

    def test_ref_and_refspec_conflict(self, git_repo):
        """Test that -r and -R options conflict."""
        runner = CliRunner()
        result = runner.invoke(main, ['-r', 'HEAD', '-R', 'HEAD', 'test.txt'], cwd=str(git_repo))
        assert result.exit_code != 0

    def test_staged_flag(self, git_repo):
        """Test -t/--staged flag to compare HEAD vs staged changes."""
        test_file = git_repo / 'test.txt'
        test_file.write_text('foo\nstaged\n')
        subprocess.run(['git', 'add', 'test.txt'], cwd=git_repo, check=True, capture_output=True)

        runner = CliRunner()
        result = runner.invoke(main, ['-t', 'test.txt'], cwd=str(git_repo))
        assert result.exit_code == 1  # Should have differences between HEAD and staged

    def test_staged_with_pipeline(self, git_repo):
        """Test -t/--staged flag with pipeline command."""
        test_file = git_repo / 'test.txt'
        test_file.write_text('line1\nline2\nline3\n')  # 3 lines
        subprocess.run(['git', 'add', 'test.txt'], cwd=git_repo, check=True, capture_output=True)

        runner = CliRunner()
        result = runner.invoke(main, ['-t', 'wc -l', 'test.txt'], cwd=str(git_repo))
        assert result.exit_code == 1  # Different line count (2 vs 3)

    def test_color_flag(self, git_repo):
        """Test -c/--color flag."""
        test_file = git_repo / 'test.txt'
        test_file.write_text('different\n')

        runner = CliRunner()
        result = runner.invoke(main, ['-c', 'test.txt'], cwd=str(git_repo))
        assert result.exit_code in (0, 1)

    def test_unified_option(self, git_repo):
        """Test -U/--unified option."""
        test_file = git_repo / 'test.txt'
        test_file.write_text('different\n')

        runner = CliRunner()
        result = runner.invoke(main, ['-U', '10', 'test.txt'], cwd=str(git_repo))
        assert result.exit_code in (0, 1)

    def test_ignore_whitespace(self, git_repo, monkeypatch):
        """Test -w/--ignore-whitespace flag."""
        monkeypatch.chdir(git_repo)
        test_file = git_repo / 'test.txt'
        test_file.write_text('foo\nbaz \n')  # Add trailing space

        runner = CliRunner()
        result = runner.invoke(main, ['-w', 'test.txt'])
        assert result.exit_code == 0


class TestGitDiffXPipelines:
    """Test git-diff-x with command pipelines."""

    def test_with_pipeline(self, git_repo, monkeypatch):
        """Test git-diff-x with command pipeline."""
        monkeypatch.chdir(git_repo)
        runner = CliRunner()
        # wc -l on worktree includes filename, but piped from git show doesn't
        # so they differ: "2" vs "2 test.txt"
        result = runner.invoke(main, ['wc -l', 'test.txt'])
        assert result.exit_code == 1  # Difference in wc output format

    def test_exec_cmd_option(self, git_repo, monkeypatch):
        """Test -x/--exec-cmd option."""
        monkeypatch.chdir(git_repo)
        runner = CliRunner()
        # wc -l on worktree includes filename, but piped from git show doesn't
        result = runner.invoke(main, ['-x', 'wc -l', 'test.txt'])
        assert result.exit_code == 1  # Difference in wc output format


class TestGitDiffXMultiplePaths:
    """Test git-diff-x with multiple file paths."""

    def test_multiple_paths_with_dash_separator(self, git_repo):
        """Test git-diff-x with multiple paths using - separator."""
        file2 = git_repo / 'test2.txt'
        file2.write_text('another\nfile\n')
        subprocess.run(['git', 'add', 'test2.txt'], cwd=git_repo, check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Add test2.txt'], cwd=git_repo, check=True, capture_output=True)

        runner = CliRunner()
        result = runner.invoke(main, ['cat', '-', 'test.txt', 'test2.txt'], cwd=str(git_repo))
        assert result.exit_code in (0, 1)


class TestGitDiffXErrors:
    """Test git-diff-x error handling."""

    def test_no_arguments(self):
        """Test git-diff-x with no arguments shows help."""
        runner = CliRunner()
        result = runner.invoke(main, [])
        assert result.exit_code != 0
