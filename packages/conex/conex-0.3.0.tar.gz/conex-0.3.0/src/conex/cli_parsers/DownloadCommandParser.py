from ..ConexAPI import ConexAPI
from . import DebugParser
import logging


_logger = logging.getLogger(__name__)


def _execute_download(args, conex_api: ConexAPI):
    _logger.debug("_execute_download")

    conex_api.download(args.pattern_or_reference, args.remote)


def setup_command(subparsers, conex_api: ConexAPI):
    parser = subparsers.add_parser("download", help='''
        Downloads recipes and binary packages to the local cache, without using settings''')
    parser.set_defaults(command_func=lambda args: _execute_download(args, conex_api))

    parser.add_argument("pattern_or_reference", help='''
        Pattern or package recipe reference, e.g., 'boost/*', 'MyPackage/1.2@user/channel' ''')

    parser.add_argument("-r", "--remote", help="download from this specific remote")

    DebugParser.setup(parser)
