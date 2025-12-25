# setup.py

from setuptools import setup, Extension
import pybind11
from pybind11.setup_helpers import build_ext
import sys

# Überprüfen des Compilers
if sys.platform == 'win32':
    # Einstellungen für Visual C++ Compiler
    extra_compile_args = ['/O2', '/std:c++17', '/openmp']
    extra_link_args = ['/openmp']
else:
    # Einstellungen für GCC oder Clang
    extra_compile_args = ['-O3', '-std=c++17', '-fopenmp']
    extra_link_args = ['-fopenmp']

ext_modules = [
    Extension(
        'plate_buckling',
        ['plate_buckling.cpp'],
        include_dirs=[
            pybind11.get_include(),
        ],
        language='c++',
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    ),
]

setup(
    name='plate_buckling_cpp',
    ext_modules=ext_modules,
    cmdclass={'build_ext': build_ext},
)
