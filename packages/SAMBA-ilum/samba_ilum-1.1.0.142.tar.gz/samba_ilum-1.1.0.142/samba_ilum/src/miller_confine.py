# SAMBA_ilum Copyright (C) 2025
# GNU GPL-3.0 license


import ase
from ase.build import surface
from ase.io import read
#==================================
from pymatgen.io.vasp import Poscar
from pymatgen.core import Structure
from pymatgen.analysis.structure_matcher import StructureMatcher
#===============================================================
import os


print ("###############################################################")
print ("## Type the name of the POSCAR/CONTCAR file to be confined:  ##")
print ("###############################################################") 
name = input ("name: "); name = str(name)
poscar_file = dir_files + '/' + name
print (" ")

print ("###############################################################")
print ("## Type the Miller indices (hkl) of the plane perpendicular  ##")
print ("##                            to the confinement direction:  ##")
print ("## --------------------------------------------------------  ##")
print ("## example: 1 1 0                                            ##")
print ("###############################################################") 
miller_indices = input ("Miller indices: "); miller_indices = str(miller_indices).split( )
direction = [int(miller_indices[0]), int(miller_indices[1]), int(miller_indices[2])]
print (" ")

print ("###############################################################")
print ("## Type the number of layers (multiple of the number of bulk ##")
print ("##                     layers in the confinement direction): ##")
print ("###############################################################") 
n_layers = input ("Number of layers: "); n_layers = int(n_layers)
print (" ")

print ("###############################################################")
print ("## Type the vacuum to be introduced (in Angstroms):          ##")
print ("###############################################################") 
vacuum = input ("Vacuum: "); vacuum = float(vacuum)
print (" ")


#==========================================================
# Contruindo o sistema confinado ==========================
#==========================================================
str_dir = ''
for i in direction: str_dir += str(i)
file_out = dir_files + '/temp.vasp'
#==========================================================
def build_nlayer(poscar_file, n_layers, direction, vacuum):
    surface = ase.build.surface(poscar_file,direction,n_layers,vacuum=vacuum)
    ase.io.vasp.write_vasp(file_out,surface,direct=False,sort=True)
#=========================
poscar = read(poscar_file)
build_nlayer(poscar, n_layers, direction, vacuum)


#===========================================================================
# Verificando a possibilidade de obtenção de uma célula de menor tamanho ===
#===========================================================================
structure = Poscar.from_file(file_out).structure
matcher = StructureMatcher()
reduced_structure = matcher._get_reduced_structure(structure)
Poscar(reduced_structure).write_file(dir_files + '/Slab_' + str(str_dir) + '_' + str(n_layers) + 'layers.vasp')
os.remove(file_out)
