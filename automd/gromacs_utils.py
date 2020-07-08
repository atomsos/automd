"""

utils of gromacs

"""


import os
import re
import shutil
import subprocess
import configparser
import json
from distutils.version import LooseVersion
from io import StringIO
import warnings

import modlog
import numpy as np
from jinja2 import FileSystemLoader, Environment

import atomtools.unit
from .default_config import default_mdrun_config


os.environ['GMX_MAXBACKUP'] = '-1'

# set default files
MIN_GROMACS_VERSION = '5.0.0'
GRO_FORMAT_EXTRA_LINES = 3
MDRUN_FILE = 'mdrun.mdp'
INPUT_XYZ = 'input.xyz'
TOP_FILE = 'obgmx.top'
ITP_FILE = 'obgmx.itp'
GRO_FILE = 'input.gro'
OUTPUT_GRO = 'output.gro'
TRR_FILE = 'traj.trr'
EDR_FILE = 'topol.edr'
XTC_FILE = 'topol.xtc'
MDRUN_TEMP = 'mdrun_temp.mdp'

BASEDIR = os.path.dirname(os.path.realpath(__file__))
logger = modlog.getLogger(__name__)

# default_mdrun_config = {
#     'time': 10,
#     'time_unit': 'ps',
#     'dt': 0.5,
#     'dt_unit': 'fs',
#     'temperature': 600,
#     'temperature_unit': 'K',
#     'constant_pressure': False,
#     'pressure': 1,
#     'pressure_unit': 'bar',
#     'compressibility': 4.5e-5,
# }


def format_convert(inputfile, outputfile, outputformat, extra_data=None):
    extra_data = extra_data or {}
    try:
        import gaseio
        x = gaseio.read(inputfile, force_gase=True)
        x.update(extra_data)
        gaseio.write(outputfile, x, format=outputformat, force_gase=True)
    except Exception as e:
        import chemio
        chemio.convert(inputfile, write_filename=outputfile,
                       write_format=outputformat, data=extra_data)


def get_gromacs_config():
    exit_code, output = subprocess.getstatusoutput(
        r"""gmx --version  | grep :\ """)
    if exit_code != 0:
        raise OSError('There is no gromacs, Please check if gmx in PATH')
    # test gromacs version
    conf = configparser.ConfigParser(delimiters=(':',), )
    conf.read_string('[gromacs]\n' + output)
    conf = conf._sections['gromacs']

    logger.debug(json.dumps(conf, indent=4))
    return conf


def get_gromacs_version():
    GROMACS_VERSION_PATTERN = r'VERSION\s+(.*)\s*'
    conf = get_gromacs_config()
    version_string = conf['gromacs']

    logger.debug(f'version_string: {version_string}')
    pattern = re.compile(GROMACS_VERSION_PATTERN, re.IGNORECASE)
    version = re.findall(pattern, version_string)[0]
    return version


def test_gromacs_version():
    version = get_gromacs_version()
    if version:
        logger.debug(f'version: {version}')
        if LooseVersion(version) >= LooseVersion(MIN_GROMACS_VERSION):
            return True
    return False


def test_gromacs():
    if not test_gromacs_version():
        raise ValueError(
            f'Gromacs should be greater than version {MIN_GROMACS_VERSION}')
    return True


def generate_gromacs_grofile(filename, dest_dir='.', notcenter: bool = False):
    write_filename = os.path.realpath(f"{dest_dir}/{GRO_FILE}")
    format_convert(filename, write_filename, outputformat='gromacs',
                   extra_data={'filename': GRO_FILE})
    # try:
    #     import gaseio
    #     x = gaseio.read(filename, force_gase=True)
    #     x['filename'] = GRO_FILE
    #     gaseio.write(write_filename, x, format="gromacs")
    # except:
    #     import chemio
    #     chemio.convert(filename, write_filename=write_filename,
    #                    write_format='gromacs', data={'filename': GRO_FILE})
    # centerize
    if not notcenter:
        cmd = f'cd {dest_dir}; gmx editconf -c -f {write_filename} -o {write_filename} \
                > editconf.log 2>editconf.err'
        logger.debug(f'grompp cmd: \n{cmd}')
        exit_code = os.system(cmd)
        if exit_code != 0:
            warnings.warn("Gromacs editconf centerize molecule fail")
    return write_filename


