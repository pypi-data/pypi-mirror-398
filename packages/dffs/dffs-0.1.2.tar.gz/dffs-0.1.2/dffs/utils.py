from __future__ import annotations

from functools import cache
from os import environ as env, getcwd
from os.path import relpath
from subprocess import Popen, PIPE
from sys import stdout

from utz import err, named_pipes, pipeline, process


@cache
def get_git_root() -> str:
    return process.line('git', 'rev-parse', '--show-toplevel', log=False)


@cache
def get_dir_path() -> str:
    return relpath(getcwd(), get_git_root())


def _format_exit_code(returncode: int) -> str:
    """Format an exit code with signal explanation if applicable.

    Python subprocess uses negative values for signals (e.g., -13 for SIGPIPE).
    Shell convention uses 128+signal (e.g., 141 for SIGPIPE).
    """
    sig_names = {
        1: "SIGHUP",
        2: "SIGINT",
        9: "SIGKILL",
        13: "SIGPIPE",
        15: "SIGTERM",
    }
    if returncode < 0:
        # Python subprocess: negative value is -signal
        sig = -returncode
        sig_name = sig_names.get(sig, f"signal {sig}")
        return f"{sig_name}"
    elif returncode > 128:
        # Shell convention: 128 + signal
        sig = returncode - 128
        sig_name = sig_names.get(sig, f"signal {sig}")
        return f"{returncode} ({sig_name})"
    return str(returncode)


def join_pipelines(
    base_cmd: list[str],
    cmds1: list[str],
    cmds2: list[str],
    verbose: bool = False,
    executable: str | None = None,
    both: bool = False,
    pipefail: bool = False,
    **kwargs,
) -> int:
    """Run two sequences of piped commands, pass their outputs as inputs to a ``base_cmd``.

    Args:
        base_cmd: Top=level command that takes two positional args (named pipes with the outputs
            of the ``cmds1`` and ``cmds2`` pipelines).
        cmds1: First sequence of commands to pipe together
        cmds2: Second sequence of commands to pipe together
        verbose: Whether to print commands being executed
        executable: Shell to use for executing commands; defaults to $SHELL
        both: Merge stderr into stdout in pipeline commands (like shell `2>&1`)
        pipefail: If True, check all processes for errors (like bash's `set -o pipefail`).
            If False (default), only check the last process of each pipeline.
        **kwargs: Additional arguments passed to subprocess.Popen

    Returns:
        Exit code: 0 if all processes succeeded, otherwise the first non-zero exit code

    Each command sequence will be piped together before being compared.
    For example, if cmds1 = ['cat foo.txt', 'sort'], the function will
    execute 'cat foo.txt | sort' before comparing with cmds2's output.

    Adapted from https://stackoverflow.com/a/28840955"""
    if executable is None:
        executable = env.get('SHELL')

    with named_pipes(n=2) as pipes:
        (pipe1, pipe2) = pipes
        join_cmd = [
            *base_cmd,
            pipe1,
            pipe2,
        ]
        # Capture stdout so we can suppress it if a pipeline fails
        proc = Popen(join_cmd, stdout=PIPE)

        # Track pipeline processes and their commands
        pipeline_groups = []  # List of (cmds, procs) tuples
        for pipe, cmds in ((pipe1, cmds1), (pipe2, cmds2)):
            if verbose:
                err(f"Running pipeline: {' | '.join(cmds)}")

            procs = pipeline(
                cmds,
                pipe,
                wait=False,
                executable=executable,
                both=both,
                **kwargs,
            )
            pipeline_groups.append((cmds, procs))

        all_pipeline_procs = [p for _, procs in pipeline_groups for p in procs]

        # Wait for pipeline processes first
        for p in all_pipeline_procs:
            p.wait()

        # Determine which (cmd, proc) pairs to check for errors
        if pipefail:
            # Check all processes (like bash's `set -o pipefail`)
            to_check = [
                (cmd, p)
                for cmds, procs in pipeline_groups
                for cmd, p in zip(cmds, procs)
            ]
        else:
            # Only check the last process of each pipeline (standard shell behavior)
            to_check = [
                (cmds[-1], procs[-1])
                for cmds, procs in pipeline_groups
                if procs
            ]

        pipeline_failed = False
        first_error_code = None
        for cmd, p in to_check:
            if p.returncode != 0:
                pipeline_failed = True
                if first_error_code is None:
                    first_error_code = p.returncode

                # Format the command for display
                cmd_str = cmd if isinstance(cmd, str) else ' '.join(cmd)
                exit_str = _format_exit_code(p.returncode)
                err(f"Pipeline command failed: `{cmd_str}` (exit {exit_str})")

                # Print stderr from failed process if available
                if p.stderr:
                    stderr_output = p.stderr.read()
                    if stderr_output:
                        if isinstance(stderr_output, bytes):
                            stderr_output = stderr_output.decode('utf-8', errors='replace')
                        err(stderr_output.rstrip())

        # Wait for base_cmd and capture its output
        proc.wait()
        base_stdout = proc.stdout.read() if proc.stdout else b''

        # If any pipeline failed, suppress base_cmd output and return error code
        if pipeline_failed:
            return first_error_code

        # Pipeline succeeded - print base_cmd output and return its exit code
        if base_stdout:
            if isinstance(base_stdout, bytes):
                base_stdout = base_stdout.decode('utf-8', errors='replace')
            stdout.write(base_stdout)
            stdout.flush()

        return proc.returncode


