# SAMBA_ilum Copyright (C) 2025
# GNU GPL-3.0 license


import numpy as np
import shutil
import os


# Warning: ===================================================================
# The code was written thinking about a Heterostructure with n_Lattice = 2 ===
# For lattices with n_Lattice > 2 tests and generalizations must be made =====
#=============================================================================


vacuo = replace_vacuo    # Minimum vacuum applied to heterostructure
z_scan = replace_zscan   # Z-axis separation to be applied between Heterostructure materials
displacement_A1 = replace_displacement_xyz_A1   # Displacements to be applied to the 2nd material, referring to vector A1 of the lattice
displacement_A2 = replace_displacement_xyz_A2   # Displacements to be applied to the 2nd material, referring to vector A2 of the lattice


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


#==========================================================================
# Obtaining the Heterostructure Lattice Vectors ===========================
#==========================================================================
contcar = open('CONTCAR', "r")
#-----------------------------
VTemp = contcar.readline()
VTemp = contcar.readline();  param = float(VTemp)
VTemp = contcar.readline().split();  A1x = float(VTemp[0]);  A1y = float(VTemp[1]);  A1z = float(VTemp[2])
VTemp = contcar.readline().split();  A2x = float(VTemp[0]);  A2y = float(VTemp[1]);  A2z = float(VTemp[2])
VTemp = contcar.readline().split();  A3x = float(VTemp[0]);  A3y = float(VTemp[1]);  A3z = float(VTemp[2])
#--------------
contcar.close()
#--------------


#==========================================================================
# Getting the z-axis height of different materials ========================
#==========================================================================
contcar = open('CONTCAR', "r")
#--------------------------------
VTemp = contcar.readline().split()
n_Lattice = len(VTemp[1].replace('+', ' ').split())
nions_Lattice = []
for m in range(n_Lattice):  nions_Lattice.append(int(VTemp[m+2]))  
#----------------------------------------------------------------
VTemp = contcar.readline();  param = float(VTemp)
#----------------------------------------------------
for k in range(3): VTemp = contcar.readline().split()
fator_Z = float(VTemp[2])*param
#--------------------------------------------
for k in range(3): VTemp = contcar.readline()
#--------------------------------------------------------------
minZ = [0]*n_Lattice;  dZ = [0]*(n_Lattice +1);  dZ_total = 0.0
#--------------------------------------------------------------
for k in range(n_Lattice):
    vZ = []
    for m in range(nions_Lattice[k]):
        VTemp = contcar.readline().split()
        vZ.append(float(VTemp[2]))
    #-----------------------------
    dZ[k+1] = (max(vZ) - min(vZ))
    dZ_total += dZ[k+1]*fator_Z
    minZ[k] = min(vZ)
#--------------------
contcar.close()
#--------------


#==========================================================================
# Moving materials to Z = 0.0 =============================================
#==========================================================================
contcar = open('CONTCAR', "r")
poscar_new = open('POSCAR_temp', "w")
#------------------------------------
for k in range(8):
    VTemp = contcar.readline()
    poscar_new.write(f'{VTemp}')
for k in range(n_Lattice):
    for m in range(nions_Lattice[k]):
        VTemp = contcar.readline().split()
        temp_z = float(VTemp[2]) -minZ[k] +dZ[k]
        if (temp_z < 0.0):  temp_z = 0.0
        poscar_new.write(f'{float(VTemp[0])} {float(VTemp[1])} {temp_z} \n')
#-------------
contcar.close()
poscar_new.close()
#-----------------


#===========================================================
# Converting coordinates to Cartesian form =================
#===========================================================
poscar = open('POSCAR_temp', "r")
poscar_new = open('POSCAR_cart', "w")
VTemp = poscar.readline();  poscar_new.write(f'{VTemp}')
VTemp = poscar.readline();  poscar_new.write(f'{VTemp}')
VTemp = poscar.readline();  poscar_new.write(f'{VTemp}');  VTemp = VTemp.split();  A = [float(VTemp[0]), float(VTemp[1]), float(VTemp[2])]  
VTemp = poscar.readline();  poscar_new.write(f'{VTemp}');  VTemp = VTemp.split();  B = [float(VTemp[0]), float(VTemp[1]), float(VTemp[2])]
VTemp = poscar.readline();  poscar_new.write(f'{VTemp}');  VTemp = VTemp.split();  C = [float(VTemp[0]), float(VTemp[1]), float(VTemp[2])]
VTemp = poscar.readline();  poscar_new.write(f'{VTemp}')
VTemp = poscar.readline();  poscar_new.write(f'{VTemp}')
VTemp = poscar.readline();  poscar_new.write(f'Cartesian \n')
#------------------------------------------------------------
# Writing Cartesian coordinates -----------------------------
#------------------------------------------------------------
for k in range(n_Lattice):
    for m in range(nions_Lattice[k]):
        VTemp = poscar.readline().split()
        k1 = float(VTemp[0]); k2 = float(VTemp[1]); k3 = float(VTemp[2])
        coord_x = ((k1*A[0]) + (k2*B[0]) + (k3*C[0]))
        coord_y = ((k1*A[1]) + (k2*B[1]) + (k3*C[1]))
        coord_z = ((k1*A[2]) + (k2*B[2]) + (k3*C[2]))
        poscar_new.write(f'{coord_x:>28,.21f} {coord_y:>28,.21f} {coord_z:>28,.21f} \n')
