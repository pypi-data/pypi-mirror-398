# SAMBA_ilum Copyright (C) 2025
# GNU GPL-3.0 license


#-----------------------------
poscar = open(dir_poscar, 'r')
new_potcar = open(dir_potcar, "w")
#-----------------------------------------------------
for m in range(6):  VTemp1 = poscar.readline().split()
poscar.close()
#-------------
label = ''
for m in range(len(VTemp1)):
    label += str(VTemp1[m])
#---------------------------
for m in range(len(VTemp1)):
    potcar = open(dir_pseudo + '/POTCAR_' + str(VTemp1[m]), 'r')
    #-----------------------------------------------------------
    test = 'nao'
    #---------------------
    while (test == 'nao'):     
       #------------------------
       VTemp = potcar.readline()
       new_potcar.write(f'{VTemp}') 
       #---------------------------
       Teste = VTemp.split() 
       #-----------------------------------------
       if (len(Teste) > 0 and Teste[0] == 'End'):
          test = 'sim'
          new_potcar.write(f'\n')
    #=============
    potcar.close() 
new_potcar.close()
#=================