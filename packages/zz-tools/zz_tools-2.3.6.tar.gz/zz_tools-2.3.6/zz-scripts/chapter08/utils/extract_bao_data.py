#!/usr/bin/env python3
# Script   : extract_bao_data.py
# Objectif : extraire et formater les données BAO pour le Chapitre 8
# Source   : https://raw.githubusercontent.com/SDSS-Science-Archive-Server/BOSS-LSS/
#            master/lss/BAOtables/bao_distances_DR12v5.dat

import os

import pandas as pd

# 1. Définition des chemins
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "../../../zz-data/chapter08"))
os.makedirs(DATA_DIR, exist_ok=True)

input_file = os.path.join(DATA_DIR, "bao_distances_DR12v5.dat")
output_file = os.path.join(DATA_DIR, "08_bao_data.csv")

# 2. Lecture du fichier brut BAO
df = pd.read_csv(input_file, delim_whitespace=True, comment="#")

# 3. Sélection et renommage des colonnes
#    - 'z'        : redshift
#    - 'DV'       : distance de diffusion baryonique
#    - 'sigma_DV' : incertitude absolue de DV
df_out = df[["z", "DV", "sigma_DV"]].rename(
    columns={"DV": "DV_obs", "sigma_DV": "sigma_DV"}
)


# 4. Classification des jalons (primaire / ordre2)
def classify(row):
    frac = row["sigma_DV"] / row["DV_obs"] if row["DV_obs"] != 0 else float("inf")
    return "primaire" if frac <= 0.01 else "ordre2"


df_out["classe"] = df_out.apply(classify, axis=1)

# 5. (Optionnel) Filtrer la plage de redshift
# df_out = df_out[(df_out['z'] >= 0.1) & (df_out['z'] <= 2.5)]

# 6. Sauvegarde au format CSV UTF-8
df_out.to_csv(output_file, index=False, encoding="utf-8")

print(f"✅ 08_bao_data.csv généré dans : {output_file}")
