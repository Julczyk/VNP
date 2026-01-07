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
    # 7-9 zarezerwowane na przyszłość

class ResourceType(Enum):
    ENERGY = 0
    RAW_ORE = 1
    PROCESSED_METAL = 2
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

