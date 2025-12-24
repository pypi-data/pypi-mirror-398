# SAMBA_ilum Copyright (C) 2025
# GNU GPL-3.0 license


from pymatgen.io.vasp import Poscar
from pymatgen.core import Structure
from pymatgen.analysis.structure_matcher import StructureMatcher
#---------------------------------------------------------------
import random
import shutil
import glob
import uuid
import sys  
import os


print("==================================")
print("Wait a moment ====================")
print("==================================")
print("")


#----------------------------------------------------------------------------
# Function to delete hidden files -------------------------------------------
#----------------------------------------------------------------------------
def delete_hidden_files(target_directory):
    search_files = os.path.join(target_directory, '.*')
    for item in glob.glob(search_files):
        try:
            if os.path.isfile(item): os.remove(item)
        except OSError: pass

#----------------------------------------------------------------------------
# Function to list all files within a given directory -----------------------
#----------------------------------------------------------------------------
def list_files(dir):
   l_files = [name for name in os.listdir(dir) if os.path.isfile(os.path.join(dir, name))]
   return l_files

#----------------------------------------------------------------------------
# Function to list all folders within a given directory ---------------------
#----------------------------------------------------------------------------
def list_folders(dir):
   l_folders = [name for name in os.listdir(dir) if os.path.isdir(os.path.join(dir, name))]
   return l_folders

#----------------------------------------------------------------------------
# Resetting the 'output' directory ------------------------------------------
#----------------------------------------------------------------------------
if os.path.isdir(dir_out):
   shutil.rmtree(dir_out)
   os.mkdir(dir_out)
else: os.mkdir(dir_out)
#----------------------


check_list = open(dir_out + '/check_list.txt', 'w')
check_list.close()


#----------------------------------------------------------------------------
# Checking if POSCAR files are written in direct coordinates ----------------
#----------------------------------------------------------------------------

files = list_files(dir_files + '/Structures')
#--------------------------
for i in range(len(files)):
    test = 0
    #--------------------------------------------------------
    poscar = open(dir_files + '/Structures/' + files[i], 'r')
    for j in range(8): VTemp = poscar.readline().split()
    if ( len(VTemp) == 1 and (VTemp[0] == 'direct' or VTemp[0] == 'Direct') ): test = 1
    #----------------------------------------------------------------------------------
    if (test == 0):
       print(f' ')
       print(f'===============================================')
       print(f'!!! Check the POSCAR files used !!! -----------')
       print(f'-----------------------------------------------')
       print(f'They must be written in direct coordinates, and')
       print(f'the "Selective dynamics" tag is not supported  ')
       print(f'===============================================')
       print(f' ')
       #==========
       sys.exit()   
       #=========


#---------------------------------------------------------------------------
shutil.copytree(dir_files + '/Structures', dir_files + '/Structures_Backup')
#---------------------------------------------------------------------------
id_poscar_files = open(dir_out + '/ID_POSCAR_Files.txt', 'w')
#------------------------------------------------------------
files = list_files(dir_files + '/Structures')
#--------------------------------------------

for i in range(len(files)):
    #------------------------------------
    Lattice0 = dir_files + '/Structures/'
    poscar = open(Lattice0 + files[i], 'r')
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
        if (j < (len(VTemp2) -1)):
           temp_ion += '_' 
    #-------------------------
    if (VTemp1[0] != 'SAMBA'):
       #----------------------
       id_material = ''
       unique_id = str(uuid.uuid4().hex[:16])
       #-------------------------------------
       poscar = open(Lattice0 + files[i], "r")
       for j in range(5): VTemp = poscar.readline()
       VTemp3 = poscar.readline().split()
       VTemp4 = poscar.readline().split()
       poscar.close()
       #---------------------------
       for j in range(len(VTemp3)):
           id_material += str(VTemp3[j])
           if (str(VTemp4[j]) != '1'): id_material += str(VTemp4[j])
       id_material +=  '_' + unique_id
       #-------------------------------------------------------------------
       with open(Lattice0 + files[i], 'r') as file: line = file.readlines()
       line[0] = 'SAMBA ' + temp_ion + ' ' + str(temp_nion) + ' ' + id_material + '\n'
       with open(Lattice0 + files[i], 'w') as file: file.writelines(line)
       #-----------------------------------------------------------------
       # os.rename(Lattice0 + files[i], Lattice0 + id_material)
       id_poscar_files.write(f'{files[i]} >> {id_material} \n')
    #-------------------------
    if (VTemp1[0] == 'SAMBA'):
       #-----------------------
       id_material = VTemp1[-1]
       #------------------------------------------------------- 
       id_poscar_files.write(f'{files[i]} >> {id_material} \n')
