# System statystyk automatów

## Opis

System statystyk zbiera informacje o działaniu każdego automatu. Statystyki są **niedostępne dla SRAPL** - służą wyłącznie do oceny efektywności działania automatu w symulacji.

## Zbierane dane

Dla każdego automatu rejestrowane są:

| Statystyka | Opis |
|------------|------|
| `steps_executed` | Liczba wykonanych kroków symulacji |
| `distance_traveled` | Łączna przebyta odległość |
| `resources_collected` | Zebrane zasoby (per typ) |
| `parts_produced` | Wyprodukowane części (per typ) |
| `offspring_count` | Liczba potomków |
| `energy_produced` | Wyprodukowana energia (IDLE + PowerGenerator) |
| `energy_consumed` | Zużyta energia |

## Konfiguracja

W `src/config.py`:

```python
# Interwał raportowania (w tickach)
# 0 = tylko przy śmierci
# n > 0 = co n kroków + przy śmierci
STATS_REPORT_INTERVAL = 0
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

## Testowanie

```bash
source .venv/bin/activate
python testing/test_stats.py
```
