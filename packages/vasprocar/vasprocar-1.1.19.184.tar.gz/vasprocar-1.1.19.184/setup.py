from distutils.core import setup
from setuptools import setup, find_packages
import json
from pathlib import Path
from typing import Optional

setup(
    name = "vasprocar",
    version = "1.1.19.184",
    entry_points={'console_scripts': ['vasprocar = vasprocar:main']},
    description = "VASProcar is an open-source package written in the Python 3 programming language, which aims to provide an intuitive tool for the post-processing of the output files produced by the DFT VASP/QE codes, through an interactive user interface.",
    author = "Augusto de Lelis Araujo and Renan da Paixao Maciel", 
    author_email = "augusto-lelis@outlook.com, renan.maciel@physics.uu.se",
    url = "https://doi.org/10.5281/zenodo.6343960",
    download_url = "https://doi.org/10.5281/zenodo.6343960",
    license = "GNU GPLv3",
    install_requires=['numpy>=1.24.1',
                      'scipy>=1.10.0',
                      'matplotlib>=3.8.0',
                      'plotly>=5.13.0',
                      'moviepy>=1.0.2',
                      'kaleido>=0.2.1',
                      'requests>=2.31.0'],
    package_data={"": ['*.dat', '*.png', '*.jpg', '*']},
)


# python3 -m pip install --upgrade twine
# python setup.py sdist
# python -m twine upload dist/*