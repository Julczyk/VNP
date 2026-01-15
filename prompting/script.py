import os


def polacz_pliki_tekstowe(sciezka_folderu, nazwa_wyniku="połaczony_plik.txt"):
    # Sprawdzenie czy folder istnieje
    if not os.path.exists(sciezka_folderu):
        print(f"Błąd: Folder '{sciezka_folderu}' nie istnieje.")
        return

    # Tworzymy (lub nadpisujemy) plik wynikowy
    with open(nazwa_wyniku, 'w', encoding='utf-8') as plik_wyjsciowy:
        pliki = [f for f in os.listdir(sciezka_folderu) if f.endswith('.py') or f.endswith('.txt') or f.endswith('.md')]

        if not pliki:
            print("W podanym folderze nie znaleziono plików .txt.")
            return

        for nazwa_pliku in sorted(pliki):
            sciezka_pliku = os.path.join(sciezka_folderu, nazwa_pliku)

            # Zapisujemy nagłówek sekcji
            plik_wyjsciowy.write(f"\n{'=' * 50}\n")
            plik_wyjsciowy.write(f"TREŚĆ PLIKU: {nazwa_pliku}\n")
            plik_wyjsciowy.write(f"{'=' * 50}\n\n")

            # Odczytujemy zawartość i dopisujemy do pliku zbiorczego
            try:
                with open(sciezka_pliku, 'r', encoding='utf-8') as f_input:
                    plik_wyjsciowy.write(f_input.read())
                    plik_wyjsciowy.write("\n")  # Dodatkowy odstęp po treści pliku
                print(f"Dodano: {nazwa_pliku}")
            except Exception as e:
                print(f"Błąd przy odczycie pliku {nazwa_pliku}: {e}")

    print(f"\nGotowe! Cała treść została zapisana w: {nazwa_wyniku}")


# --- KONFIGURACJA ---
# Podaj ścieżkę do folderu z plikami tekstowymi
# Użyj '.' jeśli skrypt jest w tym samym folderze co pliki
moj_folder = "./src"
polacz_pliki_tekstowe(moj_folder)