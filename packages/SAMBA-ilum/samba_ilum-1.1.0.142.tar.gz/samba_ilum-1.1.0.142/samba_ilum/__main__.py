# SAMBA_ilum Copyright (C) 2025
# GNU GPL-3.0 license


import numpy as np
import subprocess
import itertools
import shutil
import time
import sys
import os

#----------------
dir_codes = 'src'
#-----------------------------------------------------------------------------
if len(sys.argv) > 1 and os.path.isdir(sys.argv[-1]): dir_files = sys.argv[-1]
else: dir_files = os.getcwd()
dir_samba = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_samba)
#--------------------
print(f'{dir_samba}')
#--------------------

version = '1.1.0.142'

print(" ")
print("========================================= GNU GPL-3.0 license")
print(f'SAMBA_ilum v{version} Copyright (C) 2025 --------------------')
print("Adalberto Fazzio's research group (Ilum|CNPEM) --------------")
print("Author: Augusto de Lelis Araujo -----------------------------")
print("=============================================================")
print(" ")
print("   _____ ___    __  _______  ___       _ __              ")
print("  / ___//   |  /  |/  / __ )/   |     (_) /_  ______ ___ ")
print("""  \__ \/ /| | / /|_/ / __  / /| |    / / / / / / __ `___\ """)
print(" ___/ / ___ |/ /  / / /_/ / ___ |   / / / /_/ / / / / / /")
print("/____/_/  |_/_/  /_/_____/_/  |_|  /_/_/\__,_/_/ /_/ /_/ ")
print(f'Simulation and Automated Methods for Bilayer Analysis v{version}')
print(" ")

#------------------------------------------------
# Checking for updates for SAMBA ----------------
#------------------------------------------------
try:
    url = f"https://pypi.org/pypi/{'samba_ilum'}/json"
    response = requests.get(url)
    dados = response.json()
    current_version = dados['info']['version']; current_version = str(current_version)
    if (current_version != version):
       print(" ")
       print("--------------------------------------------------------------")
       print("        !!!!! Your SAMBA version is out of date !!!!!         ")
       print("--------------------------------------------------------------")
       print("    To update, close the SAMBA and enter into the terminal:   ")
       print("                 pip install --upgrade samba                  ")
       print("--------------------------------------------------------------")
       print(" ")
       print(" ")
    ...
except Exception as e:
    print("--------------------------------------------------------------")
    print("    !!!! Unable to verify the current version of SAMBA !!!!   ")
    print("--------------------------------------------------------------") 
    print(" ")


# ------------------------------------------------------------------------------
# Checking if the "run.input" file exists --------------------------------------
# ------------------------------------------------------------------------------
run_input = 'not'
#----------------
if os.path.isfile(dir_files + '/run.input'): run_input = 'yes'
else: run_input = 'not'
# ----------------------
if (run_input == 'yes'):
   run = open(dir_files + '/run.input', "r")
   VTemp = run.readline().split()
   if (len(VTemp) == 3): tarefa = int(VTemp[2])


if(run_input == 'not'):
   print("######################################################################")
   print("# What do you want to run? ===========================================")
   print("# ====================================================================")
   print("# [0] Setup: Initialize configuration files for options [1] and [2]   ")
   print("# [1] Build: Generate twisted hetero BiLayers                         ")
   print("# [2] High-Throughput VASP Workflow                                   ")
   print("#     (Generate VASP inputs and job execution)                        ")
   print("# [3] Extract internal Workflow settings for customizing option [2]   ")
   print("# [4] Extract Monolayers/Slabs from bulk material                     ")
   print("######################################################################")
   print("A tutorial on how to use the SAMBA is available on GitHub at the link:")
   print("https://github.com/Augusto-de-Lelis-Araujo/SAMBA/blob/main/README.md  ")
   print("######################################################################")
   tarefa = input(" "); tarefa = int(tarefa)
   print(" ")


