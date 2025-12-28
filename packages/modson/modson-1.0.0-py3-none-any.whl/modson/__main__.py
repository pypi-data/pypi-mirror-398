import sys


def main():
    """
    Main entry point for the modson command-line tool.
    """
    from .runtime import run_main
    sys.exit(run_main())


if __name__ == '__main__':
    main()
