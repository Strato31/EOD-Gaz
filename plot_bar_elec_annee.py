# Convertir en DataFrame
import pandas as pd
import matplotlib.pyplot as plt
# récupérer automatiquement les données du fichier texte
with open("scenario_energy_stats.txt", "r") as file:
    txt_data = file.read()

# Extraire les données du texte
data = []
for line in txt_data.splitlines():
    if line.startswith("Scénario"):
        scenario = line.split()[1].rstrip(":")
    elif line.strip():
        energy_type, percentage = line.strip().split(":")
        data.append({"Scénario": scenario, "Type d'énergie": energy_type.strip(), "Pourcentage": float(percentage.strip().rstrip("%"))})
df = pd.DataFrame(data)
# Pivot pour le stackplot
pivot_df = df.pivot(index="Scénario", columns="Type d'énergie", values="Pourcentage").fillna(0)
energy_order = ['Nucleaire', 'Gaz', 'Charbon', 'Biomasse', 'Fioul', 'Hydro', 'STEP Pompage', 'STEP Turbinage', 'Batterie Injection', 'Batterie Soutirage']
pivot_df = pivot_df[energy_order]
# Tracer le stackplot
plt.figure(figsize=(10, 6))
pivot_df.plot(kind='bar', stacked=True, figsize=(10, 6), color=['yellow', 'grey', 'black', 'green', 'black', 'blue', 'pink', 'purple', 'orange', 'red'])
plt.legend(loc='upper left')
plt.title("Répartition des types d'énergie par scénario")
plt.xlabel("Scénario")
plt.ylabel("Pourcentage")
plt.show()