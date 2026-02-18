# System statystyk automatów

## Opis

System statystyk zbiera informacje o działaniu każdego automatu. Statystyki są **niedostępne dla SRAPL** - służą wyłącznie do oceny efektywności działania automatu w symulacji.

## Zbierane dane

Dla każdego automatu rejestrowane są:

| Statystyka | Opis |
|------------|------|
| `automaton_id` | Unikalny identyfikator automatu |
| `birth_tick` | Tick narodzin |
| `parent_id` | ID rodzica (-1 dla automatów startowych) |
| `steps_executed` | Liczba wykonanych kroków symulacji |
| `distance_traveled` | Łączna przebyta odległość |
| `resources_collected` | Zebrane zasoby (per typ) |
| `parts_produced` | Wyprodukowane części (per typ) |
| `offspring_count` | Liczba potomków |
| `energy_produced` | Wyprodukowana energia (IDLE + PowerGenerator) |
| `energy_consumed` | Zużyta energia |
| `start_position` | Pozycja początkowa automatu |
| `alive_at_end` | Czy automat żył na końcu symulacji |
| `death_tick` | Tick śmierci (None jeśli żyje) |

## Konfiguracja

W `src/config.py`:

```python
# Interwał raportowania (w tickach)
# 0 = tylko przy śmierci
# n > 0 = co n kroków + przy śmierci
STATS_REPORT_INTERVAL = 0

# Losowa śmierć
RANDOM_DEATH_CHANCE = 0.01   # 1% szansa na losową śmierć per tick
```

## Użycie

### Dostęp do statystyk automatu

```python
from automaton import Automaton

auto = Automaton(...)

# Odczyt statystyk
print(auto.stats.steps_executed)
print(auto.stats.energy_consumed)
print(auto.stats.get_total_resources_collected())
```

### Raportowanie

```python
from stats import stats_manager, setup_stats_logging
import logging

# Włącz logowanie raportów
setup_stats_logging(logging.INFO)

# Ręczne raportowanie
stats_manager.report(auto.stats, current_tick=100, reason="manual")
```

### Podsumowanie symulacji

```python
from stats import stats_manager

# Wszystkie zebrane raporty
reports = stats_manager.get_all_reports()

# Statystyki agregowane (z raportów śmierci)
summary = stats_manager.get_summary()
print(f"Średni czas życia: {summary['avg_lifetime']}")
print(f"Średnia zebrana: {summary['avg_resources']}")
```

## Format raportu

```
=== STATS REPORT (death) ===
Automaton ID: 1
Lifetime: 150 ticks (born: 0)
Steps executed: 150
Distance traveled: 45.5
Offspring: 2
Energy: produced=120.0, consumed=180.0, balance=-60.0
Resources collected: 25 total
  - RAW_ORE: 15
  - IRON: 10
Parts produced: 0 total
==============================
```

## Lineage Tracking

System śledzi relacje rodzic-dziecko między automatami.

### Śledzenie potomków

```python
from stats import stats_manager

# Pobierz wszystkich potomków automatu (rekurencyjnie)
descendants = stats_manager.get_descendants(automaton_id=1)
print(f"Potomkowie: {descendants}")

# Pobierz statystyki po ID
stats = stats_manager.get_stats_by_id(automaton_id=2)
print(f"Rodzic: {stats.parent_id}")
```

### Reset dla nowych iteracji

```python
from stats import stats_manager

# Reset wszystkich danych (dla nowych testów)
stats_manager.reset()
```

## Logowanie akcji

Każdy automat loguje swoje akcje w formacie:
```
Tick [time]: Probe [ID] at [x, y] with energy [%] [action]
```

Przykłady:
```
Tick 100: Probe 1 at [15, 20] with energy 75.5% moving
Tick 101: Probe 1 at [16, 20] with energy 70.2% idle/charging
Tick 150: Probe 1 at [20, 25] with energy 85.0% producing offspring
```

## Simulation.py DataFrame

Funkcja `simulate()` zwraca DataFrame z pełnymi danymi automatów:

| Kolumna | Opis |
|---------|------|
| `ID` | Identyfikator automatu |
| `tick` | Tick narodzin |
| `age` | Wiek (w tickach) |
| `program` | Genom/program SRAPL |
| `position` | Pozycja początkowa |
| `total_distance_traveled` | Łączna przebyta odległość |
| `energy_produced` | Wyprodukowana energia |
| `energy_consumed` | Zużyta energia |
| `offspring_count` | Liczba potomków |
| `alive_at_end` | Czy żył na końcu |
| `parent_ID` | ID rodzica (-1 dla startowych) |
| `{RESOURCE}_gathered` | Zebrane zasoby per typ |

## Losowa śmierć

Parametr `RANDOM_DEATH_CHANCE` wprowadza losową śmierć (1% per tick domyślnie), co:
- Wymusza rotację populacji
- Zapobiega "nieśmiertelnym" automatom blokującym ewolucję
- Symuluje wypadki i nieprzewidziane zdarzenia

## Testowanie

```bash
source .venv/bin/activate
python testing/test_stats.py

# Test lineage tracking
python -c "
from stats import stats_manager
from config import ResourceType

stats_manager.reset()
parent = stats_manager.create_stats(0)
child = stats_manager.create_stats(10, parent_id=parent.automaton_id)
parent.record_resource_collected(ResourceType.GOLD, 5)
child.record_resource_collected(ResourceType.GOLD, 3)
descendants = stats_manager.get_descendants(parent.automaton_id)
print(f'Potomkowie: {descendants}')
"
```
