import subprocess
from tqdm import tqdm
import time

# On enregistre le début de l'exécution globale
start_total = time.time()
total_cost_year = 0.0

for week in tqdm(range(52)):
    start_week = time.time()
    
    # On utilise capture_output=True pour lire ce que Julia affiche
    result = subprocess.run([
        "julia",
        "Optim_mix_per_week.jl",
        str(week)
    ], capture_output=True, text=True)
    
    # Analyse de la sortie pour trouver le coût
    week_cost = 0.0
    for line in result.stdout.split('\n'):
        if "WEEK_OBJECTIVE:" in line:
            week_cost = float(line.split(":")[1].strip())
            total_cost_year += week_cost
            break
            
    end_week = time.time()
    duration_week = end_week - start_week
    
    print(f"OK Week S{week} | Durée: {duration_week:.2f}s | Coût hebdo: {week_cost:,.2f} €")

end_total = time.time()
total_duration = end_total - start_total

# --- Affichage final des coûts ---
print("-" * 30)
print(f"Simulation terminée en {total_duration / 60:.2f} minutes.")
print(f"COÛT TOTAL OPÉRATIONNEL ANNUEL : {total_cost_year:,.2f} €")
print("-" * 30)

# Optionnel : Sauvegarder le résultat dans un fichier
with open("annual_cost_summary.txt", "w") as f:
    f.write(f"Coût total de la fonction objectif sur 52 semaines : {total_cost_year} euros")