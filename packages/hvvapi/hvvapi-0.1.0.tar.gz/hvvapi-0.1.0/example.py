from hvv_client import HVVClient
import os
import dotenv

dotenv.load_dotenv()


client = HVVClient(
    username=os.environ["GEOFOX_USER"],
    password=os.environ["GEOFOX_PASSWD"]
)

print("=== System Info ===")
info = client.init()
print(f"Fahrplan gültig von {info['beginOfService']} bis {info['endOfService']}")

print("\n=== Station suchen ===")
result = client.check_name("Hauptbahnhof", "STATION", max_list=3)
for station in result['results']:
    print(f"- {station['name']}, {station['city']} (ID: {station['id']})")

print("\n=== Abfahrten ===")
station = result['results'][0]
departures = client.departure_list(station, max_list=5)
print(f"Abfahrten um {departures['time']['time']} Uhr:")
for dep in departures['departures']:
    line = dep['line']
    print(f"- {line['name']} → {line['direction']}")

print("\n=== Route berechnen ===")
start = client.check_name("Hauptbahnhof", "STATION", 1)['results'][0]
dest = client.check_name("Altona", "STATION", 1)['results'][0]
route = client.get_route(start, dest)
if route.get('routes'):
    print(f"Gefunden: {len(route['routes'])} Route(n)")
    first_route = route['routes'][0]
    print(f"Dauer: {first_route.get('time', 'N/A')} Minuten")

print("\n=== Ankündigungen ===")
announcements = client.get_announcements()
if announcements.get('announcements'):
    print(f"{len(announcements['announcements'])} aktuelle Meldung(en)")

print("\n=== PLZ prüfen ===")
plz_result = client.check_postal_code("20095")
print(f"20095 im HVV-Gebiet: {plz_result.get('exists', False)}")

print("\n=== Tickets ===")
tickets = client.ticket_list()
if tickets.get('ticketInfos'):
    print(f"{len(tickets['ticketInfos'])} Ticket-Typen verfügbar")
    for ticket in tickets['ticketInfos'][:3]:
        print(f"- {ticket['tariffKindLabel']}")
