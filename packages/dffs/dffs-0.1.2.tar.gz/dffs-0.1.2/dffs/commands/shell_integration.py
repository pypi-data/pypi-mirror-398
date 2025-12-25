"""Shell integration command."""

from os import environ
from pathlib import Path

from click import Choice
from utz import err
from utz.cli import arg


def shell_integration(shell: str | None, cli: str | None = None) -> None:
    """Output shell aliases for dffs commands.

    Usage:
        # Bash/Zsh: Add to your ~/.bashrc or ~/.zshrc:
        eval "$(dffs-shell-integration bash)"

        # For specific CLI only:
        eval "$(dffs-shell-integration bash diff-x)"

        # Fish: Add to your ~/.config/fish/config.fish:
        dffs-shell-integration fish | source

        # Or save to a file and source it:
        dffs-shell-integration bash > ~/.dffs-aliases.sh
        echo 'source ~/.dffs-aliases.sh' >> ~/.bashrc
    """
    # Auto-detect shell if not specified
    if not shell:
        shell_env = environ.get('SHELL', '')
        if 'fish' in shell_env:
            shell = 'fish'
        elif 'zsh' in shell_env:
            shell = 'zsh'
        else:
            shell = 'bash'  # default

    # Get the shell directory (in the dffs package)
    shell_dir = Path(__file__).parent.parent / 'shell'
    shell_file = shell_dir / f'dffs.{shell if shell != "zsh" else "bash"}'

    if shell_file.exists():
        with open(shell_file, 'r') as f:
            content = f.read()

            # Filter by CLI if specified
            if cli:
                lines = content.split('\n')
                output_lines = []
                in_section = False

                # Section matching: prefixes that indicate a section belongs to cli
                section_prefixes = {
                    'diff-x': ['# Core diff-x aliases'],
                    'comm-x': ['# Core comm-x aliases'],
                    'git-diff-x': ['# Core git-diff-x aliases', '# git-diff-x with'],
                }
                prefixes = section_prefixes.get(cli)

                if not prefixes:
                    err(f"Error: Unknown CLI '{cli}'. Valid options: diff-x, comm-x, git-diff-x")
                    exit(1)

                def is_section_for_cli(line: str) -> bool:
                    return any(line.startswith(p) for p in prefixes)

                # Output header comments and section
                in_header = True
                for line in lines:
                    if line.startswith('# dffs shell integration') or \
                       line.startswith('# Install dffs') or \
                       line.startswith('# Add to your') or \
                       line.startswith('#   ') or \
                       line.startswith('# Suffix conventions'):
                        output_lines.append(line)
                    elif line.startswith('# ') and not line.startswith('#  '):
                        # Section header line
                        in_header = False
                        in_section = is_section_for_cli(line)
                        if in_section:
                            output_lines.append(line)
                    elif in_section and line.startswith('alias '):
                        output_lines.append(line)
                    elif line.strip() == '' and (in_header or in_section):
                        output_lines.append(line)

                # Remove trailing blank lines
                while output_lines and output_lines[-1] == '':
                    output_lines.pop()

                print('\n'.join(output_lines))
            else:
                # Output all aliases
                print(content)
    else:
        err(f"Error: Shell integration file not found: {shell_file}")
        exit(1)


def register(cli):
    """Register command with CLI."""
    cli.command(name='shell-integration')(
        arg('shell', type=Choice(['bash', 'zsh', 'fish']), required=False)(
            arg('cli', type=Choice(['diff-x', 'comm-x', 'git-diff-x']), required=False)(
                shell_integration
            )
        )
    )
