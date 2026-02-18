import subprocess
from tqdm import tqdm

for week in tqdm(range(52)):
    subprocess.run([
        "julia",
        "Optim_mix_per_week.jl",
        str(week)
    ])
