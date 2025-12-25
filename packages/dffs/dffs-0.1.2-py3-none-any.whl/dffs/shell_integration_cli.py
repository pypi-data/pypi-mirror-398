"""CLI entry point for shell-integration command."""

from dffs.commands.shell_integration import shell_integration

def main():
    """Main entry point for shell-integration command."""
    import sys
    # Get shell and cli arguments if provided
    shell = sys.argv[1] if len(sys.argv) > 1 else None
    cli = sys.argv[2] if len(sys.argv) > 2 else None
    shell_integration(shell, cli)

if __name__ == '__main__':
    main()
