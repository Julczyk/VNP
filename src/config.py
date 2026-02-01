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

# --------------------------
# Mapowanie funkcji f_n na klasy części:
# Importy części są opóźnione (lazy) aby uniknąć cyklicznych zależności

def get_function_to_part_map():
    """
    Zwraca mapowanie FunctionID -> klasa części.
    Lazy import aby uniknąć cyklicznych zależności.
    """
    from parts import Engine, Scanner, Storage, Smelter, Assembler, Collector, PowerGenerator

    return {
        FunctionID.IDLE: PowerGenerator,    # f_0 - odpoczynek/ładowanie
        FunctionID.MOVE: Engine,            # f_1 - ruch
        FunctionID.SCAN: Scanner,           # f_2 - skanowanie
        FunctionID.STORE: Storage,          # f_3 - magazyn
        FunctionID.SMELT: Smelter,          # f_4 - huta
        FunctionID.ASSEMBLE: Assembler,     # f_5 - assembler
        # FunctionID.CHECK_BAT: Battery,    # f_6 - akumulator (niezaimplementowany)
        FunctionID.COLLECT: Collector,      # f_7 - zbieranie
    }


# Kolejność części w sekcji $PARTS programu SRAPL
# Indeks w liście = pozycja w $PARTS
PARTS_ORDER = [
    FunctionID.MOVE,      # 0 - Engine
    FunctionID.SCAN,      # 1 - Scanner
    FunctionID.STORE,     # 2 - Storage
    FunctionID.COLLECT,   # 3 - Collector
    FunctionID.SMELT,     # 4 - Smelter
    FunctionID.ASSEMBLE,  # 5 - Assembler
    FunctionID.IDLE,      # 6 - PowerGenerator
]


def get_parts_classes_ordered():
    """
    Zwraca listę klas części w kolejności zgodnej z $PARTS.
    """
    func_to_part = get_function_to_part_map()
    return [func_to_part[fid] for fid in PARTS_ORDER if fid in func_to_part]


# --------------------------
# System statystyk automatów:

# Interwał raportowania statystyk (w tickach)
# 0 = raportowanie tylko przy śmierci automatu
# n > 0 = raportowanie co n kroków + przy śmierci
STATS_REPORT_INTERVAL = 0
