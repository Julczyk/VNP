# Testy podstawowej symulacji

Programy SRAPL umożliwiające "życie" automatów - przetrwanie, zbieranie zasobów, reprodukcję.

## Uruchamianie

```bash
cd /home/julczyk/Dokumenty/Automaty/VNP
source .venv/bin/activate

# Przetrwanie - zarządzanie energią
python testing/basic_sim/test_survivor.py

# Zbieranie zasobów
python testing/basic_sim/test_gatherer.py

# Reprodukcja
python testing/basic_sim/test_reproducer.py

# Pełny cykl życia
python testing/basic_sim/test_lifecycle.py

# Ekosystem - wiele automatów
python testing/basic_sim/test_ecosystem.py
```

## Opis testów

| Test | Cel | Obserwuj |
|------|-----|----------|
| `test_survivor.py` | Przetrwanie przez zarządzanie energią | Kolor automatu, czas życia |
| `test_gatherer.py` | Zbieranie zasobów | Żółte podświetlenie, logi Storage |
| `test_reproducer.py` | Rozmnażanie | Nowe automaty (cyan), licznik w HUD |
| `test_lifecycle.py` | Pełny cykl życia | Wzrost populacji, rozprzestrzenianie |
| `test_ecosystem.py` | Konkurencja wielu automatów | Dynamika populacji |

## Kolory automatów

- **Cyan** - nowo narodzony (< 20 ticków)
- **Żółty** - właśnie zebrał zasoby
- **Zielony** - wysoka energia
- **Czerwony** - niska energia

## Wymagania reprodukcji

- 5x RAW_ORE w magazynie
- Minimum 20 ticków życia
- Energia >= 10
- Mniej niż 6 automatów w okolicy 3x3
