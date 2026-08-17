"""
Tworzenie interaktywnej mapy klastrow (folium). Zero logiki geograficznej -
przyjmuje juz policzone klastry i tylko je rysuje.
"""
import folium

COLORS = [
    "red", "blue", "green", "purple", "orange", "darkred",
    "lightred", "beige", "darkblue", "darkgreen", "cadetblue",
    "darkpurple", "pink", "lightblue", "lightgreen",
    "gray", "black",
]


def stworz_mape_klastrow(location, clusters, categories, radius, plik="mapa_klastry.html"):
    print("\nRysuje mape...")

    if not clusters:
        print("Nic do wyswietlenia")
        return None

    # UWAGA: w oryginale byla martwa galaz "else: zoom=13", ktora nigdy sie
    # nie wykonywala (funkcja juz wczesniej wraca, jesli clusters jest puste).
    zoom = 14 if len(clusters) > 10 else 15

    mapa = folium.Map(
        location=[location.latitude, location.longitude],
        zoom_start=zoom,
        tiles="OpenStreetMap"
    )

    category_colors = {cat: COLORS[i % len(COLORS)] for i, cat in enumerate(categories)}

    folium.Marker(
        location=[location.latitude, location.longitude],
        popup=f"<b>Centrum: {location.address}</b>",
        tooltip="Centrum miasta",
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(mapa)

    _dodaj_znaczniki_punktow(mapa, clusters, category_colors)
    _dodaj_okregi_klastrow(mapa, clusters, radius)
    _dodaj_legende(mapa, category_colors)

    mapa.save(plik)
    print(f"Mapa zapisana jako '{plik}'")
    return mapa


def _dodaj_znaczniki_punktow(mapa, clusters, category_colors):
    wszystkie = {}
    for cluster in clusters:
        for cat, info in cluster.items():
            wszystkie.setdefault(cat, []).append(info)

    for cat, points in wszystkie.items():
        color = category_colors.get(cat, "gray")
        for point in points:
            popup_text = f"""
            <div style="font-family: Arial, sans-serif;">
                <b>{point['nazwa']}</b><br>
                <i>Kategoria: {cat}</i><br>
                <hr>
                Lat: {point['lat']:.6f}<br>
                Lon: {point['lon']:.6f}
            </div>
            """
            folium.Marker(
                location=[point["lat"], point["lon"]],
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"{point['nazwa']} ({cat})",
                icon=folium.Icon(color=color, icon="info-sign", prefix="fa")
            ).add_to(mapa)


def _dodaj_okregi_klastrow(mapa, clusters, radius):
    for i, cluster in enumerate(clusters):
        if len(cluster) < 2:
            continue

        center_lat = sum(info["lat"] for info in cluster.values()) / len(cluster)
        center_lon = sum(info["lon"] for info in cluster.values()) / len(cluster)
        cat_list = ", ".join(cluster.keys())

        folium.Circle(
            location=[center_lat, center_lon],
            radius=radius,
            color="yellow",
            fill=True,
            fill_opacity=0.15,
            weight=2,
            popup=f"<b>Klaster #{i + 1}</b><br>Kategorie: {cat_list}<br>Liczba: {len(cluster)}"
        ).add_to(mapa)

        folium.Marker(
            location=[center_lat, center_lon],
            popup=folium.Popup(
                f'<a href="https://www.google.com/maps?q={center_lat},{center_lon}" '
                f'target="_blank">Otworz w Google Maps</a>',
                max_width=300
            ),
            icon=folium.DivIcon(
                html=f'<div style="background-color: yellow; border-radius: 50%; '
                     f'width: 30px; height: 30px; display: flex; align-items: center; '
                     f'justify-content: center; font-weight: bold; border: 2px solid black;">'
                     f'{i + 1}</div>'
            )
        ).add_to(mapa)


def _dodaj_legende(mapa, category_colors):
    legenda = """
    <div style="position: fixed; bottom: 50px; left: 50px; z-index:1000;
                background-color: white; padding: 15px; border: 2px solid grey;
                border-radius: 8px; font-family: Arial, sans-serif;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
        <h4 style="margin: 0 0 10px 0;">Legenda kategorii:</h4>
    """
    for cat, color in category_colors.items():
        legenda += f"""
        <div style="margin: 3px 0;">
            <span style="display: inline-block; width: 14px; height: 14px;
                        background-color: {color}; border-radius: 50%;
                        margin-right: 8px; border: 1px solid #666;"></span>
            <span style="font-size: 14px;">{cat}</span>
        </div>
        """
    legenda += """
        <hr style="margin: 8px 0;">
        <div style="font-size: 12px; color: #666;">
            Zolte kola = klastry<br>
            Numery = ID klastrow
        </div>
    </div>
    """
    mapa.get_root().html.add_child(folium.Element(legenda))
