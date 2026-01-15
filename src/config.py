from enum import Enum

# Definicja ID funkcji części (f_n)
class FunctionID(Enum):
    IDLE = 0        # PV Panel / Czekanie
    MOVE = 1        # Pędnik
    SCAN = 2        # Skaner
    STORE = 3       # Magazyn (zrzut/zarządzanie)
    SMELT = 4       # Huta
    ASSEMBLE = 5    # Assembler (Produkcja części)
    CHECK_BAT = 6   # Akumulator (status)
    COLLECT = 7     # Zbieranie zasobów
    # 8-9 zarezerwowane na przyszłość

class ResourceType(Enum):
    ENERGY = 0
    RAW_ORE = 1
    PROCESSED_METAL = 2
    COAL = 3
    IRON = 4
    GOLD = 5
    URANIUM = 6
    # ID części jako "surowiec" w magazynie
    PART_ENGINE = 101
    PART_SCANNER = 102
    # ...


# --------------------------
# Parametry fizyczne zasobów:

RESOURCE_MASS = {
    ResourceType.ENERGY: 0.0,
    ResourceType.RAW_ORE: 2.0,
    ResourceType.PROCESSED_METAL: 1.0,

    # Części jako ładunek
    ResourceType.PART_ENGINE: 10.0,
    ResourceType.PART_SCANNER: 8.0,
}

PART_RESOURCE_MAP = {
    "Engine": ResourceType.PART_ENGINE,
    "Scanner": ResourceType.PART_SCANNER,
}

RESOURCE_GENERATION = {
    ResourceType.RAW_ORE: {
        "weight": 50,
        "amount": (5, 20),
    },
    ResourceType.COAL: {
        "weight": 30,
        "amount": (3, 15),
    },
    ResourceType.IRON: {
        "weight": 15,
        "amount": (2, 10),
    },
    ResourceType.GOLD: {
        "weight": 4,
        "amount": (1, 5),
    },
    ResourceType.URANIUM: {
        "weight": 1,
        "amount": (1, 2),
    },
}

RESOURCE_THRESHOLD = {
    ResourceType.URANIUM: 0.85,
    ResourceType.GOLD: 0.75,
    ResourceType.IRON: 0.60,
    ResourceType.COAL: 0.55,
    ResourceType.RAW_ORE: 0.55,
}
