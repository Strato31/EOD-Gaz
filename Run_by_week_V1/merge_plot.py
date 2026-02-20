import pandas as pd
import numpy as np
import os

# ==========================
# FUSION DES FICHIERS RÉSULTATS
# ==========================

RESULTS_DIR = "Results"  # Le dossier où Julia enregistre les CSV
all_files = [f for f in os.listdir(RESULTS_DIR) if f.startswith("result_S") and f.endswith(".csv")]

# Tri naturel pour s'assurer que S10 ne vient pas avant S2 (tri par numéro de semaine)
all_files.sort(key=lambda x: int(x.replace("result_S", "").replace(".csv", "")))

print(f"📂 Fusion de {len(all_files)} fichiers trouvés dans {RESULTS_DIR}...")

list_df = []
for filename in all_files:
    path = os.path.join(RESULTS_DIR, filename)
    # On lit chaque fichier (attention au séparateur ";" utilisé dans ton code Julia)
    temp_df = pd.read_csv(path, sep=";", encoding="utf-8")
    list_df.append(temp_df)

# On concatène tout le monde
df = pd.concat(list_df, ignore_index=True)

# Nettoyage des colonnes (espaces blancs)
df.columns = [c.strip() for c in df.columns]

# Conversion des dates et tri chronologique
df["Date"] = pd.to_datetime(df["Date"])
df = df.sort_values("Date").set_index("Date")

# Optionnel : Sauvegarde du fichier global pour ton usage futur
df.to_csv("results_yearly_hourly.csv", sep=";")
# ==========================
# PARAMÈTRES
# ==========================

RESULT_FILE = "results_yearly_hourly.csv"
DATA_FILE = "Donnees_elec_gaz.xlsx"

EPS = 1e-6   # tolérance numérique (pour éviter les 1e-13)

# ==========================
# LECTURE DES DONNÉES
# ==========================

df = pd.read_csv(RESULT_FILE, sep=";", encoding="utf-8")
df.columns = [c.strip() for c in df.columns]

df["Date"] = pd.to_datetime(df["Date"])
df = df.set_index("Date").sort_index()

# ==========================
# CHARGEMENT DES dmin
# ==========================

# Thermique
Nth = 22
th_names = pd.read_excel(
    DATA_FILE, sheet_name="Parc_elec",
    usecols="A", skiprows=1, nrows=Nth
).iloc[:, 0].astype(str).str.strip().tolist()

dmin_th = pd.read_excel(
    DATA_FILE, sheet_name="Parc_elec",
    usecols="G", skiprows=1, nrows=Nth
).iloc[:, 0].to_numpy()

# CH4
N_CH4 = 2
dmin_CH4_S = [168,1]

dmin_CH4_N = [168,168]
print(dmin_CH4_N)

# H2
dmin_H2_S = 1

dmin_H2_N = 168

# ==========================
# FONCTION DE TEST dmin
# ==========================
def check_min_up_time(series, dmin, unit_name):
    """
    Vérifie que chaque séquence de production > 0
    dure au moins dmin heures.
    """
    violations = []

    prod = series.fillna(0).values
    times = series.index
    n = len(prod)

    t = 0
    while t < n:
        if prod[t] > EPS:
            start = t
            while t < n and prod[t] > EPS:
                t += 1
            duration = t - start

            if duration < dmin:
                start_time = times[start]
                end_time = times[t-1]

                violations.append({
                    "unit": unit_name,
                    "week": start_time.isocalendar().week,
                    "start": start_time,
                    "end": end_time,
                    "duration": duration,
                    "dmin": dmin
                })
        else:
            t += 1

    return violations


# ==========================
# TEST DES MOYENS
# ==========================

violations = []

# --- Thermiques ---
for i, name in enumerate(th_names):
    if name not in df.columns:
        print(f"⚠️ Colonne manquante : {name}")
        continue

    if dmin_th[i] <= 1:
        continue

    violations += check_min_up_time(
        df[name],
        int(dmin_th[i]),
        f"Thermal_{name}"
    )

# --- CH4 ---
for g in range(1, N_CH4 + 1):
    violations += check_min_up_time(
        df[f"CH4_S_prod_{g}"],
        int(dmin_CH4_S[g-1]),
        f"CH4_S_{g}"
    )

    violations += check_min_up_time(
        df[f"CH4_N_prod_{g}"],
        int(dmin_CH4_N[g-1]),
        f"CH4_N_{g}"
    )

# --- H2 ---
violations += check_min_up_time(
    df["H2_S_prod"],
    int(dmin_H2_S),
    "H2_S"
)

violations += check_min_up_time(
    df["H2_N_prod"],
    int(dmin_H2_N),
    "H2_N"
)

# ==========================
# AFFICHAGE DES RÉSULTATS
# ==========================

if violations:
    print("\n⚠️ VIOLATIONS DES DURÉES MINIMALES DE PRODUCTION\n")
    for v in violations:
        print(
            f"Semaine {v['week']:02d} | "
            f"{v['unit']} | "
            f"{v['start']} → {v['end']} | "
            f"durée={v['duration']} < dmin={v['dmin']}"
        )
else:
    print("\n✅ Toutes les durées minimales de fonctionnement sont respectées")
