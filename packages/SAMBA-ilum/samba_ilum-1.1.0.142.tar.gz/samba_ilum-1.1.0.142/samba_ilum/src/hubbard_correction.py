# SAMBA_ilum Copyright (C) 2025
# GNU GPL-3.0 license


import sys
import os


with open(dir_poscar_file + '/POSCAR', "r") as file: lines = file.readlines()
elements  = lines[5].split()

#------------------------------------------------------
exec(open(dir_inputs + '/Hubbard_U_values.txt').read())
#------------------------------------------------------

lmaxmix = 2
if any(LDAUL_VALORES.get(el, -1) == 2 for el in elements): lmaxmix = 3  # d-orbitals
if any(LDAUL_VALORES.get(el, -1) == 3 for el in elements): lmaxmix = 4  # f-orbitals

#============================================
# LDA+U/GGA+U Configuration =================
#============================================
LDAU = ".TRUE."
LDAUTYPE = "2"
LDAUL = " ".join(str(LDAUL_VALORES.get(el, -1)) for el in elements )
LDAUU = " ".join(str(U_VALORES.get(el, 0.0)) for el in elements )
LDAUJ = " ".join("0.0" for _ in elements )
LDAUPRINT = "1"

#============================================
# Updating INCAR file =======================
#============================================
with open(dir_poscar_file + '/INCAR', "a") as output_file:
    output_file.write(f" \n")
    output_file.write(f"# GGA+U =================\n")
    output_file.write(f"LDAU = {LDAU}\n")
    output_file.write(f"LMAXMIX = 4\n")
    output_file.write(f"LDAUTYPE = {LDAUTYPE}\n")
    output_file.write(f"LDAUL = {LDAUL}\n")
    output_file.write(f"LDAUU = {LDAUU}\n")
    output_file.write(f"LDAUJ = {LDAUJ}\n")
    output_file.write(f"LDAUPRINT = {LDAUPRINT}\n")
    output_file.write(f"# =======================\n")
