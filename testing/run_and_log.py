import sys
import os
import random

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from world.world import World
from automaton import Automaton
from parts import Engine, Scanner, Storage, Collector, Smelter, Assembler, PowerGenerator
from simulation_logger import SimulationLogger
from config import ResourceType

# --- CONFIG ---
WORLD_WIDTH = 200
WORLD_HEIGHT = 200
NUM_AUTOMATA = 50
TICKS = 3000
LOG_FILE = "simulation_replay.json"

GOLD_SEEKER_PROGRAM = '''
$PARTS: 1.0, 1.2, 2.0, 1.0, 1.0, 0.0, 1.5;
$PROGRAMM
f_2(1.0, 5.0);
IF (X[2]) {
    f_1(X[1], 1.0);
    f_7(1.0);
    f_4(1.0);
}
IF (0.0 - X[2]) {
    f_1(1.0, 1.0); # Random move
}
f_0();
'''

GENOME = [
    (Engine, 1.0), (Scanner, 1.2), (Storage, 2.0),
    (Collector, 1.0), (Smelter, 1.0), (Assembler, 0.0), (PowerGenerator, 1.5)
]

def main():
    print("Initializing World...")
    world = World(WORLD_WIDTH, WORLD_HEIGHT, seed=42)
    
    logger = SimulationLogger(LOG_FILE)
    
    # Spawn
    for _ in range(NUM_AUTOMATA):
        x = random.randint(0, WORLD_WIDTH-1)
        y = random.randint(0, WORLD_HEIGHT-1)
        auto = Automaton(GOLD_SEEKER_PROGRAM, GENOME, world, (x, y))
        world.add_automaton(auto)
        
        # Ensure some gold nearby for action
        tile = world.get_tile((x, y))
        if not getattr(tile, 'depth', 0):
            gx = max(0, min(WORLD_WIDTH-1, x + random.randint(-2, 2)))
            gy = max(0, min(WORLD_HEIGHT-1, y + random.randint(-2, 2)))
            world.get_tile((gx, gy)).materials[ResourceType.GOLD] = 20

    print("Logging Initial State...")
    logger.log_init(world)
    logger.log_step(world) # Log Tick 0 state
    
    print(f"Running Simulation for {TICKS} ticks...")
    for i in range(TICKS):
        world.update()
        logger.log_step(world)
        if i % 50 == 0:
            print(f"Step {i}/{TICKS}")
            
    logger.save()
    print(f"Done! Log saved to {LOG_FILE}")
    print(f"Run 'python src/replay_viewer.py {LOG_FILE}' to watch.")

if __name__ == "__main__":
    main()
