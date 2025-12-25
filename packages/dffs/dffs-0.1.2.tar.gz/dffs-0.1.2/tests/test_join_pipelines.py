"""Tests for join_pipelines function."""
import pytest
from dffs.utils import join_pipelines


class TestJoinPipelinesSuccess:
    """Test cases for successful pipeline execution."""

    def test_identical_output(self):
        """Test join_pipelines returns 0 when both pipelines produce identical output."""
        returncode = join_pipelines(
            base_cmd=['diff'],
            cmds1=['echo foo'],
            cmds2=['echo foo'],
            shell=True,
        )
        assert returncode == 0

    def test_multi_stage_pipeline(self):
        """Test join_pipelines with multi-stage pipelines that produce identical output."""
        returncode = join_pipelines(
            base_cmd=['diff'],
            cmds1=['echo "foo\nbar"', 'sort'],
            cmds2=['echo "bar\nfoo"', 'sort'],
            shell=True,
        )
        assert returncode == 0


class TestJoinPipelinesDifferences:
    """Test cases for pipelines with differences."""

    def test_diff_found(self):
        """Test join_pipelines returns 1 when diff finds differences."""
        returncode = join_pipelines(
            base_cmd=['diff'],
            cmds1=['echo foo'],
            cmds2=['echo bar'],
            shell=True,
        )
        assert returncode == 1


class TestJoinPipelinesErrors:
    """Test cases for error handling."""

    def test_cmd1_fails(self):
        """Test join_pipelines returns non-zero when first pipeline command fails."""
        returncode = join_pipelines(
            base_cmd=['diff'],
            cmds1=['false'],
            cmds2=['echo bar'],
            shell=True,
        )
        assert returncode != 0

    def test_cmd2_fails(self):
        """Test join_pipelines returns non-zero when second pipeline command fails."""
        returncode = join_pipelines(
            base_cmd=['diff'],
            cmds1=['echo foo'],
            cmds2=['false'],
            shell=True,
        )
        assert returncode != 0

    def test_both_cmds_fail(self):
        """Test join_pipelines returns non-zero when both pipeline commands fail."""
        returncode = join_pipelines(
            base_cmd=['diff'],
            cmds1=['false'],
            cmds2=['false'],
            shell=True,
        )
        assert returncode != 0

    def test_pipeline_error_nonexistent_file(self):
        """Test join_pipelines propagates errors from pipeline commands."""
        returncode = join_pipelines(
            base_cmd=['diff'],
            cmds1=['cat /nonexistent/file/that/does/not/exist'],
            cmds2=['echo bar'],
            shell=True,
        )
        assert returncode != 0

    def test_multi_stage_pipeline_with_error(self):
        """Test join_pipelines with multi-stage pipeline that fails."""
        returncode = join_pipelines(
            base_cmd=['diff'],
            cmds1=['echo "foo\nbar"', 'sort', 'false'],
            cmds2=['echo "bar\nfoo"', 'sort'],
            shell=True,
        )
        assert returncode != 0

    def test_stderr_from_failed_command(self):
        """Test that stderr from failed pipeline commands is properly handled."""
        # This test verifies that failed commands with stderr output
        # return the correct exit code. The stderr output is printed
        # directly to the terminal (bypassing pytest's capture).
        returncode = join_pipelines(
            base_cmd=['diff'],
            cmds1=['python -c "import sys; sys.stderr.write(\'Custom error message\\n\'); sys.exit(2)"'],
            cmds2=['echo bar'],
            shell=True,
        )
        assert returncode == 2


class TestJoinPipelinesStderr:
    """Test cases for stderr handling."""

    def test_both_true_merges_stderr_into_diff(self):
        """Test that both=True merges stderr into stdout for diffing."""
        returncode = join_pipelines(
            base_cmd=['diff'],
            cmds1=['sh -c "echo stdout1; echo stderr1 >&2"'],
            cmds2=['sh -c "echo stdout2; echo stderr2 >&2"'],
            shell=True,
            both=True,
        )
        # Should find differences (stderr is merged and differs)
        assert returncode == 1

    def test_both_false_separates_stderr(self):
        """Test that both=False (default) keeps stderr separate from stdout."""
        returncode = join_pipelines(
            base_cmd=['diff'],
            cmds1=['sh -c "echo same"'],
            cmds2=['sh -c "echo same; echo different >&2"'],
            shell=True,
            both=False,
        )
        # Should be identical (stderr not included in diff)
        assert returncode == 0

    def test_both_false_shows_stderr_on_error(self):
        """Test that stderr from failed commands is shown when both=False."""
        # Note: actual stderr output goes to terminal, not captured here
        returncode = join_pipelines(
            base_cmd=['diff'],
            cmds1=['sh -c "echo error message >&2; exit 2"'],
            cmds2=['echo bar'],
            shell=True,
            both=False,
        )
        assert returncode == 2


class TestJoinPipelinesShellModes:
    """Test cases for different shell modes."""

    def test_shell_false_identical_output(self):
        """Test join_pipelines with shell=False returns 0 for identical output."""
        returncode = join_pipelines(
            base_cmd=['diff'],
            cmds1=[['echo', 'foo']],
            cmds2=[['echo', 'foo']],
            shell=False,
        )
        assert returncode == 0

    def test_shell_false_diff_found(self):
        """Test join_pipelines with shell=False returns 1 when diff finds differences."""
        returncode = join_pipelines(
            base_cmd=['diff'],
            cmds1=[['echo', 'foo']],
            cmds2=[['echo', 'bar']],
            shell=False,
        )
        assert returncode == 1

    def test_shell_false_cmd_fails(self):
        """Test join_pipelines with shell=False propagates command failures."""
        returncode = join_pipelines(
            base_cmd=['diff'],
            cmds1=[['false']],
            cmds2=[['echo', 'bar']],
            shell=False,
        )
        assert returncode != 0

    def test_shell_false_multi_stage(self):
        """Test join_pipelines with shell=False and multi-stage pipeline."""
        returncode = join_pipelines(
            base_cmd=['diff'],
            cmds1=[['printf', 'foo\\nbar'], ['sort']],
            cmds2=[['printf', 'bar\\nfoo'], ['sort']],
            shell=False,
        )
        assert returncode == 0
