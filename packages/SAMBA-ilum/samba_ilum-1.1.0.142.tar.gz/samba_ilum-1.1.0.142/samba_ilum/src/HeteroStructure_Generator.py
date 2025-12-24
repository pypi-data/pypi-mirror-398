# SAMBA_ilum Copyright (C) 2025
# GNU GPL-3.0 license


# from pymatgen.io.vasp import Poscar
# from pymatgen.core import Structure
# from pymatgen.analysis.structure_matcher import StructureMatcher
# from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
#----------------------------------------------------------
# import numpy as np
import filecmp
import hashlib
import shutil
import math
import uuid
import json
import sys  
import os


#---------------------------------------------
crit_mod_vector =       float(crit_mod_vector)
crit_distorc_lattice =  float(crit_distorc_lattice)
crit_angle_perc =       float(crit_angle_perc)
crit_angle_diff =       float(crit_angle_diff)
crit_area =             float(crit_area)
#--------------------------------------------------------
if (crit_mod_vector <= 0.0):       crit_mod_vector = 0.01
if (crit_distorc_lattice <= 0.0):  crit_distorc_lattice = 0.01
if (crit_angle_perc <= 0.0):       crit_angle_perc = 0.01
if (crit_angle_diff <= 0.0):       crit_angle_diff = 0.01
if (crit_area <= 0.0):             crit_area = 0.01
#--------------------------------------------------

  
#--------------------------------------------------------------------------------------------------------------------
vLattice = [dir_poscar + '/' + Lattice1, dir_poscar + '/' + Lattice2, dir_poscar + '/' + Lattice3];  n = n_Lattice -2
label_htstructure = '';  label_material = ['']*n_Lattice
dZ = [0]*3;  dens_ions = [0]*3;  n = 0
#----------------------------------------------------------------------------------------
orig = 0   # [0] The center of the SuperCell will be the origin of the coordinate system.
           # [1] The center of the SuperCell's vector A1 will be the origin of the coordinate system.
#----------------------------------------------------------------------------------------------------
if (mismatch_type < 0 or mismatch_type > 3): mismatch_type = 0
#-------------------------------------------------------------


#----------------------------------------------------------
fator_n = 1 -(crit_area/100);  fator_p = 1 +(crit_area/100)
area_unit_cell = [0]*3
vector_areas = []
#-----------------
d_origin_x = [0]*3
d_origin_y = [0]*3
#-----------------


#----------------------------------------------------------------------------------------------------
A1x0 = [];  A1y0 = [];  A2x0 = [];  A2y0 = []  # Lists to store the vectors A1 and A2 of each lattice
#----------------------------------------------------------------------------------------------------
for k in range(n_Lattice):
    #---------------------
    Lattice = dir_files + '/' + vLattice[k]
    poscar = open(Lattice, "r")
    #-------------------------------------------
    for i in range(2): VTemp = poscar.readline()
    param = float(VTemp)
    #-------------------------------------------
    A1 = poscar.readline().split();  A1x = float(A1[0])*param;  A1y = float(A1[1])*param;  A1z = float(A1[2])*param  
    A2 = poscar.readline().split();  A2x = float(A2[0])*param;  A2y = float(A2[1])*param;  A2z = float(A2[2])*param  
    A3 = poscar.readline().split();  A3x = float(A3[0])*param;  A3y = float(A3[1])*param;  A3z = float(A3[2])*param  
    #--------------------------------------------------------------------------------------------------------------
    A1x0.append(A1x);  A1y0.append(A1y);  A2x0.append(A2x);  A2y0.append(A2y)   # Storing the vectors A1 and A2 of each lattice
    #--------------------------------------------------------------------------------------------------------------------------
    # Vectors A1 and A2
    A1 = np.array([A1x, A1y, 0.0])
    A2 = np.array([A2x, A2y, 0.0])
    #-------------------------------------------------------
    # unit cell area
    Area = np.linalg.norm(np.cross(A1, A2))
    area_unit_cell[k] = Area
    #-------------------------------------------------------
    nion = 0
    for i in range(2): VTemp = poscar.readline().split()
    for i in range(len(VTemp)):  nion += int(VTemp[i])
    #-------------------------------------------------------
    dens_ions[k] = nion/Area  # Obtaining the ion density of each material
    #-----------------------
    poscar.close()
    #-------------


#--------------------------------------------------------------------------------------------------------------------------------------------
# Obtaining the smallest rotation angle of the upper layer(s) in order to adjust the final rotation angle obtained in the heterostructure ---
#--------------------------------------------------------------------------------------------------------------------------------------------
for k in range(n_Lattice):
    #---------------------
    estrutura = Structure.from_file(dir_files + '/' + vLattice[k])
    sga = SpacegroupAnalyzer(estrutura, symprec=1e-3)
    operacoes = sga.get_symmetry_operations()
    angulos_z = []
    #-------------------
    for op in operacoes:
        R = op.rotation_matrix
        if int(round(np.linalg.det(R))) != 1: continue
        #----------------------
        z = np.array([0, 0, 1])
        Rz = R @ z
        #--------------------------------
        if np.allclose(Rz, z, atol=1e-3):
           Rxy = R[:2, :2]
           trace = np.trace(Rxy)
           cos_theta = trace / 2
           cos_theta = np.clip(cos_theta, -1.0, 1.0)
           angle = np.arccos(cos_theta)
           angle_deg = round(np.degrees(angle), 4)
           #-------------------------------------------------------------------------------------
           if 0.1 < angle_deg < 360.0 and angle_deg not in angulos_z: angulos_z.append(angle_deg)
    #--------------------------------------------------------------------------------------------
    if (k == 1):
       if angulos_z:  rot_z_2 = min(angulos_z)
       else:          rot_z_2 = 0.0
    #-----------------------------------------
    if (k == 2):
       if angulos_z:  rot_z_3 = min(angulos_z)
       else:          rot_z_3 = 0.0
    #-----------------------------------------


#---------------------------------------------------------------------------------------------------------------------------------------
# Estimating the area of each supercell (referring to each Lattice), capable of housing the range of ions [ions_crit_i, ions_crit_f] ---
#---------------------------------------------------------------------------------------------------------------------------------------
for k in range(n_Lattice):
    #---------------------
    n_ions = 0
    #---------
    for kk in range(n_Lattice): 
        #----------------------
        n_ions += area_unit_cell[k]*dens_ions[kk]
    #--------------------------------------------
    for kkk in range(1, 101):
        new_nions = n_ions*kkk
        if ( new_nions >= (ions_crit_i*fator_n) and new_nions  <= (ions_crit_f*fator_p) ): vector_areas.append(area_unit_cell[k]*kkk)
#----------------------------
temp_list = set(vector_areas)
vector_areas = list(temp_list)
#-----------------------------


#---------------------------------------------------------
# Checking for the existence of the 'output' directory ---
#---------------------------------------------------------
if os.path.isdir(dir_files + '/' + 'output'):
   0 == 0
else:
   os.mkdir(dir_files + '/' + 'output')
#--------------------------------------
diret = dir_files + '/' + 'output/'
#----------------------------------


#-----------
formula = []
id_materials = []
#----------------


#===================================================================
# Getting the height of different materials ========================
#===================================================================
for k in range(n_Lattice):
    #------------------------------------------------
    poscar = open(dir_files + '/' + vLattice[k], "r")
    #------------------------------------------------
    for i in range(2): VTemp = poscar.readline()
    param = float(VTemp)
    #---------------------------------------------------
    for i in range(3): VTemp = poscar.readline().split()
    fator_Z = float(VTemp[2])*param; fator_Z = abs(fator_Z)
    #------------------------------------------------------
    passo = 0
    VTemp1 = poscar.readline().split()
    VTemp2 = poscar.readline().split()
    for i in range(len(VTemp1)):
        passo += int(VTemp2[i])
        # label_material[k] += str(VTemp1[i]) + str(VTemp2[i])
        label_material[k] += str(VTemp1[i])
        if (i < (len(VTemp1) -1)):  label_material[k] += '_' 
    label_htstructure += label_material[k]
    if (k < (n_Lattice -1)): label_htstructure += '+'
    #------------------------------------------------
    VTemp = poscar.readline()
    #------------------------
    vZ = []
    for i in range(passo):
        VTemp = poscar.readline().split()
        vZ.append(float(VTemp[2]))
    #----------------------------------
    dZ[k] = (max(vZ) - min(vZ))*fator_Z
    #----------------------------------
    poscar.close()
    #-------------


