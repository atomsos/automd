"""


OBGMX python


"""


import os
import re
import shutil
import subprocess
import tempfile
import distro
import modlog
import atomtools.filetype


BASEDIR = os.path.dirname(os.path.realpath(__file__))
linuxdist = distro.linux_distribution(full_distribution_name=False)[0]


SUPPORTED_OBGMX_METHODS = ['online', 'exe']
OBGMX_EXE_FNAME = os.path.join(BASEDIR, 'exe', 'obgmx')

logger = modlog.getLogger(__name__)


data_format = '''


-----------------------------569524120325042211622299612
Content-Disposition: form-data; name="ufile"; filename="img1.xyz"
Content-Type: chemical/x-xyz

{0}
-----------------------------569524120325042211622299612
Content-Disposition: form-data; name="cr"

geo
-----------------------------569524120325042211622299612
Content-Disposition: form-data; name="w14"

1.0
-----------------------------569524120325042211622299612
Content-Disposition: form-data; name="angle-pot"

g96
-----------------------------569524120325042211622299612--

'''


class NotInstallError(Exception):
    def __init__(self, package_name, debian_install="", centos_install=""):
        super(NotInstallError, self).__init__()
        dist = distro.linux_distribution(full_distribution_name=False)[0]
        msg = f"\n\npackage: {package_name} not installed\n"
        if dist in ['debian', 'ubuntu']:
            msg += f"Install with: sudo apt install {debian_install}"
        elif dist in ['centos', 'redhat']:
            msg += f"Install with: sudo yum install {centos_install}"
        else:
            msg += f"Dist: {dist}; you may need to find your own command for installing {package_name}"
        self.errorinfo = msg

    def __str__(self):
        return self.errorinfo


class CommandError(Exception):
    def __init__(self, msg, cmd):
        super(CommandError, self).__init__()
        self.msg = msg
        self.cmd = cmd

    def __str__(self):
        return self.msg + '\n' + self.cmd


def get_gromacs_obgmx_UFF_top_online(xyzfilename):
    """
    online only support .xyz and .pdb
    """
    import requests
    url = 'http://software-lisc.fbk.eu/obgmx/obgmx.php'
    headers = {
        'Host': 'software-lisc.fbk.eu',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-GB,en;q=0.5',
        'Referer': 'http://software-lisc.fbk.eu/obgmx/index.php',
        'Content-Type': 'multipart/form-data; boundary=---------------------------569524120325042211622299612',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    data = data_format.format(atomtools.fileutil.get_file_content(xyzfilename))
    response = requests.post(url, headers=headers, data=data)
    output = response.text
    topfile, itpfile = re.findall(re.compile(r'<textarea.*?>([\s\S]*?)</textarea>'),
                                  output)
    # output = topfile.replace('#include <obgmx.itp>\n', itpfile)
    return topfile, itpfile


def get_gromacs_obgmx_UFF_top_exe(xyzfilename):
    assert os.path.exists(OBGMX_EXE_FNAME), f"{OBGMX_EXE_FNAME} not found"
    tempdir = tempfile.mkdtemp()
    xyzfilename = os.path.abspath(xyzfilename)
    cmd = f"cd {tempdir}; {OBGMX_EXE_FNAME} {xyzfilename}"
    logger.info(cmd)
    status, stdout = subprocess.getstatusoutput(cmd)
    fname = os.path.join(tempdir, 'obgmx.top')
    if status != 0:
        shutil.rmtree(tempdir)
        raise RuntimeError(stdout)
    with open(fname) as fd:
        output = fd.read()
    shutil.rmtree(tempdir)
    return output


# def get_gromacs_obgmx_UFF_top(filename, input_format=None, obgmx_method='exe'):
#     import chemio
#     assert obgmx_method in SUPPORTED_OBGMX_METHODS
#     xyzfilename = filename
#     rm_flag = False
#     if isinstance(xyzfilename, str) and not xyzfilename.endswith('.xyz'):
#         xyzfilename = tempfile.mktemp(suffix='.xyz', prefix='automd')
#         chemio.convert(filename, xyzfilename,
#                        read_format=input_format, write_format='xyz')
#         rm_flag = True
#     if obgmx_method == 'exe' and os.path.isfile(OBGMX_EXE_FNAME):
#         output = get_gromacs_obgmx_UFF_top_exe(xyzfilename)
#     else:
#         output = get_gromacs_obgmx_UFF_top_online(xyzfilename)
#     logger.debug(output)
#     if rm_flag and os.path.exists(xyzfilename):
#         os.remove(xyzfilename)
#     return output


# def generate_gromacs_obgmx_UFF_topfile(filename, input_format=None,
#                                        obgmx_method='exe', dest_dir=None):
#     output = get_gromacs_obgmx_UFF_top(filename, input_format=input_format,
#                                        obgmx_method=obgmx_method)
#     dest_dir = dest_dir or '.'
#     write_fname = f"{dest_dir}/obgmx.top"
#     if not os.path.exists(dest_dir):
#         os.makedirs(dest_dir)
#     with open(write_fname, 'w') as fd:
#         fd.write(output)
#     return os.path.realpath(write_fname)


def generate_gromacs_obgmx_UFF_topfile(filename, input_format=None,
                                       obgmx_method='exe', dest_dir='.'):
    """
    generate gromacs UFF top/itp file with OBGMX
    Input:
        filename: structure file
        input_format: format of the input
        obgmx_method: must be exe
        dest_dir: destination directory, default is '.'
    Output:
        realpath of obgmx.top file
    """
    # import chemio
    assert obgmx_method == 'exe', 'obgmx_method must be "exe"'
    xyzfilename = filename
    rm_flag = False
    if isinstance(xyzfilename, str) and not xyzfilename.endswith('.xyz'):
        xyzfilename = tempfile.mktemp(suffix='.xyz', prefix='automd')
        format_convert(filename, xyzfilename, outputformat='xyz')
        # chemio.convert(filename, xyzfilename,
        #                read_format=input_format, write_format='xyz')
        rm_flag = True
    cmd = f"cd {dest_dir}; {OBGMX_EXE_FNAME} {xyzfilename}"
    logger.info(cmd)
    status, stdout = subprocess.getstatusoutput(cmd)
    if rm_flag:
        os.remove(xyzfilename)
    if status != 0:
        raise RuntimeError(stdout)
    top_filename = os.path.realpath(os.path.join('.', 'obgmx.top'))
    itp_filename = os.path.realpath(os.path.join('.', 'obgmx.itp'))
    return top_filename, itp_filename


def test(obgmx_method='exe', dest_dir='tests/tmp'):
    # import chemio
    TESTDIR = os.path.join(BASEDIR, 'tests')
    # filename = os.path.join(TESTDIR, 'h2o2.xyz')
    # print(chemio.read(get_gromacs_obgmx_UFF_top(
    #     filename, obgmx_method), format='gromacs-top'))

    for filename in os.listdir(TESTDIR):
        filename = os.path.join(TESTDIR, filename)

        if not os.path.isfile(filename) or \
                os.path.splitext(filename)[-1] in ['.itp', '.top', '.ffout']:
            print('pass1', filename)
            continue
        print(filename)
        outfile, itpfile = generate_gromacs_obgmx_UFF_topfile(
            filename, obgmx_method=obgmx_method,
            dest_dir=os.path.realpath(dest_dir))
        print(outfile)
        print(open(outfile).read())


if __name__ == '__main__':
    test(obgmx_method='exe')
