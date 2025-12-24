# SAMBA_ilum Copyright (C) 2025
# GNU GPL-3.0 license


#===========================
poscar = open('POSCAR', 'r')
VTemp = poscar.readline();  VTemp = str(VTemp)
poscar.close()
#=============


#=========================================================
with open('CONTCAR', 'r') as file: line = file.readlines()
line[0] = VTemp
with open('CONTCAR', 'w') as file: file.writelines(line)
#=======================================================


#===========================================================
# Fixing the POSCAR file with Cartesian coordinates ========
#===========================================================
poscar = open('POSCAR', "r")
for i in range(8): VTemp = poscar.readline()
poscar.close()
#------------------
string = str(VTemp)
#-----------------------------
contcar = open('CONTCAR', "r")
poscar = open('POSCAR', "w")
VTemp = contcar.readline();  poscar.write(f'{VTemp}')
VTemp = contcar.readline();  poscar.write(f'{VTemp}');  param = float(VTemp)
VTemp = contcar.readline();  poscar.write(f'{VTemp}');  VTemp = VTemp.split();  A = [float(VTemp[0]), float(VTemp[1]), float(VTemp[2])]  
VTemp = contcar.readline();  poscar.write(f'{VTemp}');  VTemp = VTemp.split();  B = [float(VTemp[0]), float(VTemp[1]), float(VTemp[2])]
VTemp = contcar.readline();  poscar.write(f'{VTemp}');  VTemp = VTemp.split();  C = [float(VTemp[0]), float(VTemp[1]), float(VTemp[2])]
VTemp = contcar.readline();  poscar.write(f'{VTemp}')
VTemp = contcar.readline();  poscar.write(f'{VTemp}')
#----------------------------------------------------
nions = 0;  VTemp = VTemp.split()
for k in range(len(VTemp)): nions += int(VTemp[k])
#---------------------------------------------------------
VTemp = contcar.readline();  poscar.write(f'Cartesian \n')
#---------------------------------------------------------
# Writing Cartesian coordinates --------------------------
#---------------------------------------------------------
for k in range(nions):
    VTemp = contcar.readline().split()
    k1 = float(VTemp[0]); k2 = float(VTemp[1]); k3 = float(VTemp[2])
    coord_x = ((k1*A[0]) + (k2*B[0]) + (k3*C[0]))
    coord_y = ((k1*A[1]) + (k2*B[1]) + (k3*C[1]))
    coord_z = ((k1*A[2]) + (k2*B[2]) + (k3*C[2]))
    poscar.write(f'{coord_x} {coord_y} {coord_z} \n')
#--------------
contcar.close()   
poscar.close()
#-------------
