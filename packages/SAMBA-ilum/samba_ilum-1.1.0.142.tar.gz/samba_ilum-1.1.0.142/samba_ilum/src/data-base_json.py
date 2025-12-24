# SAMBA_ilum Copyright (C) 2025
# GNU GPL-3.0 license

from pymatgen.io.vasp import Poscar
from pymatgen.core import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
#--------------------------------------------------------
import numpy as np
import shutil
import json
import uuid
import sys
import os


pseudo_type = 'PAW_PBE'
exchange_correlation_functional = 'GGA'
vdW = 'optB86b'


# replace_type_pseudo
# replace_type_XC
# replace_type_vdW


# =========================================
# Checking files to be read: ==============
# =========================================
l_file = 'null';  l_file_SO = 'null'
if os.path.isfile('output/info_scf.txt'):       l_file = 'info_scf.txt'
if os.path.isfile('output/info_bands.txt'):     l_file = 'info_bands.txt'
if os.path.isfile('output/info_scf_SO.txt'):    l_file_SO = 'info_scf_SO.txt'
if os.path.isfile('output/info_bands_SO.txt'):  l_file_SO = 'info_bands_SO.txt'
if (l_file == 'null' and l_file_SO == 'null'):  sys.exit(0)


#==========================================================
# Extracting the k-path for the Band Structure plot =======
#==========================================================
kpoints_file = []
kpath = []
kpath_label = []
#---------------
if os.path.isdir('output/Bandas'):     dir_kpath = 'bands'
if os.path.isdir('output/Bandas_SO'):  dir_kpath = 'bands.SO'
#-----------------------------------------------------------------------------
if os.path.isfile(dir_kpath + '/' + 'KPOINTS'): kpoints_file.append('KPOINTS')
#--------------------------------------------------------------------------------------
nkpoints = len([file for file in os.listdir(dir_kpath) if file.startswith("KPOINTS.")])
for i in range(nkpoints):
    file = 'KPOINTS.' + str(i+1)
    if os.path.isfile(dir_kpath + '/' + file): kpoints_file.append(file)
#---------------------------------
for i in range(len(kpoints_file)):
    #-----------------------------
    with open(dir_kpath + '/' + kpoints_file[i], 'r') as file: lines = file.readlines()
    #----------------------------------------------------------------------------------
    if (len(kpoints_file) == 1):
       for j in range(len(lines)):
           if (j > 3 and len(lines[j]) > 1):
              line = lines[j].split()
              line[3] = line[3].replace('!', '').replace('#1', 'Gamma').replace('#', '')
              kpath.append([round(float(line[0]), 15), round(float(line[1]), 15), round(float(line[2]), 15)])
              kpath_label.append(line[3])
    #--------------------------------------
    if (len(kpoints_file) > 1):
       for j in range(len(lines)):
           if (i == 0 and j > 3 and len(lines[j]) > 1):
              line = lines[j].split()
              line[3] = line[3].replace('!', '').replace('#1', 'Gamma').replace('#', '')
              kpath.append([round(float(line[0]), 15), round(float(line[1]), 15), round(float(line[2]), 15)])
              kpath_label.append([line[3]])
           if (i > 0  and j > 4 and len(lines[j]) > 1):
              line = lines[j].split()
              line[3] = line[3].replace('!', '').replace('#1', 'Gamma').replace('#', '')
              kpath.append([round(float(line[0]), 15), round(float(line[1]), 15), round(float(line[2]), 15)])
#-------------------------------------------------------------
# Removing adjacent and repeated elements from the k-path list
#-------------------------------------------------------------
i = 0
while i < (len(kpath) -1):
    if kpath[i] == kpath[i +1]: del kpath[i +1]
    if kpath_label[i] == kpath_label[i +1]: del kpath_label[i +1]
    else: i += 1  # Avança para o próximo par de elementos


# ===================================================
# Starting tags with empty values "--" ==============
# ===================================================
area_perc_mismatch = '--';  perc_area_change = '--';  perc_mod_vectors_change = '--';
angle_perc_mismatch = '--';  perc_angle_change = '--';  rotation_angle = '--';
supercell_matrix = '--';  deformation_matrix = '--';  strain_matrix = '--'
shift_plane = '--'

