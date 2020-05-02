# coding=utf-8

import os
from setuptools import setup, find_packages


def get_version():
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import automd
    return automd.__version__


def get_all_shared_libs(root_path):
    res = []
    for fname in os.listdir(root_path):
        fname = os.path.join(root_path, fname)
        if os.path.isdir(fname):
            res.extend(get_all_shared_libs(fname))
        elif fname.endswith('.so'):
            res.append(fname)
    return res


def get_package_shared_libs(root_path):
    curdir = os.getcwd()
    os.chdir(root_path)
    res = get_all_shared_libs('.')
    os.chdir(curdir)
    return res


def get_python_version():
    import sys
    version_info = sys.version_info
    version = f"{version_info.major}.{version_info.minor}"
    return version


if __name__ == '__main__':
    setup(
        name='automd',
        version=get_version(),
        description=(
            'Automatic Molecular Dynamics using UFF potnetial',
        ),
        long_description=open('README.md').read(),
        long_description_content_type='text/markdown',
        author='Sky Zhang',
        author_email='sky.atomse@gmail.com',
        maintainer='Sky Zhang',
        maintainer_email='sky.atomse@gmail.com',
        license='MIT License',
        packages=find_packages(),
        platforms=["Linux", "Darwin"],
        url='https://github.com/atomse/automd',
        python_requires='=='+get_python_version()+'.*',
        # python_requires='>=3.6',
        classifiers=[
            'Development Status :: 4 - Beta',
            'Operating System :: POSIX',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python',
            'Programming Language :: Python :: Implementation',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
        ],
        install_requires=open('requirements.txt').read().split(),
        entry_points={
            "console_scripts": [
                "automd=automd.cli.main:main",
            ],
        },
        extras_require={
            'docs': [
                'sphinx',
                'sphinxcontrib-programoutput',
                'sphinx_rtd_theme',
                'numpydoc',
            ],
            'tests': [
                'pytest>=4.0',
                'pytest-cov'
            ],
            'curate': [
                'graphviz'
            ],
        },
        include_package_data=True,
        package_data={'': get_package_shared_libs('automd')},
        zip_safe=False,
    )