#-----------------------
id_poscar_files.close()
if (os.path.getsize(dir_out + '/ID_POSCAR_Files.txt') == 0): os.remove(dir_out + '/ID_POSCAR_Files.txt')
#-------------------------------------------------------------------------------------------------------


print(" ")
print("---------------------------------------------------------------------")
print("Creating directories and copying POSCAR and VASProcar input files ---")
print("---------------------------------------------------------------------")

#-----------------------------------------------------
structures_dir = os.path.join(dir_files, 'Structures')
delete_hidden_files(structures_dir)
#----------------------------------

files = list_files(dir_files + '/Structures')
#--------------------------------------------
t = 1.0; number = -1; n_passos = len(files)
#------------------------------------------

for i in range(len(files)):
    #--------------------------------------------------------
    poscar = open(dir_files + '/Structures/' + files[i], "r")
    VTemp = poscar.readline().split()
    if (VTemp[0] == 'SAMBA'): n_materials = len(VTemp[1].replace('+', ' ').split())
    if (VTemp[0] != 'SAMBA'): n_materials = 1
    for j in range(4): poscar.readline()
    VTemp_ions = poscar.readline().split()
    VTemp_nions = poscar.readline().split()
    poscar.close()
    #-------------
    number += 1
    porc = (number/n_passos)*100        
    #---------------------------
    if (porc >= t and porc <= 100):
       print(f'Progress  {porc:>3,.0f}%')                 
       number += 1
       if (number == 1): t = 1
       if (number == 2): t = 1
       if (number >= 3): t = t + 1
       #--------------------------
              
    #---------------------------------
    os.mkdir(dir_out + '/' + files[i])
    #---------------------------------
    for j in range(len(task)):
        #==================================================
        dir_task = dir_out + '/' + files[i] + '/' + task[j]
        #==================================================
        os.mkdir(dir_task)
        shutil.copyfile(dir_files + '/Structures' + '/' + files[i], dir_task + '/POSCAR')
        shutil.copyfile(dir_files + '/Structures' + '/' + files[i], dir_task + '/CONTCAR')
        shutil.copyfile(dir_codes + '/contcar_update.py', dir_task + '/contcar_update.py')
        #=================================================================================
        if task[j] in ['a-scan', 'z-scan', 'xy-scan', 'xyz-scan']:
           shutil.copyfile(dir_codes + '/' + task[j] + '_analysis.py', dir_task + '/' + task[j] + '_analysis.py')
           shutil.copyfile(dir_codes + '/' + task[j] + '.py', dir_task + '/' + task[j] + '.py')
           shutil.copyfile(dir_codes + '/energy_scan.py', dir_task + '/energy_scan.py')
           #---------------------------------------------------------------------------
           if task[j] in ['a-scan', 'z-scan']:
              check_list = open(dir_task + '/check_steps.txt', 'w')
              check_list.close()
           #------------------------------------------------------------------------------- 
           with open(dir_task + '/' + task[j] + '.py', "r") as file:  content = file.read()
           if (task[j] == 'z-scan'):
              #===========================================================
              # Updating the z-scan.py file ==============================
              #===========================================================
              content = content.replace('replace_vacuo', str(vacuo))
           if (task[j] == 'xy-scan'):
              #===============================================================
              # Updating the xy-scan.py file =================================
              #===============================================================
              content = content.replace('replace_displacement_A1', str(r_displacement_A1))
              content = content.replace('replace_displacement_A2', str(r_displacement_A2))
           if (task[j] == 'xyz-scan'):
              #===============================================================
              # Updating the xyz-scan.py file ================================
              #===============================================================
              content = content.replace('replace_vacuo', str(vacuo))
              content = content.replace('replace_zscan', str(displacement_Z))
              content = content.replace('replace_displacement_xyz_A1', str(displacement_xyz_A1))
              content = content.replace('replace_displacement_xyz_A2', str(displacement_xyz_A2))
           if (task[j] == 'a-scan'):
              #=========================================================================
              # Updating the a-scan.py file ============================================
              #=========================================================================
              content = content.replace('replace_factor_var', str(factor_var))
              content = content.replace('replace_vacuo', str(vacuo))
           #----------------------------------------------------------------------------
           with open(dir_task + '/' + task[j] + '.py', "w") as file: file.write(content)
        #=======================================================================
        """
        if (task[j] == 'relax'):
           shutil.copyfile(dir_codes + '/contcar_update.py', dir_task + '/contcar_update.py')
           temp = dir_codes + '/contcar_update.py', dir_task
        """
        #=====================================================
        if (task[j][:3] == 'dos'):
           os.mkdir(dir_out + '/' + files[i] + '/' + task[j] + '/inputs') 
           shutil.copyfile(dir_inputs_vasprocar + '/input.vasprocar.dos', dir_task + '/inputs/input.vasprocar.dos')
        #==========================================================================================================
        if (task[j][:3] == 'scf'):
           os.mkdir(dir_out + '/' + files[i] + '/' + task[j] + '/inputs')
           shutil.copyfile(dir_inputs_vasprocar + '/input.vasprocar.locpot', dir_task + '/inputs/input.vasprocar.locpot')
        #================================================================================================================
        if (task[j][:5] == 'bands'):
           os.mkdir(dir_out + '/' + files[i] + '/' + task[j] + '/inputs')
           shutil.copyfile(dir_inputs_vasprocar + '/input.vasprocar.orbitals', dir_task + '/inputs/input.vasprocar.orbitals')
           shutil.copyfile(dir_inputs_vasprocar + '/input.vasprocar.locpot', dir_task + '/inputs/input.vasprocar.locpot') 
           shutil.copyfile(dir_inputs_vasprocar + '/input.vasprocar.bands', dir_task + '/inputs/input.vasprocar.bands')
           if (task[j][-3:] == '.SO'):  shutil.copyfile(dir_inputs_vasprocar + '/input.vasprocar.spin', dir_task + '/inputs/input.vasprocar.spin') 
           #---------------------------------------
           poscar = open(dir_task + '/POSCAR', 'r')
           VTemp1 = poscar.readline().split();  poscar.close()
           #--------------------------------------------------           
           shutil.copyfile(dir_inputs_vasprocar + '/input.vasprocar.location', dir_task + '/inputs/input.vasprocar.location')
           #-----------------------------------------------------------------------------------------------------------------
           if (n_materials == 1): 
              label_materials = VTemp_ions
              range_ion_Lattice = [];  nion = 0
              #--------------------------------
              number_ions = VTemp_nions
              for m in range(len(label_materials)):
                  range_ion_Lattice.append( str(1 + nion) + ':')
                  nion += int(number_ions[m])
                  range_ion_Lattice[m] += str(nion) 
           #---------------------------------------
           if (n_materials > 1): 
              label_materials = VTemp1[1].replace('+', ' ').split()
              range_ion_Lattice = []; nion = 0
              #------------------------------------
              for m in range(n_materials):
                  range_ion_Lattice.append( str(1 + nion) + ':')
                  nion += int(VTemp1[m+2])
                  range_ion_Lattice[m] += str(nion) 
           #--------------------------------------------------------------------------------------------
           # Updating the input.vasprocar.location file ------------------------------------------------
           #--------------------------------------------------------------------------------------------
           with open(dir_task + '/inputs/input.vasprocar.location', "r") as file:  content = file.read()
           content = content.replace('replace_n_reg', str(len(label_materials)))
           for m in range(len(label_materials)):
               content = content.replace('replace_label_Lattice' + str(m+1), str(label_materials[m].replace('_', '')))
               content = content.replace('replace_nion_Lattice' + str(m+1), str(range_ion_Lattice[m]))
           with open(dir_task + '/inputs/input.vasprocar.location', "w") as file: file.write(content)
        #============================================================================================
        if (task[j][:5] == 'bader'):
           #-----------------------------------------------------------------------------------
           shutil.copyfile(dir_codes + '/charge_transfer.py', dir_task + '/charge_transfer.py')
           shutil.copyfile(dir_codes + '/bader_update.py', dir_task + '/bader_update.py')
           dir_poscar = dir_out + '/' + files[i] + '/' + task[j]
           exec(open(dir_codes + '/bader_poscar.py').read())
           #------------------------------------------------



