import os
import stat
import shutil
import time
from distutils.core import setup
import multiprocessing
import argparse
import tempfile
from Cython.Build import cythonize

starttime = time.time()
CURDIR = os.path.abspath('.')
PARENTPATH = os.getcwd()  # sys.argv[1] if len(sys.argv) > 1 else ""
setupfile = os.path.join(os.path.abspath('.'), __file__)
DEFAULT_BUILD_DIR = "build"  # 项目加密后位置
BUILD_TMP_DIR = tempfile.mkdtemp()


NOT_COMPILED_FILES = ['setup.py', 'test.py', 'app.py', 'server.py']


def copy_complete(source, target):
    # copy content, stat-info (mode too), timestamps...
    shutil.copy2(source, target)
    # copy owner and group
    st = os.stat(source)
    os.chown(target, st[stat.ST_UID], st[stat.ST_GID])


def get_pythons(basepath=os.path.abspath('.'), parentpath='', name='',
                build_dir=DEFAULT_BUILD_DIR,
                excepts=(), copyOther=False, delC=False):
    """
    获取py文件的路径
    :param basepath: 根路径
    :param parentpath: 父路径
    :param name: 文件/夹
    :param excepts: 排除文件
    :param copy: 是否copy其他文件
    :return: py文件的迭代器
    """
    fullpath = os.path.join(basepath, parentpath, name)
    # 返回指定的文件夹包含的文件或文件夹的名字的列表
    for fname in os.listdir(fullpath):
        ffile = os.path.join(fullpath, fname)
        print("ffile", ffile)
        # print basepath, parentpath, name,file
        # 是文件夹 且不以.开头 不是 build  ，不是迁移文件
        if os.path.isdir(ffile) and \
                fname != build_dir and \
                not fname.startswith('.') and \
                fname != "migrations":
            print("fname", fname)
            for f in get_pythons(basepath, os.path.join(parentpath, name), fname,
                                 build_dir, excepts, copyOther, delC):
                yield f
        elif os.path.isfile(ffile):
            ext = os.path.splitext(fname)[1]
            if ext == ".c":
                print("delC", delC)
                if delC and os.stat(ffile).st_mtime > starttime:
                    os.remove(ffile)
            elif ffile not in excepts and os.path.splitext(fname)[1] not in ('.pyc', '.pyx'):
                # manage.py文件不编译
                if os.path.splitext(fname)[1] in ('.py', '.pyx') and \
                        not fname.startswith('__') and \
                        not fname in NOT_COMPILED_FILES:
                    yield os.path.join(parentpath, name, fname)
                elif copyOther:
                    dstdir = os.path.join(
                        basepath, build_dir, parentpath, name)
                    if not os.path.isdir(dstdir):
                        os.makedirs(dstdir)
                    copy_complete(ffile, os.path.join(dstdir, fname))
        else:
            pass


def create_build_dir(build_dir=DEFAULT_BUILD_DIR):
    if os.path.exists(build_dir):
        if os.path.isdir(build_dir):
            shutil.rmtree(build_dir)
        else:
            raise RuntimeError(
                f"build directory {build_dir} occupied by a file")


def encryption(max_workers=1, build_dir=DEFAULT_BUILD_DIR):
    # 获取py列表
    module_list = list(
        get_pythons(basepath=CURDIR, parentpath=PARENTPATH,
                    excepts=(setupfile), build_dir=build_dir)
    )
    try:
        kwds = {
            'ext_modules': cythonize(module_list),
            'script_args': ["build_ext", "-b", build_dir, "-t", BUILD_TMP_DIR]
        }
        # here start the gcc compiling
        # sequential mode
        if max_workers == 1:
            setup(**kwds)
        else:
            task_handles = []
            with multiprocessing.Pool(max_workers) as pool:
                for mod in module_list:
                    kwds = {
                        'ext_modules': cythonize([mod]),
                        'script_args': ["build_ext", "-b", build_dir, "-t", BUILD_TMP_DIR],
                    }
                    task_handles.append(pool.apply_async(setup, kwds=kwds))
                for handle in task_handles:
                    print(handle.get())
    except Exception as e:
        print(e)
        return
    else:
        module_list = list(
            get_pythons(basepath=CURDIR, parentpath="",
                        excepts=(setupfile), build_dir=build_dir,
                        copyOther=True))
    module_list = list(
        get_pythons(basepath=CURDIR, parentpath=PARENTPATH,
                    excepts=(setupfile), build_dir=build_dir,
                    delC=True))
    if os.path.exists(BUILD_TMP_DIR):
        shutil.rmtree(BUILD_TMP_DIR)
    print("complate! time:", time.time() - starttime, 's')


def main(kargs):
    create_build_dir(kargs.build_dir)
    encryption(kargs.max_workers, kargs.build_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-j', '--max-workers', nargs='?', type=int)
    parser.add_argument('--build-dir', default=DEFAULT_BUILD_DIR, type=str)
    args = parser.parse_args()
    main(args)
