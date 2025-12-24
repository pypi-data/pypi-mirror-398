# SAMBA_ilum Copyright (C) 2025
# GNU GPL-3.0 license


# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Note: Introduce the original vacuum into the final POSCAR file
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


#-----------------
import numpy as np
import shutil
import os
#--------------------------
import plotly.offline as py
import plotly.graph_objects as go
#--------------------------------
import scipy.interpolate as interp
from scipy.interpolate import griddata
#-------------------------------------
import matplotlib as mpl
from matplotlib import cm
from matplotlib import pyplot as plt
import matplotlib.ticker as ticker
from mpl_toolkits.mplot3d.axes3d import Axes3D
from matplotlib.ticker import LinearLocator, FormatStrFormatter
import matplotlib.patheffects as path_effects
import matplotlib.colors as mcolors
#----------------------------------


n_d = 301    # The xy-scan data will be interpolated to a grid of (n_d x n_d) points


#==============================================================
# Obtaining the area in the XY plane of the Heterostructure ===
#==============================================================
poscar = open('POSCAR.0', 'r')
VTemp = poscar.readline().split()
VTemp = poscar.readline();  param = float(VTemp)
#-----------------------------------------------
A1 = poscar.readline().split();  A1x = float(A1[0])*param; A1y = float(A1[1])*param; A1z = float(A1[2])*param;  mA1 = np.linalg.norm(A1)
A2 = poscar.readline().split();  A2x = float(A2[0])*param; A2y = float(A2[1])*param; A2z = float(A2[2])*param;  mA2 = np.linalg.norm(A2)
A3 = poscar.readline().split();  A3x = float(A3[0])*param; A3y = float(A3[1])*param; A3z = float(A3[2])*param;  mA3 = np.linalg.norm(A3)
#---------------------------------------------------------------------------------------------------------------------------------------
A1 = np.array([A1x, A1y])
A2 = np.array([A2x, A2y])
#--------------------------
# Cell area in the XY plane
#--------------------------
Area = np.linalg.norm(np.cross(A1, A2))
#--------------------------------------
poscar.close()
#-------------


#=========================================================
# Extracting information from the energy_scan.txt file ===
#=========================================================
file0 = np.loadtxt('energy_scan.txt', dtype=str)
file0.shape
#-----------------------
date_shift  = file0[:,0]
date_E   = np.array(file0[:,1],dtype=float)
E_min    = min(date_E)
E_max    = max(date_E)
Delta_E_meV = ((E_max -E_min)*1000)/Area
Delta_E_J   = ((E_max -E_min)*1.6021773e-19)/(Area*1e-20)
line     = np.argmin(date_E)
delta    = date_shift[line]
#------------------------------------------
delta_min = delta.replace('_', ' ').split()
a1_min = float(delta_min[0])
a2_min = float(delta_min[1])
#--------------------------------
if (a1_min == -0.0): a1_min = 0.0
if (a2_min == -0.0): a2_min = 0.0
#--------------------------------


#===============================================
# Creating the energy_scan_shift.txt file ======
#===============================================
file0 = np.loadtxt('energy_scan.txt', dtype=str)
file0.shape
#----------------------
date_shift = file0[:,0]
date_E = np.array(file0[:,1],dtype=float)
#----------------------------------------
file = open('energy_scan_shift.txt', "w")
shift = [-2, -1, 0, +1, +2]
#-------------------------------
for i in range(len(date_shift)):
    #--------------------------------------------------
    shift_temp = date_shift[i].replace('_',' ').split()
    shift_A1 = float(shift_temp[0])
    shift_A2 = float(shift_temp[1])
    #------------------------------
    for j in range(len(shift)):
        for k in range(len(shift)):
            t_shift_A1 = shift_A1 -a1_min +shift[j]
            t_shift_A2 = shift_A2 -a2_min +shift[k]
            if (t_shift_A1 >= -0.2  and t_shift_A1 <= 1.2):
               if (t_shift_A2 >= -0.2  and t_shift_A2 <= 1.2):
                  file.write(f'{t_shift_A1}_{t_shift_A2} {(date_E[i]*1000)/Area} \n')
#-----------
file.close()
#-----------


#===============================================================
# Extracting information from the energy_scan_shift.txt file ===
#===============================================================
file0 = np.loadtxt('energy_scan_shift.txt', dtype=str)
file0.shape
#----------------------
date_shift = file0[:,0]
date_E = np.array(file0[:,1],dtype=float)
#----------------------------------------


