from click import option, argument

pipefail_opt = option('-P', '--pipefail', is_flag=True, help="Check all pipeline commands for errors (like bash's `set -o pipefail`); default only checks last command")
shell_exec_opt = option('-s', '--shell-executable', help=f'Shell to use for executing commands; defaults to $SHELL')
no_shell_opt = option('-S', '--no-shell', is_flag=True, help="Don't pass `shell=True` to Python `subprocess`es")
verbose_opt = option('-v', '--verbose', is_flag=True, help="Log intermediate commands to stderr")
exec_cmd_opt = option('-x', '--exec-cmd', 'exec_cmds', multiple=True, help='Command(s) to execute before invoking `comm`; alternate syntax to passing commands as positional arguments')
args = argument('args', metavar='[exec_cmd...] <path1> <path2>', nargs=-1)