def generate_gromacs_topfile(filename, input_format=None,
                             obgmx_method='exe', dest_dir='.'):
    from . import obgmx
    top_fname, itp_fname = obgmx.generate_gromacs_obgmx_UFF_topfile(
        filename, input_format, obgmx_method, dest_dir)
    return top_fname, itp_fname


def set_gro_element_name_with_top(
        gro_filename: str = GRO_FILE,
        top_filename: str = TOP_FILE,
        itp_filename: str = ITP_FILE):
    top_filename = top_filename or TOP_FILE
    itp_filename = itp_filename or ITP_FILE
    gro_filename = gro_filename or GRO_FILE
    with open(itp_filename) as fd:
        top_string = fd.read()
    atoms_section = re.split(
        r'\s*\[\s*atoms\s*\]\s+|\s*\[\s*bonds\s*\]\s+', top_string)[1]
    element_names = list()
    for line in atoms_section.split('\n')[1:]:
        element_names.append(line.split()[1])
    with open(gro_filename) as fd:
        gro_lines = fd.readlines()
    for i, (line, new_name) in enumerate(zip(gro_lines[2:-1], element_names)):
        line = list(line)
        line[10:15] = list('%5s' % (new_name))
        gro_lines[i+2] = ''.join(line)
    gro_string = ''.join(gro_lines)
    with open(gro_filename, 'w') as fd:
        fd.write(gro_string)
    logger.debug(gro_string)


def regularize_mdrun_config(mdrun_config):
    mdrun_config = mdrun_config.copy()
    # temperature:
    mdrun_config['temperature'] = atomtools.unit.trans_temperature(
        mdrun_config['temperature'], mdrun_config['temperature_unit'], 'Kelvin')
    mdrun_config['temperature_unit'] = 'K'
    # pressure:
    mdrun_config['pressure'] *= atomtools.unit.trans_pressure(
        mdrun_config['pressure_unit'], 'bar')
    mdrun_config['pressure_unit'] = 'bar'
    # d time, default fs
    mdrun_config['dt'] *= atomtools.unit.trans_time(
        mdrun_config['dt_unit'], 'ps')
    mdrun_config['dt_unit'] = 'ps'
    mdrun_config['time'] *= atomtools.unit.trans_time(
        mdrun_config['time_unit'], 'ps')
    mdrun_config['time_unit'] = 'ps'
    # calculate nsteps
    mdrun_config['nsteps'] = int(mdrun_config['time'] / mdrun_config['dt'])
    return mdrun_config


def generate_mdrun_file(mdrun_file=None, runtype='md', dest_dir='.', **kwargs):
    assert runtype in ['md', 'emin'], 'runtype must be either md or emin'
    if runtype == 'emin':
        mdrun_file = os.path.join(BASEDIR, 'mdrun_emin.mdp')
    else:
        mdrun_config = default_mdrun_config.copy()
        for key, val in kwargs.items():
            if key in mdrun_config:
                mdrun_config[key] = val
        mdrun_config = regularize_mdrun_config(mdrun_config)
    dest_dir = dest_dir or '.'
    dest_mdrun = os.path.realpath(f"{dest_dir}/{MDRUN_FILE}")
    if mdrun_file is not None:
        logger.debug(F"mdrun file: {mdrun_file}")
        try:
            shutil.copyfile(mdrun_file, dest_mdrun)
        except shutil.SameFileError:
            pass

    else:
        env = Environment(loader=FileSystemLoader(BASEDIR))
        template = env.get_template(MDRUN_TEMP)
        output = template.render(**mdrun_config)
        with open(dest_mdrun, 'w') as fd:
            fd.write(output)
    return dest_mdrun


