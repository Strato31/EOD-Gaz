import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
import unicodedata
from openpyxl import load_workbook

# --- Configuration et Map ---
energy_type_map = {
    'Nucleaire': ['Iconuc1', 'Iconuc2', 'Tabarnuc1', 'Tabarnuc2', 'NucPlusUltra1', 'NucPlusUltra2'],
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
    'Charge Nette': ['Net_load']
}

# --- Fonctions modifiées pour accepter des chemins ---

def merge_weeks(scenario_path, output_csv):
    """Fusionne uniquement les fichiers hebdomadaires valides."""
    # On ne prend que les fichiers commençant par 'result_S' pour éviter les fichiers agrégés
    files = sorted([f for f in os.listdir(scenario_path) 
                    if f.startswith('result_S') and f.endswith('.csv')])
    
    if not files:
        return False
    
    with open(output_csv, 'w', newline='', encoding='utf-8-sig') as year:
        for i, f in enumerate(files):
            file_path = os.path.join(scenario_path, f)
            # Lecture du fichier de la semaine (séparateur point-virgule)
            week_data = pd.read_csv(file_path, sep=';', encoding='utf-8')
            
            # Écriture dans le fichier annuel (séparateur virgule)
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

def plot_stackplot_energie(x, data, save_path, freq='Daily'):
    plt.figure(figsize=(10, 6))
    column_labels = data.columns.tolist()
    
    # Copie pour ne pas modifier l'original pendant les boucles
    df_plot = data.copy()
    for col in column_labels:
        if col in ['STEP Pompage', 'Batterie Soutirage']:
            df_plot[col] = -df_plot[col]

    if len(column_labels) <= 20: 
        colors = ['yellow', 'grey', 'black', 'green', 'black', 'blue', 'pink', 'purple', 'orange', 'red']
        plt.stackplot(x, *[df_plot.iloc[:, i] for i in range(1,10)], labels=column_labels[1:10], colors=colors)
    else:
        colors = sns.color_palette("hsv", len(column_labels))
        plt.stackplot(x, *[df_plot.iloc[:, i] for i in range(1, len(column_labels))], labels=column_labels[1:], colors=colors)

    try:
        plt.plot(x, df_plot['Charge Nette'], color='black', label='Charge Nette', ls='--', lw=0.8)
    except:
        pass
    if freq == 'Daily':
        plt.title('Production d\'énergie (quotidien)')
        plt.xlabel('Jours de l\'année')
    elif freq == 'Weekly':
        plt.title('Production d\'énergie (hebdomadaire)')
        plt.xlabel('Semaines de l\'année')
        
    plt.ylabel('Puissance (MW)')
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def plot_stackplot_week_hourly(data, week_number, save_path):
    """Affiche le stackplot électrique heure par heure pour une semaine donnée."""
    df_hourly = data.copy()
    df_hourly['Date'] = pd.to_datetime(df_hourly['Date'])
    
    # Filtrage de la semaine
    target_week = df_hourly[df_hourly['Date'].dt.isocalendar().week == week_number].copy()
    
    if target_week.empty:
        return

    column_labels = target_week.columns.tolist()
    # Correction pour éviter le Warning "SettingWithCopy"
    for col in column_labels:
        if col in ['STEP Pompage', 'Batterie Soutirage']:
            target_week.loc[:, col] = -target_week[col]

    plt.figure(figsize=(12, 7))
    x = np.arange(len(target_week))
    
    if len(column_labels) <= 20:
        colors = ['yellow', 'grey', 'black', 'green', 'black', 'blue', 'pink', 'purple', 'orange', 'red']
        plt.stackplot(x, *[target_week.iloc[:, i] for i in range(1, 10)], 
                      labels=column_labels[1:10], colors=colors)
    else:
        colors = sns.color_palette("hsv", len(column_labels))
        plt.stackplot(x, *[target_week.iloc[:, i] for i in range(1, len(column_labels))], 
                      labels=column_labels[1:], colors=colors)

    if 'Charge Nette' in target_week.columns:
        plt.plot(x, target_week['Charge Nette'], color='black', label='Charge Nette', ls='--', lw=1)

    plt.title(f'Équilibre Électrique Horaire - Semaine {week_number}')
    plt.xlabel('Heures de la semaine')
    plt.ylabel('Puissance (MW)')
    
    # --- CORRECTION ICI ---
    # On génère 7 points (le début de chaque jour)
    ticks = np.arange(0, 7 * 24, 24) 
    days = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
    plt.xticks(ticks, days)
    # -----------------------

    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.grid(axis='x', linestyle=':', alpha=0.5)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def plot_elec_gaz(x, data, save_path):
    """Plot les courbes élec juste gaz."""
    gaz_elec_data = data[["Gazby","Omaïgaz1","Omaïgaz2","Igaznodon1","Igaznodon2","Cogénérations","Pégaz","Samagaz1","Samagaz2","Gastafiore"]]
    plt.figure(figsize=(10, 6))
    plt.stackplot(x, *[gaz_elec_data.iloc[:, i] for i in range(gaz_elec_data.shape[1])], labels=gaz_elec_data.columns)
    plt.title('Production d\'électricité à partir de gaz')
    plt.xlabel('Semaine')
    plt.ylabel('Puissance (MW)')
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def plot_stackplot_ch4(x, data, save_path):
    """Plot des productions de CH4 (Méthanisation, Pyro, GNL)."""
    # Sélection des colonnes spécifiques au CH4
    ch4_cols = ['CH4_S_prod_1', 'CH4_N_prod_1', 'CH4_N_prod_2', 'CH4_S_prod_2']
    ch4_prod_data = data[ch4_cols]
    ch4_labels = ['Méthanisation Sud', 'Méthanisation Nord', 'Pyrogazeification', 'GNL']
    
    plt.figure(figsize=(10, 6))
    plt.stackplot(x, *[ch4_prod_data.iloc[:, i] for i in range(ch4_prod_data.shape[1])], 
                  labels=ch4_labels, 
                  colors=['red', 'orange', 'yellow', 'green'])
    plt.ylim(0, 600000)
    # Seuil de production maximale
    valeur_seuil = 350000
    plt.axhline(y=valeur_seuil, color='red', linestyle='--', linewidth=1.5, label='Production maximale')
    
    plt.title('Production de Méthane (CH4)')
    plt.xlabel('Date')
    plt.ylabel('Puissance (MW)')
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def plot_stackplot_h2(x, data, save_path):
    """Plot des productions d'Hydrogène (Electrolyse, Pyroreformage)."""
    # Sélection des colonnes spécifiques à l'H2
    h2_cols = ['H2_S_prod', 'H2_N_prod']
    h2_prod_data = data[h2_cols]
    h2_labels = ['Electrolyse (H2)', 'Pyroreformage (H2)']
    
    plt.figure(figsize=(10, 6))
    plt.stackplot(x, *[h2_prod_data.iloc[:, i] for i in range(h2_prod_data.shape[1])], 
                  labels=h2_labels, 
                  colors=['pink', 'blue'])
    
    plt.title("Production d'Hydrogène (H2)")
    plt.xlabel('Date')
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