print(" ")
print("-------------------------------------------------------------------------")
print("Creating POTCAR files for each material ---------------------------------")
print("-------------------------------------------------------------------------")

files0 = list_folders(dir_out)
#-------------------------------------------
t = 1.0; number = -1; n_passos = len(files0)
#-------------------------------------------

for i in range(len(files0)):
    #------------------------------------------------------------------------
    poscar = open(dir_out + '/' + files0[i] + '/' + task[0] + '/POSCAR', "r")
    VTemp = poscar.readline().split()
    if (VTemp[0] == 'SAMBA'): n_materials = len(VTemp[1].replace('+', ' ').split())
    if (VTemp[0] != 'SAMBA'): n_materials = 1
    poscar.close()
    #-------------

    #-----------------------
    number += 1
    porc = (number/n_passos)*100        
    #-----------------------------
    if (porc >= t and porc <= 100):
       print(f'Progress  {porc:>3,.0f}%')                 
       number += 1
       if (number == 1): t = 1
       if (number == 2): t = 1
       if (number >= 3): t = t + 1
       #--------------------------

    for j in range(len(task)):
        #---------------------------
        if (task[j][:5] != 'bader'):
           dir_poscar = dir_out + '/' + files0[i] + '/' + task[j] + '/POSCAR'
           dir_potcar = dir_out + '/' + files0[i] + '/' + task[j] + '/POTCAR'
           exec(open(dir_codes + '/potcar.py').read())
           #------------------------------------------
        if (task[j][:5] == 'bader'):
           #---------------------------------------------------------------
           files1 = list_folders(dir_out + '/' + files0[i] + '/' + task[j])
           #---------------------------------------------------------------
           for k in range(len(files1)):
               if (files1[k] != 'Charge_transfer'):
                  dir_poscar = dir_out + '/' + files0[i] + '/' + task[j] + '/' + files1[k] + '/POSCAR'
                  dir_potcar = dir_out + '/' + files0[i] + '/' + task[j] + '/' + files1[k] + '/POTCAR'
                  exec(open(dir_codes + '/potcar.py').read())



