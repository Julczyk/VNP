# Testy Interpretera SRAPL

Zestaw testów wizualnych dla interpretera SRAPL. Każdy test uruchamia symulację z wizualizacją i testuje inny aspekt interpretera.

## Uruchamianie testów

Każdy test można uruchomić osobno:

```bash
cd /home/julczyk/Dokumenty/Automaty/VNP
source .venv/bin/activate

# Test 1: Podstawowe skanowanie
python testing/interpreter_tests/test_basic_scan.py

# Test 2: Instrukcje warunkowe IF
python testing/interpreter_tests/test_if_conditions.py

# Test 3: REDO i RESTART
python testing/interpreter_tests/test_redo_restart.py

# Test 4: Zagnieżdżone bloki
python testing/interpreter_tests/test_nested_blocks.py

# Test 5: Wczytywanie z pliku .srl
python testing/interpreter_tests/test_file_loading.py

# Test 6: Wiele automatów
python testing/interpreter_tests/test_multiple_automata.py

# Test 7: Wyrażenia matematyczne
python testing/interpreter_tests/test_expressions.py
```

## Opis testów

### test_basic_scan.py
Podstawowy test - automat cyklicznie skanuje otoczenie.
- Sprawdza: parsowanie, wykonanie funkcji f_2

### test_if_conditions.py
Test instrukcji warunkowych IF.
- Sprawdza: ewaluacja warunków, wykonanie bloków warunkowych
- Obserwuj: zmiana z f_2 na f_0 gdy "energia" spada

### test_redo_restart.py
Test instrukcji sterujących przepływem.
- Sprawdza: REDO (powrót do początku bloku), RESTART (powrót do początku programu)
- Obserwuj: licznik X[1] rośnie do 3, potem reset

### test_nested_blocks.py
Test zagnieżdżonych bloków i złożonej logiki.
- Sprawdza: zagnieżdżone IF, REDO w wewnętrznym bloku
- Obserwuj: poprawna obsługa wielu poziomów zagnieżdżenia

### test_file_loading.py
Test wczytywania programów z plików .srl.
- Sprawdza: import z pliku, parsowanie sekcji $PARTS
- Wymaga: examples/basic_gatherer.srl

### test_multiple_automata.py
Test wielu automatów z różnymi programami.
- Sprawdza: niezależne wykonanie programów
- Obserwuj: różne zachowania (zbieracz, skaner, leniwy)

### test_expressions.py
Test wyrażeń matematycznych.
- Sprawdza: +, -, *, /, **, nawiasy, zmienne
- Obserwuj: wartości w pamięci X[0]-X[9]

## Poziomy logowania

Każdy test konfiguruje poziom logowania:
- `logging.DEBUG` - szczegółowe logi (przypisania, warunki, bloki)
- `logging.INFO` - podstawowe informacje (kroki, funkcje)
- `logging.ERROR` - tylko błędy

Aby zmienić poziom, edytuj linię `setup_logging(...)` w teście.

## Interpretacja wyników

### W konsoli
- `[SRAPL] DEBUG: Assignment: X[i] = value` - przypisanie wartości
- `[SRAPL] DEBUG: IF condition: value -> TRUE/FALSE` - wynik warunku
- `[SRAPL] DEBUG: >>> Block START/END` - wejście/wyjście z bloku
- `[SRAPL] DEBUG: REDO/RESTART signal caught` - obsługa sygnałów
- `[SRAPL] INFO: Step result: FunctionID.X, args=[...]` - wykonana funkcja

### W oknie wizualizacji
- Kolor automatu: zielony (wysoka energia) -> czerwony (niska energia)
- Cyjan: nowo narodzony automat (< 20 ticków)
- Żółty: automat właśnie zebrał zasoby