def plot_flux_ch4(x, data, save_path):
    """Plot flux CH4 avec zones colorées pour identifier l'importateur."""
    plt.figure(figsize=(10, 6))
    
    # Récupération de la série de données
    flux_values = data['CH4_flux_S_N']
    
    # On trace la courbe principale
    plt.plot(x, flux_values, label='Flux CH4 Sud->Nord', color='black', linewidth=1.5)
    
    # Zone au-dessus de 0 : Le Nord importe (Flux Sud -> Nord positif)
    plt.fill_between(x, flux_values, 0, where=(flux_values >= 0), 
                     interpolate=True, color='blue', alpha=0.2, label='Le Nord importe')
    
    # Zone au-dessous de 0 : Le Sud importe (Flux Sud -> Nord négatif)
    plt.fill_between(x, flux_values, 0, where=(flux_values < 0), 
                     interpolate=True, color='orange', alpha=0.2, label='Le Sud importe')
    
    # Ligne de référence à 0 pour bien marquer la limite
    plt.axhline(0, color='black', linewidth=0.8, linestyle='-')
    
    # Fixer l'échelle de l'axe Y
    plt.ylim(-300000, 120000)
    
    plt.title('Flux de Méthane (CH4) : Direction et montant des échanges')
    plt.xlabel('Date')
    plt.ylabel('Puissance (MW)')
    
    # La légende inclura automatiquement les zones colorées
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.grid(True, linestyle=':', alpha=0.4)
    
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def plot_flux_ch4_week_hourly(data, week_number, save_path):
    """
    Plot le flux CH4 heure par heure pour une semaine donnée avec zones colorées.
    """
    df_hourly = data.copy()
    df_hourly['Date'] = pd.to_datetime(df_hourly['Date'])
    
    # Filtrage de la semaine cible
    target_week = df_hourly[df_hourly['Date'].dt.isocalendar().week == week_number].copy()
    
    if target_week.empty:
        print(f"Semaine {week_number} non trouvée.")
        return

    plt.figure(figsize=(12, 7))
    x = np.arange(len(target_week))
    flux_values = target_week['CH4_flux_S_N']
    
    # Courbe principale
    plt.plot(x, flux_values, color='black', linewidth=1.5, label='Flux CH4 Sud->Nord')
    
    # Zone au-dessus de 0 : Le Nord importe
    plt.fill_between(x, flux_values, 0, where=(flux_values >= 0), 
                     interpolate=True, color='blue', alpha=0.2, label='Le Nord importe')
    
    # Zone au-dessous de 0 : Le Sud importe
    plt.fill_between(x, flux_values, 0, where=(flux_values < 0), 
                     interpolate=True, color='orange', alpha=0.2, label='Le Sud importe')
    
    # Ligne de référence zéro
    plt.axhline(0, color='black', linewidth=1, linestyle='-')
    
    # Échelle fixe (ajustée à vos flux habituels)
    plt.ylim(-300000/24, 120000/24)
    
    # Graduation des jours
    ticks = np.arange(0, 7 * 24, 24)
    days = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
    plt.xticks(ticks, days)
    
    plt.title(f'Flux de Méthane (CH4) - Horaire - Semaine {week_number}')
    plt.xlabel('Heures de la semaine')
    plt.ylabel('Puissance (MW)')
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.grid(True, linestyle=':', alpha=0.4)
    
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def plot_flux_h2(x, data, save_path):
    """Plot flux H2 N-S au cours de l'année avec échelle fixe."""
    plt.figure(figsize=(10, 6))
    
    # On trace le flux H2
    plt.plot(x, data['H2_flux_S_N'], label='Flux H2 Sud->Nord', color='cyan')
    
    # Fixer l'échelle de l'axe Y
    #plt.ylim(0, 500000)
    
    plt.title('Flux d\'Hydrogène (H2) au cours de l\'année')
    plt.xlabel('Date')
    plt.ylabel('Puissance (MW)')
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.grid(True, linestyle=':', alpha=0.6)
    
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def plot_stock_STEP(x, data, save_path):
    """Plot le stock de la STEP au cours de l'année."""
    plt.figure(figsize=(10, 6))
    
    # On trace le flux H2
    plt.plot(x, data['stock_STEP'], label='Niveau de stock STEP', color='blue')
    
    plt.ylim(-100000,3500000)
    plt.title('Stock STEP au cours de l\'année')
    plt.xlabel('Date')
    plt.ylabel('Puissance stockée (MW)')
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.grid(True, linestyle=':', alpha=0.6)
    
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def plot_stock_STEP_week_hourly(data, week_number, save_path):
    """
    Plot le niveau de stock de la STEP heure par heure pour une semaine donnée.
    """
    df_hourly = data.copy()
    df_hourly['Date'] = pd.to_datetime(df_hourly['Date'])
    
    # Filtrage de la semaine cible
    target_week = df_hourly[df_hourly['Date'].dt.isocalendar().week == week_number].copy()
    
    if target_week.empty:
        print(f"Semaine {week_number} non trouvée.")
        return

    plt.figure(figsize=(12, 7))
    x = np.arange(len(target_week))
    
    # On trace le niveau de stock
    plt.plot(x, target_week['stock_STEP'], color='blue', linewidth=2, label='Niveau de stock STEP')
    
    # Remplissage sous la courbe pour mieux voir le volume
    plt.fill_between(x, target_week['stock_STEP'], 0, color='blue', alpha=0.1)
    
    # Échelle fixe identique à votre fonction globale pour faciliter la comparaison
    #plt.ylim(-100000/24, 3500000/24)
    
    # Graduation des jours
    ticks = np.arange(0, 7 * 24, 24)
    days = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
    plt.xticks(ticks, days)
    
    plt.title(f'Niveau du Stock STEP - Horaire - Semaine {week_number}')
    plt.xlabel('Heures de la semaine')
    plt.ylabel('Énergie stockée (MWh)')
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.grid(True, linestyle=':', alpha=0.6)
    
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def plot_stock_battery(x, data, save_path):
    """Plot le niveau de stock théorique des batteries (différence cumulée)."""
    plt.figure(figsize=(10, 6))
    
    plt.plot(x, data['stock_battery'], label='Niveau de stock des batteries', color='blue')
    
    plt.title('Évolution du stock Batterie au cours de l\'année')
    plt.xlabel('Date')
    plt.ylabel('Énergie stockée cumulée (MWh)')
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.grid(True, linestyle=':', alpha=0.6)
    
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def group_by_day(data):
    data['Date'] = pd.to_datetime(data['Date'])
    daily_data = data.groupby(data['Date'].dt.date).sum(numeric_only=True)
    daily_data.insert(0, 'Date', daily_data.index)
    return daily_data

