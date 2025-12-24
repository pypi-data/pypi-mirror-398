# SAMBA_ilum Copyright (C) 2025
# GNU GPL-3.0 license

import json
import os

dados_combinados = []

folders = os.listdir()

for i in range(len(folders)):
    if (folders[i] != 'database_union.py'):
       with open(folders[i] + '/info.json') as file:
            file_data = json.load(file)
            dados_combinados.append(file_data)

with open("SAMBA_database.json", "w") as file_output:
    json.dump(dados_combinados, file_output, indent=4)

print(" ")
print("=============================")
print("Merging .json files completed")
print("=============================")
print(" ")
