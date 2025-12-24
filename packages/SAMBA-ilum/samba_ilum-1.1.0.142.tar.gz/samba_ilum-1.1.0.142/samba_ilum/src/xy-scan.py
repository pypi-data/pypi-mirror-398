# SAMBA_ilum Copyright (C) 2025
# GNU GPL-3.0 license


import numpy as np
import shutil
import os


"""
INSERT FUNCTION TO CHECK IF THE INITIAL POSCAR FILE IS WRITTEN IN DIRECT OR CARTESIAN COORDINATES.
IF IT IS WRITTEN IN DIRECT COORDINATES, CONVERT IT TO CARTESIAN COORDINATES.
PERHAPS CREATING A FUNCTION FOR THIS PURPOSE WOULD BE PRACTICAL FOR THE ENTIRE CODE
"""


# Warning: ===================================================================
# The code was written thinking about a Heterostructure with n_Lattice = 2 ===
# For lattices with n_Lattice > 2 tests and generalizations must be made =====
#=============================================================================


displacement_A1 = replace_displacement_A1   # Displacements to be applied to the 2nd material, referring to vector A1 of the lattice
displacement_A2 = replace_displacement_A2   # Displacements to be applied to the 2nd material, referring to the A2 vector of the lattice


"""
#----------------------------------------------------------------
# Testing POSCAR file compatibility -----------------------------
#----------------------------------------------------------------
poscar = open('POSCAR', "r")
VTemp = poscar.readline().split()
poscar.close()
#-------------
crit = 0
for k in range(len(VTemp)):
    try:
       inteiro = int(VTemp[k])
       if (k > 0 and k < 3): crit += 1
    except ValueError:
       if (k == 0):  crit += 1
    #------------------------------
    if (len(VTemp) < 3 or crit < 3):
       print(f' ')
       print(f'========================================')
       print(f'Check the POSCAR file used! ============')
       print(f'INCOMPATIBILITY with code detected =====')
       print(f'========================================')
       print(f' ')
       #==========
       sys.exit()
       #=========
"""


#----------------------------------------------------------------------------
# Function to list all folders within a given directory ---------------------
#----------------------------------------------------------------------------
def list_folders(dir):
   l_folders = [name for name in os.listdir(dir) if os.path.isdir(os.path.join(dir, name))]
   return l_folders


#----------------
dir = os.getcwd()
#--------------------------
folders = list_folders(dir)
#---------------------------------------------------------
for i in range(len(folders)):  shutil.rmtree('folders[i]')
#--------------------------------------------------------------------
# if os.path.isfile('energy_scan.txt'):  os.remove('energy_scan.txt')


#==========================================================================
# Obtaining the Heterostructure Lattice Vectors ===========================
#==========================================================================
poscar = open('POSCAR', "r")
#---------------------------------
line_0 = poscar.readline().split()
if (line_0[-7] == 'Shift_plane'):  shift = str(line_0[-5])
if (line_0[-7] != 'Shift_plane'):  shift = '0.0_0.0'
#-----------------------------------------------
VTemp = poscar.readline();  param = float(VTemp)
VTemp = poscar.readline().split();  A1x = float(VTemp[0]);  A1y = float(VTemp[1]);  A1z = float(VTemp[2])
VTemp = poscar.readline().split();  A2x = float(VTemp[0]);  A2y = float(VTemp[1]);  A2z = float(VTemp[2])
VTemp = poscar.readline().split();  A3x = float(VTemp[0]);  A3y = float(VTemp[1]);  A3z = float(VTemp[2])
#-------------
poscar.close()
#-------------


