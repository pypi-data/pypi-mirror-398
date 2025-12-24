# SAMBA_ilum Copyright (C) 2025
# GNU GPL-3.0 license


import numpy as np
import shutil
import os


# Warning: ===================================================================
# The code was written thinking about a Heterostructure with n_Lattice = 2 ===
# For lattices with n_Lattice > 2 tests and generalizations must be made =====
#=============================================================================


vacuo = replace_vacuo       # Minimum vacuum applied to heterostructure


#----------------------------------------------------------------------------
# Function to list all folders within a given directory ---------------------
#----------------------------------------------------------------------------
def list_folders(dir):
   l_folders = [name for name in os.listdir(dir) if os.path.isdir(os.path.join(dir, name))]
   return l_folders
#----------------
dir = os.getcwd()
#----------------


#==================================================
# Checking the current calculation step ===========
#==================================================
file = open('check_steps.txt', "r")
VTemp = file.readline()
step = int(VTemp)
file.close()
#-----------
passo = 1.0/(2**(step-1))
#------------------------


if (step == 1):
   #-------------------------------------------------------------
   z_scan = [1.0, 2.0, 3.0, 4.0, 5.0, 7.0, 9.0, 11.0, 13.0, 15.0]
   #-------------------------------------------------------------
   folders = list_folders(dir)
   for i in range(len(folders)):  shutil.rmtree('folders[i]')
   if os.path.isfile('energy_scan.txt'):  os.remove('energy_scan.txt')
   #------------------------------------------------------------------
if (step > 1):
   #------------------------------------
   file0 = np.loadtxt('energy_scan.txt')
   file0.shape
   #-------------------
   date_z   = file0[:,0]
   date_E   = file0[:,1]
   #---------------------------
   line_min = np.argmin(date_E)
   delta_z  = date_z[line_min]
   #--------------------------
   passo_i = delta_z -passo
   passo_f = delta_z +passo
   z_scan = [passo_i, passo_f]
   #--------------------------


#==========================================================================
# Getting the z-axis height of different materials ========================
#==========================================================================
contcar = open('CONTCAR', "r")
#---------------------------------
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
#----------------
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
#-------------i
contcar.close()
poscar_new.close()
#-----------------


#===========================================================
# Converting coordinates to Cartesian form =================
#===========================================================
poscar = open('POSCAR_temp', "r")
poscar_new = open('POSCAR_cart', "w")
VTemp = poscar.readline();  poscar_new.write(f'{VTemp}')
VTemp = poscar.readline();  poscar_new.write(f'{VTemp}');  param = float(VTemp)
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


#===========================================================
# Generating POSCAR files for each Z separation ============
#===========================================================
for deltaZ in z_scan:
    os.mkdir(str(deltaZ))
    if os.path.isfile('vdw_kernel.bindat'): shutil.copyfile('vdw_kernel.bindat', str(deltaZ) + '/vdw_kernel.bindat')
    shutil.copyfile('contcar_update.py', str(deltaZ) + '/contcar_update.py')
    shutil.copyfile('energy_scan.py', str(deltaZ) + '/energy_scan.py')
    shutil.copyfile('KPOINTS', str(deltaZ) + '/KPOINTS')
    shutil.copyfile('POTCAR', str(deltaZ) + '/POTCAR')
    shutil.copyfile('INCAR', str(deltaZ) + '/INCAR')
    #-----------------------------------------------
    poscar = open('POSCAR_cart', "r")
    poscar_new = open(str(deltaZ) + '/POSCAR', "w")
    VTemp = poscar.readline();  poscar_new.write(f'{VTemp}')
    VTemp = poscar.readline();  poscar_new.write(f'{VTemp}');  param = float(VTemp)
    VTemp = poscar.readline();  poscar_new.write(f'{VTemp}');  VTemp = VTemp.split();  A = [float(VTemp[0]), float(VTemp[1]), float(VTemp[2])]
    VTemp = poscar.readline();  poscar_new.write(f'{VTemp}');  VTemp = VTemp.split();  B = [float(VTemp[0]), float(VTemp[1]), float(VTemp[2])]
    VTemp = poscar.readline().split();  C = [float(VTemp[0]), float(VTemp[1]), float(VTemp[2])]
    #---------------------------------------------
    # temp_Z = (dZ_total + deltaZ_f + vacuo)/param
    temp_Z = (dZ_total + deltaZ + vacuo)/param
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


#-----------------------
os.remove('POSCAR_temp')
os.remove('POSCAR_cart')
#-----------------------