#-------------
poscar.close()   
poscar_new.close()
#-----------------


for z in range(len(z_scan)):
    #-----------------
    deltaZ = z_scan[z]
    #-----------------

    #===========================================================
    # Generating POSCAR files for each Z separation ============
    #===========================================================
    poscar = open('POSCAR_cart', "r")
    poscar_new = open('POSCAR_deltaZ', "w")
    VTemp = poscar.readline();  poscar_new.write(f'{VTemp}')
    VTemp = poscar.readline();  poscar_new.write(f'{VTemp}')
    VTemp = poscar.readline();  poscar_new.write(f'{VTemp}');  VTemp = VTemp.split();  A = [float(VTemp[0]), float(VTemp[1]), float(VTemp[2])]
    VTemp = poscar.readline();  poscar_new.write(f'{VTemp}');  VTemp = VTemp.split();  B = [float(VTemp[0]), float(VTemp[1]), float(VTemp[2])]
    VTemp = poscar.readline().split();  C = [float(VTemp[0]), float(VTemp[1]), float(VTemp[2])]
    #---------------------------------------------
    # temp_Z = (dZ_total + deltaZ_f + vacuo)/param
    temp_Z = (dZ_total + deltaZ + vacuo)/param;  A3z = temp_Z
    poscar_new.write(f'{float(VTemp[0]):>28,.21f} {float(VTemp[1]):>28,.21f} {float(temp_Z):>28,.21f} \n')
    #-----------------------------------------------------------------------------------------------------
    VTemp = poscar.readline();  poscar_new.write(f'{VTemp}')
    VTemp = poscar.readline();  poscar_new.write(f'{VTemp}')
    VTemp = poscar.readline();  poscar_new.write(f'Cartesian \n')
    #------------------------------------------------------------
    for k in range(n_Lattice):
        for m in range(nions_Lattice[k]):
            VTemp = poscar.readline().split()
            coord_x = float(VTemp[0]); coord_y = float(VTemp[1]); coord_z = float(VTemp[2])
            #-------------------------------------------------------------------------------
            coord_z = coord_z + (vacuo/2)
            if (k > 0):  coord_z = coord_z + deltaZ
            poscar_new.write(f'{coord_x:>28,.21f} {coord_y:>28,.21f} {coord_z:>28,.21f} \n')
            #-------------------------------------------------------------------------------
    #-------------
    poscar.close()   
    poscar_new.close()
    #-----------------


    #==========================================================================
    # Generating and Storing POSCAR Files Displaced on the Plane ==============
    #==========================================================================
    os.mkdir('POSCAR_temp_cart')
    #---------------------------
    number = 0
    #---------
    for ii in displacement_A1:
        for jj in displacement_A2:
            #-----------------------------------------------
            displacement_X = (ii*A1x*param) + (jj*A2x*param)        
            displacement_Y = (ii*A1y*param) + (jj*A2y*param)   
            #-----------------------------------------------
            number += 1
            #---------------------------------
            poscar = open('POSCAR_deltaZ', "r")
            poscar_new = open('POSCAR_temp_cart/POSCAR_' + str(number), "w") 
            #---------------------------------------------------------------
            VTemp = poscar.readline()
            poscar_new.write(f'{VTemp}')
            VTemp = VTemp.split()
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
            dir_temp = str(ii) + '_' + str(jj) + '_' + str(deltaZ)
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
    #------------------------
    os.remove('POSCAR_deltaZ')
    shutil.rmtree('POSCAR_temp_cart')
#------------------------------------
os.remove('POSCAR_temp')
os.remove('POSCAR_cart')
#-----------------------
