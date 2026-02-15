import time
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from world.world import World
from automaton import Automaton
from parts import Engine, Scanner, Storage, Collector, Smelter, Assembler, PowerGenerator
from stats import setup_stats_logging

def benchmark():
    setup_stats_logging()
    print("Setting up benchmark...")
    world = World(80, 80, seed=42)
    
    # Create some automata
    genome = [
        (Engine, 1.0),
        (Scanner, 1.0),
        (Storage, 1.0),
        (Collector, 1.0),
        (Smelter, 1.0),
        (Assembler, 1.0),
        (PowerGenerator, 1.0),
    ]
    
    program = '''
$PARTS:
1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0;

$PROGRAMM
f_2(1.0, 1.0);
'''
    
    # Add 50 automata
    for i in range(50):
        pos = (i % 80, (i // 80) % 80)
        a = Automaton(program, genome, world, pos)
        world.add_automaton(a)
        
    print(f"Starting benchmark with {len(world.automata)} automata...")
    start_time = time.time()
    steps = 100
    
    for i in range(steps):
        world.update()
        
    end_time = time.time()
    duration = end_time - start_time
    tps = steps / duration
    
    print(f"Benchmark finished: {steps} steps in {duration:.4f}s")
    print(f"TPS: {tps:.2f}")

if __name__ == "__main__":
    benchmark()
