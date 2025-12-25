from ..ConexAPI import ConexAPI
from . import DebugParser
import logging


_logger = logging.getLogger(__name__)


def _execute_migrate(args, conex_api: ConexAPI):
    _logger.debug("_execute_migrate")

    conex_api.migrate(args.pattern_or_reference, args.src_remote, args.dst_remote)


def setup_command(subparsers, conex_api: ConexAPI):
    parser = subparsers.add_parser("migrate", help='''
        Copies recipes and binary packages from one remote to another by 
        first downloading and then uploading them. NOTE: The downloaded 
        recipes and binary packages are placed in your local cache and are 
        not removed after upload.''')
    parser.set_defaults(command_func=lambda args: _execute_migrate(args, conex_api))

    parser.add_argument("pattern_or_reference", help='''
        Pattern or package recipe reference, e.g., 'boost/*', 'MyPackage/1.2@user/channel' ''')

    parser.add_argument("src_remote", help='''Download from this remote''')
    parser.add_argument("dst_remote", help='''Upload to this remote''')

    DebugParser.setup(parser)
