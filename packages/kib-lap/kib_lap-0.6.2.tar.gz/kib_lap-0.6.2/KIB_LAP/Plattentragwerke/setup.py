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
        'plate_bending_cpp',
        ['plate_bending.cpp', 'Functions.cpp'],  # Fügen Sie alle Ihre .cpp-Dateien hinzu
        include_dirs=[
            pybind11.get_include(),  # Include-Verzeichnis von pybind11
            '.',  # Aktuelles Verzeichnis
            'KIB_LAP/Plattentragwerke',  # Verzeichnis der Header-Dateien
        ],
        language='c++',
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    ),
]

setup(
    name='plate_bending_cpp',
    version='0.1',
    author='Ihr Name',
    author_email='ihre.email@example.com',
    description='Platten nach Kirchhoff',
    ext_modules=ext_modules,
    cmdclass={'build_ext': build_ext},
)
