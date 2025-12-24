# SAMBA_ilum Copyright (C) 2025
# GNU GPL-3.0 license


import numpy as np
import shutil
import os


vacuo = replace_vacuo             # Minimum vacuum applied to heterostructure
factor_var = replace_factor_var   # Percentage change in network parameter (modulo the smallest lattice vector)


#----------------------------------------------------------------------------
# Function to list all folders within a given directory ---------------------
#----------------------------------------------------------------------------
def list_folders(dir):
   l_folders = [name for name in os.listdir(dir) if os.path.isdir(os.path.join(dir, name))]
   return l_folders
#----------------
dir = os.getcwd()
#----------------


#==========================================================================
# Obtaining the Heterostructure Lattice Vectors ===========================
#==========================================================================
contcar = open('CONTCAR', "r")
#-----------------------------
VTemp = contcar.readline()
VTemp = contcar.readline();  param = float(VTemp)
VTemp = contcar.readline().split();  A1x = float(VTemp[0])*param;  A1y = float(VTemp[1])*param;  A1z = float(VTemp[2])*param
VTemp = contcar.readline().split();  A2x = float(VTemp[0])*param;  A2y = float(VTemp[1])*param;  A2z = float(VTemp[2])*param
VTemp = contcar.readline().split();  A3x = float(VTemp[0])*param;  A3y = float(VTemp[1])*param;  A3z = float(VTemp[2])*param
VTemp = contcar.readline()
VTemp = contcar.readline().split(); nions = 0
for i in np.arange(len(VTemp)):
    nions += int(VTemp[i])
#--------------
contcar.close()
#--------------


#=====================================================================================
# Adopting the lattice parameter as the modulus of the smallest lattice vector =======
#=====================================================================================
A1 = np.array([float(A1x), float(A1y), float(A1z)]);  module_a1 = float(np.linalg.norm(A1))
A2 = np.array([float(A2x), float(A2y), float(A2z)]);  module_a2 = float(np.linalg.norm(A2))
A3 = np.array([float(A3x), float(A3y), float(A3z)]);  module_a3 = float(np.linalg.norm(A3))
#------------------------------------------------------------------------------------------
if (module_a1 <= module_a2):
   param  = module_a1
   vector = 'A1'
if (module_a2 < module_a1):
   param  = module_a2
   vector = 'A2'
# if ((type_lattice = 3) and (module_a3 < module_a1) or (module_a3 < module_a2)):
#    param  = module_a3
#    vector = 'A3'
#--------------------------------------------------
A1x = A1x/param;  A1y = A1y/param;  A1z = A1z/param
A2x = A2x/param;  A2y = A2y/param;  A2z = A2z/param
A3x = A3x/param;  A3y = A3y/param;  A3z = A3z/param
#--------------------------------------------------


#===================================================
# Checking the current calculation step ============
#===================================================
file = open('check_steps.txt', "r")
VTemp = file.readline()
step = int(VTemp)
file.close()
#---------------------------------------------
passo = (param*(factor_var/100))/(2**(step-1))
#---------------------------------------------


if (step == 1):
   #-----------------------------------------------
   a_scan = [(param -passo), param, (param +passo)]
   #-----------------------------------------------
   folders = list_folders(dir)
   for i in range(len(folders)):  shutil.rmtree('folders[i]')
   if os.path.isfile('energy_scan.txt'):  os.remove('energy_scan.txt')
   #------------------------------------------------------------------
if (step > 1):
   #------------------------------------
   file0 = np.loadtxt('energy_scan.txt')
   file0.shape
   #-------------------
   date_a   = file0[:,0]
   date_E   = file0[:,1]
   #---------------------------
   line_min = np.argmin(date_E)
   param_new  = date_a[line_min]
   #----------------------------
   passo_i = param_new -passo
   passo_f = param_new +passo
   a_scan = [passo_i, passo_f]
   #--------------------------


#============================================================
# Generating POSCAR files for each value of a (param) =======
#============================================================

