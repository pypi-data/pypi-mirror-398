from ..ConexAPI import ConexAPI
from . import DebugParser


def _execute_upload(args, conex_api: ConexAPI):
    conex_api.upload(args.path, args.lock, args.remote, args.all)


def setup_command(subparsers, conex_api: ConexAPI):
    parser = subparsers.add_parser("upload", help='''
        Uploads recipes and binary packages to a remote''')
    parser.set_defaults(command_func=lambda args: _execute_upload(args, conex_api))

    parser.add_argument("path", help='''
        Path to a folder containing a conanfile.py or conan.lock file (whichever is present). 
        If the folder has both files it will select the conanfile. Use --lock to force the
        selection of the conan.lock file.''')

    parser.add_argument("--lock", default=False, action='store_true', help="Only look for a lock file in the specified path")
    parser.add_argument("-r", "--remote", help="upload to this specific remote")
    parser.add_argument('--no-all', dest='all', default=True, action='store_false',  help="Upload both package recipe and packages")

    DebugParser.setup(parser)
