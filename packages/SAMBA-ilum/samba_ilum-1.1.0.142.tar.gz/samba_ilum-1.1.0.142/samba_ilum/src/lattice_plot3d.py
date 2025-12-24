# SAMBA_ilum Copyright (C) 2025
# GNU GPL-3.0 license


from pymatgen.io.vasp import Poscar
from pymatgen.core import Structure
from pymatgen.analysis.structure_matcher import StructureMatcher
#---------------------------------------------------------------
import plotly.graph_objects as go
import numpy as np
import os


Lattice = 'POSCAR'                       # POSCAR file to be read.
type_lattice    = 2                      # [1] 1D Lattices (Periodic in X); [2] 2D Lattices (Periodic in XY); [3] 3D Lattices.
fator_supercell = 3                      # Multiplication factor of the cell present in the "Lattice" file.
fator_r = 0.15                           # Atomic radius multiplication factor.
fator_l = 1.1                            # Multiplication factor to define chemical bonds based on the sum of atomic radii (r1+r2)*factor_l.
f_raio  = 15                             # Scale factor for the radius of each lattice ion.
vetores = 1                              # [0] NO, [1] YES. Plot of the Vectors that define the Cell used.


#==========================================================================
# VESTA Standard: Atomic radii and RGB color for each ion type ============
#==========================================================================
rc_H  = (0.46, 1.20, 0.200, 1.00000, 0.80000, 0.80000)
rc_He = (1.22, 1.40, 1.220, 0.98907, 0.91312, 0.81091)
rc_Li = (1.57, 1.40, 0.590, 0.52731, 0.87953, 0.45670)
rc_Be = (1.12, 1.40, 0.270, 0.37147, 0.84590, 0.48292)
rc_B  = (0.81, 1.40, 0.110, 0.12490, 0.63612, 0.05948)
rc_C  = (0.77, 1.70, 0.150, 0.50430, 0.28659, 0.16236)
rc_N  = (0.74, 1.55, 1.460, 0.69139, 0.72934, 0.90280)
rc_O  = (0.74, 1.52, 1.400, 0.99997, 0.01328, 0.00000)
rc_F  = (0.72, 1.47, 1.330, 0.69139, 0.72934, 0.90280)
rc_Ne = (1.60, 1.54, 1.600, 0.99954, 0.21788, 0.71035)
rc_Na = (1.91, 1.54, 1.020, 0.97955, 0.86618, 0.23787)
rc_Mg = (1.60, 1.54, 0.720, 0.98773, 0.48452, 0.08470)
rc_Al = (1.43, 1.54, 0.390, 0.50718, 0.70056, 0.84062)
rc_Si = (1.18, 2.10, 0.260, 0.10596, 0.23226, 0.98096)
rc_P  = (1.10, 1.80, 0.170, 0.75557, 0.61256, 0.76425)
rc_S  = (1.04, 1.80, 1.840, 1.00000, 0.98071, 0.00000)
rc_Cl = (0.99, 1.75, 1.810, 0.19583, 0.98828, 0.01167)
rc_Ar = (1.92, 1.88, 1.920, 0.81349, 0.99731, 0.77075)
rc_K  = (2.35, 1.88, 1.510, 0.63255, 0.13281, 0.96858)
rc_Ca = (1.97, 1.88, 1.120, 0.35642, 0.58863, 0.74498)
rc_Sc = (1.64, 1.88, 0.745, 0.71209, 0.38930, 0.67279)
rc_Ti = (1.47, 1.88, 0.605, 0.47237, 0.79393, 1.00000)
rc_V  = (1.35, 1.88, 0.580, 0.90000, 0.10000, 0.00000)
rc_Cr = (1.29, 1.88, 0.615, 0.00000, 0.00000, 0.62000)
rc_Mn = (1.37, 1.88, 0.830, 0.66148, 0.03412, 0.62036)
rc_Fe = (1.26, 1.88, 0.780, 0.71051, 0.44662, 0.00136)
rc_Co = (1.25, 1.88, 0.745, 0.00000, 0.00000, 0.68666)
rc_Ni = (1.25, 1.88, 0.690, 0.72032, 0.73631, 0.74339)
rc_Cu = (1.28, 1.88, 0.730, 0.13390, 0.28022, 0.86606)
rc_Zn = (1.37, 1.88, 0.740, 0.56123, 0.56445, 0.50799)
rc_Ga = (1.53, 1.88, 0.620, 0.62292, 0.89293, 0.45486)
rc_Ge = (1.22, 1.88, 0.530, 0.49557, 0.43499, 0.65193)
rc_As = (1.21, 1.85, 0.335, 0.45814, 0.81694, 0.34249)
rc_Se = (1.04, 1.90, 1.980, 0.60420, 0.93874, 0.06122)
rc_Br = (1.14, 1.85, 1.960, 0.49645, 0.19333, 0.01076)
rc_Kr = (1.98, 2.02, 1.980, 0.98102, 0.75805, 0.95413)
rc_Rb = (2.50, 2.02, 1.610, 1.00000, 0.00000, 0.60000)
rc_Sr = (2.15, 2.02, 1.260, 0.00000, 1.00000, 0.15259)
rc_Y  = (1.82, 2.02, 1.019, 0.40259, 0.59739, 0.55813)
rc_Zr = (1.60, 2.02, 0.720, 0.00000, 1.00000, 0.00000)
rc_Nb = (1.47, 2.02, 0.640, 0.29992, 0.70007, 0.46459)
rc_Mo = (1.40, 2.02, 0.590, 0.70584, 0.52602, 0.68925)
rc_Tc = (1.35, 2.02, 0.560, 0.80574, 0.68699, 0.79478)
rc_Ru = (1.34, 2.02, 0.620, 0.81184, 0.72113, 0.68089)
rc_Rh = (1.34, 2.02, 0.665, 0.80748, 0.82205, 0.67068)
rc_Pd = (1.37, 2.02, 0.860, 0.75978, 0.76818, 0.72454)
rc_Ag = (1.44, 2.02, 1.150, 0.72032, 0.73631, 0.74339)
rc_Cd = (1.52, 2.02, 0.950, 0.95145, 0.12102, 0.86354)
rc_In = (1.67, 2.02, 0.800, 0.84378, 0.50401, 0.73483)
rc_Sn = (1.58, 2.02, 0.690, 0.60764, 0.56052, 0.72926)
rc_Sb = (1.41, 2.00, 0.760, 0.84627, 0.51498, 0.31315)
rc_Te = (1.37, 2.06, 2.210, 0.67958, 0.63586, 0.32038)
rc_I  = (1.33, 1.98, 2.200, 0.55914, 0.12200, 0.54453)
rc_Xe = (2.18, 2.16, 0.480, 0.60662, 0.63218, 0.97305)
rc_Cs = (2.72, 2.16, 1.740, 0.05872, 0.99922, 0.72578)
rc_Ba = (2.24, 2.16, 1.420, 0.11835, 0.93959, 0.17565)
rc_La = (1.88, 2.16, 1.160, 0.35340, 0.77057, 0.28737)
rc_Ce = (1.82, 2.16, 0.970, 0.82055, 0.99071, 0.02374)
rc_Pr = (1.82, 2.16, 1.126, 0.99130, 0.88559, 0.02315)
rc_Nd = (1.82, 2.16, 1.109, 0.98701, 0.55560, 0.02744)
rc_Pm = (1.81, 2.16, 1.093, 0.00000, 0.00000, 0.96000)
rc_Sm = (1.81, 2.16, 1.270, 0.99042, 0.02403, 0.49195)
rc_Eu = (2.06, 2.16, 1.066, 0.98367, 0.03078, 0.83615)
rc_Gd = (1.79, 2.16, 1.053, 0.75325, 0.01445, 1.00000)
rc_Tb = (1.77, 2.16, 1.040, 0.44315, 0.01663, 0.99782)
rc_Dy = (1.77, 2.16, 1.027, 0.19390, 0.02374, 0.99071)
rc_Ho = (1.76, 2.16, 1.015, 0.02837, 0.25876, 0.98608)
rc_Er = (1.75, 2.16, 1.004, 0.28688, 0.45071, 0.23043)
rc_Tm = (1.00, 2.16, 0.994, 0.00000, 0.00000, 0.88000)
rc_Yb = (1.94, 2.16, 0.985, 0.15323, 0.99165, 0.95836)
rc_Lu = (1.72, 2.16, 0.977, 0.15097, 0.99391, 0.71032)
rc_Hf = (1.59, 2.16, 0.710, 0.70704, 0.70552, 0.35090)
rc_Ta = (1.47, 2.16, 0.640, 0.71952, 0.60694, 0.33841)
rc_W  = (1.41, 2.16, 0.600, 0.55616, 0.54257, 0.50178)
rc_Re = (1.37, 2.16, 0.530, 0.70294, 0.69401, 0.55789)
rc_Os = (1.35, 2.16, 0.630, 0.78703, 0.69512, 0.47379)
rc_Ir = (1.36, 2.16, 0.625, 0.78975, 0.81033, 0.45049)
rc_Pt = (1.39, 2.16, 0.625, 0.79997, 0.77511, 0.75068)
rc_Au = (1.44, 2.16, 1.370, 0.99628, 0.70149, 0.22106)
rc_Hg = (1.55, 2.16, 1.020, 0.82940, 0.72125, 0.79823)
rc_Tl = (1.71, 2.16, 0.885, 0.58798, 0.53854, 0.42649)
rc_Pb = (1.75, 2.16, 1.190, 0.32386, 0.32592, 0.35729)
rc_Bi = (1.82, 2.16, 1.030, 0.82428, 0.18732, 0.97211)
rc_Po = (1.77, 2.16, 0.940, 0.00000, 0.00000, 1.00000)
rc_At = (0.62, 2.16, 0.620, 0.00000, 0.00000, 1.00000)
rc_Rn = (0.80, 2.16, 0.800, 1.00000, 1.00000, 0.00000)
rc_Fr = (1.00, 2.16, 1.800, 0.00000, 0.00000, 0.00000)
rc_Ra = (2.35, 2.16, 1.480, 0.42959, 0.66659, 0.34786)
rc_Ac = (2.03, 2.16, 1.120, 0.39344, 0.62101, 0.45034)
rc_Th = (1.80, 2.16, 1.050, 0.14893, 0.99596, 0.47106)
rc_Pa = (1.63, 2.16, 0.780, 0.16101, 0.98387, 0.20855)
rc_U  = (1.56, 2.16, 0.730, 0.47774, 0.63362, 0.66714)
rc_Np = (1.56, 2.16, 0.750, 0.30000, 0.30000, 0.30000)
rc_Pu = (1.64, 2.16, 0.860, 0.30000, 0.30000, 0.30000)
rc_Am = (1.73, 2.16, 0.975, 0.30000, 0.30000, 0.30000)


