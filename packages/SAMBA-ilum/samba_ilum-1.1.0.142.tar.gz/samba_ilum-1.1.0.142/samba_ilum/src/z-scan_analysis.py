# SAMBA_ilum Copyright (C) 2025
# GNU GPL-3.0 license


from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import numpy as np
import shutil
import os


#====================================================================
# Obtaining the area in the XY plane of the Heterostructure =========
#====================================================================
poscar = open('POSCAR.0', 'r')
VTemp = poscar.readline().split()
VTemp = poscar.readline();  param = float(VTemp)
#-----------------------------------------------
A1 = poscar.readline().split();  A1x = float(A1[0])*param; A1y = float(A1[1])*param; A1z = float(A1[2])*param
A2 = poscar.readline().split();  A2x = float(A2[0])*param; A2y = float(A2[1])*param; A2z = float(A2[2])*param
A3 = poscar.readline().split();  A3x = float(A3[0])*param; A3y = float(A3[1])*param; A3z = float(A3[2])*param
#------------------------------------------------------------------------------------------------------------
A1 = np.array([A1x, A1y])
A2 = np.array([A2x, A2y])
#---------------------------
# Área da célula no plano XY
Area = np.linalg.norm(np.cross(A1, A2))
#--------------------------------------


#===================================================
# Extracting information ===========================
#===================================================
shutil.copy('energy_scan.txt', 'z-scan.dat')
#-------------------------------------------
file0 = np.loadtxt('z-scan.dat')
file0.shape
#--------------------
date_z   = file0[:,0]
date_E   = file0[:,1] -min(file0[:,1])
#-------------------------------------
z_min    = min(date_z)
z_max    = max(date_z)
E_min    = min(date_E)
E_max    = max(date_E) 
line_min = np.argmin(date_E)
line_max = np.argmax(date_z)
delta_z  = date_z[line_min]
#--------------------------
E_final = date_E[line_max]
Eb = date_E[line_max] -date_E[line_min]
delta_E = abs(Eb)*0.1


#--------------------------------------------------
shutil.copyfile(str(delta_z) + '/POSCAR', 'POSCAR')
shutil.copyfile(str(delta_z) + '/CONTCAR', 'CONTCAR')
#----------------------------------------------------


"""
#=======================================
# Interpolating z-scan data ============
#=======================================
n_d = 250
#--------
f = interp1d(date_z, date_E, kind='cubic')
x_interp = np.linspace(z_min, z_max, n_d)
y_interp = f(x_interp)
"""


#============================================
# Reordering the date_z and date_E lists ====
#============================================
listas_combinadas = list(zip(date_z, date_E))    # Combining the lists
listas_ordenadas = sorted(listas_combinadas)     # Sorting the combined lists based on the elements of the first list
new_date_z, new_date_E = zip(*listas_ordenadas)  # Separating the lists
new_date_z = list(new_date_z)                    # Converting to list format
new_date_E = list(new_date_E)                    # Converting to list format
#============================


#===================================================
# Plot 2D ==========================================
#===================================================
fig, ax = plt.subplots()
plt.plot([delta_z, delta_z], [-1000.0, +1000.0], color = 'red', linestyle = '--', linewidth = 1.0, alpha = 1.0)
plt.plot([-1000.0, +1000.0], [E_min, E_min], color = 'blue', linestyle = '--', linewidth = 1.0, alpha = 1.0)
plt.plot([-1000.0, +1000.0], [E_final, E_final], color = 'blue', linestyle = '--', linewidth = 1.0, alpha = 1.0)
# plt.plot(x_interp, y_interp, color = 'black', linestyle = '-', linewidth = 1.0)
plt.plot(new_date_z, new_date_E, color = 'black', linestyle = '-', linewidth = 1.0)
plt.scatter(date_z, date_E, s=5, color = 'black')
#------------------------------------------------
Eb_meV = (Eb*1000)/Area
Eb_J   = (Eb*1.6021773e-19)/(Area*1e-20)
text   = 'z-scan:  $E_b$ = ' + str(round(Eb_meV, 3)) + ' $meV/{Å^2}$  (' + str(round(Eb_J, 3)) + ' $J/{m^2}$)'
#-------------------------------------------------------------------------------------------------------------
plt.title(text, fontsize=10)
plt.xlim((z_min, z_max))
plt.ylim((E_min -delta_E, E_final +delta_E))
plt.xlabel('${\Delta}$Z(${\AA}$)')
plt.ylabel('$E-E_{min}(eV)$')
ax.set_box_aspect(1.25/1)
#----------------------------------------------------------------------
plt.savefig('z-scan.png', dpi = 600, bbox_inches='tight', pad_inches=0)
# plt.savefig('z-scan.pdf', dpi = 600, bbox_inches='tight', pad_inches=0)
# plt.savefig('z-scan.svg', dpi = 600, bbox_inches='tight', pad_inches=0)
# plt.savefig('z-scan.eps', dpi = 600, bbox_inches='tight', pad_inches=0)


#=====================================================
info = open('info_z-scan.dat', "w", encoding='utf-8')
info.write(f'====================================================== \n')
info.write(f'Displacement carried out over the 2nd material lattice   \n')
info.write(f'Z_Displacement = {delta_z} in Å \n')
info.write(f'------------------------------------------------------ \n')
info.write(f'Eb = {Eb_meV:.12f} meV/Å^2  or  {Eb_J:.12f} J/m^2 \n')
info.write(f'====================================================== \n')
info.close()
#===========
