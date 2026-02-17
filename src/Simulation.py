# Utwórz Skrypt do przeprowadzania symulacji:
# W katalogu src utwórz plik run.py służący do przeprowadzania symulacji VNP.
# W skrypcie tym musi się znajdować funkcja:
def simulate(resources, #thresholds for resources
             time=300, #number of ticks in presentation
             starting_population = [], #automata at the beginning
             size=[80,80], #size of the world
             mutation_speed = 0, # mutation speed. 0 is none (non-mutating), passed as an argument for mutation functions
             mutation_type = "", # "disabled" disables mutations (same as mutation_speed=0), "all" all mutations are possible.
             visualize=False, #toggle visualization
             seed=42, #seed of the world
             return_data="df", #format of returned data
             make_timelapse=False, #make timelapse of simulation:
             export_frames=[] #if there are any positive integers - export frames on these ticks):
"""
Funkcja ta ma przeprowadzać symulację przez czas time, z populacją startową starting_population - która to jest listą pól
automaton z pozycją startową i programem dla automatu.
Make timelapse of simulation - wyeksportuj obraz z symulacji na każdy tick
jeżeli return_data to "df" - funkcja powinna zwracać dataframe zawierający rekordy automatów zawierające:
- ID (nadawane w kolejności zaistnienia w populacji - najpierw początkowe w kolejności w starting_population, potem kolejne w kolejności zaistnienia)
- tick (tick, w którym automat został stworzony)
- age (wiek automatu w chwili zakończenia symulacji lub jego śmierci)
- program (genom automatu)
- position (pozycja automatu w chwili stworzenia)
- total_distance_traveled (całkowita odległość przebytych przez automat)
- energy_produced (całkowita energia wyprodukowana przez automat)
- energy_consumed (całkowita energia zużyta przez automat)
- offspring_count (liczba potomków automatu)
- [resource]_gathered (całkowita ilość surowców zebranych przez automat - różne surowce - różne kolumny)
- alive_at_end (czy automat żył na końcu symulacji - to jest czy nie umarł i czy miał dodatnią energię w trakcie zakończenia symulacji)
- parent_ID (ID automatu, z którego powstał dany automat - jeżeli jest to automat startowy, parent_ID = -1)
"""
automaton = {
    program/genome[""],
    position [x,y]
}

"Pod "

"""
Cały eksperyment:

"""