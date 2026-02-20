import subprocess
from tqdm import tqdm

for week in tqdm(range(3)):
    subprocess.run([
        "julia",
        "Optim_mix_per_week.jl",
        str(week)
    ])
    print(f"OK Week S{week}")
