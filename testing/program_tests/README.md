# Testy programów SRAPL

Symulacja z wieloma robotami, każdy z własnym programem.

## Struktura

```
testing/program_tests/
├── run_multi_program_sim.py   # Główny skrypt symulacji
├── start_programs/            # Folder z programami .srl
│   ├── gatherer.srl          # Aktywny zbieracz
│   ├── lazy.srl              # Leniwy (duży generator)
│   └── explorer.srl          # Szybki eksplorator
└── README.md
```

## Uruchamianie

```bash
cd /home/julczyk/Dokumenty/Automaty/VNP
source .venv/bin/activate
python testing/program_tests/run_multi_program_sim.py
```

## Dodawanie własnych programów

1. Utwórz plik `.srl` w folderze `start_programs/`
2. Uruchom skrypt - nowy program zostanie automatycznie wczytany

### Format programu

```srl
$PARTS:
<engine>, <scanner>, <storage>, <collector>, <smelter>, <assembler>, <power>;

$PROGRAMM
# Twój kod SRAPL
f_2(1.0, 1.0);
```

## Zachowanie

- Każdy program dostaje jednego robota
- Roboty są rozmieszczone równomiernie na mapie
- Genom jest tworzony automatycznie z sekcji `$PARTS`
