import json
import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# konwersja współrzędnych - używam tego wszędzie
transformer = Transformer.from_crs("EPSG:4326", "EPSG:2180", always_xy=True)


def wczytaj_dane_json(plik):
    """Ładuje JSON i przelicza współrzędne na metry."""
    with open(plik, "r", encoding="utf-8") as f:
        dane = json.load(f)

    kategorie = {}
    for nazwa, punkty in dane.items():
        if not punkty:
            print(f"Uwaga: {nazwa} jest pusta")
            kategorie[nazwa] = pd.DataFrame()
            continue
            
        df = pd.DataFrame(punkty)
        
        # no to liczymy
        try:
            x, y = transformer.transform(df["lon"].values, df["lat"].values)
            df["x"] = x
            df["y"] = y
            kategorie[nazwa] = df
        except Exception as e:
            print(f"Błąd przy {nazwa}: {e}")
            kategorie[nazwa] = df

    return kategorie


def szukaj_klastrow(kategorie, lista_kategorii, promien=100.0, min_kategorii=2):
    """
    Szuka miejsc gdzie różne kategorie są blisko siebie.
    Czasem daje fałszywe alarmy ale generalnie działa.
    """
    # najpierw filtrujemy
    dostepne = {}
    for kat in lista_kategorii:
        if kat in kategorie and not kategorie[kat].empty:
            dostepne[kat] = kategorie[kat]
        else:
            print(f"Uwaga: {kat} brak danych")
    
    if len(dostepne) < min_kategorii:
        print(f"Potrzeba co najmniej {min_kategorii} kategorii")
        return []
    
    # przygotowuje punkty
    wszystkie_punkty = []
    info_o_punktach = {}
    
    for kat, df in dostepne.items():
        for _, row in df.iterrows():
            x, y = row["x"], row["y"]
            klucz = (x, y)
            info_o_punktach[klucz] = {
                "kategoria": kat,
                "nazwa": row.get("nazwa", f"{kat}_punkt"),
                "lat": row["lat"],
                "lon": row["lon"],
                "x": x,
                "y": y
            }
            wszystkie_punkty.append([x, y])
    
    if not wszystkie_punkty:
        return []
    
    wszystkie_punkty = np.array(wszystkie_punkty)
    drzewo = cKDTree(wszystkie_punkty)
    
    klastry = []
    przetworzone = set()
    
    for i, punkt in enumerate(wszystkie_punkty):
        if tuple(punkt) in przetworzone:
            continue
            
        # szukam sąsiadów
        indeksy = drzewo.query_ball_point(punkt, r=promien)
        
        if len(indeksy) < min_kategorii:
            continue
        
        kategorie_w_okolicy = {}
        punkty_w_okolicy = []
        
        for idx in indeksy:
            x, y = wszystkie_punkty[idx]
            klucz = (x, y)
            if klucz in info_o_punktach:
                info = info_o_punktach[klucz]
                kat = info["kategoria"]
                if kat not in kategorie_w_okolicy:
                    kategorie_w_okolicy[kat] = []
                kategorie_w_okolicy[kat].append(info)
                punkty_w_okolicy.append(info)
                przetworzone.add(klucz)
        
        if len(kategorie_w_okolicy) >= min_kategorii:
            # środek ciężkości
            cx = np.mean([p["x"] for p in punkty_w_okolicy])
            cy = np.mean([p["y"] for p in punkty_w_okolicy])
            
            klaster = {}
            for kat, punkty in kategorie_w_okolicy.items():
                # biorę najbliższy środka
                najblizszy = min(punkty, key=lambda p: np.sqrt((p["x"] - cx)**2 + (p["y"] - cy)**2))
                klaster[kat] = {
                    "nazwa": najblizszy["nazwa"],
                    "lat": najblizszy["lat"],
                    "lon": najblizszy["lon"],
                    "odleglosc": np.sqrt((najblizszy["x"] - cx)**2 + (najblizszy["y"] - cy)**2)
                }
            
            # tylko jak wszystkie kategorie są
            if set(klaster.keys()) == set(dostepne.keys()):
                klastry.append(klaster)
    
    # pozbywam się duplikatów
    unikalne = []
    widziane = set()
    for klaster in klastry:
        klucz = tuple(sorted([info["nazwa"] for info in klaster.values()]))
        if klucz not in widziane:
            widziane.add(klucz)
            unikalne.append(klaster)
    
    # sortuję po ilości
    unikalne.sort(key=lambda x: len(x), reverse=True)
    
    return unikalne


