# HVV API Client

Eine einfache Python-Library für die HVV Geofox GTI API.

## Installation

```bash
uv sync
```

## Verwendung

```python
from hvv_client import HVVClient

# Client initialisieren
client = HVVClient(
    username="DEIN_USERNAME",
    password="DEIN_PASSWORD"
)

# Systeminformationen abrufen
info = client.init()
print(info)

# Station suchen
result = client.check_name("Hauptbahnhof", "STATION", max_list=5)
station = result['results'][0]

# Abfahrten abrufen
departures = client.departure_list(station, max_list=10)
for dep in departures['departures']:
    print(f"{dep['line']['name']} → {dep['line']['direction']}")

# Route berechnen
start = client.check_name("Hauptbahnhof", "STATION", 1)['results'][0]
dest = client.check_name("Altona", "STATION", 1)['results'][0]
route = client.get_route(start, dest)
```

## Verfügbare Methoden

### `init()`
Systeminformationen und Fahrplangültigkeit abrufen.

### `check_name(name, type_="STATION", max_list=10)`
Stationen, Adressen oder POIs suchen.
- `type_`: `"STATION"`, `"ADDRESS"`, `"POI"`, `"UNKNOWN"`

### `get_route(start, dest, time=None)`
Route zwischen zwei Orten berechnen.
- `start`, `dest`: Station-Objekte von `check_name()`
- `time`: Optional `{"date": "heute", "time": "jetzt"}`

### `departure_list(station, max_list=10, time=None)`
Abfahrten einer Haltestelle abrufen.
- `station`: Station-Objekt von `check_name()`
- `time`: Optional `{"date": "heute", "time": "jetzt"}`

### `departure_course(departure_id)`
Verlauf einer Fahrt abrufen.

### `list_stations(data_id=None)`
Alle Haltestellen auflisten.

### `list_lines(data_id=None)`
Alle Linien auflisten.

### `get_announcements()`
Aktuelle Bekanntmachungen und Störungen.

### `check_postal_code(postal_code)`
Prüfen, ob PLZ im HVV-Gebiet liegt.

### `get_station_information(station)`
Zusätzliche Informationen zu einer Haltestelle.

### `tariff_meta_data()`
Tarif-Metadaten abrufen.

### `tariff_zone_neighbours()`
Nachbarzonen von Tarifzonen.

### `ticket_list()`
Liste aller verfügbaren Tickets.

### `get_vehicle_map(bbox)`
Fahrzeugpositionen in einem Bereich.
- `bbox`: Bounding Box als Dictionary

## Beispiel

Siehe `example.py` für ein vollständiges Beispiel.

## API-Dokumentation

Die vollständige API-Dokumentation findest du in `manuals/manual.md` und `manuals/openapi.json`.

## Authentifizierung

Die API verwendet HMAC-SHA1-Authentifizierung. Du benötigst einen Benutzernamen und ein Passwort von HBT GmbH.