# =============================================================
# Extracting Configuration Information from Heterostructure ===
# =============================================================
if os.path.isfile('output/POSCAR.info'):
   #---------------------------------------
   poscar = open('output/POSCAR.info', "r")
   VTemp = poscar.readline().split()
   param = float(poscar.readline())
   poscar.close()
   #------------------------
   if (VTemp[0] == 'SAMBA'):
      #----------------------------------------------------------------
      l_materials = VTemp[1].replace('+', ' ').replace('_', '').split()
      n_materials = len(l_materials)
      #------------------------------------------
      r_ions_materials = []; nions_materials = []
      nion = 0;  passo = 0
      #-----------------------------
      for m in range(n_materials):
          r_ions_materials.append( str(1 + nion) + ':')
          nion += int(VTemp[m+2])
          r_ions_materials[m] += str(nion)
          nions_materials.append(int(VTemp[m+2]))
      #------------------------------------------
      id_materials = []
      #--------------------


      if (n_materials > 1):
         #----------------------------------------------------------------------
         area_perc_mismatch = []; angle_perc_mismatch = [];  rotation_angle = []
         perc_area_change = [];  perc_mod_vectors_change = [];  perc_angle_change = []
         supercell_matrix = [];  deformation_matrix = [];  strain_matrix = []
         shift_plane = []
         #---------------------
         passo = n_materials +1
         passo += 4
         temp1 = str(VTemp[passo]).replace('_', ' ').split()
         area_perc_mismatch.append([round(float(temp1[0]), 15), round(float(temp1[1]), 15)])
         if (n_materials == 3):
            area_perc_mismatch.append([round(float(temp1[2]), 15), round(float(temp1[3]), 15)])
         #-------------------------------------------------
         passo += 4
         temp1 = str(VTemp[passo]).replace('_', ' ').split()
         for ii in range(len(temp1)): perc_area_change.append(round(float(temp1[ii]), 15))
         #--------------------------------------------------------------
         passo += 4
         temp1 = str(VTemp[passo]).replace('_', ' ').split()
         perc_mod_vectors_change.append([round(float(temp1[0]), 15), round(float(temp1[1]), 15)])
         perc_mod_vectors_change.append([round(float(temp1[2]), 15), round(float(temp1[3]), 15)])
         if (n_materials == 3):
            perc_mod_vectors_change.append([round(float(temp1[4]), 15), round(float(temp1[5]), 15)])
         #------------------------------------------------------
         passo += 4
         temp1 = str(VTemp[passo]).replace('_', ' ').split()
         angle_perc_mismatch.append([round(float(temp1[0]), 15), round(float(temp1[1]), 15)])
         if (n_materials == 3):
            angle_perc_mismatch.append([round(float(temp1[2]), 15), round(float(temp1[3]), 15)])
         #--------------------------------------------------
         passo += 4
         temp1 = str(VTemp[passo]).replace('_', ' ').split()
         for ii in range(len(temp1)): perc_angle_change.append(round(float(temp1[ii]), 15))
         #---------------------------------------------------------------
         passo += 4
         temp1 = str(VTemp[passo]).replace('_', ' ').split()
         for ii in range(len(temp1)): rotation_angle.append(round(float(temp1[ii]), 15))
         #------------------------------------------------------------
         for i in range(n_materials):
             passo += 4
             temp1 = str(VTemp[passo]).replace('_', ' ').split()
             supercell_matrix.append([[int(temp1[0]), int(temp1[1])], [int(temp1[2]), int(temp1[3])]])
             # supercell_matrix.append([[round(float(temp1[0]), 15), round(float(temp1[1]), 15)], [round(float(temp1[2]), 15), round(float(temp1[3]), 15)]])
         #------------------------------------------------------------------------
         for i in range(n_materials):
             passo += 4
             temp1 = str(VTemp[passo]).replace('_', ' ').split()
             deformation_matrix.append([[round(float(temp1[0]), 15), round(float(temp1[1]), 15)], [round(float(temp1[2]), 15), round(float(temp1[3]), 15)]])
         #--------------------------------------------------------------------------
         for i in range(n_materials):
             passo += 4
             temp1 = str(VTemp[passo]).replace('_', ' ').split()
             strain_matrix.append([[round(float(temp1[0]), 15), round(float(temp1[1]), 15)], [round(float(temp1[2]), 15), round(float(temp1[3]), 15)]])
         #---------------------------------------------------------------------
         passo += 4
         temp1 = str(VTemp[passo]).replace('_', ' ').split()
         for ii in range(len(temp1)): shift_plane.append(round(float(temp1[ii]), 15))
         #---------------------------------------------------------
         passo += 1
         for i in range(n_materials):
             id_materials.append(str(VTemp[-n_materials -1 +i]))
      #--------------------------------------------
      temp_id = VTemp[-1].replace('_', ' ').split()
      if (len(temp_id) > 1): estequiometria = temp_id[0]
      id_code = VTemp[-1]
   #-------------------------------------------------------
   if (n_materials == 1): id_materials.append(str(id_code))
   #-------------------------------------------------------
   if (VTemp[0] != 'SAMBA'): exit()
   #-------------------------------


# =============================================================
# Extracting Configuration Information from Heterostructure ===
# =============================================================
poscar = open('output/POSCAR.info', "r")
VTemp = poscar.readline().split()
materials = VTemp[1].replace('+', ' ').split()
#---------------------------------------------
t_ions_materials = []
for i in range(len(materials)):
    ions_vector = []
    mat_temp = materials[i].replace('_', ' ').split()
    for j in range(len(mat_temp)): 
        ions_vector.append(str(mat_temp[j]))
    t_ions_materials.append(ions_vector)