def licz_odleglosci(kategorie, kategoria_bazowa, max_odl=None):
    """
    Dla każdego punktu z kategorii bazowej liczy odległości do innych.
    Czasem używam tego do szybkiego sprawdzenia co jest blisko.
    """
    if kategoria_bazowa not in kategorie:
        raise ValueError(f"Nie ma takiej kategorii: {kategoria_bazowa}")
    
    bazowa_df = kategorie[kategoria_bazowa]
    if bazowa_df.empty:
        print(f"Pusta kategoria: {kategoria_bazowa}")
        return pd.DataFrame()
    
    # buduję drzewa dla każdej kategorii
    drzewa = {}
    for kat, df in kategorie.items():
        if df.empty:
            continue
        if "x" not in df.columns or "y" not in df.columns:
            continue
        drzewa[kat] = cKDTree(df[["x", "y"]].values)
    
    if not drzewa:
        print("Brak danych")
        return pd.DataFrame()
    
    wspolrzedne = bazowa_df[["x", "y"]].values
    suma_odl = np.zeros(len(bazowa_df))
    licznik = np.zeros(len(bazowa_df), dtype=int)
    
    for kat, drzewo in drzewa.items():
        if kat == kategoria_bazowa:
            continue
        
        odleglosci, _ = drzewo.query(wspolrzedne, k=1)
        
        if max_odl is not None:
            odleglosci = np.minimum(odleglosci, max_odl)
            licznik += (odleglosci < max_odl).astype(int)
        
        bazowa_df[f"odl_do_{kat}_m"] = np.round(odleglosci, 1)
        suma_odl += odleglosci
    
    bazowa_df["suma_odleglosci"] = np.round(suma_odl, 1)
    
    # domyślnie liczę co jest w promieniu 30m
    if max_odl is None:
        prog = 30.0
        for col in bazowa_df.columns:
            if col.startswith("odl_do_"):
                licznik += (bazowa_df[col] < prog).astype(int)
        bazowa_df["liczba_w_okolicy"] = licznik
    
    return bazowa_df.sort_values(by="suma_odleglosci", ascending=True)


def znajdz_w_promieniu(kategorie, kategoria_bazowa, promien=30.0, min_miejsc=1):
    """
    Szuka miejsc w promieniu dla każdego punktu bazowego.
    Używam tego głównie do raportów.
    """
    if kategoria_bazowa not in kategorie:
        raise ValueError(f"Nie ma takiej kategorii: {kategoria_bazowa}")
    
    bazowa_df = kategorie[kategoria_bazowa]
    if bazowa_df.empty:
        return pd.DataFrame()
    
    wyniki = []
    
    for idx, row in bazowa_df.iterrows():
        wsp = np.array([[row["x"], row["y"]]])
        w_okolicy = {}
        suma = 0
        
        for kat, df in kategorie.items():
            if kat == kategoria_bazowa or df.empty:
                continue
            
            wspolrzedne = df[["x", "y"]].values
            if len(wspolrzedne) == 0:
                continue
            
            drzewo = cKDTree(wspolrzedne)
            odl, ind = drzewo.query(wsp, k=1)
            
            if odl[0] <= promien:
                w_okolicy[kat] = {
                    "nazwa": df.iloc[ind[0]]["nazwa"],
                    "odl": round(odl[0], 1)
                }
                suma += odl[0]
        
        if len(w_okolicy) >= min_miejsc:
            rezultat = {
                "nazwa": row["nazwa"],
                "lat": row["lat"],
                "lon": row["lon"],
                "suma": round(suma, 1),
                "ile": len(w_okolicy)
            }
            
            for kat, info in w_okolicy.items():
                rezultat[f"odl_do_{kat}_m"] = info["odl"]
                rezultat[f"nazwa_{kat}"] = info["nazwa"]
            
            wyniki.append(rezultat)
    
    return pd.DataFrame(wyniki)


def mapa_ciepla(kategorie):
    """
    Tworzy dane do mapy ciepła - każde punkt ma wagę na podstawie liczby sąsiadów.
    Używam tego do wizualizacji w folium.
    """
    wszystkie = []
    
    for kat, df in kategorie.items():
        if df.empty:
            continue
        tmp = df.copy()
        tmp["kategoria"] = kat
        wszystkie.append(tmp)
    
    if not wszystkie:
        return pd.DataFrame()
    
    polaczone = pd.concat(wszystkie, ignore_index=True)
    
    wsp = polaczone[["x", "y"]].values
    drzewo = cKDTree(wsp)
    
    wagi = []
    for i, p in enumerate(wsp):
        # liczę ile jest w promieniu 50m, bez siebie
        indeksy = drzewo.query_ball_point(p, r=50.0)
        waga = len([j for j in indeksy if j != i])
        wagi.append(waga)
    
    polaczone["waga"] = wagi
    return polaczone[["lat", "lon", "waga", "kategoria"]]


# szybki test
if __name__ == "__main__":
    try:
        dane = wczytaj_dane_json("dane.json")
        print(f"\nZaładowano: {len(dane)} kategorii")
        
        # testowo pierwsze 3 kategorie
        test = list(dane.keys())[:3]
        if len(test) >= 2:
            klastry = szukaj_klastrow(dane, test, 100)
            print(f"\nZnaleziono {len(klastry)} klastrow:")
            for i, k in enumerate(klastry, 1):
                print(f"\nKlaster {i}:")
                for kat, info in k.items():
                    print(f"  {kat}: {info['nazwa']}")
        
    except FileNotFoundError:
        print("Nie znaleziono pliku dane.json")