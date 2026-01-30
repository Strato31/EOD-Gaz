import matplotlib.pyplot as plt
# import seaborn as sns
import pandas as pd
import numpy as np

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

#TODO : agréger ensemble les centrales de même type 
#TODO : ajouter le plot de la demande électrique sur le graphe
#TODO : ajouter choix de la semaine à afficher
#TODO : proposer des plots par centrale/source d'énergie
