"""
merge_weeks() : fusionner les fichiers de chaque semaine en un seul fichier pour l'année complète
agregate_data_by_energy_type(data, energy_type_map) : sommer les colonnes par type d'énergie
plot_stackplot_energie(x, data, imagename) : tracer les courbes empilées pour les types d'énergie
print_up_rates(data) : print les taux d'allumage
plot_gaz_stock_with_min_max(data, imagename) : tracer l'évolution du stockage de gaz avec les min et max quotidiens et les bornes à ne pas franchir
group_by_day(data) : regrouper les données par jour et calculer la somme pour chaque jour

"""

import os

import matplotlib.pyplot as plt
# import seaborn as sns
import pandas as pd
import numpy as np
import seaborn as sns
from openpyxl import load_workbook



# Map des types d'énergie aux colonnes correspondantes
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

def merge_weeks():
    """Fusionne les fichiers de chaque semaine en un seul fichier pour l'année complète"""
    path = './Run_by_week_V1/Results/'
    with open('year.csv', 'w', newline='') as year:
        for f in os.listdir(path):
            week_data = pd.read_csv(path + f, sep=';', encoding='ISO-8859-1')
            week_data.to_csv(year, index=False, header=not year.tell())
    year.close()

def agregate_data_by_energy_type(data, energy_type_map):
    "Somme ensemble les colonnes correspondant à un même type d'énergie"
    aggregated_data = pd.DataFrame()
    aggregated_data['Date'] = data['Date']
    for energy_type, columns in energy_type_map.items():
        aggregated_data[energy_type] = data[columns].sum(axis=1)

    agg = open('./aggregated_data.csv', 'w', newline='')
    aggregated_data.to_csv(agg, index=False)
    agg.close()
    return aggregated_data


def plot_stackplot_energie(x, data, imagename):
    """Fait les courbes empilées pour les différents types de production d'énergie non fatales"""
    plt.figure(figsize=(10, 6))
    column_labels = data.columns.tolist() # Liste des labels des colonnes après agrégation
    # plot en négatif des colonnes de consommation (STEP pompage, Batterie soutirage)
    for _, col in enumerate(column_labels[1:27]):
        if col in ['STEP Pompage', 'Batterie Soutirage']:
            data[col] = -data[col]

    # Tracé des courbes empilées
    print("column labels : ", column_labels)
    if len(column_labels) == 14: 
        # couleurs choisies pour 10 types d'énergie si données agrégées utilisées
        colors = ['yellow', 'grey', 'black', 'green', 'black', 'blue', 'pink', 'purple', 'orange', 'red']
        # Tracé des courbes empilées pour les types d'énergie sauf les 3 dernières colonnes (RES, Charge, Charge Nette)
        plt.stackplot(x, *[data.iloc[:, i] for i in range(1,10)], labels=column_labels[1:10], colors=colors)
    else:
        # palette générique pour d'autres cas
        colors = sns.color_palette("hsv", 27)
        # Tracé des courbes empilées pour les types d'énergie sauf les 3 dernières colonnes (RES, Charge, Charge Nette)
        plt.stackplot(x, *[data.iloc[:, i] for i in range(1,27)], labels=column_labels[1:27], colors=colors)

    # Ajout de la courbe de charge nette : on teste les deux noms possibles
    try :
        plt.plot(x, data['Charge Nette'], color='black', label='Charge Nette', ls='--', lw=0.8)
    except : 
        plt.plot(x, data['Net_load'], color='black', label='Net Load', ls='--', lw=0.8)

    plt.title('Production d\'énergie (courbe de charge nette en pointillé)')
    plt.xlabel('Heures')
    plt.ylabel('Puissance (MW)')
    plt.legend(loc='upper left')

    # Enregistrer le plot dans le dossier images
    plt.savefig(os.path.join('./images', f'{imagename}.png'))
    plt.close()

# Print les taux d'allumage pour chaque type de centrale
def print_up_rates(data):
    "Calcule et affiche les taux d'allumage pour chaque type de centrale"
    up_rates = {}
    total_hours = data.shape[0]
    print("Taux d'allumages (% d\'heures en fonctionnement):")
    print("-----------------------------------------")
    for column in data.columns:
        if column not in ['Date', 'RES', 'Charge', 'Charge Nette', 'load', 'net load']:
            hours_on = (data[column] > 0).sum()
            up_rate = hours_on / total_hours
            up_rates[column] = up_rate
    for energy_type, rate in up_rates.items():
        print(f"Taux d'allumage pour {energy_type}: {rate:.2%}")
    print("-----------------------------------------")


