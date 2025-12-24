# SAMBA_ilum Copyright (C) 2025
# GNU GPL-3.0 license

import numpy as np
import sys
import os
#----------------
import matplotlib
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
#--------------------------------
from scipy.spatial import Voronoi
#--------------------------------



#============================================================
# Extracting the k-path used in the Band Structure plot =====
#============================================================
kpoints_file = []
kpath = []
#-------------------
continue_plot_bz = 0
if os.path.isdir('output/Bandas'):
   dir_kpath = 'bands'
   continue_plot_bz = 1
if os.path.isdir('output/Bandas_SO'):
   dir_kpath = 'bands.SO'
   continue_plot_bz = 1
if (continue_plot_bz == 0): sys.exit()
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
              if (line[3] == 'Gamma' or line[3] == 'gamma' or line[3] == 'G' or line[3] == 'g'): line[3] = '${\\Gamma}$'
              kpath.append([float(line[0]), float(line[1]), float(line[2]), str(line[3])])
    #-------------------------------------------------------------------------------------
    if (len(kpoints_file) > 1):
       for j in range(len(lines)):
           if (i == 0 and j > 3 and len(lines[j]) > 1):
              line = lines[j].split()
              line[3] = line[3].replace('!', '').replace('#1', 'Gamma').replace('#', '')
              kpath.append([float(line[0]), float(line[1]), float(line[2]), str(line[3])])
           if (i > 0  and j > 4 and len(lines[j]) > 1):
              line = lines[j].split()
              line[3] = line[3].replace('!', '').replace('#1', 'Gamma').replace('#', '')
              kpath.append([float(line[0]), float(line[1]), float(line[2]), str(line[3])])
#-----------------------------------------------------------------------------------------
# Removing adjacent and repeated elements from the k-path list
#-------------------------------------------------------------
i = 0
while i < (len(kpath) -1):
    if kpath[i] == kpath[i +1]: del kpath[i +1]
    else: i += 1  # Avança para o próximo par de elementos
#---------------------------------------------------------
kpath_set = []
for sublista in kpath:
    if sublista not in kpath_set:
        kpath_set.append(sublista)
#---------------------------------



#====================================================================
# Extracting information about the Direct and Reciprocal lattices ===
#====================================================================
contcar = open(dir_kpath + '/CONTCAR', "r")
VTemp = contcar.readline().split()
n_materials = len(VTemp[1].replace('+', ' ').split())
t_label = VTemp[-1].replace('_', ' ').split(); label = t_label[0]
VTemp = contcar.readline(); a = float(VTemp)
VTemp = contcar.readline().split(); A1x = float(VTemp[0])*a; A1y = float(VTemp[1])*a; A1z = float(VTemp[2])*a
VTemp = contcar.readline().split(); A2x = float(VTemp[0])*a; A2y = float(VTemp[1])*a; A2z = float(VTemp[2])*a
VTemp = contcar.readline().split(); A3x = float(VTemp[0])*a; A3y = float(VTemp[1])*a; A3z = float(VTemp[2])*a
contcar.close()
#--------------------------------
ss1 = A1x*((A2y*A3z) - (A2z*A3y))
ss2 = A1y*((A2z*A3x) - (A2x*A3z))
ss3 = A1z*((A2x*A3y) - (A2y*A3x))
ss =  ss1 + ss2 + ss3
#-------------------------------
B1x = ((A2y*A3z) - (A2z*A3y))/ss
B1y = ((A2z*A3x) - (A2x*A3z))/ss 
B1z = ((A2x*A3y) - (A2y*A3x))/ss
B2x = ((A3y*A1z) - (A3z*A1y))/ss                             
B2y = ((A3z*A1x) - (A3x*A1z))/ss
B2z = ((A3x*A1y) - (A3y*A1x))/ss
B3x = ((A1y*A2z) - (A1z*A2y))/ss
B3y = ((A1z*A2x) - (A1x*A2z))/ss
B3z = ((A1x*A2y) - (A1y*A2x))/ss
#-------------------------------
ft = 6.2831853071795860
B1 = [B1x*ft, B1y*ft]
B2 = [B2x*ft, B2y*ft]
#--------------------



#==============================================================
# 2D plot of the 1st Brillouin Zone ===========================
#==============================================================
fig, ax = plt.subplots()
#-----------------------

