"""
Interfejs uzytkownika: menu, wybor kategorii, glowna petla programu.
Ten modul spina razem geocoding / overpass_client / storage / geo / map_builder,
ale sam nie zawiera logiki geograficznej ani sieciowej.
"""
import os
import webbrowser

from osm.geocoding import Geocoder, USER_AGENT
from osm.overpass_client import OverpassClient
from storage.storage import (
    wczytaj_tagi,
    wczytaj_zapisane_dane,
    zapisz_wiele_kategorii,
    zapisz_klastry_csv,
    load_path,
    save_path
)
from osm.geo import wczytaj_dane_json, szukaj_klastrow
from osm.map_builder import stworz_mape_klastrow


def wyczysc_ekran():
    os.system("cls" if os.name == "nt" else "clear")


def naglowek(tytul):
    wyczysc_ekran()
    print("=" * 70)
    print(f"   {tytul}")
    print("=" * 70)
    print()


def menu_glowne():
    naglowek("WYSZUKIWARKA MIEJSC - ZNAJDZ KLASTRY KATEGORII")
    print("1. Pobierz dane i znajdz klastry (wiele kategorii)")
    print("2. Wyszukaj klastry z istniejacych danych")
    print("3. Wyswietl statystyki danych")
    print("4. Wyjscie")
    print("\n" + "-" * 70)


def dopasuj_kategorie(wpisana, dostepne):
    """
    Dopasowuje wpisany tekst (numer / pelna nazwa / fragment) do listy
    dostepnych kategorii. Wydzielone z main.py, gdzie ten sam kod byl
    wklejony w dwoch miejscach (wybor po pobraniu danych i wybor z pliku).
    """
    wpisana = wpisana.strip().lower()

    if wpisana.isdigit() and 1 <= int(wpisana) <= len(dostepne):
        return dostepne[int(wpisana) - 1]

    if wpisana in dostepne:
        return wpisana

    pasujace = [k for k in dostepne if wpisana in k.lower()]
    if len(pasujace) == 1:
        print(f"Dopasowano '{wpisana}' -> '{pasujace[0]}'")
        return pasujace[0]
    elif len(pasujace) > 1:
        print(f"\nZnaleziono kilka dopasowan dla '{wpisana}':")
        for idx, match in enumerate(pasujace, 1):
            print(f"  {idx}. {match}")
        num = input("Wybierz numer: ")
        if num.isdigit() and 1 <= int(num) <= len(pasujace):
            return pasujace[int(num) - 1]
        return None
    else:
        print(f"Nie znam '{wpisana}' - pomijam")
        return None


def wybierz_kategorie_z_listy(dostepne, tytul="WYBOR KATEGORII", pokaz_liczbe=None):
    """Wyswietla dostepne kategorie i zwraca liste wybranych przez uzytkownika."""
    naglowek(tytul)
    print("Dostepne kategorie:")
    print("-" * 70)
    for idx, kat in enumerate(dostepne, 1):
        etykieta = f"{idx:3d}. {kat:20s}"
        if pokaz_liczbe:
            etykieta += f"({pokaz_liczbe(kat)} miejsc)"
            print(etykieta)
        else:
            print(etykieta, end="")
            if idx % 3 == 0:
                print()
    if not pokaz_liczbe and len(dostepne) % 3 != 0:
        print()

    print("\n" + "-" * 70)
    print("Podaj kategorie (oddziel przecinkami)")
    print("Przyklad: restauracja, parkingi")
    print("-" * 70)
    wybor = input("\nKategorie: ").strip()

    wybrane = []
    for kat in wybor.split(","):
        dopasowana = dopasuj_kategorie(kat, dostepne)
        if dopasowana:
            wybrane.append(dopasowana)

    if not wybrane:
        raise ValueError("Nie wybrano zadnej kategorii")

    return wybrane


def _wypisz_klastry(clusters, radius=None):
    for i, cluster in enumerate(clusters, 1):
        naglowek_klastra = f"\nKlaster #{i}" + (f" (promien {radius}m):" if radius else ":")
        print(naglowek_klastra)
        for cat, info in cluster.items():
            # klucz "odleglosc" pochodzi z geo.szukaj_klastrow
            dist = info.get("odleglosc", 0)
            print(f"  {cat}: {info['nazwa']} (od srodka: {dist:.1f}m)")


