# SAMBA_ilum Copyright (C) 2025
# GNU GPL-3.0 license


os.chdir(path_vaspkit)

type_kpoints = 1
if (task[m][:5] == 'bands'):  type_kpoints = 0 


if (type_kpoints == 0):

   #=====================================================================
   # Generating the KPOINTS file of the scf calculation (viA VASPKIT) ===
   #=====================================================================
   f = open('temp.txt', 'w')
   subprocess.run(['vaspkit', '-task', '30' + str(type_lattice)], stdout=f)
   os.remove('temp.txt')

   #=================================================================
   # Editing the KPOINTS file of the scf calculation ================
   #=================================================================
   if os.path.exists('HIGH_SYMMETRY_POINTS'):  os.remove('HIGH_SYMMETRY_POINTS')
   if os.path.exists('PRIMCELL.vasp'):  os.remove('PRIMCELL.vasp')
   if os.path.exists('SYMMETRY'):  os.remove('SYMMETRY')
   if os.path.exists('INCAR'):  os.remove('INCAR')
   os.rename('KPATH.in', 'KPOINTS_bands_t.txt')
   #-------------------------------------------
   bands0 = open('KPOINTS_bands_t.txt', "r")
   bands1 = open('KPOINTS',   "w")
   #----------------------------------------------------
   VTemp = bands0.readline();  bands1.write(f'BANDS \n')
   VTemp = bands0.readline();  bands1.write(f'{n_kpoints} \n')
   for ii in range(2):
       VTemp = bands0.readline();  bands1.write(f'{VTemp}')
   test = 0
   while (test != 2):	
         VTemp = bands0.readline().replace('_', '').replace('GAMMA', '#1 (Gamma)').split()
         if (len(VTemp) != 0):
            test = 0
            for ii in range(len(VTemp)): bands1.write(f'{VTemp[ii]} ') 
            bands1.write(f'\n')
         if (len(VTemp) == 0):
            test += 1
            bands1.write(f'\n')
   #-------------
   bands0.close()
   bands1.close()
   #-------------------------------
   os.remove('KPOINTS_bands_t.txt')
   #-------------------------------

   #=============================================================
   # Checking whether the band calculation should be splitted ===
   #=============================================================
   poscar = open('POSCAR', "r")
   nions = 0
   for ii in range(7): VTemp = poscar.readline().split()
   for ii in range(len(VTemp)): nions += int(VTemp[ii])
   poscar.close()
   #-------------

   if (nions >= nions_split):
      #-----------------------------
      kpoints = open('KPOINTS', "r")
      VTemp1 = kpoints.readline()
      VTemp2 = kpoints.readline()
      VTemp3 = kpoints.readline()
      VTemp4 = kpoints.readline()
      number2  = 0
      for ii in range(100):
          VTemp = kpoints.readline().split()
          if (len(VTemp) > 0): number2  += 1
      kpoints.close()     
      #-------------------
      for ii in range(100):
          crit = number2  -1 -ii
          if (crit == (ii+1)): n_kpoints_file = ii+1 
      #---------------------------------------------
      kpoints = open('KPOINTS', "r")
      for ii in range(4): VTemp = kpoints.readline()
      #---------------------------------------------
      for ii in range(n_kpoints_file):
          kpoints_new = open('KPOINTS.' + str(ii+1), "w")
          kpoints_new.write(f'{VTemp1}')
          kpoints_new.write(f'{VTemp2}')
          kpoints_new.write(f'{VTemp3}')
          kpoints_new.write(f'{VTemp4}')
          for ij in range(3):
              VTemp = kpoints.readline()
              kpoints_new.write(f'{VTemp}')
          kpoints_new.close()

      #-------------------
      os.remove('KPOINTS')
      #-------------------



