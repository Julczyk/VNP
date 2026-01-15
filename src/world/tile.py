from config import ResourceType


class Tile:
    """
    Reprezentuje pojedynczy kafelek lądu.
    Może zawierać surowce (np. RAW_ORE).
    """

    def __init__(self):
        # słownik zasobów na kafelku
        # np. {ResourceType.RAW_ORE: 12}
        self.materials: dict[ResourceType, float] = {}

    def has_resources(self) -> bool:
        """Czy kafelek zawiera jakiekolwiek zasoby"""
        return bool(self.materials)

    def __repr__(self):
        return "🍀"


class WaterTile(Tile):
    """
    Kafelek wody - nie zawiera zasobów,
    ale ma głębokość (do wizualizacji).
    """

    def __init__(self, depth: float = 0.0):
        super().__init__()
        self.depth = depth

    def __repr__(self):
        return "🌊"