def pobierz_i_analizuj():
    """Opcja 1: pobiera dane z Overpass i szuka klastrow."""
    try:
        tags_data = wczytaj_tagi()
        wybrane = wybierz_kategorie_z_listy(list(tags_data.keys()))
        print(f"\nWybrano: {', '.join(wybrane)}")

        naglowek("WYBOR LOKALIZACJI")
        miasto = input("Podaj nazwe miejscowosci: ").strip()

        geocoder = Geocoder(user_agent=USER_AGENT)
        loc = geocoder.geokoduj_miasto(miasto)
        area_id = geocoder.pobierz_id_obszaru(loc)

        client = OverpassClient(user_agent=USER_AGENT)
        query = client.zbuduj_zapytanie(area_id, wybrane, tags_data)
        response = client.pobierz_dane(query)

        elements = response.json().get("elements", [])
        print(f"\nPobrano {len(elements)} elementow")

        elements_by_cat = {cat: [] for cat in wybrane}
        for elem in elements:
            tags = elem.get("tags", {})
            for category in wybrane:
                for tag_dict in tags_data[category]:
                    if all(tags.get(k) == v for k, v in tag_dict.items()):
                        elements_by_cat[category].append(elem)
                        break

        print("\nZnalezione obiekty:")
        for cat, elems in elements_by_cat.items():
            print(f"  {cat}: {len(elems)}")

        zapisz_wiele_kategorii(miasto, elements_by_cat)

        print("\nSzukam klastrow...")
        categories_data = wczytaj_dane_json(save_path)

        # zapisz_wiele_kategorii zapisuje kazda kategorie pod kluczem
        # "kategoria - miasto" (patrz storage.py), wiec do szukania
        # klastrow trzeba uzyc tych samych, "pelnych" kluczy - inaczej
        # szukaj_klastrow nie znajdzie dopasowania i zglosi brak danych.
        wybrane_klucze = [f"{kat} - {miasto}" for kat in wybrane]

        radius_input = input("\nPromien w metrach (Enter = 100): ").strip()
        radius = float(radius_input) if radius_input else 100

        clusters = szukaj_klastrow(categories_data, wybrane_klucze, promien=radius)

        if clusters:
            print(f"\nZnaleziono {len(clusters)} klastrow!")
            print("\n" + "=" * 70)
            print("ZNALEZIONE KLASTRY:")
            print("=" * 70)
            _wypisz_klastry(clusters, radius)

            stworz_mape_klastrow(loc, clusters, wybrane_klucze, radius)

            if input("\nZapisac do CSV? (t/n): ").strip().lower() == "t":
                zapisz_klastry_csv(clusters)

            if input("\nOtworzyc mape? (t/n): ").strip().lower() == "t":
                webbrowser.open("mapa_klastry.html")
        else:
            print("\nNie znaleziono klastrow")
            print("\nPorady:")
            print("  - Zwieksz promien")
            print("  - Wybierz inne kategorie")
            print("  - Sprawdz czy w tym miescie sa takie miejsca")

        input("\n\nNacisnij Enter aby wrocic...")

    except Exception as e:
        print(f"\nBLAD: {e}")
        import traceback
        traceback.print_exc()
        input("\nNacisnij Enter aby wrocic...")


def szukaj_z_istniejacych_danych():
    """Opcja 2: szuka klastrow w danych juz zapisanych w dane.json."""
    try:
        if not os.path.exists(save_path):
            print("\nBrak dane.json - najpierw pobierz dane (opcja 1)")
            input("\nNacisnij Enter...")
            return

        categories_data = wczytaj_dane_json(save_path)
        available = list(categories_data.keys())

        selected = wybierz_kategorie_z_listy(
            available,
            tytul="WYSZUKIWANIE Z ISTNIEJACYCH DANYCH",
            pokaz_liczbe=lambda cat: len(categories_data[cat]),
        )
        print(f"\nWybrano: {', '.join(selected)}")

        radius_input = input("Promien w metrach (Enter = 100): ").strip()
        radius = float(radius_input) if radius_input else 100

        clusters = szukaj_klastrow(categories_data, selected, radius)

        if clusters:
            print(f"\nZnaleziono {len(clusters)} klastrow!")
            _wypisz_klastry(clusters)

            pierwszy = clusters[0]
            center_lat = sum(info["lat"] for info in pierwszy.values()) / len(pierwszy)
            center_lon = sum(info["lon"] for info in pierwszy.values()) / len(pierwszy)

            class Lokalizacja:
                pass

            loc = Lokalizacja()
            loc.latitude = center_lat
            loc.longitude = center_lon
            loc.address = "Srodek klastra"

            stworz_mape_klastrow(loc, clusters, selected, radius)

            if input("\nOtworzyc mape? (t/n): ").strip().lower() == "t":
                webbrowser.open("mapa_klastry.html")
        else:
            print("\nNie znaleziono klastrow")

        input("\nNacisnij Enter...")

    except Exception as e:
        print(f"Blad: {e}")
        import traceback
        traceback.print_exc()
        input("\nNacisnij Enter...")


def pokaz_statystyki():
    """Opcja 3: wyswietla liczbe zapisanych miejsc w kazdej kategorii."""
    try:
        if not os.path.exists(save_path):
            print("\nBrak dane.json")
            input("\nNacisnij Enter...")
            return

        naglowek("STATYSTYKI")
        data = wczytaj_zapisane_dane(save_path)

        print("Kategoria        | Liczba miejsc")
        print("-" * 35)
        total = 0
        for cat, places in data.items():
            count = len(places)
            total += count
            print(f"{cat:15s} | {count:3d}")
        print("-" * 35)
        print(f"RAZEM            | {total} miejsc w {len(data)} kategoriach")

        input("\nNacisnij Enter...")

    except Exception as e:
        print(f"Blad: {e}")
        input("\nNacisnij Enter...")


def main():
    akcje = {
        "1": pobierz_i_analizuj,
        "2": szukaj_z_istniejacych_danych,
        "3": pokaz_statystyki,
    }

    while True:
        wyczysc_ekran()
        menu_glowne()
        wybor = input("Wybierz opcje (1-4): ").strip()

        if wybor == "4":
            print("\n" + "=" * 70)
            print("   KONIEC")
            print("=" * 70)
            break
        elif wybor in akcje:
            akcje[wybor]()
        else:
            print("Niepoprawny wybor (1-4)")
            input("\nNacisnij Enter...")


if __name__ == "__main__":
    main()