for k in range(n_Lattice):
    n += 1
    #-------------------------------------
    ion_label = []; ion_label_string  = ''
    ion_label_temp  = []; ion_label_temp_string  = ''
    nlabel = []; nions = 0
    #--------------------------------------
    Lattice = dir_files + '/' + vLattice[k]
    label = 'Lattice' + str(k+1)


    #=========================================================
    # Getting the Lattices ID ================================
    #=========================================================
    poscar = open(Lattice, "r")
    VTemp = poscar.readline().split()
    poscar.close()
    #------------------------------------------------------------
    if (VTemp[0] == 'SAMBA'): id_materials.append(str(VTemp[-1]))
    if (VTemp[0] != 'SAMBA'): id_materials.append('none') 
    #----------------------------------------------------


    #======================================================================
    # Copying the POSCAR files to the 'output' directory ==================
    #======================================================================
    structure = Poscar.from_file(Lattice).structure
    supercell = structure.copy()
    supercell.make_supercell([1,1,1])
    Poscar(supercell).write_file(diret + 'temp0_' + label + '.vasp')


    #=========================================================
    # Obtaining the Stoichiometry of Lattices ================
    #=========================================================
    poscar = open(diret + 'temp0_' + label + '.vasp', "r")
    for i in range(5): VTemp = poscar.readline()
    VTemp0 = poscar.readline().split()
    VTemp1 = poscar.readline().split()
    poscar.close()
    #----------------
    temp_formula = ''
    #---------------------------
    for i in range(len(VTemp0)):
        temp_formula += str(VTemp0[i])
        if (str(VTemp1[i]) != '1'): temp_formula += str(VTemp1[i])
    formula.append(temp_formula) 
    #---------------------------


    #==========================================================================
    # Getting the z-axis height of different materials ========================
    #==========================================================================
    poscar = open(diret + 'temp0_' + label + '.vasp', "r")
    #-----------------------------------------------------
    for i in range(2): VTemp = poscar.readline()
    param = float(VTemp)
    #---------------------------------------------------
    for i in range(3): VTemp = poscar.readline().split()
    fator_Z = float(VTemp[2])*param; fator_Z = abs(fator_Z)
    #------------------------------------------------------
    passo = 0
    VTemp1 = poscar.readline().split()
    VTemp2 = poscar.readline().split()
    for i in range(len(VTemp1)):
        passo += int(VTemp2[i])
        # label_material[k] += str(VTemp1[i]) + str(VTemp2[i])
        label_material[k] += str(VTemp1[i])
        if (i < (len(VTemp1) -1)):  label_material[k] += '_' 
    # label_htstructure += label_material[k]
    # if (k < (n_Lattice -1)): label_htstructure += '+'
    #--------------------------------------------------
    VTemp = poscar.readline()
    #------------------------
    vZ = []
    for i in range(passo):
        VTemp = poscar.readline().split()
        vZ.append(float(VTemp[2]))
    #-----------------------------
    minZ = min(vZ)
    for i in range(len(vZ)): vZ[i] = vZ[i] - minZ
    #--------------------------------------------
    poscar.close()
    #-------------


    #======================================================================================================
    # Shifting the ions to the bottom of the lattice (Z = 0.0) and modifying the magnitude of vector A3 ===
    #======================================================================================================
    if (n_Lattice == 2):  d = (dZ[0] + dZ[1] + separacao1 + vacuum)/param                        
    if (n_Lattice == 3):  d = (dZ[0] + dZ[1] + dZ[2] + separacao1 + separacao2 + vacuum)/param
    #-----------------------------------------------------------------------------------------
    poscar = open(diret + 'temp0_' + label + '.vasp', "r")
    poscar_new = open(diret + 'temp1_' + label + '.vasp', "w")
    #---------------------------------------------------------
    for i in range(4):
        VTemp = poscar.readline()
        poscar_new.write(f'{VTemp}')
    #-------------------------------
    VTemp = poscar.readline().split()
    poscar_new.write(f'{VTemp[0]} {VTemp[0]} {d:.19f} \n')
    #-----------------------------------------------------
    for i in range(3):
        VTemp = poscar.readline()
        poscar_new.write(f'{VTemp}')
    #-------------------------------
    for i in range(passo):
        VTemp = poscar.readline().split()
        poscar_new.write(f'{float(VTemp[0])} {float(VTemp[1])} {(float(VTemp[2]) -minZ)*(fator_Z/d)} \n')
    #-------------
    poscar.close()
    poscar_new.close()
    #-----------------


    #==========================================================================================
    # Obtained and stored all possible cells (linear combinations of vectors A1 and A2) =======
    #==========================================================================================
    poscar = open(diret + 'temp1_' + label + '.vasp', "r")
    poscar_new = open(diret + 'Coord_Supercell_Lattice' + str(k+1) + '.dat', "w")
    #----------------------------------------------------------------------------
    for i in range(2): VTemp = poscar.readline()
    param = float(VTemp)
    #-------------------------------------------
    A1 = poscar.readline().split();  A1x = float(A1[0])*param;  A1y = float(A1[1])*param;  A1z = float(A1[2])*param  
    A2 = poscar.readline().split();  A2x = float(A2[0])*param;  A2y = float(A2[1])*param;  A2z = float(A2[2])*param  
    A3 = poscar.readline().split();  A3x = float(A3[0])*param;  A3y = float(A3[1])*param;  A3z = float(A3[2])*param  
    #--------------------------------------------------------------------------------------------------------------
    # Vectors A1 and A2
    A1 = np.array([A1x, A1y])
    A2 = np.array([A2x, A2y])
    #----------------------------------------------------
    for ii in range(cell_fator[0]*(-1), cell_fator[0]+1):
        for iii in range(cell_fator[1]*(-1), cell_fator[1]+1):
            if (ii !=0 or iii != 0):
               #-----------------------------
               coord_x = (ii*A1x) + (iii*A2x)
               coord_y = (ii*A1y) + (iii*A2y)
               coord_z = A3z
               #----------------------------------------------
               m_vector = ((coord_x)**2 + (coord_y)**2)**(0.5)
               #---------------------------------------------------------------------------------------------------
               poscar_new.write(f'{coord_x:>28,.21f} {coord_y:>28,.21f} {coord_z:>28,.21f} {m_vector:>28,.21f} \n')
    #-----------------
    poscar.close()
    poscar_new.close()
    #-----------------


    #==========================================================================================
    # Obtained and stored all possible cells (linear combinations of vectors A1 and A2) =======
    #==========================================================================================

    dir_cells_Lattice = 'cells_Lattice' + str(k+1)
    diret_structures  = 'Lattice' + str(k+1)

    #------------------------------------------------------------
    # Checking for existence of 'dir_cells_Lattice' directory ---
    #------------------------------------------------------------
    if os.path.isdir(diret + dir_cells_Lattice):
       0 == 0
    else:
       os.mkdir(diret + dir_cells_Lattice)
    #-------------------------------------

    #-------------------------------------------------------------------
    # Checking for the existence of the 'diret_structures' directory ---
    #-------------------------------------------------------------------
    if os.path.isdir(diret + diret_structures):
       0 == 0
    else:
       os.mkdir(diret + diret_structures)
    #------------------------------------

    #--------------------------------------------------------------------------------------------------------
    SLattice = np.loadtxt(diret + 'Coord_Supercell_Lattice' + str(k+1) + '.dat', dtype='str'); SLattice.shape
    #--------------------------------------------------------------------------------------------------------
    vx = SLattice[:,0]; vy = SLattice[:,1]; vz = SLattice[:,2]; dist = SLattice[:,3]
    #-------------------------------------------------------------------------------


    print(f' ')
    print(f'=================================================================================================')
    print(f'Step {n}: Analyzing all possible cells of the {k+1} Material (Linear combinations of vectors A1 and A2)')
    print(f'=================================================================================================')

    #--------------------------------------------------
    temp = 1.0; number = -1; n_passos = len(vx)*len(vx)
    #-----------------------
    for i in range(len(vx)):
        for j in range(len(vx)):
            #---------------------------
            number += 1;  cell_write = 0
            porc = (number/n_passos)*100        
            #---------------------------
            if porc >= temp:
               bar_length = 50
               filled_length = int(bar_length * porc // 100)
               bar = '#' * filled_length + '-' * (bar_length - filled_length)
               print(f'\rProgress: |{bar}| {porc:.1f}%', end="")
               sys.stdout.flush()
               temp += 1   # updates every 1%

            #------------------------------------------------------------------------------
            v1x = float(vx[i]); v1y = float(vy[i]); v1z = float(vz[i]); d1 = float(dist[i])
            v2x = float(vx[j]); v2y = float(vy[j]); v2z = float(vz[j]); d2 = float(dist[j])
            #------------------------------------------------------------------------------

            #------------------------------------------------------------------------
            vector1 = np.array([v1x, v1y, 0.0]);  vector2 = np.array([v2x, v2y, 0.0])
            #------------------------------------------------------------------------
            Area = np.linalg.norm(np.cross(vector1, vector2))
            if (n_Lattice == 2):  n_ions = Area*(dens_ions[0] + dens_ions[1])
            if (n_Lattice == 3):  n_ions = Area*(dens_ions[0] + dens_ions[1] + dens_ions[2])
            #-------------------------------------------------------------------------------

            if ( n_ions >= (ions_crit_i*fator_n) and n_ions <= (ions_crit_f*fator_p) ):
               try:
                   #-----------------------------------------------------------------------------------------------
                   # Filtering lattices whose triple product is negative ------------------------------------------
                   #-----------------------------------------------------------------------------------------------
                   a = np.array([v1x, v1y, 0.0])
                   b = np.array([v2x, v2y, 0.0])
                   c = np.array([0.0, 0.0, 15.0])
                   produto_vetorial = np.cross(a, b)              # Calculation of the vector product between vectors a and b
                   produto_triplo = np.dot(c, produto_vetorial)   # Calculation of the scalar product of vector c with the result of the vector product (a x b)

                   if (produto_triplo > 0):
                      #-----------------------------------------------------------------------
                      u = vector1/np.linalg.norm(vector1);  v = vector2/np.linalg.norm(vector2)
                      dot_product = np.dot(u, v)
                      #--------------------------------------------------------------------
                      if (dot_product < -1.0 and dot_product > -1.001):  dot_product = -1.0
                      if (dot_product > +1.0 and dot_product < +1.001):  dot_product = +1.0
                      #--------------------------------------------------------------------
                      angle = np.arccos(dot_product) / np.pi * 180
                      angle = round(angle, 4)                 
                      #----------------------------------------------
                      if (angle >= angle_min and angle <= angle_max):
                         if (angle != 0.0 and angle != 180.0):
                            #---------------------------------
                            for t in range(len(vector_areas)):
                                area_min = vector_areas[t]*fator_n;  area_min = round(area_min, 3)
                                area_max = vector_areas[t]*fator_p;  area_max = round(area_max, 3)
                                #-----------------------------------------------------------------
                                if (Area >= area_min and Area <= area_max):
                                   cell_Lattice = open(diret + dir_cells_Lattice + '/Cells_Lattice_' + str(area_min) + '_' + str(area_max) + '.dat', "a")
                                   #-------------------------------------------------------------------------------------------------------------------------------
                                   cell_Lattice.write(f'{v1x:>28,.21f} {v1y:>28,.21f} {d1:>28,.21f} {v2x:>28,.21f} {v2y:>28,.21f} {d2:>28,.21f} {angle:>28,.21f} ')
                                   #-------------------------------------------------------------------------------------------------------------------------------
                                   # Obtaining the Transformation Matrices that lead to the original unit cell with all possible cells of the {k+1}º Material
                                   #--------------------------------------------------------------------------------------------------------------------------
                                   Lattice_A = [ [A1x0[k], A1y0[k]], [A2x0[k], A2y0[k]] ]
                                   Lattice_B = [ [v1x, v1y], [v2x, v2y] ]
                                   #-------------------------------------
                                   Lattice_A_inv = np.linalg.inv(Lattice_A)
                                   MTransf = np.dot(Lattice_B, Lattice_A_inv)
                                   #-----------------------------------------
                                   for aa in range(2):
                                       for bb in range(2):
                                           MTransf[aa][bb] = round(MTransf[aa][bb], 4)
                                   #------------------------------------------------------
                                   New_MTransf = [[0 for _ in range(2)] for _ in range(2)]
                                   for aa in range(2):
                                       for bb in range(2):
                                           if ( (MTransf[aa][bb] -int(MTransf[aa][bb])) == 0.0): New_MTransf[aa][bb] = int(MTransf[aa][bb])
                                           if ( (MTransf[aa][bb] -int(MTransf[aa][bb])) != 0.0): New_MTransf[aa][bb] = MTransf[aa][bb]
                                   #--------------------------------------------------------------------------------------------------
                                   cell_Lattice.write(f'{New_MTransf[0][0]} {New_MTransf[0][1]} {New_MTransf[1][0]} {New_MTransf[1][1]} \n')
                                   cell_Lattice.close()  
               except Exception as e:
                   0 == 0
    #-----------------------------------------
    print(f"\rProgress completed !{' ' * 60}")
    #-----------------------------------------


    files = os.listdir(diret + dir_cells_Lattice)
    #--------------------------------------------
    if (len(files) == 0):
       print(f' ')
       print(f'=====================')
       print(f'No cells were found !')
       print(f'=====================')
       print(f' ')
       #========================================
       shutil.rmtree(dir_files + '/' + 'output')
       sys.exit()   
       #=========


#=========================================================
# Getting the Heterostructure ID =========================
#=========================================================
teste_samba = 1
#--------------

for k in range(n_Lattice):
    #--------------------------------------
    Lattice = dir_files + '/' + vLattice[k]
    #--------------------------------------
    poscar = open(Lattice, "r")
    VTemp = poscar.readline().split()
    poscar.close()
    #----------------------------------------
    if (VTemp[0] != 'SAMBA'): teste_samba = 0
    #----------------------------------------

if (teste_samba == 0): unique_id = str(uuid.uuid4().hex[:16])
if (teste_samba == 1):
    combined_ids = ''.join(sorted(id_materials))                     # Concatenating the IDs (ensuring a fixed order)  
    sha256_hash = hashlib.sha256(combined_ids.encode()).hexdigest()  # Calculating the SHA-256 hash  
    unique_id = sha256_hash[:16]                                     # Returning the first 16 characters of the hash as the new ID


#============================================================
# Obtaining the Chemical Formula from the Heterostructure ===
#============================================================
formula_bilayer = ''
for i in range(len(formula)):
    formula_bilayer += formula[i]
    if (i < (len(formula) -1)): formula_bilayer += '+'


#============================================================
# Analyzing all possible lattice matches ====================
#============================================================
for k in range(n_Lattice):
   files = os.listdir(diret + 'cells_Lattice' + str(k+1))
   for s in range(len(files)):
       if ( os.path.getsize(diret + 'cells_Lattice' + str(k+1) + '/' + files[s]) == 0 ):
          os.remove(diret + 'cells_Lattice' + str(k+1) + '/' + files[s])
#=======================================================================
n_test = 1
#-------------------
if (n_Lattice >= 2):
   n_lattice1 = os.listdir(diret + 'cells_Lattice1')
   n_lattice2 = os.listdir(diret + 'cells_Lattice2')
   if (len(n_lattice1) == 0 or len(n_lattice2) == 0): n_test = 0
#-------------------
if (n_Lattice == 3):
   n_lattice3 = os.listdir(diret + 'cells_Lattice3') 
   if (len(n_lattice3) == 0): n_test = 0
#----------------
if (n_test == 0):
   print(f' ')
   print(f'=====================')
   print(f'No cells were found !')
   print(f'=====================')
   print(f' ')
   #========================================
   shutil.rmtree(dir_files + '/' + 'output')
   sys.exit()   
   #==========


#--------------------------------------------------------------------
# Checking for the existence of the 'Matching_Lattices' directory ---
#--------------------------------------------------------------------
if os.path.isdir(diret + 'Matching_Lattices'):
   0 == 0
else:
   os.mkdir(diret + 'Matching_Lattices')
#---------------------------------------

n += 1
#----------
print(f' ')
print(f'==========================================================')
print(f'Step {n}: Analyzing lattices matches (1st and 2nd materials)')
print(f'==========================================================')

files = os.listdir(diret + 'cells_Lattice1')
#=============================================
temp = 1.0; number = -1; n_passos = len(files)
#-----------------------
for s in range(len(files)):
    #----------------------
    number += 1; cont = 0
    porc = (number/(s+1))*100        
    #-------------------------
    if porc >= temp:
       bar_length = 50
       filled_length = int(bar_length * porc // 100)
       bar = '#' * filled_length + '-' * (bar_length - filled_length)
       print(f'\rProgress: |{bar}| {porc:.1f}%', end="")
       sys.stdout.flush()
       temp += 1

    if (n_Lattice == 2):  
       if os.path.isfile(diret + 'cells_Lattice1' + '/' + files[s]):
          if os.path.isfile(diret + 'cells_Lattice2' + '/' + files[s]):
             cont = 1
             #-------
    if (n_Lattice == 3):
       if os.path.isfile(diret + 'cells_Lattice1' + '/' + files[s]):
          if os.path.isfile(diret + 'cells_Lattice2' + '/' + files[s]):
             if os.path.isfile(diret + 'cells_Lattice3' + '/' + files[s]):
                cont = 1
                #-------

    if (cont == 1):
       #---------------------------------------------------------------------------------
       SLattice1 = np.loadtxt(diret + 'cells_Lattice1' + '/' + files[s]); SLattice1.shape
       SLattice2 = np.loadtxt(diret + 'cells_Lattice2' + '/' + files[s]); SLattice2.shape
       #---------------------------------------------------------------------------------
       temp_area = files[s].replace('.dat', '').replace('_', ' ').split()
       area_min = temp_area[2];  area_max = temp_area[3]
       #-------------------------------------------------------------------------------------------------------------------------------------
       if (n_Lattice == 2):  Structures = open(diret + 'Matching_Lattices' + '/Matching_Lattices_' + area_min + '_' + area_max + '.dat', "w")
       if (n_Lattice == 3):  Structures = open(diret + 'Matching_Lattices' + '/Matching_Lattices_' + area_min + '_' + area_max + '_12.dat', "w")
       #--------------------------------------------------------------------------------------------------------------------------------------------------------
       A1x = SLattice1[:,0]; A1y = SLattice1[:,1]; dA1 = SLattice1[:,2]; B1x = SLattice1[:,3]; B1y = SLattice1[:,4]; dB1 = SLattice1[:,5]; ang1 = SLattice1[:,6]
       A2x = SLattice2[:,0]; A2y = SLattice2[:,1]; dA2 = SLattice2[:,2]; B2x = SLattice2[:,3]; B2y = SLattice2[:,4]; dB2 = SLattice2[:,5]; ang2 = SLattice2[:,6]
       #--------------------------------------------------------------------------------------------------------------------------------------------------------
       MT1_00 = SLattice1[:,7];  MT1_01 = SLattice1[:,8];  MT1_10 = SLattice1[:,9];  MT1_11 = SLattice1[:,10]
       MT2_00 = SLattice2[:,7];  MT2_01 = SLattice2[:,8];  MT2_10 = SLattice2[:,9];  MT2_11 = SLattice2[:,10]
       #-----------------------------------------------------------------------------------------------------

       #-------------------------
       for i in range(len(A1x)):
           for j in range(len(A2x)):
               #--------------------------------------------------------------
               # Criterion: Variation in the opening angle of the lattices ---
               #--------------------------------------------------------------
               var_angle_1 = ((ang2[j] -ang1[i])/ang1[i])*100;  var_angle_1 = round(var_angle_1, 4)
               var_angle_2 = ((ang1[i] -ang2[j])/ang2[j])*100;  var_angle_2 = round(var_angle_2, 4)
               ang_diff    = (ang1[i] -ang2[j])
               #---------------------------------------------------------------------------------------------------------------------
               if (abs(var_angle_1) <= crit_angle_perc and abs(var_angle_2) <= crit_angle_diff and abs(ang_diff) <= crit_angle_diff):

                  #--------------------------------------------
                  # Criterion: area mismatch ------------------
                  #--------------------------------------------
                  A1 = np.array([A1x[i], A1y[i], 0.0]);  B1 = np.array([B1x[i], B1y[i], 0.0]);  area_cell1 = np.linalg.norm(np.cross(A1, B1))
                  A2 = np.array([A2x[j], A2y[j], 0.0]);  B2 = np.array([B2x[j], B2y[j], 0.0]);  area_cell2 = np.linalg.norm(np.cross(A2, B2))
                  var_area_cell1 = ((area_cell2 -area_cell1)/area_cell1)*100;  var_area_cell1 = round(var_area_cell1, 4)
                  var_area_cell2 = ((area_cell1 -area_cell2)/area_cell2)*100;  var_area_cell2 = round(var_area_cell2, 4)
                  #-------------------------------------------------------------------------------
                  # Obtaining the rotation angle between cells -----------------------------------
                  #-------------------------------------------------------------------------------
                  if (rot_angle_calc == 'center_cell'):
                     V1 = 0.5*A1 + 0.5*B1
                     V2 = 0.5*A2 + 0.5*B2
                  if (rot_angle_calc == 'A1'):
                     V1 = 0.5*A1
                     V2 = 0.5*A2
                  if (rot_angle_calc == 'A2'):
                     V1 = 0.5*B1
                     V2 = 0.5*B2
                  #-------------------------------------------------------------------------------
                  angle_V12 = np.arctan2(np.cross(V2, V1)[2], np.dot(V2, V1))   # angle in radians
                  angle0 = np.degrees(angle_V12)
                  if (abs(angle0) == 0.0):  angle0 = 0.0
                  #-------------------------------------
                  angle1 = angle0
                  #-----------------------------------------------------------------------------
                  # Reducing angle1 to the smallest equivalent positive rotation by symmetry ---
                  #-----------------------------------------------------------------------------
                  if rot_z_2 != 0.0:
                     theta_mod = angle1 % rot_z_2
                     angle1 = min(theta_mod, rot_z_2 - theta_mod)
                  #----------------------------------------------
                  angle1 = round(angle1, 4)
                  #------------------------
                  if (abs(var_area_cell1) <= crit_area and abs(var_area_cell2) <= crit_area):
                     #--------------------------------------------------------------------------
                     # Calculation of the mismatch of the modulus of vectors A and B -----------
                     #--------------------------------------------------------------------------
                     var_A1 = ((dA2[j] -dA1[i])/dA1[i])*100;  var_A1 = round(var_A1, 4)
                     var_B1 = ((dB2[j] -dB1[i])/dB1[i])*100;  var_B1 = round(var_B1, 4)
                     #-----------------------------------------------------------------
                     if (abs(var_A1) <= crit_mod_vector and abs(var_B1) <= crit_mod_vector):
                        var_A2 = ((dA1[i] -dA2[j])/dA2[j])*100;  var_A2 = round(var_A2, 4)
                        var_B2 = ((dB1[i] -dB2[j])/dB2[j])*100;  var_B2 = round(var_B2, 4)
                        #-----------------------------------------------------------------
                        if (abs(var_A2) <= crit_mod_vector and abs(var_B2) <= crit_mod_vector):
                           if (n_Lattice == 2):
                              #========================================================================================
                              Structures.write(f'{A1x[i]:>14,.9f} {A1y[i]:>14,.9f} {B1x[i]:>14,.9f} {B1y[i]:>14,.9f} ')
                              Structures.write(f'{A2x[j]:>14,.9f} {A2y[j]:>14,.9f} {B2x[j]:>14,.9f} {B2y[j]:>14,.9f} ')
                              Structures.write(f'0.0 0.0 0.0 0.0 ')                                               
                              Structures.write(f'{MT1_00[i]} {MT1_01[i]} {MT1_10[i]} {MT1_11[i]} ')
                              Structures.write(f'{MT2_00[j]} {MT2_01[j]} {MT2_10[j]} {MT2_11[j]} ')
                              Structures.write(f'0.0 0.0 0.0 0.0 {angle1} {0.0} \n')
                              #=====================================================
                           if (n_Lattice == 3):
                              #====================================================================================================================
                              Structures.write(f'{A1x[i]:>14,.9f} {A1y[i]:>14,.9f} {dA1[i]} {B1x[i]:>14,.9f} {B1y[i]:>14,.9f} {dB1[i]} {ang1[i]} ')
                              Structures.write(f'{A2x[j]:>14,.9f} {A2y[j]:>14,.9f} {dA2[j]} {B2x[j]:>14,.9f} {B2y[j]:>14,.9f} {dB2[j]} {ang2[j]} ')
                              Structures.write(f'{MT1_00[i]} {MT1_01[i]} {MT1_10[i]} {MT1_11[i]} ')
                              Structures.write(f'{MT2_00[j]} {MT2_01[j]} {MT2_10[j]} {MT2_11[j]} {angle1} \n')
                              #===============================================================================
       #-----------------
       Structures.close()
#-----------------------------------------
print(f"\rProgress completed !{' ' * 60}")
#-----------------------------------------


if (n_Lattice == 3):
   n += 1
   #----------
   print(f' ')
   print(f'==========================================================')
   print(f'Step {n}: Analyzing lattices matches (1st and 3rd materials)')
   print(f'==========================================================')

   #==============================================
   files = os.listdir(diret + 'Matching_Lattices')
   #==============================================
   for s in range(len(files)):
       if ( os.path.getsize(diret + 'Matching_Lattices' + '/' + files[s]) == 0 ):
          os.remove(diret + 'Matching_Lattices' + '/' + files[s])

   #==============================================
   temp = 1.0; number = -1; n_passos = len(files)
   #-----------------------
   for s in range(len(files)):
       #----------------------
       number += 1; cont = 0
       porc = (number/(s+1))*100        
       #-------------------------
       if porc >= temp:
          bar_length = 50
          filled_length = int(bar_length * porc // 100)
          bar = '#' * filled_length + '-' * (bar_length - filled_length)
          print(f'\rProgress: |{bar}| {porc:.1f}%', end="")
          sys.stdout.flush()
          temp += 1

       #-----------------------------------------------------------------------------------------------
       files_lattice3 = files[s].replace("Matching_Lattices","Cells_Lattice").replace("_12.dat",".dat")
       #-----------------------------------------------------------------------------------------------
       if os.path.isfile(diret + 'Matching_Lattices' + '/' + files[s]):
          if os.path.isfile(diret + 'cells_Lattice3' + '/' + files_lattice3):
             cont = 1
             #-------

       if (cont == 1):
          #-----------------------------------------------------------------
          temp_area = files[s].replace('.dat', '').replace('_', ' ').split()
          area_min = temp_area[2];  area_max = temp_area[3]
          #------------------------------------------------------------------------------------
          SLattice1 = np.loadtxt(diret + 'Matching_Lattices' + '/' + files[s]); SLattice1.shape
          SLattice3 = np.loadtxt(diret + 'cells_Lattice3' + '/' + files_lattice3); SLattice3.shape
          #---------------------------------------------------------------------------------------------------------------
          Structures = open(diret + 'Matching_Lattices' + '/Matching_Lattices_' + area_min + '_' + area_max + '.dat', "w")
          #---------------------------------------------------------------------------------------------------------------

          #-----------------------------------------------------------------------------------------------------------------------------------------------------------
          A1x = SLattice1[:,0]; A1y = SLattice1[:,1]; dA1 = SLattice1[:,2]; B1x = SLattice1[:,3];  B1y = SLattice1[:,4];  dB1 = SLattice1[:,5];  ang1 = SLattice1[:,6]
          A2x = SLattice1[:,7]; A2y = SLattice1[:,8]; dA2 = SLattice1[:,9]; B2x = SLattice1[:,10]; B2y = SLattice1[:,11]; dB2 = SLattice1[:,12]; ang2 = SLattice1[:,13]
          A3x = SLattice3[:,0]; A3y = SLattice3[:,1]; dA3 = SLattice3[:,2]; B3x = SLattice3[:,3];  B3y = SLattice3[:,4];  dB3 = SLattice3[:,5];  ang3 = SLattice3[:,6]
          #-----------------------------------------------------------------------------------------------------------------------------------------------------------
          MT1_00 = SLattice1[:,14];  MT1_01 = SLattice1[:,15];  MT1_10 = SLattice1[:,16];  MT1_11 = SLattice1[:,17]
          MT2_00 = SLattice1[:,18];  MT2_01 = SLattice1[:,19];  MT2_10 = SLattice1[:,20];  MT2_11 = SLattice1[:,21]
          MT3_00 = SLattice3[:,7];   MT3_01 = SLattice3[:,8];   MT3_10 = SLattice3[:,9];   MT3_11 = SLattice3[:,10]
          #--------------------------------------------------------------------------------------------------------
          Angle_r_12 = SLattice1[:,22]
          #---------------------------

          #-------------------------
          for i in range(len(A1x)):
              for j in range(len(A3x)):
                  #---------------------------------------------------------
                  # Criterion: Variation of the Lattice opening angle ------
                  #---------------------------------------------------------
                  var_angle_1 = ((ang3[j] -ang1[i])/ang1[i])*100;  var_angle_1 = round(var_angle_1, 4)
                  var_angle_3 = ((ang1[i] -ang3[j])/ang3[j])*100;  var_angle_3 = round(var_angle_3, 4)
                  ang_diff    = (ang1[i] -ang3[j])
                  #---------------------------------------------------------------------------------------------------------------------
                  if (abs(var_angle_1) <= crit_angle_perc and abs(var_angle_3) <= crit_angle_diff and abs(ang_diff) <= crit_angle_diff):
                     #--------------------------------------------
                     # Criterion: area mismatch ------------------
                     #--------------------------------------------
                     A1 = np.array([A1x[i], A1y[i], 0.0]);  B1 = np.array([B1x[i], B1y[i], 0.0]);  area_cell1 = np.linalg.norm(np.cross(A1, B1))
                     A3 = np.array([A3x[j], A3y[j], 0.0]);  B3 = np.array([B3x[j], B3y[j], 0.0]);  area_cell3 = np.linalg.norm(np.cross(A3, B3))
                     var_area_cell1 = ((area_cell3 -area_cell1)/area_cell1)*100;  var_area_cell1 = round(var_area_cell1, 4)
                     var_area_cell3 = ((area_cell1 -area_cell3)/area_cell3)*100;  var_area_cell3 = round(var_area_cell3, 4)
                     #-------------------------------------------------------------------------------
                     # Obtaining the rotation angle between cells -----------------------------------
                     #-------------------------------------------------------------------------------
                     if (rot_angle_calc == 'center_cell'):
                        V1 = 0.5*A1 + 0.5*B1
                        V3 = 0.5*A3 + 0.5*B3
                     if (rot_angle_calc == 'A1'):
                        V1 = 0.5*A1
                        V3 = 0.5*A3
                     if (rot_angle_calc == 'A2'):
                        V1 = 0.5*B1
                        V3 = 0.5*B3
                     angle_V13 = np.arctan2(np.cross(V3, V1)[2], np.dot(V3, V1))   # angle in radians
                     angle2 = np.degrees(angle_V13)
                     if (abs(angle2) == 0.0):  angle2 = 0.0
                     #-----------------------------------------------------------------
                     angle3 = angle2
                     #------------------------------------------------------------------------------
                     # Reducing angle 3 to the smallest equivalent positive rotation by symmetry ---
                     #------------------------------------------------------------------------------
                     if rot_z_3 != 0.0:
                        theta_mod = angle3 % rot_z_3
                        angle3 = min(theta_mod, rot_z_3 - theta_mod)
                     #----------------------------------------------
                     angle3 = round(angle3, 4)
                     #-------------------------------------------------------------------------- 
                     if (abs(var_area_cell1) <= crit_area and abs(var_area_cell3) <= crit_area):
                        #-----------------------------------------------------------------------
                        # Calculation of the mismatch of the modulus of vectors A and B --------
                        #-----------------------------------------------------------------------
                        var_A1 = ((dA3[j] -dA1[i])/dA1[i])*100;  var_A1 = round(var_A1, 4)
                        var_B1 = ((dB3[j] -dB1[i])/dB1[i])*100;  var_B1 = round(var_B1, 4)
                        #-----------------------------------------------------------------
                        if (abs(var_A1) <= crit_mod_vector and abs(var_B1) <= crit_mod_vector):
                           var_A3 = ((dA1[i] -dA3[j])/dA3[j])*100;  var_A3 = round(var_A3, 4)
                           var_B3 = ((dB1[i] -dB3[j])/dB3[j])*100;  var_B3 = round(var_B3, 4)
                           #-----------------------------------------------------------------
                           if (abs(var_A3) <= crit_mod_vector and abs(var_B3) <= crit_mod_vector):
                              #============================================================================================
                              Structures.write(f'{A1x[i]:>14,.9f} {A1y[i]:>14,.9f} {B1x[i]:>14,.9f} {B1y[i]:>14,.9f} ')
                              Structures.write(f'{A2x[i]:>14,.9f} {A2y[i]:>14,.9f} {B2x[i]:>14,.9f} {B2y[i]:>14,.9f} ')
                              Structures.write(f'{A3x[j]:>14,.9f} {A3y[j]:>14,.9f} {B3x[j]:>14,.9f} {B3y[j]:>14,.9f} ')
                              Structures.write(f'{MT1_00[i]} {MT1_01[i]} {MT1_10[i]} {MT1_11[i]} ')
                              Structures.write(f'{MT2_00[i]} {MT2_01[i]} {MT2_10[i]} {MT2_11[i]} ')
                              Structures.write(f'{MT3_00[j]} {MT3_01[j]} {MT3_10[j]} {MT3_11[j]} ')
                              Structures.write(f'{Angle_r_12[i]} {angle3} \n')
                              #===============================================
          #-----------------
          Structures.close()
       #------------------------------------------------------
       os.remove(diret + 'Matching_Lattices' + '/' + files[s])
   #----------------------------------------------------------
   print(f"\rProgress completed !{' ' * 60}")
   #-----------------------------------------


#==============================================
files = os.listdir(diret + 'Matching_Lattices')
#==============================================
for s in range(len(files)):
    if ( os.path.getsize(diret + 'Matching_Lattices' + '/' + files[s]) == 0 ):
       os.remove(diret + 'Matching_Lattices' + '/' + files[s])
#-------------------------------------------------------------
n_test = 1
#---------
dir_matchings = os.listdir(diret + 'Matching_Lattices')
if (len(dir_matchings) == 0): n_test = 0
#---------------------------------------
if (n_test == 0):
   print(f' ')
   print(f'=====================')
   print(f'No cells were found !')
   print(f'=====================')
   print(f' ')
   #========================================
   shutil.rmtree(dir_files + '/' + 'output')
   sys.exit()    
   #=========


#----------------------------------------------
files = os.listdir(diret + 'Matching_Lattices')
num_lines = 0
#--------------------------
for s in range(len(files)):
    #------------------------------------------------------
    filename = diret + 'Matching_Lattices' + '/' + files[s]
    #---
    try:
        with open(filename, 'r') as file_data:
            for line in file_data: num_lines += 1
    except FileNotFoundError: print(f"Error: The file '{filename}' was not found.")
    except Exception as e: print(f"error detected: {e}")
    #---------------------------------------------------

#=========================================
print(f'--------------------------')
print(f'{num_lines} cells were identified')
#=========================================


n += 1
#----------
print(f' ')
print(f'=================================')
print(f'Step {n}: Deleting Similar Lattices')
print(f'=================================')

#----------------------------------------------
files = os.listdir(diret + 'Matching_Lattices')
num_lines_i = 0
num_lines_f = 0
#--------------------------
for s in range(len(files)):
    #------------------------------------------------------
    filename = diret + 'Matching_Lattices' + '/' + files[s]
    filtered_lines = []
    unique_keys = set()
    #------------------
    try:
        with open(filename, 'r') as file_data:
            for line in file_data:
                #-----------------
                num_lines_i += 1
                line = line.strip()
                if not line: continue
                try: values = [float(term) for term in line.split()]
                except (ValueError, IndexError): continue
                #------------------------------------------------------------------------
                A1x, A1y, B1x, B1y, A2x, A2y, B2x, B2y, A3x, A3y, B3x, B3y = values[:12]
                Angle_r_12, Angle_r_13 = values[-2:]
                #-----------------------------------------------------------------------------------------------------------
                DA1 = math.sqrt(A1x**2 + A1y**2); DB1 = math.sqrt(B1x**2 + B1y**2); DA1 = round(DA1, 6); DB1 = round(DB1, 6)
                DA2 = math.sqrt(A2x**2 + A2y**2); DB2 = math.sqrt(B2x**2 + B2y**2); DA2 = round(DA2, 6); DB2 = round(DB2, 6)
                DA3 = math.sqrt(A3x**2 + A3y**2); DB3 = math.sqrt(B3x**2 + B3y**2); DA3 = round(DA3, 6); DB3 = round(DB3, 6)
                #-----------------------------------------------------------------------------------------------------------
                comparison_key = (DA1, DB1, DA2, DB2, DA3, DB3, Angle_r_12, Angle_r_13)
                #------------------------------------------------------------------------
                if comparison_key not in unique_keys:
                    unique_keys.add(comparison_key)
                    filtered_lines.append(line)
        #--------------------------------------
        with open(filename, 'w') as new_file:
            for filtered_line in filtered_lines:
                new_file.write(filtered_line + '\n')
    #------------------------------------------------------------------------------
    except FileNotFoundError: print(f"Error: The file '{filename}' was not found.")
    except Exception as e: print(f"error detected: {e}")
    #---------------------------------------------------
    try:
        with open(filename, 'r') as file_data:
            for line in file_data: num_lines_f += 1
    except FileNotFoundError: print(f"Error: The file '{filename}' was not found.")
    except Exception as e: print(f"error detected: {e}")
    #---------------------------------------------------

#========================================================
print(f'{num_lines_i -num_lines_f} cells were filtered/excluded')
print(f'{num_lines_f} remaining cells')
#========================================================

n += 1
#----------
print(f' ')
print(f'============================================================')
print(f'Step {n}: Writing the POSCAR files for the {n_Lattice} material lattices')
print(f'============================================================')

if (n_test == 1):
   temp = 1.0; number = -1; n_passos = len(dir_matchings)
   #-----------------------
   for s in range(len(dir_matchings)):
       #----------------------
       number += 1; cont = 0
       porc = (number/(s+1))*100        
       #-------------------------
       if porc >= temp:
          bar_length = 50
          filled_length = int(bar_length * porc // 100)
          bar = '#' * filled_length + '-' * (bar_length - filled_length)
          print(f'\rProgress: |{bar}| {porc:.1f}%', end="")
          sys.stdout.flush()
          temp += 1

       #------------------------------------------------
       dir_temp_m = dir_matchings[s].replace('.dat', '')
       #------------------------------------------------
       structures = np.loadtxt(diret + 'Matching_Lattices' + '/' + dir_matchings[s], dtype='str'); structures.shape
       n_structures = len(structures[:,0])
       #----------------------------------

       #=============================================================================
       # Obtaining the POSCAR files for each of the lattices and cells found ========
       #=============================================================================

       #----------------------------------------------------------
       # New module for the A3 vector of the Heterostructures cell
       #----------------------------------------------------------
       if (n_Lattice == 2):  d = dZ[0] + dZ[1] + separacao1 + vacuum                        
       if (n_Lattice == 3):  d = dZ[0] + dZ[1] + dZ[2] + separacao1 + separacao2 + vacuum

       #-----------------------
       for k in range(n_Lattice):
           match = open(diret + 'Matching_Lattices' + '/' + dir_matchings[s], "r")
           for j in range(n_structures):

               #---------------------------------------------------------
               # Checking for existence of directory 'dir_temp_m' -------
               #---------------------------------------------------------
               temp_dir = diret + 'Lattice' + str(k+1) + '/' + dir_temp_m
               if os.path.isdir(temp_dir): 0 == 0
               else: os.mkdir(temp_dir)
               #-----------------------

               #------------------------------
               if (k == 0): label = 'Lattice1'
               if (k == 1): label = 'Lattice2'
               if (k == 2): label = 'Lattice3'
               p = 4*(3+k)
               #------------------------------- 
               VTemp = match.readline().split()
               #-------------------------------
               try:
                   #---------------------------------------------
                   f1 = float(VTemp[p+0]); f2 = float(VTemp[p+1])
                   f3 = float(VTemp[p+2]); f4 = float(VTemp[p+3])
                   null = 0.0
                   #---------------------------------------------
                   MTransf = np.array([ [f1, f2, 0],
                                        [f3, f4, 0],
                                        [0,  0,  1] ])
                   #------------------------------------------------------------------
                   unit_cell = Structure.from_file(diret + 'temp1_' + label + '.vasp')
                   supercell = unit_cell.make_supercell(MTransf)
                   supercell.to(fmt="poscar", filename = temp_dir + '/POSCAR_' + str(j+1) + '.vasp')
                   #-------------------------------------------------------------------------------- 

                   ...

               except Exception  as e:
                   print(f"error detected: {e}")

           match.close()
   #-----------------------------------------
   print(f"\rProgress completed !{' ' * 60}")
   #-----------------------------------------


n += 1
#----------
print(f' ')
print(f'=================================================') 
print(f'Step {n}: Writing the Heterostructures POSCAR files')
print(f'=================================================')  

if (n_test == 1):
   temp = 1.0; number = -1; n_passos = len(dir_matchings)
   #-----------------------
   for s in range(len(dir_matchings)):
       #----------------------
       number += 1; cont = 0
       porc = (number/(s+1))*100        
       #-------------------------
       if porc >= temp:
          bar_length = 50
          filled_length = int(bar_length * porc // 100)
          bar = '#' * filled_length + '-' * (bar_length - filled_length)
          print(f'\rProgress: |{bar}| {porc:.1f}%', end="")
          sys.stdout.flush()
          temp += 1

       #------------------------------------------------
       dir_temp_m = dir_matchings[s].replace('.dat', '')
       #------------------------------------------------

       #=====================================================================
       # Building the Heterostructures ======================================
       #=====================================================================

       tfile = np.loadtxt(diret + 'Matching_Lattices' + '/' + dir_matchings[s]); tfile.shape
       n_structures = len(tfile[:,0])
       #------------------------------------------
       MT1_00 = tfile[:,12];  MT2_00 = tfile[:,16]
       MT1_01 = tfile[:,13];  MT2_01 = tfile[:,17]
       MT1_10 = tfile[:,14];  MT2_10 = tfile[:,18]
       MT1_10 = tfile[:,15];  MT2_10 = tfile[:,19]

       if (n_Lattice == 3):
          #-------------------
          MT3_00 = tfile[:,20]
          MT3_01 = tfile[:,21]
          MT3_10 = tfile[:,22]
          MT3_10 = tfile[:,23]

       if (n_structures != 0):

          for i in range(n_structures):
              #------------------------------------------------------------------------
              # Checking the existence of the Heterostructures save directory ---------
              #------------------------------------------------------------------------
              if os.path.isdir(dir_files + '/' + dir_o): 0 == 0
              else: os.mkdir(dir_files + '/' + dir_o)
              #--------------------------------------
              if (loop_ht == 0):
                 if os.path.isdir(dir_files + '/' + dir_o + '/' + dir_temp_m): 0 == 0
                 else: os.mkdir(dir_files + '/' + dir_o + '/' + dir_temp_m)
                 diret2 = dir_files + '/' + dir_o + '/'
              #----------------------------------------
              if (loop_ht == 1):
                 if os.path.isdir(dir_files + '/' + dir_o + '/' + dir_loop): 0 == 0
                 else: os.mkdir(dir_files + '/' + dir_o + '/' + dir_loop)
                 #-------------------------------------------------------
                 if os.path.isdir(dir_files + '/' + dir_o + '/' + dir_loop + '/' + dir_temp_m): 0 == 0
                 else: os.mkdir(dir_files + '/' + dir_o + '/' + dir_loop + '/' + dir_temp_m)
                 #--------------------------------------------------------------------------
                 diret2 = dir_files + '/' + dir_o + '/' + dir_loop + '/'


              #------------------------------------------------------------------------
              # Getting the angle of rotation between materials -----------------------
              #------------------------------------------------------------------------
              poscar1 = open(diret + 'Lattice1' + '/' + dir_temp_m + '/' + '/POSCAR_' + str(i+1) + '.vasp', "r")
              poscar2 = open(diret + 'Lattice2' + '/' + dir_temp_m + '/' + '/POSCAR_' + str(i+1) + '.vasp', "r")
              if (n_Lattice == 3):  poscar3 = open(diret + 'Lattice3' + '/' + dir_temp_m + '/' + '/POSCAR_' + str(i+1) + '.vasp', "r")
              #-----------------------------------------------------------------------------------------------------------------------
              VTemp = poscar1.readline()
              VTemp = poscar1.readline(); param = float(VTemp)
              A = poscar1.readline().split(); A1 = np.array([float(A[0])*param, float(A[1])*param, 0.0])
              B = poscar1.readline().split(); B1 = np.array([float(B[0])*param, float(B[1])*param, 0.0])
              #-----------------------------------------------------------------------------------------
              VTemp = poscar2.readline()
              VTemp = poscar2.readline(); param = float(VTemp)
              A = poscar2.readline().split(); A2 = np.array([float(A[0])*param, float(A[1])*param, 0.0])
              B = poscar2.readline().split(); B2 = np.array([float(B[0])*param, float(B[1])*param, 0.0])
              #-----------------------------------------------------------------------------------------
              if (n_Lattice == 3):
                 VTemp = poscar3.readline()
                 VTemp = poscar3.readline(); param = float(VTemp)
                 A = poscar3.readline().split(); A3 = np.array([float(A[0])*param, float(A[1])*param, 0.0])
                 B = poscar3.readline().split(); B3 = np.array([float(B[0])*param, float(B[1])*param, 0.0])
              #--------------------------------------------------------------------------------------------
              if (rot_angle_calc == 'center_cell'):
                 V1 = 0.5*A1 + 0.5*B1; V2 = 0.5*A2 + 0.5*B2
                 if (n_Lattice == 3):  V3 = 0.5*A3 + 0.5*B3
                 #-----------------------------------------
              if (rot_angle_calc == 'A1'):
                 V1 = 0.5*A1; V2 = 0.5*A2
                 if (n_Lattice == 3):  V3 = 0.5*A3
                 #--------------------------------
              if (rot_angle_calc == 'A2'):
                 V1 = 0.5*B1; V2 = 0.5*B2
                 if (n_Lattice == 3):  V3 = 0.5*B3
              #-------------------------------------------------------------------------------
              angle_V12 = np.arctan2(np.cross(V2, V1)[2], np.dot(V2, V1))   # angle in radians
              angle0 = np.degrees(angle_V12)
              if (abs(angle0) == 0.0):  angle0 = 0.0
              #-----------------------------------------------------------------
              # if (angle0 < 10):                    angle1 = '00' + str(angle0)
              # if (angle0 >= 10 and angle0 < 100):  angle1 = '0'  + str(angle0)
              # if (angle0 >= 100):                  angle1 = ''   + str(angle0)
              # if (len(angle1) == 5):               angle1 = angle1 + '00'
              # if (len(angle1) == 6):               angle1 = angle1 + '0'
              #-----------------------------------------------------------------
              angle1 = angle0
              #------------------------------------------------------------------------------
              # Reducing angle 1 to the smallest equivalent positive rotation by symmetry ---
              #------------------------------------------------------------------------------
              if rot_z_2 != 0.0:
                 theta_mod = angle1 % rot_z_2
                 angle1 = min(theta_mod, rot_z_2 - theta_mod)
              #-----------------------------------------------------------------
              angle1 = round(angle1, 4)
              #=================================================================
              if (n_Lattice == 3):
                 angle_V13 = np.arctan2(np.cross(V3, V1)[2], np.dot(V3, V1))   # angle in radians
                 angle2 = np.degrees(angle_V13)
                 if (abs(angle2) == 0.0):  angle2 = 0.0
                 #-----------------------------------------------------------------
                 # if (angle2 < 10):                    angle3 = '00' + str(angle2)
                 # if (angle2 >= 10 and angle2 < 100):  angle3 = '0'  + str(angle2)
                 # if (angle2 >= 100):                  angle3 = ''   + str(angle2)
                 # if (len(angle3) == 5):               angle3 = angle3 + '00'
                 # if (len(angle3) == 6):               angle3 = angle3 + '0'
                 #-----------------------------------------------------------------
                 angle3 = angle2
                 #------------------------------------------------------------------------------
                 # Reducing angle 3 to the smallest equivalent positive rotation by symmetry ---
                 #------------------------------------------------------------------------------
                 if rot_z_3 != 0.0:
                    theta_mod = angle3 % rot_z_3
                    angle3 = min(theta_mod, rot_z_3 - theta_mod)
                 #-----------------------------------------------------------------
                 angle3 = round(angle3, 4)
              #====================================================================
              for j in range(3):
                  VTemp1 = poscar1.readline().split()
                  VTemp2 = poscar2.readline().split()
                  if (n_Lattice == 3): VTemp3 = poscar3.readline().split()
              #-----------------------------------------------------------
              nions_1 = nions_2 = nions_3 = 0
              for m in range(len(VTemp1)): nions_1 += int(VTemp1[m])
              for m in range(len(VTemp2)): nions_2 += int(VTemp2[m])
              if (n_Lattice == 3):
                 for m in range(len(VTemp3)): nions_3 += int(VTemp3[m])
              #--------------
              poscar1.close()
              poscar2.close()
              if (n_Lattice == 3):  poscar3.close()
              #------------------------------------

              # if ( ((n_Lattice == 2) and (angle1 >= 0.0)) or ((n_Lattice == 3) and (angle1 >= 0.0) and (angle3 >= 0.0)) ): 
              if ( (n_Lattice == 2) or (n_Lattice == 3) ): 
                 #------------------------------------------------------------------------
                 # Writing the POSCAR file of Heterostructures ---------------------------
                 #------------------------------------------------------------------------
                 poscar1 = open(diret + 'Lattice1' + '/' + dir_temp_m + '/' + '/POSCAR_' + str(i+1) + '.vasp', "r")
                 poscar2 = open(diret + 'Lattice2' + '/' + dir_temp_m + '/' + '/POSCAR_' + str(i+1) + '.vasp', "r")
                 if (n_Lattice == 3):  poscar3 = open(diret + 'Lattice3' + '/' + dir_temp_m + '/' + '/POSCAR_' + str(i+1) + '.vasp', "r")  
                 poscar_new = open(diret2 + dir_temp_m + '/POSCAR_' + str(i+1) + '.vasp', "w")

                 #-----------------------------------------------------
                 ID_Heteroestrutura = formula_bilayer + '_' + unique_id
                 #-----------------------------------------------------

                 #================================================
                 VTemp1 = poscar1.readline()
                 VTemp2 = poscar2.readline()
                 if (n_Lattice == 3):  VTemp3 = poscar3.readline()
                 #================================================
                 if (mismatch_type >= 0 and mismatch_type <= 3):
                    #--------------------------
                    VTemp1 = poscar1.readline()
                    VTemp2 = poscar2.readline()
                    if (n_Lattice == 3):  VTemp3 = poscar3.readline()
                    #----------------------------
                    for j in range(2):
                        VTemp1 = poscar1.readline()
                        VTemp2 = poscar2.readline()
                        if (n_Lattice == 3): VTemp3 = poscar3.readline()

                    #----------------------------------------------------------------------------------------
                    # Obtaining the module of the vectors (A, B), Area and the Opening Angle of the cells ---
                    #----------------------------------------------------------------------------------------
                    mod_A1 = np.linalg.norm(A1)
                    mod_B1 = np.linalg.norm(B1)
                    mod_A2 = np.linalg.norm(A2)
                    mod_B2 = np.linalg.norm(B2)
                    Area1 = np.linalg.norm(np.cross(A1, B1))
                    Area2 = np.linalg.norm(np.cross(A2, B2))
                    angle_1 = np.arccos(np.dot(A1,B1)/(mod_A1*mod_B1))
                    angle_2 = np.arccos(np.dot(A2,B2)/(mod_A2*mod_B2))
                    if (n_Lattice == 3):
                       mod_A3 = np.linalg.norm(A3)
                       mod_B3 = np.linalg.norm(B3)
                       Area3 = np.linalg.norm(np.cross(A3, B3))
                       angle_3 = np.arccos(np.dot(A3,B3)/(mod_A3*mod_B3))

                    #----------------------------------------------------------------------------------------------------------------
                    # Aligning the cells of the different lattices ------------------------------------------------------------------
                    #----------------------------------------------------------------------------------------------------------------
                    theta = angle_V12;  rotation_matrix = np.array([ [np.cos(theta), -np.sin(theta), 0], [np.sin(theta), np.cos(theta), 0], [0, 0, 1] ])
                    A2_rotated = np.dot(rotation_matrix, A2)
                    B2_rotated = np.dot(rotation_matrix, B2)
                    #---------------------------------------
                    if (n_Lattice == 3):
                       theta = angle_V13;  rotation_matrix = np.array([ [np.cos(theta), -np.sin(theta), 0], [np.sin(theta), np.cos(theta), 0], [0, 0, 1] ])
                       A3_rotated = np.dot(rotation_matrix, A3)
                       B3_rotated = np.dot(rotation_matrix, B3)
                    #-------------------------------------------------------
                    # Defining the intermediate cell -----------------------
                    #-------------------------------------------------------
                    if (mismatch_type == 0):
                       if (n_Lattice == 2):
                          A_int = (A1 + A2_rotated)/2
                          B_int = (B1 + B2_rotated)/2
                       if (n_Lattice == 3):
                          A_int = (A1 + A2_rotated + A3_rotated)/3
                          B_int = (B1 + B2_rotated + B3_rotated)/3
                    #---------------------------------------------
                    if (mismatch_type == 1):
                       A_int = A1
                       B_int = B1
                    #-----------------------
                    if (mismatch_type == 2):
                       A_int = A2_rotated
                       B_int = B2_rotated
                    #-----------------------
                    if (mismatch_type == 3):
                       A_int = A3_rotated
                       B_int = B3_rotated
                    #--------------------------------   
                    mod_A_int = np.linalg.norm(A_int)
                    mod_B_int = np.linalg.norm(B_int)
                    Area_int = np.linalg.norm(np.cross(A_int, B_int))
                    angle_int = np.arctan2(np.cross(A_int,B_int)[2], np.dot(A_int,B_int))

                    #-----------------------------------------------------------------------------------------------------------
                    # Use of temporary vectors (A,B) to estimate the deformation applied to the original cells -----------------
                    #-----------------------------------------------------------------------------------------------------------
                    var_A1 = ((mod_A_int -mod_A1)/mod_A1)*100;  var_A1 = round(var_A1, 4)
                    var_B1 = ((mod_B_int -mod_B1)/mod_B1)*100;  var_B1 = round(var_B1, 4)
                    var_A2 = ((mod_A_int -mod_A2)/mod_A2)*100;  var_A2 = round(var_A2, 4)
                    var_B2 = ((mod_B_int -mod_B2)/mod_B2)*100;  var_B2 = round(var_B2, 4)
                    if (n_Lattice == 3):
                       var_A3 = ((mod_A_int -mod_A3)/mod_A3)*100;  var_A3 = round(var_A3, 4)
                       var_B3 = ((mod_B_int -mod_B3)/mod_B3)*100;  var_B3 = round(var_B3, 4)
                    #--------------------------------------------------------------------------------
                    mm_angle12 = ((angle_2 -angle_1)/angle_1)*100;  mm_angle12 = round(mm_angle12, 4)
                    mm_angle21 = ((angle_1 -angle_2)/angle_2)*100;  mm_angle21 = round(mm_angle21, 4)
                    if (n_Lattice == 3): 
                       mm_angle13 = ((angle_3 -angle_1)/angle_1)*100;  mm_angle13 = round(mm_angle13, 4)
                       mm_angle31 = ((angle_1 -angle_3)/angle_3)*100;  mm_angle31 = round(mm_angle31, 4)
                    #-----------------------------------------------------------------------------------
                    var_angle1 = ((angle_int -angle_1)/angle_1)*100;  var_angle1 = round(var_angle1, 4)
                    var_angle2 = ((angle_int -angle_2)/angle_2)*100;  var_angle2 = round(var_angle2, 4)
                    if (n_Lattice == 3):
                       var_angle3 = ((angle_int -angle_3)/angle_3)*100;  var_angle3 = round(var_angle3, 4)
                    #-------------------------------------------------------------------------------------
                    mm_Area12 = ((Area2 -Area1)/Area1)*100;  mm_Area12 = round(mm_Area12, 4)
                    mm_Area21 = ((Area1 -Area2)/Area2)*100;  mm_Area21 = round(mm_Area21, 4)
                    if (n_Lattice == 3):
                       mm_Area13 = ((Area3 -Area1)/Area1)*100;  mm_Area13 = round(mm_Area13, 4)
                       mm_Area31 = ((Area1 -Area3)/Area3)*100;  mm_Area31 = round(mm_Area31, 4)
                    #--------------------------------------------------------------------------
                    var_Area1 = ((Area_int -Area1)/Area1)*100;  var_Area1 = round(var_Area1, 4)
                    var_Area2 = ((Area_int -Area2)/Area2)*100;  var_Area2 = round(var_Area2, 4)
                    if (n_Lattice == 3):
                       var_Area3 = ((Area_int -Area3)/Area3)*100;  var_Area3 = round(var_Area3, 4)
                    #-----------------------------------------------------------------------------
                    if(var_A1 == -0.0): var_A1 = 0.0
                    if(var_B1 == -0.0): var_B1 = 0.0
                    if(var_A2 == -0.0): var_A2 = 0.0
                    if(var_B2 == -0.0): var_B2 = 0.0
                    if(var_Area1 == -0.0):  var_Area1 = 0.0
                    if(var_Area2 == -0.0):  var_Area2 = 0.0
                    if(mm_Area12 == -0.0):  mm_Area12 = 0.0
                    if(mm_Area21 == -0.0):  mm_Area21 = 0.0
                    if(var_angle1 == -0.0): var_angle1 = 0.0
                    if(var_angle2 == -0.0): var_angle2 = 0.0
                    if(mm_angle12 == -0.0): mm_angle12 = 0.0
                    if(mm_angle21 == -0.0): mm_angle21 = 0.0
                    if (n_Lattice == 3):
                       if(var_A3 == -0.0): var_A3 = 0.0
                       if(var_B3 == -0.0): var_B3 = 0.0
                       if(var_Area3 == -0.0):  var_Area3 = 0.0
                       if(mm_Area13 == -0.0):  mm_Area13 = 0.0
                       if(mm_Area31 == -0.0):  mm_Area31 = 0.0
                       if(var_angle3 == -0.0): var_angle3 = 0.0
                       if(mm_angle13 == -0.0): mm_angle13 = 0.0
                       if(mm_angle31 == -0.0): mm_angle31 = 0.0
                    #------------------------------------------

                    #===============================================
                    # Obtaining Strain Matrices for each lattice ===
                    #===============================================
                    Lattice_A = [ [A1[0], A1[1]], [B1[0], B1[1]] ]
                    Lattice_B = [ [A2_rotated[0], A2_rotated[1]], [B2_rotated[0], B2_rotated[1]] ]
                    if (n_Lattice == 3):
                       Lattice_C = [ [A3_rotated[0], A3_rotated[1]], [B3_rotated[0], B3_rotated[1]] ]
                    Lattice_D = [ [A_int[0], A_int[1]], [B_int[0], B_int[1]] ]
                    #---------------------------------------------------------
                    I = np.eye(2)
                    Lattice_A_inv = np.linalg.inv(Lattice_A)
                    F_A = np.dot(Lattice_D, Lattice_A_inv)
                    MStrain_A = 0.5 * (np.dot(F_A.T, F_A) - I)
                    for aa in range(2):
                        for bb in range(2):
                            #----------------------------------
                            F_A[aa][bb] = round(F_A[aa][bb], 9)
                            MStrain_A[aa][bb] = round(MStrain_A[aa][bb], 9)
                            #----------------------------------------------
                            if (F_A[aa][bb] == -0.0): F_A[aa][bb] = 0.0
                            if (MStrain_A[aa][bb] == -0.0): MStrain_A[aa][bb] = 0.0
                    #--------------------------------------------------------------
                    Lattice_B_inv = np.linalg.inv(Lattice_B)
                    F_B = np.dot(Lattice_D, Lattice_B_inv)
                    MStrain_B = 0.5 * (np.dot(F_B.T, F_B) - I)
                    for aa in range(2):
                        for bb in range(2):
                            #----------------------------------
                            F_B[aa][bb] = round(F_B[aa][bb], 9)
                            MStrain_B[aa][bb] = round(MStrain_B[aa][bb], 9)
                            #----------------------------------------------
                            if (F_B[aa][bb] == -0.0): F_B[aa][bb] = 0.0
                            if (MStrain_B[aa][bb] == -0.0): MStrain_B[aa][bb] = 0.0
                    #--------------------------------------------------------------
                    if (n_Lattice == 3): 
                       Lattice_C_inv = np.linalg.inv(Lattice_C)
                       F_C = np.dot(Lattice_D, Lattice_C_inv)
                       MStrain_C = 0.5 * (np.dot(F_C.T, F_C) - I)
                       for aa in range(2):
                           for bb in range(2):
                               #----------------------------------
                               F_C[aa][bb] = round(F_C[aa][bb], 9)
                               MStrain_C[aa][bb] = round(MStrain_C[aa][bb], 9)
                               #----------------------------------------------
                               if (F_C[aa][bb] == -0.0): F_C[aa][bb] = 0.0
                               if (MStrain_C[aa][bb] == -0.0): MStrain_C[aa][bb] = 0.0


                    poscar_new.write(f'SAMBA {label_htstructure} {nions_1} {nions_2}')
                    if (n_Lattice == 3): poscar_new.write(f' {nions_3}')
                    #---------------------------------------------------
                    if (n_Lattice == 2):
                       poscar_new.write(f' | mismatch_areas_12_21 = {mm_Area12}_{mm_Area21}')
                       poscar_new.write(f' | var_areas = {var_Area1}_{var_Area2}')
                       poscar_new.write(f' | var_vectors = {var_A1}_{var_B1}_{var_A2}_{var_B2}')
                       poscar_new.write(f' | mismatch_angles_12_21 = {mm_angle12}_{mm_angle21}')
                       poscar_new.write(f' | var_angles = {var_angle1}_{var_angle2}')
                       poscar_new.write(f' | rotation_angle = {angle1}')
                    if (n_Lattice == 3):
                       poscar_new.write(f' | mismatch_Areas_12_21_13_31 = {mm_Area12}_{mm_Area21}_{mm_Area13}_{mm_Area31}')
                       poscar_new.write(f' | var_Areas = {var_Area1}_{var_Area2}_{var_Area3}')
                       poscar_new.write(f' | var_vectors = {var_A1}_{var_B1}_{var_A2}_{var_B2}_{var_A3}_{var_B3}')
                       poscar_new.write(f' | mismatch_angles_12_21_13_31 = {mm_angle12}_{mm_angle21}_{mm_angle13}_{mm_angle31}')
                       poscar_new.write(f' | var_angles = {var_angle1}_{var_angle2}_{var_angle3}')
                       poscar_new.write(f' | rotation_angle = {angle1}_{angle3}')
                    #------------------------------------------------------------
                    poscar_new.write(f' | MSCell_1 = {int(MT1_00[i])}_{int(MT1_01[i])}_{int(MT1_10[i])}_{int(MT1_10[i])}')
                    poscar_new.write(f' | MSCell_2 = {int(MT2_00[i])}_{int(MT2_01[i])}_{int(MT2_10[i])}_{int(MT2_10[i])}')
                    if (n_Lattice == 3):
                       poscar_new.write(f' | MSCell_3 = {int(MT3_00[i])}_{int(MT3_01[i])}_{int(MT3_10[i])}_{int(MT3_10[i])}')
                    #----------------------------------------------
                    poscar_new.write(f' | MDeform_1 = {float(F_A[0][0])}_{float(F_A[0][1])}_{float(F_A[1][0])}_{float(F_A[1][1])}')
                    poscar_new.write(f' | MDeform_2 = {float(F_B[0][0])}_{float(F_B[0][1])}_{float(F_B[1][0])}_{float(F_B[1][1])}')
                    if (n_Lattice == 3):
                       poscar_new.write(f' | MDeform_3 = {float(F_C[0][0])}_{float(F_C[0][1])}_{float(F_C[1][0])}_{float(F_C[1][1])}')
                    #----------------------------------------------
                    poscar_new.write(f' | MSTrain_1 = {float(MStrain_A[0][0])}_{float(MStrain_A[0][1])}_{float(MStrain_A[1][0])}_{float(MStrain_A[1][1])}')
                    poscar_new.write(f' | MSTrain_2 = {float(MStrain_B[0][0])}_{float(MStrain_B[0][1])}_{float(MStrain_B[1][0])}_{float(MStrain_B[1][1])}')
                    if (n_Lattice == 3):
                       poscar_new.write(f' | MSTrain_3 = {float(MStrain_C[0][0])}_{float(MStrain_C[0][1])}_{float(MStrain_C[1][0])}_{float(MStrain_C[1][1])}')
                    #--------------------------------------------
                    if (n_Lattice == 2):
                       poscar_new.write(f' | Shift_plane = 0.0_0.0')
                    if (n_Lattice == 3):
                       poscar_new.write(f' | Shift_plane = 0.0_0.0_0.0_0.0')
                    #----------------------------------------------
                    poscar_new.write(f' | {ID_Heteroestrutura} \n')
                    #----------------------------------------------
                    poscar_new.write(f'1.0 \n')
                    poscar_new.write(f'{A_int[0]} {A_int[1]} 0.0 \n')
                    poscar_new.write(f'{B_int[0]} {B_int[1]} 0.0 \n')

                    VTemp1 = poscar1.readline().split()
                    VTemp2 = poscar2.readline()
                    if (n_Lattice == 3): VTemp3 = poscar3.readline()
                    poscar_new.write(f'{VTemp1[0]} {VTemp1[1]} {VTemp1[2]} \n')

                 #=================================================================
                 VTemp1 = poscar1.readline().split()
                 VTemp2 = poscar2.readline().split()
                 if (n_Lattice == 3):  VTemp3 = poscar3.readline().split()
                 for j in range(len(VTemp1)): poscar_new.write(f'{str(VTemp1[j])} ')
                 for j in range(len(VTemp2)): poscar_new.write(f'{str(VTemp2[j])} ')
                 if (n_Lattice == 3):
                    for j in range(len(VTemp3)): poscar_new.write(f'{str(VTemp3[j])} ')
                 poscar_new.write(f' \n')
                 #--------------------------------------------------------------------- 
                 VTemp1 = poscar1.readline().split()
                 VTemp2 = poscar2.readline().split()
                 if (n_Lattice == 3):  VTemp3 = poscar3.readline().split()
                 for j in range(len(VTemp1)): poscar_new.write(f'{str(VTemp1[j])} ')
                 for j in range(len(VTemp2)): poscar_new.write(f'{str(VTemp2[j])} ')
                 if (n_Lattice == 3):
                    for j in range(len(VTemp3)): poscar_new.write(f'{str(VTemp3[j])} ')
                 poscar_new.write(f' \n')
                 #--------------------------------------------------------------------- 
                 VTemp1 = poscar1.readline()
                 VTemp2 = poscar2.readline()
                 if (n_Lattice == 3):  VTemp3 = poscar3.readline()
                 poscar_new.write(f'direct \n')
                 #-----------------------------
                 for j in range(nions_1):
                     VTemp1 = poscar1.readline().split()
                     Z1 = ((vacuum/2)/d)
                     poscar_new.write(f'{float(VTemp1[0])} {float(VTemp1[1])} {Z1 + float(VTemp1[2])} \n')
                 for j in range(nions_2):
                     VTemp2 = poscar2.readline().split()
                     Z2 = Z1 + ((dZ[0] + separacao1)/d)
                     poscar_new.write(f'{float(VTemp2[0])} {float(VTemp2[1])} {Z2 + float(VTemp2[2])} \n')
                 if (n_Lattice == 3):  
                    for j in range(nions_3):
                        VTemp3 = poscar3.readline().split()
                        Z3 = Z2 + ((dZ[1] + separacao2)/d)
                        poscar_new.write(f'{float(VTemp3[0])} {float(VTemp3[1])} {Z3 + float(VTemp3[2])} \n')
                 #-------------------------------------------------------------------------------------------
                 poscar1.close()
                 poscar2.close()
                 if (n_Lattice == 3):  poscar3.close()
                 poscar_new.close()
                 #-----------------

                 #--------------------------------------------------------------
                 # Excluding Distorted Heterostructures ------------------------
                 #--------------------------------------------------------------
                 dist_3 = 0.0
                 dist_1 = abs(var_A1 -var_B1)
                 dist_2 = abs(var_A2 -var_B2)
                 if (n_Lattice == 3): dist_3 = abs(var_A3 -var_B3)
                 #----------------------------------------------------------------------------------------------------
                 if (dist_1 > crit_distorc_lattice or dist_2 > crit_distorc_lattice or dist_3 > crit_distorc_lattice):
                    os.remove(diret2 + dir_temp_m + '/POSCAR_' + str(i+1) + '.vasp')
   #-----------------------------------------
   print(f"\rProgress completed !{' ' * 60}")
   #-----------------------------------------


#=====================================================================
# Deleting the directory containing temporary calculation files: =====
#=====================================================================
shutil.rmtree(dir_files + '/' + 'output')
#========================================


#---------------
n_structures = 0
#---------------
files0 = os.listdir(diret2)
#--------------------------
for i in range(len(files0)):
    files1 = os.listdir(diret2 + files0[i])
    n_structures += len(files1)
#------------------------------


n += 1
#----------
print(f' ')
print(f'================================')
print(f'Step {n}: Excluding non-unit cells')
print(f'================================')

files0 = os.listdir(diret2)
n_exclusion = 0

temp = 1.0; number = -1; n_passos = len(files0)
#---------------------------
for s in range(len(files0)):
    #-----------------------
    number += 1; cont = 0
    porc = (number/(s+1))*100        
    #-------------------------
    if porc >= temp:
       bar_length = 50
       filled_length = int(bar_length * porc // 100)
       bar = '#' * filled_length + '-' * (bar_length - filled_length)
       print(f'\rProgress: |{bar}| {porc:.1f}%', end="")
       sys.stdout.flush()
       temp += 1

    #---------------------
    dir_temp_m = files0[s]
    #---------------------

    files = os.listdir(diret2 + files0[s])

    for i in range(len(files)):
        #--------------------------
        structure = Poscar.from_file(diret2 + files0[s] + '/' + files[i]).structure   # Reading the POSCAR file
        matcher = StructureMatcher()                                                  # Creating a StructureMatcher object 
        reduced_structure = matcher._get_reduced_structure(structure)                 # Obtaining the corresponding reduced unit cell
        Poscar(reduced_structure).write_file(diret2 + files0[s] + '/' + 'temp_' + str(i+1) + '.vasp')

        poscar1 = open(diret2 + files0[s] + '/' + files[i], "r")
        poscar2 = open(diret2 + files0[s] + '/' + 'temp_' + str(i+1) + '.vasp', "r")

        nion1 = 0; nion2 = 0
        #-------------------
        for ii in range(7):
            VTemp1 = poscar1.readline().split()
            VTemp2 = poscar2.readline().split()
        for j in range(len(VTemp1)): nion1 += int(VTemp1[j])
        for j in range(len(VTemp2)): nion2 += int(VTemp2[j])
        poscar1.close()
        poscar2.close()
        #---------------------------------------------------
        if (nion2 < nion1):
           os.remove(diret2 + files0[s] + '/' + files[i])
           n_exclusion += 1

    for i in range(len(files)):
        os.remove(diret2 + files0[s] + '/' + 'temp_' + str(i+1) + '.vasp')
#-----------------------------------------
print(f"\rProgress completed !{' ' * 60}")
#-----------------------------------------

#---------------
n_structures = 0
#---------------
files0 = os.listdir(diret2)
#--------------------------
for i in range(len(files0)):
    files1 = os.listdir(diret2 + files0[i])
    n_structures += len(files1) 
    #--------------------------
    if (len(files1) == 0): shutil.rmtree(diret2 + files0[i])
#-----------------------------------------------------------
files0 = os.listdir(diret2)
#-------------------------------------------
if (len(files0) == 0):
   print(f' ')
   print(f'=====================')
   print(f'No cells were found !')
   print(f'=====================')
   print(f' ')
   #========================================================
   if (loop_ht == 0): shutil.rmtree(dir_files + '/' + dir_o)
   sys.exit()    
   #=========


#========================================================
print(f'--------------------------------')
print(f'{n_exclusion} cells were filtered/excluded')
print(f'{n_structures} remaining cells')
#========================================================


#=====================================================================
# Filtering/Excluding Similar POSCAR Files ===========================
# within the temporary subdirectories of the POSCAR files ============
#=====================================================================

n += 1
#----------
print(f' ')
print(f'=================================')
print(f'Step {n}: Deleting Similar Lattices')
print(f'=================================')

files0 = os.listdir(diret2)
n_exclusion = 0

temp = 1.0; number = -1; n_passos = len(files0)
#---------------------------
for s in range(len(files0)):
    #-----------------------
    number += 1; cont = 0
    porc = (number/(s+1))*100        
    #-------------------------
    if porc >= temp:
       bar_length = 50
       filled_length = int(bar_length * porc // 100)
       bar = '#' * filled_length + '-' * (bar_length - filled_length)
       print(f'\rProgress: |{bar}| {porc:.1f}%', end="")
       sys.stdout.flush()
       temp += 1

    #---------------------
    dir_temp_m = files0[s]
    #-------------------------------------
    files = os.listdir(diret2 + files0[s])
    files_delete = []
    #--------------------------
    for i in range(len(files)):
        #------------------------------------------------------
        if os.path.exists(diret2 + files0[s] + '/' + files[i]):
           #---------------------------------------------------------------------------
           structure1 = Poscar.from_file(diret2 + files0[s] + '/' + files[i]).structure
           #---------------------------------------------------------------------------
           poscar = open(diret2 + files0[s] + '/' + files[i], "r")
           #--------------------------------
           VTemp = poscar.readline().split()
           if (n_Lattice == 2):
              Angle_AB1 = float(VTemp[27])
           if (n_Lattice == 3):
              temp_angle = VTemp[28].replace('_',' ').split()
              Angle_AB1 = float(temp_angle[0]) 
           #---------------------------------------------- 
           param = poscar.readline(); param = float(param)
           VTemp = poscar.readline().split();  Ax = float(VTemp[0])*param; Ay = float(VTemp[1])*param;  A = np.array([Ax, Ay]);  mA = np.linalg.norm(A)
           VTemp = poscar.readline().split();  Bx = float(VTemp[0])*param; By = float(VTemp[1])*param;  B = np.array([Bx, By]);  mB = np.linalg.norm(B)
           dAB1 = abs(mA - mB)
           poscar.close()
           #-------------

           for j in range(len(files)):
               if (i != j):
                  #------------------------------------------------------
                  if os.path.exists(diret2 + files0[s] + '/' + files[j]):
                     #--------------------------------------------------------------------------
                     structure2 = Poscar.from_file(diret2 + files0[s] + '/' + files[j]).structure
                     #----------------------------------------------------------------------------------
                     matcher = StructureMatcher()                   # Creating a StructureMatcher object
                     if matcher.fit(structure1, structure2):        # Checking if the structures are similar
                        #-----------------------------------------------------------------------------------
                        poscar = open(diret2 + files0[s] + '/' + files[j], "r")
                        #--------------------------------
                        VTemp = poscar.readline().split()
                        if (n_Lattice == 2):
                           Angle_AB2 = float(VTemp[27])
                        if (n_Lattice == 3):
                           temp_angle = VTemp[28].replace('_',' ').split()
                           Angle_AB2 = float(temp_angle[0]) 
                        #---------------------------------------------- 
                        param = poscar.readline(); param = float(param)
                        VTemp = poscar.readline().split();  Ax = float(VTemp[0])*param; Ay = float(VTemp[1])*param;  A = np.array([Ax, Ay]);  mA = np.linalg.norm(A)
                        VTemp = poscar.readline().split();  Bx = float(VTemp[0])*param; By = float(VTemp[1])*param;  B = np.array([Bx, By]);  mB = np.linalg.norm(B)
                        dAB2 = abs(mA - mB)
                        poscar.close()
                        #----------------
                        if (dAB1 < dAB2):
                           if os.path.exists(diret2 + files0[s] + '/' + files[j]):
                              os.remove(diret2 + files0[s] + '/' + files[j])
                              n_exclusion += 1
                        #----------------
                        if (dAB1 > dAB2):
                           if os.path.exists(diret2 + files0[s] + '/' + files[i]):
                              os.remove(diret2 + files0[s] + '/' + files[i])
                              n_exclusion += 1
                        #-----------------
                        if (dAB1 == dAB2):
                           cont = 1
                           #--------------------------------------------------------
                           if ( (Angle_AB1 < 0) and (Angle_AB2 > 0) and cont == 1 ):
                              if os.path.exists(diret2 + files0[s] + '/' + files[i]):
                                 os.remove(diret2 + files0[s] + '/' + files[i])
                                 n_exclusion += 1; cont = 0
                           if ( (Angle_AB1 > 0) and (Angle_AB2 < 0) and cont == 1 ):
                              if os.path.exists(diret2 + files0[s] + '/' + files[j]):
                                 os.remove(diret2 + files0[s] + '/' + files[j])
                                 n_exclusion += 1; cont = 0
                           if (abs(Angle_AB1) < abs(Angle_AB2) and cont == 1):
                              if os.path.exists(diret2 + files0[s] + '/' + files[j]):
                                 os.remove(diret2 + files0[s] + '/' + files[j])
                                 n_exclusion += 1; cont = 0
                           if (abs(Angle_AB1) > abs(Angle_AB2) and cont == 1):
                              if os.path.exists(diret2 + files0[s] + '/' + files[i]):
                                 os.remove(diret2 + files0[s] + '/' + files[i])
                                 n_exclusion += 1; cont = 0
                           if (Angle_AB1 == Angle_AB2 and cont == 1):
                              if os.path.exists(diret2 + files0[s] + '/' + files[j]):
                                 os.remove(diret2 + files0[s] + '/' + files[j])
                                 n_exclusion += 1
#-----------------------------------------
print(f"\rProgress completed !{' ' * 60}")
#-----------------------------------------

#---------------
n_structures = 0
#---------------
files0 = os.listdir(diret2)
#---------------------------
for i in range(len(files0)):
    files1 = os.listdir(diret2 + files0[i])
    n_structures += len(files1) 
#========================================================
print(f'---------------------------------')
print(f'{n_exclusion} cells were filtered/excluded')
print(f'{n_structures} remaining cells')
#========================================================


#=====================================================================
# Deleting temporary subdirectories of POSCAR files ==================
#=====================================================================
number = 0
#--------------------------
files0 = os.listdir(diret2)
#---------------------------
for i in range(len(files0)):
    #--------------------------------------
    files1 = os.listdir(diret2 + files0[i])
    #--------------------------------------
    for j in range(len(files1)):
        number += 1 
        shutil.copyfile(diret2 + files0[i] + '/' + files1[j],  diret2 + 'POSCAR_' + str(number))
    #-------------------------------------------------------------------------------------------
    shutil.rmtree(diret2 + files0[i])
    #--------------------------------


#=====================================================================
# Filtering/Excluding Similar POSCAR Files ===========================
# within the final directory of the POSCAR files =====================
#=====================================================================

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Introduce the exclusion loop until two iterations return a null exclusion
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

n_exclusion_cont = 0

while n_exclusion_cont != 2:

   n += 1
   #----------
   print(f' ')
   print(f'=================================')
   print(f'Step {n}: Deleting Similar Lattices')
   print(f'=================================')

   files = os.listdir(diret2)
   n_exclusion = 0

   temp = 1.0; number = -1; n_passos = len(files)
   #--------------------------
   for i in range(len(files)):
       #----------------------
       number += 1; cont = 0
       porc = (number/(s+1))*100        
       #-------------------------
       if porc >= temp:
          bar_length = 50
          filled_length = int(bar_length * porc // 100)
          bar = '#' * filled_length + '-' * (bar_length - filled_length)
          print(f'\rProgress: |{bar}| {porc:.1f}%', end="")
          sys.stdout.flush()
          temp += 1
 
       #----------------
       files_delete = []
       #------------------------------------
       if os.path.exists(diret2 + files[i]):
          #---------------------------------------------------------
          structure1 = Poscar.from_file(diret2 + files[i]).structure
          #---------------------------------------------------------
          poscar = open(diret2 + files[i], "r")
          #--------------------------------
          VTemp = poscar.readline().split()
          if (n_Lattice == 2):
             Angle_AB1 = float(VTemp[27])
          if (n_Lattice == 3):
             temp_angle = VTemp[28].replace('_',' ').split()
             Angle_AB1 = float(temp_angle[0]) 
          #---------------------------------------------- 
          param = poscar.readline(); param = float(param)
          VTemp = poscar.readline().split();  Ax = float(VTemp[0])*param; Ay = float(VTemp[1])*param;  A = np.array([Ax, Ay]);  mA = np.linalg.norm(A)
          VTemp = poscar.readline().split();  Bx = float(VTemp[0])*param; By = float(VTemp[1])*param;  B = np.array([Bx, By]);  mB = np.linalg.norm(B)
          dAB1 = abs(mA - mB)
          poscar.close()
          #-------------
          for j in range(len(files)):
              if (i != j):
                 #------------------------------------
                 if os.path.exists(diret2 + files[j]):
                    #---------------------------------------------------------
                    structure2 = Poscar.from_file(diret2 + files[j]).structure
                    #----------------------------------------------------------------------------------
                    matcher = StructureMatcher()                   # Creating a StructureMatcher object
                    if matcher.fit(structure1, structure2):        # Checking if the structures are similar
                       #-----------------------------------------------------------------------------------
                       poscar = open(diret2 + files[j], "r")
                       #--------------------------------
                       VTemp = poscar.readline().split()
                       if (n_Lattice == 2):
                          Angle_AB2 = float(VTemp[27])
                       if (n_Lattice == 3):
                          temp_angle = VTemp[28].replace('_',' ').split()
                          Angle_AB2 = float(temp_angle[0]) 
                       #----------------------------------------------
                       param = poscar.readline(); param = float(param)
                       VTemp = poscar.readline().split();  Ax = float(VTemp[0])*param; Ay = float(VTemp[1])*param;  A = np.array([Ax, Ay]);  mA = np.linalg.norm(A)
                       VTemp = poscar.readline().split();  Bx = float(VTemp[0])*param; By = float(VTemp[1])*param;  B = np.array([Bx, By]);  mB = np.linalg.norm(B)
                       dAB2 = abs(mA - mB)
                       poscar.close()
                       #----------------
                       if (dAB1 < dAB2):
                          if os.path.exists(diret2 + + files[j]):
                             os.remove(diret2 + files[j])
                             n_exclusion += 1
                       #----------------
                       if (dAB1 > dAB2):
                          if os.path.exists(diret2 + files[i]):
                             os.remove(diret2 + files[i])
                             n_exclusion += 1
                       #-----------------
                       if (dAB1 == dAB2):
                          cont = 1
                          #--------------------------------------------------------
                          if ( (Angle_AB1 < 0) and (Angle_AB2 > 0) and cont == 1 ):
                             if os.path.exists(diret2 + files[i]):
                                os.remove(diret2 + files[i])
                                n_exclusion += 1; cont = 0
                          if ( (Angle_AB1 > 0) and (Angle_AB2 < 0) and cont == 1 ):
                             if os.path.exists(diret2 + files[j]):
                                os.remove(diret2 + files[j])
                                n_exclusion += 1; cont = 0
                          if (abs(Angle_AB1) < abs(Angle_AB2) and cont == 1):
                             if os.path.exists(diret2 + files[j]):
                                os.remove(diret2 + files[j])
                                n_exclusion += 1; cont = 0
                          if (abs(Angle_AB1) > abs(Angle_AB2) and cont == 1):
                             if os.path.exists(diret2 + files[i]):
                                os.remove(diret2 + files[i])
                                n_exclusion += 1; cont = 0
                          if (Angle_AB1 == Angle_AB2 and cont == 1):
                             if os.path.exists(diret2 + files[j]):
                                os.remove(diret2 + files[j])
                                n_exclusion += 1
   #-----------------------------------------
   print(f"\rProgress completed !{' ' * 60}")
   #-----------------------------------------

   #-------------------------
   files = os.listdir(diret2)
   n_structures = len(files)
   #------------------------

   if (n_exclusion != 0):  n_exclusion_cont  = 0
   if (n_exclusion == 0):  n_exclusion_cont += 1
   if (n_structures == 1): n_exclusion_cont  = 2


#=====================================================================
# Renaming POSCAR files for better data organization =================
#=====================================================================
files = os.listdir(diret2)
#--------------------------
for i in range(len(files)):
    #--------------------------------------------------------------------------------------------
    # Creating a unique 8-digit ID that encodes the POSCAR file structure -----------------------
    #--------------------------------------------------------------------------------------------
    with open(diret2 + files[i], 'r') as f: lines = [line.strip() for line in f.readlines() if line.strip()]
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
    new_id = hashlib.sha256(canonical_string.encode('utf-8')).hexdigest()[:8]
    #------------------------------------------------------------------------


    #------------------------------------
    poscar = open(diret2 + files[i], "r")
    #------------------------------------ 
    VTemp1 = poscar.readline().split()
    if (n_Lattice == 2):
       var_area = str(VTemp1[11])
       rotation_angle = str(VTemp1[27])
    if (n_Lattice == 3):
       var_area = str(VTemp1[12])
       rotation_angle = str(VTemp1[28])
    #---------------------------------
    VTemp = poscar.readline()
    param = float(VTemp)
    #----------------------------
    A = poscar.readline().split()
    B = poscar.readline().split()
    #----------------------------------------------------
    for ii in range(3): VTemp = poscar.readline().split()
    nion = 0
    for j in range(len(VTemp)):  nion += int(VTemp[j])
    if (nion < 10):                  n_ion = '00' + str(nion) + 'atoms'
    if (nion >= 10 and nion < 100):  n_ion = '0'  + str(nion) + 'atoms'
    if (nion >= 100):                n_ion = ''   + str(nion) + 'atoms'
    #------------------------------------------------------------------
    poscar.close()
    #-------------


    #-------------------------------------
    current_name = diret2 + files[i]
    if (n_Lattice == 2):
       new_name = diret2 + n_ion + '_' + var_area + '_' + rotation_angle + '_' + str(VTemp1[-1]) + '+' + new_id + '.vasp'
    if (n_Lattice == 3):
       new_name = diret2 + n_ion + '_' + var_area + '_' + rotation_angle + '_'+ str(VTemp1[-1]) + '+' + new_id + '.vasp'
    os.rename(current_name, new_name)
    #--------------------------------


    #---------------------------
    poscar = open(new_name, "r")
    VTemp = poscar.readline().split()
    poscar.close()
    #-------------
    t_VTemp = ''
    for ii in range(len(VTemp) -1):
        t_VTemp += str(VTemp[ii]) + ' '
    if (n_Lattice > 1): 
       for ii in range(n_Lattice): t_VTemp += id_materials[ii] + ' ' 
    t_VTemp += str(VTemp[len(VTemp)-1])
    #=-------------------------------------------------------
    with open(new_name, 'r') as file: line = file.readlines()
    #=-------------------------------------------------------
    line[0] = t_VTemp + '+' + new_id + '\n'
    #--------------------------------------
    """
    for ii in range(nion):
        VTemp = line[8+ii].split()
        for ij in range(3):
            VTemp[ij] = float(VTemp[ij])
            for ik in range(len(coord_direct)):
                if (abs(VTemp[ij] -coord_direct[ik]) < 0.0001): VTemp[ij] = coord_direct[ik]
        line[8+ii] = str(VTemp[0]) + ' ' + str(VTemp[1]) + ' ' + str(VTemp[2]) + '\n'
    """
    #------------------------------------------------------
    with open(new_name, 'w') as file: file.writelines(line)
    #------------------------------------------------------
    nions = int(n_ion.replace("atoms",""))
    if (nions < ions_crit_i or nions > ions_crit_f):
       n_exclusion_cont += 1
       os.remove(new_name)

#-------------------------
files = os.listdir(diret2)
n_structures = len(files)
#------------------------

#==========================================
print(f'---------------------------------')
print(f'{n_exclusion} cells were filtered/excluded')
if (n_structures == 1): print(f'Only one cell was found')
if (n_structures >  1): print(f'{n_structures} cells were found')
#==========================================


"""
#=====================================================================
# Adjusting direct coordinates of lattices ===========================
#=====================================================================

n += 1
#----------
print(f' ')
print(f'=====================================')
print(f'Step {n}: Adjusting direct coordinates')
print(f'=====================================')

if (loop_ht == 0):
   dir1 = dir_files + '/' + dir_o + '/'
   dir2 = dir_files + '/' + dir_o + '_temp/'
if (loop_ht == 1):
   dir1 = dir_files + '/' + dir_o + '/' + dir_loop + '/'
   dir2 = dir_files + '/' + dir_o + '/' + dir_loop + '_temp/'

os.mkdir(dir2)

vector_p = [0.0, 0.5, 1.0, 1.7320508075688772935274463415059, 0.86602540378443864676372317075294, 0.28867513459481288225457439025098, 1.4142135623730950488016887242097, 0.70710678118654752440084436210485]

vector_n = [0.0, -0.5, -1.0, -1.7320508075688772935274463415059, -0.86602540378443864676372317075294, -0.28867513459481288225457439025098, -1.4142135623730950488016887242097, -0.70710678118654752440084436210485]

#--------------------------------------------------------------------------

def truncate_to_14_decimals(number):
    factor = 10 ** 14                              # Multiply by 10^14 to move the decimal point
    return math.trunc(number * factor) / factor    # Truncates and returns to original scale

shift0_xy = []
shift1_xy = []

for i in range(1,(10+1)):
    for j in range(0,(10+1)):
        if (i != 7):
           frac = j/i
           frac = round(frac, 15)
           if (frac < 1.0):
              shift0_xy.append(frac)

for i in range(0,10):
    for j in range(1,(10+1)):
        if (j != 20):
           frac = (i/10) + (j/90)
           frac = round(frac, 15)
           if (frac < 1.0):
              shift0_xy.append(frac)

vector = [0.0, (1/15), (1/12), (1/8), (1/6), (1/4), (1/3), (1/2), (2/3), (3/4), (5/6), 1.0]
#------------------------------------------------------------------------------------------
for i in range(len(vector)):
    for j in range(len(shift0_xy)):
        frac = float(vector[i]) + shift0_xy[j]
        frac = round(frac, 15)
        frac = truncate_to_14_decimals(frac)
        if (frac < 1.0):
           shift1_xy.append(frac)
#--------------------------------
vector = sorted(set(shift1_xy))

#-------------------------
files = os.listdir(diret2)
#-------------------------
temp = 1.0; number = -1; n_passos = len(files)
#--------------------------
for i in range(len(files)):
    #----------------------
    number += 1; cont = 0
    porc = (number/(s+1))*100        
    #-------------------------
    if porc >= temp:
       bar_length = 50
       filled_length = int(bar_length * porc // 100)
       bar = '#' * filled_length + '-' * (bar_length - filled_length)
       print(f'\rProgress: |{bar}| {porc:.1f}%', end="")
       sys.stdout.flush()
       temp += 1

    poscar  = open(dir1 + files[i], "r")
    poscar2 = open(dir2 + files[i], "w")

    VTemp = poscar.readline()
    poscar2.write(f'{VTemp}')

    VTemp = poscar.readline().split()
    poscar2.write(f'{VTemp[0]} \n')

    for j in range(3):
        VTemp = poscar.readline().split()
        for k in range(3):
            VTemp[k] = float(VTemp[k]); VTemp[k] = round(VTemp[k], 12)
            for l in range(len(vector_p)):
                if (abs(VTemp[k] -vector_p[l]) < 0.0001): VTemp[k] = vector_p[l]
                if (abs(VTemp[k] -vector_n[l]) < 0.0001): VTemp[k] = vector_n[l]
        poscar2.write(f'{VTemp[0]} {VTemp[1]} {VTemp[2]} \n')

    for j in range(3):
        VTemp = poscar.readline().split()
        for k in range(len(VTemp)):
            poscar2.write(f'{VTemp[k]} ')
        poscar2.write(f'\n')
        #-------------------
        if (j == 1):
           nion = 0
           for k in range(len(VTemp)):
               nion += int(VTemp[k])

    for j in range(nion):
        VTemp = poscar.readline().split()
        for k in range(3):
            VTemp[k] = float(VTemp[k]); VTemp[k] = round(VTemp[k], 12)
            for l in range(len(vector)):
                if (abs(VTemp[k] -vector[l]) < 0.00001): VTemp[k] = vector[l]
        #----------------------------------------------------
        poscar2.write(f'{VTemp[0]} {VTemp[1]} {VTemp[2]} \n')
    #-------------
    poscar.close()
    poscar2.close()
#-----------------------------------------
print(f"\rProgress completed !{' ' * 60}")
#-----------------------------------------

#------------------
shutil.rmtree(dir1)
os.rename(dir2,dir1)
#-------------------
"""


print(f' ')
print(f'============================================')
print(f'Completed ==================================')
print(f'============================================')
print(f' ')
#----------
sys.exit() 
#----------
