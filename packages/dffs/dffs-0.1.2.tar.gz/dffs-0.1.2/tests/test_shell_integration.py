"""Tests for shell-integration command."""

from dffs.commands.shell_integration import shell_integration
from io import StringIO
import sys


def test_shell_integration_bash():
    """Test that shell-integration outputs bash aliases."""
    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = buffer = StringIO()

    try:
        shell_integration('bash')
        output = buffer.getvalue()
        lines = output.rstrip('\n').split('\n')

        expected = [
            '# dffs shell integration for bash/zsh',
            '# Install dffs: pipx install dffs',
            '# Add to your ~/.bashrc or ~/.zshrc:',
            '#   eval "$(dffs-shell-integration bash)"',
            '',
            '# Suffix conventions: c=color, n=no-color, w=ignore-whitespace',
            '#   r=ref (-R, compare to parent), s=refspec (-r), t=staged (--staged)',
            '',
            '# Core diff-x aliases (color auto-enabled in TTY)',
            "alias dx='diff-x'",
            "alias dxc='diff-x --color'",
            "alias dxn='diff-x --no-color'",
            "alias dxw='diff-x -w'",
            "alias dxwc='diff-x -w --color'",
            "alias dxwn='diff-x -w --no-color'",
            '',
            '# Core comm-x aliases',
            "alias cx='comm-x'",
            "alias cx1='comm-x -1'",
            "alias cx2='comm-x -2'",
            "alias cx3='comm-x -3'",
            "alias cx12='comm-x -12'",
            "alias cx13='comm-x -13'",
            "alias cx23='comm-x -23'",
            '',
            '# Core git-diff-x aliases (color auto-enabled in TTY)',
            "alias gdx='git diff-x'",
            "alias gdxc='git diff-x --color'",
            "alias gdxn='git diff-x --no-color'",
            "alias gdxw='git diff-x -w'",
            "alias gdxwc='git diff-x -w --color'",
            "alias gdxwn='git diff-x -w --no-color'",
            '',
            '# git-diff-x with ref (r = -R, compare commit to parent)',
            "alias gdxr='git diff-x -R'",
            "alias gdxrc='git diff-x -R --color'",
            "alias gdxcr='git diff-x --color -R'",
            "alias gdxrn='git diff-x -R --no-color'",
            "alias gdxrw='git diff-x -R -w'",
            "alias gdxrwc='git diff-x -R -w --color'",
            "alias gdxrwn='git diff-x -R -w --no-color'",
            '',
            '# git-diff-x with refspec (s = -r, explicit refspec)',
            "alias gdxs='git diff-x -r'",
            "alias gdxsc='git diff-x -r --color'",
            "alias gdxcs='git diff-x --color -r'",
            "alias gdxsn='git diff-x -r --no-color'",
            "alias gdxsw='git diff-x -r -w'",
            "alias gdxswc='git diff-x -r -w --color'",
            "alias gdxswn='git diff-x -r -w --no-color'",
            '',
            '# git-diff-x with staged (t = --staged, compare HEAD vs index)',
            "alias gdxt='git diff-x --staged'",
            "alias gdxtc='git diff-x --staged --color'",
            "alias gdxct='git diff-x --color --staged'",
            "alias gdxtn='git diff-x --staged --no-color'",
            "alias gdxtw='git diff-x --staged -w'",
            "alias gdxtwc='git diff-x --staged -w --color'",
            "alias gdxtwn='git diff-x --staged -w --no-color'",
        ]
        assert lines == expected
    finally:
        sys.stdout = old_stdout


