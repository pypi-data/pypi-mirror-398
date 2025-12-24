#!/usr/bin/env python3
# Script : extract_pantheon_plus_data.py
# Source des données brutes Pantheon+ SH0ES :
# https://raw.githubusercontent.com/PantheonPlusSH0ES/DataRelease/
#   main/Pantheon+_Data/4_DISTANCES_AND_COVAR/Pantheon+SH0ES.dat

import os

import pandas as pd

# Chemins relatifs depuis ce script
DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../zz-data/chapter08")
)

# Fichier brut Pantheon+SH0ES (sans caractères spéciaux dans le nom)
input_file = os.path.join(DATA_DIR, "pantheon_plus_sh0es.dat")
# Fichier CSV de sortie
output_file = os.path.join(DATA_DIR, "08_pantheon_data.csv")

# 1. Lecture du fichier brut
df = pd.read_csv(input_file, delim_whitespace=True, comment="#")

# 2. Sélection et renommage des colonnes
df_out = df[["zHD", "MU_SH0ES", "MU_SH0ES_ERR_DIAG"]].rename(
    columns={"zHD": "z", "MU_SH0ES": "mu_obs", "MU_SH0ES_ERR_DIAG": "sigma_mu"}
)

# 3. Filtrer la plage 0 ≤ z ≤ 2.3
df_out = df_out[(df_out["z"] >= 0) & (df_out["z"] <= 2.3)]

# 4. Sauvegarde au format CSV UTF-8
df_out.to_csv(output_file, index=False, encoding="utf-8")

print(f"✅ 08_pantheon_data.csv généré dans : {output_file}")
