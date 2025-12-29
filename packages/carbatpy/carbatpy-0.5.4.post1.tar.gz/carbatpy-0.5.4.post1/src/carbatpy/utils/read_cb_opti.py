# -*- coding: utf-8 -*-
"""
Script to read the content of a Carnot Battery Optimization directory

and do the CB calcultions with the optimal results and plot them.

Created on Fri Aug  8 16:07:33 2025

@author: atakan
Universität Duisburg-Essen, Germany

In the framework of the Priority Programme: "Carnot Batteries: Inverse Design from
Markets to Molecules" (SPP 2403)
https://www.uni-due.de/spp2403/
https://git.uni-due.de/spp-2403/residuals_weather_storage

"""

import numpy as np
import pandas as pd
import carbatpy as cb
from pathlib import Path
import yaml
import pickle

# === EINSTELLUNGEN ===
# Replace the results directory with the one wanted:
RES_DIR = Path(r"C:\Users\atakan\sciebo\results\2025-08-08-17-07-cb_opt_result")  # Ordner vom ersten Skript
CSV_FILE = list(RES_DIR.glob("*cb_opti_res.csv"))[0]  # nimmt automatisch die einzige CSV
YAML_FILE = RES_DIR / "config_bound.yaml"

PLOT = True        # Plots speichern?
ALL_POP = False    # True = alle Zeilen aus CSV berechnen, False = nur beste Lösung

# === DATEIEN LADEN ===
with open(YAML_FILE, "r") as f:
    yaml_data = yaml.safe_load(f)

configs_m = yaml_data["configs"]
bounds_m = yaml_data["bounds"]
POWER_C = yaml_data["power_compressor"]


# io-Dateien
dir_names_both = {
    "hp": str(RES_DIR / "io-cycle-data.yaml"),
    "orc": str(RES_DIR / "io-orc-data.yaml"),
}


# === Zuerst versuchen, saved paths zu laden ===
paths_file = RES_DIR / "paths.pkl"
if paths_file.exists():
    with open(paths_file, "rb") as pf:
        paths = pickle.load(pf)
    print("Loaded 'paths' from paths.pkl")
else:
    # Fallback: selbst erzeugen (verwende Deine Funktion)
    print("No 'paths.pkl' found — reconstructing paths from config/bounds (best-effort).")
    paths = {}
    for k in ["hp", "orc"]:
        _, _, p_list = cb.opti_cycle_comp_helpers.extract_optim_data_with_paths(configs_m[k], bounds_m[k])
        paths[k] = p_list

# === CSV lesen (Index-Spalte ausschließen) ===
df = pd.read_csv(CSV_FILE, index_col=0)  # falls Optimierer index=False nimmt, ist das auch ok
energy_col = df.columns[-1]
x_cols = df.columns[:-1].tolist()

# === Sanity-check: Anzahl x in paths vs CSV ===
expected_len = sum(len(paths[k]) for k in ("hp", "orc"))
if expected_len != len(x_cols):
    raise RuntimeError(
        f"Mismatch between expected number of x-variables ({expected_len}) from 'paths' and CSV columns ({len(x_cols)}). "
        f"CSV columns (first 12): {x_cols[:12]}. Save 'paths.pkl' during optimization or check CSV writing."
    )
print(f"OK: expected_len={expected_len}, csv_x_cols={len(x_cols)}")

# === calc-Funktion ===
def calc_from_row(row, idx):
    x_vals = row[x_cols].values.astype(float)
    co_n = cb.opti_cycle_comp_helpers.extract_cb_conf_from_x(x_vals, configs_m, paths)
    rte, res_ = cb.cb_comp.cb_calc(dir_names_both, POWER_C, config=co_n, plotting=PLOT)
    if PLOT:
        for key in res_:
            file_fig = RES_DIR / f"recalc_{idx}_{key}.png"
            res_[key]["figure"].savefig(file_fig)
    return rte

# === Auswahl ===
if ALL_POP:
    results = []
    for i, row in df.iterrows():
        rte_val = calc_from_row(row, i)
        results.append((i, rte_val))
    print("Alle Ergebnisse neu berechnet:", results)
else:
    best_idx = df[energy_col].idxmin()
    rte_val = calc_from_row(df.loc[best_idx], best_idx)
    print(f"Beste Lösung neu berechnet (Index {best_idx}): RTE = {rte_val}")
