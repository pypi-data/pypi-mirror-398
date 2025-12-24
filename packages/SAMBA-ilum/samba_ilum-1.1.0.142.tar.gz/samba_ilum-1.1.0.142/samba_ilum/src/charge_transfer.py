# SAMBA_ilum Copyright (C) 2025
# GNU GPL-3.0 license


import numpy as np


#---------------------------
poscar = open('POSCAR', 'r')
VTemp = poscar.readline().split()
#-------------------------------------------------------------------------------------
# Obtaining the label and number of atoms for each material in the Heterostructure ---
#-------------------------------------------------------------------------------------
label_materials = VTemp[1].replace('+', ' ').replace('_', '').split()
n_Lattice = len(label_materials)
n_ions_material = [0]*n_Lattice;  n_ions = 0
for ii in range(n_Lattice):
    n_ions_material[ii] = int(VTemp[ii+2])
    n_ions += int(VTemp[ii+2])
#-----------------------------

#--------------------------------------------------------------
# Obtaining the Area in the XY Plane of the Heterostructure ---
#--------------------------------------------------------------
VTemp = poscar.readline();  param = float(VTemp)
#-----------------------------------------------
A1 = poscar.readline().split();  A1x = float(A1[0])*param; A1y = float(A1[1])*param; A1z = float(A1[2])*param
A2 = poscar.readline().split();  A2x = float(A2[0])*param; A2y = float(A2[1])*param; A2z = float(A2[2])*param
A3 = poscar.readline().split();  A3x = float(A3[0])*param; A3y = float(A3[1])*param; A3z = float(A3[2])*param
#------------------------------------------------------------------------------------------------------------
A1 = np.array([A1x, A1y])
A2 = np.array([A2x, A2y])
#------------------------
# Cell area
Area = np.linalg.norm(np.cross(A1, A2))
Area = Area*(1e-16)  # Converting from Å^2 to cm^2
#-------------------------------------------------

#--------------------------------------------------------------------------------
# Obtaining the label and number of atoms for each type of ion in the lattice ---
#--------------------------------------------------------------------------------
VTemp = poscar.readline().split()
label_ions = ['a']*len(VTemp)
for ii in range(len(VTemp)):  label_ions[ii] = str(VTemp[ii])
#------------------------------------------------------------
VTemp = poscar.readline().split()
range_ions = [0]*len(VTemp)
for ii in range(len(VTemp)):  range_ions[ii] = int(VTemp[ii])
#------------------------------------------------------------
poscar.close()
#-------------



#-----------------------------------------------
bader_0   = open('HeteroStructure/ACF.dat', "r")
#------------------------------------------------------------------------------
acf_files = {}  # Creating a dictionary to store the ACF_material_'i'.dat files
for ii in range(n_Lattice):  acf_files[f'{ii}'] = open('material_' + str(ii+1) + '/ACF.dat', "r")
#------------------------------------------------------------------------------------------------

material_transfer = [0.0]*n_Lattice
ion_transfer = [0.0]*len(label_ions)

for ii in range(2):
    VTemp0 = bader_0.readline()
    for ij in range(n_Lattice):  VTemp = acf_files[f'{ij}'].readline()

#----------------------
number_ion = 0; ion = 0
#--------------------------
for ii in range(n_Lattice):
    for ij in range(n_ions_material[ii]):
        #----------------------------------
        VTemp0 = bader_0.readline().split()
        VTemp1 = acf_files[f'{ii}'].readline().split()
        shift_charge = float(VTemp0[4]) - float(VTemp1[4])
        material_transfer[ii] += shift_charge
        #------------------------------------
        number_ion += 1
        if (number_ion > range_ions[ion]):
           ion += 1;  number_ion = 1 
        ion_transfer[ion] += shift_charge
        #--------------------------------

#--------------
bader_0.close()
for file in acf_files.values():  file.close()
#--------------------------------------------



#--------
ion_f = 0
charger = open('Charge_transfer/Bader_charge_transfer.dat', "w")
#---------------------------------------------------------------

#--------------------
charger.write(f' \n')
charger.write(f'======================================= \n')
charger.write(f'total charge transfer: ================ \n')
charger.write(f'Area (XY plane): {Area:.6} cm^2 \n')
charger.write(f'======================================= \n')
#--------------------------
for ii in range(n_Lattice):
    #------------------------------------------------------------------------------------------------------
    charger.write(f'material_{ii+1} ({label_materials[ii]}): {(material_transfer[ii]/Area):.6e} e/cm^2 \n')
    #------------------------------------------------------------------------------------------------------
    ion_i = ion_f;  ion_f += n_ions_material[ii]
    #-------------------------------------------
    number_ion = 0
    #-------------
    for ij in range(len(label_ions)):
        number_ion += range_ions[ij]
        if (number_ion > ion_i and number_ion <= ion_f):
           charger.write(f'{label_ions[ij]} charge transfer: {(ion_transfer[ij]/Area):.6e} e/cm^2 \n')
    charger.write(f'======================================= \n')
#--------------------
charger.write(f' \n')
#--------------------

#-----------------------------------------------
bader_0   = open('HeteroStructure/ACF.dat', "r")
#------------------------------------------------------------------------------
acf_files = {}  # Creating a dictionary to store the ACF_material_'i'.dat files
for ii in range(n_Lattice):  acf_files[f'{ii}'] = open('material_' + str(ii+1) + '/ACF.dat', "r")
#------------------------------------------------------------------------------------------------

for ii in range(2):
    VTemp0 = bader_0.readline()
    for ij in range(n_Lattice):  VTemp = acf_files[f'{ij}'].readline()

charger.write(f'    #         X            Y            Z         CHARGE      MIN DIST    ATOMIC VOL \n')
charger.write(f' ----------------------------------------------------------------------------------- \n')

#------------------
charge_transfer = 0
#-----------------------
for ii in range(n_Lattice):
    for ij in range(n_ions_material[ii]):
        #----------------------------------
        VTemp0 = bader_0.readline().split()
        VTemp1 = acf_files[f'{ii}'].readline().split()
        shift_charge = float(VTemp0[4]) - float(VTemp1[4])
        charge_transfer += shift_charge
        #---------------------------------------------------------------------------------------------------------------------
        charger.write(f'{int(VTemp1[0]):>5} {float(VTemp1[1]):12,.6f} {float(VTemp1[2]):12,.6f} {float(VTemp1[3]):12,.6f} ')
        charger.write(f'{shift_charge:12,.6f} {float(VTemp1[5]):12,.6f} {float(VTemp1[6]):12,.6f} \n')

for ii in range(4):
    VTemp = bader_0.readline()
    charger.write(f'{VTemp}')
charger.write(f'    CHARGE TRANSFER:            {charge_transfer:.6e} \n')
charger.write(f' ----------------------------------------------------------------------------------- \n')

#--------------
charger.close()
bader_0.close()
for file in acf_files.values():  file.close()
#--------------------------------------------