#######GAZ#########
# plot stockage gaz sur l'année complète, et des min et max pour chaque jour
def plot_gaz_stock_with_min_max(data, imagename):
    """Trace l'évolution du stockage de gaz avec les min et max quotidiens et les bornes à ne pas franchir."""
    # Conversion de la colonne 'Date' en format datetime
    data['Date'] = pd.to_datetime(data['Date'])
    
    # récupération de la capacité de stockage totale du gaz depuis l'Excel en K4
    # Charger le fichier Excel
    excel = load_workbook("Donnees_elec_gaz.xlsx")["Données_gaz"]
    # Accéder à la cellule K4
    capa_stock = excel["K4"].value


    # Regroupement des données par jour pour obtenir les min et max quotidiens, en sommant N et S pour obtenir le stockage total
    data['CH4_stock'] = data['CH4_N_stock'] + data['CH4_S_stock'] # Stockage total de gaz (Nord + Sud)
    daily_min = (data.groupby(data['Date'].dt.date)['CH4_stock'].min())/1000000 # conversion en TWh
    daily_max = (data.groupby(data['Date'].dt.date)['CH4_stock'].max())/1000000 # conversion en TWh

    # Création de l'axe x basé sur les dates quotidiennes
    daily_dates = daily_min.index 

    # Lecture des bornes quotidiennes depuis l'Excel
    bounds = pd.read_excel("Donnees_elec_gaz.xlsx", sheet_name="Conso_gaz", usecols="K:L", skiprows=1, nrows=len(daily_dates))
    
    # Multiplication des bornes par la capacité de stockage
    lower_bound = (bounds.iloc[:, 0]*capa_stock).to_numpy()
    upper_bound = (bounds.iloc[:, 1]*capa_stock).to_numpy()

    # Tracé des courbes
    plt.figure(figsize=(10, 6))

    # Intervalle rempli entre le min et max atteints dans la journée
    plt.fill_between(daily_dates, daily_min, daily_max, color='blue', alpha=0.2, label='Intervalle quotidien (min-max)')

    # Bornes quotidiennes à ne pas franchir (pointillés)
    plt.plot(daily_dates, lower_bound, label='Borne quotidienne min', color='orange', linestyle='--')
    plt.plot(daily_dates, upper_bound, label='Borne quotidienne max', color='red', linestyle='--')

    plt.title('Évolution du stockage de gaz avec bornes et intervalles quotidiens')
    plt.xlabel('Date')
    plt.ylabel('Volume (TWh)')
    plt.legend()
    plt.grid()

    # Enregistrement du graphique
    plt.savefig(os.path.join('./images', f'{imagename}.png'))
    plt.close()



def group_by_day(data):
    """Regroupe les données par jour et calcule la somme pour chaque jour."""
    data['Date'] = pd.to_datetime(data['Date'])
    daily_data = data.groupby(data['Date'].dt.date).sum(numeric_only=True)
    # ajouter la colonne Date au début du DataFrame
    daily_data.insert(0, 'Date', daily_data.index)
    return daily_data


##############################
# appel des fonctions, tests #
##############################

merge_weeks()

# Chargement des données
results = pd.read_csv('year.csv', sep=',')
results.columns = results.columns.str.strip()  # Retirer les espaces dans les noms de colonnes

# Sélection d'une période spécifique
results_short = results.iloc[100:269, :]
x_short = np.arange(len(results_short)) # Axe des x pour la semaine sélectionnée

# Agrégation des données par type d'énergie
aggregated_results = agregate_data_by_energy_type(results, energy_type_map)
# Print des taux d'allumage pour chaque type de centrale
print_up_rates(aggregated_results)
# Plot des min/max atteints pour le stockage de gaz et des bornes à ne pas franchir
plot_gaz_stock_with_min_max(results, "gaz_stock_with_min_max")

# Groupement des données par jour pour tracer les courbes empilées à l'échelle quotidienne
daily_year = group_by_day(aggregated_results)
# Plot des courbes empilées pour les types d'énergie à l'échelle quotidienne
plot_stackplot_energie(np.arange(len(daily_year)), daily_year, "stackplot_energie_daily") 