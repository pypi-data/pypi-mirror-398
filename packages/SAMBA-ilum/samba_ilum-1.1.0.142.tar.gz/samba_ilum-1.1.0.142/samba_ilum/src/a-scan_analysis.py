# SAMBA_ilum Copyright (C) 2025
# GNU GPL-3.0 license


from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import numpy as np
import shutil
import os


#==========================================================================
# Obtaining the Heterostructure Lattice Vectors ===========================
#==========================================================================
poscar = open('POSCAR.0', "r")
#-----------------------------
VTemp = poscar.readline()
VTemp = poscar.readline();  param = float(VTemp)
VTemp = poscar.readline().split();  A1x = float(VTemp[0])*param;  A1y = float(VTemp[1])*param;  A1z = float(VTemp[2])*param
VTemp = poscar.readline().split();  A2x = float(VTemp[0])*param;  A2y = float(VTemp[1])*param;  A2z = float(VTemp[2])*param
VTemp = poscar.readline().split();  A3x = float(VTemp[0])*param;  A3y = float(VTemp[1])*param;  A3z = float(VTemp[2])*param
#-------------
poscar.close()
#-------------


#=====================================================================================
# Adopting the lattice parameter as the modulus of the smallest lattice vector =======
#=====================================================================================
A1 = np.array([float(A1x), float(A1y), float(A1z)]);  module_a1 = float(np.linalg.norm(A1))
A2 = np.array([float(A2x), float(A2y), float(A2z)]);  module_a2 = float(np.linalg.norm(A2))
A3 = np.array([float(A3x), float(A3y), float(A3z)]);  module_a3 = float(np.linalg.norm(A3))
#------------------------------------------------------------------------------------------
if (module_a1 <= module_a2):
   param_initial = module_a1
   vector = 'A1'
if (module_a2 < module_a1):
   param_initial = module_a2
   vector = 'A2'
# if ((type_lattice = 3) and (module_a3 < module_a1) or (module_a3 < module_a2)):
#    param_initial = module_a3
#    vector = 'A3'
#-----------------


#====================================================
# Extracting information ============================
#====================================================
shutil.copy('energy_scan.txt', 'a-scan.dat')
#-------------------------------------------
file0 = np.loadtxt('a-scan.dat')
file0.shape
#-------------------
date_a  = file0[:,0]
date_E  = file0[:,1] -min(file0[:,1])
#------------------------------------
a_min   = min(date_a)
a_max   = max(date_a)
E_min   = min(date_E)
E_max   = max(date_E)
a_opt = date_a[np.argmin(date_E)]
#-------------------------------------------------
fator = ((a_opt -param_initial)/param_initial)*100
fator = np.around(fator, decimals=3)
#-----------------------------------


#------------------------------------------------
shutil.copyfile(str(a_opt) + '/POSCAR', 'POSCAR')
shutil.copyfile(str(a_opt) + '/CONTCAR', 'CONTCAR')
#--------------------------------------------------


"""
#=======================================
# Interpolating a-scan data ============
#=======================================
n_d = 250
#--------
f = interp1d(date_a, date_E, kind='cubic')
x_interp = np.linspace(a_min, a_max, n_d)
y_interp = f(x_interp)
"""


#=============================================
# Reordering the lists date_a and date_E =====
#=============================================
listas_combinadas = list(zip(date_a, date_E))    # Combining the lists
listas_ordenadas = sorted(listas_combinadas)     # Sorting the combined lists based on the elements of the first list
new_date_a, new_date_E = zip(*listas_ordenadas)  # Separating the lists
new_date_a = list(new_date_a)                    # Converting to list format
new_date_E = list(new_date_E)                    # Converting to list format
#============================================


#===================================================
# Plot 2D ==========================================
#===================================================
fig, ax = plt.subplots()
plt.plot([a_opt, a_opt], [-1000.0, +1000.0], color = 'red', linestyle = '--', linewidth = 1.0, alpha = 1.0)
# plt.plot(x_interp, y_interp, color = 'black', linestyle = '-', linewidth = 1.0)
plt.plot(date_a, date_E, color = 'black', linestyle = '-', linewidth = 1.0)
plt.scatter(date_a, date_E, s=5, color = 'black')
plt.title('$a$-scan', fontsize=10)
plt.xlim((a_min, a_max))
#------------------------------
delta_E = abs(E_max -E_min)*0.1
#------------------------------
plt.ylim((E_min -delta_E, E_max +delta_E))
plt.xlabel('$a_{optimized}$(${\AA}$)')
plt.ylabel('$E-E_{min}(eV)$')
ax.set_box_aspect(1.25/1)
#----------------------------------------------------------------------
plt.savefig('a-scan.png', dpi = 600, bbox_inches='tight', pad_inches=0)
# plt.savefig('a-scan.pdf', dpi = 600, bbox_inches='tight', pad_inches=0)
# plt.savefig('a-scan.svg', dpi = 600, bbox_inches='tight', pad_inches=0)
# plt.savefig('a-scan.eps', dpi = 600, bbox_inches='tight', pad_inches=0)


#=====================================================
info = open('info_a-scan.dat', "w", encoding='utf-8')
info.write(f'============================================================================== \n')
info.write(f'Optimized lattice parameter: a = {a_opt} Å\n')
info.write(f'------------------------------------------------------------------------------ \n')
info.write(f'a_initial = {param_initial} Å (|{vector}|);  multiplication factor = {fator}% \n')
info.write(f'============================================================================== \n')
info.close()
#===========
                                                                                                                                                                                                                                                                                   