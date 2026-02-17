# System statystyk automatów

## Opis

System statystyk zbiera informacje o działaniu każdego automatu. Statystyki są **niedostępne dla SRAPL** - służą wyłącznie do oceny efektywności działania automatu w symulacji.

## Zbierane dane

Dla każdego automatu rejestrowane są:

| Statystyka | Opis |
|------------|------|
| `automaton_id` | Unikalny identyfikator automatu |
| `birth_tick` | Tick narodzin |
| `parent_id` | ID rodzica (None dla pierwszych automatów) |
| `steps_executed` | Liczba wykonanych kroków symulacji |
| `distance_traveled` | Łączna przebyta odległość |
| `resources_collected` | Zebrane zasoby (per typ) |
| `parts_produced` | Wyprodukowane części (per typ) |
| `offspring_count` | Liczba potomków |
| `energy_produced` | Wyprodukowana energia (IDLE + PowerGenerator) |
| `energy_consumed` | Zużyta energia |
| `gold_fitness_reported` | Czy gold_fitness został zaraportowany |
| `gold_fitness_report_tick` | Tick raportowania gold_fitness |

## Konfiguracja

W `src/config.py`:

```python
# Interwał raportowania (w tickach)
# 0 = tylko przy śmierci
# n > 0 = co n kroków + przy śmierci
STATS_REPORT_INTERVAL = 0

# Gold Fitness
GOLD_FITNESS_TIME = 200      # Ticks po których obliczany jest gold_fitness
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

## Gold Fitness

Gold fitness to miara sukcesu ewolucyjnego: suma złota zebranego przez automata i wszystkich jego potomków.

### Obliczanie gold_fitness

```python
from stats import stats_manager

# Oblicz gold_fitness dla automatu
gold_fitness = stats_manager.calculate_gold_fitness(automaton_id=1)
print(f"Gold fitness: {gold_fitness}")
```

### Automatyczne raportowanie

Gold fitness jest automatycznie raportowany:
1. Po `GOLD_FITNESS_TIME` tickach od narodzin automatu
2. Przy śmierci automatu (jeśli nie był wcześniej raportowany)

Format logu:
```
GOLD_FITNESS: automaton_id=1, gold_fitness=14, tick=200
```

### Losowa śmierć

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
print(f'Gold fitness: {stats_manager.calculate_gold_fitness(parent.automaton_id)}')
"
```
