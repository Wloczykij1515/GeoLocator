# GeoLocator

## 📌 Opis projektu

Celem projektu jest stworzenie prostego i użytecznego narzędzia do wyszukiwania obiektów znajdujących się w bazie OpenStreetMap.

Aplikacja pozwala wybrać miasto oraz wpisać słowo kluczowe lub kategorię obiektu, a następnie pobiera wszystkie pasujące wyniki za pomocą Overpass API. Wyniki mogą zostać wyświetlone w konsoli, zapisane do pliku CSV lub wykorzystane w dalszej analizie danych GIS.

Projekt może służyć do wyszukiwania m.in. fontann, plaż, restauracji, hoteli, parkingów, szkół, stacji paliw czy innych obiektów zapisanych w OpenStreetMap.

## 🏗️ Architektura systemu

```text
           Użytkownik
               ↓
          Wybór miasta
               ↓
              Tag
               ↓
          Overpass API
               ↓
 Konsola / CSV / Interaktywna Mapa
```

## ✨ Funkcje

* Wyszukiwanie obiektów w całym kraju
* Obsługa danych OpenStreetMap
* Automatyczne generowanie zapytań Overpass API
* Wyświetlanie współrzędnych geograficznych
* Eksport wyników do pliku CSV
* Interaktywna mapa

## 🔧 Wymagania
```bash
pip install -r requirements.txt
```
## 💡 Przykładowe wyszukiwania

Program umożliwia wyszukiwanie między innymi:

| Kategoria    | Tag OpenStreetMap  |
| ------------ | ------------------ |
| Fontanna     | amenity=fountain   |
| Plaża        | natural=beach      |
| Restauracja  | amenity=restaurant |
| Hotel        | tourism=hotel      |
| Parking      | amenity=parking    |
| Szkoła       | amenity=school     |
| Stacja paliw | amenity=fuel       |
| Szpital      | amenity=hospital   |

## ⚙️ Instalacja i konfiguracja

### 1. Klonowanie repozytorium

```bash
git clone https://github.com/TWOJ_LOGIN/osm-poi-finder.git
```

### 2. Instalacja zależności

```bash
pip install -r requirements.txt
```
## 🚀 Uruchomienie

## 📊 Zapis do pliku CSV

Każde wyszukiwanie może zostać zapisane do pliku CSV.

Format pliku:

```csv
name,latitude,longitude,type
```

Przykład:

```csv
Klaster 	Kategoria	            Nazwa	           Lat	       Lon       Odleglosc od srodka
  1	    parkingi - Legnica	    parkingi_1064   	51.206512	16.179065	         63.4
  1	    restauracja - Legnica	Had Food	        51.206687	16.178676	         44.5
  2	    restauracja - Legnica	Lara Döner Kebab	51.209543	16.167775         	 132.6

```

## 📁 Struktura projektu

```text
├── osm
    ├── geo.py              // tworzenie klastrów
    ├── geocoding.py        // geokodowanie miasta
    ├── map_builder.py      // tworzenie mapy
    └── overpass_client.py  // wysyłanie zapytań do API
├── storage
    ├── tags.json           // lokalizacja tagów OpenStreetMap
├── └── storage.py          // zapis i wczytywanie miejsc
├── cli.py                  // połączenie wszystkich funkcji w programie
├── launcher.py             // dla prostszego uruchomienia
└── main.py                 // punkt wejścia
```

## 📚 Źródło danych

Projekt wykorzystuje dane pochodzące z OpenStreetMap za pośrednictwem Overpass API.

Dane OpenStreetMap są udostępniane na licencji ODbL.

## 👤 Autor

Wloczykij1515
