# VASProcar Copyright (C) 2023   -   GNU GPL-3.0 license

VASProcar is an open-source package written in the Python 3 programming language, which aims to provide an intuitive tool for the post-processing of the output files produced by the DFT VASP or QE code, through an interactive user interface.

VASProcar extracts information and results from the following VASP output files (CONTCAR, KPOINTS, OUTCAR, PROCAR, DOSCAR, LOCPOT, PARCHG and vasprun.xml) or QE output files (scf.in, scf.out, nscf.in, nscf.out, bands.in, bands.out, projwfc.in, projwfc.out, "filband", "filproj".projwfc_up and "filpdos".pdos_atm#_wfc).

Please use the following DOI ([10.5281/zenodo.6343960](https://doi.org/10.5281/zenodo.6343960)) to cite the use of the code in publications.

### Repositories:  [ZENODO](https://doi.org/10.5281/zenodo.6343960), [GitHub](https://github.com/Augusto-de-Lelis-Araujo/VASProcar-Python-tools-VASP), and [PyPi](https://pypi.org/project/vasprocar)

For more informations/questions send an e-mail to: augusto-lelis@outlook.com

------------------------------------------------------------------------

## Installation

-  Requirements

    - [Numpy](https://pypi.org/project/numpy/)
    - [Scipy](https://pypi.org/project/scipy/)
    - [Matplotlib](https://pypi.org/project/matplotlib/)
    - [Plotly](https://pypi.org/project/plotly/)
    - [Moviepy](https://pypi.org/project/moviepy/)
    - [Kaleido](https://pypi.org/project/kaleido/)
    
- Using Pip:

  ```bash
  pip install vasprocar
  ```

- Manual Installation:

  ```bash
  python manual_installation.py
  ```

- Run Code:

  ```bash
  python -m vasprocar
  ```
------------------------------------------------------------------------
