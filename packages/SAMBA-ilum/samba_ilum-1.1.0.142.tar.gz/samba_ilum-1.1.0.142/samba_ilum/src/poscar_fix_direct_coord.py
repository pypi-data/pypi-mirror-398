# SAMBA_ilum Copyright (C) 2025
# GNU GPL-3.0 license


import numpy as np
import shutil
import uuid
import hashlib
import json
import glob
import sys
import os


#------------------------------------------------------
# Function to delete hidden files ---------------------
#------------------------------------------------------
def delete_hidden_files(target_directory):
    search_files = os.path.join(target_directory, '.*')
    for item in glob.glob(search_files):
        try:
            if os.path.isfile(item): os.remove(item)
        except OSError: pass


#------------------------------------------------------
# Listing files inside the "dir_files_in" directory ---
#------------------------------------------------------
poscar_dir_path = os.path.join(dir_files, dir_files_in)
#-----------------------------------
delete_hidden_files(poscar_dir_path)
files0 = [name for name in os.listdir(poscar_dir_path) if os.path.isfile(os.path.join(poscar_dir_path, name))]


#======================================================
# Checking/Correcting POSCAR files ====================
#======================================================
poscar_backup_dir_path = os.path.join(dir_files, 'POSCAR_Backup_temp')
os.rename(poscar_dir_path, poscar_backup_dir_path)
os.makedirs(poscar_dir_path, exist_ok=True)
#------------------------------------------
files1 = [name for name in os.listdir(poscar_backup_dir_path) if os.path.isfile(os.path.join(poscar_backup_dir_path, name))]
for file_in in files1:
    #-----------------------------------------------
    file_out = file_in.replace(".vasp","") + '.vasp'
    #-----------------------------------------------
    type_poscar = 'none'
    poscar_in  = open(poscar_backup_dir_path + '/' + file_in, "r")
    for i in range(8): VTemp = poscar_in.readline().split()
    if (VTemp[0][0] == 'D' or VTemp[0][0] == 'd'): type_poscar = 'direct'
    if (VTemp[0][0] == 'C' or VTemp[0][0] == 'c'): type_poscar = 'cartesian'
    if (VTemp[0][0] == 'S' or VTemp[0][0] == 's'): type_poscar = 'selective'
    poscar_in.close()
    #----------------

    if (type_poscar != 'cartesian'): shutil.copy2(poscar_backup_dir_path + '/' + file_in, poscar_dir_path + '/' + file_out)

    if (type_poscar == 'cartesian'):
       #-------------------------------------------------------------
       poscar_in  = open(poscar_backup_dir_path + '/' + file_in, "r")
       poscar_out = open(poscar_dir_path + '/' + file_out, "w")
       #-------------------------------------------------------
       VTemp = poscar_in.readline()
       poscar_out.write(f'{VTemp}')
       #------------------------------------------------------------
       VTemp = poscar_in.readline().split(); param = float(VTemp[0])
       poscar_out.write(f'1.0 \n')
       #-----------------------------------
       VTemp = poscar_in.readline().split()
       A1x = float(VTemp[0])*param
       A1y = float(VTemp[1])*param
       A1z = float(VTemp[2])*param
       poscar_out.write(f'{A1x:.16} {A1y:.16} {A1z:.16} \n')
       #----------------------------------------------------
       VTemp = poscar_in.readline().split()
       A2x = float(VTemp[0])*param
       A2y = float(VTemp[1])*param
       A2z = float(VTemp[2])*param
       poscar_out.write(f'{A2x:.16} {A2y:.16} {A2z:.16} \n')
       #----------------------------------------------------
       VTemp = poscar_in.readline().split()
       A3x = float(VTemp[0])*param
       A3y = float(VTemp[1])*param
       A3z = float(VTemp[2])*param
       poscar_out.write(f'{A3x:.16} {A3y:.16} {A3z:.16} \n')
       #----------------------------------------------------
       VTemp = poscar_in.readline()
       poscar_out.write(f'{VTemp}')
       #---------------------------
       nions = 0
       VTemp = poscar_in.readline()
       poscar_out.write(f'{VTemp}')
       VTemp = VTemp.split()
       for i in range(len(VTemp)): nions += int(VTemp[i])
       #-------------------------------------------------
       VTemp = poscar_in.readline()
       poscar_out.write(f'Direct \n')
       #-----------------------------
       a = np.array([A1x, A1y, A1z])
       b = np.array([A2x, A2y, A2z])
       c = np.array([A3x, A3y, A3z])
       T = np.linalg.inv(np.array([a, b, c]).T)      # Defines the transformation matrix
       #---------------------------------------
       for i in range(nions):
           #-----------------------------------
           VTemp = poscar_in.readline().split()
           x = float(VTemp[0])*param
           y = float(VTemp[1])*param
           z = float(VTemp[2])*param
           #------------------------
           r = np.array([x, y, z])      # Defines the Cartesian position of the atom
           f = np.dot(T, r)             # Calculates fractional position
           f = f % 1.0
           #-------------------------------------------------------
           poscar_out.write(f'{f[0]:.16} {f[1]:.16} {f[2]:.16} \n')
       #-----------------------------------------------------------
       poscar_in.close()   
       poscar_out.close()
