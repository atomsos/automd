"""

automd run cli 


"""
import automd
from automd.default_config import default_mdrun_config
from automd import gromacs_utils


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
        parser.add_argument("gentype", type=str)
        parser.add_argument("input_file", type=str)
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
        if args.gentype == 'top':
            gromacs_utils.generate_gromacs_topfile(args.input_file)
        elif args.gentype == 'mdrun':
            gromacs_utils.generate_mdrun_file(**args.__dict__)
        else:
            raise NotImplementedError('only top mdrun is supported')
