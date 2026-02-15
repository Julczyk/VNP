#projektowe #sonda

# Nagłówek budowy
program zaczyna się spisem części, który zaczyna się znacznikiem kluczowym `$PARTS:`
Następnie jest lista oddzielonych przecinkami liczb float, która oznacza skalę każdej części (w kolejności ID części, tj. pierwsza liczba to skala części o ID 0, druga o ID 1, itd). Spis kończy się średnikiem `;`

# Program
Właściwy program rozpoczyna się znacznikiem $PROGRAMM
## Pamięć automatu
Na potrzeby symulacji pamięć każdego automatu (niezależnie od budowy) stanowi lista/tablica stałego rozmiaru przechowująca zmienne float. Każda część ma zdefiniowaną przestrzeń do której może zapisywać zmienne - część ta nie podlega ewolucji w celu zrozumienia procesu.

### Zarezerwowane indeksy pamięci
- **X[0]** - energia automatu (0.0 - 1.0, proporcja do maksymalnej energii)
- **X[1]** - typ zasobu (wynik skanera: 0=brak, 1=IRON, 2=GOLD, 3=inne)
- **X[2]** - kierunek do najbliższego zasobu (wynik skanera, 0-3 lub -1 jeśli nie znaleziono)
- **X[3]** - dystans do najbliższego zasobu (wynik skanera, lub -1 jeśli nie znaleziono)
- **X[4-63]** - dostępne dla programu użytkownika

## Schemat działania:
1. Automat w każdym kroku uruchamia lub kontynuuje swój program. Program ma do dyspozycji pamięć automatu i za pomocą wyrażeń może go dowolnie modyfikować.
2. Program na podstawie instrukcji warunkowych lub priorytetu (liczby przypisanej do części) wybiera jedną z części do uruchomienia
3. Automat uruchamia jej funkcję z podanymi argumentami

Funkcje części są zapisane w programie jako f_n, gdzie n jest ID części
Komórki pamięci są odczytywane poprzez X\[i\], gdzie i to indeks komórki.

Wyrażenia mają prostą budowę, np `"(X[1]+(3/x[8]))"`

Niech funkcje będą uruchamiane z argumentami, np:
`f_4(X[1], 4, (X[6]-(2*X[5]))`
Liczba argumentów będzie kontrolowana na wyższym poziomie

Przypisanie:
`X[5] = (X[3] + X[8]) * 2`

blok kodu:
`{ kod }`
Komentarz:
`# komentarz`
Wywołanie dowolnej funkcji f_n kończy działanie programu (tj. całym zadaniem pojedynczego uruchomienia programu jest wywołanie jednej, odpowiedniej funkcji f_n z odpowiednimi argumentami). Z tego powodu f_n nie mogą pojawiać się w wyrażeniach, warunkach, czy pętlach

Warunek:
`IF(wyrażenie){blok}` - Kod w bloku wykonuje się wtedy i tylko wtedy, gdy wartość wyrażenia jest > 0

"pętla":
funkcjonalność pętli zapewnia słowo kluczowe "REDO". Które jest funkcją skoku do początku bloku kodu w którym się blok kodu, w którym słowo się znajduje znajduje.
Na przykład:
```
{<blok0>
	{<blok1>
		<Przypisanie>
		<Przypisanie>
		<Warunek>
		{<blok2>
			<wywołanie f_1>
		}
		<Warunek>
		{<blok3>
			REDO
		}	
	}
	<dalszy kod>
}
```
powtórzy cały blok 1, ale nie blok 0.

Szczególnym przypadkiem "REDO" jest "RESTART", które niezależnie od miejsca w kodzie zaczyna wykonywać program od początku

(to może być uwzględniane w wyższym poziomie)

Uruchomienie dowolnej funkcji f_i kończy krok czasu.
Program powinien być w stanie wznowić program w następnym kroku symulacji w miejscu (po funkcji) w którym się zatrzymał.
Cały powinien stanowić loopa - to jest po dojściu do końca programu  powinien uruchomić się on od początku.

Linie kończą się znakiem `;` w podobnej konwencji, jak w C

operatory w wyrażeniach: +, -, *, /, **


## przykładowy program
```
$PARTS:
1.0, 1.0, 2.0, 1.0, 0.5, 0.5, 1.5;

$PROGRAMM
# Konwencja pamieci:
#   X[0] = energia (0.0-1.0)
#   X[1] = typ zasobu (0=brak, 1=IRON, 2=GOLD, 3=inne)
#   X[2] = kierunek do zasobu (wynik skanera)
#   X[3] = dystans do zasobu (wynik skanera)

# Glowna petla
{
    # Jesli energia < 30% - odpoczywaj
    IF (0.3 - X[0]) {
        f_0();
    }

    # Skanuj otoczenie (zapisuje do X[1], X[2], X[3])
    f_2(1.0, 1.0);

    # Jesli zasob blisko (dystans <= 1) - zbieraj
    IF (1.5 - X[3]) {
        f_7(1.0);
    }

    # Jesli zasob daleko - idz w kierunku
    IF (X[3] - 1.5) {
        f_1(X[2], 1.0);
    }

    # Jesli nie znaleziono (dystans < 0) - losowy ruch
    IF (0.0 - X[3]) {
        f_1(0.0, 1.0);
    }

    REDO;
}
```
