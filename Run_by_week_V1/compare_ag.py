import pandas as pd
import matplotlib.pyplot as plt
import os

def save_ag_performance_plots():
    # 1. Configuration et initialisation
    scenarios = {1: "AG=3", 2: "AG=4", 3: "AG=5", 4: "AG=6", 5: "AG=7", 14: "AG=0"}
    week_id = 51
    target_avg_ch4 = 0.734 * 20 * 10**6
    
    results_step, results_batt, results_ch4 = {}, {}, {}
    hours = range(1, 25)

    if not os.path.exists("./images"):
        os.makedirs("./images")

    # 2. Collecte des données
    for sc_id, label in scenarios.items():
        folder_name = f"Results_{sc_id:02}"
        file_path = f"./Scenarios/{folder_name}/result_S{week_id}.csv"
        
        if not os.path.exists(file_path):
            print(f"⚠️ Fichier manquant : {file_path}")
            continue
            
        df_week = pd.read_csv(file_path, sep=';', encoding='utf-8')
        # On prend le dernier jour de la semaine (indices 144 à 168)
        last_day = df_week.iloc[144:168].copy()
        
        # Stockage dans les dictionnaires
        results_step[label] = last_day['stock_STEP'].values
        results_batt[label] = last_day['stock_battery'].values
        
        ch4_total = last_day['stock_CH4_N'].values + last_day['stock_CH4_S'].values
        results_ch4[label] = ch4_total #/ target_avg_ch4 

    # 3. Fonction utilitaire pour générer chaque image
    def create_single_plot(data_dict, title, ylabel, filename):
        plt.figure(figsize=(10, 6))
        for label, values in data_dict.items():
            plt.plot(hours, values, label=label)
        
            
        plt.title(title)
        plt.ylabel(ylabel)
        plt.xlabel("Heures du dernier jour (S51)")
        plt.legend()
        plt.grid(True, linestyle=':', alpha=0.6)
        plt.tight_layout()
        
        output_path = f"./images/{filename}.png"
        plt.savefig(output_path)
        plt.close() # Important pour ne pas saturer la mémoire
        print(f"Image enregistrée : {output_path}")

    # 4. Génération des 3 fichiers distincts
    create_single_plot(results_step, "Stock STEP - S51", "Volume (MWh)", "stock_STEP")
    create_single_plot(results_batt, "Stock BATTERIES - S51", "Volume (MWh)", "stock_BATTERIES")
    create_single_plot(results_ch4, "Stock CH4 Normalisé - S51", "Ratio (Réel / Cible)", "stock_CH4_norm")

# Lancement
save_ag_performance_plots()