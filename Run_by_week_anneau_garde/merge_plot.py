import os
import pandas as pd
import matplotlib.pyplot as plt

RESULTS_DIR = "Results"
OUTPUT_FILE = "results_yearly_hourly.csv"

def read_week_file(path):
    """
    Retourne :
    - df_hourly : DataFrame des pas horaires
    - state : dict des états de fin de semaine
    """
    with open(path, "r") as f:
        lines = f.readlines()

    split_idx = None
    for i, line in enumerate(lines):
        if line.strip() == "#STATE_END":
            split_idx = i
            break

    if split_idx is None:
        raise ValueError(f"#STATE_END manquant dans {path}")

    # ----- Hourly part -----
    header = lines[0].strip().split(";")
    header = [h.strip() for h in header if h.strip()]

    data_lines = lines[1:split_idx]
    rows = []
    for l in data_lines:
        vals = [v.strip() for v in l.split(";") if v.strip()]
        rows.append(vals)

    df_hourly = pd.DataFrame(rows, columns=header)
    df_hourly["Date"] = pd.to_datetime(df_hourly["Date"])

    # ----- State part -----
    state = {}
    for l in lines[split_idx+1:]:
        if ";" in l:
            k, v = l.strip().split(";")
            state[k] = float(v)

    return df_hourly, state


# ==========================
# Lecture des csv results
# ==========================
files = sorted(
    f for f in os.listdir(RESULTS_DIR)
    if f.startswith("result_S") and f.endswith(".csv")
)

all_dfs = []
states = []

for f in files:
    path = os.path.join(RESULTS_DIR, f)
    
    # Extraire le numéro de semaine depuis le nom du fichier
    # Ex: "result_S12.csv" -> 12
    week_num = int(f.split("S")[1].split(".")[0])
    
    df, state = read_week_file(path)
    
    # Ajouter la colonne "Week"
    df["Week"] = week_num
    
    all_dfs.append(df)
    states.append(state)

# Merge annuel
df_year = pd.concat(all_dfs, ignore_index=True)
df_year = df_year.sort_values("Date")
df_year.to_csv(OUTPUT_FILE, index=False, sep=";")

print(f"\n📁 Fichier annuel créé : {OUTPUT_FILE}")
print(f"⏱️ Nombre d'heures : {len(df_year)}")


# ==========================
# Vérification des durées minimales de fonctionnement
# ==========================

# Forcer UTF-8
df = pd.read_csv("results_yearly_hourly.csv", sep=";", encoding="utf-8")

df["Date"] = pd.to_datetime(df["Date"])
df = df.set_index("Date")
# Nettoyer les colonnes du CSV
df.columns = [c.strip() for c in df.columns]



print(df.columns)

data_file = "Donnees_elec_gaz.xlsx"
# Thermal units
Nth=22
dmin = pd.read_excel(data_file, sheet_name="Parc_elec", usecols="G", skiprows=1, nrows=22).to_numpy().flatten()

# CH4 units
N_CH4 = 2
dmin_CH4_S = pd.read_excel(data_file, sheet_name="Données_gaz", usecols="J", skiprows=13, nrows=2).to_numpy().flatten()
dmin_CH4_N = pd.read_excel(data_file, sheet_name="Données_gaz", usecols="J", skiprows=15, nrows=2).to_numpy().flatten()

# H2 units
dmin_H2_S = pd.read_excel(data_file, sheet_name="Données_gaz", usecols="J", skiprows=35, nrows=1).to_numpy().flatten()[0]
dmin_H2_N = pd.read_excel(data_file, sheet_name="Données_gaz", usecols="J", skiprows=36, nrows=1).to_numpy().flatten()[0]


violations_all = []

# Thermal units
# Noms des centrales thermiques
Nth = 22
th_names = pd.read_excel(data_file, sheet_name="Parc_elec", usecols="A", skiprows=1, nrows=Nth).to_numpy().flatten()

# Nettoyer les noms des unités depuis Excel
th_names = [str(n).strip() for n in th_names]
def check_dmin_sequence(series, dmin, unit_name):
    """
    Vérifie que toutes les séquences consécutives de valeurs non nulles
    dans `series` sont d'une longueur >= dmin.
    
    series : pd.Series de valeurs (MW, MWh, etc.)
    dmin   : durée minimale (en pas de temps, ex : heures)
    unit_name : nom de l'unité pour l'affichage
    
    Retourne une liste de violations
    """
    violations = []
    values = series.fillna(0).values  # remplacer NaN par 0
    times = series.index

    start = None  # début d'une séquence non nulle

    for i, v in enumerate(values):
        if v != 0:
            if start is None:
                start = i  # début d'une nouvelle séquence
        else:
            if start is not None:
                duration = i - start
                if duration < dmin:
                    violations.append({
                        "unit": unit_name,
                        "start": times[start],
                        "end": times[i-1],
                        "duration": duration,
                        "dmin": dmin
                    })
                start = None

    # dernière séquence si elle se termine à la fin de la série
    if start is not None:
        duration = len(values) - start
        if duration < dmin:
            violations.append({
                "unit": unit_name,
                "start": times[start],
                "end": times[-1],
                "duration": duration,
                "dmin": dmin
            })

    return violations
violations_all = []

# Thermal units
for g, uc_name in enumerate(th_names, start=1):
    dmin_g = dmin[g-1]
    if dmin_g <= 1:
        continue
    if uc_name not in df.columns:
        print(f"⚠️ Colonne manquante dans le CSV : {uc_name}")
        continue
    v = check_dmin_sequence(df[uc_name], dmin_g, f"Thermal_{g}")
    violations_all.extend(v)

"""# CH4 units
for g in range(1, N_CH4+1):
    vS = check_dmin_sequence(df[f"UC_CH4_S_{g}"], dmin_CH4_S[g-1], f"CH4_S_{g}")
    vN = check_dmin_sequence(df[f"UC_CH4_N_{g}"], dmin_CH4_N[g-1], f"CH4_N_{g}")
    violations_all.extend(vS + vN)

# H2 units
violations_all.extend(check_dmin_sequence(df["UC_H2_S"], dmin_H2_S, "H2_S"))
violations_all.extend(check_dmin_sequence(df["UC_H2_N"], dmin_H2_N, "H2_N"))
"""
# Affichage
if violations_all:
    print("⚠️ VIOLATIONS DES DURÉES MINIMALES DÉTECTÉES\n")
    for v in violations_all:
        print(
            f"{v['unit']} | {v['start']} → {v['end']} | "
            f"durée={v['duration']} < dmin={v['dmin']}"
        )
else:
    print("✅ Toutes les durées minimales sont respectées")


# ==========================
# Fusion annuelle
# ==========================
df_year = pd.concat(all_dfs, ignore_index=True)
df_year = df_year.sort_values("Date")
df_year.to_csv(OUTPUT_FILE, index=False, sep=";")

print(f"\n📁 Fichier annuel créé : {OUTPUT_FILE}")
print(f"⏱️ Nombre d'heures : {len(df_year)}")