#-------------------------------------
file = open('xy-scan_direct.dat', "w")
#-------------------------------------
for i in range(len(date_shift)):
    VTemp = str(date_shift[i])
    VTemp = VTemp.replace('_', ' ')
    file.write(f'{VTemp} {date_E[i]} \n')
#-----------
file.close()
#-----------


#----------------------------------------
file = open('xy-scan_cartesian.dat', "w")
#----------------------------------------
for i in range(len(date_shift)):
    VTemp = str(date_shift[i])
    VTemp = VTemp.replace('_', ' ').split()
    Coord_X = ((float(VTemp[0])*A1x) + (float(VTemp[1])*A2x))
    Coord_Y = ((float(VTemp[0])*A1y) + (float(VTemp[1])*A2y))
    file.write(f'{Coord_X} {Coord_Y} {date_E[i]} \n')
#-----------
file.close()
#-----------


#===================================================
# 3D Plot - Cartesian Coordinates (.html) ==========
#===================================================
label1 = '\u0394' + 'X' + ' (' + '\u212B' + ')'
label2 = '\u0394' + 'Y' + ' (' + '\u212B' + ')'
label3 = 'E-Emin' + ' (meV/' + '\u212B' + '\u00B2' + ')'
#-------------------------------------------------------
file2 = np.loadtxt('xy-scan_cartesian.dat')
file2.shape
#------------------
eixo1c = file2[:,0]
eixo2c = file2[:,1]
eixo3c = file2[:,2]
#---------------------------
# Create meshgrid for (x, y):
x = np.linspace(min(eixo1c), max(eixo1c), n_d)
y = np.linspace(min(eixo2c), max(eixo2c), n_d)
x_grid, y_grid = np.meshgrid(x, y)
# Grid data:
e2_grid = griddata((eixo1c, eixo2c), eixo3c, (x_grid, y_grid), method = 'cubic', fill_value=np.nan)
#--------------------------------------------------------------------------------------------------


#============================================================
# Getting the coordinates of the E_minimum point ============
#============================================================
e2_grid[np.isnan(e2_grid)] = np.inf
min_idx = np.unravel_index(np.argmin(e2_grid), e2_grid.shape)   # Finding the index of the lowest energy value in e_grid
delta_X = x_grid[min_idx]                                       # Finding the corresponding delta_X value
delta_Y = y_grid[min_idx]                                       # Finding the corresponding delta_Y value
E_min   = e2_grid[min_idx]                                      # Finding the corresponding value of E_min
# print(min_idx, delta_X, delta_Y, E_min)
#----------------------------------------
fig = go.Figure()
fig.add_trace(go.Surface(x = x_grid, y = y_grid, z = (e2_grid -E_min), name = 'xy-scan', opacity = 0.8, showscale = False, colorscale='jet'))
fig.update_layout(title = 'xy-scan', scene = dict(xaxis_title = label1, yaxis_title = label2, zaxis_title = label3, aspectmode = 'cube'), margin = dict(r = 20, b = 10, l = 10, t = 10))
fig.update_layout(xaxis_range=[min(eixo1c), max(eixo1c)])
fig.update_layout(yaxis_range=[min(eixo2c), max(eixo2c)])
fig.write_html('xy-scan_3D_cartesian.html')
#------------------------------------------


#===========================================================================
# Obtaining the coordinates of the E_minimum point in direct form ==========
#===========================================================================
a = np.array([A1x, A1y, A1z])
b = np.array([A2x, A2y, A2z])
c = np.array([A3x, A3y, A3z])
T = np.linalg.inv(np.array([a, b, c]).T)     # Defining the transformation matrix
#---------------------------------------
r = np.array([delta_X, delta_Y, 0.0])        # Defining the Cartesian position vector of the atom
#------------------------------------
f = np.dot(T, r)                             # Calculating the corresponding position in fractional coordinates
for m in range(3):
    f = np.where(f < 0, f + 1, f)
    f = np.where(f > 1, f - 1, f)
#--------------------------------
for m in range(3):
    # f[m] = round(f[m], 6)
    if (f[m] > 0.9999 or f[m] < 0.0001):
       f[m] = 0.0
