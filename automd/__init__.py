"""

AutoMD


Using UFF as potential and Gromacs as Engine to run MD for isomer searching



"""


from .main import run, get_isomers, generate_gromacs_topfile_itpfile


__version__ = '3.2.2'


def version():
    """
    version
    """
    return __version__