print(" ")
print("-------------------------------------------------------------------------")
print("Creating KPOINT file for each material ----------------------------------")
print("-------------------------------------------------------------------------")

#---------------------------------------------------
exec(open(dir_pseudo + '/cut_off_energy.py').read())
#---------------------------------------------------

files = list_folders(dir_out)
#------------------------------------------
t = 1.0; number = -1; n_passos = len(files)
#------------------------------------------

for i in range(len(files)):
    #-----------------------------------------------------------------------
    poscar = open(dir_out + '/' + files[i] + '/' + task[0] + '/POSCAR', "r")
    VTemp = poscar.readline().split()
    if (VTemp[0] == 'SAMBA'): n_materials = len(VTemp[1].replace('+', ' ').split())
    if (VTemp[0] != 'SAMBA'): n_materials = 1
    poscar.close()
    #-------------
    number += 1
    porc = (number/n_passos)*100        
    #---------------------------
    if (porc >= t and porc <= 100):
       print(f'Progress  {porc:>3,.0f}%')                 
       number += 1
       if (number == 1): t = 1
       if (number == 2): t = 1
       if (number >= 3): t = t + 1
       #--------------------------

    for m in range(len(task)):
        #------------------------------------------------------
        if (task[m][:6] == 'a-scan'):    k_dens = k_dens_a_scan
        if (task[m][:6] == 'z-scan'):    k_dens = k_dens_z_scan
        if (task[m][:7] == 'xy-scan'):   k_dens = k_dens_xy_scan
        if (task[m][:8] == 'xyz-scan'):  k_dens = k_dens_xyz_scan
        if (task[m][:5] == 'relax'):     k_dens = k_dens_relax
        if (task[m][:5] == 'bader'):     k_dens = k_dens_bader
        if (task[m][:3] == 'scf'):       k_dens = k_dens_scf
        if (task[m][:3] == 'dos'):       k_dens = k_dens_dos
        #---------------------------------------------------
        if (task[m][:5] != 'bader'):
           #------------------------------------------------------
           path_vaspkit = dir_out + '/' + files[i] + '/' + task[m]
           exec(open(dir_codes + '/kpoints.py').read())
           #------------------------
        if (task[m][:5] == 'bader'):
           files1 = list_folders(dir_out + '/' + files0[i] + '/' + task[m])
           for k in range(len(files1)):
               if (files1[k] != 'Charge_transfer'):
                  #------------------------------------------------------------------------
                  path_vaspkit = dir_out + '/' + files[i] + '/' + task[m] + '/' + files1[k]
                  exec(open(dir_codes + '/kpoints.py').read())
                  #-------------------------------------------


print(" ")
print("-------------------------------------------------------------------------")
print("Creating INCAR file for each material -----------------------------------")
print("-------------------------------------------------------------------------")


if (vdWDF != 'none' and vdW != 0): replace_type_vdW = str(vdW)
if (vdWDF == 'none' and vdW == 0): replace_type_vdW = str(vdW)
if (vdWDF == 'none' and vdW != 0): replace_type_vdW = str(vdW)
if (vdWDF != 'none' and vdW == 0): exec(open(dir_codes + '/vdW_DF.py').read())