#-------------------------------------------------------------
# Constructing the 2D BZ using Voronoi (Supercell S) ---------
#-------------------------------------------------------------
nx, ny = 6, 6  # Number of points in the grid
points = np.dot(np.mgrid[-nx:nx+1, -ny:ny+1].reshape(2, -1).T, np.array([B1, B2]))
vor = Voronoi(points)
#-------------------------------
# Plotting the 2D Brillouin zone
#--------------------------------
for simplex in vor.ridge_vertices:
    simplex = np.asarray(simplex)
    if np.all(simplex >= 0): ax.plot(vor.vertices[simplex, 0], vor.vertices[simplex, 1], color = 'black', linewidth = 0.25, alpha = 0.5, zorder=4)
#-------------------------------------------------------------------------------------------------------------------------------------------------
plt.quiver(0, 0, B1[0], B1[1], angles='xy', scale_units='xy', scale=1.0, color='blue', alpha = 0.5, zorder=0)
plt.quiver(0, 0, B2[0], B2[1], angles='xy', scale_units='xy', scale=1.0, color='blue', alpha = 0.5, zorder=0)
plt.text(B1[0]*1.0, B1[1]*1.0, "B$_1$", fontsize=10, alpha = 1.0, color="black", zorder=1)
plt.text(B2[0]*1.0, B2[1]*1.0, "B$_2$", fontsize=10, alpha = 1.0, color="black", zorder=1)
#-----------------------------------------------------------------------------------------
for i in range(len(kpath) -1):
    coord_x_1 = (kpath[i][0]*B1[0])   + (kpath[i][1]*B2[0]);   coord_x_1 = float(coord_x_1)
    coord_y_1 = (kpath[i][0]*B1[1])   + (kpath[i][1]*B2[1]);   coord_y_1 = float(coord_y_1)
    coord_x_2 = (kpath[i+1][0]*B1[0]) + (kpath[i+1][1]*B2[0]); coord_x_2 = float(coord_x_2) -coord_x_1
    coord_y_2 = (kpath[i+1][0]*B1[1]) + (kpath[i+1][1]*B2[1]); coord_y_2 = float(coord_y_2) -coord_y_1
    plt.quiver(coord_x_1, coord_y_1, coord_x_2, coord_y_2, angles='xy', scale_units='xy', scale=1.0, color='red', alpha = 0.5, zorder=2)
#---------------------------------------------------------------------------------------------------------------------------------------
initial_colors = ['black', 'red', 'blue', 'green', 'yellow', 'cyan', 'magenta']
all_colors = list(matplotlib.colors.CSS4_COLORS.keys())
remaining_colors = [color for color in all_colors if color not in initial_colors]
color_list = (initial_colors + remaining_colors)[:len(kpath_set)]
#----------------------------------------------------------------
for i in range(len(kpath_set)):
    coord_x = (kpath_set[i][0]*B1[0]) + (kpath_set[i][1]*B2[0])
    coord_y = (kpath_set[i][0]*B1[1]) + (kpath_set[i][1]*B2[1])
    plt.scatter(coord_x, coord_y, c=color_list[i], marker='o', s=30, edgecolor='black', linewidth=0.5, label = str(kpath_set[i][3]), zorder=3)
#---------------------------------------------------------------------------------------------------------------------------------------------
plt.title('1º Brillouin Zone (' + label + ')')
plt.xlabel('kx (' + '${\AA}^{-1}$' + ' )')
plt.ylabel('ky (' + '${\AA}^{-1}$' + ' )')
#-----------------------------------------
x_range = [B1[0], -B1[0], B2[0], -B2[0]]
y_range = [B1[1], -B1[1], B2[1], -B2[1]]
x_min = min(x_range) - abs(min(x_range))*0.1
x_max = max(x_range) + abs(max(x_range))*0.1
y_min = min(y_range) - abs(min(y_range))*0.1
y_max = max(y_range) + abs(max(y_range))*0.1
#--------------------------------------------
plt.xlim((x_min, x_max))
plt.ylim((y_min, y_max))
#----------------------------------------------------
ax.legend(loc = "lower left", title = "", fontsize=8)
ax.set_box_aspect(abs((y_max - y_min) / (x_max - x_min)))
#-------------------------------------------------------------------------------------------------------------------------------
if os.path.isdir('output/Bandas'): plt.savefig('output/Bandas/Brillouin_Zone.png', dpi = 600, bbox_inches='tight', pad_inches=0)
if os.path.isdir('output/Bandas_SO'): plt.savefig('output/Bandas_SO/Brillouin_Zone.png', dpi = 600, bbox_inches='tight', pad_inches=0)
#-------------------------------------------------------------------------------------------------------------------------------------
