import json
import os
from config import ResourceType

class SimulationLogger:
    def __init__(self, filepath):
        self.filepath = filepath
        self.data = {
            "width": 0,
            "height": 0,
            "map_resources": [], # List of (x, y, resource_type, amount)
            "water_tiles": [],   # List of (x, y, depth)
            "steps": []          # List of step data
        }

    def log_init(self, world):
        """Logs the initial state of the world."""
        self.data["width"] = world.width
        self.data["height"] = world.height
        
        # Log map tiles
        for y in range(world.height):
            for x in range(world.width):
                tile = world.map[y, x]
                # Log water
                if hasattr(tile, 'depth'):
                    self.data["water_tiles"].append((x, y, tile.depth))
                
                # Log resources
                if tile.materials:
                    for res, amt in tile.materials.items():
                        # Serialize enum to name or value
                        self.data["map_resources"].append((x, y, res.name, amt))

    def log_step(self, world):
        """Logs a single simulation step."""
        step_data = {
            "tick": world.tick,
            "automata": [],
            "wrecks": []
        }

        # Log automata
        for auto in world.automata:
            step_data["automata"].append({
                "id": auto.stats.automaton_id,
                "x": auto.position[0],
                "y": auto.position[1],
                "energy": round(auto.energy, 1),
                "gold": auto.stats.gold_processed
            })
            
        # Log wrecks (simplified)
        for w in world.wrecks:
            # w is (x, y, resources)
            # resources is dict
            res_dict = {r.name: amt for r, amt in w[2].items()}
            step_data["wrecks"].append({
                "x": w[0],
                "y": w[1],
                "resources": res_dict
            })

        self.data["steps"].append(step_data)

    def save(self):
        """Writes the log to file."""
        print(f"Saving simulation log to {self.filepath}...")
        try:
            with open(self.filepath, 'w') as f:
                json.dump(self.data, f, indent=None) # Compact JSON
            print("Log saved successfully.")
        except Exception as e:
            print(f"Error saving log: {e}")
