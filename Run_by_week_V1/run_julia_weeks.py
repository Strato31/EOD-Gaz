import subprocess
from tqdm import tqdm
import time

# On enregistre le début de l'exécution globale
start_total = time.time()

for week in tqdm(range(52)):
    # On enregistre le début de la semaine spécifique
    start_week = time.time()
    
    subprocess.run([
        "julia",
        "Optim_mix_per_week.jl",
        str(week)
    ])
    
    end_week = time.time()
    duration_week = end_week - start_week
    
    # Affichage du temps par semaine (en secondes, arrondi)
    print(f"OK Week S{week} | Durée: {duration_week:.2f}s")

end_total = time.time()
total_duration = end_total - start_total

# Conversion en minutes pour plus de clarté à la fin
print("-" * 30)
print(f"Simulation terminée en {total_duration / 60:.2f} minutes.")