# AutoMD


Automatic run gromacs with Universal Forcefield(UFF)

Right now we are using repo `obgmx.exe` instead of `obgmx.singularity`, no other
softwares are needed to implement AutoMD




I'm trying to make it a docker so that it will be extremely
convenient for installation.



## Installation

* Install requirements
        - `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt`
        - Or `pip install -r requirements.txt`
* install
        - `python3 setup.py install`

## OBGMX

[OBGMX, http://software-lisc.fbk.eu/obgmx/index.php](http://software-lisc.fbk.eu/obgmx/index.php)

GROMACS topology generator using Open Babel.

This tool is used to generate top file with UFF forcefield.

all related tools are in `obgmx.py`, key function is:

* `generate_gromacs_obgmx_UFF_topfile`: generate top file for gromacs

* version: 2.3.2(Aug. 6, 2015)



## AutoMD

AutoMD generate .top with OBGMX, and .gro with ChemIO.

* `generate_gromacs_top_gro`: generate top and gro file to specific dir

* mdrun.mdp is generate with jinja2 template to dest directory. 

* `gromacs` will be then executed

* several framse of the output trajectory will be extracted.



## Code encryption

Since the code may be executed on public machine, we encrypted the code with cython,

just `make build` will execute encrypt.py, generate encrypted code and assemble

like normal setup.py
