from setuptools import setup, Extension
import numpy
from os.path import exists
from ctypes.util import find_library

useMtg = exists("./mrarbgrad_src/ext/mtg/")
useJemalloc = find_library("jemalloc") is not None

_sources = \
[
    './mrarbgrad_src/ext/utility/global.cpp',
    './mrarbgrad_src/ext/utility/v3.cpp',
    './mrarbgrad_src/ext/mag/GradGen.cpp',
    './mrarbgrad_src/ext/main.cpp',
    './mrarbgrad_src/ext/mtg/mtg_functions.cpp',
    './mrarbgrad_src/ext/mtg/spline.cpp'
]
if not useMtg:
    _sources.remove('./mrarbgrad_src/ext/mtg/mtg_functions.cpp')
    _sources.remove('./mrarbgrad_src/ext/mtg/spline.cpp')

modExt = Extension\
(
    "mrarbgrad.ext", 
    sources = _sources,
    libraries = ['jemalloc'] if useJemalloc else [],
    include_dirs = ["./mrarbgrad_src/ext/", numpy.get_include()],
    define_macros = [("USE_MTG", None)] if useMtg else None,
    language = 'c++'
)

_packages = \
[
    "mrarbgrad", 
    "mrarbgrad.ext", 
    "mrarbgrad.ext.traj",
    "mrarbgrad.ext.mag", 
    "mrarbgrad.ext.mtg",
    "mrarbgrad.ext.utility",
]
if not useMtg:
    _packages.remove("mrarbgrad.ext.mtg")

_package_dir = \
{
    "mrarbgrad":"./mrarbgrad_src/", 
    "mrarbgrad.ext":"./mrarbgrad_src/ext/", 
    "mrarbgrad.ext.traj":"./mrarbgrad_src/ext/traj/",
    "mrarbgrad.ext.mag":"./mrarbgrad_src/ext/mag/", 
    "mrarbgrad.ext.mtg":"./mrarbgrad_src/ext/mtg/",
    "mrarbgrad.ext.utility":"./mrarbgrad_src/ext/utility/"
}

setup\
(
    name = 'mrarbgrad',
    # install_requires = ["numpy", "matplotlib"], # pip will automatically upgrade numpy if it see this, which might corrupt the environment
    ext_modules = [modExt],
    packages = _packages,
    package_dir = _package_dir,
    include_package_data = True
)