if (tarefa == 0):
   shutil.copyfile(dir_codes + '/BibTeX.dat', dir_files + '/BibTeX.dat')
   shutil.copyfile(dir_codes + '/INPUTS/SAMBA_WorkFlow.input', dir_files + '/SAMBA_WorkFlow.input')
   shutil.copyfile(dir_codes + '/INPUTS/SAMBA_HeteroStructure.input', dir_files + '/SAMBA_HeteroStructure.input')

if (tarefa == 1):
   #--------------------------------------------------------------------
   shutil.copyfile(dir_codes + '/BibTeX.dat', dir_files + '/BibTeX.dat')
   #--------------------------------------------------------------------------------------------------
   # Checking if the "SAMBA_HeteroStructure.input" file exists, if it does not exist it is created ---
   #--------------------------------------------------------------------------------------------------
   if os.path.isfile(dir_files + '/SAMBA_HeteroStructure.input'):
      0 == 0
   else:
      shutil.copyfile(dir_codes + '/SAMBA_HeteroStructure.input', dir_files + '/SAMBA_HeteroStructure.input')
      #------------------------------------------------------------------------------------------------------
      print(" ")
      print("==============================================================")
      print("Generated SAMBA_HeteroStructure.input file !!! ===============")
      print("--------------------------------------------------------------")
      print("Configure the SAMBA_HeteroStructure.input file and run the ---")
      print("                                                code again ---")
      print("==============================================================")
      print(" ")
      #--------------------------------------------------------
      confirmacao = input (" "); confirmacao = str(confirmacao)
      sys.exit()
      #---------

   #------------------------------------------------------------
   exec(open(dir_files + '/SAMBA_HeteroStructure.input').read())
   #------------------------------------------------------------
   separacao1 = separation_1
   separacao2 = separation_2
   #------------------------
   if (loop_ht == 0):
      Lattice1 = Lattice1.replace(".vasp","") + ".vasp"
      Lattice2 = Lattice2.replace(".vasp","") + ".vasp"
      Lattice3 = Lattice3.replace(".vasp","") + ".vasp"
   #---------------------------------------------------

   #=============================================================
   # Fixing the coordinates of POSCAR files in direct form ======
   #=============================================================
   dir_files_in = dir_poscar 
   exec(open(dir_codes + '/poscar_fix_direct_coord.py').read())
   #=============================================================
   # Checking the structure of POSCAR files, regarding the ======
   # rotation angle in relation to the z-axis ===================
   #=============================================================
   exec(open(dir_codes + '/cell_check.py').read())
   #=============================================================

   if (loop_ht == 1):
      #--------------
      n_Lattice = 2
      #--------------------------------------------------------------------------
      # Checking for existence of non-empty file 'check_list_loop.txt' ----------
      #--------------------------------------------------------------------------
      temp_check = 0
      #-------------
      check_list_dir = dir_files + '/check_list_loop.txt'
      if os.path.exists(check_list_dir) and os.path.getsize(check_list_dir) != 0:
         check = np.loadtxt(check_list_dir, dtype='str');  check.shape
         n_ht = check[:,0];  mat1 = check[:,1];  mat2 = check[:,2]
         temp_check = 1
      #------------------------------
      if (temp_check == 0): nloop = 0
      if (temp_check == 1): nloop = len(mat1)
      #--------------------------------------
      temp_dir = dir_files + '/' + dir_poscar
      files0 = [name for name in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, name))]  # Listando os arquivos dentro do diretório "dir_poscar"
      files = sorted(files0)
      #---------------------------------------------------------------------
      # bilayer_materials = list(itertools.combinations(files, 2))
      # for material in files:  bilayer_materials.append((material, material))
      #---------------------------------------------------------------------
      bilayer_materials = []
      for material1 in files:
          for material2 in files:
              bilayer_materials.append((material1, material2))
      #-------------------------------------------------------
      vistos = set()   
      new_bilayer_materials = []                      # List to store unique elements
      for elemento in bilayer_materials:          
          elem_ordenado = tuple(sorted(elemento))     # Sorts the elements (ignoring permutations)
          if elem_ordenado not in vistos:
              new_bilayer_materials.append(elemento)  # Adding elements that do not have permutations
              vistos.add(elem_ordenado)
      bilayer_materials = new_bilayer_materials       # Saving the new list with the permutations removed
      #-------------------------------------------------------
      for loop in range(len(bilayer_materials)):
          Lattice1 = bilayer_materials[loop][0]
          Lattice2 = bilayer_materials[loop][1]
          Lattice3 = ''
          #------
          run = 1
          #-------------------
          if (temp_check == 1):
             for mnt in range(len(mat1)):
                 temp0_mat1 = str(mat1[mnt]); temp0_mat2 = str(mat2[mnt])
                 temp1_mat1 = Lattice1.replace('.vasp', ''); temp1_mat2 = Lattice2.replace('.vasp', '')
                 if ( (temp0_mat1 == temp1_mat1 and temp0_mat2 == temp1_mat2) or (temp0_mat1 == temp1_mat2 and temp0_mat2 == temp1_mat1) ): run = 0
                 #---------------------------------------------------------------------------------------------------------------------------------

          if ( temp_check == 0 or (temp_check == 1 and run == 1) ):
             #------------------------------------------------------------------
             # Heterostructure loop check_list ---------------------------------
             #------------------------------------------------------------------
             nloop += +1
             if (nloop >= 0    and nloop < 10):   nloop2 = '000' + str(nloop)
             if (nloop >= 10   and nloop < 100):  nloop2 = '00'  + str(nloop)
             if (nloop >= 100  and nloop < 1000): nloop2 = '0'   + str(nloop)
             if (nloop >  1000):                  nloop2 =         str(nloop)
             dir_loop = str(nloop2) + '--' + Lattice1.replace('.vasp', '') + '--' + Lattice2.replace('.vasp', '')
             #---------------------------------------------------------------------------------------------------
             check_list = open(dir_files + '/check_list_loop.txt', 'a')
             t_Lattice1 = Lattice1.replace('.vasp', ' ');  t_Lattice2 = Lattice2.replace('.vasp', ' ')   
             if (n_Lattice == 2):
                check_list.write(f'{nloop2} {t_Lattice1} {t_Lattice2} \n')
             if (n_Lattice == 3):
                t_Lattice3 = Lattice3.replace('.vasp', ' ')
                check_list.write(f'{nloop2} {t_Lattice1} {t_Lattice2} {t_Lattice3} \n')
             check_list.close()
             #-----------------
             try:
                 exec(open(dir_codes + '/HeteroStructure_Generator.py').read())
                 ...
             except SystemExit as e: 0 == 0
             except Exception as e: 0 == 0     
             #----------------------------

   if (loop_ht == 2):
      #--------------
      n_Lattice = 2
      #-------------------------------------------------------------------
      # Checking for existence of non-empty file 'check_list_loop.txt' ---
      #-------------------------------------------------------------------
      temp_check = 0
      #-------------
      check_list_dir = dir_files + '/check_list_loop.txt'
      if os.path.exists(check_list_dir) and os.path.getsize(check_list_dir) != 0:
         check = np.loadtxt(check_list_dir, dtype='str');  check.shape
         if (check.ndim == 1): check = check.reshape(1, -1)  # Ensures it's 2D even if there's only one line.
         n_ht = check[:,0];  mat1 = check[:,1];  mat2 = check[:,2]
         temp_check = 1
      #------------------------------
      if (temp_check == 0): nloop = 0
      if (temp_check == 1): nloop = len(mat1)
      #--------------------------------------
      # Defining Directories ----------------
      #--------------------------------------
      dir_p1 = dir_files + '/POSCAR.1'
      dir_p2 = dir_files + '/POSCAR.2'
      dir_target = dir_files + '/POSCAR'
      if not os.path.exists(dir_target): os.makedirs(dir_target)
      #---------------------------------------------------------
      # Listing files ------------------------------------------
      #---------------------------------------------------------
      files1_0 = [name for name in os.listdir(dir_p1) if os.path.isfile(os.path.join(dir_p1, name))]
      files2_0 = [name for name in os.listdir(dir_p2) if os.path.isfile(os.path.join(dir_p2, name))]
      files1 = sorted(files1_0)
      files2 = sorted(files2_0)
      #----------------------------------------------------
      # Loop: Cartesian Product (All of 1 vs. All of 2) ---
      #----------------------------------------------------
      for item1 in files1:
          for item2 in files2:
             Lattice1 = item1
             Lattice2 = item2
             Lattice3 = ''
             #------
             run = 1
             #----------------------------
             # Checkpoint Verification ---
             #----------------------------
             if (temp_check == 1):
                for mnt in range(len(mat1)):
                    temp0_mat1 = str(mat1[mnt]); temp0_mat2 = str(mat2[mnt])
                    temp1_mat1 = Lattice1.replace('.vasp', ''); temp1_mat2 = Lattice2.replace('.vasp', '')
                    # Checks if the pair has already been calculated                    
                    if ( (temp0_mat1 == temp1_mat1 and temp0_mat2 == temp1_mat2) or (temp0_mat1 == temp1_mat2 and temp0_mat2 == temp1_mat1) ): run = 0 
             #--------------------------------------------------------
             if ( temp_check == 0 or (temp_check == 1 and run == 1) ):
                #------------------------------------------------------------------
                # Heterostructure loop check_list ---------------------------------
                #------------------------------------------------------------------
                nloop += +1
                if (nloop >= 0    and nloop < 10):   nloop2 = '000' + str(nloop)
                if (nloop >= 10   and nloop < 100):  nloop2 = '00'  + str(nloop)
                if (nloop >= 100  and nloop < 1000): nloop2 = '0'   + str(nloop)
                if (nloop >  1000):                  nloop2 =        str(nloop)
                #---------------------------------------------------------
                check_list = open(dir_files + '/check_list_loop.txt', 'a')
                t_Lattice1 = Lattice1.replace('.vasp', ' ');  t_Lattice2 = Lattice2.replace('.vasp', ' ')   
                check_list.write(f'{nloop2} {t_Lattice1} {t_Lattice2} \n')
                check_list.close()
                #----------------------------------------------------
                # Copying files to the 'Poscar' folder --------------
                #----------------------------------------------------
                shutil.copyfile(dir_p1 + '/' + Lattice1, dir_target + '/' + Lattice1)
                shutil.copyfile(dir_p2 + '/' + Lattice2, dir_target + '/' + Lattice2)
                #--------------------------------------------------------------------------------------------
                # Updating the dir_poscar variable to point to the folder where the files are now located ---
                #--------------------------------------------------------------------------------------------
                dir_poscar = 'POSCAR' 
                dir_files_in = dir_poscar 
                #----------------------------------------------------------
                # Fixing the coordinates of POSCAR files in direct form ---
                #-----------------------------------------------------------------------------------------
                # Run the fix in the 'POSCAR' folder to ensure correct formatting before the generator ---
                #-----------------------------------------------------------------------------------------
                exec(open(dir_codes + '/poscar_fix_direct_coord.py').read())
                #-----------------------------------------------------------
                try:
                    exec(open(dir_codes + '/HeteroStructure_Generator.py').read())
                except SystemExit as e: 0 == 0
                except Exception as e: 
                    print(f"Error processing {Lattice1} + {Lattice2}: {e}")
                    0 == 0      
                #--------------------------------------------------------------------------           
                # Optional: Clean the POSCAR folder after use to prevent buildup or clutter
                # if os.path.exists(dir_target + '/' + Lattice1): os.remove(dir_target + '/' + Lattice1)
                # if os.path.exists(dir_target + '/' + Lattice2): os.remove(dir_target + '/' + Lattice2)
                #---------------------------------------------------------------------------------------

   if (loop_ht == 0): exec(open(dir_codes + '/HeteroStructure_Generator.py').read())