if ((type_kpoints == 1) and (type_k_dens < 3)):
   #===========================================================
   # Generating the KPOINTS file of the nscf calculation ======
   #===========================================================

   #---------------------------------------------------
   if (type_k_dens == 1):     l_dens = 'Monkhorst-Pack'
   if (type_k_dens == 2):     l_dens = 'Gamma'
   if (task[m][:3] == 'dos'): l_dens = 'Gamma'
   #------------------------------------------
   poscar = open('POSCAR', "r")
   kpoints = open('KPOINTS', "w")
   #-----------------------------
   VTemp = poscar.readline()
   VTemp = poscar.readline().split();  param = float(VTemp[0])
   V = poscar.readline().split();  A1x=float(V[0])*param; A1y=float(V[1])*param; A1z=float(V[2])*param
   V = poscar.readline().split();  A2x=float(V[0])*param; A2y=float(V[1])*param; A2z=float(V[2])*param
   V = poscar.readline().split();  A3x=float(V[0])*param; A3y=float(V[1])*param; A3z=float(V[2])*param
   #-------------
   poscar.close()

   #----------------------------------------------
   # Obtaining the vectors of reciprocal space ---
   #----------------------------------------------
   ss1 = A1x*((A2y*A3z) - (A2z*A3y))
   ss2 = A1y*((A2z*A3x) - (A2x*A3z))
   ss3 = A1z*((A2x*A3y) - (A2y*A3x))
   ss =  ss1 + ss2 + ss3
   V_real = abs(ss)           # Cell volume in real space
   #-----------------------------------------------------
   B1x = ((A2y*A3z) - (A2z*A3y))/ss;  B1x = B1x*(2*np.pi)
   B1y = ((A2z*A3x) - (A2x*A3z))/ss;  B1y = B1y*(2*np.pi)
   B1z = ((A2x*A3y) - (A2y*A3x))/ss;  B1z = B1z*(2*np.pi)
   B2x = ((A3y*A1z) - (A3z*A1y))/ss;  B2x = B2x*(2*np.pi)
   B2y = ((A3z*A1x) - (A3x*A1z))/ss;  B2y = B2y*(2*np.pi)
   B2z = ((A3x*A1y) - (A3y*A1x))/ss;  B2z = B2z*(2*np.pi)
   B3x = ((A1y*A2z) - (A1z*A2y))/ss;  B3x = B3x*(2*np.pi)
   B3y = ((A1z*A2x) - (A1x*A2z))/ss;  B3y = B3y*(2*np.pi)
   B3z = ((A1x*A2y) - (A1y*A2x))/ss;  B3z = B3z*(2*np.pi)

   #-------------------------------------------------------------------------
   # Getting the number of k-points in each direction of reciprocal space ---
   #-------------------------------------------------------------------------
   B1 = [B1x, B1y, B1z];  mB1 = np.linalg.norm(B1)
   B2 = [B2x, B2y, B2z];  mB2 = np.linalg.norm(B2)
   B3 = [B3x, B3y, B3z];  mB3 = np.linalg.norm(B3)
   #----------------------------------------------
   N1 = mB1 * k_dens; t = N1 - int(N1)
   if (t >= 0.5):  N1 = int(N1) + 1
   if (t <  0.5):  N1 = int(N1)
   if (N1 < 3):    N1 = 3
   #-------------------------------------
   N2 = mB2 * k_dens; t = N2 - int(N2)
   if (t >= 0.5):  N2 = int(N2) + 1
   if (t <  0.5):  N2 = int(N2)
   if (N2 < 3):    N2 = 3
   #-------------------------------------
   N3 = mB3 * k_dens; t = N3 - int(N3)
   if (t >= 0.5):  N3 = int(N3) + 1
   if (t <  0.5):  N3 = int(N3)
   if (N3 < 3):    N3 = 3
   #--------------------------------------------------------------------------
   if (type_lattice == 1  or  type_lattice == '1D'  or  type_lattice == '1d'):
      N2 = 1;  N3 = 1
   if (type_lattice == 2  or  type_lattice == '2D'  or  type_lattice == '2d'):
      N3 = 1

   #-----------------------------
   # Writing the KPOINTS file ---
   #-----------------------------
   kpoints.write(f'KPOINTS {N1}x{N2}x{N3} \n')
   kpoints.write(f'0 \n')
   kpoints.write(f'{l_dens} \n')
   kpoints.write(f'{N1} {N2} {N3} \n')
   kpoints.write(f'0.0 0.0 0.0 \n')
   kpoints.close()

os.chdir(dir_samba)
