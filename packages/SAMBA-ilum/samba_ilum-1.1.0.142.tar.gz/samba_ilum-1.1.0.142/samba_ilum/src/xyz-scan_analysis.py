# SAMBA_ilum Copyright (C) 2025
# GNU GPL-3.0 license


# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Note: Introduce the original vacuum into the final POSCAR file
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


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
import matplotlib.colors as mcolors


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
file0 = np.loadtxt('energy_scan.txt', dtype=str)
file0.shape
#----------------------
date_shift = file0[:,0]
date_E = np.array(file0[:,1],dtype=float)
E_min  = min(date_E)
E_max  = max(date_E)
delta  = date_shift[np.argmin(date_E)]
#------------------------------------------
delta_min = delta.replace('_', ' ').split()
a1_min = delta_min[0]; a2_min = delta_min[1]; z_min = delta_min[2] 
#-----------------------------------------------------------------


#------------------------------------------------
shutil.copyfile(str(delta) + '/POSCAR', 'POSCAR')
shutil.copyfile(str(delta) + '/CONTCAR', 'CONTCAR')
exec(open('contcar_update.py').read())
#--------------------------------------------------


"""
#--------------------------------------
file = open('xyz-scan_direct.dat', "w")
#--------------------------------------
for i in range(len(date_shift)):
    VTemp = str(date_shift[i])
    VTemp = VTemp.replace('_', ' ')
    file.write(f'{VTemp} {((date_E[i] -E_min)*1000)/Area} \n')
#-----------
file.close()
#-----------


#-----------------------------------------
file = open('xyz-scan_cartesian.dat', "w")
#-----------------------------------------
for i in range(len(date_shift)):
    VTemp = str(date_shift[i])
    VTemp = VTemp.replace('_', ' ').split()
    Coord_X = ((float(VTemp[0])*A1x) + (float(VTemp[1])*A2x))
    Coord_Y = ((float(VTemp[0])*A1y) + (float(VTemp[1])*A2y))
    file.write(f'{Coord_X} {Coord_Y} {((date_E[i] -E_min)*1000)/Area} \n')
#-----------
file.close()
#-----------
"""


#=====================================================
info = open('info_xyz-scan.dat', "w", encoding='utf-8')
info.write(f'====================================================== \n')
info.write(f'Displacement carried out over the 2nd material lattice   \n')
info.write(f'XY_Displacement = ({a1_min}*A1, {a2_min}*A2) \n')
info.write(f'Z_Displacement = {z_min} Å \n')
# info.write(f'------------------------------------------------------ \n')
# info.write(f'ΔE = {Delta_E_meV:.12f} meV/Å^2  or  {Delta_E_J:.12f} J/m^2 \n')
info.write(f'====================================================== \n')
info.close()
#===========