#------------------------------------------
t = 1.0; number = -1; n_passos = len(files)
#------------------------------------------

for i in range(len(files)):
    #-----------------------------------------------------------------------
    poscar = open(dir_out + '/' + files[i] + '/' + task[0] + '/POSCAR', "r")
    VTemp = poscar.readline().split()
    if (VTemp[0] == 'SAMBA'): n_materials = len(VTemp[1].replace('+', ' ').split())
    if (VTemp[0] != 'SAMBA'): n_materials = 1
    poscar.close()
    #-------------
    number += 1
    porc = (number/n_passos)*100        
    #---------------------------
    if (porc >= t and porc <= 100):
       print(f'Progress  {porc:>3,.0f}%')                 
       number += 1
       if (number == 1): t = 1
       if (number == 2): t = 1
       if (number >= 3): t = t + 1
       #--------------------------


    #-----------------------------------------------------------------------
    poscar = open(dir_out + '/' + files[i] + '/' + task[0] + '/POSCAR', 'r')
    VTemp = poscar.readline().split()
    VTemp = poscar.readline();  param = float(VTemp)
    A1 = poscar.readline().split();  A1x = float(A1[0])*param;  A1y = float(A1[1])*param;  A1z = float(A1[2])*param;  A1 = np.array([A1x, A1y, A1z]);  mA1 = np.linalg.norm(A1)
    A2 = poscar.readline().split();  A2x = float(A2[0])*param;  A2y = float(A2[1])*param;  A2z = float(A2[2])*param;  A2 = np.array([A2x, A2y, A2z]);  mA2 = np.linalg.norm(A2)
    A3 = poscar.readline().split();  A3x = float(A3[0])*param;  A3y = float(A3[1])*param;  A3z = float(A3[2])*param;  A3 = np.array([A3x, A3y, A3z]);  mA3 = np.linalg.norm(A3)
    VTemp = poscar.readline()
    VTemp = poscar.readline().split()
    nion = 0
    for j in range(len(VTemp)):  nion += int(VTemp[j])
    poscar.close 
    #---------------------------------------------------
    lreal = '.FALSE.';  amin = '# AMIN';  algo = '# ALGO'
    if (nion > 30):  lreal = 'Auto'
    if (nion > 100):
       amin = 'AMIN'
       algo = 'ALGO = Fast'
    if ((mA1 > 50.0) or (mA2 > 50.0) or (mA3 > 50.0)):  amin = 'AMIN'
    #----------------------------------------------------------------


    #----------------
    ENCUT = ENCUT_min
    #-----------------------------------------------------------------------
    poscar = open(dir_out + '/' + files[i] + '/' + task[0] + '/POSCAR', 'r')
    #-----------------------------------------------------------------------
    for j in range(6):  VTemp1 = poscar.readline().split()
    VTemp2 = poscar.readline().split()
    poscar.close()
    #---------------------------
    for j in range(len(VTemp1)):
        temp = globals()['ENCUT_' + str(VTemp1[j])]    # Getting the value of the ENCUT variable for the corresponding atom.
        temp = temp*fator_encut
        if (ENCUT <= temp):  ENCUT = temp
    ENCUT = float(int(ENCUT) +1)


    for j in range(len(task)):
        #---------------
        type_kpoints = 1
        #------------------------------------------------
        if (task[j][:5] == 'bands'):     type_kpoints = 0
        if (task[j][:6] == 'a-scan'):    k_dens = 1/k_dens_a_scan
        if (task[j][:6] == 'z-scan'):    k_dens = 1/k_dens_z_scan
        if (task[j][:7] == 'xy-scan'):   k_dens = 1/k_dens_xy_scan
        if (task[j][:8] == 'xyz-scan'):  k_dens = 1/k_dens_xyz_scan
        if (task[j][:5] == 'relax'):     k_dens = 1/k_dens_relax
        if (task[j][:5] == 'bader'):     k_dens = 1/k_dens_bader
        if (task[j][:3] == 'scf'):       k_dens = 1/k_dens_scf
        if (task[j][:3] == 'dos'):       k_dens = 1/k_dens_dos
        #-----------------------------------------------------


        if (task[j][:5] != 'bader'):
           #--------------------------------------------
           dir_incar  = dir_inputs + '/INCAR_' + task[j]
           dir_output = dir_out + '/' + files[i] + '/' + task[j] + '/INCAR'
           #---------------------------------------------------------------
           shutil.copyfile(dir_incar, dir_output)
           #-------------------------------------
           if (vdWDF != 'none' and vdW == 0): 
              shutil.copyfile(dir_inputs + '/vdw_kernel.bindat',  dir_out + '/' + files[i] + '/' + task[j] + '/vdw_kernel.bindat')
           #--------------------------
           magmom = '' 
           for ijk in range(len(VTemp2)):  magmom += str(int(VTemp2[ijk])) + '*0 '
           #--------------------------
           if (task[j][-3:] == '.SO'):
              magmom = '' 
              for ijk in range(len(VTemp2)):  magmom += str(int(VTemp2[ijk])*3) + '*0 '
           #===============================================================
           # Updating the INCAR file ======================================
           #===============================================================
           with open(dir_output, "r") as file:  content = file.read()
           content = content.replace('replace_encut', str(ENCUT))
           content = content.replace('replace_lreal', str(lreal))
           content = content.replace('replace_vdW', str(vdW))
           content = content.replace('replace_ispin', 'ISPIN = ' + str(ispin))
           content = content.replace('# AMIN', str(amin))
           content = content.replace('# ALGO', str(algo))
           content = content.replace('# NCORE', 'NCORE = ' + str(NCORE))
           #--------------------
           if (dipol != 'none'):
              content = content.replace('# LDIPOL = .TRUE.', 'LDIPOL = .TRUE.')
              content = content.replace('# IDIPOL = 3', 'IDIPOL = 3')
              #------------------------------------------------------
              if (dipol == 'center_cell'):
                 content = content.replace('# DIPOL', 'DIPOL  = 0.5 0.5 0.5')
              #--------------------------------------------------------------
              if (dipol == 'center_mass'):
                 structure = Structure.from_file(dir_out + '/' + files[i] + '/' + task[j] + '/POSCAR')
                 total_mass = sum(site.species.weight for site in structure)
                 center_of_mass = sum(site.frac_coords * site.species.weight for site in structure) / total_mass
                 #-------------------------------------------------------------
                 content = content.replace('# DIPOL', 'DIPOL  = ' + str(center_of_mass[0]) + ' ' + str(center_of_mass[1]) + ' ' + str(center_of_mass[2]))
           #---------------------------------------------------------------------------------------
           if (vdWDF != 'none' and vdW == 0): content = content.replace('# vdW_DF', replace_vdW_DF)
           #---------------------------------------------------------------------------------------
           if ( (task[j][-3:] == '.SO') or (ispin == 2) ):
              if (magnet_mode == 'MAGMOM=0'):  content = content.replace('# MAGNETIC', 'MAGMOM = ' + magmom)
              if (magnet_mode == 'NUPDOWN=0'): content = content.replace('# MAGNETIC', 'NUPDOWN = 0')
           #---------------
           if (ispin == 1):
              if (magnet_mode == 'MAGMOM=0'):  content = content.replace('MAGNETIC', 'MAGMOM = ' + magmom)
              if (magnet_mode == 'NUPDOWN=0'): content = content.replace('MAGNETIC', 'NUPDOWN = 0')
           #---------------------------------------------------------------------------------------
           if (type_kpoints == 1):
              if (type_k_dens == 3):
                 content = content.replace('# KSPACING', 'KSPACING = ' + str(k_dens))
                 content = content.replace('# KGAMMA',   'KGAMMA = ' + 'False')
              if (type_k_dens == 4):
                 content = content.replace('# KSPACING', 'KSPACING = ' + str(k_dens))
                 content = content.replace('# KGAMMA',   'KGAMMA = ' + 'True')
           with open(dir_output, "w") as file: file.write(content)
           #---------------------------
           if (task[j][:5] == 'relax'):
              dir_incar  = dir_out + '/' + files[i] + '/' + task[j] + '/INCAR'
              dir_output = dir_out + '/' + files[i] + '/' + task[j] + '/INCAR_relax_frozen'
              shutil.copyfile(dir_incar, dir_output)
              with open(dir_output, "r") as file:  content = file.read()
              content = content.replace('NSW', 'NSW = 0   # ')
              with open(dir_output, "w") as file: file.write(content)
        #------------------------------------------------------------
        if (U_correction == 1):
           if (task[j] != 'a-scan' and task[j] != 'z-scan' and task[j] != 'xy-scan' and task[j] != 'xyz-scan' and task[j] != 'relax'):
              dir_poscar_file = dir_out + '/' + files[i] + '/' + task[j]
              shutil.copyfile(dir_codes + '/hubbard_correction.py', dir_out + '/' + files[i] + '/' + task[j] + '/hubbard_correction.py')
              exec(open(dir_out + '/' + files[i] + '/' + task[j] + '/hubbard_correction.py').read())
              os.remove(dir_out + '/' + files[i] + '/' + task[j] + '/hubbard_correction.py')
        #-----------------------------------------------------------------------------------

        if (task[j][:5] == 'bader' and n_materials > 1):
           #--------------------------------------------------------------
           files2 = list_folders(dir_out + '/' + files[i] + '/' + task[j])
           for k in range(len(files2)):
              if (files2[k] != 'Charge_transfer'):
                 #--------------------------------
                 poscar = open(dir_out + '/' + files[i] + '/' + task[j] + '/' + files2[k] + '/POSCAR', 'r')
                 for ijk in range(7):  VTemp3 = poscar.readline().split()
                 poscar.close()
                 #-------------
                 magmom = ''
                 for ijk in range(len(VTemp3)):  magmom += str(int(VTemp3[ijk])) + '*0 '
                 #--------------------------------
                 if (task[j][-3:] == '.SO'):
                    poscar = open(dir_out + '/' + files[i] + '/' + task[j] + '/' + files2[k] + '/POSCAR', 'r')
                    for ijk in range(7):  VTemp3 = poscar.readline().split()
                    poscar.close()
                    #-------------
                    magmom = ''
                    for ijk in range(len(VTemp3)):  magmom += str(int(VTemp3[ijk])*3) + '*0 '
                 #---------------------------------------------------------------------------
                 if (vdWDF != 'none' and vdW == 0): 
                    shutil.copyfile(dir_inputs + '/vdw_kernel.bindat',  dir_out + '/' + files[i] + '/' + task[j] + '/' + files2[k] + '/vdw_kernel.bindat')
                 #------------------------------------------------------------------------------------------------------------------------
                 dir_incar = dir_inputs + '/INCAR_' + task[j]
                 dir_output = dir_out + '/' + files[i] + '/' + task[j] + '/' + files2[k] + '/INCAR'
                 #---------------------------------------------------------------------------------
                 shutil.copyfile(dir_incar,  dir_output)
                 shutil.copyfile(dir_codes + '/bader',  dir_out + '/' + files[i] + '/' + task[j] + '/' + files2[k] + '/bader')
                 shutil.copyfile(dir_codes + '/chgsum.pl',  dir_out + '/' + files[i] + '/' + task[j] + '/' + files2[k] + '/chgsum.pl')
                 #------------------------------------------------------------
                 # Updating the INCAR file -----------------------------------
                 #------------------------------------------------------------
                 with open(dir_output, "r") as file:  content = file.read()
                 content = content.replace('replace_encut', str(ENCUT))
                 content = content.replace('replace_lreal', str(lreal))
                 content = content.replace('replace_vdW', str(vdW))
                 content = content.replace('replace_ispin', 'ISPIN = ' + str(ispin))
                 content = content.replace('# AMIN', str(amin))
                 content = content.replace('# ALGO', str(algo))
                 content = content.replace('# NCORE', 'NCORE = ' + str(NCORE))
                 #--------------------
                 if (dipol != 'none'):
                    content = content.replace('# LDIPOL = .TRUE.', 'LDIPOL = .TRUE.')
                    content = content.replace('# IDIPOL = 3', 'IDIPOL = 3')
                    #------------------------------------------------------
                    if (dipol == 'center_cell'):
                       content = content.replace('# DIPOL', 'DIPOL  = 0.5 0.5 0.5')
                    #--------------------------------------------------------------
                    if (dipol == 'center_mass'):
                       structure = Structure.from_file(dir_out + '/' + files[i] + '/' + task[j] + '/POSCAR')
                       total_mass = sum(site.species.weight for site in structure)
                       center_of_mass = sum(site.frac_coords * site.species.weight for site in structure) / total_mass
                       #-------------------------------------------------------------
                       content = content.replace('# DIPOL', 'DIPOL  = ' + str(center_of_mass[0]) + ' ' + str(center_of_mass[1]) + ' ' + str(center_of_mass[2]))
                 #---------------------------------------------------------------------------------------  
                 if (vdWDF != 'none' and vdW == 0): content = content.replace('# vdW_DF', replace_vdW_DF)
                 #---------------------------------------------------------------------------------------
                 if ( (task[j][-3:] == '.SO') or (ispin == 2) ):
                    if (magnet_mode == 'MAGMOM=0'):  content = content.replace('# MAGNETIC', 'MAGMOM = ' + magmom)
                    if (magnet_mode == 'NUPDOWN=0'): content = content.replace('# MAGNETIC', 'NUPDOWN = 0')
                 #---------------
                 if (ispin == 1):
                    if (magnet_mode == 'MAGMOM=0'):  content = content.replace('MAGNETIC', 'MAGMOM = ' + magmom)
                    if (magnet_mode == 'NUPDOWN=0'): content = content.replace('MAGNETIC', 'NUPDOWN = 0')
                 #--------------------------------------------------------- 
                 if (type_kpoints == 1):
                    if (type_k_dens == 3):
                       content = content.replace('# KSPACING', 'KSPACING = ' + str(k_dens))
                       content = content.replace('# KGAMMA',   'KGAMMA = ' + 'False')
                    if (type_k_dens == 4):
                       content = content.replace('# KSPACING', 'KSPACING = ' + str(k_dens))
                       content = content.replace('# KGAMMA',   'KGAMMA = ' + 'True')
                 with open(dir_output, "w") as file: file.write(content)
                 #-------------------------------------------------------
                 if (U_correction == 1):
                    dir_poscar_file = dir_out + '/' + files[i] + '/' + task[j] + '/' + files2[k]
                    shutil.copyfile(dir_codes + '/hubbard_correction.py', dir_out + '/' + files[i] + '/' + task[j] + '/' + files2[k] + '/hubbard_correction.py')
                    exec(open(dir_out + '/' + files[i] + '/' + task[j] + '/' + files2[k] + '/hubbard_correction.py').read())
                    os.remove(dir_out + '/' + files[i] + '/' + task[j] + '/' + files2[k] + '/hubbard_correction.py')
           #----------------------------------------------------------------
           # os.remove(dir_out + '/' + files[i] + '/' + task[j] + '/POSCAR')
           #----------------------------------------------------------------