def exec_grompp(mdrun_filename=MDRUN_FILE, top_filename=TOP_FILE,
                gro_filename=GRO_FILE, dest_dir='.'):
    # """gmx grompp to generate important files"""
    # generate_mdrun_file(mdrun_file=mdrun_file)
    cmd = f'cd {dest_dir}; gmx grompp -f {mdrun_filename} \
-p {top_filename} -c {gro_filename} \
>log_grompp.log 2>log_grompp.err'
    logger.debug(f'grompp cmd: \n{cmd}')
    exit_code = os.system(cmd)
    if exit_code != 0:
        raise OSError('grompp error')
    return mdrun_filename


def exec_mdrun(maxcore=4, device='cpu', dest_dir='.'):
    """
    execute mdrun, the main part of MD simulation
    Input:
        maxcore: int, max core using
        device: str: default cpu, also gpu/auto
        dest_dir: destination directory
    Output:
        dict: including trr_filename, edr_filename, xtc_filename
    """
    if not isinstance(maxcore, int):
        maxcore = 4
    dest_dir = dest_dir or '.'
    assert device in ['auto', 'cpu', 'gpu']
    help_cmd = f'gmx mdrun -h'
    _, help_text = subprocess.getstatusoutput(help_cmd)
    pme_flag = ''
    pmefft_flag = ''
    if '-pme ' in help_text:
        pme_flag = f'-pme {device} '
    if '-pmefft ' in help_text:
        pmefft_flag = f'-pmefft {device} '
    cmd = f'cd {dest_dir}; \
gmx mdrun -v -deffnm topol \
-nt {maxcore} -nb {device} {pme_flag} {pmefft_flag} -pin on \
-o traj.trr \
>log_mdrun.log 2>log_mdrun.err'
    logger.debug(f"mdrun cmd:\n{cmd}")
    exit_code, _ = subprocess.getstatusoutput(cmd)
    if exit_code != 0:
        raise OSError('mdrun error')
    trr_filename = os.path.realpath(f"{dest_dir}/{TRR_FILE}")
    edr_filename = os.path.realpath(f"{dest_dir}/{EDR_FILE}")
    xtc_filename = os.path.realpath(f"{dest_dir}/{XTC_FILE}")
    return {
        'trr_filename': trr_filename,
        'edr_filename': edr_filename,
        'xtc_filename': xtc_filename
    }


def gromacs_extract_data(cmd, data_filename,
                         error_msg='', debug_msg=''):
    import pandas as pd
    logger.debug(debug_msg)
    exit_code, output = subprocess.getstatusoutput(cmd)
    logger.debug(f"extract_data: {cmd}, \n{output}")
    if exit_code != 0:
        raise OSError(error_msg)
    with open(data_filename) as fd:
        line = fd.read()
    datablock = re.match(r'^[\s\S]*?\n\s*(\d+[\s\S]*)$', line)[1].strip()
    logger.debug(datablock)
    res = pd.read_csv(StringIO(datablock), sep=r'\s+',
                      header=None, index_col=0).values
    if res.ndim == 1:
        res = np.array([res])
    return res


def exec_get_trajectory(outgro_filename=OUTPUT_GRO, dest_dir='.'):
    dest_dir = dest_dir or '.'
    # outgro_filename = os.path.realpath(f'{outgro_filename}')
    all_traj_filenames = ['topol.xtc', 'traj.trr']
    for traj_filename in all_traj_filenames:
        cmd = f'cd {dest_dir}; gmx trjconv -f {traj_filename} \
-o {outgro_filename} << EOF\n0 EOF \
>/dev/null 2>&1'
        logger.debug(f"trjconv cmd:\n {cmd}")
        exit_code, output = subprocess.getstatusoutput(cmd)
        if exit_code == 0:
        #     logger.warning(output)
        #     raise OSError('trjcov error')
            outgro_filename = os.path.realpath(f"{dest_dir}/{outgro_filename}")
            return outgro_filename
    logger.warning(output)
    raise OSError('trjcov error')


