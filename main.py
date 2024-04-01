import argparse
from xia_framework import Application


def main():
    # Top level parser
    parser = argparse.ArgumentParser(description='Application tools')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Create the parser for the "prepare" command
    parser_create = subparsers.add_parser('init-module', help='Initialization of a new module')
    parser_create.add_argument('-n', '--module_name', type=str, help='Create files relates to module')

    # Parse the arguments
    args = parser.parse_args()

    # Handle different commands
    application = Application()
    if args.command == 'init-module':
        application.prepare()
        application.create(args.module_name)
    else:
        # If no command is provided, show help
        parser.print_help()


if __name__ == "__main__":
    main()