#---------------------
delta_A1 = float(f[0])
delta_A2 = float(f[1])
#---------------------


#=======================================================
# 2D Plot - Cartesian Coordinates (Color Map) ==========
#=======================================================
n_contour = 100
#------------------------------------
mod_x = abs(max(eixo1c) -min(eixo1c))
mod_y = abs(max(eixo2c) -min(eixo2c))
#----------------------------------------------------------------
cmap_gray = (mpl.colors.ListedColormap(['darkgray', 'darkgray']))
#-----------------------
fig, ax = plt.subplots()
cp = plt.contourf(x_grid, y_grid, (e2_grid -E_min), levels = n_contour, cmap = 'jet', alpha = 1.0, antialiased = True)
plt.quiver(0, 0, A1x, A1y, angles='xy', scale_units='xy', scale=1, color='red', label='A$_1$', linewidth=0.1, edgecolor='black')
plt.quiver(0, 0, A2x, A2y, angles='xy', scale_units='xy', scale=1, color='red', label='A$_2$', linewidth=0.1, edgecolor='black')
plt.plot([A1x, (A1x+A2x)], [A1y, (A1y+A2y)], color = 'black', linewidth = 1.0, zorder=3)
plt.plot([A2x, (A1x+A2x)], [A2y, (A1y+A2y)], color = 'black', linewidth = 1.0, zorder=3)
text1 = plt.text((A1x/2), (A1y/2), "A$_1$", fontsize=10, color="red")
text2 = plt.text((A2x/2), (A2y/2), "A$_2$", fontsize=10, color="red")
text1.set_path_effects([path_effects.Stroke(linewidth=0.2, foreground='black'), path_effects.Normal()])
text2.set_path_effects([path_effects.Stroke(linewidth=0.2, foreground='black'), path_effects.Normal()])
cbar = fig.colorbar(cp, orientation = 'vertical', shrink = 1.0)
#-------------------
plt.title('xy-scan')
plt.xlabel('$\Delta$X' + '$\ ({\AA})$')
plt.ylabel('$\Delta$Y' + '$\ ({\AA})$')
cbar.set_label('$E-E_{min}\ $(meV/${\AA^2})$')
#---------------------------------------------
ax.set_box_aspect(mod_y/mod_x)
#-----------------------------------------------------------------------------------
plt.savefig('xy-scan_cartesian.png', dpi = 600, bbox_inches='tight', pad_inches = 0)
# plt.savefig('xy-scan_cartesian.pdf', dpi = 600, bbox_inches='tight', pad_inches = 0)
# plt.savefig('xy-scan_cartesian.eps', dpi = 600, bbox_inches='tight', pad_inches = 0)
# plt.savefig('xy-scan_cartesian.svg', dpi = 600, bbox_inches='tight', pad_inches = 0)
#-------------------------------------------------------------------------------------


#------------------------------------------------
shutil.copyfile(str(delta) + '/POSCAR', 'POSCAR')
shutil.copyfile(str(delta) + '/CONTCAR', 'CONTCAR')
#--------------------------------------------------


#-----------------------------
contcar = open('CONTCAR', "r")
#----------------------------------
line_0 = contcar.readline().split()
if (line_0[-7] == 'Shift_plane'):
   shift_0 = str(line_0[-5])
   shift_0 = shift_0.replace('_', ' ').split()
   #------------------------------------------
   shift_A1 = float(shift_0[0])
   shift_A2 = float(shift_0[1])
   shift_X = (shift_A1*A1x) + (shift_A2*A2x)
   shift_Y = (shift_A1*A1y) + (shift_A2*A2y)
   #----------------------------------------
contcar.close()
#--------------


#=====================================================
info = open('info_xy-scan.dat', "w", encoding='utf-8')
info.write(f'====================================================== \n')
info.write(f'Displacement carried out over the 2nd material lattice   \n')
#------------------------------------------------------------------
info.write(f'Displacement_XY = ({shift_X}, {shift_Y}) in Å \n')
info.write(f'Displacement_XY = ({shift_A1}*A1, {shift_A2}*A2) \n')
#----------------------------------------------------------------
info.write(f'------------------------------------------------------ \n')
info.write(f'ΔE = {Delta_E_meV:.12f} meV/Å^2  or  {Delta_E_J:.12f} J/m^2 \n')
info.write(f'====================================================== \n')
info.close()
#===========