def test_shell_integration_filter_diff_x():
    """Test filtering to only diff-x aliases."""
    old_stdout = sys.stdout
    sys.stdout = buffer = StringIO()

    try:
        shell_integration('bash', 'diff-x')
        output = buffer.getvalue()
        lines = output.rstrip('\n').split('\n')

        expected = [
            '# dffs shell integration for bash/zsh',
            '# Install dffs: pipx install dffs',
            '# Add to your ~/.bashrc or ~/.zshrc:',
            '#   eval "$(dffs-shell-integration bash)"',
            '',
            '# Suffix conventions: c=color, n=no-color, w=ignore-whitespace',
            '#   r=ref (-R, compare to parent), s=refspec (-r), t=staged (--staged)',
            '',
            '# Core diff-x aliases (color auto-enabled in TTY)',
            "alias dx='diff-x'",
            "alias dxc='diff-x --color'",
            "alias dxn='diff-x --no-color'",
            "alias dxw='diff-x -w'",
            "alias dxwc='diff-x -w --color'",
            "alias dxwn='diff-x -w --no-color'",
        ]
        assert lines == expected
    finally:
        sys.stdout = old_stdout


def test_shell_integration_filter_comm_x():
    """Test filtering to only comm-x aliases."""
    old_stdout = sys.stdout
    sys.stdout = buffer = StringIO()

    try:
        shell_integration('bash', 'comm-x')
        output = buffer.getvalue()
        lines = output.rstrip('\n').split('\n')

        expected = [
            '# dffs shell integration for bash/zsh',
            '# Install dffs: pipx install dffs',
            '# Add to your ~/.bashrc or ~/.zshrc:',
            '#   eval "$(dffs-shell-integration bash)"',
            '',
            '# Suffix conventions: c=color, n=no-color, w=ignore-whitespace',
            '#   r=ref (-R, compare to parent), s=refspec (-r), t=staged (--staged)',
            '',
            '# Core comm-x aliases',
            "alias cx='comm-x'",
            "alias cx1='comm-x -1'",
            "alias cx2='comm-x -2'",
            "alias cx3='comm-x -3'",
            "alias cx12='comm-x -12'",
            "alias cx13='comm-x -13'",
            "alias cx23='comm-x -23'",
        ]
        assert lines == expected
    finally:
        sys.stdout = old_stdout


def test_shell_integration_filter_git_diff_x():
    """Test filtering to only git-diff-x aliases."""
    old_stdout = sys.stdout
    sys.stdout = buffer = StringIO()

    try:
        shell_integration('bash', 'git-diff-x')
        output = buffer.getvalue()
        lines = output.rstrip('\n').split('\n')

        expected = [
            '# dffs shell integration for bash/zsh',
            '# Install dffs: pipx install dffs',
            '# Add to your ~/.bashrc or ~/.zshrc:',
            '#   eval "$(dffs-shell-integration bash)"',
            '',
            '# Suffix conventions: c=color, n=no-color, w=ignore-whitespace',
            '#   r=ref (-R, compare to parent), s=refspec (-r), t=staged (--staged)',
            '',
            '# Core git-diff-x aliases (color auto-enabled in TTY)',
            "alias gdx='git diff-x'",
            "alias gdxc='git diff-x --color'",
            "alias gdxn='git diff-x --no-color'",
            "alias gdxw='git diff-x -w'",
            "alias gdxwc='git diff-x -w --color'",
            "alias gdxwn='git diff-x -w --no-color'",
            '',
            '# git-diff-x with ref (r = -R, compare commit to parent)',
            "alias gdxr='git diff-x -R'",
            "alias gdxrc='git diff-x -R --color'",
            "alias gdxcr='git diff-x --color -R'",
            "alias gdxrn='git diff-x -R --no-color'",
            "alias gdxrw='git diff-x -R -w'",
            "alias gdxrwc='git diff-x -R -w --color'",
            "alias gdxrwn='git diff-x -R -w --no-color'",
            '',
            '# git-diff-x with refspec (s = -r, explicit refspec)',
            "alias gdxs='git diff-x -r'",
            "alias gdxsc='git diff-x -r --color'",
            "alias gdxcs='git diff-x --color -r'",
            "alias gdxsn='git diff-x -r --no-color'",
            "alias gdxsw='git diff-x -r -w'",
            "alias gdxswc='git diff-x -r -w --color'",
            "alias gdxswn='git diff-x -r -w --no-color'",
            '',
            '# git-diff-x with staged (t = --staged, compare HEAD vs index)',
            "alias gdxt='git diff-x --staged'",
            "alias gdxtc='git diff-x --staged --color'",
            "alias gdxct='git diff-x --color --staged'",
            "alias gdxtn='git diff-x --staged --no-color'",
            "alias gdxtw='git diff-x --staged -w'",
            "alias gdxtwc='git diff-x --staged -w --color'",
            "alias gdxtwn='git diff-x --staged -w --no-color'",
        ]
        assert lines == expected
    finally:
        sys.stdout = old_stdout


