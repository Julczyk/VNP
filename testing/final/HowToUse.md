# Instrukcja obslugi notebooka evolution.ipynb

## Wymagania

- Python 3.10+
- Jupyter Notebook lub JupyterLab
- Zainstalowane zaleznosci: `pandas`, `numpy`, `matplotlib`

```bash
pip install pandas numpy matplotlib jupyter
```

## Uruchomienie

```bash
cd testing/final
jupyter notebook evolution.ipynb
# lub
jupyter lab evolution.ipynb
```

## Struktura notebooka

### 1. Importy
Laduje wszystkie potrzebne biblioteki i modul `Simulation` z projektu.

### 2. Parametry eksperymentu
Tutaj ustawiasz parametry eksperymentu:

| Parametr | Opis | Domyslna wartosc |
|----------|------|------------------|
| `STAGES` | Liczba etapow (generacji) | 5 |
| `TO_NEXT` | Automaty przechodzace do nastepnego etapu | 5 |
| `EVAL_COUNT` | Automaty do ewaluacji (musi byc < TO_NEXT) | 3 |

**Parametry symulacji etapu (`STAGE_PARAMS`):**
- `time` - czas trwania etapu w tickach (500)
- `size` - rozmiar mapy [80, 80]
- `mutation_speed` - wspolczynnik mutacji (0.1)
- `export_frames` - lista tickow do eksportu klatek

**Parametry ewaluacji (`EVAL_PARAMS`):**
- `time` - krotszy czas (100 tickow)
- `mutation_speed` - 0 (brak mutacji)

**Program startowy (`INITIAL_PROGRAM`):**
Mozesz zmienic program SRAPL, od ktorego zaczyna sie ewolucja.

### 3. Funkcje pomocnicze
Definiuje funkcje do obliczania statystyk, selekcji i ewaluacji.
**Nie wymaga modyfikacji.**

### 4. Glowna petla eksperymentu
Uruchamia caly eksperyment:
1. Dla kazdego etapu uruchamia symulacje
2. Oblicza statystyki
3. Wybiera najlepsze automaty (na podstawie fitness)
4. Uruchamia rownolegle ewaluacje
5. Zapisuje wyniki do folderu `results/`

**Uruchom te komorke, aby rozpoczac eksperyment.**

### 5. Funkcje ewaluacji i rywalizacji
Po zakonczeniu eksperymentu mozesz uzyc:

```python
# Ewaluacja pojedynczego automatu
df = evaluate_automaton(automaton_id=1, generation=0, time=200)

# Rywalizacja miedzy automatami z roznych generacji
df = run_competition([
    {'id': 1, 'generation': 0},
    {'id': 2, 'generation': 2},
    {'id': 3, 'generation': 4}
], map_size=120, make_video=True)
```

### 6. Wykresy zbiorcze
Generuje 6 wykresow:
- Populacja w etapach
- Sredni wiek
- Srednia potomkow
- Zebrane zasoby
- Energia (wyprodukowana vs zuyta)
- Mediana zasobow z ewaluacji

### 7. Historia populacji w czasie
Wykres pokazujacy liczbe automatow w kazdym ticku dla wszystkich etapow.

### 8. Podsumowanie tekstowe
Wyswietla i zapisuje podsumowanie eksperymentu.

## Struktura wynikow

Po zakonczeniu eksperymentu w folderze `results/evolution_YYYYMMDD_HHMMSS/`:

```
results/evolution_20260218_120000/
├── generation_0/
│   ├── stage_results.csv      # Pelne dane z DataFrame
│   ├── stage_stats.json       # Statystyki podsumowujace
│   ├── programs/              # Programy przetrwalych
│   │   ├── 1.srl
│   │   ├── 2.srl
│   │   └── ...
│   ├── evals/                 # Wyniki ewaluacji
│   │   ├── 1.json
│   │   └── ...
│   └── frames/                # Klatki z symulacji
├── generation_1/
│   └── ...
├── competitions/              # Wyniki rywalizacji
│   └── comp_HHMMSS/
│       ├── frames/
│       └── competition.mp4
├── experiment_summary.png     # Wykresy zbiorcze
├── population_history.png     # Historia populacji
└── summary.txt               # Podsumowanie tekstowe
```

## Szybki start

1. Uruchom komorki 1-3 (importy, parametry, funkcje)
2. Uruchom komorke 4 (glowna petla) - to zajmie najwiecej czasu
3. Uruchom komorki 5-8 (analiza wynikow)

## Przykladowy krotki eksperyment

Dla szybkiego testu zmien parametry:

```python
STAGES = 2
TO_NEXT = 3
EVAL_COUNT = 2

STAGE_PARAMS = {
    'time': 100,
    'size': [40, 40],
    'mutation_speed': 0.1,
    ...
}
```

## Rozwiazywanie problemow

**"Brak danych - najpierw uruchom eksperyment"**
- Uruchom najpierw komorke z glowna petla (Cell 4)

**"Program nie istnieje"**
- Upewnij sie, ze eksperyment zostal ukonczony
- Sprawdz czy folder `results/` zawiera dane

**Brak filmiku z rywalizacji**
- Zainstaluj ffmpeg: `sudo apt install ffmpeg` (Linux) lub `brew install ffmpeg` (Mac)