#==================================================
ion_label = []; nlabel = []; label = []; nions = 0
#==================================================


#==========================================================================
# Copying the POSCAR files to the 'output/' directory =====================
#==========================================================================
structure = Poscar.from_file('output/' + Lattice).structure
#-------------------------------------------------------
# Creates a supercell by multiplying the lattice vectors
#-------------------------------------------------------
supercell = structure.copy()
if (type_lattice == 1):  supercell.make_supercell([fator_supercell, 1, 1])
if (type_lattice == 2):  supercell.make_supercell([fator_supercell, fator_supercell, 1])
if (type_lattice == 3):  supercell.make_supercell([fator_supercell, fator_supercell, fator_supercell])
Poscar(supercell).write_file('output/' + 'temp_' + Lattice)


#=======================================
# Reading the "Lattice" file ===========
#=======================================
poscar = open('output/' + Lattice , "r")
#-------------------------------------------
for i in range(2): VTemp = poscar.readline()
param = float(VTemp)
A0 = np.array([0.0, 0.0, 0.0])
A = poscar.readline().split();  A1 = np.array([float(A[0]), float(A[1]), float(A[2])])*param
B = poscar.readline().split();  A2 = np.array([float(B[0]), float(B[1]), float(B[2])])*param
C = poscar.readline().split();  A3 = np.array([float(C[0]), float(C[1]), float(C[2])])*param
#--------------------------------------------------------------------------------------------
poscar.close()
#-------------

