from __future__ import annotations

import shlex
import sys
from shlex import quote

from click import option, argument, command
from utz import process, err

from dffs.cli import shell_exec_opt, no_shell_opt, pipefail_opt, verbose_opt, exec_cmd_opt
from dffs.diff_x import color_opt, unified_opt, ignore_whitespace_opt
from dffs.utils import join_pipelines


@command('git-diff-x', short_help='Diff a Git-tracked file at two commits (or one commit vs. current worktree), optionally passing both through another command first', no_args_is_help=True)
@color_opt
@option('-r', '--refspec', help='<commit 1>..<commit 2> (compare two commits) or <commit> (compare <commit> to the worktree)')
@option('-R', '--ref', help="Diff a specific commit; alias for `-r <ref>^..<ref>`")
@option('-t', '--staged', is_flag=True, help='Compare HEAD vs. staged changes (index)')
@pipefail_opt
@shell_exec_opt
@no_shell_opt
@unified_opt
@verbose_opt
@ignore_whitespace_opt
@exec_cmd_opt
@argument('args', metavar='[exec_cmd...] [<path> | - [paths...]]', nargs=-1)
def main(
    color: bool,
    refspec: str | None,
    ref: str | None,
    staged: bool,
    pipefail: bool,
    shell_executable: str | None,
    no_shell: bool,
    unified: int | None,
    verbose: bool,
    ignore_whitespace: bool,
    exec_cmds: tuple[str, ...],
    args: tuple[str, ...],
):
    """Diff files at two commits, or one commit and the current worktree, after applying an optional command pipeline.

    Examples:

    # Compare the number of lines (`wc -l`) in file `foo` at the previous vs. current commit (`-r HEAD^..HEAD`):

    git diff-x -r HEAD^..HEAD wc -l foo

    # Colorized (`-c`) diff of `md5sum`s of `foo`, at HEAD (last committed value) vs. the current worktree content:

    git diff-x -c md5sum foo

    # Use `-` to separate pipeline commands from paths (when more than one path is to be diffed), e.g. this compares
    the largest 10 numbers in `file{1,2}` (HEAD vs. worktree):

    git diff-x 'sort -rn' head - file1 file2
    """
    if '-' in args:
        idx = args.index('-')
        cmd_args = args[:idx]
        paths = args[idx+1:]
    else:
        *cmd_args, path = args
        paths = [path]

    cmds = list(exec_cmds) + list(cmd_args)
    shell = not no_shell
    git_relpath_prefix = process.line('git', 'rev-parse', '--show-prefix', log=False)

    if sum([bool(refspec), bool(ref), staged]) > 1:
        raise ValueError("Specify at most one of -r/--refspec, -R/--ref, -C/--cached")
    if ref:
        refspec = f'{ref}^..{ref}'
    elif staged:
        refspec = 'HEAD'
    elif not refspec:
        refspec = 'HEAD'

    pcs = refspec.split('..', 1)
    if len(pcs) == 1:
        ref1 = pcs[0]
        ref2 = None
    elif len(pcs) == 2:
        ref1, ref2 = pcs
    else:
        raise ValueError(f"Invalid refspec: {refspec}")

    # Auto-detect color based on TTY if not explicitly set
    use_color = color if color is not None else sys.stdout.isatty()

    diff_args = [
        *(['-w'] if ignore_whitespace else []),
        *(['-U', str(unified)] if unified is not None else []),
        *(['--color=always'] if use_color else []),
    ]
    for path in paths:
        if len(paths) > 1:
            err(path)
        if cmds:
            git_path = f'{git_relpath_prefix}{path}'
            cmds1 = [ f'git show {ref1}:{quote(git_path)}', *cmds ]
            if ref2:
                cmds2 = [ f'git show {ref2}:{quote(git_path)}', *cmds ]
            else:
                cmd, *sub_cmds = cmds
                if staged:
                    # Use :0: to read from index (staged version)
                    cmds2 = [ f'git show :0:{quote(git_path)} | {cmd}', *sub_cmds ]
                else:
                    # Read from worktree
                    cmds2 = [ f'{cmd} {quote(path)}', *sub_cmds ]
            if not shell:
                cmds1 = [ shlex.split(c) for c in cmds1 ]
                cmds2 = [ shlex.split(c) for c in cmds2 ]

            returncode = join_pipelines(
                base_cmd=['diff', *diff_args],
                cmds1=cmds1,
                cmds2=cmds2,
                verbose=verbose,
                shell=not no_shell,
                executable=shell_executable,
                pipefail=pipefail,
            )
            raise SystemExit(returncode)
        else:
            git_diff_args = ['git', 'diff', *diff_args]
            if staged:
                git_diff_args.append('--cached')
            git_diff_args.extend([refspec, '--', path])
            process.run(git_diff_args)
