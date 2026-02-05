"""
results : données complètes
results_short : données pour une semaine spécifique

agregate_data_by_energy_type(data, energy_type_map) : sommer les colonnes par type d'énergie
plot_stackplot(x, data, column_labels) : tracer les courbes empilées pour les types d'énergie
print_up_rates(data) : print les taux d'allumage

"""

import matplotlib.pyplot as plt
# import seaborn as sns
import pandas as pd
import numpy as np

<<<<<<< HEAD
# Chargement des résultats
results = pd.read_csv('results.csv', sep=';')
column_labels = results.columns.tolist()

results_week = results[:169]

x = np.arange(len(results_week))
print(results_week.shape)
print(results_week.columns)
plt.figure(figsize=(10, 6))
plt.stackplot(x, *[results_week.iloc[:, i] for i in range(1,results_week.shape[1]-2)], labels=column_labels[1:])
plt.legend(loc='upper left')
plt.show()
=======
# Chargement des données
results = pd.read_csv('results.csv', sep=';')
results.columns = results.columns.str.strip() #retirer les espaces dans les noms de colonnes
column_labels = results.columns.tolist() # Liste des labels des colonnes
x_year = np.arange(len(results)) # Axe des x pour une année complète

# Sélection d'une semaine spécifique (par exemple, de l'index 100 à 268)
results_short = results.iloc[100:269, :]
x_short = np.arange(len(results_short)) # Axe des x pour la semaine sélectionnée

# Map des types d'énergie aux colonnes correspondantes
energy_type_map = {
    'Nuclear': ['Iconuc1', 'Iconuc2', 'Tabarnuc1', 'Tabarnuc2', 'NucPlusUltra1', 'NucPlusUltra2'],
    'Gaz': ['Gazby', 'Pégaz', 'Samagaz', 'Omaïgaz1', 'Omaïgaz2', 'Gastafiore', 'Igaznodon1', 'Igaznodon2', 'Cogénérations'],
    'Charbon': ['Coron1', 'Coron2', 'Mockingjay', 'Lantier'],
    'Biomasse': ['Tacotac'],
    'Fioul': ['TicEtTac'],
    'Hydro': ['Hydro'],
    'STEP Pompage': ['STEP pompage'],
    'STEP Turbinage': ['STEP turbinage'],
    'Batterie Injection': ['Batterie injection'],
    'Batterie Soutirage': ['Batterie soutirage'],
    'RES': ['RES'],
    'Charge': ['load'],
    'Charge Nette': ['Net load']
}

def agregate_data_by_energy_type(data, energy_type_map):
    "Somme ensemble les colonnes correspondant à un même type d'énergie"
    aggregated_data = pd.DataFrame()
    aggregated_data['Date'] = data['Date']
    for energy_type, columns in energy_type_map.items():
        aggregated_data[energy_type] = data[columns].sum(axis=1)
    return aggregated_data


def plot_stackplot(x, data, column_labels):
    """Fait les courbes empilées pour les différents types de production d'énergie non fatales"""
    plt.figure(figsize=(10, 6))

    # Tracé des courbes empilées
    if len(column_labels)-4 == 10: 
        # couleurs choisies pour 10 types d'énergie si données agrégées utilisées
        colors = ['yellow', 'grey', 'black', 'green', 'black', 'blue', 'pink', 'purple', 'orange', 'red']
    else:
        # palette générique pour d'autres cas
        colors = sns.color_palette("hsv", len(column_labels)-4)
    # plot en négatif des colonnes de consommation (STEP pompage, Batterie soutirage)
    for _, col in enumerate(column_labels[1:data.shape[1]-3]):
        if col in ['STEP Pompage', 'Batterie Soutirage']:
            data[col] = -data[col]
    
    # Tracé des courbes empilées pour les types d'énergie sauf les 3 dernières colonnes (RES, Charge, Charge Nette)
    plt.stackplot(x, *[data.iloc[:, i] for i in range(1,data.shape[1]-3)], labels=column_labels[1:], colors=colors)
    
    # Ajout de la courbe de charge nette : on teste les deux noms possibles
    try :
        plt.plot(x, data['Charge Nette'], color='black', label='Charge Nette', ls='--', lw=0.8)
    except : 
        plt.plot(x, data['Net load'], color='black', label='Net Load', ls='--', lw=0.8)
    
    plt.title('Production d\'énergie (courbe de charge nette en pointillé)')
    plt.xlabel('Heures')
    plt.ylabel('Puissance (MW)')
    plt.legend(loc='upper left')
    
    plt.show()

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


# appel des fonctions, tests
aggregated_results = agregate_data_by_energy_type(results, energy_type_map)
plot_stackplot(x_year, aggregated_results, aggregated_results.columns.tolist())
print_up_rates(results)

>>>>>>> 3a9af5d0b60c07cd1059f4bb051f5c8a797f1e5d