#================================================
# Reading the file "temp_Lattice" ===============
#================================================
poscar = open('output/' + 'temp_' + Lattice, "r")
#------------------------------------------------
for i in range(2): VTemp = poscar.readline()
param = float(VTemp)
A0 = np.array([0.0, 0.0, 0.0])
A = poscar.readline().split();  S1 = np.array([float(A[0]), float(A[1]), float(A[2])])*param
B = poscar.readline().split();  S2 = np.array([float(B[0]), float(B[1]), float(B[2])])*param
C = poscar.readline().split();  S3 = np.array([float(C[0]), float(C[1]), float(C[2])])*param
#-------------------------------------------------------------------------------------------
VTemp = poscar.readline().split()
for i in range(len(VTemp)):  
    ion_label.append(str(VTemp[i]))         # Storing the label of each ion in the lattice.      
#----------------------------------
VTemp = poscar.readline().split()
for i in range(len(VTemp)):                         
    nlabel.append(int(VTemp[i]))            # Storing the number of each type of ion in the lattice.
    nions += int(VTemp[i])                  # Getting the total number of ions in the lattice.
    #-------------------------
    for j in range(nlabel[i]):
        label.append(ion_label[i]) 
#----------------------------------------
ion_coord = [[0]*4 for i in range(nions)]   # ion_coord[ni][coord_x, coord_y, coord_z, label]
#----------------------------------------
VTemp = poscar.readline()
#------------------------
for i in range(nions):
   VTemp = poscar.readline().split()
   coord_x = ((float(VTemp[0])*S1[0]) + (float(VTemp[1])*S2[0]) + (float(VTemp[2])*S3[0]))
   coord_y = ((float(VTemp[0])*S1[1]) + (float(VTemp[1])*S2[1]) + (float(VTemp[2])*S3[1]))
   coord_z = ((float(VTemp[0])*S1[2]) + (float(VTemp[1])*S2[2]) + (float(VTemp[2])*S3[2]))
   ion_coord[i][0] = coord_x
   ion_coord[i][1] = coord_y
   ion_coord[i][2] = coord_z
   ion_coord[i][3] = label[i]
