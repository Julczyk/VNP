import sys
import os
import random
import statistics
import csv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from world.world import World
from automaton import Automaton
from parts import Engine, Scanner, Storage, Collector, Smelter, Assembler, PowerGenerator
from config import ResourceType, FunctionID
from simulation_logger import SimulationLogger

# --- KONFIGURACJA SYMULACJI ---
WORLD_WIDTH = 200
WORLD_HEIGHT = 200
NUM_AUTOMATA = 50
SIMULATION_TICKS = 2000
METRICS_INTERVAL = 10
LOG_FILE = "simulation_gold.json"

# Program: Szukaj Złota, Idź, Zbierz, Przetwórz (Smelt)
# Zoptymalizowany pod kątem zarządzania energią
GOLD_SEEKER_PROGRAM = '''
$PARTS: 1.0, 1.2, 2.0, 1.0, 1.0, 0.0, 1.5;
# Engine, Scanner, Storage, Collector, Smelter, Assembler, Generator

$PROGRAMM
# 1. CRITICAL ENERGY CHECK
# X[0] is energy% (0.0-1.0). If < 40%, forced rest.
IF (0.4 - X[0]) {
    f_0();
}

# 2. Skanuj w poszukiwaniu ZŁOTA (ID 5)
f_2(1.0, 5.0);

# Jeśli znaleziono (dist >= 0). 
# X[2] = dist. Jeśli nie znaleziono, X[2] = -1.
# X[2] + 0.5 > 0 dla dist >= 0. Dla dist -1 jest < 0.
IF (X[2] + 0.5) {
    # Jeśli daleko (dist > 0), idź
    IF (X[2]) {
        f_1(X[1], 4.0); # Ruch (Szybciej!)
        f_0();          # Regeneracja po ruchu
    }
    
    # Zawsze próbuj zbierać (jeśli jesteśmy na miejscu lub blisko)
    f_7(1.0);       # Zbierz
    f_0();          # Regeneracja
    f_4(1.0);       # Przetwórz
    f_0();          # Regeneracja
}

# Jeśli NIE znaleziono złota (X[2] = -1)
# -1 + 0.5 = -0.5 (False). Więc else:
IF (0.0 - (X[2] + 0.5)) {
    f_2(1.0, 1.0); # Skanuj rude
    IF (X[2] + 0.5) {
        IF (X[2]) {
            f_1(X[1], 4.0); # Ruch (Szybciej!)
            f_0();
        }
        f_7(1.0);
        f_0();
        f_4(1.0);
    }
    # Random walk
    IF (0.0 - (X[2] + 0.5)) {
        f_1(1.0, 4.0); # Ruch losowy (Szybciej!)
        f_0();
    }
}

# Zawsze odpocznij na koniec pętli
f_0();
'''

GENOME = [
    (Engine, 1.0),
    (Scanner, 1.2),
    (Storage, 2.0),
    (Collector, 1.0),
    (Smelter, 1.0),
    (Assembler, 0.0),
    (PowerGenerator, 1.5),
]

def ascii_plot(data, title, height=15):
    """Rysuje prosty wykres ASCII."""
    if not data:
        return
    
    max_val = max(data)
    min_val = min(data)
    range_val = max_val - min_val if max_val > min_val else 1.0
    
    print(f"\n--- {title} (Max: {max_val:.2f}) ---")
    
    # Downsample to ~60 points width
    width = 60
    step = max(1, len(data) // width)
    sampled = data[::step][:width]
    
    grid = [[' ' for _ in range(len(sampled))] for _ in range(height)]
    
    for x, val in enumerate(sampled):
        # Normalize to 0..height-1
        y = int(((val - min_val) / range_val) * (height - 1))
        y = max(0, min(height - 1, y))
        grid[height - 1 - y][x] = '*'
        
    for row in grid:
        print("".join(row))
    print("-" * len(sampled))


def main():
    print(f"Inicjalizacja świata {WORLD_WIDTH}x{WORLD_HEIGHT}...")
    world = World(WORLD_WIDTH, WORLD_HEIGHT, seed=42)
    
    logger = SimulationLogger(LOG_FILE)
    
    print(f"Spawnowanie {NUM_AUTOMATA} automatów typu 'Gold Seeker'...")
    for _ in range(NUM_AUTOMATA):
        x = random.randint(0, WORLD_WIDTH - 1)
        y = random.randint(0, WORLD_HEIGHT - 1)
        
        # Znajdź ląd
        tries = 0
        while tries < 100:
            if not getattr(world.get_tile((x, y)), 'depth', 0): # Check if not water
                break
            x = random.randint(0, WORLD_WIDTH - 1)
            y = random.randint(0, WORLD_HEIGHT - 1)
            tries += 1
            
        auto = Automaton(GOLD_SEEKER_PROGRAM, GENOME, world, (x, y))
        world.add_automaton(auto)
        
        # --- BONUS: Spawn Gold near robot to ensure fitness > 0 for demo ---
        # Place gold 1-3 steps away
        gx = max(0, min(WORLD_WIDTH-1, x + random.randint(-3, 3)))
        gy = max(0, min(WORLD_HEIGHT-1, y + random.randint(-3, 3)))
        tile = world.get_tile((gx, gy))
        if not getattr(tile, 'depth', 0): # Check not water
            tile.materials[ResourceType.GOLD] = 50 # Rich deposit
            # print(f"  -> Spawning RICH GOLD deposit at ({gx}, {gy}) for robot at ({x}, {y})")

    history = {
        'tick': [],
        'count': [],
        'max_fitness': [],
        'avg_fitness': []
    }

    print("Logging Initial State...")
    logger.log_init(world)
    logger.log_step(world) # Log Tick 0

    print(f"Start symulacji ({SIMULATION_TICKS} kroków)...")
    
    for i in range(SIMULATION_TICKS):
        world.update()
        logger.log_step(world)
        
        if i % METRICS_INTERVAL == 0:
            count = len(world.automata)
            
            # Pobierz fitness ŻYWYCH automatów
            fitness_values = [a.stats.calculate_fitness() for a in world.automata]
            
            if fitness_values:
                max_fit = max(fitness_values)
                avg_fit = statistics.mean(fitness_values)
            else:
                max_fit = 0.0
                avg_fit = 0.0
            
            history['tick'].append(i)
            history['count'].append(count)
            history['max_fitness'].append(max_fit)
            history['avg_fitness'].append(avg_fit)
            
            if i % 100 == 0:
                print(f"Tick {i}: Pop={count}, MaxFit={max_fit:.1f}, AvgFit={avg_fit:.2f}")

        if len(world.automata) == 0:
            print("Wszystkie automaty wymarły!")
            break

    logger.save()

    # --- ZAPIS WYNIKÓW ---
    csv_path = 'simulation_gold_results.csv'
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Tick', 'Population', 'Max_Fitness', 'Avg_Fitness'])
        for t, c, mx, av in zip(history['tick'], history['count'], history['max_fitness'], history['avg_fitness']):
            writer.writerow([t, c, mx, av])
            
    print(f"\nWyniki zapisano do: {csv_path}")
    
    # --- PREZENTACJA ---
    ascii_plot(history['max_fitness'], "Max Fitness (Gold Processed)")
    ascii_plot(history['avg_fitness'], "Avg Fitness")
    ascii_plot(history['count'], "Population Count")

if __name__ == "__main__":
    main()
