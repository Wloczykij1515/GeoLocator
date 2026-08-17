"""
Wczytywanie i zapisywanie danych do plikow JSON/CSV.
Zero logiki geograficznej - tylko I/O.
"""

import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

load_path = BASE_DIR / "tags.json"
save_path = BASE_DIR / "dane.json"
json_path = save_path


def wczytaj_tagi(plik=load_path):
    """Wczytuje definicje tagow OSM dla poszczegolnych kategorii."""
    try:
        with open(plik, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Nie ma pliku {plik}")
    except json.JSONDecodeError:
        raise ValueError(f"{plik} ma zly format")


def wczytaj_zapisane_dane(plik=save_path):
    """Wczytuje wczesniej zapisane dane (surowy JSON, bez konwersji wspolrzednych)."""
    try:
        with open(plik, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def zapisz_wiele_kategorii(miasto, elements_dict, plik=save_path):
    """Dopisuje/nadpisuje kategorie w pliku dane.json na podstawie danych z Overpass."""
    zapisane = wczytaj_zapisane_dane(plik)

    print("\nZapisuje:")
    for category, elements in elements_dict.items():
        # Tworzymy klucz w formacie "kategoria - miasto"
        klucz_kategorii = f"{category} - {miasto}"

        if not elements:
            print(f"  '{klucz_kategorii}': brak danych")
            continue

        prefix = category[0].upper()
        lista = []

        for idx, elem in enumerate(elements, 1):
            tags = elem.get("tags", {})
            nazwa = tags.get("name", f"{category}_{idx}")

            if elem["type"] == "node":
                lat = elem.get("lat")
                lon = elem.get("lon")
            else:
                lat = elem.get("center", {}).get("lat")
                lon = elem.get("center", {}).get("lon")

            if lat is not None and lon is not None:
                lista.append({
                    "id": f"{prefix}{idx}",
                    "nazwa": nazwa,
                    "lat": round(lat, 6),
                    "lon": round(lon, 6)
                })

        # Zapisujemy pod kluczem kategoria - miasto
        zapisane[klucz_kategorii] = lista
        print(f"  '{klucz_kategorii}': {len(lista)} obiektow")

    with open(plik, "w", encoding="utf-8") as f:
        json.dump(zapisane, f, ensure_ascii=False, indent=2)

    print(f"\nZapisano {plik}")

def zapisz_klastry_csv(clusters, plik="klastry.csv"):
    """Eksportuje znalezione klastry do pliku CSV."""
    with open(plik, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Klaster", "Kategoria", "Nazwa", "Lat", "Lon", "Odleglosc od srodka"])
        for i, cluster in enumerate(clusters, 1):
            for cat, info in cluster.items():
                # UWAGA: klucz z geo.szukaj_klastrow to "odleglosc", nie
                # "distance_from_center" - w oryginale to zawsze dawalo 0.0
                dist = info.get("odleglosc", 0)
                writer.writerow([i, cat, info["nazwa"], info["lat"], info["lon"], round(dist, 1)])
    print(f"Zapisano '{plik}'")