#----------------------------
poscar.close()
#-------------



#==========================================
# Starting Plot 3D ========================
#==========================================
fig = go.Figure()
#----------------


#=======================
# Lighting Effects Setup
#=======================
lighting_effects = dict(
    ambient=0.8,    # Ambient light (default: 0.8)
    diffuse=0.8,    # Diffuse reflection (default: 0.8)
    roughness=0.5,  # Roughness (default: 0.5)
    specular=0.5,   # Specular Reflection (default: 0.5)
    fresnel=0.2)    # Fresnel Effect (default: 0.2)


#===========================================
# Adding the atoms within the unit cell ====
#===========================================
n = -1
for i in range(len(ion_label)):
    #--------------------------------------------
    x = []; y = []; z = []; color = []; raio = [] 
    #--------------------------------------------
    for j in range(nlabel[i]):
        #---------------------
        n += 1
        x.append(ion_coord[n][0])
        y.append(ion_coord[n][1])
        z.append(ion_coord[n][2])
        #-----------------------------------------
        cor = globals()['rc_' + str(ion_label[i])]
        color.append('rgb(' + str(int(cor[3]*255)) + ', ' + str(int(cor[4]*255)) + ', ' + str(int(cor[5]*255)) + ')')
        raio.append(cor[0]*f_raio)
    #===================================================================================================================================================================
    fig.add_trace(go.Scatter3d(x=x, y=y, z=z, name=ion_label[i], mode='markers', marker=dict(size=raio, color=color, opacity=1.0, line=dict(color='black', width=1.0))))   


