from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext
import pybind11
import sys

# Lesen der README-Datei (optional)
try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "KIB package description."

# Überprüfen des Compilers und Anpassen der Flags (falls erforderlich)
if sys.platform == 'win32':
    # Einstellungen für Visual C++ Compiler
    extra_compile_args = ['/O2', '/std:c++17', '/D_USE_MATH_DEFINES']
    extra_link_args = []
else:
    # Einstellungen für GCC oder Clang
    extra_compile_args = ['-O3', '-std=c++17', '-D_USE_MATH_DEFINES']
    extra_link_args = []

# Definiere die Erweiterung für pybind11
ext_modules = [
    Extension(
        "KIB_LAP.plate_buckling_cpp",  # Modulname (muss mit dem Python-Import übereinstimmen)
        ["KIB_LAP/Plattenbeulen/plate_buckling.cpp"],  # Pfad zur C++-Datei
        include_dirs=[
            pybind11.get_include(),  # Include-Verzeichnis von pybind11
            '.',  # Aktuelles Verzeichnis
            'KIB_LAP/Plattenbeulen',  # Verzeichnis der Header-Dateien
        ],
        language="c++",  # Sprache ist C++
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    ),
    Extension(
        "KIB_LAP.plate_bending_cpp",  # Modulname (muss mit dem Python-Import übereinstimmen)
        [
            "KIB_LAP/Plattentragwerke/plate_bending.cpp",
            "KIB_LAP/Plattentragwerke/Functions.cpp"
        ],  # Pfad zu den C++-Dateien
        include_dirs=[
            pybind11.get_include(),  # Include-Verzeichnis von pybind11
            '.',  # Aktuelles Verzeichnis
            'KIB_LAP/Plattentragwerke',  # Verzeichnis der Header-Dateien
        ],
        language="c++",  # Sprache ist C++
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    )
]

setup(
    name="kib_lap",
    version="0.6.4",
    packages=find_packages(),
    include_package_data=True,
    description="A package for structural engineering calculations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="leoth",
    author_email="thomas.leonard@outlook.de",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "pybind11>=2.6",  # pybind11 als Abhängigkeit hinzufügen
    ],
    ext_modules=ext_modules,  # Erweiterungen (C++-Module) hinzufügen
    cmdclass={"build_ext": build_ext},  # Build-Kommando für Erweiterungen
)
