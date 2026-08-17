"""
Budowanie zapytan Overpass QL i pobieranie danych z API (z fallbackiem
na kilka serwerow Overpass). Zero logiki UI, zero zapisu do plikow.
"""
import requests

DEFAULT_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]


class OverpassClient:
    def __init__(self, user_agent, endpoints=None, http_timeout=(10, 120), query_timeout=110):
        self.headers = {"User-Agent": user_agent, "Accept": "application/json"}
        self.endpoints = endpoints or DEFAULT_ENDPOINTS
        self.http_timeout = http_timeout
        self.query_timeout = query_timeout

    def zbuduj_zapytanie(self, area_id, categories, tags_data):
        """Sklada zapytanie Overpass QL dla wybranych kategorii tagow."""
        query_filters = ""
        for category in categories:
            for tag_dict in tags_data[category]:
                for klucz, wartosc in tag_dict.items():
                    query_filters += f'  nwr["{klucz}"="{wartosc}"](area.searchArea);\n'

        return f"""
[out:json][timeout:{self.query_timeout}];
area({area_id})->.searchArea;
(
{query_filters});
out center;
"""

    def pobierz_dane(self, query):
        """Wysyla zapytanie, probujac kolejne serwery az do skutku."""
        print("\nWysylam zapytanie...")

        for i, url in enumerate(self.endpoints, 1):
            try:
                print(f"  Proba {i}/{len(self.endpoints)}: {url}")
                res = requests.post(
                    url,
                    data={"data": query},
                    headers=self.headers,
                    timeout=self.http_timeout
                )
                if res.status_code == 200:
                    print("Otrzymano dane")
                    return res
                elif res.status_code == 429:
                    print("Serwer przeciazony, probuje inny...")
                    continue
                else:
                    print(f"  Serwer zwrocil status {res.status_code}, probuje inny...")
            except requests.exceptions.RequestException as e:
                print(f"Blad: {e}")
                continue

        raise RuntimeError("Wszystkie serwery Overpass nie odpowiadaja")