#-------------------------------------------
for i in range(6): VTemp = poscar.readline().split()
t_nions_materials = [];  number = -1
for i in range(len(materials)):
    nions_vector = []
    mat_temp = materials[i].replace('_', ' ').split()
    for j in range(len(mat_temp)):
        number += 1
        nions_vector.append(int(VTemp[number]))
    t_nions_materials.append(nions_vector)
#-------------
poscar.close()
#-------------


# =====================================================
# Extracting the positions of ions from the Lattice ===
# =====================================================
poscar = open('output/CONTCAR', "r")
for i in range(5): VTemp = poscar.readline()
type_ions = poscar.readline().split()
type_ions_n = poscar.readline().split()
poscar.readline()
coord_ions = []
rotulo_ions = []
for i in range(len(type_ions)):
    for j in range(int(type_ions_n[i])):
        VTemp = poscar.readline().split()
        coord_ions.append([ round(float(VTemp[0]), 15), round(float(VTemp[1]), 15), round(float(VTemp[2]), 15) ])
        rotulo_ions.append(type_ions[i])
poscar.close()


# ========================================================
# Extracting thicknesses and separating materials ========
# ========================================================
thickness = []; temp_z = [];  z_separation = []
#----------------------------------------------
poscar = open('output/POSCAR.info', "r")
for i in range(8): VTemp = poscar.readline()
for i in range(nion):
    VTemp = poscar.readline().split()
    temp_z.append(float(VTemp[2]))
total_thickness = (max(temp_z) -min(temp_z))*param
total_thickness = round(total_thickness, 15)
poscar.close()
#---------------------------------------------------------
if (n_materials == 1): thickness.append( total_thickness )
#---------------------------------------------------------
if (n_materials > 1):
   poscar = open('output/POSCAR.info', "r")
   for i in range(8): VTemp = poscar.readline()
   for i in range(n_materials):
       temp_z = []
       for j in range(int(nions_materials[i])):
           VTemp = poscar.readline().split()
           temp_z.append(float(VTemp[2]))
       temp_t = (max(temp_z) -min(temp_z))*param
       thickness.append(round(temp_t, 15))
       #---------------------------------------
       if (i > 0):
          temp_sep = (min(temp_z) -temp_max)*param
          z_separation.append(round(temp_sep, 15))
       temp_max = max(temp_z)
       #---------------------
   poscar.close()   
#----------------


# =================================================
# Extracting Binding Energy =======================
# =================================================
e_binding = '--'
if os.path.isfile('output/z-scan/info_z-scan.dat'):
   #--------------------------------------------------
   zscan = open('output/z-scan/info_z-scan.dat', "r")
   #--------------------------------------------------
   for i in range(5): VTemp = zscan.readline().split()
   e_binding = float(VTemp[2])
   #-------------
   zscan.close()

   # -------------------------------------
   # Updating Binding Energy -------------
   # -------------------------------------
   file_oszicar   = 'relax/OSZICAR'
   file_oszicar_f = 'relax/OSZICAR_frozen'
   #--------------------------------------
   if os.path.isfile(file_oszicar):
      if os.path.isfile(file_oszicar_f):
         #------------------------------------
         with open(file_oszicar, 'r') as file:
            lines = file.readlines()
            last_line = lines[-1].split()
            energ_r = float(last_line[2])
         #--------------------------------------
         with open(file_oszicar_f, 'r') as file:
            lines = file.readlines()
            last_line = lines[-1].split()
            energ_f = float(last_line[2])
         #-------------------------------
         e_binding += (energ_f - energ_r)


# =================================================
# Extracting Slide Energy =========================
# =================================================
e_slide = '--'
if os.path.isfile('output/xy-scan/info_xy-scan.dat'):
   #----------------------------------------------------
   xyscan = open('output/xy-scan/info_xy-scan.dat', "r")
   #----------------------------------------------------
   for i in range(6): VTemp = xyscan.readline().split()
   e_slide = round(float(VTemp[2]), 15)
   #-------------
   xyscan.close()


# ==========================================
# Splitting the POSCAR file ================
# ==========================================

if (n_materials > 1):

   #---------------------------------------
   poscar = open('output/POSCAR.info', 'r')
   #---------------------------------------
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

   for m in range(n_Lattice):
       #---------------------------------------
       poscar = open('output/POSCAR.info', 'r')
       poscar_new = open('output/POSCAR.material_' + str(m+1), 'w')
       #-----------------------------------------------------------
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
       #-----------------------------
       VTemp = poscar.readline()
       poscar_new.write(f'{ntype_ions[m]} \n')
       #--------------------------------------
       VTemp = poscar.readline()
       poscar_new.write(f'direct \n')
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


# ===============================================
# Building the .json file =======================
# ===============================================

