"""

main executor of automd


"""

import os
import shutil
import json
import modlog
import pdb

from . import gromacs_utils
# from .default_config import default_mdrun_config

logger = modlog.getLogger(__name__)
DEFAULT_MAX_CORE = 4


def generate_gromacs_topfile_itpfile(input_file, dest_dir='.', outfilename=None):
    """
    generate topfile with the given outfilename
    Input:
        input_file: filename of structure file
    Output:
        abspath of topfile
    """
    os.makedirs(dest_dir, exist_ok=True)
    topfile, itpfile = gromacs_utils.generate_gromacs_topfile(
        input_file, dest_dir=dest_dir)
    if outfilename:
        shutil.move(topfile, outfilename)
        topfile = outfilename
    return os.path.realpath(topfile), os.path.realpath(itpfile)


def run(input_file, runtype='md', mdrun_file=None, dest_dir='.',
        max_core: int = DEFAULT_MAX_CORE, device: str = 'cpu',
        extract_forces: bool = False, topfile=None, itpfile=None,
        dry_run: bool = False, **args):
    """
    run automd
    Input:
        input_file: filename of input
        dest_dir: directory where output will be saved
        max_core: maximum number of cores
        device: str, default cpu, but also gpu/auto
        extract_forces: extract forces with output
        topfile: run gromacs with given topfile
        dry_run: bool, do not execute gromacs if true
    Output:
        dict, including all the calculated properties
    """
    # pdb.set_trace()
    if isinstance(input_file, str) and os.path.exists(input_file):
        input_file = os.path.abspath(input_file)
    assert runtype in ['md', 'emin'], 'runtype must be either md or emin'
    max_core = max_core or DEFAULT_MAX_CORE
    logger.debug(f"max_core: {max_core}")
    logger.debug(f"input_file: {input_file}, \nargs: {args}")
    # main part
    gromacs_utils.test_gromacs()
    out_dict = dict()
    os.makedirs(dest_dir, exist_ok=True)
    grofile = gromacs_utils.generate_gromacs_grofile(
        input_file,
        dest_dir=dest_dir)
    if not topfile:
        topfile, itpfile = gromacs_utils.generate_gromacs_topfile(
            input_file,
            dest_dir=dest_dir)
    else:
        if not itpfile:
            itpfile = os.path.splitext(topfile)[0] + '.itp'
    mdrunfile = gromacs_utils.generate_mdrun_file(
        mdrun_file, runtype=runtype, dest_dir=dest_dir, **args)
    gromacs_utils.set_gro_element_name_with_top(
        grofile, topfile, itpfile)
    mdrunfile = gromacs_utils.exec_grompp(
        mdrunfile, topfile, grofile, dest_dir=dest_dir)
    out_dict['grofile'] = grofile
    out_dict['topfile'] = topfile
    out_dict['itpfile'] = itpfile
    out_dict['mdrunfile'] = mdrunfile
    out_dict['mdrunfile'] = mdrunfile
    logger.debug(f"{json.dumps(out_dict, indent=4)}")
    if not dry_run:
        _fdict = gromacs_utils.exec_mdrun(
            max_core, device=device, dest_dir=dest_dir)
        out_dict.update(_fdict)
        # import pdb; pdb.set_trace()
        output_gro = gromacs_utils.exec_get_trajectory(dest_dir=dest_dir)
        out_dict['output_gro'] = output_gro
        logger.debug(f"{json.dumps(out_dict, indent=4)}")
        energies_dict = gromacs_utils.extract_energies_dict(
            edr_filename=out_dict['edr_filename'], dest_dir=dest_dir)
        out_dict['energies_dict'] = energies_dict
        out_dict['potential_energy'] = energies_dict['Potential']
        if extract_forces:
            forces = gromacs_utils.extract_forces(
                trr_filename=out_dict['trr_filename'], dest_dir=dest_dir)
            out_dict['forces'] = forces
    logger.debug(f"{out_dict}")
    return out_dict


def get_isomers(input_file, mdrun_file=None, dest_dir='.', max_core=DEFAULT_MAX_CORE,
                device: str = 'cpu', extract_forces=False, topfile=None,
                dry_run=False, **args):
    """
    get_isomers:
    Input:
        input_file: filename of inputfile
        dest_dir: directory of destination
        max_core: maximum core available
        device: cpu/gpu/auto
        extract_forces: whether forces extracted
        topfile: given topology file, if None then will be generated automatically
        dry_run: whether to run
        **args: arguments for MD simulation
    Output:
        isomers: json format
    """
    out_dict = run(input_file, mdrun_file, dest_dir, max_core, device,
                   extract_forces, topfile=topfile,
                   dry_run=dry_run, **args)
    output_gro = out_dict['output_gro']
    res = gromacs_utils.extract_structures(output_gro)
    logger.debug(f"get_isomers: {res}")
    return res