if (tarefa == 2):
   #--------------------------------------------------------------------
   shutil.copyfile(dir_codes + '/BibTeX.dat', dir_files + '/BibTeX.dat')
   #-------------------------------------------------------------------------------------------
   # Checking if the "SAMBA_WorkFlow.input" file exists, if it does not exist it is created ---
   #-------------------------------------------------------------------------------------------
   if os.path.isfile(dir_files + '/SAMBA_WorkFlow.input'):
      0 == 0
   else:
      shutil.copyfile(dir_codes + '/SAMBA_WorkFlow.input', dir_files + '/SAMBA_WorkFlow.input')
      #----------------------------------------------------------------------------------------
      print(" ")
      print("==============================================================")
      print("SAMBA_WorkFlow.input file generated !!! ======================")
      print("--------------------------------------------------------------")
      print("Configure the SAMBA_WorkFlow.input file and run the code again")
      print("==============================================================")
      print(" ")
      #--------------------------------------------------------
      confirmacao = input (" "); confirmacao = str(confirmacao)
      sys.exit()
      #---------

   #----------------------------------------------------
   # Checking if the "WorkFlow_INPUTS" folder exists ---
   #----------------------------------------------------
   if os.path.isdir(dir_files + '/WorkFlow_INPUTS'):
      dir_inputs = dir_files + '/WorkFlow_INPUTS'
   else:
      dir_inputs = dir_codes + '/INPUTS'
   #------------------------------------------------------
   dir_inputs_vasprocar = dir_inputs + '/inputs_VASProcar'
   #------------------------------------------------------

   #------------------------------------------------
   # Checking if the "POTCAR" folder exists --------
   #------------------------------------------------
   if os.path.isdir(dir_files + '/POTCAR'):
      0 == 0
   else:
      print('')
      print('Warning: -----------------------------------------')
      print('Missing POTCAR folder and POTCAR_[ion] files -----')
      print('Enter and then press [ENTER] to continue ---------')
      print('--------------------------------------------------')
      confirmacao = input (" "); confirmacao = str(confirmacao)
   #------------------------------------
   dir_pseudo = dir_files + '/POTCAR'
   shutil.copyfile(dir_codes + '/_info_pseudo.py', dir_pseudo + '/_info_pseudo.py')
   os.chdir(dir_pseudo)
   exec(open(dir_pseudo + '/_info_pseudo.py').read())
   os.chdir(dir_samba)
   #------------------

   #-----------------------------------------------------
   exec(open(dir_files + '/SAMBA_WorkFlow.input').read())
   #-----------------------------------------------------
   vacuo = vacuum
   #-------------
   dir_out   = dir_files + '/' + dir_o
   #----------------------------------
   task = []
   for i in range(len(tasks)):
       if (tasks[i] == 'a-scan' or tasks[i] == 'z-scan' or tasks[i] == 'xy-scan' or tasks[i] == 'xyz-scan' or tasks[i] == 'relax'):  task.append(tasks[i])
       for j in range(len(type)):
           if (type[j] == 'sem_SO'):  rot = '' 
           if (type[j] == 'com_SO'):  rot = '.SO' 
           if (tasks[i] != 'a-scan' and tasks[i] != 'z-scan' and tasks[i] != 'xy-scan' and tasks[i] != 'xyz-scan' and tasks[i] != 'relax'):  task.append(tasks[i] + rot)
   #--------------------------------------------------------------------------------------------------------------------------------------------------------------------

   #=============================================================
   # Fixing the coordinates of POSCAR files in direct form ======
   #=============================================================
   dir_files_in = 'Structures'
   exec(open(dir_codes + '/poscar_fix_direct_coord.py').read())
   #=============================================================
   exec(open(dir_codes + '/make_files.py').read())
   #=============================================================


if (tarefa == 3):
   shutil.copyfile(dir_codes + '/BibTeX.dat', dir_files + '/BibTeX.dat')
   shutil.copytree(dir_codes + '/INPUTS', dir_files + '/WorkFlow_INPUTS')


if (tarefa == 4):
   shutil.copyfile(dir_codes + '/BibTeX.dat', dir_files + '/BibTeX.dat')
   exec(open(dir_codes + '/miller_confine.py').read())


print(" ")
print("=============")
print("Completed ===")
print("=============")
print(" ")