def group_by_week(data):
    data['Date'] = pd.to_datetime(data['Date'])
    weekly_data = data.groupby(data['Date'].dt.isocalendar().week).sum(numeric_only=True)
    weekly_data.insert(0, 'Week', weekly_data.index)
    return weekly_data

# TODO
# SUR LE DOC : 
#  - expliquer oscillations
#  - ajouter courbes points mensuels pour montrer échec
#  - étoffer analyses avec résultats des visualisations

# --- BOUCLE PRINCIPALE SUR TOUS LES SCÉNARIOS ---

def visu_scenarios(scenarios=[range(24)]):
    base_scenarios_dir = './Scenarios'

    for i in scenarios:  # De 00 à 23
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
        daily_results = group_by_day(results) # non agrégé, pour les flux et stockages
        weekly_results = group_by_week(results) # non agrégé, pour les flux et stockages

        # 4. Traitement et Visualisations
        # Agrégation
        aggregated_results = agregate_data_by_energy_type(results, energy_type_map, scenario_path)
        
        # Plot Stock Gaz
        gaz_plot_path = os.path.join(image_folder_path, "gaz_stock_with_min_max.png")
        plot_gaz_stock_with_min_max(results, gaz_plot_path)

        # Plot Flux Gaz Daily
        flux_plot_path_ch4 = os.path.join(image_folder_path, "flux_gaz_daily_CH4.png")
        plot_flux_ch4(np.arange(len(daily_results)), daily_results, flux_plot_path_ch4)
        flux_plot_path_h2 = os.path.join(image_folder_path, "flux_gaz_daily_H2.png")
        plot_flux_h2(np.arange(len(daily_results)), daily_results, flux_plot_path_h2)

        # Plot Flux Gaz Weekly
        flux_plot_path_ch4 = os.path.join(image_folder_path, "flux_gaz_weekly_CH4.png")
        plot_flux_ch4(np.arange(len(weekly_results)), weekly_results, flux_plot_path_ch4)
        flux_plot_path_h2 = os.path.join(image_folder_path, "flux_gaz_weekly_H2.png")
        plot_flux_h2(np.arange(len(weekly_results)), weekly_results, flux_plot_path_h2)

        # Groupement quotidien et Stackplot élec
        daily_year = group_by_day(aggregated_results)
        stack_plot_path = os.path.join(image_folder_path, "stackplot_energie_daily.png")
        plot_stackplot_energie(np.arange(len(daily_year)), daily_year, stack_plot_path)

        # Groupement hebdomadaire et Stackplot élec
        weekly_year = group_by_week(aggregated_results)
        stack_plot_weekly_path = os.path.join(image_folder_path, "stackplot_energie_weekly.png")
        plot_stackplot_energie(np.arange(len(weekly_year)), weekly_year, stack_plot_weekly_path, freq='Weekly')

        # Plot Production Elec au gaz Weekly
        gaz_prod_weekly_path = os.path.join(image_folder_path, "gaz_elec_weekly.png")
        plot_elec_gaz(np.arange(len(weekly_results)), weekly_results, gaz_prod_weekly_path)

        # Plot Production Gaz
        gaz_prod_path_CH4 = os.path.join(image_folder_path, "gaz_production_CH4.png")
        plot_stackplot_ch4(np.arange(len(daily_results)), daily_results, gaz_prod_path_CH4)
        gaz_prod_path_H2 = os.path.join(image_folder_path, "gaz_production_H2.png")
        plot_stackplot_h2(np.arange(len(daily_results)), daily_results, gaz_prod_path_H2)

        # Plot Stcok STEP
        stock_step_path = os.path.join(image_folder_path, "stock_step.png")
        plot_stock_STEP(np.arange(len(weekly_results)), weekly_results, stock_step_path)
        
        # Plot Stock STEP Horaire Semaine 30
        step_hourly_path = os.path.join(image_folder_path, "stock_step_hourly_W30.png")
        plot_stock_STEP_week_hourly(results, 30, step_hourly_path)

        # Plot Stock Batterie
        stock_battery_path = os.path.join(image_folder_path, "stock_battery.png")
        plot_stock_battery(np.arange(len(daily_results)), daily_results, stock_battery_path)

