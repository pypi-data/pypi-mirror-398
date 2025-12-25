import codecs
import os.path
from pathlib import Path
from setuptools import setup, Extension, find_packages
from distutils.command.build import build as build_orig

def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()

def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")

here = Path(__file__).parent
readme_file = (here / "README.md").read_text()

exts = []

# class build(build_orig):

#     def finalize_options(self):
#         super().finalize_options()

#         from Cython.Build import cythonize
#         self.distribution.ext_modules = cythonize(self.distribution.ext_modules,
#                                                   language_level=3)

setup(
    name="tactigon_ironboy",
    version=get_version("tactigon_ironboy/__init__.py"),
    author="Next Industries s.r.l.",
    author_email="info@nextind.eu",
    url="https://nextind.eu",
    description="IronBoy Library",
    long_description=readme_file,
    long_description_content_type='text/markdown',
    keywords="tactigon,arduino,robot,cobot,ironboy",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.8.0",
    install_requires=[
        "bleak==2.0.0"
    ],
    ext_modules=exts,
)
