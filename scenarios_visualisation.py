import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
import unicodedata
from openpyxl import load_workbook

# --- Configuration et Map ---
energy_type_map = {
    'Nuclear': ['Iconuc1', 'Iconuc2', 'Tabarnuc1', 'Tabarnuc2', 'NucPlusUltra1', 'NucPlusUltra2'],
    'Gaz': ['Gazby', 'Omaïgaz1', 'Omaïgaz2', 'Igaznodon1', 'Igaznodon2', 'Cogénérations', 'Pégaz', 'Samagaz1', 'Samagaz2', 'Gastafiore'],
    'Charbon': ['Coron1', 'Coron2', 'Mockingjay', 'Lantier'],
    'Biomasse': ['Tacotac'],
    'Fioul': ['TicEtTac'],
    'Hydro': ['Hydro'],
    'STEP Pompage': ['STEP_pompage'],
    'STEP Turbinage': ['STEP_turbinage'],
    'Batterie Injection': ['Batt_inj'],
    'Batterie Soutirage': ['Batt_sout'],
    'RES': ['RES'],
    'Charge': ['Load'],
    'Charge Nette': ['Net_load']
}

# --- Fonctions modifiées pour accepter des chemins ---

def merge_weeks(scenario_path, output_csv):
    """Fusionne les fichiers d'un scénario spécifique."""
    files = sorted([f for f in os.listdir(scenario_path) if f.endswith('.csv') and f != 'year.csv'])
    if not files:
        return False
    
    with open(output_csv, 'w', newline='', encoding='utf-8-sig') as year:
        for i, f in enumerate(files):
            file_path = os.path.join(scenario_path, f)
            week_data = pd.read_csv(file_path, sep=';', encoding='utf-8')
            week_data.to_csv(year, index=False, header=(i == 0), sep=',') 
    return True

def agregate_data_by_energy_type(data, energy_type_map, scenario_path):
    aggregated_data = pd.DataFrame()
    aggregated_data['Date'] = data['Date']
    for energy_type, columns in energy_type_map.items():
        # Vérifier si les colonnes existent dans le CSV pour éviter les erreurs
        existing_cols = [c for c in columns if c in data.columns]
        aggregated_data[energy_type] = data[existing_cols].sum(axis=1)
    
    aggregated_data.to_csv(os.path.join(scenario_path, 'aggregated_data.csv'), index=False)
    return aggregated_data

def plot_stackplot_energie(x, data, save_path):
    plt.figure(figsize=(10, 6))
    column_labels = data.columns.tolist()
    
    # Copie pour ne pas modifier l'original pendant les boucles
    df_plot = data.copy()
    for col in column_labels:
        if col in ['STEP Pompage', 'Batterie Soutirage']:
            df_plot[col] = -df_plot[col]

    if len(column_labels) == 14: 
        colors = ['yellow', 'grey', 'black', 'green', 'black', 'blue', 'pink', 'purple', 'orange', 'red']
        plt.stackplot(x, *[df_plot.iloc[:, i] for i in range(1,10)], labels=column_labels[1:10], colors=colors)
    else:
        colors = sns.color_palette("hsv", len(column_labels))
        plt.stackplot(x, *[df_plot.iloc[:, i] for i in range(1, len(column_labels))], labels=column_labels[1:], colors=colors)

    try:
        plt.plot(x, df_plot['Charge Nette'], color='black', label='Charge Nette', ls='--', lw=0.8)
    except:
        pass

    plt.title('Production d\'énergie (quotidien)')
    plt.xlabel('Jours de l\'année')
    plt.ylabel('Puissance (MW)')
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def plot_gaz_stock_with_min_max(data, save_path):
    data['Date'] = pd.to_datetime(data['Date'])
    
    # Charger la capacité (on suppose que le fichier est à la racine du projet)
    excel_wb = load_workbook("Donnees_elec_gaz.xlsx", data_only=True)
    capa_stock = excel_wb["Données_gaz"]["K4"].value

    data['CH4_stock'] = data['CH4_N_stock'] + data['CH4_S_stock']
    daily_min = (data.groupby(data['Date'].dt.date)['CH4_stock'].min())/1000000
    daily_max = (data.groupby(data['Date'].dt.date)['CH4_stock'].max())/1000000
    daily_dates = daily_min.index 

    bounds = pd.read_excel("Donnees_elec_gaz.xlsx", sheet_name="Conso_gaz", usecols="K:L", skiprows=1, nrows=len(daily_dates))
    lower_bound = (bounds.iloc[:, 0]*capa_stock).to_numpy()
    upper_bound = (bounds.iloc[:, 1]*capa_stock).to_numpy()

    plt.figure(figsize=(10, 6))
    plt.fill_between(daily_dates, daily_min, daily_max, color='blue', alpha=0.2, label='Intervalle quotidien (min-max)')
    plt.plot(daily_dates, lower_bound, label='Borne min', color='orange', linestyle='--')
    plt.plot(daily_dates, upper_bound, label='Borne max', color='red', linestyle='--')

    plt.title('Stockage de gaz (TWh)')
    plt.grid(True)
    plt.legend()
    plt.savefig(save_path)
    plt.close()

def group_by_day(data):
    data['Date'] = pd.to_datetime(data['Date'])
    daily_data = data.groupby(data['Date'].dt.date).sum(numeric_only=True)
    daily_data.insert(0, 'Date', daily_data.index)
    return daily_data

# --- BOUCLE PRINCIPALE SUR TOUS LES SCÉNARIOS ---

base_scenarios_dir = './Scenarios'

for i in range(24):  # De 00 à 23
    scenario_id = f"{i:02d}"
    scenario_folder = f"Results_{scenario_id}"
    scenario_path = os.path.join(base_scenarios_dir, scenario_folder)
    
    # Vérifier si le dossier du scénario existe
    if not os.path.exists(scenario_path):
        print(f"Skipping: {scenario_folder} (Dossier non trouvé)")
        continue

    print(f"Traitement du scénario {scenario_id}...")

    # 1. Création du dossier Images_ID à l'intérieur de Results_ID
    image_folder_path = os.path.join(scenario_path, f"Images_{scenario_id}")
    if not os.path.exists(image_folder_path):
        os.makedirs(image_folder_path)

    # 2. Fusion des semaines
    year_csv_path = os.path.join(scenario_path, 'year.csv')
    success = merge_weeks(scenario_path, year_csv_path)
    
    if not success:
        print(f"Pas de fichiers CSV trouvés dans {scenario_folder}")
        continue

    # 3. Chargement et Nettoyage
    results = pd.read_csv(year_csv_path)
    results.columns = results.columns.str.strip()
    results.columns = [unicodedata.normalize('NFC', col) for col in results.columns]

    # 4. Traitement et Visualisations
    # Agrégation
    aggregated_results = agregate_data_by_energy_type(results, energy_type_map, scenario_path)
    
    # Plot Stock Gaz
    gaz_plot_path = os.path.join(image_folder_path, "gaz_stock_with_min_max.png")
    plot_gaz_stock_with_min_max(results, gaz_plot_path)

    # Groupement quotidien et Stackplot
    daily_year = group_by_day(aggregated_results)
    stack_plot_path = os.path.join(image_folder_path, "stackplot_energie_daily.png")
    plot_stackplot_energie(np.arange(len(daily_year)), daily_year, stack_plot_path)

    print(f"Scénario {scenario_id} terminé. Images sauvegardées dans {image_folder_path}")

print("\n--- Tous les scénarios ont été traités ---")