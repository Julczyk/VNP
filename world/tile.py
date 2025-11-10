class Tile:
    '''
    Class representing a single tile, its parameters and raw materials that the tile contains.

    Attributes:
        materials : dict
            Dictionary, where key is type of material and value its quantity.
    '''
    def __init__(self, value: float):
        self.materials = {}
        if (value > 0):
            self.materials["steel"] = 1