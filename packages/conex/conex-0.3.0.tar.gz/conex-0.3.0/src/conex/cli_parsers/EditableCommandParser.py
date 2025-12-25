from ..ConexAPI import ConexAPI
from . import DebugParser


def _setup_remove_command(subparsers, conex_api: ConexAPI):
    parser = subparsers.add_parser("remove", help="Disable editable mode for a package")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("path", nargs="?", help="Remove the package located at the path in the user workspace")
    group.add_argument("--all", action="store_true", help="Remove all editable packages")
    parser.set_defaults(command_func=lambda args: conex_api.editable.remove(args.path, args.all))


def _setup_add_command(subparsers, conex_api: ConexAPI):
    parser = subparsers.add_parser("add", help="Put a package in editable mode")
    parser.add_argument("path", help="Path to the package folder in the user workspace")
    parser.add_argument("-l", "--layout", default=None, help="Relative or absolute path to a file containing the layout")
    parser.set_defaults(command_func=lambda args: conex_api.editable.add(args.path, args.layout))


def setup_command(subparsers, conex_api: ConexAPI):
    parser = subparsers.add_parser("editable", help='''
        Manages editable packages (packages that reside in the user workspace, 
        but are consumed as if they were in the cache).''')

    subparsers = parser.add_subparsers(title="subcommand", dest="subcommand")
    subparsers.required = True

    _setup_add_command(subparsers, conex_api)
    _setup_remove_command(subparsers, conex_api)

    DebugParser.setup(parser)