for param in a_scan:

    #---------------------------------------------
    dir_temp = str(param);  os.mkdir(dir_temp)
    if os.path.isfile('vdw_kernel.bindat'): shutil.copyfile('vdw_kernel.bindat', dir_temp + '/vdw_kernel.bindat')
    shutil.copyfile('contcar_update.py', dir_temp + '/contcar_update.py')
    shutil.copyfile('energy_scan.py', dir_temp + '/energy_scan.py')
    shutil.copyfile('KPOINTS', dir_temp + '/KPOINTS')
    shutil.copyfile('POTCAR', dir_temp + '/POTCAR')
    shutil.copyfile('INCAR', dir_temp + '/INCAR')
    #--------------------------------------------
    contcar = open('CONTCAR', "r")
    poscar_new = open(dir_temp + '/POSCAR_temp', "w") 
    VTemp = contcar.readline();  poscar_new.write(f'{VTemp}')
    VTemp = contcar.readline();  poscar_new.write(f'{param} \n')
    #--------------------------------------------------------
    VTemp = contcar.readline().split();  poscar_new.write(f'{A1x} {A1y} {A1z} \n')
    VTemp = contcar.readline().split();  poscar_new.write(f'{A2x} {A2y} {A2z} \n')
    VTemp = contcar.readline().split();  poscar_new.write(f'{A3x} {A3y} {A3z} \n')
    #-----------------------------------------------------------------------------
    VTemp = contcar.readline();  poscar_new.write(f'{VTemp}')
    VTemp = contcar.readline();  poscar_new.write(f'{VTemp}')
    VTemp = contcar.readline();  poscar_new.write(f'Cartesian \n')
    #-------------------------------------------------------------
    temp_z = []
    for j in np.arange(nions):
        VTemp = contcar.readline().split()
        coord_x = ((float(VTemp[0])*A1x) + (float(VTemp[1])*A2x) + (float(VTemp[2])*A3x))
        coord_y = ((float(VTemp[0])*A1y) + (float(VTemp[1])*A2y) + (float(VTemp[2])*A3y))
        coord_z = ((float(VTemp[0])*A1z) + (float(VTemp[1])*A2z) + (float(VTemp[2])*A3z))
        temp_z.append(coord_z)
        poscar_new.write(f'{coord_x:>28,.21f} {coord_y:>28,.21f} {coord_z:>28,.21f} \n')
    #--------------
    contcar.close()   
    poscar_new.close()
    #-----------------

    #---------------------------------
    delta_z = max(temp_z) -min(temp_z)
    z_min = min(temp_z)
    #---------------------------------
    poscar = open(dir_temp + '/POSCAR_temp', "r")
    poscar_new = open(dir_temp + '/POSCAR', "w") 
    VTemp = poscar.readline();  poscar_new.write(f'{VTemp}')
    VTemp = poscar.readline();  poscar_new.write(f'{param} \n')
    #----------------------------------------------------------
    VTemp = poscar.readline().split();  poscar_new.write(f'{A1x} {A1y} {A1z} \n')
    VTemp = poscar.readline().split();  poscar_new.write(f'{A2x} {A2y} {A2z} \n')
    VTemp = poscar.readline().split();  poscar_new.write(f'0.0 0.0 {delta_z + (vacuo/param)} \n')
    #--------------------------------------------------------------------------------------------
    VTemp = poscar.readline();  poscar_new.write(f'{VTemp}')
    VTemp = poscar.readline();  poscar_new.write(f'{VTemp}')
    VTemp = poscar.readline();  poscar_new.write(f'Cartesian \n')
    #------------------------------------------------------------
    temp_z = []
    for j in np.arange(nions):
        VTemp = poscar.readline().split()
        coord_x = float(VTemp[0])
        coord_y = float(VTemp[1])
        coord_z = float(VTemp[2]) -z_min + ((vacuo/2)/param)
        temp_z.append(temp_z)
        poscar_new.write(f'{coord_x:>28,.21f} {coord_y:>28,.21f} {coord_z:>28,.21f} \n')
    #--------------
    poscar.close()   
    poscar_new.close()
    #-----------------

    #-----------------------------------
    os.remove(dir_temp + '/POSCAR_temp')
    #-----------------------------------
