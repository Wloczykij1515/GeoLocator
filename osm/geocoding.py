"""
Geokodowanie nazw miejscowosci (Nominatim) i wyznaczanie obszaru OSM
do zapytan Overpass. Zero logiki UI, zero I/O na plikach.
"""
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

# WAZNE: polityka uzytkowania Nominatim wymaga user-agenta z realnym
# kontaktem (mail / link do repo), inaczej ryzykujesz zablokowanie IP.
USER_AGENT = "LocationFinder/alpha (kontakt: podaj-tu-swoj-email-lub-link-do-repo)"


class Geocoder:
    def __init__(self, user_agent=USER_AGENT, timeout=10):
        self.geolocator = Nominatim(user_agent=user_agent, timeout=timeout)

    def geokoduj_miasto(self, nazwa_miasta):
        """Zwraca obiekt lokalizacji (geopy Location) dla podanej miejscowosci."""
        nazwa_miasta = (nazwa_miasta or "").strip()
        if not nazwa_miasta:
            raise ValueError("Musisz podac nazwe miasta")

        print(f"\nSzukam: {nazwa_miasta}...")
        try:
            loc = self.geolocator.geocode(
                nazwa_miasta,
                featuretype="administrative",
                addressdetails=True
            )
            if not loc:
                raise ValueError(f"Nie znaleziono: {nazwa_miasta}")

            print(f"Znaleziono: {loc.address}")
            return loc
        except (GeocoderTimedOut, GeocoderUnavailable) as e:
            raise ConnectionError(f"Blad geokodowania: {e}")

    @staticmethod
    def pobierz_id_obszaru(location):
        """Konwertuje OSM id/typ na Overpass area id (relation/way)."""
        osm_id = location.raw["osm_id"]
        osm_type = location.raw["osm_type"]

        if osm_type == "relation":
            return 3600000000 + osm_id
        elif osm_type == "way":
            return 2400000000 + osm_id
        else:
            raise ValueError(
                f"Nieobslugiwany typ obszaru: {osm_type} "
                f"(Overpass area wymaga relation lub way)"
            )
