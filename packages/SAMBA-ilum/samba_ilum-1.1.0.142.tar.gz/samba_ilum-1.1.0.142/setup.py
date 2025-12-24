from distutils.core import setup
from setuptools import setup, find_packages
from pathlib import Path
from typing import Optional
import json

setup(
    name = "SAMBA_ilum",
    version = "1.1.0.142",
    entry_points={'console_scripts': ['samba_ilum = samba_ilum:main']},
    description = "The SAMBA code is an open-source, high-throughput Python workflow for generating, simulating, and analyzing twisted bilayers. It features modules for: (i) creating thousands of quasi-commensurate structures via the coincidence lattice method; (ii) assist in the running DFT calculations using VASP; and (iii) extracting and organizing structural, electronic, and energetic properties into a robust dataset.",
    author = "Augusto de Lelis Araujo", 
    author_email = "augusto-lelis@outlook.com",
    license = "GNU General Public License v3.0",
    install_requires=['matplotlib',
                      'pymatgen',
                      'pyfiglet',
                      'requests',
                      'plotly',
                      'scipy',
                      'numpy',
                      'uuid',
                      'ase',
                      'vasprocar'],
    package_data={"": ['*.dat', '*.png', '*.jpg', '*']},
)

# python3 -m pip install --upgrade twine
# python setup.py sdist
# python -m twine upload dist/*