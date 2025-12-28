"""
    This module provides console commands for packaging Dask dependencies to compute on cluster.

    The main entry point of this module is ``dask-create-dask-dep-pkg`` command. This command creates a ZIP package
    containing modules needed by workers to execute the tasks( dependencies modules).

    Examples
    --------
    The following command creates a package named distributed-mlbox.zip in which we found all package modules::

    dask-create-dask-dep-pkg -m src/distributed-mlbox-utils -o distributed-mlbox.zip

    By default,if you don't give a name to zip (without -o option), The above command creates package named
    ``dask_dep.zip`` in root directory by default.

    The created package includes all package modules exclude some specific modules given in -e options

    You can set this file to ``[client]`` section of a cfg file \
    configuration to submit Dask tasks with the dependencies::

     [client]
     upload_file=dask_dep.zip

    ``dask-create-dask-dep-pkg`` command is intended to be used when deploying by .gitlab.yml or on time
    development.


    Example help return::
    dask-create-dask-dep-pkg -help
    usage: dask-create-dask-dep-pkg [-h] -m modules [-o DASK_DEP_PKG]
                                         [-e [MODULE_NAME [MODULE_NAME ...]]]
                                         [--dist_path PATH]

    Package dependencies of Dask tasks

    optional arguments:
      -h, --help            show this help message and exit
      -m modules, --modules modules
                            required Dask tasks modules
      -o DASK_DEP_PKG, --output DASK_DEP_PKG
                            Name of Dask task dependency package to create
      -e [MODULE_NAME [MODULE_NAME ...]], --excludes [MODULE_NAME [MODULE_NAME ...]]
                            Modules to exclude from the package
      --dist_path PATH      Build directory


"""

import argparse
import logging
import os
import re
import shutil
import sys
import threading
import zipfile

DASK_DEP_PKG = "dask_dep.zip"
""" Default name of Dask job dependency packages """

logger = logging.getLogger(__name__)
__context = threading.local()
__context.is_cli = False


def __init_cli_logging():
    if __context.is_cli:
        logging.root.handlers = []
        logging.basicConfig(
            stream=sys.stdout,
            level=logging.INFO,
            format="%(levelname)s: %(msg)s"
        )


__excludes = [
    '__pycache__'
]


def clean_dist_dir(dist_path):
    if os.path.exists(dist_path):
        logger.info("Clean dist path: {}".format(dist_path))
        shutil.rmtree(dist_path)
    base_path = os.path.basename(os.path.normpath(dist_path))
    return os.path.join(dist_path, base_path)


def init_dist_dir(src, dist_path):
    base_path = os.path.basename(os.path.normpath(src))
    return os.path.join(dist_path, base_path)


def __copy_directories(src, dist_path):
    try:
        logger.info("Copy directories and files : {}->{}".format(src, dist_path))
        shutil.copytree(src, dist_path)
    except shutil.Error as e:
        logger.error("Directory not copied. Error: {}".format(e))
    except OSError as e:
        logger.error("Directory not copied. Error: {}".format(e))


def copy_dependencies(modules,
                      dist_path,
                      excludes=None):
    """ Copy dependencies.

    Parameters
    ----------
    modules: str
        path to modules to copy
    dist_path: str
        path of the destination directory where the modules will be copied
    excludes: list[str]
        name of modules to be excluded
    """

    logger.info("Copy dependencies: {} -> {}".format(modules, dist_path))
    __copy_directories(modules, dist_path)
    __init_cli_logging()

    excludes = __excludes + (excludes or [])

    logger.info("Exclude dependencies: {}".format(", ".join(excludes)))
    for f in os.listdir(dist_path):
        name = re.sub("[\\-.].+$", "", f)
        if name in excludes:
            path = os.path.join(dist_path, f)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)


def list_dependencies(dist_path, excludes=None):
    """ list modules in a directory

    Parameters
    ----------
    dist_path: str
        path of the directory to scan
    excludes: list[str]
        name of the modules to be excluded

    Returns
    -------
    (list[str], list[str])
        names of the modules and full path location of the modules

    """
    excludes = set(excludes or [])
    names = set()
    contents = []

    for f in os.listdir(dist_path):
        name = re.sub("[\\-.].+$", "", f)
        if name not in excludes:
            names.add(name)
            contents.append(os.path.join(dist_path, f))
    names = list(names)
    names.sort()
    return names, contents


def package_dependencies(dist_path, dependency_pkg, excludes=None):
    """ Create a package of dependencies

    Parameters
    ----------
    dist_path: str
        path of the directory where dependencies are located
    dependency_pkg: str
        name of the dependency package file to create
    excludes: list[str]
        names of the modules to be excluded
    """
    names, contents = list_dependencies(dist_path, excludes)
    logger.info("Package dependencies: {} -> {}".format(", ".join(names), dependency_pkg))

    with zipfile.ZipFile(dependency_pkg, 'w', zipfile.ZIP_DEFLATED) as archive:
        for c in contents:
            if os.path.isdir(c):
                for root, dirs, files in os.walk(c):
                    for f in files:
                        src = os.path.join(root, f)
                        dst = os.path.relpath(src, dist_path)
                        archive.write(src, dst)
            else:
                archive.write(c, os.path.relpath(c, dist_path))


def create_dask_dep_pkg():
    """ Console command to package dependencies of Dask tasks """

    sys.path.append(os.path.curdir)

    __context.is_cli = True
    __init_cli_logging()

    parser = argparse.ArgumentParser(description="Package dependencies of Dask tasks")

    target = os.path.join(".", "target")

    parser.add_argument("-m", "--modules", metavar="MODULES_PATH", required=True, help="required Dask tasks modules")

    parser.add_argument("-o", "--output", metavar="DASK_DEP_PKG",
                        help="Name of Dask task dependency package to create ", default=DASK_DEP_PKG)

    parser.add_argument("-e", "--excludes", metavar="MODULE_NAME",
                        help="Modules to exclude from the package", nargs="*")

    parser.add_argument("--dist_path", metavar="PATH",
                        help="Build directory", default=os.path.join(target))

    args = parser.parse_args()

    try:
        clean_dist_dir(args.dist_path)
        dist_path = init_dist_dir(args.modules, args.dist_path)
        copy_dependencies(args.modules, dist_path, args.excludes)
        package_dependencies(args.dist_path, args.output)

    except ValueError as e:
        logger.error(e.message)
        exit(1)