#       Plot Horaire spécifique (Exemple : Semaine 30 en été)
        hourly_week_path = os.path.join(image_folder_path, "stackplot_hourly_W30.png")
        # Attention : passez bien 'aggregated_results' car la fonction attend les types d'énergie
        plot_stackplot_week_hourly(aggregated_results, 30, hourly_week_path)

        # Plot Flux CH4 Horaire Semaine 30
        flux_hourly_path = os.path.join(image_folder_path, "flux_ch4_hourly_W30.png")
        plot_flux_ch4_week_hourly(results, 30, flux_hourly_path)

        print(f"Scénario {scenario_id} terminé. Images sauvegardées dans {image_folder_path}")

    print("\n--- Tous les scénarios ont été traités ---")

    # écrit dans un fichier txt les taux d'allumage et les parts de chaque source d'énergie pour chaque scénario
    output_file = "scenario_energy_stats.txt"
    with open(output_file, 'w') as f:
        for i in scenarios:
            scenario_id = f"{i:02d}"
            scenario_folder = f"Results_{scenario_id}"
            scenario_path = os.path.join(base_scenarios_dir, scenario_folder)
            
            if not os.path.exists(scenario_path):
                continue
            
            aggregated_csv_path = os.path.join(scenario_path, 'aggregated_data.csv')
            if not os.path.exists(aggregated_csv_path):
                continue
            
            data = pd.read_csv(aggregated_csv_path)
            # ne pas compter la charge nette pour le total d'énergie
            total_energy = data.drop(columns=['Date', 'Charge Nette', 'RES']).sum().sum()
            f.write(f"Scénario {scenario_id}:\n")
            for energy_type in energy_type_map.keys():
                if energy_type in data.columns and energy_type not in ['Charge Nette', 'RES']:
                    energy_sum = data[energy_type].sum()
                    percentage = (energy_sum / total_energy) * 100 if total_energy > 0 else 0
                    f.write(f"  {energy_type}: {percentage:.2f}%\n")
            f.write("\n")

visu_scenarios([1, 23])

# comparer prod_CH4_S_2 sur les deux scénarios pour voir si différences d'importation
somme_S1 = pd.read_csv('./Scenarios/Results_01/year.csv')['CH4_S_prod_2'].sum()
somme_S23 = pd.read_csv('./Scenarios/Results_23/year.csv')['CH4_S_prod_2'].sum()
print(f"Somme CH4_S_prod_2 Scénario 1: {somme_S1}")
print(f"Somme CH4_S_prod_2 Scénario 23: {somme_S23}")