def get_gromacs_legends(filename):
    with open(filename, 'r') as fd:
        _string = fd.read()
        legends = re.findall(r'@ s\d+ legend "(.*)"', _string)
    return legends


def extract_forces(trr_filename=TRR_FILE, dest_dir='.'):
    dest_dir = dest_dir or '.'
    cmd = f'cd {dest_dir}; gmx traj -f {trr_filename} -of <<EOF\n0 EOF\
>/dev/null 2>&1'
    debug_msg = f"extract_forces cmd: {cmd}"
    error_msg = 'extract_forces gmx traj error'
    force_fname = f'{dest_dir}/force.xvg'
    forces = gromacs_extract_data(cmd, force_fname, error_msg, debug_msg)
    forces = forces.reshape((len(forces), -1, 3))
    utrans = float(atomtools.unit.trans_energy('kJ/mol', 'eV') /
                   atomtools.unit.trans_length('nm', 'Ang'))
    forces = forces * utrans
    return forces


def extract_energies_dict(edr_filename=EDR_FILE, dest_dir='.'):
    """
-------------------------------------------------------------------
  1  Bond             2  G96Angle         3  LJ-(SR)          4  Disper.-corr.
  5  Coulomb-(SR)     6  Potential        7  Kinetic-En.      8  Total-Energy
  9  Conserved-En.   10  Temperature     11  Pres.-DC        12  Pressure
 13  Vir-XX          14  Vir-XY          15  Vir-XZ          16  Vir-YX
 17  Vir-YY          18  Vir-YZ          19  Vir-ZX          20  Vir-ZY
 21  Vir-ZZ          22  Pres-XX         23  Pres-XY         24  Pres-XZ
 25  Pres-YX         26  Pres-YY         27  Pres-YZ         28  Pres-ZX
 29  Pres-ZY         30  Pres-ZZ         31  #Surf*SurfTen   32  T-System

    Selelcting system is changing frequently, so we get all data and make a dictionary
    """
    numbers = list(map(str, range(1, 100)))
    numcmd = ' \n'.join(numbers)
    cmd = f'cd {dest_dir}; gmx energy -f {edr_filename} -o <<EOF\n'+numcmd+'\n\n EOF \
>/dev/null 2>&1'
    debug_msg = f"extract_energies cmd: {cmd}"
    error_msg = 'extract_energies with gmx energy failed'
    energies_fname = f'{dest_dir}/energy.xvg'
    energies = gromacs_extract_data(cmd, energies_fname, error_msg, debug_msg)
    legends = get_gromacs_legends(energies_fname)
    energies = energies.T
    utrans = float(atomtools.unit.trans_energy('kJ/mol', 'eV'))
    if 'Temperature' in legends:
        energies[:legends.index('Temperature')] *= utrans
    energies_dict = dict(zip(legends, energies))
    return energies_dict

# def old_extract_structures(output_gro=OUTPUT_GRO):
#     # with open(output_gro) as fd:
#     os.system("sed -i  '/^[[:space:]]*$/d' {0}".format(output_gro))
#     cmd = f"sed -n '2p' {output_gro}"
#     exit_code, output = subprocess.getstatusoutput(cmd)
#     nlines_per_frame = int(output) + GRO_FORMAT_EXTRA_LINES
#     structures = list()
#     tmp_gro_file = tempfile.mktemp()
#     with open(output_gro) as fd:
#         gro_lines = fd.readlines()
#     for i in range(len(gro_lines)//(nlines_per_frame)):
#         filestring = ''.join(
#             gro_lines[i*nlines_per_frame:(i+1)*nlines_per_frame])
#         with open(tmp_gro_file, 'w') as fd:
#             fd.write(filestring)
#         structures.append(read_atoms(tmp_gro_file, format='gromacs'))
#     return structures


def extract_structures(output_gro=OUTPUT_GRO):
    try:
        import gaseio
        return gaseio.read(output_gro, index=':')
    except:
        import chemio
        return chemio.read(output_gro, index=":")
