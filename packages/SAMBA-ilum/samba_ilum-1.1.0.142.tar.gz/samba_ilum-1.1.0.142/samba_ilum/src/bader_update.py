# SAMBA_ilum Copyright (C) 2025
# GNU GPL-3.0 license


import shutil


#---------------------------
poscar = open('POSCAR', 'r')
#--------------------------------
VTemp = poscar.readline().split()
label_materials = VTemp[1].replace('+', ' ').split()
n_Lattice = len(label_materials);  nion = 0
range_ion_Lattice = []; ntype_ions = ['']*n_Lattice           
#--------------------------------------------------
for m in range(n_Lattice):
    range_ion_Lattice.append( str(1 + nion) + ' ')
    nion += int(VTemp[m+2])
    range_ion_Lattice[m] += str(nion)
#----------------------------------------------------
for m in range(6):  VTemp = poscar.readline().split()
#----------------------------------------------------
poscar.close()
#-------------
for m in range(n_Lattice):
    contador = 0
    for n in range(len(VTemp)):
        contador += int(VTemp[n])
        range_ion = range_ion_Lattice[m].split()
        ion_i = int(range_ion[0]);  ion_f = int(range_ion[1])
        if (contador >= ion_i and contador <= ion_f):
           ntype_ions[m] += str(VTemp[n]) + ' '

#================================================================================

shutil.copyfile('POSCAR', 'HeteroStructure' + '/POSCAR')

for m in range(n_Lattice):
    #---------------------------
    poscar = open('POSCAR', 'r')
    poscar_new = open('material_' + str(m+1) + '/POSCAR', 'w')
    #---------------------------------------------------------
    VTemp = poscar.readline()
    poscar_new.write(f'POSCAR \n')
    #-----------------------------
    for n in range(4):
        VTemp = poscar.readline()
        poscar_new.write(f'{VTemp}')
    #-------------------------------
    print(label_materials)
    VTemp = poscar.readline()
    temp = label_materials[m].replace('_', ' ')
    poscar_new.write(f'{temp} \n')
    #-----------------------------
    VTemp = poscar.readline()
    poscar_new.write(f'{ntype_ions[m]} \n')
    #--------------------------------------
    VTemp = poscar.readline()
    if (VTemp[0] == 'c' or VTemp[0] == 'C'): poscar_new.write(f'Cartesian \n')
    if (VTemp[0] == 'd' or VTemp[0] == 'D'): poscar_new.write(f'Direct \n')
    #---------------------------------------
    range_ion = range_ion_Lattice[m].split()
    ion_i = int(range_ion[0]);  ion_f = int(range_ion[1])
    #----------------------------------------------------
    for n in range(1,(nion+1)):
        VTemp = poscar.readline()
        if (n >= ion_i and n <= ion_f):  poscar_new.write(f'{VTemp}')
    #----------------------------------------------------------------
    poscar.close()
    poscar_new.close()
    #-----------------