def test_shell_integration_auto_detect():
    """Test that shell-integration auto-detects shell from environment."""
    import os
    old_shell = os.environ.get('SHELL')
    os.environ['SHELL'] = '/bin/bash'

    old_stdout = sys.stdout
    sys.stdout = buffer = StringIO()

    try:
        shell_integration(None)
        output = buffer.getvalue()
        lines = output.rstrip('\n').split('\n')

        expected = [
            '# dffs shell integration for bash/zsh',
            '# Install dffs: pipx install dffs',
            '# Add to your ~/.bashrc or ~/.zshrc:',
            '#   eval "$(dffs-shell-integration bash)"',
            '',
            '# Suffix conventions: c=color, n=no-color, w=ignore-whitespace',
            '#   r=ref (-R, compare to parent), s=refspec (-r), t=staged (--staged)',
            '',
            '# Core diff-x aliases (color auto-enabled in TTY)',
            "alias dx='diff-x'",
            "alias dxc='diff-x --color'",
            "alias dxn='diff-x --no-color'",
            "alias dxw='diff-x -w'",
            "alias dxwc='diff-x -w --color'",
            "alias dxwn='diff-x -w --no-color'",
            '',
            '# Core comm-x aliases',
            "alias cx='comm-x'",
            "alias cx1='comm-x -1'",
            "alias cx2='comm-x -2'",
            "alias cx3='comm-x -3'",
            "alias cx12='comm-x -12'",
            "alias cx13='comm-x -13'",
            "alias cx23='comm-x -23'",
            '',
            '# Core git-diff-x aliases (color auto-enabled in TTY)',
            "alias gdx='git diff-x'",
            "alias gdxc='git diff-x --color'",
            "alias gdxn='git diff-x --no-color'",
            "alias gdxw='git diff-x -w'",
            "alias gdxwc='git diff-x -w --color'",
            "alias gdxwn='git diff-x -w --no-color'",
            '',
            '# git-diff-x with ref (r = -R, compare commit to parent)',
            "alias gdxr='git diff-x -R'",
            "alias gdxrc='git diff-x -R --color'",
            "alias gdxcr='git diff-x --color -R'",
            "alias gdxrn='git diff-x -R --no-color'",
            "alias gdxrw='git diff-x -R -w'",
            "alias gdxrwc='git diff-x -R -w --color'",
            "alias gdxrwn='git diff-x -R -w --no-color'",
            '',
            '# git-diff-x with refspec (s = -r, explicit refspec)',
            "alias gdxs='git diff-x -r'",
            "alias gdxsc='git diff-x -r --color'",
            "alias gdxcs='git diff-x --color -r'",
            "alias gdxsn='git diff-x -r --no-color'",
            "alias gdxsw='git diff-x -r -w'",
            "alias gdxswc='git diff-x -r -w --color'",
            "alias gdxswn='git diff-x -r -w --no-color'",
            '',
            '# git-diff-x with staged (t = --staged, compare HEAD vs index)',
            "alias gdxt='git diff-x --staged'",
            "alias gdxtc='git diff-x --staged --color'",
            "alias gdxct='git diff-x --color --staged'",
            "alias gdxtn='git diff-x --staged --no-color'",
            "alias gdxtw='git diff-x --staged -w'",
            "alias gdxtwc='git diff-x --staged -w --color'",
            "alias gdxtwn='git diff-x --staged -w --no-color'",
        ]
        assert lines == expected
    finally:
        sys.stdout = old_stdout
        if old_shell:
            os.environ['SHELL'] = old_shell
        else:
            os.environ.pop('SHELL', None)