#==========================================================================
# Generating and Storing POSCAR Files Displaced on the Plane ==============
#==========================================================================
os.mkdir('POSCAR_temp_cart')
#---------
number = 0
#---------
for ii in displacement_A1:
    for jj in displacement_A2:
        #-----------------------------------------------
        displacement_X = (ii*A1x*param) + (jj*A2x*param)
        displacement_Y = (ii*A1y*param) + (jj*A2y*param)
        #-----------------------------------------------
        number += 1
        #---------------------------
        poscar = open('POSCAR', "r")
        poscar_new = open('POSCAR_temp_cart/POSCAR_' + str(number), "w")
        #---------------------------------------------------------------
        VTemp = poscar.readline().split()
        #-----------
        temp_shift = shift.replace('_', ' ').split()
        shift_A1 = float(temp_shift[0]) + float(ii)
        shift_A2 = float(temp_shift[1]) + float(jj)
        for k in range(3):
            if (shift_A1 > 1.0): shift_A1 = shift_A1 -1.0
            if (shift_A2 > 1.0): shift_A2 = shift_A2 -1.0
        if (shift_A1 == 1.0): shift_A1 = 0.0
        if (shift_A2 == 1.0): shift_A2 = 0.0
        new_shift = str(shift_A1) + '_' + str(shift_A2)
        line_0[-5] = new_shift
        #-----------
        for k in range(len(line_0)):  poscar_new.write(f'{line_0[k]} ')
        poscar_new.write(f' \n')
        #----------------------------------------------
        nions1 = int(VTemp[2]);  nions2 = int(VTemp[3])
        #----------------------------------------------
        for k in range(7 + nions1):
            VTemp = poscar.readline()
            poscar_new.write(f'{VTemp}')
        #-------------------------------
        for k in range(nions2):
            VTemp = poscar.readline().split()
            poscar_new.write(f'{float(VTemp[0]) + displacement_X} {float(VTemp[1]) + displacement_Y} {VTemp[2]} \n')
        #-----------------------------------------------------------------------------------------------------------
        poscar.close()
        poscar_new.close()
        #-----------------


#=============================================================================
# Converting POSCAR file coordinates from Cartesian to Direct ================
#=============================================================================

#---------
number = 0
#----------
a = np.array([A1x*param, A1y*param, A1z*param])
b = np.array([A2x*param, A2y*param, A2z*param])
c = np.array([A3x*param, A3y*param, A3z*param])
T = np.linalg.inv(np.array([a, b, c]).T)  # Defining the transformation matrix
#-----------------------------------------------------------------------------

for ii in displacement_A1:
    for jj in displacement_A2:
        #----------
        number += 1
        #---------------------------------
        dir_temp = str(ii) + '_' + str(jj)
        os.mkdir(dir_temp)
        if os.path.isfile('vdw_kernel.bindat'): shutil.copyfile('vdw_kernel.bindat', dir_temp + '/vdw_kernel.bindat')
        shutil.copyfile('contcar_update.py', dir_temp + '/contcar_update.py')
        shutil.copyfile('energy_scan.py', dir_temp + '/energy_scan.py')
        shutil.copyfile('KPOINTS', dir_temp + '/KPOINTS')
        shutil.copyfile('POTCAR', dir_temp + '/POTCAR')
        shutil.copyfile('INCAR', dir_temp + '/INCAR')
        #-----------------------------------------------------------
        poscar = open('POSCAR_temp_cart/POSCAR_' + str(number), "r")
        poscar_new = open(dir_temp + '/POSCAR', "w")
        #-------------------------------------------
        for k in range(7):
            VTemp = poscar.readline()
            poscar_new.write(f'{VTemp}')
        #------------------------
        VTemp = poscar.readline()
        poscar_new.write(f'Direct \n')

        #-----------------------------------------------------------------------------------
        # Converting the Cartesian atomic positions of all atoms in the cell to direct form,
        # and adjusting the positions of atoms outside the cell.
        #-------------------------------------------------------
        for k in range(nions1 + nions2):
            VTemp = poscar.readline().split()
            x = float(VTemp[0])
            y = float(VTemp[1])
            z = float(VTemp[2])
            #----------------------
            r = np.array([x, y, z])        # Defining the Cartesian position vector of the atom
            #----------------------
            f = np.dot(T, r)               # Calculating the corresponding position in fractional coordinates
            for m in range(3):
                f = np.where(f < 0, f + 1, f)
                f = np.where(f > 1, f - 1, f)
            #--------------------------------
            for m in range(3):
                # f[m] = round(f[m], 6)
                if (f[m] > 0.9999 or f[m] < 0.0001):
                   f[m] = 0.0
            poscar_new.write(f'{f[0]} {f[1]} {f[2]} \n')

        #-------------
        poscar.close()
        poscar_new.close()
        #-----------------


# os.remove('POSCAR')
# os.remove('KPOINTS')
# os.remove('POTCAR')
# os.remove('INCAR')

shutil.rmtree('POSCAR_temp_cart')
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       