RESOURCES = {
    "coal": 0.25,
    "copper": 0.45,
    "iron": 0.60,
    "gold": 0.75,
    "uranium": 0.90
}

UNDERWATER_RESOURCES = {        ## TO DO - RESPAWNING RESOURCES
    "clay": 0.2,
    "sand": 0.7
}

class Tile:
    '''
    Class representing a single tile, its parameters and raw materials that the tile contains.

    Attributes:
        materials : dict
            Dictionary, where key is type of material and value its quantity.
    '''
    def __init__(self, values):
        self.materials = {}

        candidates = [
            r for r, threshold in RESOURCES.items()
            if values[r] > threshold
        ]

        if candidates:
            resource = max(candidates, key=lambda r: RESOURCES[r])
            self.materials[resource] = max(abs(values[resource] - RESOURCES[resource])/1)

