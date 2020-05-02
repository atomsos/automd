"""

AutoMD


Using UFF as potential and Gromacs as Engine to run MD for isomer searching



"""


from .main import run, get_isomers, generate_gromacs_topfile


__version__ = '3.1.3'


def version():
    """
    version
    """
    return __version__