#---------------------------------------------------------------------------------
# Deleting processes for systems with n_materials = 1 ----------------------------
#---------------------------------------------------------------------------------
for i in range(len(files)):
    #------------------------------------------------------------------------
    poscar = open(dir_out + '/' + files[i] + '/' + task[0] + '/POSCAR', "r")
    VTemp = poscar.readline().split()
    if (VTemp[0] == 'SAMBA'): n_materials = len(VTemp[1].replace('+', ' ').split())
    if (VTemp[0] != 'SAMBA'): n_materials = 1
    poscar.close()
    #---------------------
    if (n_materials == 1):
       tasks_delete = ['xyz-scan', 'xy-scan', 'z-scan', 'bader', 'bader.SO']
       for j in range(len(tasks_delete)):
           dir_delete = dir_out + '/' + files[i] + '/' + str(tasks_delete[j])
           if os.path.isdir(dir_delete): shutil.rmtree(dir_delete)


#---------------------------------------------------------------------------------
# Copying python codes to the main directory -------------------------------------
#---------------------------------------------------------------------------------
for i in range(len(files)):
    shutil.copyfile(dir_codes + '/data-base_json.py', dir_out + '/' + files[i] + '/data-base_json.py')
    shutil.copyfile(dir_codes + '/lattice_plot3d.py', dir_out + '/' + files[i] + '/lattice_plot3d.py')
    shutil.copyfile(dir_codes + '/output.py', dir_out + '/' + files[i] + '/output.py')
    shutil.copyfile(dir_codes + '/BZ_2D.py', dir_out + '/' + files[i] + '/BZ_2D.py')
    #-------------------------------------------------------------------------------
    dir_file = dir_out + '/' + files[i] + '/data-base_json.py'
    with open(dir_file, "r") as file:  content = file.read()
    content = content.replace('# replace_type_pseudo', 'pseudo_type = ' + "'" + str(replace_type_pseudo) + "'")
    content = content.replace('# replace_type_XC', 'exchange_correlation_functional = ' + "'" + str(replace_type_XC) + "'")
    content = content.replace('# replace_type_vdW', 'vdW = ' + "'" + str(replace_type_vdW) + "'")
    with open(dir_file, "w") as file: file.write(content)
    #----------------------------------------------------


#---------------------------------------
shutil.rmtree(dir_files + '/Structures')
os.rename(dir_files + '/Structures_Backup', dir_files + '/Structures')
#---------------------------------------------------------------------


######################################################
# Writing the job file to perform DFT calculations ###
######################################################
exec(open(dir_codes + '/job.py').read())
#---------------------------------------
