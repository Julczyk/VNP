#projektowe #sonda 

# Ogólne:
całość potrzebuje:
	Świata, którego Chunki są generowane proceduralnie.

## Obiekty:
Do świata i symulacji: Symulacja, Świat, Chunk
Robotów: Abstraktycjny Part, dziedziczące wszystkie części

Każde i w wymienionych f_i jest inne.

## Opis minimalnego zestawu części:
- Komputer pokładowy: obowiązkowa, przechowuje program, stanowi mózg automatu
	- Skala: Im większy, tym więcej programu może zrealizować w kroku symulacji
- Pędnik: Odpowiada za poruszanie się automatu w świecie
	- Funkcja: f_i(dir: int, dist:int) - poruszaj się w kierunku dir na odległość dist (a właściwie min(dist, max). Prędkość max i zużycie energii są zależne od całkowitej masy automatu (sumy mas wszystkich części)
	- Skala: Liniowo zwiększa max (dystans jaki może pokonać robot w kroku symulacji) oraz zużywaną energię
- Akumulator: Przechowuję energię. Można zrobić to na dwa sposoby - energia, paliwo. Energia jest po prostu przechowywana, paliwo, to przetwarzanie surowców, pewnie trudniejsze.
	- Funkcja(?) f_i - nie zużywa czasu. Zwraca ilość energii
	- Skala - liniowo zwiększa masę oraz pojemność. Można pokusić się o większe niż liniowe zwiększenie pojemności
- Skaner: Szuka surowców. W najprostszym wydaniu:
	- Funkcja f_i (pow, ?res): zapisuje do pamięci kierunek i odległość od najbliższego wystąpienia surowca (jeśli wiele surowców - surowca res).
	- Skala - zwiększa zasięg i/lub zmniejsza czas potrzebny na przeprowadzenie skanowania. Zwiększa oczywiście też masę i zużycie energii.
- Magazyn (lub rama): Decyduje o udźwigu, przechowuje ładunek.
	- Ładunek: Surowce, Przetworzone surowce gotowe części
	- Posiada metodę, która jest wywoływana przez inne części zwraca informację, czy jest wystarczająco dużo "miejsca" na wynik operacji innych części - tj. wydobywania, przetwarzania surowców i/lub robienia z nich części. (W przypadku niedostępności miejsca anuluje operację robienia części, wypisuje na log komunikat). W przypadku wydobycia/przetwarzania - ucina liczbę przechowywanych do max.
	- Skala. Zwiększa masę i ładowność
	- Funkcja f_i(ammount): zrzuca ładunek. Opisać, jak wybierane jest jak (może być np 1: cała ruda, 2: cały przetworzony, 3: części, 4: 1. część itp)
-  Huta: Przetwarza surowiec na przetworzony (w ostateczności można pominąć)
	- Skala: Zwiększa prędkość i zużycie energii
	- Główna właściwość/problem: Proces Huty jest niepodzielny, tj. nie może zajść, jeśli energia i/lub ruda są niewystarczające
	- Funkcja f_i(pow): Przeprowadź przerabianie surowca, powi
- Assembler: Wytwarza części z przetworzonych surowców
	- Funkcja f_i(partID): Przeprowadza operację wytworzenia części o numerze partID (gdzie każdy rodzaj wymieniony w tej liście ma inne ID)
	- Skala: zmienia masę i prędkość wytwarzania
- Panel PV - pasywne Źródło energii: Wytwarza energię
	- Należy zdecydować, czy energia jest wytwarzana zawsze, czy tylko w trybie Idle (aktywne f_0)
	- Skala: Zmienia masę i prędkość wytwarzania. Masa może być nieliniowo, śmieszniej będzie