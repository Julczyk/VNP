# tytuł: Symulacja automatów samoreplikujących oraz eksploracja ich zachowania w zależności od zmieniającego się otoczenia

# Cel:

Wizja samoreplikujących się urządzeń od zapostulowania konceptu sondy Johna Von Neumanna rozpala wyobraźnię zarówno fizykom, jak i futurystom głównie za sprawą wykładniczego wzrostu. Celem naszego projektu jest uproszczone zasymulowanie takich automatów i za pomocą doboru parametrów symulacji oraz algorytmów eksploracja tego w jakich warunkach takie zjawisko jest w ogóle możliwe oraz jak zmiany w środowisku takich automatów wpływa na to, jakie jest ich optymalne zachowanie

# Ogólnikowo:
## Elementy symulacji:
- Budowa sondy: Każdy jej komponent daje jakieś możliwości, wymaga jakichś surowców do produkcji i ma jakieś koszta (np masę lub energetyczny). Każdy powinien mieć parametr skali, który liniowo skaluje jego benefity i koszta
- Program sondy: Działanie sondy określone jest programem w uproszczonym [[jezyku programowania]]. W każdym kroku symulacji sonda posiada zestaw informacji, które może zebrać z otoczenia, oraz zestaw akcji, jakie może podjąć (np wydobywanie danego surowca, poruszanie się w daną stronę, utworzenie komponentu itp)
- Świat: sondy poruszają się w "świecie" (2D lub 3D, który jest proceduralnie losowany i posiada w różnych miejscach różne surowce, przestrzenie, warunki, itp). świat powinien być parametryzowalny, by obserwować zmianę zachowania sond przy zmianie świata w którym są.

# Konkterniej:
## Automat:
Automat A jest w modelu trójką (krotką) \(E, P, L\), gdzie:
- E - Zbiór par \(K, m)
	- K - komponent
	- m - skala
- P - Program automatu nad gramatyką pewnego języka
- L - Ładunek sondy
Ponadto przechowuje wartości takie, jak masa - czyli suma mas Komponentów pomnożonych przez ich skalę oraz elementów ładunku
W praktyce typ każdy automat w symulacji będzie instancją swojej klasy

### Komponent:
- Wykonuje jedno, określone zadanie
- Ma parametry wspólne dla wszystkich typów komponentów:
	- Masa
	- Zużycie Energii (aktywne)
	- Zużycie Energii (pasywne, może być 0)
	Ponadto każdy komponent Dla każdej instancji (typu) ma zdefiniowaną skalę. Komponenty o większej skali mają większą masę i zużycie energii, ale również dają większe możliwości (np większy skaner ma większy zasięg, a większy pędnik pozwala pokonać większą odległość w kroku czasu)
- Wymaga określonych surowców do wytworzenia. W bardziej zaawansowanej symulacji może składać się z subkomponentów.

### Program automatu:
- Zarządza aktywacją i deaktywacją komponentów oraz zachowaniem aktywnego komponentu (co jest równoważne przejściu między stanami automatu)
- Zbiór możliwych do osiągnięcia stanów jest zależny od listy komponentów (intuicja: automat bez skanera nie będzie skanował otoczenia)
- W każdym kroku definiuje stan automatu na dany krok
- Ma przestrzeń zmiennych - pamięć
- Wielkość programu wpływa na skalę komponentu - komputera pokładowego
- Obiera kurs i zarządza poruszaniem się
- Ma dostęp do danych zbieranych przez sensory automatu

### Poruszanie się automatu:
- Odległość jaką automat może pokonać w kroku symulacji jest zależna od jego masy (sumy mas komponentów i ładunku) oraz skali pędnika
- Nie ma jeszcze consensusu, czy powinna być symulowana przestrzeń znana z powierzchni Ziemi, czy kosmiczna (czy wystarczy jeden impuls, czy zużycie energii rośnie liniowo z pokonaną odległością)

### "Rozmnażanie się" automatów:
Jeżeli automat w ładunku posiada wszystkie komponenty z których sam jest zbudowany, to na jego pozycji w następnym kroku pojawia się nowa instancja automatu, a te komponenty są z ładunku usuwane

### "Śmierć" automatu:
Ta kwestia jest dalej płynna, ale w najprostszej symulacji automat zostaje usunięty z symulacji, gdy nie jest w stanie wytwarzać więcej energii, niż zużywa bez aktywnego komponentu (tryb *idle*) i nie ma zmagazynowanego paliwa/energii.

## Budowa Świata:
Świat jest modelowany przez parkietaż kwadratowy (2D), gdziekażdy kafelek  (w najprostszym modelu) posiada następujące parametry:
- Zbiór par \(S, k\) - typ surowca, jego ilość
- Zbiór automatów znajdujących się w nim
Wartości początkowe dla każdego kafelka obliczane są prodecuralnie Przy pierwszym "dostrzeżeniu" go - tj. gdy pierwszy raz znajdzie się na nim dowolny automat, lub gdy będzie on w zasięgu skanera

# Algorytm genetyczny
Jako, że głównym celem projektu jest eksploracja, jak zmienia się zachowanie automatów w zależności od wielu parametrów symulacji: od częstości występowania surowców po np energochłonność danego komponentu.
Zaimplementowany zostanie więc algorytm genetyczny, który dla zdefiniowanych parametrów symulacji będzie szukał optymalnej budowy, jak i programu automatów.
Możliwe są do zaimplementowania dwa typy algorytmu genetycznego:
- startowy: Co generację uruchamiana jest symulacja z nową populacją automatów i "świeżym" światem. Dużo bardziej wymagająca obliczeniowo, ale pozwalająca uniknąć problemu początkowego wymierania
- "W symulacji" - Mutacje mogą być przekazane "dziecku" automatu przy samoreplikacji Może nieść wiele benefitów, jak bardziej organiczny proces uczenia się i ciągłej optymalizacji do zmieniających się warunków. Wymaga jednak dobrego programu na początek, który będzie w stanie od razu doprowadzić do tej replikacji

[[sonda podzial pracy]]