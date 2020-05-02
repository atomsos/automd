"""

automd run cli 


"""
import automd
from automd.default_config import default_mdrun_config


class CLICommand:
    """Print information about files or system.

    Without any filename(s), informations about the Chemio installation will be
    shown (Python version, library versions, ...).

    With filename(s), the file format will be determined for each file.
    """

    @staticmethod
    def add_arguments(parser):
        # parser.add_argument('filename', nargs='*',
        #                     help='Name of file to determine format for.')
        # parser.add_argument('-i', '--index' , default=-1,
        #                     help='Index to show')
        # parser.add_argument('-v', '--verbose', action='store_true',
        #                     help='Show more information about files.')
        # parser.add_argument('-k', '--key',
        #                     help='key to show')
        parser.add_argument("input_file", type=str)
        parser.add_argument("--mdrun_file", nargs='?', type=str, default=None)
        parser.add_argument("--topfile", nargs='?', type=str, default=None)
        parser.add_argument("--dest_dir", default='.', type=str)
        parser.add_argument("--max_core", default=4, type=int)
        parser.add_argument("--dry_run", action="store_true")
        parser.add_argument("--extract_forces", action="store_true")
        for key, value in default_mdrun_config.items():
            if isinstance(value, bool):
                parser.add_argument(
                    f"--{key}", default=value, action="store_true",
                    help=f"{key}, default: {value}")
            else:
                parser.add_argument(
                    f"--{key}", default=value, type=type(value),
                    help=f"{key}, default: {value}")

    @staticmethod
    def run(args):
        if args.debug:
            import json
            print(json.dumps(args.__dict__, indent=4))
        results = automd.run(**args.__dict__)
        if args.debug:
            import json_tricks
            print(json_tricks.dumps(results, allow_nan=True))
