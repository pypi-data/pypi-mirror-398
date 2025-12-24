# SAMBA_ilum Copyright (C) 2025
# GNU GPL-3.0 license


import os


try:
    path_dir, name_dir = os.path.split(os.getcwd())
except Exception as e:
    pass


#----------------
converged = False
#----------------
try:
    with open('OUTCAR', 'r') as f:
        for line in f:
            if 'reached' in line:
                converged = True
                break
except FileNotFoundError:
    pass
except Exception as e:
    pass


if converged:
    try:
        with open('OSZICAR', 'r') as f:
            last_line = f.readlines()[-1].strip()
            energy_value = last_line.replace('=', ' ').split()[4]
        #--------------------------------------------------------
        with open('../energy_scan.txt', "a") as energy_file:
            energy_file.write(f'{name_dir} {energy_value}\n')
            #---------------------------------------------
            temp_name = name_dir.replace('_', ' ').split()
            #---------------------------------------------
            if len(temp_name) == 2:
                t_temp_name_original = temp_name.copy()
                #---------------------------------------------
                if temp_name[0] == '0.0': temp_name[0] = '1.0'
                if temp_name[1] == '0.0': temp_name[1] = '1.0'
                #---------------------------------------------
                if temp_name[0] == '1.0' or temp_name[1] == '1.0':
                    new_name_dir = f'{temp_name[0]}_{temp_name[1]}'
                    energy_file.write(f'{new_name_dir} {energy_value}\n')
                #------------------------------------------------------------------------
                if t_temp_name_original[0] == '0.0' and t_temp_name_original[1] == '0.0':
                    energy_file.write(f'1.0_0.0 {energy_value}\n')
                    energy_file.write(f'0.0_1.0 {energy_value}\n')
    except FileNotFoundError:
        pass
    except IndexError:
        pass
    except Exception as e:
        pass