#===================================
# Adding the bonds between atoms ===
#===================================
lines_x = []; lines_y = []; lines_z = []; lines_colors = []
#----------------------------------------------------------
for i in range(nions):
    #--------------------------------------------------------------------------
    vector_ion1 = np.array([ion_coord[i][0], ion_coord[i][1], ion_coord[i][2]])
    label_ion1  = ion_coord[i][3]
    temp_r = globals()['rc_' + str(label_ion1)];  r1 = temp_r[0]
    #-----------------------------------------------------------
    for j in range(nions):
        if (j > i):
           #--------------------------------------------------------------------------
           vector_ion2 = np.array([ion_coord[j][0], ion_coord[j][1], ion_coord[j][2]])
           label_ion2  = ion_coord[j][3]
           temp_r = globals()['rc_' + str(label_ion2)];  r2 = temp_r[0]
           #-----------------------------------------------------------
           dist = np.linalg.norm(vector_ion2 - vector_ion1)
           #-----------------------------------------------
           if (dist <= (r1 + r2)*fator_l):
              #------------------------
              ion_i  = ion_coord[i][3];  ion_j  = ion_coord[j][3]
              cor_i = globals()['rc_' + str(ion_i)];  cor_j = globals()['rc_' + str(ion_j)]
              color_i = 'rgb(' + str(int(cor_i[3]*255)) + ', ' + str(int(cor_i[4]*255)) + ', ' + str(int(cor_i[5]*255)) + ')'
              color_j = 'rgb(' + str(int(cor_j[3]*255)) + ', ' + str(int(cor_j[4]*255)) + ', ' + str(int(cor_j[5]*255)) + ')'
              color_0 = 'rgb(255, 255, 255)'
              #--------------------------------------------------------------------------------------------------------------
              lines_x.extend([vector_ion1[0], vector_ion2[0], None])
              lines_y.extend([vector_ion1[1], vector_ion2[1], None])
              lines_z.extend([vector_ion1[2], vector_ion2[2], None])
              lines_colors.extend([color_i, color_j, color_0])
#----------------------------------------------------------------------------------------------------------------------------------------------
fig.add_trace(go.Scatter3d(x=lines_x, y=lines_y, z=lines_z, name='Bonds', mode='lines', line=dict(color=lines_colors, width=10), opacity=1.0))  


#===================================================================
# Adding the vectors that define the boundaries of the unit cell ===
#===================================================================
lines_x = []; lines_y = []; lines_z = []; lines_colors = []
#----------------------------------------------------------
for i in range(12):
    #--------------
    if (i == 0):
       V1 = A0;     V2 = A1
    if (i == 1):
       V1 = A0;     V2 = A2
    if (i == 2):
       V1 = A0;     V2 = A3
    if (i == 3):
       V1 = A1;     V2 = A1+A2
    if (i == 4):
       V1 = A1;     V2 = A1+A3
    if (i == 5):
       V1 = A2;     V2 = A2+A1
    if (i == 6):
       V1 = A2;     V2 = A2+A3
    if (i == 7):
       V1 = A3;     V2 = A3+A1
    if (i == 8):
       V1 = A3;     V2 = A3+A2
    if (i == 9):
       V1 = A1+A2;  V2 = A1+A2+A3
    if (i == 10):
       V1 = A1+A3;  V2 = A1+A3+A2
    if (i == 11):
       V1 = A2+A3;  V2 = A2+A3+A1
    #-----------------------------------
    lines_x.extend([V1[0], V2[0], None])
    lines_y.extend([V1[1], V2[1], None])
    lines_z.extend([V1[2], V2[2], None])
    if (i < 3):   lines_colors.extend(['red', 'red', 'red'])
    if (i >= 3):  lines_colors.extend(['black', 'black', 'black'])
#------------------------------------------------------------------------------------------------------------------------------ 
fig.add_trace(go.Scatter3d(x=lines_x, y=lines_y, z=lines_z, name='Cell', mode='lines', line=dict(color=lines_colors, width=2)))
fig.add_trace(go.Scatter3d(x=lines_x, y=lines_y, z=lines_z, name='', mode='lines', line=dict(color='black', width=2), opacity=0.0)) # showlegend=False


#=================================
# Finalizing the 3D Plot setup ===
#=================================
fig.update_scenes(xaxis_visible=False, yaxis_visible=False, zaxis_visible=False, camera_projection_type='orthographic')
#----------------------------------------------------------------------------------------------------------------------
fig.update_layout(scene=dict(xaxis_title='', yaxis_title='', zaxis_title='',
    xaxis=dict(showticklabels=False, showgrid=False),
    yaxis=dict(showticklabels=False, showgrid=False),
    zaxis=dict(showticklabels=False, showgrid=False),
    aspectmode='data',
    camera=dict(up=dict(x=0, y=0, z=1), center=dict(x=0, y=0, z=0), eye=dict(x=1, y=1, z=0.5))))
#-----------------------------------------------------------------------------------------------
fig.write_html('output/' + 'Lattice_Plot3D.html')
# fig.write_json('output/' + 'Lattice_Plot3D.json')
#--------------------------------------------------
# fig.show()

os.remove('output/' + 'temp_' + Lattice)