#-----------------------------------------------------
# Initializing the JSON file with an empty dictionary:
#-----------------------------------------------------
with open('output/info.json', 'w') as file_json:
    json.dump({}, file_json)

# ===============================================
# Updating .json file information ===============
# ===============================================

for n in range(2):


    #-------
    crit = 1
    #-----------
    if (n == 0):
       file = l_file
       if (file == 'null'):  crit = 0
    #-----------
    if (n == 1):
       file = l_file_SO
       if (file == 'null'):  crit = 0
    #---------


    if (crit == 1):
       # ===================================================
       # Starting tags with empty values "--" ==============
       # ===================================================
       loop = 0
       #-------
       id = '--';  id_monolayers = '--'
       label = '--';  label_materials = '--';  formula = '--'
       nlayers = '--';  nions = '--';  nions_monolayers = '--';  range_ions_materials = '--'
       type_ions_materials = '--';  type_nions_materials = '--' 
       lattice_type = '--';  point_group = [];  point_group_schoenflies = [];  space_group = [];  space_group_number = [];  inversion_symmetry = []
       param_a = '--';  a1 = '--';  a2 = '--';  a3 = '--';  param_b = '--';  b1 = '--';  b2 = '--';  b3 = '--'
       module_a1_a2_a3 = '--'; module_b1_b2_b3 = '--';  angle_a1a2_a1a3_a2a3 = '--'; angle_b1b2_b1b3_b2b3 = '--'
       cell_area = '--';  cell_vol = '--';  zb_area = '--';  zb_volume = '--'
       direct_coord_ions = '--';  label_ions = '--';  k_path = '--'
       #----------------------------------------------------------------------------------------------------------
       e_vbm = '--';  e_cbm = '--';  e_fermi = '--';  e_vacuum = '--';  work_function = '--';  total_energy = '--'
       tk_vbm = '--';  tk_cbm = '--'; k_vbm = '--';  k_cbm = '--' 
       nk = '--';  nb = '--';  ne = '--';  ne_valence = '--';  vbm = '--';  cbm = '--';  charge_transfer = [];  charge_transfer_SO = []
       gap = '--';  type_gap = '--';  k_vbm = [];  k_cbm = [];  lorbit = '--';  ispin = '--'
       #------------------------------------------------------------------------------------
       non_collinear = '--';  spin_orbit = '--';  lorbit = '--';  ispin = '--'
       #----------------------------------------------------------------------


       # =========================================  ????????????????????????????????????????????????????????????????????????????????????????????????????????????
       # Extracting the vacuum level: ============  ?????????????????????????????? Only makes sense for 2D systems confined in Z ???????????????????????????????
       # =========================================  ????????????????????????????????????????????????????????????????????????????????????????????????????????????
       l_pot = 'null';  l_pot_SO = 'null'
       #-----------------------------------------------------------
       if os.path.isfile('output/Potencial_bands/Potencial_Z.dat'):     l_pot = 'output/Potencial_bands/Potencial_Z.dat'
       if os.path.isfile('output/Potencial_scf/Potencial_Z.dat'):       l_pot = 'output/Potencial_scf/Potencial_Z.dat'
       if os.path.isfile('output/Potencial_bands_SO/Potencial_Z.dat'):  l_pot_SO = 'output/Potencial_bands_SO/Potencial_Z.dat'
       if os.path.isfile('output/Potencial_scf_SO/Potencial_Z.dat'):    l_pot_SO = 'output/Potencial_scf_SO/Potencial_Z.dat'
       #------------------------------------------------------------
       if (l_pot != 'null'):
          file0 = np.loadtxt(l_pot)
          file0.shape
          #-----------------
          date_e = file0[:,1]
          e_vacuum = max(date_e)
       #------------------------
       if (l_pot_SO != 'null'):
          file1 = np.loadtxt(l_pot_SO)
          file1.shape
          #-----------------
          date_e = file1[:,1]
          e_vacuum = max(date_e) 


       # ===========================================
       # Extracting data from VASProcar output =====
       # ===========================================
       with open('output/' + file, "r") as info: lines = info.readlines()
       #-----------------------------------------------------------------
       for i in range(len(lines)):
           VTemp = lines[i].replace('(', ' ( ').replace(')', ' ) ').replace(';', '').replace(',', '').split()
           if (len(VTemp) > 0):
              #----------------------------------------
              if (VTemp[0] == 'LNONCOLLINEAR'):  non_collinear = str(VTemp[2])
              #----------------------------------------
              elif (VTemp[0] == 'LSORBIT'):  spin_orbit = str(VTemp[2])
              #----------------------------------------
              elif (VTemp[0] == 'nº' or VTemp[0] == 'nÂº'):
                 if (VTemp[1] == 'k-points'):  nk = int(VTemp[3])
                 if (VTemp[5] == 'bands'):  nb = int(VTemp[7])
                 if (VTemp[1] == 'ions'):  ni = int(VTemp[3])
                 if (VTemp[5] == 'electrons'):  ne = round(float(VTemp[7]), 15)
              #--------------------------------------------------------------------
              elif (VTemp[0] == 'LORBIT'):
                 lorbit = int(VTemp[2])
                 if (VTemp[3] == 'ISPIN'):  ispin = int(VTemp[5])
              #----------------------------------------
              elif (VTemp[0] == 'Last'):  vbm = int(VTemp[4])
              #----------------------------------------
              elif (VTemp[0] == 'First'):  cbm = vbm +1
              #----------------------------------------
              elif (VTemp[0] == 'Valence'):
                   e_vbm = round(float(VTemp[7]), 15)
                   tk_vbm = int(VTemp[11])
              #----------------------------------------
              elif (VTemp[0] == 'Conduction'):
                   e_cbm = round(float(VTemp[7]), 15)
                   tk_cbm = int(VTemp[11])
              #----------------------------------------
              elif (VTemp[0] == 'GAP'):
                type_gap = str(VTemp[2])
                gap = round(float(VTemp[5]), 15)
              #----------------------------------------
              elif (VTemp[0] == 'Fermi'): e_fermi = round(float(VTemp[3]), 15)
              #----------------------------------------
              elif (VTemp[0] == 'free'):
                   total_energy = round(float(VTemp[4]), 15)
                   # e_per_ion = round(float(total_energy)/ni, 15)
              #--------------------------------------------------------
              elif (VTemp[0] == 'Volume_cell'):  Volume_cell = round(float(VTemp[2]), 15)
              #----------------------------------------
              elif (VTemp[0] == 'Param.'):  param = float(VTemp[2])   
              #----------------------------------------
              elif (VTemp[0] == 'A1'):
                   a1 = [round(float(VTemp[4])*param, 15), round(float(VTemp[5])*param, 15), round(float(VTemp[6])*param, 15)]                  
                   A1 = np.array([float(VTemp[4]), float(VTemp[5]), float(VTemp[6])])*param;  module_a1_a2_a3 = []; module_a1_a2_a3.append(round(np.linalg.norm(A1), 15))
              elif (VTemp[0] == 'A2'):
                   a2 = [round(float(VTemp[4])*param, 15), round(float(VTemp[5])*param, 15), round(float(VTemp[6])*param, 15)]
                   A2 = np.array([float(VTemp[4]), float(VTemp[5]), float(VTemp[6])])*param;  module_a1_a2_a3.append(round(np.linalg.norm(A2), 15))
              elif (VTemp[0] == 'A3'):
                   a3 = [round(float(VTemp[4])*param, 15), round(float(VTemp[5])*param, 15), round(float(VTemp[6])*param, 15)]
                   A3 = np.array([float(VTemp[4]), float(VTemp[5]), float(VTemp[6])])*param;  module_a1_a2_a3.append(round(np.linalg.norm(A3), 15))
                   #-------------------------------------------------------
                   angle_a1a2_a1a3_a2a3 = []
                   angle_a1a2_a1a3_a2a3.append(round(np.degrees(np.arccos(np.dot(A1,A2) / (np.linalg.norm(A1) * np.linalg.norm(A2)))), 15))
                   angle_a1a2_a1a3_a2a3.append(round(np.degrees(np.arccos(np.dot(A1,A3) / (np.linalg.norm(A1) * np.linalg.norm(A3)))), 15))
                   angle_a1a2_a1a3_a2a3.append(round(np.degrees(np.arccos(np.dot(A2,A3) / (np.linalg.norm(A2) * np.linalg.norm(A3)))), 15))
              #----------------------------------------
              elif (VTemp[0] == '2pi/Param.'):  fator_rec = float(VTemp[2])   
              #----------------------------------------
              elif (VTemp[0] == 'B1'):
                   b1 = [round(float(VTemp[4])*fator_rec, 15), round(float(VTemp[5])*fator_rec, 15), round(float(VTemp[6])*fator_rec, 15)]
                   B1 = np.array([float(VTemp[4]), float(VTemp[5]), float(VTemp[6])])*fator_rec;  module_b1_b2_b3 = []; module_b1_b2_b3.append(round(np.linalg.norm(B1), 15))
              elif (VTemp[0] == 'B2'):
                   b2 = [round(float(VTemp[4])*fator_rec, 15), round(float(VTemp[5])*fator_rec, 15), round(float(VTemp[6])*fator_rec, 15)]
                   B2 = np.array([float(VTemp[4]), float(VTemp[5]), float(VTemp[6])])*fator_rec;  module_b1_b2_b3.append(round(np.linalg.norm(B2), 15))
              elif (VTemp[0] == 'B3'):
                   b3 = [round(float(VTemp[4])*fator_rec, 15), round(float(VTemp[5])*fator_rec, 15), round(float(VTemp[6])*fator_rec, 15)]
                   B3 = np.array([float(VTemp[4]), float(VTemp[5]), float(VTemp[6])])*fator_rec;  module_b1_b2_b3.append(round(np.linalg.norm(B3), 15))
                   #-------------------------------------------------------
                   angle_b1b2_b1b3_b2b3 = []
                   angle_b1b2_b1b3_b2b3.append(round(np.degrees(np.arccos(np.dot(B1,B2) / (np.linalg.norm(B1) * np.linalg.norm(B2)))), 15))
                   angle_b1b2_b1b3_b2b3.append(round(np.degrees(np.arccos(np.dot(B1,B3) / (np.linalg.norm(B1) * np.linalg.norm(B3)))), 15))
                   angle_b1b2_b1b3_b2b3.append(round(np.degrees(np.arccos(np.dot(B2,B3) / (np.linalg.norm(B2) * np.linalg.norm(B3)))), 15))
              #----------------------------------------
              elif (VTemp[0] == 'Volume_ZB'):  vol_zb = VTemp[2]   
              #----------------------------------------
              elif (VTemp[0] == 'k-points'):  loop = i+3



       if (tk_vbm != '--' and tk_cbm != '--'):
          # ===========================================
          # Finding the band gap k-points =============
          # ===========================================
          if (file == 'info_bands.txt' or file == 'info_bands_SO.txt'):
             if (n == 0): info = open('output/info_bands.txt', "r")
             if (n == 1): info = open('output/info_bands_SO.txt', "r")
             #-----------
             test = 'nao'
             #-----------
             while (test == 'nao'):             
               #--------------------------------
               VTemp = info.readline().split()
               #-----------------------------------------------------------
               if (len(VTemp) > 0 and VTemp[0] == 'k-points'): test = 'sim'                       
               #-----------------------------------------------------------
             for nn in range(2): VTemp = info.readline()
             for nn in range(1,(nk+1)):
                 VTemp = info.readline().split()
                 if (nn == int(tk_vbm)): k_vbm = [round(float(VTemp[1]), 15), round(float(VTemp[2]), 15), round(float(VTemp[3]), 15)]
                 if (nn == int(tk_cbm)): k_cbm = [round(float(VTemp[1]), 15), round(float(VTemp[2]), 15), round(float(VTemp[3]), 15)]


       # =================================================================
       # Searching for values ​​for the Transfer of Bader's Charge =========
       # =================================================================
       if (n_materials > 1):
          #===========
          if (n == 0):
             if os.path.isfile('output/Charge_transfer/Bader_charge_transfer.dat'):
                file_bader = 'output/Charge_transfer/Bader_charge_transfer.dat'
                #----------------------------
                bader = open(file_bader, "r")
                for nn in range(4): VTemp = bader.readline()
                for mn in range(len(t_ions_materials)):
                    vector_bader = []
                    VTemp = bader.readline()
                    VTemp = bader.readline().split()
                    vector_bader.append(round(float(VTemp[2]), 15))
                    for mm in range(len(t_ions_materials[mn])):
                        VTemp = bader.readline().split()
                        vector_bader.append(round(float(VTemp[3]), 15))
                    charge_transfer.append(vector_bader)
          #===========
          if (n == 1):
             if os.path.isfile('output/Charge_transfer_SO/Bader_charge_transfer.dat'):
                file_bader = 'output/Charge_transfer_SO/Bader_charge_transfer.dat'
                #----------------------------
                bader = open(file_bader, "r")
                for nn in range(4): VTemp = bader.readline()
                for mn in range(len(t_ions_materials)):
                    vector_bader = []
                    VTemp = bader.readline()
                    VTemp = bader.readline().split()
                    vector_bader.append(round(float(VTemp[2]), 15))
                    for mm in range(len(t_ions_materials[mn])):
                        VTemp = bader.readline().split()
                        vector_bader.append(round(float(VTemp[3]), 15))
                    charge_transfer_SO.append(vector_bader)


       """
       # ===========================================================
       # Obtaining and organizing k-point information ==============
       # ===========================================================
       if (file == 'info_bands.txt' or file == 'info_bands_SO.txt'):
          #---------------------------------
          info = open('output/' + file, "r")
          #---------------------------------
          if (loop != 0):
             #-----------------------------------------------------
             k_points_direct = []; k_points_cart = [];  k_path = []
             #---------------------------------------------
             for i in range(loop):  VTemp = info.readline()
             for i in range(nk):
                 VTemp = info.readline().split()
                 k_points_direct.append([VTemp[1], VTemp[2], VTemp[3]])
                 k_points_cart.append([VTemp[4], VTemp[5], VTemp[6]])
                 k_path.append(VTemp[7])
          print(k_path)
          #-----------
          info.close()
       """


       # =========================================================
       # Obtaining lattice symmetries ============================
       # =========================================================

       #--------------------------------------------------------------------
       # Hermann-Mauguin Mapping Dictionary for Schoenflies ----------------
       #--------------------------------------------------------------------
       schoenflies = {"1": "C1",  "-1": "Ci",  "2": "C2",  "m": "Cs",  "2/m": "C2h",  "222": "D2",  "mm2": "C2v",  "mmm": "D2h",  "4": "C4",  "-4": "S4",  "4/m": "C4h",
                      "422": "D4",  "4mm": "C4v",  "-42m": "D2d",  "4/mmm": "D4h",  "3": "C3",  "-3": "C3i",  "32": "D3",  "3m": "C3v",  "-3m": "D3d",  "6": "C6",  "-6": "C3h",  
                      "6/m": "C6h",  "622": "D6",  "6mm": "C6v",  "-6m2": "D3h",  "6/mmm": "D6h",  "23": "T",  "m-3": "Th",  "432": "O",  "-43m": "Td",  "m-3m": "Oh"}
       #--------------------------------------------------------------------
       if (n_materials == 1): passo = 1
       if (n_materials >  1): passo = n_materials +1
       #--------------------------------------------
       for i in range(passo):
           #-----------------
           if (i == 0): structure = Poscar.from_file('output/POSCAR.info').structure
           if (i >  0): structure = Poscar.from_file('output/POSCAR.material_' + str(i)).structure
           analyzer = SpacegroupAnalyzer(structure)
           #----------------------------------------------------
           point_group.append(analyzer.get_point_group_symbol())
           space_group.append(analyzer.get_space_group_symbol())
           space_group_number.append(analyzer.get_space_group_number())
           inversion_symmetry.append(analyzer.is_laue())
           if (i == 0): lattice_type = analyzer.get_lattice_type()
           point_group_schoenflies.append(schoenflies.get(point_group[0], "Desconhecido"))
           #------------------------------------------------------------------------------
           # if (i > 0): os.remove('output/POSCAR.material_' + str(i)) # ERROR !!!!!!!!!!!


       #======================================================
       # Obtaining the area in the XY plane of the lattice ===
       #======================================================
       V1 = np.array([A1[0], A1[1]])
       V2 = np.array([A2[0], A2[1]])
       #----------------------------
       # Cell area in the XY plane
       Area_cell = round(np.linalg.norm(np.cross(V1, V2)), 15)
       #------------------------------------------------------


       #===================================================
       # Obtaining the area in the KxKy plane of the ZB ===
       #===================================================
       V1 = np.array([B1[0], B1[1]])
       V2 = np.array([B2[0], B2[1]])
       #----------------------------
       # Area of ​​ZB in the KxKy plane
       Area_ZB = round(np.linalg.norm(np.cross(V1, V2)), 15)
       #----------------------------------------------------


       # ===========================================
       # Creating the Dictionary ===================
       # ===========================================

       dados0 = {
                "id": id_code,
                "number_layers": n_materials,
                "id_layers": id_materials,
                "formula": estequiometria,
                "type_ions_layers": t_ions_materials,
                "number_ions_layers": nions_materials,
                "number_type_ions_layers": t_nions_materials,
                "range_ions_layers": r_ions_materials,
                "number_ions": ni,
                # ---------------------------------------------------------------------
                "doi": "10.1038/s41524-025-01892-z",
                "article": "A high-throughput framework and database for twisted 2D vander Waals bilayers",
                "bibteX": "@article{araujo2025twisted,\n title = {A high-throughput framework and database for twisted 2D van der Waals bilayers},\n author = {Araújo, Augusto L. and Sophia, Pedro H. and Crasto de Lima, F. and Fazzio, Adalberto},\n journal = {npj Computational Materials},\n year = {2025},\n doi = {10.1038/s41524-025-01892-z},\n url = {https://doi.org/10.1038/s41524-025-01892-z},\n publisher = {Nature Publishing Group}\n}",
                # ---------------------------------------------------------------------
                "area_perc_mismatch": area_perc_mismatch  if n_materials > 1 else None,
                "perc_area_change": perc_area_change  if n_materials > 1 else None,
                "perc_mod_vectors_change": perc_mod_vectors_change  if n_materials > 1 else None,
                "angle_perc_mismatch": angle_perc_mismatch  if n_materials > 1 else None,
                "perc_angle_change": perc_angle_change  if n_materials > 1 else None,
                "rotation_angle": rotation_angle  if n_materials > 1 else None,
                "supercell_matrix": supercell_matrix  if n_materials > 1 else None,
                "deformation_matrix": deformation_matrix  if n_materials > 1 else None,
                "strain_matrix": strain_matrix  if n_materials > 1 else None,
                # "structural_optimization": 'DFT',      # 'none', 'DFT', 'ML', 'ML/DFT'
                "shift_plane": shift_plane if n_materials > 1 else None,
                "z_separation": z_separation  if n_materials > 1 else None,
                "thickness": thickness,
                "total_thickness": total_thickness,
                # ---------------------------------------------------------------------
                "lattice_type": lattice_type,
                "point_group": point_group,
                # "point_group_schoenflies": point_group_schoenflies,
                "space_group": space_group,
                "space_group_number": space_group_number,
                "inversion_symmetry": inversion_symmetry,
                "pseudo_type": pseudo_type,
                "exchange_correlation_functional": exchange_correlation_functional,
                "vdW": vdW,
                "non_collinear": non_collinear,
                "spin_orbit": spin_orbit,
                # "param_a": param,
                "a1": a1,
                "a2": a2,
                "a3": a3,
                "module_a1_a2_a3": module_a1_a2_a3,
                "angle_a1a2_a1a3_a2a3": angle_a1a2_a1a3_a2a3,
                "cell_area": Area_cell,
                # "cell_vol": Volume_cell,
                # "param_b": fator_rec,
                "b1": b1,
                "b2": b2,
                "b3": b3,
                "module_b1_b2_b3": module_b1_b2_b3,
                "angle_b1b2_b1b3_b2b3": angle_b1b2_b1b3_b2b3,
                "zb_area": Area_ZB,
                # "zb_volume": vol_zb,
                "direct_coord_ions": coord_ions,
                "label_ions": rotulo_ions,
                "kpath": kpath,
                "kpath_label": kpath_label,
                }


       if (n == 0):
          #---------
          dados1 = {
                   "lorbit": lorbit,
                   "ispin": ispin,
                   "nk": nk,
                   "nb": nb,
                   "ne": ne,
                   "gap": gap,
                   "e_vbm": e_vbm,
                   "e_cbm": e_cbm,
                   "vbm": vbm,
                   "cbm": cbm,
                   "type_gap": type_gap,
                   "k_vbm": k_vbm,
                   "k_cbm": k_cbm,
                   "e_fermi": e_fermi,
                   "e_vacuum": e_vacuum,
                   # "work_function": work_function,
                   "total_energy": total_energy,
                   "e_per_ion":  round(float(total_energy)/ni, 15),
                   "e_per_area": round(float(total_energy)/float(Area_cell), 15),
                   "e_binding": e_binding  if n_materials > 1 else None,
                   "e_slide": e_slide  if n_materials > 1 else None,
                   "charge_transfer": charge_transfer  if n_materials > 1 else None,
                   }


       if (n == 1):
          #---------
          dados1 = {
                   "lorbit_SO": lorbit,
                   "ispin_SO": ispin,
                   "nk_SO": nk,
                   "nb_SO": nb,
                   "ne_SO": ne,
                   "gap_SO": gap,
                   "e_vbm_SO": e_vbm,
                   "e_cbm_SO": e_cbm,
                   "vbm_SO": vbm,
                   "cbm_SO": cbm,
                   "type_gap_SO": type_gap,
                   "k_vbm_SO": k_vbm,
                   "k_cbm_SO": k_cbm,
                   "e_fermi_SO": e_fermi,
                   "e_vacuum_SO": e_vacuum,
                   # "work_function_SO": work_function,
                   "total_energy_SO": total_energy,
                   "e_per_ion_SO":  round(float(total_energy)/ni, 15),
                   "e_per_area_SO": round(float(total_energy)/float(Area_cell), 15),
                   "charge_transfer_SO": charge_transfer_SO  if n_materials > 1 else None,
                   }


       # ==================================================
       # Inserting the information into the .json file ====
       # ==================================================
       with open('output/info.json', 'r') as file:  data = json.load(file)            # Loading the current contents of the info.json file
       data.update(dados0)                                                            # Updating the dictionary with new information
       with open('output/info.json', 'w') as file: json.dump(data, file, indent=4)    # Saving updated content to the info.json file
       #----------------------
       with open('output/info.json', 'r') as file:  data = json.load(file)            # Loading the current contents of the info.json file
       data.update(dados1)                                                            # Updating the dictionary with new information
       with open('output/info.json', 'w') as file: json.dump(data, file, indent=4)    # Saving updated content to the info.json file


#===============================================================
# Updating POSCAR and CONTCAR files ============================
#===============================================================
with open('output/POSCAR', 'r') as file: line = file.readlines()
tline = line[0].split()
#--------------------
replace_line = tline[0] + ' ' + tline[1] + ' '
for i in range(n_materials): replace_line += tline[2 +i] + ' '
replace_line += tline[-1] + '\n'
#------------------------------
line[0] = replace_line
with open('output/POSCAR', 'w') as file: file.writelines(line)
#================================================================
with open('output/CONTCAR', 'r') as file: line = file.readlines()
line[0] = replace_line
with open('output/CONTCAR', 'w') as file: file.writelines(line)
#==============================================================


"""
# ===============================================
# Opening and reading the .json database ========
# ===============================================
with open('output/info.json', "r") as file_json: date = json.load(file_json)
#------------------------------------------------
print(" ")
print("=========================")
print("Data from info.json file:")
print("=========================")
print(" ")
for chave, valor in date.items(): print(f"{chave}: {valor}")
"""