#------------------------------------
shutil.rmtree(poscar_backup_dir_path)
delete_hidden_files(poscar_dir_path)
#-----------------------------------


#============================================
# creating IDs for POSCAR files =============
#============================================
id_poscar_files = open(dir_files + '/ID_POSCAR_Files.txt', 'w')
files0 = [name for name in os.listdir(poscar_dir_path) if os.path.isfile(os.path.join(poscar_dir_path, name))]
#---------------------------
for i in range(len(files0)):
    #--------------------------------------------
    Lattice0 = dir_files + '/' + dir_files_in + '/'
    poscar = open(Lattice0 + files0[i], 'r')
    VTemp1 = poscar.readline().split()
    for j in range(4): VTemp = poscar.readline()
    VTemp2 = poscar.readline().split()
    VTemp3 = poscar.readline().split()
    poscar.close()
    #-------------
    temp_ion = ''
    temp_nion = 0
    for j in range(len(VTemp2)):
        temp_ion += str(VTemp2[j]) 
        temp_nion += int(VTemp3[j])
        if (j < (len(VTemp2) -1)): temp_ion += '_' 
    #---------------------------------------------
    if (VTemp1[0] != 'SAMBA'):
       #----------------------
       id_material = ''
       #---------------------------------------
       poscar = open(Lattice0 + files0[i], "r")
       for j in range(5): VTemp = poscar.readline()
       VTemp3 = poscar.readline().split()
       VTemp4 = poscar.readline().split()
       poscar.close()
       #--------------------------------------------------------------------------------------------
       # Creating a unique 16-digit ID that encodes the POSCAR file structure ----------------------
       #--------------------------------------------------------------------------------------------
       with open(Lattice0 + files0[i], 'r') as f: lines = [line.strip() for line in f.readlines() if line.strip()]
       #----------------------
       tag_1 = float(lines[1])
       #---------
       tag_2 = []
       for j in range(2, 5):
           vector = [float(x) for x in lines[j].split()]
           tag_2.append(vector)
       #-----------------------
       tag_3 = lines[5].split()
       #-----------------------
       tag_4 = [int(x) for x in lines[6].split()]
       #-----------------------------------------
       tag_5 = lines[7].lower()
       #-----------------------
       tag_6 = []
       natoms = sum(tag_4)
       for j in range(8, 8 + natoms):
           coord = [float(x) for x in lines[j].split()[:3]]
           tag_6.append(coord)
       #----------------------
       data_hash = [tag_1, tag_2, tag_3, tag_4, tag_5, tag_6]
       canonical_string = json.dumps(data_hash, separators=(',', ':'))
       unique_id = hashlib.sha256(canonical_string.encode('utf-8')).hexdigest()[:16]
       #----------------------------------------------------------------------------
       for j in range(len(VTemp3)):
           id_material += str(VTemp3[j])
           if (str(VTemp4[j]) != '1'): id_material += str(VTemp4[j])
       id_material +=  '_' + unique_id
       #--------------------------------------------------------------------
       with open(Lattice0 + files0[i], 'r') as file: line = file.readlines()
       line[0] = 'SAMBA ' + temp_ion + ' ' + str(temp_nion) + ' ' + id_material + '\n'
       with open(Lattice0 + files0[i], 'w') as file: file.writelines(line)
       #------------------------------------------------------------------
       id_poscar_files.write(f'{files0[i]} >> {id_material} \n')
    #-------------------------
    if (VTemp1[0] == 'SAMBA'):
       #----------------------------
       id_material = str(VTemp1[-1])
       #--------------------------------------------------------
       id_poscar_files.write(f'{files0[i]} >> {id_material} \n')
#----------------------
id_poscar_files.close()
#----------------------
