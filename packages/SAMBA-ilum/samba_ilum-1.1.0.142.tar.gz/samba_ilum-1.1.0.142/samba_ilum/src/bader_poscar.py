# SAMBA_ilum Copyright (C) 2025
# GNU GPL-3.0 license


#---------------------------------------
poscar = open(dir_task + '/POSCAR', 'r')
#---------------------------------------
VTemp = poscar.readline().split()
label_materials = VTemp[1].replace('+', ' ').split()
n_Lattice = len(label_materials);  nions = 0
range_ion_Lattice = []; ntype_ions = ['']*n_Lattice           
#--------------------------------------------------
for m in range(n_Lattice):
    range_ion_Lattice.append( str(1 + nions) + ' ')
    nions += int(VTemp1[m+2])
    range_ion_Lattice[m] += str(nions)
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

os.mkdir(dir_task + '/Charge_transfer')
os.mkdir(dir_task + '/Charge_transfer' + '/inputs')
shutil.copyfile(dir_codes + '/INPUTS/inputs_VASProcar/input.vasprocar.chgcar', dir_task + '/Charge_transfer' + '/inputs' + '/input.vasprocar.chgcar')

#---------------------------------------------------------------------------------------------------------------
# Updating the input.vasprocar.chgcar file ---------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------
with open(dir_task + '/Charge_transfer' + '/inputs/input.vasprocar.chgcar', "r") as file:  content = file.read()
content = content.replace('replace_nfiles', str(n_Lattice +1))
string_temp = f'["CHGCAR_HeteroStructure", '
for m in range(n_Lattice):
    if (m < (n_Lattice -1)):   string_temp += f'"CHGCAR_material_{m +1}", '
    if (m == (n_Lattice -1)):  string_temp += f'"CHGCAR_material_{m +1}"]'
content = content.replace('replace_names', string_temp)
with open(dir_task + '/Charge_transfer' + '/inputs/input.vasprocar.chgcar', "w") as file: file.write(content)
#------------------------------------------------------------------------------------------------------------ 

os.mkdir(dir_task + '/HeteroStructure')
os.mkdir(dir_task + '/HeteroStructure' + '/inputs')
shutil.copyfile(dir_codes + '/INPUTS/inputs_VASProcar/input.vasprocar.locpot', dir_task + '/HeteroStructure' + '/inputs' + '/input.vasprocar.locpot')
shutil.copyfile(dir_task + '/POSCAR', dir_task + '/HeteroStructure' + '/POSCAR')

for m in range(n_Lattice):
    os.mkdir(dir_task + '/material_' + str(m+1))
    os.mkdir(dir_task + '/material_' + str(m+1) + '/inputs')
    shutil.copyfile(dir_codes + '/INPUTS/inputs_VASProcar/input.vasprocar.locpot', dir_task + '/material_' + str(m+1) + '/inputs/input.vasprocar.locpot')
    #----------------------------------------------------------------------------------------------------------------------------------------------------
    poscar = open(dir_task + '/POSCAR', 'r')
    poscar_new = open(dir_task + '/material_' + str(m+1) + '/POSCAR', 'w')
    #---------------------------------------------------------------------
    VTemp = poscar.readline()
    poscar_new.write(f'POSCAR \n')
    #-----------------------------
    for n in range(4):
        VTemp = poscar.readline()
        poscar_new.write(f'{VTemp}')
    #-------------------------------
    VTemp = poscar.readline()
    temp = label_materials[m].replace('_', ' ')
    poscar_new.write(f'{temp} \n')
    #------------------------------------------
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
    for n in range(1,(nions+1)):
        VTemp = poscar.readline()
        if (n >= ion_i and n <= ion_f):  poscar_new.write(f'{VTemp}')
    #----------------------------------------------------------------
    poscar.close()
    poscar_new.close()
    #-----------------