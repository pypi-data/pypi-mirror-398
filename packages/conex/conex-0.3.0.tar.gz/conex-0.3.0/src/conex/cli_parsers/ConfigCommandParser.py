from ..ConexAPI import ConexAPI
from . import DebugParser


def _print_config_items_and_values(conex_api: ConexAPI):
    _convex_config = conex_api.config.load()

    print(f"conex configuration:")
    for pair in _convex_config.items():
        print(f"    {pair[0]} = {pair[1]}")


def _setup_list_command(subparsers, conex_api: ConexAPI):
    parser = subparsers.add_parser("show", help="Show all the specified configuration items with their values")
    parser.set_defaults(command_func=lambda args: _print_config_items_and_values(conex_api))


def _setup_get_command(subparsers, conex_api: ConexAPI):
    parser = subparsers.add_parser("get", help="Get the value of a configuration item")

    parser.add_argument("item", help="item to print")
    parser.set_defaults(command_func=lambda args: conex_api.config.get(args.item))


def _set_config(input_: str, conex_api: ConexAPI):
    tokens = input_.split("=")
    item = tokens[0]
    value = tokens[1]

    if input_ != f"{item}={value}":
        raise ValueError()

    if value == "None":
        value = None

    conex_api.config.set(item, value)


def _setup_set_command(subparsers, conex_api: ConexAPI):
    parser = subparsers.add_parser("set", help="Set a value for a configuration item")

    parser.add_argument("item", help="'item=value' to set")
    parser.set_defaults(command_func=lambda args: _set_config(args.item, conex_api))


def _setup_remove_command(subparsers, conex_api: ConexAPI):
    parser = subparsers.add_parser("remove", help="Remove an existing config element")

    parser.add_argument("item", help="item to remove")
    parser.set_defaults(command_func=lambda args: conex_api.config.remove(args.item))


def setup_command(subparsers, conex_api: ConexAPI):
    parser = subparsers.add_parser("config", help='''Manages conex configuration.''')

    subparsers = parser.add_subparsers(title="subcommand", dest="subcommand")
    subparsers.required = True

    _setup_list_command(subparsers, conex_api)
    _setup_get_command(subparsers, conex_api)
    _setup_set_command(subparsers, conex_api)
    _setup_remove_command(subparsers, conex_api)

    DebugParser.setup(parser)
