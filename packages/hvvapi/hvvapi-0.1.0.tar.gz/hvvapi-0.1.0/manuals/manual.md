# GTI Anwenderhandbuch

#### öffentlicher Teil

## Version 63.

#### für API-Version 63

```
HBT Hamburger Berater Team
Stadthausbrücke 3, 20355 Hamburg
Tel: +49 40 369779-
Fax: +49 40 369779-
info@hbt.de, http://www.hbt.de
```
HBT GmbH; Version 63.

24. November 2025 Seite 1 von 107


## Inhaltsverzeichnis

## HBT GmbH; Version 63.

## HBT GmbH; Version 63.

## HBT GmbH; Version 63.

## HBT GmbH; Version 63.




- 1 Allgemeines
   - 1.1 Format und Felder eines HTTP-Paketes
      - 1.1.1 TraceID (UUID)
   - 1.2 Formate zur Codierung des HTTP-Bodys
      - 1.2.1 JSON
      - 1.2.2 XML
   - 1.3 Authentifikation
   - 1.4 Request und Response
      - 1.4.1 Feldversion: API-Version
      - 1.4.2 Feldlanguage: Systemsprache
      - 1.4.3 FeldfilterType: Datenfilter
      - 1.4.4 Felder parsen
   - 1.5 Fachbegriffe des ÖPNV
   - 1.6 Datenformate
      - 1.6.1 Datumsformate (date, time, GTITime, dateTime)
      - 1.6.2 Koordinaten und ihr Format
      - 1.6.3 Line Keys
      - 1.6.4 Zeitumstellung
      - 1.6.5 Exakte Dokumentation in der WADL
   - 1.7 Soll-Fahrplan
   - 1.8 Echtzeit
   - 1.9 Inaktivität
   - 1.10 Zugriffsbeschränkung
   - 1.11 Funktionsübersicht
   - 1.12 Klassendiagramme
- 2 Bereitgestellte Methoden
   - 2.1 Methodeinit.
      - 2.1.1 Beispiel
   - 2.2 MethodecheckName
      - 2.2.1 CNRequest
      - 2.2.2 CNResponse
      - 2.2.3 Beispiel
   - 2.3 MethodegetRoute.
      - 2.3.1 ContinousSearch
- HBT GmbH; Version 63.
         - 24. November 2025 Seite 1 von
      - 2.3.2 Tarifinformationen
      - 2.3.3 Penalties
      - 2.3.4 DesiredType
      - 2.3.5 DesiredCarrier
      - 2.3.6 Beispiel der Umsetzung aufgeofox.hvv.de
      - 2.3.7 GRResponse
      - 2.3.8 Echtzeit
      - 2.3.9 Beispiel
   - 2.4 MethodedepartureList
      - 2.4.1 DLRequest
      - 2.4.2 DLResponse
      - 2.4.3 Filter
      - 2.4.4 Beispiel
   - 2.5 MethodegetTariff
      - 2.5.1 TariffRequest
      - 2.5.2 TariffResponse
      - 2.5.3 Beispiel
   - 2.6 MethodedepartureCourse
      - 2.6.1 DCResponse
      - 2.6.2 Beispiel
   - 2.7 MethodelistStations
      - 2.7.1 LSRequest
      - 2.7.2 LSResponse
      - 2.7.3 Beispiel
   - 2.8 MethodelistLines
      - 2.8.1 LLRequest
      - 2.8.2 LLResponse
      - 2.8.3 Beispiel
   - 2.9 MethodegetAnnouncements
      - 2.9.1 AnnouncementRequest
      - 2.9.2 AnnouncementResponse
      - 2.9.3 Beispiel
   - 2.10 MethodegetIndividualRoute.
      - 2.10.1 IndividualRouteRequest
      - 2.10.2 IndividualRouteResponse
      - 2.10.3 Beispiel
- HBT GmbH; Version 63.
         - 24. November 2025 Seite 2 von
   - 2.11 MethodengetVehicleMapundgetTrackCoordinates
      - 2.11.1 VehicleMapRequest
      - 2.11.2 VehicleMapResponse
      - 2.11.3 Beispiel
      - 2.11.4 TrackCoordinatesRequest
      - 2.11.5 TrackCoordinatesResponse
      - 2.11.6 Beispiel
   - 2.12 MethodecheckPostalCode
      - 2.12.1 Beispiel
   - 2.13 MethodegetStationInformation.
      - 2.13.1 StationInformationRequest
      - 2.13.2 StationInformationResponse
      - 2.13.3 Beispiel
   - 2.14 MethodetariffZoneNeighbours
      - 2.14.1 TariffZoneNeighboursRequest
      - 2.14.2 TariffZoneNeighboursResponse
      - 2.14.3 Beispiel
   - 2.15 MethodetariffMetaData.
      - 2.15.1 TariffMetaDataRequest
      - 2.15.2 TariffMetaDataResponse
      - 2.15.3 Beispiel
   - 2.16 MethodesingleTicketOptimizer.
      - 2.16.1 SingleTicketOptimizerRequest
      - 2.16.2 SingleTicketOptimizerResponse
   - 2.17 MethodeticketList
      - 2.17.1 TLRequest
      - 2.17.2 TLResponse
      - 2.17.3 Beispiel
- 3 Beispiele zur Implementierung von Clients
   - 3.1 Objective-C (iOS)
      - 3.1.1 Erstellung der Signatur
      - 3.1.2 Verarbeitung von JSON
   - 3.2 Java und PHP
   - 3.3 Python
   - 3.4 Typescript
- HBT GmbH; Version 63.
         - 24. November 2025 Seite 3 von
- 4 Wichtige Hinweise zur Umsetzung
   - 4.1 Das FeldidinSDName
   - 4.2 Caching von Stationen und Linien
   - 4.3 Implementierung: Icons vom Icon Service
      - 4.3.1 Vehicle Icons
      - 4.3.2 Line Icons
      - 4.3.3 Miscellaneous Icons
- 5 Status-Codes und Error-Codes
- A Tabellen
- B Listings
- C Versionshistorie
- HBT GmbH; Version 63.
         - 24. November 2025 Seite 4 von


## 1 Allgemeines

#### Das GEOFOX Thin Interface, im folgenden GTI genannt, ist eine REST-ähnliche Web-Service-

#### Schnittstelle für GEOFOX. Die Kommunikation erfolgt per HTTP, im Body werden Requests

#### und Responses in den Formaten JSON oder XML transportiert. Sie löst die bisherige SOAP-

#### Schnittstelle ab und befindet sich in laufender Entwicklung.

#### Eine Motivation zur Entwicklung des GTI als SOAP-Nachfolger war die zusätzliche Eig-

#### nung für mobile Geräte, dabei sollte die Eignung zur Server-Server-Kommunikation natürlich

#### beibehalten werden.

#### Für die mobile Nutzung war neben Overheadreduktion und guter Parsbarkeit die Erweite-

#### rung der Authentifizierung um dynamische IPs wichtig.

### 1.1 Format und Felder eines HTTP-Paketes

#### Alle Methoden werden per HTTP-POST aufgerufen und mit dem UTF-8-codierten Request

#### im HTTP-Body gesendet. In Tabelle 1 werden die Felder eines Geofox-HTTP-Paketes genannt.

#### Über den HeaderX-Platformkann die Plattform des Klienten angegeben werden. Wenn mög-

#### lich sollteX-Platformeinen Wert aus Tabelle 2 enthalten.

```
Header-Name Typ Default-Wert/Beschreibung
Content-Type application/jsonoder text/plain, wird
application/xml nicht unterstützt, daher
ist dieses Feld obligatorisch
Accept-Encoding gzip, deflate Unkomprimiert
Accept application/jsonoder Gewünschter Content-Type
application/xml der Antwort
Benutzerdefinierte Header-Felder :
geofox-auth-signature Signatur, siehe Kapitel 1.3 Authentifikation
geofox-auth-user Application-ID (wird
von der HBT GmbH vergeben)
geofox-auth-type Algorithmus zur HmacSHA
Signaturerstellung
X-Platform (Optional) Betriebssystem des Klienten, ungesetzt
z.B.ios,android,winphone,web,mobile
Tabelle 1: Felder eines Geofox-HTTP-Paketes
```
```
X-Platform Beschreibung
ios für iOS Apps
android für Android Apps
winphone für Windows Phone Apps
web für Desktop Webseiten
mobile für mobile Webseiten
Tabelle 2: Mögliche Werte fürX-Platform
```
HBT GmbH; Version 63.

24. November 2025 Seite 5 von 107


#### Ein Beispiel für einen GTI-HTTP-POST-Request zeigt Listing 1.

#### Listing 1: HTTP-Post

```
1 POST /gti/public/init HTTP/1.
2 Accept: application/json
3 Content-Type: application/json;charset=UTF-
4 geofox-auth-type: HmacSHA
5 geofox-auth-user: gnw
6 geofox-auth-signature: G9sE5wm9vpYu441iJ7Ag5vPKerw=
7 User-Agent: JUnitTest
8 X-TraceId: f144f2e3-c5f6-42fd-bf3d-27be4ede899b
9 Content-Length: 2
```
10 Host: gti.geofox.de

11 Connection: Keep-Alive

12

13 {}

#### 1.1.1 TraceID (UUID)

#### Als TraceID wird das optionale FeldX-TraceIdim HTTP-Header bezeichnet, es identifiziert

#### einen Request. Zu verwenden ist eine UUID gemäß RFC4122. Weil alle Backendsysteme diesen

#### Parameter erhalten und loggen, wird ein Debuggen einzelner Request erleichtert – es empfiehlt

#### sich folglich eine Verwendung und Ausgabe derselben in sämtlichen Fehlerprotokollen.

### 1.2 Formate zur Codierung des HTTP-Bodys

#### Die Kommunikation (Requests und Responses) im HTTP-Body kann in den Formaten JSON

#### oder XML codiert sein.

#### 1.2.1 JSON

#### In Listing 2 wird ein Beispiel von einemCNRequestim JSON-Format gegeben.

#### Listing 2:CNRequestfür Haltestelle „Altona“

```
1 {
2 "coordinateType": "EPSG_4326",
3 "maxList": 1,
4 "theName": {
5 "name": "Altona",
6 "type": "STATION"
7 }
8 }
```
#### In Listing 3 wird ein Beispiel für eineCNResponseim JSON-Format gegeben.

#### Listing 3:CNResponsefür Haltestelle „Altona“

```
1 {
2 "results": [
3 {
```
HBT GmbH; Version 63.

24. November 2025 Seite 6 von 107


```
4 "name": "Altona",
5 "id": "Master:80953",
6 "type": "STATION",
7 "city": "Hamburg",
8 "coordinate": {
9 "x": 9.93454,
```
10 "y": 53.

11 }

12 }

13 ],

14 "returnCode": "OK"

15 }

#### 1.2.2 XML

#### Listing 4 zeigt ein Beispiel für einCNRequestim XML-Format.

#### Listing 4:CNRequestfür Haltestelle „Altona“

```
1 <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
2 <gti:CNRequest xmlns:gti="http://www.geofox.de/schema/geofoxThinInterface">
3 <theName>
4 <name>Altona</name>
5 <type>STATION</type>
6 </theName>
7 <maxList>1</maxList>
8 <coordinateType>EPSG_4326</coordinateType>
9 </gti:CNRequest>
```
#### Listing 5 zeigt ein Beispiel für einCNResponseim XML-Format.

#### Listing 5:CNResponsefür Haltestelle „Altona“

1 <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
2 <gti:CNResponse xmlns:gti="http://www.geofox.de/schema/geofoxThinInterface">
3 <returnCode>OK</returnCode>
4 <results>
5 <name>Altona$<$/name>
6 <city>Hamburg</city>
7 <id>Master:80953</id>
8 <type>STATION</type>
9 <coordinate>
10 <x>9.93454</x>

11 <y>53.552405</y>

12 </coordinate>

13 </results>

14 </gti:CNResponse>

### 1.3 Authentifikation

#### Wenn die Zugriffe von einem oder mehreren Servern mit statischer IP-Adresse geschieht, können

#### diese Adressen zur Authentifizierung des Benutzers verwendet werden. Um innerhalb einer

#### authorisierten IP-Adresse zwischen unterschiedlichen Benutzern unterscheiden zu können, kann

HBT GmbH; Version 63.

24. November 2025 Seite 7 von 107


#### zusätzlich über das HTTP-Header-Feldgeofox-auth-userein Benutzername mit angegeben

#### werden.

#### Alternativ gibt es insbesondere für dynamische IP-Adressen die Möglichkeit, sich mittels

#### Benutzernamen und Signatur über die HTTP-Header Feldergeofox-auth-userundgeofox-

#### auth-signaturezu authentifizieren. Die zu verwendende Signatur ist ein hash-basierender

#### Code (hash-based message authentication code gemäß RFC2104, kurz HMAC) aus Request-

#### Body und UTF-8 kodiertem Passwort. Der Hashcode wird dabei mit dem Verfahren SHA

#### gebildet und Base64-codiert gesendet. Beispielcode zur Erstellung einer Signatur in Objective-C

#### (iOS) und Java (z.B. für Android) ist in Abschnitt 3 zu finden.

#### Die Einrichtung von Benutzerkonten erfolgt durch die HBT GmbH.

#### Der Entwickler von Client-Applikation hat dafür zu sorgen, dass das Passwort im Client

#### für Dritte nicht leicht auffindbar und sicher gespeichert ist. Dazu gehört der Einsatz von Ver-

#### schlüsselung und/oder Code-Obfuscation.

### 1.4 Request und Response

#### Alle Methoden nehmen nur ein Objekt als Request und geben nur ein Objekt als Response

#### zurück, es gibt für jede Methode ein eigenes Request- und Response-Objekt.

#### Alle Requests erben (i.d.R. direkt) von BaseRequestTypeund erben damit dessen Fel-

#### derlanguage,versionundfilterType, die hier besprochen werden. Alle Responses erben

#### (stets direkt) vonBaseResponseTypeFelder zur Fehlerbehandlung, die in Kapitel 5 gesondert

#### behandelt wird.

#### 1.4.1 Feldversion: API-Version

#### Über dieses Feld ist eine Abwärtskompatibilität implementiert. In jedem Request ist im Feld

#### versioninBaseRequestTypedie Versionsnummer der API zu übermitteln, die dem Client

#### bekannt ist, so dass der Server die Response auf diese API-Version zuschneiden kann.

#### Der Default-Wert für dasversion-Feld ist 1 – Da diese Version jedoch mitlerweile veraltet

#### ist, sollte in jedem Request die gewünschte Version mit übertragen werden. Eine kleine API-

#### Versionshistorie kann aus der Versionshistorie dieser Dokumentation in Anhang C abgeleitet

#### werden.

#### 1.4.2 Feldlanguage: Systemsprache

#### Die default-Sprache des Systems für übersetzbare Textfelder, wie Anmerkungen und Namen von

#### Bereichen und Fahrkarten, ist deutsch. Sie kann mit dem optionalen Feldlanguageexplizit

#### aufen(für englisch) oderde(für deutsch) gesetzt werden.

#### Dies betrifft die Ausgabe von Anmerkungen, Ticketnamen, HVV-Zonen und ähnlichem,

#### nicht jedoch die Namen von Haltestellen.

HBT GmbH; Version 63.

24. November 2025 Seite 8 von 107


#### 1.4.3 FeldfilterType: Datenfilter

#### Der Geofox-Datenbestand ist sehr groß und umfasst viele Haltestellen, Linien und Tarifgebiete.

#### Enthalten sind neben dem öffentlichen Personennahverkehr des HVV auch Fernverkehrsver-

#### bindungen der Deutschen Bahn und diversen Bus- und Bahnlinien in Schleswig-Holstein und

#### anderen Bereichen.

#### Eine Besonderheit sind die ausbrechenden Linien; das sind die, die prinzipiell im HVV

#### liegen, die aber ein paar letzte Stationen samt Endhaltestelle außerhalb des HVV-Bereiches

#### haben. Das Teilstück der Linie im HVV-Bereich zählt dann als Linie im HVV. Beispiele dafür

#### sind alle Regionalbahnen oder Buslinien wie die 410 und die 412.

#### Das GTI bietet die Möglichkeit, über einen Filter die betrachtete Region einzustellen. Der-

#### zeit gibt es die beiden Möglichkeiten, entweder ausschließlich den HVV-Bereich (inklusive HVV-

#### Teilstücken von ausbrechenden Linien) oder den gesamten, ungefilterten Geofox-Datenbestand

#### zu betrachten.

#### Dies wird in allen Requests über das vonBaseRequestTypegeerbte EnumfilterType

#### festgelegt, es ist vom TypFilterType. Derzeit gibt es die WerteHVV_LISTEDundNO_FILTER.

#### Die öffentliche Schnittstelle ist dabei auf HVV-Linien beschränkt, es wird daher immer auf den

#### WertHVV_LISTEDgesetzt und die Reichweite damit auf das Gebiet des HVVs beschränkt.

#### 1.4.4 Felder parsen

#### Im Client sind Parser so zu implementieren, dass eine Erweiterung (auch innerhalb einer API-

#### Version) nicht zu Fehlfunktionen führt. Empfehlungen für Parser werden in Kapitel 3 gegeben.

### 1.5 Fachbegriffe des ÖPNV

#### Es wird eine kleine Einführung in die Begriffe des GTI-Routings gegeben. Oft ist die Abgrenzung

#### nicht ganz scharf, die Bedeutung ergibt sich jedoch stets aus dem Kontext.

#### • Eine Haltestelle (Typstation) ist ein Ort, an dem von einem Verkehrsmittel ein- und

#### ausgestiegen werden kann.

#### • Knoten (TypchangingNode) sind Mengen von Haltestellen, zwischen denen eine Um-

#### steigemöglichkeit besteht. Der Hauptbahnhof ist ein solcher Knoten, einige seiner Halte-

#### stellen sind „Hbf. Nord”, „Hbf. Süd”, „Hbf. ZOB”. Optional haben manche Haltestellen

#### eineplatform, dies ist z.B. in einem großen Bahnhof das Gleis, von dem ein Zug fährt.

#### Knoten finden lediglich in der MethodedepartureListVerwendung.

#### • POIs sind Points of Interest wie z.B. der Flughafen oder die Alster.

#### • Dem System bekannte Orte (Adressen, Haltestellen, POIs,...) können als Start und als

#### Destination verwendet werden, ihr TypSDNameträgt deren Abkürzungen im Namen.

#### • Eine Linie (TypLine) ist eine U/S/A/R/Bus/...-Linie, genauer: eine Liste von Haltestel-

#### len.

#### • Eine allgemeine Strecke zwischen zwei Orten heißt auchRoute.

HBT GmbH; Version 63.

24. November 2025 Seite 9 von 107


#### • EinScheduleist eineRoutezu einem Zeitpunkt mit feststehenden Verkehrsmitteln.

#### • Eine Fahrt unterteilt sich in Abschnitte, in mehrereScheduleElements. Diese Abschnitte

#### können Fußwege/Fahrradfahrten, fahrten mit dem ÖPNV-Verkehrsmitteln und Umstei-

#### gefußwege sein.

#### • Mit den ermäßigten Online-Tickets ist eine Rabatt-Aktion des HVV gemeint, die für

#### online erworbene Tickets eine Ermäßigung gibt. Sie läuft seit März 2013 auf unbestimmte

#### Zeit.

### 1.6 Datenformate

#### 1.6.1 Datumsformate (date, time, GTITime, dateTime)

#### Einige Felder bezeichnen Tage, sie werden üblicherweise mitdatebezeichnet, Uhrzeiten im Feld

#### time. Es werden dabei Strings gespeichert, die sehr flexibel sind: Beispiele sind27.03.2014,

#### montagsundheutefürdatesowie18:05, 14-16, jetztfürtime. Der TypGTITimekom-

#### biniert diese, er enthält genau ein Felddateund ein Feldtime.

#### Der TypdateTimeenthält Datum und Zeitpunkt in einem Feld. Es ist im Pattern

#### yyyy-MM-dd’T’HH:mm:ss.SSSZzu codieren.

#### Ein Beispiel dafür ist2015-09-21T08:24:06.634+0200.

#### 1.6.2 Koordinaten und ihr Format

#### Koordinaten geben einen Punkt auf der Erdoberfläche in zweidouble-Werten an, sie werden

#### z.B. in JSON mit"coordinate:{*:9.962371, "y:53.569501}notiert.

#### Das GTI arbeitet per default mit Koordinaten im Format EPSG-4326 (WGS84). Unter-

#### stützt wird außerdem EPSG-31467 (System nach Gauß/Krüger, angewendet in Zone 3). Das

#### Enum CoordinateTypesteuert dies, die zugehörigen Werte sindEPSG_ 4326 undEPSG_ 31467.

#### Zusätzlich kann der Client den gewünschten Koordinatentyp in der Antwort vorgeben.

#### 1.6.3 Line Keys

#### Die verschiedenen Linien von z.B. Bussen und U-Bahnen werden über ID-Strings identifiziert.

#### Diese folgen dem SchemaL:N_BoderL:N_B_X, dabei steht dasNfür den Namen der Linie,

#### dasBsteht für den Betreiber, dasXist ein optionaler Zusatz. Eine Linie hat keine Richtung,

#### also auch keine Anfangs- und Endhaltestelle. Beispiele für Line Keys sindVHH:569_VHHfür die

#### Buslinie 569,ZVU-DB:S1_ZVU-DB_S-ZVUbezeichnet die S-Bahn S1.

#### 1.6.4 Zeitumstellung

#### In der Schnittstelle gibt es einige Felder, die als Zeit in Minuten nach einem bestimmten Zeit-

#### punkt angegeben sind. Diese sind immer als reale Minuten zu interpretieren. Beispiel: Wenn

#### eine departureList um 01:30 Uhr am Tag der Zeitumstellung im Frühjahr abgefragt wird, und

#### die Antwort enthält eine Abfahrt (Departure) mit der Zeit (time) 120 min., dann ist hier

HBT GmbH; Version 63.

24. November 2025 Seite 10 von 107


#### nicht etwa 03:30 Uhr gemeint, sondern 04:30 Uhr, da die Zeit von 2 Uhr auf 3 Uhr an diesem

#### Tag vor gestellt wurde und somit zwischen 01:30 Uhr und 04:30 Uhr nur 120 min. vergangen

#### sind.

#### 1.6.5 Exakte Dokumentation in der WADL

#### Aufhttps://gti.geofox.de/gti/public?_wadl&_type=xmlist eine Beschreibung des GTI

#### im Format WADL (Web App Description Language^1 ) abrufbar. Die WADL-Datei gibt Auskunft

#### über die verfügbaren Methoden, deren URL, zulässige MIME-Typen sowie Struktur von Re-

#### quest und Response. Im Zweifel gilt diese WADL als Referenz.

### 1.7 Soll-Fahrplan

#### Es ist möglich, den aktuell für die Fahrplanauskunft verwendeten Soll-Fahrplan unter der URL

#### https://gti.geofox.de/gti/data/Plandaten.zipabzurufen. Voraussetzung dafür ist die

#### Authentifizierung mittels des GTI-Accounts per Basic Auth. Der Fahrplan liegt im ISA-Format

#### (IVU.pool-Standard-ASCII-Schnittstelle) der Firma IVU Traffic Technologies AG vor. Für wei-

#### tere Informationen zum Soll-Fahrplan und dem Datenformat bitte anapi@hochbahn.dewen-

#### den.

### 1.8 Echtzeit

#### Einige der bereitgestellten Methoden (z.B.getRoute,departureList,departureCourse)

#### stellen zusätzlich zu den Plandaten auch Echtzeitinformationen zur Verfügung. Diese Verspä-

#### tungen, Ausfälle, Verstärkerfahrten und Gleisänderungen werden in GTI generell in den Fel-

#### derndelay (bzw. depDelayundarrDelay), cancelled, extra undrealtimePlatform

#### angegeben. Zur Nutzung von Echtzeitinformationen müssen hierbei in den jeweiligen Metho-

#### den (getRoute,departureList,getVehicleMap) die diesbezüglichen Flags (realtimebzw.

#### useRealtime), wie in der Spezifikation beschrieben, gesetzt werden.

### 1.9 Inaktivität

#### Wir behalten uns vor, inaktive Benutzer nach einem Jahr zu löschen.

### 1.10 Zugriffsbeschränkung

#### Benutzern, welche im Schnitt mehr als einen API-Aufruf pro Sekunde tätigen, wird der API-

#### Zugang temporär gesperrt.

(^1) XML basiertes Dateiformat zur Beschreibung von REST-Webservices, analog zur WSDL
HBT GmbH; Version 63.

24. November 2025 Seite 11 von 107


### 1.11 Funktionsübersicht

#### Die Tabelle 3 gibt eine Übersicht über die aktuellen Methoden des APIs.

```
Methode, URL Beschreibung
Init
/gti/public/init
```
```
Abrufen allgemeiner Systeminformationen
```
```
checkName
/gti/public/checkName
```
```
Finden von für das System verwertbaren Orten
```
```
getRoute
/gti/public/getRoute
```
```
Finden einer optimalen Route
```
```
departureList
/gti/public/departureList
```
```
Finden der Abfahrten einer Haltestelle
```
```
getTariff
/gti/public/getTariff
```
```
Finden von Tarif-Informationen zu einer Route
```
```
departureCourse
/gti/public/departureCourse
```
```
Anfragen des Verlaufes (Haltestellenabfolge) einer
Fahrt
listStations
/gti/public/listStations
```
```
Ermöglicht Erstellung und Pflege eines
Haltestellen-Caches im Client
listlines
/gti/public/listLines
```
```
Anfragen aller Linien, die seit einer Datenversion eine
Änderung erfahren haben
getAnnouncements
/gti/public/getAnnouncements
```
```
Anfragen von aktuellen Bekanntmachungen wie
Fahrplanabweichungen
checkPostalCode
/gti/public/checkPostalCode
```
```
Überprüfung, ob eine Postleitzahl im HVV Gebiet liegt
```
```
getVehicleMap
/gti/public/getVehicleMap
```
```
Gibt alle Fahrzeuge und deren Bewegung in einer
bestimmten Gegend zu einer bestimmten Zeit zurück
getTrackCoordinates
/gti/public/getTrackCoordinates
```
```
Gibt die Koordinaten zu bestimmten
Streckenabschnitten zurück
getIndividualRoute
/gti/public/getIndividualRoute
```
```
Komplementäre Mobilität: Finden einer optimalen
individuellen Route
getStationInformation
/gti/public/getStationInformation
```
```
Abruf zusätzlicher Informationen einer Haltestelle
```
```
tariffMetaData
/gti/public/tariffMetaData
```
```
Liefert diverse statische Tarif-Informationen
```
```
singleTicketOptimizer
/gti/public/singleTicketOptimizer
```
```
Tarifberater für Gruppen
```
```
ticketList
/gti/public/ticketList
```
```
Liefert eine Liste der Fahrkarten im HVV mit diversen
Eigenschaften
Tabelle 3: Methoden des aktuellen APIs
```
HBT GmbH; Version 63.

24. November 2025 Seite 12 von 107


### 1.12 Klassendiagramme

#### Die folgenden Klassendiagramme geben eine Übersicht zum Aufbau von Requests und Respon-

#### ses. Einige Details sind dabei zur besseren Übersicht nicht genannt. Die Grafiken sind lediglich

#### als Verständniserleichterung gedacht, im Zweifel ist die WADL als Referenz anzusehen.

#### Abbildung 1: GTI-Requests

HBT GmbH; Version 63.

24. November 2025 Seite 13 von 107


#### Abbildung 2: GTI-Responses

HBT GmbH; Version 63.

24. November 2025 Seite 14 von 107


## 2 Bereitgestellte Methoden

#### Im Folgenden werden die verfügbaren Methoden vorgestellt.

#### Jede Methode hat nur ein Objekt als Parameter und gibt nur ein Objekt zurück, welches

#### genau auf die Methode zugeschnitten ist. Die MethodecheckName (kurz „CN”) nimmt ein

#### CNRequestund gibt einCNResponsezurück. Dieses Namensschema gilt dabei für andere Me-

#### thoden analog. Die Requests erben Felder vonBaseRequestType, Responses erben Felder (zur

#### Fehlerbehandlung) vonBaseResponseType. Diese und ihre Felder sind in Abschnitt 1.4 vorge-

#### stellt und werden bei der folgenden Besprechung der einzelnen GTI-Methoden nicht wiederholt,

#### obwohl sie natürlich vorhanden sind und ggf. auch ausgewertet werden.

#### Tritt kein Fehler auf, enthält jede Response das Key/Value-Paar"returnCode":"OK".

### 2.1 Methodeinit.

#### URL:/gti/public/init

#### Ein Aufruf voninitliefert zu einem (leeren)InitRequesteineInitResponse, die ledig-

#### lich allgemeine Informationen wie Fahrplangültigkeit (Beginn, Ende) und GEOFOX Versions-

#### Informationen liefert.

#### Die in der WADL zusätzlich genannten Properties haben derzeit keine Funktion. Für zu-

#### künftige APIs ist eine Abfragemöglichkeit für die Properties angedacht, z.B. ob der gerade

#### verwendete Fahrplan die „Weihnachtseigenschaft” hat – ob der derzeitige Fahrplan im Ausnah-

#### meintervall der Weihnachtsfeiertage liegt.

#### 2.1.1 Beispiel

#### Das Beispiel in den Listings 6 und 7 zeigt den einzig möglichenInitRequest. Dieser ist leer,

#### zurückgegeben werden einige Informationen des aktuellen Fahrplanes.

#### Listing 6:InitRequest

```
1 {}
```
#### Listing 7:InitResponse

```
1 {
2 "returnCode": "OK",
3 "beginOfService": "10.10.2017",
4 "endOfService": "10.12.2017",
5 "id": "03.29.01.21.01",
6 "dataId": "29.74.01",
7 "buildDate": "10.10.2017",
8 "buildTime": "13:14:38",
9 "buildText": "Regelfahrplan 2017"
```
10 }

HBT GmbH; Version 63.

24. November 2025 Seite 15 von 107


### 2.2 MethodecheckName

#### Die MethodecheckNameliefert einen vom System verwertbaren, eindeutigen Ort mit allen

#### Details. Dieser kann z.B. anhand von Adressen, Stationen oder POIs gefunden werden. Die

#### allgemeine Funktionsweise kann als Vervollständigung von unvollständigenSDNames angesehen

#### werden. Alle anderen im System auftretendenSDNames sind vollständig. Deren Input ist daher

#### typischerweise der Output voncheckName, tatsächlich benötigt werden jedoch nur die Felder

#### id,typesowiecombinedNameodernameundcity.

#### 2.2.1 CNRequest

#### URL:/gti/public/checkName

#### Die Methode hat verschiedene Anfragetypen, die gestellt werden können. In Tabelle 4 wer-

#### den die Felder vorgestellt. Nicht alle davon werden bei jedem Abfragetyp ausgewertet.

```
Feld Typ Beschreibung
theName SDName Ein unvollständigerSDName, enthält Suchinformationen
maxList integer Maximale Anzahl an Ergebnissen
maxDistance integer Für STATION: Maximale Entfernung in Metern, die eine Haltestelle von der
angegeben Koordinate entfernt liegen darf (max. 3000m)
coordinateType CoordinateType Bezugssystem der Koordinaten,EPSG_ 4326 (default) oderEPSG_ 31467.
tariffDetails boolean Entscheidet, ob die Response Tarif-Informationen enthält
allowTypeSwitch boolean Entscheidet, ob bei Anfragen vom Typ STATION, ADDRESS, POI auch
andere Ergebnistypen als intheNameangefordert zurückgegeben werden
dürfen
Tabelle 4:CNRequest
```
#### Alle Felder des TypsSDName(Tabelle 6) sind in der WADL als optional gekennzeichnet. Je

#### nach Anfragetyp, der durch das EnumSDType(Tabelle 5) inSDNamedefiniert wird, müssen

#### jedoch bestimmte Felder gefüllt sein. Der TypTariffDetailswird in Tabelle 7 vorgestellt.

HBT GmbH; Version 63.

24. November 2025 Seite 16 von 107


```
WertSDType
/ Anfragetyp
```
```
Erforderliche
Felder intheName
```
```
Response
```
```
STATION nameundcityoder
combinedNameoder
coordinate
```
```
Bei gesetzten FeldernnameundcityodercombinedNameeine
Liste aller Haltestellen, die mit dem gesetzten Namen/Stadt
übereinstimmen. FallsallowTypeSwitchden Werttruehat,
sind auch Adressen und POIs möglich. Bei gesetzter
coordinateenthält die Response eine Liste von bis zu 10
Haltestellen, die sich im Umkreis vonmaxDistanceMeter
von der angegebenen Koordinate befinden
COORDINATE coordinateund
optionallayer
```
```
Liefert zur angegebenen Koordinate die nächstgelegene
Adresse. Die maximale Entfernung beträgt 100 Meter.
ADDRESS nameundcityoder
combinedName
```
```
Eine Liste aller Adressen, die mit dem gesetzten
Namen/Stadt übereinstimmen. FallsallowTypeSwitchden
Werttruehat, sind auch Haltestellen und POIs möglich
POI nameundcityoder
combinedName
```
```
Eine Liste aller POIs, die mit dem gesetzten Namen/Stadt
übereinstimmen. FallsallowTypeSwitchden Werttruehat,
sind auch Haltestellen und Adressen möglich
UNKNOWN nameundcityoder
combinedName
```
```
Eine Liste aller übereinstimmender Haltestellen, Adressen
und POIs
Tabelle 5: Der EnumSDType
```
```
Feld Typ Beschreibung
name string Name des Ortes
city string Stadt
combinedName string Kombinierter Name (ausnameundcity)
id string ID-Nummer des Ortes
type SDType Ein Enum, das den Typ des Ortes angibt. Mögliche Werte:
UNKNOWN(hier default),STATION,ADDRESS,POI,COORDINATE.
Dieses Feld entscheidet über den Anfragetyp voncheckName.
coordinate Coordinate Koordinaten der geografischen Position
layer integer zusätzlich zur Koordinate noch der Layer für
unterirdische/überirdische Punkte (ab Version 53). Wird im
Fußwegrouting ausgewertet.
tariffDetails TariffDetails Tarifrelevante Eigenschaften des Ortes, z.B. in welcher
Tarifzone sie liegt (Tabelle 7)
serviceTypes Liste vonstring Liste der hier verkehrenden Verkehrsmittel (z.B:u,bus)
hasStationInformation boolean Können zusätzliche Informationen über diese Haltestelle über
getStationInformationabgefragt werden? (Seit API
Version 28)
provider string Information über Provider der Activity-Station (Seit API
Version 58)
address string Adressangabe, hauptsächlich verwendet für POIs (Seit API
Version 59)
Tabelle 6: Die Felder vonSDName
```
HBT GmbH; Version 63.

24. November 2025 Seite 17 von 107


```
Feld Typ Beschreibung
innerCity boolean Entscheidet die Zugehörigkeit der Haltestelle zum
Hamburger Innenstadtbereich
city boolean Veraltet: Entscheidet eine Stadtzugehörigkeit für nicht mehr
existente Tickets (City-Karte wurde durch Kurzstrecke
ersetzt)
cityTraffic boolean Entscheidet die Zugehörigkeit zum lokalen Stadtverkehr, wie
ihn z.B. Bad Bramstedt oder Stade haben
gratis boolean Entscheidet, ob an dieser Haltestelle ausschließlich kostenlose
Linien (z.B. Parkshuttlebusse zum Volksparkstadion)
verkehren
greaterArea boolean Entscheidet die Zugehörigkeit zum HVV-Großbereich
shVillageId int Orts-ID im SH-Tarif
shTariffZone int SH-Tarif Zone, in der der Ort liegt
tariffZones Liste vonint Liste der Zonen, in denen der Ort liegt
regions Listevonint Veraltet
counties Liste vonstring Liste der Kreise, in denen der Ort liegt
rings Liste vonstring Liste der Ringe, in denen der Ort liegt
fareStage boolean Entscheidet, ob hier eine Zahlgrenze vorliegt
fareStageNumber int Mehrere Haltestellen können zu einem Zahlgrenzknoten
(KTN) zusammenfallen. Dessen ID ist hier angegeben.
tariffNames Liste vonstring Liste der Tarifarten (HVV, SH)
uniqueValues boolean Veraltet
Tabelle 7: Die Felder des TypsTariffDetails(inSDName)
```
#### 2.2.2 CNResponse

#### DieCNResponseliefert eine Liste von Orten, genauer: vonRegionalSDNames. Der TypSDNa-

#### me(mit seinen Feldernid,name,city,combinedName,type,coordinate,tariffDetails

#### undserviceTypes) wurde zurRegionalSDNameerweitert um die Felderdistanceundti-

#### me, die bei einem STATION-Request (zusätzlich zur Liste der Haltestellen in der Nähe einer

#### gegebenen Koordinate) auch deren jeweilige Entfernung in Metern Luftlinie und in Gehminuten

#### übermittelt.

#### Interessant für den AnfragetypSTATIONist das FeldserviceTypesinSDName, welches seit

#### API Version 16 existiert. Es enthält zu den zurückgegeben Orten die ggf. dort verkehrenden

#### Fahrzeugtypen wie U-Bahn, Schiff und ähnliche.

#### 2.2.3 Beispiel

#### In Listings 8 und 9 werden Ergebnisse zum Begriff „Christuskirche” angefragt. Eine Haltestelle

#### wird gefunden, die mit ihren Details zurückgegeben wird.

#### Listing 8:CNRequestzum Begriff „Christuskirche“

1 {

2 "version":63,

3 "theName":{

4 "name":"Christuskirche",

5 "type":"UNKNOWN"
6 },

7 "maxList":1,

HBT GmbH; Version 63.

24. November 2025 Seite 18 von 107


```
8 "coordinateType":"EPSG_4326"
9 }
```
#### Listing 9:CNResponsezum Begriff „Christuskirche“

```
1 {
2 "returnCode": "OK",
3 "results": [
4 {
5 "name": "Christuskirche",
6 "city": "Hamburg",
7 "combinedName": "Christuskirche",
8 "id": "Master:84902",
9 "type": "STATION",
```
10 "coordinate": {

11 ...

12 },
13 "serviceTypes": [

14 "bus",

15 "u"

16 ],

17 "hasStationInformation": true

18 }

19 ]

20 }

HBT GmbH; Version 63.

24. November 2025 Seite 19 von 107


### 2.3 MethodegetRoute.

#### URL:/gti/public/getRoute

#### Die MethodegetRouteführt eine Verbindungssuche durch. Die Parameterstart,destund

#### das optionaleviasind dabei vom TypSDNameund am einfachsten dem Output voncheck-

#### Namezu entnehmen, da dort alle erforderlichen Felder bestimmt werden. Der Request wird in

#### Tabelle 8 vorgestellt.

HBT GmbH; Version 63.1

24. November 2025 Seite 20 von 107


```
Feld Typ Beschreibung
start SDName Start
dest SDName Ziel (engl. destination)
via SDName Via (die Route soll hierüber verlaufen)
time GTITime Zeit (Bedeutung durchtimeIsDeparture)
timeIsDeparture boolean Entscheidettimeals Abfahrtszeit (sonst: Ankunftszeit)
numberOfSchedules integer Gewünschte Anzahl auszugebender Fahrten, evtl. werden nur weniger
gefunden. Sie verlaufen alle zur gleichen Zeit auf unterschiedlichen
Routen. Wenn „0” angegeben wird, wird der Wert Serverseitig auf
„1” gesetzt.
tariffDetails boolean Entscheidet, ob die Response Tarif/Ticket-Informationen zur Route
enthalten sein soll
continousSearch boolean Garantiert, dass alle Abfahrtszeiten der Routen zu oder nachtime
(Abfahrtszeit) liegen bzw. alle Ankunftszeiten vor oder zutime
(Ankunftszeit) liegen, siehe Anmerkungen unten. Nicht sinnvoll
kombinierbar mitschedulesBefore/-After, da durch sietime
bereits auf diese Weise interpretiert wird.
contSearchByServiceId ContSearchByServiceId Abhängig vontimeIsDeparturewird die nächste/vorherige Route
gesucht (Erläuterung in Tabelle 9). Ist dieses Feld gesetzt, so werden
continousSearchund die Uhrzeit-Komponente vontimeignoriert.
(seit API Version 29)
coordinateType coordinateType Bezugssystem der Koordinaten,EPSG_ 4326 (default) oder
EPSG_ 31467.
schedulesBefore integer Anzahl zusätzlicher Routen, die zeitlich vor der gesuchten optimalen
Route starten. Diese können unterschiedlichen Streckenverlauf haben.
Nicht kombinierbar mitnumberOfSchedules
schedulesAfter integer Anzahl zusätzlicher Routen, die zeitlich nach der optimalen Route
starten. Diese können unterschiedlichen Streckenverlauf haben. Nicht
kombinierbar mitnumberOfSchedules
returnReduced boolean Entscheidet, ob zusätzlich ermäßigte Preise für elektronische
Fahrkarten zurückgegeben werden
tariffInfoSelector Liste ausTariff
InfoSelector
```
```
Gibt an, welche Tarifinformationen zurückgeliefert werden sollen.
Siehe dazu einen folgenden Abschnitt
penalties Penalty Siehe dazu einen folgenden Abschnitt
returnPartialTickets boolean Gibt an, ob Fahrkarten für Abschnitte der Gesamtroute berechnet
werden sollen
realtime RealtimeType Konfiguriert die Berücksichtigung von Echtzeitinformationen bei der
Routenberechnung. (seit API Version 19)
intermediateStops boolean Gibt an, ob auch die Zwischenhalte einer Fahrt zurückgegeben
werden sollen. (seit API Version 24)
useStationPosition boolean Default:true. Gibt an, ob die Fahrt auch an Haltestellen in der Nähe
der Start- und Zielhaltestelle enden darf. (seit API Version 27)
forcedStart SDName Die Fahrt beginnt hier. Muss eine Haltestelle sein. (seit API Version
27)
forcedDest SDName Die Fahrt beginnt hier. Muss eine Halstestelle sein. (seit API Version
27)
toStartBy SimpleServiceType Gibt an, wie zur Starthaltestelle zu gelangen ist. Überschreibt für die
Starthaltestelle den Wert der PenaltyToStartStationBy. Darf nur
FOOTPATHoderBICYCLEsein. (seit API Version 27)
toDestBy SimpleServiceType Gibt an, wie zur Endhaltestelle zu gelangen ist. Überschreibt für die
Endhaltestelle den Wert der PenaltyToStartStationBy. Darf nur
FOOTPATHoderBICYCLEsein. (seit API Version 27)
returnContSearchData boolean Es werden zusätzliche Objekte zurückgegeben, welche die Suche nach
einer späteren/vorherigen Route vereinfachen (seit API Version 29)
withPaths boolean Gibt an ob die Path Daten zurückgegeben werden sollen (seit API
Version 51)
useBikeAndRide boolean Gibt an, ob Bike and Ride Stationen bei der Suche berücksichtigt
werden sollen (seit API Version 58)
Tabelle 8:GRRequest
```
#### Bei Anfrage mehrerer Verbindungen mittels Setzen des FeldesnumberOfScheduleswerden

#### die (optimale) Verbindung und evtl. weitere weniger optimale Verbindungen mit abweichender

HBT GmbH; Version 63.1

24. November 2025 Seite 21 von 107


#### Route zurückgegeben.

#### Bei Anfrage mehrerer Verbindungen mittels Setzen der FelderschedulesBefore/-After

#### werden (zeitlich nach der optimalen Verbindung) weitere berechnet, die jedoch unterschiedli-

#### chen Streckenverlauf haben können. Je nach Bedarf kann eine der beiden Varianten gewählt

#### werden; ein kombiniertes Setzen dieser Felder ist aufgrund der inhaltlichen Verschiedenheit

#### nicht möglich.

#### 2.3.1 ContinousSearch

#### DiecontinousSearchdient kurz gesagt dazu, eine Art Weitersuche umzusetzen. Hierbei ist

#### gemeint, ausgehend von einer Fahrt die darauffolgende oder vorherige Fahrt zu erhalten. Da

#### die Nutzung und die Auswirkungen nicht ganz intuitiv sind, sind zum FeldcontinousSearch

#### und dessen Nutzung nachfolgende Anmerkungen zu machen:

#### Es wird im Falltruedie erste Fahrt um oder nach der angegebenen Abfahrtszeit genommen,

#### unabhängig davon, ob bei einer späteren Abfahrt eine kürzere Fahrzeit gefunden wird.

#### Als Beispiel seien zu einer gewünschten Abfahrtszeit von 10:00 Uhr zwei Routen gegeben:

#### Fahrt 1 startet um 10:00 Uhr und dauert 60 Minuten, Fahrt 2 startet um 10:31 und dauert 30

#### Minuten (kommt also eine Minute später an und ist deutlich kürzer).

#### Im FallcontinousSearch==truewird Fahrt 1 besser bewertet und die Wartezeit als Rei-

#### sezeit gezählt, im anderen Fall Fahrt 2.

#### Damit ist die Möglichkeit geschaffen, zu einer bekannten Fahrt (mit Abfahrttime) die nach-

#### folgende Fahrt zu ermitteln: Man setzecontinousSearchauftrueund wähle als Abfahrtszeit

#### time+1min, ganz analog kann im Fall einer gegebenen Ankunftszeit mitcontinousSearchauf

#### trueundtime-1mindie vorherige Fahrt gefunden werden.

#### Dieses Vorgehen stellt sich im Bezug auf Echtzeit jedoch nicht als komplett fehlertolerant

#### dar. Man stelle sich das Beispiel vor, bei dem eine Fahrt eine Verspätung hat. Wendet man auf

#### diese Fahrt das oben beschriebene Verfahren an, kann es dazu kommen, dass eben genau diese

#### Fahrt als nachfolgende Fahrt ermittelt wird, da die Abfahrt durch die Echtzeit verschoben ist,

#### ein Kreisschluss kann entstehen.

#### Aus diesem Grund kann man ab Version 29 auch das FeldreturnContSearchDataset-

#### zen. Die inSchedule.contSearchBeforeundSchedule.contSearchAfterzurückgegebe-

#### nen Objekte eignen sich dann, um die vorherige, bzw. nächste Fahrt zu ermitteln. Diese Methode

#### ist in Bezug auf Echtzeit fehlertoleranter alscontinousSearch, welche im Fall von Verspätun-

#### gen Probleme hat die nächst-spätere Route zu ermitteln. Da das Verfahren neben der Nutzung

#### desSchedule.contSearchBefore- bzw.Schedule.contSearchAfter-Objekts auch von der

#### richtigen Nutzung desTimeIsDeparture-Feldes abhängig ist, soll folgende Erklärung das Vor-

#### gehen weiter erklären:

#### Möchte man nach vorherigen Fahrten suchen, setzt man dasSchedule.contSearchBefore

#### alsContSearchByServiceId ein, sowietimeIsDeparture=false. Umgekehrt, wenn man

#### die nachfolgende Fahrt bekommen möchte, setzt man dasSchedule.contSearchAfter als

#### ContSearchByServiceIdein, sowietimeIsDeparture=true.

HBT GmbH; Version 63.1

24. November 2025 Seite 22 von 107


```
Vorhaben ContSearchByServiceId-Typ TimeIsDeparture
Vorherigen Route suchen contSearchBefore false
Nächste Route suchen contSearchAfter true
Tabelle 9:ContSearch-TimeIsDeparture Zusammenhang
```
#### 2.3.2 Tarifinformationen

#### Die Liste ausTariffInfoSelectorim FeldtariffInfoSelectorgibt an, welche Tarife und

#### Kartenarten für jedesSchedulezurückgegeben werden sollen. Der TypTariffInfoSelector

#### wird in Tabelle 10 vorgestellt.

```
Typ Typ Ergebnis
tariff String Name des Tarifs (hvv,sh,all). Der Wertallbezieht die
Filterangaben auf alle Tarife. Wird nur der hvv-Tarif
gefiltert und die Verbindung hat nur SH-Tarif, dann werden
alle Tickets zurückgegeben. Gilt analog bei Filtern von SH,
wenn Verbindung nur hvv. (default:hvv)
tariffRegions Boolean Entscheidet, ob Tarifbereiche (-zonen, -ringe, -kreise)
zurückgegeben werden (default:true)
kinds Liste ausinteger Die zurückzugebenden Kartenarten. Bei einer leeren Liste
vonkindsundgroupswerden alle gültigen Karten
zurückgegeben.
groups Liste ausinteger Die zurückzugebenden Kartengruppen. Bei einer leeren Liste
vonkindsundgroupswerden alle gültigen Karten
zurückgegeben. Seit API Version 54.
blacklist Boolean Entscheidet, ob Tickets gewhitelistet oder geblacklistet
werden sollen. Whitelisting: Gibt alle Tickets zurück, die
entweder denkindsoder dengroupsentsprechen.
Blacklisting: Gibt alle Tickets zurück, die weder denkinds
noch dengroupsentsprechen. (default:false) Seit API
Version 54.
Tabelle 10:TariffInfoSelector
```
#### Die Liste der verfügbaren HVV-Karten (kinds) hier ist nur exemplarisch. Sie ist auf dem

#### Stand von Juli 2012 in der Tabelle 11 aufgeführt.

HBT GmbH; Version 63.1

24. November 2025 Seite 23 von 107


```
ID Kartenart ID Kartenart
1 Einzelfahrt 52 Wochenkarte
2 Einzelkarte für Kinder 70 9-Uhr-Senioren-Monatskarte
11 Ganztageskarte 71 9-Uhr-Senioren-Abo-Karte
21 9-Uhr-Tageskarte 72 Kinder-Monatskarte
22 9-Uhr-Tageskarte Kind 73 Kinder-Abonnementskarte
23 9-Uhr-Gruppenkarte 80 Schüler-Monatskarte
31 3-Tage-Karte 82 Schüler-Monatsnebenkarte
50 Allgemeine Monatskarte 81 Schüler-Abonnementskarte
51 Allgemeine Abonnementskarte 83 Schüler-Abo-Nebenkarte
60 CC-Monatskarte 90 Studierende/Azubi-Monatskarte
61 CC-Abonnementskarte 91 Studierende/Azubi-Abo-Karte
Tabelle 11: Liste der verfügbaren HVV-Karten
```
#### 2.3.3 Penalties

#### Die MethodegetRoutefindet die optimale Route und führt dazu im Hintergrund eine ma-

#### thematische Minimierung der Bewertung verschiedener Routen hinsichtlich ihres Verlaufes und

#### ihrer Eigenschaften aus. Es wird jene Route zurückgegeben, die die beste Bewertung hat, ei-

#### ne typische Bewertung ist die Dauer. Eine Route wird jedoch nicht ausschließlich anhand ihrer

#### Dauer gemessen. Für ungewünschte Eigenschaften einer Route fließen zusätzliche Faktoren (Be-

#### strafungen, engl. penalties) in die Bewertung ein. Für den Wunsch „bitte Schiff vermeiden” wird

#### bei einer diese Forderung verletzenden Route jede Minute auf einem Schiff mit einem Strafffak-

#### tor multipliziert, so dass die kürzeste Route (bei verfügbaren Alternativen) keinen Abschnitt

#### per Schiff enthalten wird. Über das optionale Feldpenalties kann also die Routenfindung

#### zuungunsten verschiedener Eigenschaften beeinflusst werden; auch ein Einfluss „zugunsten” ist

#### möglich, da die Penalties prinzipiell auch negativ sein können – negative Straffaktoren fallen

#### positiv ins Gewicht, wie z.B. im Falle vonDesiredType. Die Penalities werden in Tabelle 12

#### aufgeführt.

```
Penalty Name Typ d. Value Beschreibung
ChangeEvent Integer Bewertung von Umsteigen
ExtraFare Integer Bewertung von zuschlagspflichtigen Fahrten
Walker Integer Bewertung von Fußwegen, vgl.AnyHandicap
AnyHandicap Integer Bewertung von Wegerschwernissen Mobilität/des Fahrgastes
(z.B. Treppen, lange Fußwege), vgl.Walker
ToStartStationBy Integer Art der Fortbewegung zur Haltestelle
TimeRange Integer Gibt den Faktor zur Bewertung von Wartezeit als Reisezeit
an, siehe FeldcontinousSearchimGRRequest
ForVisitors Integer Gibt an, ob der Fahrgast ortsfremd ist und längere
Umsteigezeiten gewünscht sind
DesiredType String Bewertung einzelner Verkehrsmittel
DesiredLine String Präferenz von Linien (geplant nach API Verison 16)
Tabelle 12: Die Penalties
```
#### Man kann sich vorstellen, dass einige der Penalties so etwas wie Strafminuten darstellen; dies

#### wird deutlich bei der Frage, welchen Umweg man zur Vermeidung von z.B. eines Umsteigens in

HBT GmbH; Version 63.1

24. November 2025 Seite 24 von 107


#### Kauf nehmen möchte. Dies gilt jedoch nicht allgemein, so dass diese Werte lediglich symbolisch

#### zu betrachten sind.

#### Die in Tabelle 13 beschriebenen Key/Value-Paare der Penalties sind daher bindend, nicht

#### genannte Zwischenabstufungen sind nicht zulässig.

```
Penalty
(Umsteigen)
```
```
Werte Bedeutung der
Werte
```
```
Bemerkung
```
```
ChangeEvent
(Umsteigen)
```
##### 0

##### 4

##### 8

##### 20

```
gern, wenn schneller
normal
ungern
vermeiden
```
```
Default: normal, 4
```
```
ExtraFare
(Zuschlag)
```
##### 0

##### 10

##### 20

##### 50

```
gern, wenn schneller
normal
ungern
vermeiden
```
```
Default: normal, 10
```
```
Walker
(Fußweg)
```
##### 0

##### 1

##### 3

##### 8

```
gern, wenn schneller
normal
ungern
vermeiden
```
```
Default: normal, 1
```
```
AnyHandicap
(Mobilität)
```
##### -1

##### 0 1 2 3 4 5

```
gut zu fuß
normal
langsam
sehr langsam
mit Traglast
ohne Treppe
ohne Treppe/Stufe
```
```
Default: normal, 0
```
```
ToStartStationBy
(Weg zur Haltestelle)
```
##### 0

##### 1

##### 7

```
zu Fuß
mit Fahrrad
mit Fahrrad auch
am Ziel
```
```
Default: zu Fuß, 0
```
```
TimeRange
(Zeitvorgabe)
```
##### 10

##### 20

##### 30

##### 45

##### 60

```
sehr groß
groß
normal
gering
sehr gering
```
```
Default: normal, 30
Je größer dieser Wert, desto weniger
werden Abweichungen vom Vorgabewert
akzeptiert.
```
```
ForVisitors
(Ortsfremd, zus.
Umsteigezeit)
```
##### 0

##### 1

```
nein
ja
```
```
Default:nein, 0
```
```
DesiredType
(Verkehrsmitteltyp)
```
##### -10

##### -2

##### 0

##### 2

##### 10

##### 10000

```
unbedingt
bevorzugen
neutral
ungern
vermeiden
ausschließen
```
```
Default: 0
Mögliche Verkehrsmittel: siehe
DesiredType
```
```
DesiredLine
(Linien)
```
##### 2

##### 1

```
bevorzugen
vermeiden
```
```
kein Default. Kombinationen wie
{"name":"DesiredLine",
"value":"u2,s1:1"}sind möglich.
DesiredCarrier
(Betreiber)
```
##### 2

##### 0

##### 1

```
bevorzugen
neutral
vermeiden
```
```
Default: neutral, 0
Es kann nur ein Betreiber angegeben
werden. Mögliche Betreiber: siehe
DesiredCarrier
Tabelle 13: Mögliche Penaltytypen und ihre Werte
```
HBT GmbH; Version 63.1

24. November 2025 Seite 25 von 107


#### 2.3.4 DesiredType

#### In Tabelle 14 sind die möglichen Fahrzeugtypen für die PenaltyDesiredTypeaufgelistet.

```
Wert Bedeutung
bus Bus
ship Schiff
u U-Bahn
s S-Bahn
r Regionalbahnen (R-Bahn)
train alle Bahnen
fasttrain&extrafasttrain IC/EC/ICE/TGV
extrafasttrain ICE/TGV
callable Anruf-Sammel-Taxi
ast Anruf-Sammel-Taxi. Alias fürcallableAnruf-Sammel-Taxi
rb Regionalbahn (nicht Regionalexpress). Bezeichnung für Linien die mitRxxoderRBxx
beginnen, wobeixxfür eine Zahl steht.
re Regionalexpress
normalbus Alle Busse, ausser ASTs, Fernbussen oder Schnellbussen.
fastbus Schnellbus
longdistancebus Fernbus
Tabelle 14:DesiredTypeFahrzeugtypen
```
#### 2.3.5 DesiredCarrier

#### In der folgenden Liste sind die möglichen Betreiber für die PenaltyDesiredCarrieraufgelistet.

#### Achtung: Die möglichen Werte aus dieser Liste können sich mit jeder Datenlieferung ändern.

```
AKN Autokraft DB-Regio Dahmetal
EVB EVM Fernzug Globetrotter
HHA HL Hadag KVIP
LVG metronom MZH nordbahn
PVG RB S-H S-Bahn Storjohann
VHH VOG
```
#### 2.3.6 Beispiel der Umsetzung aufgeofox.hvv.de

#### Auf der Internetseitehttp://geofox.hvv.dekann ein persönlicher Fahrplan angefragt wer-

#### den, wie es auch mittelsgetRoutemöglich ist. In Abb. 3 sind die beiden Möglichkeiten dersel-

#### ben Anfrage gegenüberstellt.

HBT GmbH; Version 63.1

24. November 2025 Seite 26 von 107


#### Abbildung 3: Zuordnung eines GRRequests und den Optionen der Webseite von http:

//geofox.hvv.de

HBT GmbH; Version 63.1

24. November 2025 Seite 27 von 107


#### In Tabelle 15 wird beschrieben, welche Optionenauswahl zu welchen zusätzlichen Penalties

#### führt.

```
Optionen Penalties
Beste Verbindung
Hohe Geschwindigkeit
```
```
AnyHandicap=-1
```
```
Beste Verbindung
Normale Geschwindigkeit
```
```
Default, keine extra Penalties
```
```
Beste Verbindung
Niedrige Geschwindigkeit
```
```
AnyHandicap=1
```
```
Schnellste Verbindung
Hohe Geschwindigkeit
```
```
AnyHandicap=-1
ChangeEvent=0
Walker=0
ExtraFare=0
Schnellste Verbindung
Normale Geschwindigkeit
```
```
ChangeEvent=0
Walker=0
ExtraFare=0
Schnellste Verbindung
Niedrige Geschwindigkeit
```
```
AnyHandicap=1
ChangeEvent=0
Walker=0
ExtraFare=0
Rollstuhl ExtraFare=0
AnyHandicap=5
Tabelle 15: Vergleich http://geofox.hvv.de-Optionen/Penalties
```
#### 2.3.7 GRResponse

#### Die folgende Tabelle beschreibt einen GRResponse

```
Feld Typ Beschreibung
schedules Liste aus Schedule s Liste von Routenergebnissen basierend auf Plandaten
realtimeSchedules Liste aus Schedule s Liste von Routenergebnissen basierend auf
Echtzeitdaten
realtimeAffected SDName Gibt an ob das angegebene Suchergebnis durch
Echtzeitdaten beeinflusst wurde.
individualTrack SDName Informationen über den direkten Fuß- oder
Fahrradweg als Vergleichswert zur
ÖPNV-Verbindung
Tabelle 16:GRResponse
```
HBT GmbH; Version 63.1

24. November 2025 Seite 28 von 107


#### EinScheduleerweitertBaseScheduleum eine Liste vonscheduleElements. Eine Zu-

#### sammenfassung aller Felder steht in Tabelle 17.

```
Feld Typ Beschreibung
routeId Integer Eine ID zur Identifikation der Route
start SDName Wiederholung von Start
dest SDName Wiederholung von Ziel
time Integer Die gesamte Reisedauer, inkl. Umstiege und Fußwege
zu/ab Start/Ziel
plannedDepartureTime DateTime Die geplante Abfahrtszeit am Start
plannedArrivalTime DateTime Die geplante Ankunftszeit am Ziel
realDepartureTime DateTime Die tatsächliche Abfahrtszeit am Start
realArrivalTime DateTime Die tatsächliche Ankunftszeit am Ziel
footpathTime Integer Die Dauer aller Fußwege inkl. Umstiege
tickets ListeausTicket EineListeallerfürdieseRoutegültigenTickets.Zu
jedemTypeinTicketmitminimalnotwendigem
Level. Veraltet seit API 13.
scheduleElements Liste ausScheduleElement Liste der Verbingungsabschnitte. Seit API Version 12
sind auch Umsteigefußwege eigene Abschnitte und
damitScheduleElements
tariffInfos Liste ausTariffInfo Ggf. eine Liste von Tarifinformationen, abhängig vom
tariffInfoSelectorim Request (seit API 13)
contSearchBefore ContSearchByServiceId Ein Objekt, das gegebenenfalls durch Setzen von
GRRequest.returnContSearchDataermittelt werden
kann. (seit API 29)
contSearchAfter ContSearchByServiceId Ein Objekt, das gegebenenfalls durch Setzen von
GRRequest.returnContSearchDataermittelt werden
kann. (seit API 29)
Tabelle 17:Schedule
```
#### Möchte man das zurückgegebeneSchedule.contSearchBefore/After-Objekt in einem neu-

#### en Request fürGRRequest.contSearchByServiceIdverwenden, so muss

#### GRRequest.timeIsDepartureauf false/truegesetzt werden. Aufgrund der zusätzlichen

#### Informationen in GRRequest.contSearchByServiceId wird die Uhrzeit-Komponente von

#### GRRequest.timeignoriert. Nur die Datums-Komponente wird genutzt.

#### Die Felder vonScheduleElement(derGRResponse) werden in Tabelle 18 beschrieben.

HBT GmbH; Version 63.1

24. November 2025 Seite 29 von 107


```
Feld Typ Beschreibung
from JourneySDName Starthaltestelle inklusive der Abfahrtszeit und
Gleisinformationen (platform)
to JourneySDName Zielhaltestelle inklusive Ankunftszeit und Gleisinformationen
(platform)
line Service Das Verkehrsmittel
paths Liste ausPath Eine Liste von möglichen Streckenverläufen. Jeder Path hat
nur ein Feldtrack, dies ist eine Liste ausCoordinate
attributes Liste ausAttribute EinAttributebesteht aus demString value(enthält den
Nachrichtentext) und einer Liste vontypes, letzteres nimmt
z.B. für Linieninformationen („Nach 19 Uhr kann auch
zwischen Haltestellen ausgestiegen werden”) den Wert
NORMALan.FürFahrplanderänderungen
(„StraßenbauarbeitenbewirkenFahrtverzögerungen”,
„Schienenersatzverkehr”)hatesdenWertANNOUNCEMENT
(nur bis Version 54). Seit Version 43 gibt es das Feldidvom
TypString, welches eine eindeutige ID enthalten kann,
bspw. für Announcements. Für den Fall, dass die
Echtzeit-Verspätungszeiten ungenau sind, gibt es noch die
Attribut-TypenTRAFFIC_JAM,TECHNICAL_PROBLEM(z.B. Bei
der Übermittlung der Daten is ein Problem aufgetreten,
keine aktuellen Informationen vorhanden),
DISPOSITIVE_ACTION(z.B. Zur Sicherung eines Anschlusses
wartet das Fahrzeug),MISSING_UPDATE(z.B. eine Prognose
liegt vor, kann aber Aufgrund von Kommunikationsstörungen
nicht aktualisiert werden.). Ab Version 55 werden Attribute
des TypsANNOUNCEMENTnicht mehr ausgeliefert.
announcements Liste ausAnnouncement Announcements werden in Tabelle 46 beschrieben.
Announcements werden ausschließlich in diesem Feld
ausgeliefert, und nicht mehr als Attribute des Typs
ANNOUNCEMENT. Falls das Startdatum desScheduleElement
innerhalb despublication-Zeitraums des Announcements,
aber nicht innerhalb einesvalidities-Zeitraums des
Announcements liegt, so handelt es sich um eine
Vorankündigung. Ab Version 55.
extra boolean Fahrt ist Verstärkerfahrt (seit API Version 19)
cancelled boolean Fahrt fällt aus (seit API Version 19)
intermediateStops Liste ausJourneySDName Eine Liste der Zwischenhalte. Um die Daten klein zu halten,
werden weniger wichtige Informationen z.B. zum Tarif oder
zur Ankunftszeit weggelassen. (seit API Version 24)
vehicles Liste ausVehicle Eine Liste der Fahrzeuge, die diese Fahrt durchführen,
optional (seit API Version 57)
shopInfo Liste ausShopInfo Informationen über Shops zum Kauf von Fahrkarten für
diesen Streckenabschnitt
Tabelle 18:ScheduleElement
```
#### Die Felder vonContSearchByServiceIdwerden in Tabelle 19 beschrieben.

```
Feld Typ Beschreibung
serviceId integer Die Service-Id des Fahrzeugs des ersten/letzen gefahrenen
Streckenabschnitts
lineKey String Die Linien-Id des Fahrzeugs des ersten/letzten gefahrenen
Streckenabschnitts
plannedDepArrTime GTITime Die Uhrzeit in Minuten, zu der die Start-/Zielhaltestelle
nach Fahrplan angefahren werden sollte.
additionalOffset integer Die Dauer des Fußwegs/Fahrradwegs zur ersten/letzten
Haltestelle. IsttimeIsDeparturegesetzt, so sollte
additionalOffset0 oder negativ sein.
Tabelle 19:ContSearchByServiceId
```
HBT GmbH; Version 63.1

24. November 2025 Seite 30 von 107


#### EinService(inScheduleElement) speichert das verwendete Verkehrsmittel. Es wird in

#### Tabelle 54 beschrieben.

```
Feld Typ Beschreibung
id string optionale ID für diesen Service
name string Name, optional
direction string Richtung, optional
directionId integer Id für die Richtung, optional. Hin- (1) und Rückrichtung (6)
type ServiceType EinServiceTypeenthält drei Felder: Das Enum
SimpleServiceType(mit den WertenBUS,TRAIN,SHIP,
FOOTPATH,BICYCLE,AIRPLANE,CHANGE,
CHANGE_SAME_PLATFORM,ACTIVITY_BIKE_AND_RIDE)
klassifiziert den Typ desService, zwei StringsshortInfo
undlongInfobeschreiben ihn
carrierNameShort string Kurzname des Betreibers des Verkehrsmittels, optional
carrierNameLong string Name des Betreibers des Verkehrsmittels, optional
Tabelle 20:Service
```
#### Der Typ JourneySDName(inScheduleElement) erweitert den bei der Besprechung des

#### CNRequestvorgestelltenSDName(mit seinen Feldernname,city,combinedName,id,type,

#### coordinate,tariffDetails,serviceTypes). Die Erweiterung zumJourneySDNamebesteht

#### aus den Feldern in Tabelle 21.

```
Feld Typ Beschreibung
arrTime GTITime planmäßige Ankunftszeit an diesemJourneySDName, optional
depTime GTITime planmäßige Abfahrtszeit an diesemJourneySDName, optional
attributes Liste vonAttribute Liste der Attribute des Ortes, siehe Tabelle zu
scheduleElement
platform string Das Gleis, an dem das Verkehrsmittel verkehrt
arrDelay int Ankunfts-Verspätungszeit in Sekunden (seit API Version 19)
depDelay int Abfahrts-Verspätungszeit in Sekunden (seit API Version 19)
extra boolean Dieses Flag wird gesetzt wenn die angegebene Fahrt hier
außerplanmäßig zusätzlich hält. (seit API Version 19)
cancelled boolean Dieses Flag wird gesetzt wenn die angegebene Fahrt
aufgrund aktueller Fahrplanabweichungen nicht an dieser
Haltstelle hält. (seit API Version 19)
realtimePlatform string Das Gleis, dass als Echtzeitinformation zu diesem Halt
übermittelt wurde.
Tabelle 21:JourneySDName
```
HBT GmbH; Version 63.1

24. November 2025 Seite 31 von 107


#### Der TypVehicle(inScheduleElement) beschreibt ein konkretes Fahrzeug, welches ein-

#### zeln oder im Verbund eine Fahrt durchführt.

```
Feld Typ Beschreibung
id string Fahrzeug-Id, optional
number string Fahrzeugnummer, optional
Tabelle 22:Vehicle
```
#### Der TypTariffInfo(derGRResponse) wird in Tabelle 23 beschrieben.

```
Feld Typ Beschreibung
tariffName String Name des Tarifes
tariffRegions Liste von
TariffRegionInfo
```
```
DieTariffRegionInfoenthalten je ein Enum
TariffRegionType(enumsZONE,GH_ZONE,RING,COUNTY)
sowie eine Liste vonTariffRegionList, die eine Liste ihres
einzigen Feldesregions (String)speichert. Anschaulich
speichertTariffRegionInfoden Tarifbereich und die
durchfahrenen Tarifzonen (Zonen, Ringe, Kreise). Weil einige
Haltestellen zu zwei Tarifzonen gehören (zwischen zwei
Tarifzonen liegen), sind die durchfahrenen Tarifzonen einer
Fahrt mehrdeutig – alle möglichen Interpretationen
(Tarifzonenlisten) werden hier als Liste gespeichert.
extraFareType Enum
extraFareType
```
```
Das Enum gibt Auskunft über die Notwendigkeit eines
erste-Klasse/Schnellbus-Zuschlags mit den WertenNO
(zuschlagsfrei, default),POSSIBLE(Zuschlag möglich),
REQUIRED(Zuschlagszahlung erforderlich).
ticketInfos Liste von
TicketInfo
```
```
Eine Liste der gültigen Tickets, siehe die folgende Tabelle
```
```
ticketRemarks string Weitere Informationen zum Ticket, z.B. eine beschränkte
Gültigkeit für nur einen Teilabschnitt der Strecke (seit API
18). Ist dem Fahrgast zwingend mitzuteilen, da dies die
Gültigkeit der Preisauskunft einschränkt
Tabelle 23:TariffInfo
```
#### TicketInfoObjekte sind aufgebaut wie in Tabelle 24 beschrieben. Die FeldertariffGrou-

#### pIDundtariffGroupLabelexistieren zur strukturierteren Darstellung der Kartenarten im

#### Client; dadurch sind z.B. HVV-Tickets gruppierbar in die Kategorien Monatskarte, CC-Karte,

#### ermäßigte Karte usw.

HBT GmbH; Version 63.1

24. November 2025 Seite 32 von 107


```
Feld Typ Beschreibung
tariffKindID integer ID der Kartenart
tariffKindLabel string Name der Kartenart
tariffLevelID integer ID der Tarifstufe
tariffLevelLabel string Name der Tarifstufe
viaPathId string ID des Überwegs, falls anwendbar (z.B. bei SH-Tarifen)
tariffGroupID integer ID der Tarifgruppe
tariffGroupLabel string Name der Tarifgruppe
basePrice double Basispreis der Fahrkarte ohne Zuschlag
extraFarePrice double Zuschlagspreis. Diese Feld ist leer, wenn in der
TariffResponsedas FeldextraFareTypeaufNOsteht.
reducedBasePrice double Seit API Version 16 können zusätzlich reduzierte Preise für
elektronische Fahrkarten zurückgegeben werden, dies
erfordert im Request das FlagreturnReduced
```
```
reducedExtraFarePrice double
```
```
currency string Währung (default:EUR)
regionType Enum Dieser Typ von Bereichsinformationen wird (ab API Version
14) für dieses Ticket zusätzlich benötigt. Werte:ZONE,
GH_ZONE,RING,COUNTY
notRecommended boolean Wenn auf true gesetzt, dann wird diese Karte nicht
empfohlen, da es günstigere Alternativen gibt.
shopLinkRegular string Definiert den offiziellen Link zum bestellen/kaufen des
regulären Tickets.
shopLinkExtraFare string Definiert den offiziellen Link zum bestellen/kaufen des
Zuschlagtickets.
startStationId string ID der Starthaltestelle. Aktuell nur bei SH-Tarif benutzt.
endStationId string ID der Zielhaltestelle. Aktuell nur bei SH-Tarif benutzt.
baseTicketID string ID der Ticket-Variante 2. Klasse ohne Rabatt. Seit
API-Version 60.
reducedBaseTicketID string ID der Ticket-Variante 2. Klasse mit Rabatt. Im Request
mussreturnReducedgesetzt sein. Seit API-Version 60.
extraFareID string ID der Ticket-Variante 1. Klasse ohne Rabatt. Seit
API-Version 60.
reducedExtraFareTicketID string ID der Ticket-Variante 1. Klasse mit Rabatt. Im Request
mussreturnReducedgesetzt sein. Seit API-Version 60.
Tabelle 24:TicketInfo
```
#### 2.3.8 Echtzeit

#### Zur Konfiguration der Berücksichtigung von Echtzeitinformationen bei der Routensuche gibt es

#### den optionalen Request Paramterrealtimevom TypRealtimeType. Über diesen Paramter

#### kann der Client steuern, ob er ein Ergebnis auf Basis von Echtzeitinformationen (REALTIME)

#### oder auf Basis von Plandaten (PLANDATA) erhalten möchte. In beiden Fällen wird das Sucher-

#### gebnis mit Verspätungs-, Verstärker- und Ausfallinformationen angereichert. Der Unterschied

#### besteht darin, dass für die Suche der optimalen Route Echtzeitinformationen berücksichtigt

#### werden. So kann bei einer Suche auf Basis von Plandaten auch ein Ergebnis berechnet werden,

#### dass aufgrund von verpassten Anschlüssen durch Verspätungen so nicht gefahren werden kann.

#### Zusätzlich zu diesen beiden Varianten gibt es noch eine automatische Einstellungsmöglichkeit

#### (AUTO). In diesem Fall wird sowohl das Plan- als auch das Echtzeitergebnis geliefert, wenn diese

#### beiden Ergebnisse sich von einander unterscheiden. Ob sich das Echtzeitergebnis vom Planer-

#### gebnis unterscheidet kann dem Response-FlagrealtimeAffectedentnommen werden. (siehe

#### auch Abschnitt 1.8).

HBT GmbH; Version 63.1

24. November 2025 Seite 33 von 107


#### 2.3.9 Beispiel

#### Es wird angefragt, vom Rosenhof in Ahrensburg über Kellinghusenstraße zur Stadthausbrücke

#### zu fahren. Dabei wird vom regionalen Datenfilter Gebrauch gemacht und die Variablefilter-

#### TypeaufHVV_LISTEDgesetzt.

#### Die Antwort beinhaltet mehrere Routen, von denen nur jene mit"routeId": 0hier an-

#### gegeben ist. In einer Route werden zunächst Start und Ziel wiederholt, es wird die Reise- und

#### Fußwegzeit ausgegeben sowie das günstigste Ticket, das für diese Reise gültig ist, benannt.

#### Danach werden die Reiseabschnitte (scheduleElements) als Liste ausgegeben. Sie beinhalten

#### fromundto(welcheSDNamessamt Details sind), danach folgt das Feldline, das die Fort-

#### bewegungsart zwischenfromundtoangibt – dies kann eine Linie (z.B. U2), aber auch ein

#### Fußweg oder Umsteigeweg sein.

#### In jedemscheduleElementist zuletzt derpathgenannt. Dies ist eine Liste der Koordina-

#### ten, anhand derer dasscheduleElementam Client gezeichnet werden kann. In denschedu-

#### leElementkönnen auch Attribute enthalten sein, von denen vielleicht der TypANNOUNCEMENT

#### hervorzuheben ist. In diesem Feld sind Bekanntgaben des Betreibers zumscheduleElement

#### (hier: S3) vermerkt, z.B. Umleitungen und Schienenersatzverkehr. Diese werden zwar in der

#### Regel schon bei der Routenfindung berücksichtig, jedoch kann natürlich eine Verzögerung auf-

#### treten, bis eine temporäre Änderung am Streckennetz (wie eine Umleitung nach einem Unfall)

#### ihren Weg in die Daten gefunden hat.

#### Listing 10:GRRequest

```
1 {
2 "version": 63,
3 "language": "de",
4 "start": {
5 "name": "Rosenhof",
6 "city": "Ahrensburg",
7 "combinedName": "Ahrensburg, Rosenhof",
8 "id": "Master:35009",
9 "type": "STATION",
```
10 "coordinate": {

11 "x": 9.93454,

12 "y": 53.552405

13 }

14 },

15 "dest": {
16 "name": "Stadthausbrücke",

17 "city": "Hamburg",

18 "combinedName": "Stadthausbrücke",

19 "id": "Master:11952",

20 "type": "STATION",

21 "coordinate": {

22 "x": 9.93454,

23 "y": 53.552405

24 }

25 },

26 "via":{

27 "name": "Kellinghusenstraße",

28 "city": "Hamburg",

HBT GmbH; Version 63.1

24. November 2025 Seite 34 von 107


29 "id": "Master:90904",

30 "type": "STATION",

31 "coordinate": {

32 "x": 9.93454,

33 "y": 53.552405

34 }

35 },

36 "time": {

37 "date": "17.10.2017",

38 "time": "13:10"

39 },

40 "timeIsDeparture": true,

41 "schedulesBefore": 1,

42 "schedulesAfter": 2,

43 "realtime": "REALTIME"

44 }

#### Listing 11:GRResponse

```
1 {
2 "returnCode": "OK",
3 "realtimeSchedules": [
4 {
5 "routeId": 0,
6 "start": {
7 "name": "Rosenhof",
8 "city": "Ahrensburg",
9 "combinedName": "Ahrensburg, Rosenhof",
```
10 "id": "Master:35009",

11 "type": "STATION",

12 "coordinate": {...},
13 "serviceTypes": [

14 "bus"

15 ],

16 "hasStationInformation": false

17 },

18 "dest": {

19 "name": "Stadthausbrücke",

20 "city": "Hamburg",

21 "combinedName": "Stadthausbrücke",

22 "id": "Master:11952",

23 "type": "STATION",

24 "coordinate": {...},

25 "serviceTypes": [

26 "s"

27 ],

28 "hasStationInformation": true

29 },

30 "time": 81,

31 "footpathTime": 6,

32 "tickets": [

33 {

34 "price": 3.2,
35 "type": "Einzelkarte HVV (EUR)",

36 "level": "Hamburg AB",

HBT GmbH; Version 63.1

24. November 2025 Seite 35 von 107


37 "tariff": "HVV"

38 }

39 ],

40 "scheduleElements": [

41 {

42 "from": {

43 "name": "Rosenhof",

44 "city": "Ahrensburg",

45 "combinedName": "Ahrensburg, Rosenhof",

46 "id": "Master:35009",

47 "type": "STATION",

48 "coordinate": {...},

49 "serviceTypes": [

50 "bus"

51 ],

52 "hasStationInformation": false,

53 "depTime": {

54 "date": "17.10.2017",

55 "time": "13:19"

56 }

57 },
58 "to": {

59 "name": "U Ahrensburg West",

60 "city": "Ahrensburg",

61 "combinedName": "U Ahrensburg West",

62 "id": "Master:34009",

63 "type": "STATION",

64 "coordinate": {...},

65 "serviceTypes": [

66 "bus",

67 "u"

68 ],

69 "hasStationInformation": false,

70 "arrTime": {

71 "date": "17.10.2017",

72 "time": "13:45"

73 }

74 },

75 "line": {

76 "name": "569",

77 "direction": "Ahrensburg, Schulzentrum Am Heimgarten",

78 "origin": "Ahrensburg, Rosenhof",

79 "type": {
80 "simpleType": "BUS",

81 "shortInfo": "Bus",

82 "longInfo": "Niederflur Stadtbus",

83 "model": "Niederflur Stadtbus"

84 },

85 "id": "VHH:569_VHH",

86 "carrierNameShort": "VHH",

87 "carrierNameLong": "Verkehrsbetriebe Hamburg-Holstein GmbH"

88 },

89 "paths": [

90 {

91 "track": [

92 {

HBT GmbH; Version 63.1

24. November 2025 Seite 36 von 107


```
93 "x": 10.240837,
94 "y": 53.683063
95 },
96 {
97 "x": 10.240822,
98 "y": 53.683063
99 },
```
100 ...

101 ]

102 }

103 ],

104 "attributes": [

105 {

106 "value": "Test-Meldung für das Gesamtnetz",

107 "types": [

108 "ANNOUNCEMENT"

109 ]

110 }

111 ],

112 "serviceId": 60848

113 },
114 {

115 "from": {

116 "name": "U Ahrensburg West",

117 "city": "Ahrensburg",

118 "combinedName": "U Ahrensburg West",

119 "id": "Master:34009",

120 "type": "STATION",

121 "coordinate": {...},

122 "serviceTypes": [

123 "bus",

124 "u"

125 ],

126 "hasStationInformation": false,

127 "depTime": {

128 "date": "17.10.2017",

129 "time": "13:45"

130 }

131 },

132 "to": {

133 "name": "Ahrensburg West",

134 "city": "Ahrensburg",

135 "combinedName": "Ahrensburg West",
136 "id": "Master:34900",

137 "type": "STATION",

138 "coordinate": {...},

139 "serviceTypes": [

140 "bus",

141 "u"

142 ],

143 "hasStationInformation": true,

144 "arrTime": {

145 "date": "17.10.2017",

146 "time": "13:47"

147 }

148 },

HBT GmbH; Version 63.1

24. November 2025 Seite 37 von 107


149 "line": {

150 "name": "Umstiegsfußweg",

151 "type": {

152 "simpleType": "CHANGE"

153 }

154 }

155 },

156 ...

157 ]

158 }

159 ],

160 "individualTrack": {

161 "time": 371,

162 "length": 25562,

163 "type": "FOOTPATH"

164 }

165 }

HBT GmbH; Version 63.1

24. November 2025 Seite 38 von 107


### 2.4 MethodedepartureList

#### Die MethodedepartureListliefert die Abfahrten an einer gegebenen Haltestelle in einem

#### gegebenen Zeitintervall.

#### 2.4.1 DLRequest

#### URL:/gti/public/departureList

#### Die Felder des Requests sind in Tabelle 25 gelistet.

```
Feld Typ Beschreibung
station SDName Haltestelle, für die Abfahrten gesucht werden
stations Liste vonSDName Haltestellen, für die Abfahrten gesucht werden. Von
stationoderstationmuss mindestens ein Feld ge-
füllt sein.
time GTITime Zeitpunkt, ab dem Abfahrten gesucht werden
maxList integer Maximale Anzahl an zurückzugebenden Abfahrten
maxTimeOffset integer Länge des Zeitintervalls abtime, in dem Abfahrten
gesucht werden
allStationsInChangingNode boolean Falls diestationein Umsteigeknoten (changingNode)
ist und damit ggf. mehrere Haltestellen hat, entschei-
det dieses Feld, ob Abfahrten aller Haltestellen dieses
Knotens gemeint sind.
returnFilters boolean Steuert ob eine Liste vonFilterEntrys zurück gege-
ben werden soll (siehe 2.4.3). (seit API Version 20)
filter Liste vonFilterEntry Ist dieses Feld gefüllt, wird eine gefilterte Liste von
Departures ausgegeben (siehe 2.4.3). (seit API Version
20)
serviceTypes Liste vonFilterServiceType Ist dieses Feld gefüllt, wird die Ergebnisliste anhand
von Verkehrsmitteln gefiltert. (seit API Version 22)
useRealtime boolean Gibt an ob Echtzeitinformationen berücksichtigt wer-
den sollen.
coordinateType coordinateType Bezugssystem der Koordinaten,EPSG_ 4326 (default)
oderEPSG_ 31467. (seti API Version 61)
Tabelle 25:DLRequest
```
#### 2.4.2 DLResponse

#### Die Felder derDLResponsesind in Tabelle 26 gelistet.

```
Feld Typ Beschreibung
time GTITime Referenzzeit für diese Abfahrtstafel
departures Liste vonDepartures Liste der Abfahrten
filter Liste vonDLFilterEntry Liste mit sinnvollen Filtermöglichkeiten für die abge-
fragte Haltestelle (siehe 2.4.3)
serviceTypes Liste vonFilterServiceType Liste der Verkehrsmittel die an der angegebenen Hal-
testelle abfahren/ankommen
Tabelle 26:DLResponse
```
HBT GmbH; Version 63.1

24. November 2025 Seite 39 von 107


#### Die Felder derDeparturesind in Tabelle 27 gelistet.

```
Feld Typ Beschreibung
line Service Name,direction,typeundIDdes Verkehrsmittels, sieheGRResponse
direction integer Die Richtungs-ID der Fahrt (1 für vorwärts, 6 für rückwärts) (seit API Version
39)
timeOffset integer Die Minuten zwischentimeaus dem Request und der Abfahrt
station SDName Die Haltestelle des Umsteigeknotens, von dem aus diese Fahrt abfährt. Dieses
Feld wird nur verwendet im FallallStationsInChangingNode==true
stopPoint SDName Der Mast / das Gleis der Station, von dem aus diese Fahrt abfährt. (seit API
Version 61)
serviceId integer Eine eindeutige ID dieser Fahrt
platform string Gleisinformationen (seit API Version 11)
delay int Verspätungszeit in Sekunden (seit API Version 19)
extra boolean Fahrt ist Verstärkerfahrt (seit API Version 19)
cancelled boolean Fahrt fällt aus (seit API Version 19)
realtimePlatform string Das Gleis, dass als Echtzeitinformation zu dieser Fahrt übermittelt wurde.
(seit API Version 21)
vehicles Liste vonVehicles Eine Liste der Fahrzeuge, die diese Fahrt durchführen (seit API Version 62)
attributes Attribute Zusätzliche textuelle Informationen zu dieser Fahrt (seit API Version 23)
Tabelle 27:Departure
```
#### 2.4.3 Filter

#### Die Liste der zurückgegebenenDepartures kann serverseitig gefiltert werden. Im DLRequest

#### gibt es dafür zwei Filtermöglichkeiten. Über das Feldfilterkann auf einzelne Linien/Rich-

#### tungen gefiltert werden. EinFilterEntryenthält dabei die folgenden Felder.

```
Feld Typ Beschreibung
serviceID String Linien-ID: Filtert die Liste anhand von Linien.
stationIDs Liste vonString Filtert die Liste anhand einer Richtung auf der ange-
gebenen Linie.
serviceName String Anzuzeigender Linienname (Wird im DLRequest nicht
benötigt)
label String Anzuzeigender Richtungstext (Wird im DLRequest
nicht benötigt)
Tabelle 28:FilterEntry
```
#### Ein gültigerFilterEntrymuss mindestens das FeldserviceIDgefüllt haben. Wird zu-

#### sätzlich das FeldstationIDsgefüllt, werden nur Fahrten zurückgegeben, die über mindestens

#### eine der angegebenen Haltestellen führen. So kann zum Beispiel auch ein Filter aus einem

#### GRResponse erstellt werden indem alsstationIDdie Zielhaltestelle angegeben wird. Das Er-

#### gebnis würde dann nur Fahrten beinhalten, die auch tatsächlich über diese Zielhaltestelle fahren,

HBT GmbH; Version 63.1

24. November 2025 Seite 40 von 107


#### während solche Fahrten nicht geliefert werden würden, die zwar in die richtige Richtung fahren,

#### aber bereits vor der angegebenen Haltestelle enden (Wird als Richtung für die U2 beispiels-

#### weise Niendorf Nord angegeben, werden keine Fahrten zurückgegeben die bereits in Niendorf

#### Markt enden). Bei Ringlinien werden nur die Fahrten übermittelt die den kürzeren Weg im

#### Ring zur angegebenen Haltestelle haben (Bei der U3 von Barmbek in Richtung Berliner Tor

#### beispielsweise würden nur Fahrten der U3 im Uhrzeigersinn geliefert werden).

#### Des Weiteren gibt es über das FeldserviceTypesdie Möglichkeit nach Verkehrsmitteln

#### zu filtern. Die Typen aus der EnumerationFilterServiceTypesind in Tabelle Tabelle 29

#### beschrieben.

```
ZUG Alle Züge inkl. U-Bahnen, S-Bahnen, AKNs, R-
Bahnen und Fernbahnen
UBAHN Die U-Bahn-Linien der Hamburger Hochbahn AG
SBAHN Die S-Bahn-Linien der S-Bahn Hamburg
AKN Die Linien der AKN Eisenbahn AG
RBAHN Regional-Express und Regionalbahn
FERNBAHN Fernverkehrszüge wie z.B. Intercity-Express
BUS Alle Busse inkl. Stadtbusse, Metrobusse, Schnellbusse,
Nachtbusse, XpressBusse und Anruf-Sammel-Taxis
STADTBUS Stadt- und Regionalbusse
METROBUS Metrobusse
SCHNELLBUS Schnellbusse
NACHTBUS Nachtbusse
XPRESSBUS XpressBusse
AST Anruf-Sammel-Taxis
FAEHRE Fähren wie z.B. die Hafenfähren der HADAG Seetou-
ristik und Fährdienst AG
Tabelle 29:Fahrzeugtypen für den Verkehrsmittelfilter
```
#### Zu beachten ist, dass die Typen UBAHN, SBAHN, AKN, RBAHN und FERNBAHN voll-

#### ständig in ZUG und die Typen STADTBUS, METROBUS, SCHNELLBUS, NACHTBUS,

#### XPRESSBUS und AST vollständig in BUS enthalten sind. Es ist somit nicht sinnvoll Typen

#### wie beispielsweise METROBUS und BUS gemeinsam zu verwenden.

#### Wird imDLRequestdas FeldreturnFiltersauftruegesetzt, wird imDLResponsein

#### den FeldernserviceTypesundfiltersinnvolle Filtermöglichkeiten für diese Anfrage zurück-

#### gegeben. Diese Filtermöglichkeiten können dem Benutzer direkt zur Filterauswahl angeboten

#### werden.

HBT GmbH; Version 63.1

24. November 2025 Seite 41 von 107


#### 2.4.4 Beispiel

#### In diesem Beispiel werden die nächsten (höchstens 10) Abfahrten (in den nächsten, max. 200

#### Minuten) von der Station Rosenhof zu einem gegebenen Zeitpunkt angefragt.

#### Es werden drei Fahrten gefunden (von denen eine hier ausführlich zitiert wird) und mit aus-

#### führlichen stationsbezogenen Details zurückgegeben. Das FeldtimeOffsetist anfragebezogen

#### und gibt die Differenz zwischentimeder Anfrage und Abfahrt in Minuten an.

#### Listing 12:DLRequest

```
1 {
2 "version": 63,
3 "station": {
4 "name": "Rosenhof",
5 "city": "Ahrensburg",
6 "combinedName": "Ahrensburg, Rosenhof",
7 "id": "Master:35009",
8 "type": "STATION",
9 "coordinate": {...}
```
10 },

11 "time": {

12 "date": "11.10.2017", "time": "21:28"

13 },

14 "maxList": 10,

15 "maxTimeOffset": 200,

16 "useRealtime":true

17 }

#### Listing 13:DLResponse

```
1 {
2 "returnCode": "OK",
3 "time": {
4 "date": "11.10.2017",
5 "time": "21:28"
6 },
7 "departures": [
8 {
9 "line": {
```
10 "name": "476",

11 "direction": "Ahrensburg, Auestieg",

12 "origin": "Bf. Ahrensburg",

13 "type": {

14 "simpleType": "BUS",

15 "shortInfo": "Bus",

16 "longInfo": "Niederflur Stadtbus",

17 "model": "Niederflur Stadtbus"

18 },

19 "id": "VHH:476_VHH"

20 },
21 "timeOffset": 20,

22 "serviceId": 200023670,

23 "station": {

HBT GmbH; Version 63.1

24. November 2025 Seite 42 von 107


24 "combinedName": "Ahrensburg, Rosenhof",

25 "id": "Master:35009"

26 }

27 },

28 {

29 "line": {

30 "name": "8110",

31 "direction": "Bf. Bad Oldesloe (ZOB)",

32 "origin": "Bf. Ahrensburg",

33 "type": {

34 "simpleType": "BUS",

35 "shortInfo": "Bus",

36 "longInfo": "Stadtbus",

37 "model": "Stadtbus"

38 },

39 "id": "AKma:8110_AKma_AKMA"

40 },

41 "timeOffset": 26,

42 "serviceId": 200059035,

43 "station": {

44 "combinedName": "Ahrensburg, Rosenhof",
45 "id": "Master:35009"

46 }

47 },

48 ...

49 ]

50 }

HBT GmbH; Version 63.1

24. November 2025 Seite 43 von 107


#### Im zweiten Beispiel werden Abfahrten von mehreren Haltestellen gesucht.

#### Listing 14:DLRequest

```
1 {
2 "version": 63,
3 "stations": [
4 {
5 "name": "Groß Flottbeker Straße",
6 "city": "Hamburg",
7 "combinedName": "Groß Flottbeker Straße",
8 "id": "Master:80086",
9 "type": "STATION",
```
10 "coordinate": { ... }

11 },

12 {

13 "name": "Flottbeker Drift",

14 "city": "Hamburg",

15 "combinedName": "Flottbeker Drift",

16 "id": "Master:80097",

17 "type": "STATION",

18 "coordinate": { ... }

19 }

20 ],

21 "time": {

22 "date": "heute", "time": "jetzt"

23 },
24 "maxList": 10,

25 "maxTimeOffset": 200

26 }

### 2.5 MethodegetTariff

#### DerTariffRequestliefert zu einer Fahrt eine Liste von gültigen Fahrkarten.

#### 2.5.1 TariffRequest

#### URL:/gti/public/getTariff

#### Für die Berechnung werden natürlich Start, Ziel, Zeitpunkt und eine eindeutige Beschreibung

#### des gewählten Weges benötigt. Letztere wird über die kostenpflichtigenscheduleElementssi-

#### chergestellt. Umsteigefußwege sind zwar kostenlos, aber nicht zu übertragen. Der Request wird

#### in Tabelle 30 beschrieben.

HBT GmbH; Version 63.1

24. November 2025 Seite 44 von 107


```
Feld Typ Beschreibung
scheduleElements Liste vonScheduleElementLight Liste der Streckenabschnitte. Da
ScheduleElement mit SDNames in from/to
sowie einem Path sehr groß ist, gibt es hier
die Light-VersionScheduleElementLight.
departure GTITime Abfahrtszeitpunkt des ersten
ScheduleElements
arrival GTITime Ankunftszeitpunkt des letzten
ScheduleElements. Optional, wenn nicht
gesetzt, wird keine 9-Uhr-Tageskarte beaus-
kunftet.
returnReduced boolean Entscheidet, ob zusätzlich Preise ermäßigter
elektronischer Tickets zurückgegeben werden.
Optional, default istfalse
tariffInfoSelector Liste vonTariffInfoSelector Dient zur Filterung von Tarifgruppen und Ta-
rifkinds. Seit API Version 54
Tabelle 30:TariffRequest
```
```
Feld Typ Beschreibung
departureStationId string Haltestellen-Id der Starthaltestelle
arrivalStationId string Haltestellen-Id der Endhaltestelle
intermediateStops string Liste von Ids der Zwischenhaltestellen (Optional)
lineId string Id der Linie
Tabelle 31: Die Felder vonScheduleElementLight
```
#### 2.5.2 TariffResponse

#### DieTariffResponsebesteht ausschließlich aus einer Liste vonTariffInfo-Objekten. Diese

#### enthalten einerseits Informationen über die verwendeten Tarifzonen der gegeben Route (tarif-

#### fRegions) und andererseits die für diese Tarifzonenkombinationen gültigen Tickets (ticket-

#### Infos). Der TypTariffInfowird in Tabelle 32 beschrieben.

HBT GmbH; Version 63.1

24. November 2025 Seite 45 von 107


```
Feld Typ Beschreibung
tariffName String Die Region des Tarifs (z.B.HVV,HL,SH)
extraFareType Enum NO: Es wird kein Zuschlag benötigt
POSSIBLE: Erste Klasse Zuschlag ist möglich.
REQUIRED: Zuschlag ist zwingend erforderlich
tariffRegions Liste von
TariffRegionInfo
```
```
Die TariffRegionInfo enthalten je ein Enum
TariffRegionType (EnumsZONE, GH_ZONE, RING, COUNTY)
sowie eine Liste vonTariffRegionList, die eine Liste ihres
einzigen Feldes regions (String) speichert. Anschaulich
speichertTariffRegionInfoden Tarifbereich und die durch-
fahrenen Tarifzonen (Zonen, Ringe, Kreise). Weil einige
Haltestellen zu zwei Tarifzonen gehören (zwischen zwei
Tarifzonen liegen), sind die durchfahrenen Tarifzonen einer
Fahrt mehrdeutig – alle möglichen Interpretationen werden
daher als Liste von Listen gespeichert.
ticketInfos Liste vonTicketInfo Liste der für diese Fahrt gültigen Tickets (incl. deren Gültig-
keitsbereichen und Preisen), s.GetRouteResponse
regionTexts Liste vonString Liste der durchfahrenden Tarif-Regionen
Tabelle 32:TariffInfo
```
#### 2.5.3 Beispiel

#### In diesem Beispiel werden die für eine Fahrt (mit Haltestelle und Zeit von Start und Ziel)

#### gültigen Fahrscheine angefragt. In der Response werden zunächst Eigenschaften der angefragten

#### Fahrt wie die durchfahrenen Zonen mitgeteilt. Danach folgt eine Auflistung der gültigen Tickets

#### samt deren Eigenschaften, der Länge wegen wurden einige herausgekürzt.

#### Listing 15:TariffRequest

```
1 {
2 "language": "de",
3 "version": 63,
4 "scheduleElements": [
5 {
6 "departureStationId": "Master:10950",
7 "arrivalStationId": "Master:37979",
8 "lineId": "DB-EFZ:RE8_DB-EFZ_Z"
9 }
```
10 ],
11 "departure": {

12 "date": "11.10.2017", "time": "8:04"

13 },

14 "arrival": {

15 "date": "11.10.2017", "time": "8:29"

16 }

17 }

#### Listing 16:TariffResponse

```
1 {
2 "returnCode": "OK",
3 "tariffInfos": [
```
HBT GmbH; Version 63.1

24. November 2025 Seite 46 von 107


```
4 {
5 "tariffName": "HVV",
6 "tariffRegions": [
7 {
8 "regionType": "ZONE",
9 "alternatives": [
```
10 {

11 "regions": [

12 "000",

13 "105",

14 "205",

15 "305",

16 "405",

17 "505",

18 "605",

19 "705"

20 ]

21 }

22 ]

23 },

24 {
25 "regionType": "RING",

26 "alternatives": [

27 {

28 "regions": [

29 "A",

30 "B",

31 "C",

32 "D"

33 ]

34 }

35 ]

36 },

37 ...

38 ],

39 "extraFareType": "POSSIBLE",

40 "ticketInfos": [

41 {

42 "tariffKindID": 1,

43 "tariffKindLabel": "Einzelkarte",

44 "tariffLevelID": 304,

45 "tariffLevelLabel": "4 Ringe",

46 "tariffGroupID": 1,
47 "tariffGroupLabel": "Einzelkarten",

48 "basePrice": 7.1,

49 "extraFarePrice": 2,

50 "regionType": "RING"

51 },

52 {

53 "tariffKindID": 2,

54 "tariffKindLabel": "Einzelkarte Kind",

55 "tariffLevelID": 600,

56 "tariffLevelLabel": "Gesamtbereich ABCDE",

57 "tariffGroupID": 1,

58 "tariffGroupLabel": "Einzelkarten",

59 "basePrice": 2.4,

HBT GmbH; Version 63.1

24. November 2025 Seite 47 von 107


60 "extraFarePrice": 2

61 },

62 ...

63 ]

64 }

65 ]

66 }

HBT GmbH; Version 63.1

24. November 2025 Seite 48 von 107


### 2.6 MethodedepartureCourse

#### URL:/gti/public/departureCourse

#### Die MethodedepartureCourseruft zu einer Linie (mit Richtung) und Haltestelle alle nach-

#### folgenden oder vorhergehenden Haltestellen incl. Abfahrtszeiten bis zur End- bzw. Anfangshal-

#### testelle ab. DerDCRequestwird in Tabelle 33 beschrieben.

#### Eine Fahrt wird entweder durchtimeunddirectionoder durchserviceIdidentifiziert.

#### Nicht ganz korrekt ist daher die Angabe in der WADL, dass alle drei Felder jeweils für sich

#### optional wären.

```
Feld Typ Beschreibung
lineKey string Der volle Line Key der Linie, für die die
Haltestellen-Liste erscheinen soll (z.B. HHA
U:U1_HHA-U), siehe dazu Abschnitt 1.6
station SDName Die Haltestelle, für die Abfahrten gesucht wer-
den sollen. Diese muss vom Typ (SDType) Sta-
tion sein
time dateTime Abfahrtszeit der Fahrt an der angegebenen
Haltestelle (nur relevant, falls keineserviceId
angegeben werden kann)
direction string Name der Ziel-Haltestelle (nur relevant, falls
keineserviceIdangegeben werden kann)
serviceId integer ID der Fahrt, falls bekannt (überschreibt die
Wirkung vontimeunddirection)
segments Enum SegmentSelector Ein SegmentSelectorenthält ausschließlich
einenString, der entscheidet, ob das Ergeb-
nis die Haltestellen nach oder vor der gege-
benen Haltestelle oder alle Haltestellen liefert,
die zugehörigen Elemente sindBEFORE,AFTER
undALL(default)
showPath boolean Entscheidet, ob zusätzlich ein geographischer
Verlauf der Fahrt mit ausgegeben wird
coordinateType CoordinateType Bezugssystem der Koordinaten inshowPath,
EPSG_ 4326 (default) oderEPSG_ 31467
Tabelle 33:DCRequest
```
#### 2.6.1 DCResponse

#### Die DCResponseenthält eine Liste courseElementsvon CourseElements und eine Liste

#### vehiclesvonVehicles. Der TypCourseElementwird in Tabelle 34 und der TypVehicle

#### (verfügbar ab API-Version 63) wird in Tabelle 35 beschrieben.

HBT GmbH; Version 63.1

24. November 2025 Seite 49 von 107


```
Feld Typ Beschreibung
fromStation SDName Start-Haltestelle für diesen Abschnitt
fromPlatform string Gleis-Angabe fürfromStation(falls vorhanden)
toStation SDName Ziel-Haltestelle für diesen Abschnitt
toPlatform string Gleis-Angabe fürtoStation(falls vorhanden)
depTime dateTime Abfahrtszeit abfromStation
arrTime dateTime Ankunftszeit antoStation
path Path Streckenverlauf (falls angefordert und verfügbar, derzeit nicht imple-
mentiert)
depDelay int Abfahrts-Verspätungszeit in Sekunden (seit API Version 19)
arrDelay int Ankunfts-Verspätungszeit in Sekunden (seit API Version 19)
fromExtra boolean Dieses Flag wird gesetzt wenn diefromStationein außerplanmäßig
zusätzlicher Halt ist. (seit API Version 19)
fromCancelled boolean Dieses Flag wird gesetzt wenn die angegebene Fahrt aufgrund aktu-
eller Fahrplanabweichungen nicht an derfromStationhält. (seit API
Version 19)
fromRealtimePlatform string Das Gleis, dass als Echtzeitinformation zurfromStationübermittelt
wurde. (seit API Version 21)
toExtra boolean Dieses Flag wird gesetzt wenn dietoStationein außerplanmäßig zu-
sätzlicher Halt ist. (seit API Version 19)
toCancelled boolean Dieses Flag wird gesetzt wenn die angegebene Fahrt aufgrund aktu-
eller Fahrplanabweichungen nicht an dertoStationhält. (seit API
Version 19)
toRealtimePlatform string Das Gleis, dass als Echtzeitinformation zurtoStationübermittelt
wurde. (seit API Version 21)
attributes Attribute Zusätzliche textuelle Informationen zu diesem Fahrtabschnitt (seit
API Version 23)
model String Zusätzliche Informationen zum Verkehrsmittel(z.B. „DT4”,
„Midibus”,... ) (seit API Version 24)
Tabelle 34:CourseElement
```
```
Feld Typ Beschreibung
id String ID des Fahrzeugs
number String Nummer des Fahrzeugs
Tabelle 35:Vehicle
```
#### 2.6.2 Beispiel

#### Hier wird zu gegebenem Datum und Uhrzeit von der Haltestelle Rosenhof ausgehend nach den

#### nächsten Haltestellen der Buslinie 569 bis zum Ahrensburger Bahnhof gefragt, die mit allen

#### Details zurückgegeben werden.

#### Listing 17:DCRequest

1 {

2 "language": "de",

3 "version": 63,

4 "lineKey": "VHH:569_VHH",
5 "station": {

6 "name": "Rosenhof",

HBT GmbH; Version 63.1

24. November 2025 Seite 50 von 107


```
7 "city": "Ahrensburg",
8 "combinedName": "Ahrensburg, Rosenhof",
9 "id": "Master:35009",
```
10 "type": "STATION",

11 "coordinate": {"x": 10.240928, "y": 53.683071}

12 },

13 "time": "2017-10-11T16:19:00.000+0200",

14 "direction": "Ahrensburg, Schulzentrum Am Heimgarten"

15 }

#### Listing 18:DCResponse

```
1 {
2 "returnCode": "OK",
3 "courseElements": [
4 {
5 "fromStation": {
6 "name": "Rosenhof",
7 "city": "Ahrensburg",
8 "combinedName": "Ahrensburg, Rosenhof",
9 "id": "Master:35009",
```
10 "type": "STATION",

11 "coordinate": {

12 "x": 10.240837,

13 "y": 53.683063

14 },

15 "serviceTypes": [

16 "bus"

17 ],

18 "hasStationInformation": false

19 },
20 "toStation": {

21 "name": "Pellwormstieg",

22 "city": "Ahrensburg",

23 "combinedName": "Ahrensburg, Pellwormstieg",

24 "id": "Master:35244",

25 "type": "STATION",

26 "coordinate": {

27 "x": 10.24222,

28 "y": 53.685322

29 },

30 "serviceTypes": [

31 "bus"

32 ],

33 "hasStationInformation": false

34 },

35 "model": "Niederflur Stadtbus",

36 "depTime": "2017-10-11T16:19:00.000+0200",

37 "arrTime": "2017-10-11T16:20:00.000+0200"

38 },

39 {

40 "fromStation": {

41 "name": "Pellwormstieg",
42 "city": "Ahrensburg",

43 "combinedName": "Ahrensburg, Pellwormstieg",

HBT GmbH; Version 63.1

24. November 2025 Seite 51 von 107


44 "id": "Master:35244",

45 "type": "STATION",

46 "coordinate": {

47 "x": 10.24222,

48 "y": 53.685322

49 },

50 "serviceTypes": [

51 "bus"

52 ],

53 "hasStationInformation": false

54 },

55 "toStation": {

56 "name": "Helgolandring",

57 "city": "Ahrensburg",

58 "combinedName": "Ahrensburg, Helgolandring",

59 "id": "Master:35047",

60 "type": "STATION",

61 "coordinate": {

62 "x": 10.242032,

63 "y": 53.68562

64 },
65 "serviceTypes": [

66 "bus"

67 ],

68 "hasStationInformation": false

69 },

70 "model": "Niederflur Stadtbus",

71 "depTime": "2017-10-11T16:21:00.000+0200",

72 "arrTime": "2017-10-11T16:22:00.000+0200"

73 },

74 ...

75 ],

76 "vehicles": [

77 {

78 "id": "FzgID_ 431600 _ 21 _437",

79 "number": "437"

80 },

81 ...

82 ]

83 }

HBT GmbH; Version 63.1

24. November 2025 Seite 52 von 107


### 2.7 MethodelistStations

#### Viele Methoden nehmenSDNamesals Argument. Von dessen vielen Feldern verwenden sie jedoch

#### oft nur die Felderid,name,cityundtype. Weil nun Haltestellen (das sind jedeSDNamesmit

#### type==STATION) besonders häufig alsSDNameverwendet werden, enthält eine aufid,name

#### undcitybeschränkte Haltestellenliste bereits alle vier relevanten Felder eines SDName, um

#### z.B. für eingetRoutezwei vorhergehendecheckName-Aufrufe fürstartunddestzu sparen

#### – was insbesondere auf mobilen Clients viel Zeit spart. Ebenfalls möglich ist mit solch einem

#### Cache ein Vorschlager, der bereits bei wenigen eingegebenen Buchstaben Haltestellenvorschläge

#### machen kann. Es ist vorgesehen, dass der Cache auf dem Client die Felderid,name,cityund,

#### optional für die grafische Darstellung, die Koordinaten der Stationen zwischenspeichert.

#### Eine solche Liste auf Endgeräten erfordert die Initialbefüllung und eine Möglichkeit zum

#### Update. Für diese Funktionen istlistStationsvorgesehen.

#### 2.7.1 LSRequest

#### URL:/gti/public/listStations

#### Für eine Initialbefüllung des Clients ist das FelddataReleaseID leer zu lassen. Ist es das

#### nicht, werden nur (vollständige) Datensätze zurückgegeben, die sich seit der angegebenen Ver-

#### sion hinsichtlich der drei Felderid,name,citybzw. dem Feldcoordinategeändert haben

#### (diff). Über den Listeneintrag MAINin der ListemodificationTypes werden Datensätze

#### mit Änderungen inid,name,cityangewählt, überPOSITIONsolche mit Änderungen im Feld

#### coordinate. Ist die Liste leer, werden Änderungen gemäß allen möglichen Werten des Enums

#### ModificationTypezurückgegeben. Der Request wird in Tabelle 36 beschrieben.

```
Feld Typ Beschreibung
dataReleaseID string Die bereits vorhandene Datenversion. Ein leeres Feld
fragt alle Datensätze an
modificationTypes Liste von Enums
ModificationType
```
```
Legt die Felder fest, hinsichtlich welcher einSDName
als verändert betrachtet wird, derzeit sind die
möglichen Felder die genanntenMAINundPOSITION
coordinateType CoordinateType Bezugssystem der Koordinaten,EPSG_ 4326 (default)
oderEPSG_ 31467
filterEquivalent boolean Fügt äquivalente Haltestellen zusammen (z.B.
RödingsmarktundU Rödingsmarkt)
Tabelle 36:LSRequest
```
HBT GmbH; Version 63.1

24. November 2025 Seite 53 von 107


#### 2.7.2 LSResponse

#### Die Response wird in Tabelle 37 beschrieben. Der TypStationListEntrywird in Tabelle 38

#### beschrieben.

```
Feld Typ Beschreibung
dataReleaseID string Version der aktuellen Daten
stations Liste von
StationListEntry
```
```
Die Daten: Stationen, die sich geändert haben
```
Tabelle 37:LSResponse

```
Feld Typ Beschreibung
id string ID (wie inSDName)
name string Name (wie inSDName)
city string Ort (wie inSDName)
combinedName string Voller Name (wie inSDName)
shortcuts Liste ausstring Kürzel des Haltestellennamens
aliasses Liste ausstring Alternativbezeichnungen des Haltestellennamens
vehicleTypes Liste ausEnum
VehicleType
```
```
Die hier verkehrenden Verkehrsmittel (z.B.U_BAHN,
SCHNELLBUS,SCHIFF,NACHTBUS,XPRESSBUS,AST).
Entspricht demserviceTypesausSDName, ist aber
nicht so fein aufgelöst.
coordinate Coordinate Koordinaten (wie inSDName)
exists Boolean Flag zur Übermittlung von gelöschten Haltestellen
Tabelle 38:StationListEntry
```
#### Wird eine Haltestelle gelöscht, werden von ihr nur die Felderidundexists(mit Wert

#### false) zurückgegeben – damit kann der Client den Eintrag aus seinem Cache entfernen.

HBT GmbH; Version 63.1

24. November 2025 Seite 54 von 107


#### 2.7.3 Beispiel

#### Listing 19:LSRequest

```
1 {
2 "language": "de",
3 "version":63,
4 "dataReleaseID": "29.73.01",
5 "modificationTypes": ["MAIN"]
6 }
```
#### Listing 20:LSResponse

```
1 {
2 "returnCode": "OK",
3 "dataReleaseID": "29.74.01",
4 "stations": [
5 {
6 "id": "Master:52982",
7 "name": "Neumühlen/Övelgönne",
8 "city": "Hamburg",
9 "combinedName": "Neumühlen/Övelgönne",
```
10 "shortcuts": [

11 "neua"

12 ],

13 "aliasses": [

14 "Neumühlen"

15 ],

16 "vehicleTypes": [

17 "SCHIFF"

18 ]

19 },

20 {

21 "id": "Master:19072",

22 "exists": false

23 },

24 {

25 "id": "Master:56103",

26 "name": "Im Ort",

27 "city": "Wendhausen",

28 "aliasses": [
29 "Reinstorf, Wendhausen",

30 "Wendhausen, Ort"

31 ],

32 "vehicleTypes": [

33 "REGIONALBUS",

34 "AST"

35 ]

36 }

37 ]

38 }

HBT GmbH; Version 63.1

24. November 2025 Seite 55 von 107


### 2.8 MethodelistLines

#### Die Methode ermöglicht es dem Client, eine Liste der bestehenden Linien als Cache vorzu-

#### halten, ähnlich wielistStationses mit den Haltestellen ermöglicht. Dies ermöglicht einen

#### Vorschlager für Linien.

#### Zunächst sind Begrifflichkeiten anzumerken: Eine Linie hat eine oder mehrere Sublinien.

#### Sublinien sind dann gegeben, wenn beispielsweise auf einer Buslinie nur jeder zweite Bus zur

#### Endhaltestelle fährt – die anderen Busse haben eine frühere Endhaltestelle.

#### Sublinien gibt es auch bei der U1, die durch das hamburger Zentrum fährt und sich draußen

#### in Volksdorf aufteilt: Ungefähr jeder zweite Zug fährt danach Richtung Ohlstedt, die verbleiben-

#### den fahren nach Volksdorf Richtung Großhansdorf. An letzterem Beispiel ist nachvollziehbar,

#### dass jede Sublinie eine (sortierte) Liste von Haltestellen hat. Der hier behandelten Liste einer

#### Linie, die alle Haltestellen ihrer Sublinien speichert, kann keine Haltestellenabfolge entnommen

#### werden.

#### 2.8.1 LLRequest

#### URL:/gti/public/listLines

#### Der Request wird in Tabelle 39 beschrieben.

```
Feld Typ Beschreibung
dataReleaseID string Die bereits vorhandene Datenversion. Ein leeres Feld
fragt alle Datensätze an
modificationTypes Liste von Enums
LineModificationType
```
```
Legt über die EnumsMAINundSEQUENCEdie Felder
fest, hinsichtlich welcher eine Linie als verändert
betrachtet wird
withSublines boolean Entscheidet, ob auch Sublinien zurückgegeben
werden sollen
Tabelle 39:LLRequest
```
#### Im EnumLineModificationTypegibt es derzeit die EnumsMainundSEQUENCE, von

#### denen ersteres Änderungen der Linie bezüglich ihres Namens, Betreibers (Carrier,Carrier-

#### Long,CarrierShort) anfragt, während das EnumSEQUENCEÄnderungen in der Haltestellen-

#### liste der Linie anfragt.

#### 2.8.2 LLResponse

#### Die Response wird in Tabelle 40 beschrieben.

HBT GmbH; Version 63.1

24. November 2025 Seite 56 von 107


```
Feld Typ Beschreibung
dataReleaseID string Version der aktuellen Daten
lines Liste von
LineListEntry
```
```
Die Daten: Linien, die sich geändert haben.
```
Tabelle 40:LLResponse

#### Der TypLineListEntrywird in Tabelle 41 beschrieben.

#### Wird eine Linie gelöscht, werden von ihr nur die Felderidundexists(mit Wertfalse)

#### zurückgegeben – damit kann der Client den Eintrag aus seinem Cache entfernen.

```
Feld Typ Beschreibung
id string ID der Linie
name string Name der Linie, z.B.U1
carrierNameShort string Namenskürzel des Betreibers
carrierNameLong string Name des Betreibers
sublines Liste von
SublineListEntry
```
```
Die Liste der Sublinien dieser Linie
```
```
exists boolean Flag zur Übermittlung von gelöschten
Haltestellen
type ServiceType Beschreibt den Fahrzeugtyp der Linie. Es
werden nur die FeldersimpleTypeund
shortInfogefüllt.
Tabelle 41:LineListEntry
```
#### Der TypSublineListEntrywird in Tabelle 42 beschrieben.

```
Feld Typ Beschreibung
sublineNumber string Interne Nummer der Sublinie. Diese kann sich
häufig ändern, z.B. bei neuer Datenversion.
vehicleType VehicleType Das Verkehrsmittel der Sublinie (z.B.U_BAHN,
SCHNELLBUS,SCHIFF,NACHTBUS,XPRESSBUS,
AST). Entspricht demserviceTypesaus
SDName, ist aber nicht so fein aufgelöst.
stationSequence Liste von
StationLight
```
```
Diese Liste enthält die Stationen dieser
Sublinie
Tabelle 42:SublineListEntry
```
#### Der TypStationLightwird in Tabelle 43 beschrieben.

HBT GmbH; Version 63.1

24. November 2025 Seite 57 von 107


```
Feld Typ Beschreibung
id string ID der Haltestelle
name string Der Name der Haltestelle
Tabelle 43:StationLight
```
HBT GmbH; Version 63.1

24. November 2025 Seite 58 von 107


#### 2.8.3 Beispiel

#### Listing 21:LLRequest

```
1 {
2 "language": "de",
3 "version": 63,
4 "dataReleaseID": "29.71.01",
5 "modificationTypes": ["MAIN"]
6 }
```
#### Listing 22:LLResponse

```
1 {
2 "returnCode": "OK",
3 "dataReleaseID": "29.74.01",
4 "lines": [
5 {
6 "id": "HHA-B:175_HHA-B",
7 "exists": false
8 },
9 {
```
10 "id": "KVGBer:Elb-Shuttle_KVGBer_KVGM",

11 "exists": false

12 },

13 {

14 "id": "HHA-B:U3-SEV_HHA-B",

15 "exists": false

16 },

17 {

18 "id": "KVGBer:Elbe-Radwanderbus_KVGBer_KVGM",

19 "exists": false

20 },

21 {

22 "id": "KVGBer:Regionalpark-Shuttle_KVGBer_KVGM",

23 "exists": false

24 },

25 {

26 "id": "HHA-B:SEV-U3_HHA-B",

27 "name": "SEV-U3",

28 "carrierNameShort": "Hochbahn",
29 "carrierNameLong": "Hamburger Hochbahn AG",

30 "exists": true

31 }

32 ]

33 }

HBT GmbH; Version 63.1

24. November 2025 Seite 59 von 107


### 2.9 MethodegetAnnouncements

#### 2.9.1 AnnouncementRequest

#### URL:/gti/public/getAnnouncements

#### DerAnnouncementRequestfragt die aktuellen Fahrplanabweichungen ab. Die Menge der zu-

#### rückgegebenen Meldungen kann dabei z.B. nach Zeitraum, Linie oder Verkehrsunternehmen

#### gefiltert werden. Der Request wird in Tabelle 44 beschrieben.

```
Feld Typ Beschreibung
names Liste vonString Liste von zu betrachtenden Liniennamen oder
Verkehrsunternehmen, z.B. „S1”, „2” oder „KVG”.
timeRange TimeRange Besteht aus den beidendateTime-Objektenbegin
undend(siehe Abschnitt 1.6). Nur Meldungen dieses
Zeitintervalls ausgeben. Optional (falls nicht gesetzt,
werden alle aktuellen Meldungen zurückgegeben)
full boolean Gibt an ob die Antwort vollständige Linien,
Haltestellen und Gültigkeitsinformationen enthalten
soll.
filterPlanned AnnouncementFilter-
PlannedType
```
```
Filterung derAnnouncements nach dem Flag
planned. (optional, seit API Version 30)
showBroadcastRelevant boolean Filterung derAnnouncements nach dem Flag
broadcastRelevant. (optional, seit API Version 46)
Tabelle 44:AnnouncementRequest
```
#### Der Enum AnnouncementFilterPlannedTypekann folgende Werte annehmen: ONLY_-

#### PLANNED,ONLY_UNPLANNEDundNO_FILTER. Anhand dieser Werte werden die Announcements

#### nach dem Flagplannedgefiltert, oder auch nicht. Ist das Feldfilterz.B. nicht gesetzt, so

#### wird wie auch im Fall vonNO_FILTERnicht gefiltert.

#### 2.9.2 AnnouncementResponse

#### DieAnnouncementResponseenthält den Zeitpunkt der letzten Aktualisierung und eine Liste

#### der einzelnen Meldungen. Sie wird in Tabelle 45 beschrieben.

```
Feld Typ Beschreibung
announcements Liste vonAnnouncement Liste aller angefragten Meldungen
lastUpdate dateTime Zeitpunkt der letzten serverseitigen Aktualisierung
Tabelle 45:AnnouncementResponse
```
#### Der TypAnnouncementwird in Tabelle 46 beschrieben.

HBT GmbH; Version 63.1

24. November 2025 Seite 60 von 107


```
Feld Typ Beschreibung
id string Eindeutige ID für diese Meldung
version integer Versionsnummer für diese Meldung
locations Liste vonLocation DieLocationbeschreibt die Region bzw. die Fahrten
die von dem beschriebenen Ereignis betroffen sind.
Falls eine veraltete bzw. nicht mehr vorhandene
Haltestelle betroffen ist, kann diese Liste auch leer
sein. (siehe Tabelle 47).
summary string Der Kurzmeldungstext, ein zusammenfassender Satz,
der z.B. als Überschrifft verwendet werden kann.
Wird im Fall von ungeplanten Meldungen nicht
gesetzt.
description string Der ausführliche Meldungstext
links Liste vonLink Eine Liste vonLinks mit zusätzlichen Informationen
zur Meldung (z.B. Ersatzfahrplan als PDF o.ä.). Ein
Linkenthält die beidenStringslabelundurl.
publication TimeRange Veröffentlichungszeitraum, also der Zeitraum in dem
die Meldung für den Fahrgast angezeigt werden soll.
validities Liste vonTimeRange Liste der Gültigkeitszeiträume, also die Zeiträume in
denen Fahrten vom beschriebenen Ereignis betroffen
sind.
lastModified DateTime Zeitpunkt der letzten Aktualisierung dieser Meldung
(Entspricht immer dem Erstellungszeitpunkt, da
Meldungen grundsätzlich nicht verändert sondern nur
durch neue Meldungen ersetzt werden können).
planned boolean Entspricht das Announcement einem geplanten
Ereignis? (seit API Version 30)
reason String Der Grund für das Ereignis. Ein kurzer Schlüssel, der
nur feste Werte annehmen kann. Mögliche Werte
werden in Tabelle 48 aufgezählt. (seit API Version
30)
broadcastRelevant boolean Ist das Announcement relevant für die
Veröffentlichung im öffentlichen Rundfunk? (seit API
Version 46)
Tabelle 46:Announcement
```
#### DieLocationbeschreibt die Region bzw. die Fahrten die von dem beschriebenen Ereignis

#### betroffen sind. Dies können einzelne Linien aber auch ganze Netze oder Verkehrsunternehmen

#### sein. Die Location wird nur dann mit detaillierten Informationen gefüllt, wenn das Feldfull

#### auftruegesetzt ist. Die Location wird in Tabelle 47 beschrieben.

#### Falls das Startdatum desScheduleElement innerhalb despublication-Zeitraums des

#### Announcements, aber nicht innerhalb einesvalidities-Zeitraums des Announcements liegt,

#### so handelt es sich um eine Vorankündigung.

HBT GmbH; Version 63.1

24. November 2025 Seite 61 von 107


```
Feld Typ Beschreibung
type LocationType Beschreibungstyp, möglich sind einzelne Linien, alle
Linien eines Betreibers oder ein gesamtes Netz.
name string Wenn ein ganzer Betreiber oder ein ganzes Netz
betroffen ist, steht hier um welches es sich handelt.
line Service Wenn eine einzelne Linie betroffen ist, steht hier um
welche es sich handelt (siehe Tabelle 54).
begin SDName Die erste Haltestelle auf der angegebenen Linie, die
betroffen ist (null = Die ganze Linie ist betroffen).
end SDName Die letzte Haltestelle auf der angegebenen Linie, die
betroffen ist (null = Die ganze Linie ist betroffen).
bothDirections boolean Wenn eine einzelne Linie betroffen ist, ist hier
angegeben ob nur die angegebene, oder beide
Richtungen, betroffen sind. Der Richtungstext der
Gegenrichtung kann dann dem Feld Origin im
Service entnommen werden.
Tabelle 47:Location
```
HBT GmbH; Version 63.1

24. November 2025 Seite 62 von 107


#### Das Feldreasonnimmt im Moment nur folgende mögliche Werte an:

```
Wert
UNDEFINED_PROBLEM
ROADWORKS
CONGESTION
SPECIAL_EVENT
SLIPPERINESS
POLICE_REQUEST
FIRE_BRIGADE_SAFETY_CHECKS
STATION_OVERRUN
SERVICE_FAILURE
ROAD_CLOSED
VEHICLE_ON_THE_LINE
ACCIDENT
DEMONSTRATION
STAFF_ABSENCE
BOMB_ALERT
LOW_WATER_LEVEL
ROUTE_BLOCKAGE
ROUGH_SEA
Tabelle 48:Announcement.Reason
```
HBT GmbH; Version 63.1

24. November 2025 Seite 63 von 107


#### 2.9.3 Beispiel

#### In diesem Beispiel werden alle Meldungen zur Linie S3 angefragt. Es wird eine Meldung zu-

#### rückgegeben, die die Linie S3 in beide Richtungen betrifft. Zusätzlich werden mehrere Links

#### mit weiteren Informationen für den Fahrgast angegeben.

#### Listing 23:AnnouncementRequest

```
1 {
2 "language": "de",
3 "version": 63,
4 "names": [
5 "S3"
6 ],
7 "full": true
8 }
```
#### Listing 24:AnnouncementResponse

```
1 {
2 "returnCode": "OK",
3 "announcements": [
4 {
5 "id": "171012003C",
6 "locations": [
7 {
8 "type": "SINGLE_LINE",
9 "line": {
```
10 "name": "S1",

11 "direction": "Poppenbüttel / Hamburg Airport (Flughafen)",
12 "origin": "Wedel",

13 "type": {

14 "simpleType": "TRAIN",

15 "shortInfo": "S",

16 "longInfo": "S-Bahn"

17 },

18 "id": "ZVU-DB:S1_ZVU-DB_S-ZVU",

19 "dlid": "de:hvv:S1:"

20 },

21 "begin": {

22 "name": "Poppenbüttel",

23 "city": "Hamburg",

24 "combinedName": "Poppenbüttel",

25 "id": "Master:71953",

26 "type": "STATION"

27 },

28 "end": {

29 "name": "Wedel",

30 "city": "Wedel",

31 "combinedName": "Wedel",

32 "id": "Master:85950",

33 "type": "STATION"
34 }

35 },

HBT GmbH; Version 63.1

24. November 2025 Seite 64 von 107


36 {

37 "type": "SINGLE_LINE",

38 "line": {

39 "name": "S11",

40 "direction": "Poppenbüttel",

41 "origin": "Blankenese",

42 "type": {

43 "simpleType": "TRAIN",

44 "shortInfo": "S",

45 "longInfo": "S-Bahn"

46 },

47 "id": "ZVU-DB:S11_ZVU-DB_S-ZVU",

48 "dlid": "de:hvv:S1:"

49 },

50 "begin": {

51 "name": "Poppenbüttel",

52 "city": "Hamburg",

53 "combinedName": "Poppenbüttel",

54 "id": "Master:71953",

55 "type": "STATION"

56 },
57 "end": {

58 "name": "Blankenese",

59 "city": "Hamburg",

60 "combinedName": "Blankenese",

61 "id": "Master:81950",

62 "type": "STATION"

63 }

64 },

65 ...

66 ],

67 "description": " \nAufgrund eines mittlerweile behobenen Stromausfalls am Hamburger

```
Hauptbahnhof kommt es noch auf allen Linien zu Zugausfällen und Verspätungen. Die
Züge der Linie S11 fallen aus.",
```
68 "publication": {

69 "begin": "2015-01-01T13:00:00.000+0100",

70 "end": "2017-10-12T10:00:00.000+0200"

71 },

72 "validities": [

73 {

74 "begin": "2017-10-12T08:00:00.000+0200",

75 "end": "2017-10-12T10:00:00.000+0200"

76 }
77 ],

78 "lastModified": "2017-10-12T08:34:55.877+0200"

79 },

80 ...

81 ],

82 "lastUpdate": "2017-10-12T08:34:55.877+0200"

83 }

HBT GmbH; Version 63.1

24. November 2025 Seite 65 von 107


### 2.10 MethodegetIndividualRoute.

#### Diese Methode berechnet Routen im Individualverkehr. Derzeit versteht das GTI darunter

#### Fußwege und Radstrecken.

#### Im Request können mehrere Startpunkte und mehrere Ziele angeben werden. Bei mehre-

#### ren Zielen wird stets zu jedem Ziel eine Route zurückgegeben. Sind gleichzeitig mehrere Starts

#### gegeben, starten die zurückgegeben Routen beim dichtesten Start aus der Menge der Start-

#### punkte, es gibt also nicht zwingend zu jedem Start eine Route. Über die FeldermaxLengthund

#### maxResultsdes Requests können Routen verworfen werden. Der erste Parameter veranlasst

#### ein Verwerfen von zu langen Routen, der zweite wählt eine Anzahl an kürzesten Routen.

#### Soll also beispielsweise der Fußweg zur dichtesten Haltestelle berechnet werden, kann über

#### eincheckNamevom Typ STATION eine Liste der Haltestellen im Umfeld angefragt werden, die

#### zusammen mitmaxResults=1angetIndividualRoutegegeben wird. DieIndividualRou-

#### teResponseenthält dann die Route der gegebenen Position zur nächstgelegenen Haltestelle.

#### Optional ist die Angabe des Verkehrsmitteltyps (serviceType) oder eines Individualprofils

#### (profile). Der Router berücksichtigt über das Profil bestimmte Einschränkungen oder Neigun-

#### gen des Verkehrsteilnehmers. Beispielsweise werden Rennradfahrer bevorzugt über befestigte

#### Strecken geleitet.

#### 2.10.1 IndividualRouteRequest

#### URL:/gti/public/getIndividualRoute

#### DerIndividualRouteRequestwird in Tabelle 49 beschrieben.

```
Feld Typ Name
starts Liste vonSDName Liste der Startpunkte (muss gefüllt sein)
dests Liste vonSDName Liste der Zielpunkte (muss gefüllt sein)
maxLength Integer Maximale Länge der Ergebnisrouten in Metern
maxResults Integer Maximale Anzahl von Ergebnisrouten
type CoordinateType Bezugssystem der Koordinaten, EPSG_4326
(default) oder EPSG_31467.
serviceType SimpleServiceType Verkehrsmitteltyp, optional, default: FOOTPATH
profile IndividualProfileType Individualprofil, optional, default: FOOT_NORMAL
Tabelle 49:IndividualRouteRequest
```
```
Feld
BICYCLE_NORMAL
BICYCLE_RACING
BICYCLE_QUIET_ROADS
BICYCLE_MAIN_ROADS
BICYCLE_BAD_WEATHER
FOOT_NORMAL
Tabelle 50:IndividualProfileType
```
HBT GmbH; Version 63.1

24. November 2025 Seite 66 von 107


#### 2.10.2 IndividualRouteResponse

#### DieIndividualRouteResponsebesteht aus einer Liste vonIndiviualRoutes die in Tabel-

#### le 51 beschrieben werden.

```
Feld Typ Name
start SDName Start der Route
dest SDName Ziel der Route
paths Path Streckenverlauf als Liste von Pfaden mit Attributen
(z. B. Oberflächenbeschaffenheit)
length Integer Länge der Route in Metern
time Integer Geschätzte Fußweg-/Fahrzeit in Sekunden
serviceType SimpleServiceType Verkehrsmitteltyp der berechneten Routen
Tabelle 51:IndiviualRoute
```
#### 2.10.3 Beispiel

#### Listing 25:IndividualRouteRequest

```
1 {
2 "version": 63,
3 "starts":[
4 {
5 "name":"HBT - Hamburger Berater Team",
6 "city":"Hamburg",
7 "combinedName":"HBT - Hamburger Berater Team",
8 "id":"1501000",
9 "type":"POI",
```
10 "coordinate":{"x":9.985721, "y":53.549983}

11 }

12 ],

13 "dests":[

14 {

15 "name":"Niendorf Nord",

16 "city":"Hamburg",
17 "combinedName":"Niendorf Nord",

18 "id":"Master:91900",

19 "type":"STATION",

20 "coordinate":{"x":9.950054, "y":53.640807}

21 }

22 ],

23 "type":"EPSG_4326",

24 "serviceType":"FOOTPATH"

25 }

HBT GmbH; Version 63.1

24. November 2025 Seite 67 von 107


#### Listing 26:IndividualRouteRespose

```
1 {
2 "returnCode": "OK",
3 "routes": [
4 {
5 "start": {
6 "name": "HBT - Hamburger Berater Team",
7 "city": "Hamburg",
8 "combinedName": "HBT - Hamburger Berater Team",
9 "id": "1501000",
```
10 "type": "POI",

11 "coordinate": { "x": 9.985721, "y": 53.549983 }

12 },

13 "dest": {

14 "name": "Niendorf Nord",

15 "city": "Hamburg",
16 "combinedName": "Niendorf Nord",

17 "id": "Master:91900",

18 "type": "STATION",

19 "coordinate": { "x": 9.950054, "y": 53.640807 }

20 },

21 "paths": [

22 {

23 "track": [

24 { "x": 9.985726, "y": 53.54998 },

25 { "x": 9.985862, "y": 53.549988 },

26 { "x": 9.985835, "y": 53.550158 },

27 { "x": 9.985822, "y": 53.550248 },

28 { "x": 9.985782, "y": 53.550473 },

29 { "x": 9.985843, "y": 53.550482 }

30 ],

31 "attributes": [

32 "SURFACE_UNKNOWN"

33 ]

34 },

35 ...

36 ],

37 "length": 12060,
38 "time": 181,

39 "serviceType": "FOOTPATH"

40 }

41 ]

42 }

HBT GmbH; Version 63.1

24. November 2025 Seite 68 von 107


### 2.11 MethodengetVehicleMapundgetTrackCoordinates

#### Die MethodegetVehicleMapermöglicht es dem Client eine Liste aller ÖV-Fahrzeuge und deren

#### Fahrtverlauf zu einem bestimmten Zeitabschnitt in einer bestimmten Gegend zu erhalten. Dabei

#### kann spezifiziert werden, ob Fahrplandaten oder Livedaten verwendet werden sollen.

#### Dabei werden für alle Fahrzeuge, die im Laufe ihrer Fahrt die Gegend (Bounding-Box)

#### schneiden, die Streckenabschnitte zurück gegeben, die den Zeitabschnitt schneiden und wieder-

#### um den Ausschnitt schneiden.

#### Aus Perfomancegründen sollte das FlagVehicleMapRequest.withoutCoordsgesetzt wer-

#### den. In diesem Fall können über denTrackCoordinatesRequest die Koordinaten für die

#### Streckenabschnitte bei Bedarf nachgeholt werden.

#### Diese Methode kann z.B. benutzt werden um eine Karte mit den aktuellen Fahrzeugposi-

#### tionen anzuzeigen.

#### 2.11.1 VehicleMapRequest

#### URL:/gti/public/getVehicleMap

#### Der Request wird in Tabelle 52 beschrieben.

```
Feld Typ Name
boundingBox BoundingBox Der Ausschnitt (Gegend)
periodBegin Long Zeitstempel des Periodenbegins (UNIX-time)
periodEnd Long Zeitstempel des Periodenendes (UNIX-time)
withoutCoords Boolean Es sollen keine Koordinaten zurückgesendet werden
coordinateType CoordinateType Das gewünschte Koordinatenreferenzsystem,
Achtung: der Server muss sich nicht daran halten
vehicleTypes Liste vonVehicleType Die Liste der gewünschten Fahrzeugtypen
realtime boolean Bestimmt, ob Echtzeit- oder Fahrplandaten
zurückgegeben werden sollen
Tabelle 52:VehicleMapRequest
```
#### EineBoundingBoxenthällt 2Coordinate:lowerLeft&upperRight, welche zwischen

#### sich ein Gebiet eingrenzen (in der GIS-Sprache:EnvelopeoderBoundingBox)

#### 2.11.2 VehicleMapResponse

#### Die Response besteht aus einer Liste vonJourney(Fahrten), die in Tabelle 53 beschrieben

#### werden.

HBT GmbH; Version 63.1

24. November 2025 Seite 69 von 107


```
Feld Typ Name
journeyID String Eindeutige ID der Fahrt
line Service Eindeutige ID der Linie, deren Teil die Fahrt ist. Wird in
Tabelle 54 beschrieben
vehicleType VehicleType Der Fahrzeugtyp, mit dem diese Linie betrieben wird. Mögliche
Werte sind in Tabelle 57 aufgezählt.
realtime Boolean Zeigt an, ob die Daten echtzeitbehaftet sind
segments Liste vonPathSegment Die Streckenabschnitte
Tabelle 53:Journey
```
```
Feld Typ Name
name String Der Name der Linie, z.B. ”S1”
direction String Ziel/Richtung der Fahrt
origin String Start/Ursprung der Fahrt
type ServiceType Typ der Linie, wird in Tab. 55 beschrieben
id String ID der Linie
dlid String DLID der Linie
Tabelle 54:Service
```
```
Feld Typ Name
simpleType SimpleServiceType Type der Linie, Eine Auzählung, die in Tab. 56 beschrieben wird
shortInfo String Eine kurze Info zur Linie
longInfo String Eine längere Info zur Linie
model String Zusätzliche Informationen über die Art des Verkehrsmittels, z.B
(„DT4”, „Midibus”,... ) (Seit API Version 24)
Tabelle 55:ServiceType
```
```
Feld
BUS
TRAIN
SHIP
FOOTPATH
BICYCLE
AIRPLANE
CHANGE
CHANGE_SAME_PLATFORM
ACTIVITY_BIKE_AND_RIDE
Tabelle 56:SimpleServiceType
```
HBT GmbH; Version 63.1

24. November 2025 Seite 70 von 107


```
Wert Beschreibung
REGIONALBUS Regionalbusse. Busse, die nicht unter die vier folgenden
Bustypen fallen
METROBUS Metrobus
NACHTBUS Nachtbus
SCHNELLBUS Schnellbus
XPRESSBUS XpressBus
AST Anruf-Sammel-Taxi, sonstige Verkehrsmittel, die nur bei
vorherigem Telefonanruf fahren
SCHIFF Fähre
U_BAHN U-Bahn
S_BAHN S-Bahn
A_BAHN A-Bahn
R_BAHN Regionalbahn
F_BAHN Fernbahn
Tabelle 57:VehicleType
```
#### Der TypPathSegmentwird in Tabelle 58 beschrieben.

```
Feld Typ Name
startStopPointKey String Der StopPointKey des Segment-Starts
endStopPointKey String Der StopPointKey des Segment-Endes
startStationName String Der Stationsname des Segment-Starts
startStationKey String Der StationKey des Segment-Starts
startDateTime String Der Zeitstempel zu dem das Fahrzeug am Anfang des
Tracks ist (UNIX-time)
endStationName String Der Stationsname des Segment-Endes
endStationKey String Der StationKey des Segment-Endes
endDateTime String Der Zeitstempel zu dem das Fahrzeug am Ende des
Tracks ist (UNIX-time)
track VehicleMapPath Streckenverlauf in Koordinaten. Wird nur gesetzt,
fallswithoutCoordsim Request nicht gesetzt ist.
destination String Richtung der Fahrt. Informationsgehalt hängt von
diesem Streckenabschnitt ab
realtimeDelay Integer Verspätung in Minuten
isFirst Boolean Zeigt an, ob dies der erste Abschnitt der Fahrt ist
isLast Boolean Zeigt an, ob dies der letzte Abschnitt der Fahrt ist
Tabelle 58:PathSegment
```
#### Der Typ VehicleMapPathist eine platzsparendere Version des Typs Path. Er wird in

#### Tabelle 59 beschrieben.

```
Feld Typ Name
track Liste vonDouble Eine Liste vonDouble. Je zwei hintereinander
folgendeDoublebilden eine Koordinate.
coordinateType CoordinateType Das Koordinatensystem, in welchem die Werte von
trackinterpretiert werden müssen.
Tabelle 59:VehicleMapPath
```
HBT GmbH; Version 63.1

24. November 2025 Seite 71 von 107


#### 2.11.3 Beispiel

#### Listing 27:VehicleMapRequest

```
1 {
2 "version":63,
3 "boundingBox":{
4 "lowerLeft":{"x":9.986250400543213, "y":53.54789377955267, "type":"EPSG_4326"},
5 "upperRight":{"x":9.739487171173096, "y":53.40829355253501, "type":"EPSG_4326"}
6 },
7 "periodBegin":1507797056,
8 "periodEnd":1507840256,
9 "withoutCoords":true,
```
10 "coordinateType":"EPSG_31467",

11 "vehicleTypes":["F_BAHN", "R_BAHN", "S_BAHN", "A_BAHN", "SCHIFF", "XPRESSBUS"],

12 "realtime":false

13 }

#### Listing 28:VehicleMapResponse

```
1 {
2 "returnCode": "OK",
3 "journeys": [
4 {
5 "journeyID": "ZVU-DB:S3_ZVU-DB_S-ZVU.1.52.PISTAD.N.520.null (subline 52, sdIndex 10,
Fahrt 0)",
6 "line": {
7 "name": "S3",
8 "direction": "Stade",
9 "type": {
```
10 "simpleType": "TRAIN"

11 },

12 "id": "ZVU-DB:S3_ZVU-DB_S-ZVU"

13 },

14 "vehicleType": "S_BAHN",

15 "realtime": true,

16 "segments": [

17 {

18 "startStopPointKey": "ZVU-DB:499101:1",

19 "endStopPointKey": "ZVU-DB:409101:1",

20 "startStationName": "Harburg",

21 "startStationKey": "Master:49950",

22 "startDateTime": 1507797660,

23 "endStationName": "Harburg Rathaus",
24 "endStationKey": "Master:40950",

25 "endDateTime": 1507797780,

26 "destination": "Stade",

27 "realtimeDelay": 7,

28 "isFirst": false,

29 "isLast": false

30 },

31 {

HBT GmbH; Version 63.1

24. November 2025 Seite 72 von 107


32 "startStopPointKey": "ZVU-DB:409101:1",

33 "endStopPointKey": "ZVU-DB:429101:1",

34 "startStationName": "Harburg Rathaus",

35 "startStationKey": "Master:40950",

36 "startDateTime": 1507797780,

37 "endStationName": "Heimfeld",

38 "endStationKey": "Master:42950",

39 "endDateTime": 1507797840,

40 "destination": "Stade",

41 "realtimeDelay": 6,

42 "isFirst": false,

43 "isLast": false

44 },

45 ...

46 ]

47 },

48 {

49 "journeyID": "ZVU-DB:S1_ZVU-DB_S-ZVU.6.6.PBSB .N.520.null (subline 6, sdIndex 1,

```
Fahrt 2)",
```
50 "line": {

51 "name": "S1",
52 "direction": "Blankenese",

53 "type": {

54 "simpleType": "TRAIN"

55 },

56 "id": "ZVU-DB:S1_ZVU-DB_S-ZVU"

57 },

58 "vehicleType": "S_BAHN",

59 "realtime": true,

60 "segments": [

61 {

62 "startStopPointKey": "ZVU-DB:119107:1",

63 "endStopPointKey": "ZVU-DB:809101:1",

64 "startStationName": "Stadthausbrücke",

65 "startStationKey": "Master:11952",

66 "startDateTime": 1507799580,

67 "endStationName": "Landungsbrücken",

68 "endStationKey": "Master:80950",

69 "endDateTime": 1507799700,

70 "destination": "Blankenese",

71 "realtimeDelay": 0,

72 "isFirst": false,

73 "isLast": false
74 },

75 {

76 "startStopPointKey": "ZVU-DB:809101:1",

77 "endStopPointKey": "ZVU-DB:809103:1",

78 "startStationName": "Landungsbrücken",

79 "startStationKey": "Master:80950",

80 "startDateTime": 1507799700,

81 "endStationName": "Reeperbahn",

82 "endStationKey": "Master:80951",

83 "endDateTime": 1507799820,

84 "destination": "Blankenese",

85 "realtimeDelay": 0,

86 "isFirst": false,

HBT GmbH; Version 63.1

24. November 2025 Seite 73 von 107


87 "isLast": false

88 },

89 ...

90 ]

91 },

92 ...

93 ]

94 }

#### 2.11.4 TrackCoordinatesRequest

#### URL:/gti/public/getTrackCoordinates

#### Der Client erhält die Koordinaten zu bestimmten Streckenabschnitten durch denTrackCoor-

#### dinatesRequest. Da einige Streckenabschnitte öfters angefragt werden, ist es ökonomischer,

#### nur einmal die Koordinaten für diese Abschnitte anzufragen. Hierzu dient dieser Request, der

#### in Tabelle 60 beschrieben wird.

```
Feld Typ Name
coordinateType CoordinateType Das gewünschte Koordinatenreferenzsystem,
Achtung: der Server muss sich nicht daran halten
stopPointKeys Liste vonString Eine Liste vonStopPointKeys. Je zwei
aufeinanderfolgende Strings representieren einen
Streckenabschnitt.
Tabelle 60:TrackCoordinatesRequest
```
#### 2.11.5 TrackCoordinatesResponse

#### Die Response besteht aus zwei geordneten Listen. Das n -te Element vonTrackCoordina-

#### tesResponse.trackIDs(Ein String, bestehend aus dem Start-StopPointKey des Streckenab-

#### schnitts, einem ”∗” und dem End-StopPointKey des Streckabschnitts) identifiziert das n -te

#### Element vonTrackCoordinatesResponse.tracks(EinVehicleMapPath, der die Koordina-

#### ten für einen Streckenabschnitt enthält).

#### 2.11.6 Beispiel

#### Listing 29:TrackCoordinatesRequest

```
1 {
2 "version":63,
3 "coordinateType":"EPSG_4326",
4 "stopPointKeys":[
5 "ZVU-DB:8004248:2","ZVU-DB:8004247:2",
6 "ZVU-DB:809100:1","ZVU-DB:119106:1",
7 "ZVU-DB:429101:1","ZVU-DB:419103:1",
```
HBT GmbH; Version 63.1

24. November 2025 Seite 74 von 107


```
8 ...
9 ]
```
10 }

#### Listing 30:TrackCoordinatesResponse

```
1 {
2 "returnCode": "OK",
3 "trackIDs": [
4 "ZVU-DB:8004248:2*ZVU-DB:8004247:2",
5 "ZVU-DB:809100:1*ZVU-DB:119106:1",
6 "ZVU-DB:429101:1*ZVU-DB:419103:1",
7 ...
8 ],
9 "tracks": [
```
10 {

11 "track": [

12 9.819357930428565,

13 53.474756741591555,

14 9.819357757192398,

15 53.4747477574321,

16 ...

17 ],

18 "coordinateType": "EPSG_4326"

19 },

20 {

21 "track": [

22 9.970592739589032,

23 53.54623412569607,

24 9.971028521129297,

25 53.546158702368494,

26 ...

27 ],

28 "coordinateType": "EPSG_4326"
29 },

30 {

31 "track": [

32 9.963175016379674,

33 53.465407532129674,

34 9.963159757749652,

35 53.46539866976629,

36 ...

37 ],

38 "coordinateType": "EPSG_4326"

39 },

40 ...

41 ]

42 }

### 2.12 MethodecheckPostalCode

#### URL:/gti/public/checkPostalCode

HBT GmbH; Version 63.1

24. November 2025 Seite 75 von 107


#### Ein Aufruf voncheckPostalCodeliefert zu einemPCRequesteinePCResponse, die angibt, ob

#### das Postleitzahlgebiet im HVV Bereich liegt. DerPCRequestbesitzt nur das FeldpostalCode

#### mit TypInteger, welches die zu prüfende Postleitzahl enthält.

#### 2.12.1 Beispiel

#### Das Beispiel in den Listings 31 und 32 zeigt den möglichenPCRequest.

#### Listing 31:PCRequest

1 {

2 "version":63,

3 "postalCode":24558

4 }

#### Listing 32:PCResponse

1 {

2 "returnCode": "OK",

3 "isHVV": true

4 }

HBT GmbH; Version 63.1

24. November 2025 Seite 76 von 107


### 2.13 MethodegetStationInformation.

#### Die MethodegetStationInformationliefert zu einer Haltestelle zusätzliche Informationen.

#### Diese können einen Link zu einer Haltestellenskizze, oder Informationen über Aufzüge an die-

#### ser Haltestelle beinhalten. Ob diese zusätzlichen Informationen vorhanden sind, steht im Feld

#### SDName.hasStationInformation, welches z.B. über einencheckNameermittelt wird.

#### 2.13.1 StationInformationRequest

#### URL:/gti/public/getStationInformation

#### Die MethodegetStationInformationnimmt als Eingabe einenStationInformationRe-

#### quest. Die zu überprüfende Haltestelle wird im FeldStationInformationRequest.station

#### alsSDNameangegeben.

#### 2.13.2 StationInformationResponse

#### Die MethodegetStationInformation liefert als Ergebnis eine StationInformationRe-

#### sponsezurück. In Tabelle 61 werden die Felder vorgestellt.

```
Feld Typ Beschreibung
partialStations Liste vonPartialStation Beinhaltet die Informationen über die Haltestelle.
lastUpdate GTITime Zeitpunkt, zu dem die Daten zuletzt auf den Servern aktualisiert worden
sind.
Tabelle 61:StationInformationResponse
```
#### Das Feld partialStations ist meistens nur mit einem Eintrag gefüllt, welcher für die

#### gesamte Haltestelle steht. Es gibt jedoch auch Ausnahmen, wie z.B. Berliner Tor, bei der der

#### U-Bahn-Verkehr separat in einem zweiten Eintrag behandelt wird. Der TypPartialStation

#### wird in Tabelle 62 beschrieben.

```
Feld Typ Beschreibung
lines Liste vonstrings Beinhaltet die Linien, welche an dieser Teilhaltestelle bedient werden. Kann
leer oder ungesetzt sein.
stationOutline URL Link zu einer Haltestellenskizze für diese Teilhaltestelle.
elevators Liste vonElevator Die Aufzüge an dieser Teilhaltestelle.
Tabelle 62:PartialStation
```
#### Falls das Feldlinesleer oder ungesetzt ist, so werden alle Linien bedient, die die Haltestelle

#### anfahren und nicht explizit in einer anderen Teilhaltestelle gesetzt sind.

HBT GmbH; Version 63.1

24. November 2025 Seite 77 von 107


#### Der TypElevatorwird in Tabelle 63 beschrieben.

```
Feld Typ Beschreibung
lines Liste vonstrings Die Linien, die über diesen Aufzug erreicht werden können.
label string Identifiziert den Aufzug an dieser Haltestelle.
cabinWidth integer Die Breite der Aufzugskabine (in cm).
cabinLength integer Die Tiefe der Aufzugskabine (in cm).
doorWidth integer Die Breite der Aufzugstür (in cm).
description string Beschreibung des Aufzugs.
elevatorType string Der Auzugstyp.
buttonType ElevatorButtonType Der Typ der Aufzugsknöpfe.
state ElevatorState Der Zustand des Aufzugs.
cause string Ein eventueller Grund für den Aufzugszustand.
Tabelle 63:Elevator
```
#### Der TypButtonTypeist ein Enum und kann die WerteBRAILLE,ACUSTIC,COMBIund

#### UNKNOWNannehmen. Der TypElevatorStateist ein Enum und kann die WerteREADY,OU-

#### TOFORDERundUNKNOWNannehmen.

#### 2.13.3 Beispiel

#### In Listings 33 und 34 werden Zusatzinformationen zur Haltestelle Berliner Tor angefragt.

#### Listing 33:StationInformationRequestzur Haltestelle „Berliner Tor“

```
1 {
2 "version":63,
3 "station": {
4 "id": "Master:10952"
5 }
6 }
```
#### Listing 34:StationInformationResponsezur Haltestelle „Berliner Tor“

```
1 {
2 "returnCode": "OK",
3 "partialStations": [
4 {
5 "stationOutline": "http://www.geofox.de/images/mobi/stationDescriptions/
Berliner_Tor_S_ 200217 _ZM3.jpg"
6 },
7 {
8 "lines": [
9 "U2",
```
10 "U3"

11 ],

12 "stationOutline": "http://www.geofox.de/images/mobi/stationDescriptions/

```
Berliner_Tor_U_ 200217 _ZM3.jpg",
```
HBT GmbH; Version 63.1

24. November 2025 Seite 78 von 107


13 "elevators": [

14 {

15 "lines": [

16 "U2",

17 "U3",

18 "U4"

19 ],

20 "label": "A",

21 "cabinWidth": 93,

22 "cabinLength": 216,

23 "doorWidth": 90,

24 "description": "Schalterhalle <-> U2 Ri. Niendorf Nord und U3 Ri. Schlump/Barmbek

```
und U4 Ri. HafenCity Universität",
```
25 "elevatorType": "Durchlader",

26 "buttonType": "COMBI",

27 "state": "READY"

28 },

29 {

30 "lines": [

31 "U2",

32 "U3",
33 "U4"

34 ],

35 "label": "B",

36 "cabinWidth": 93,

37 "cabinLength": 216,

38 "doorWidth": 90,

39 "description": "Schalterhalle <-> U2 Ri. Mümmelmannsberg und U3 Ri. Wandsbek

```
Gartenstadt und U4 Ri. Billstedt",
```
40 "elevatorType": "Durchlader",

41 "buttonType": "COMBI",

42 "state": "READY"

43 },

44 {

45 "label": "C",

46 "cabinWidth": 93,

47 "cabinLength": 216,

48 "doorWidth": 90,

49 "description": "Zugang Beim Strohhause <-> Schalterhalle",

50 "elevatorType": "Durchlader",

51 "buttonType": "COMBI",

52 "state": "READY"

53 }
54 ]

55 }

56 ],

57 "lastUpdate": {

58 "date": "12.10.2017",

59 "time": "12:33"

60 }

61 }

HBT GmbH; Version 63.1

24. November 2025 Seite 79 von 107


### 2.14 MethodetariffZoneNeighbours

#### DerTariffZoneNeighboursRequestliefert alle zum HVV gehörenden Tarifzonen und der

#### jeweiligen benachbarten Tarifzonen.

#### 2.14.1 TariffZoneNeighboursRequest

#### URL:/gti/public/tariffZoneNeighbours

#### DerTariffZoneNeighboursRequestbietet keine Einstellungsmöglichkeiten.

#### 2.14.2 TariffZoneNeighboursResponse

#### DerTariffZoneNeighboursResponsewird in Tabelle 64 beschrieben.

```
Feld Typ Beschreibung
zone string Eine Tarifzone im HVV.
ring string Der Tarifring in dem sich die Tarifzone befindet.
neighbours Liste vonstring Die zur Tarifzone benachbarten Tarifzonen.
Tabelle 64:TariffZoneNeighboursResponse
```
#### 2.14.3 Beispiel

#### Nachfolgend wird ein Beispiel-Request dargestellt.

#### Listing 35:TariffZoneNeighboursRequest

```
1 {}
```
#### Listing 36:TariffZoneNeighboursResponse

```
1 {
2 "tariffZones": [
3 {
4 "zone": "000",
5 "ring": "A",
6 "neighbours": [
7 "101",
8 "103",
9 "105",
```
10 "106",

11 "108"

12 ]
13 },

14 {

HBT GmbH; Version 63.1

24. November 2025 Seite 80 von 107


15 "zone": "101",

16 "ring": "A",

17 "neighbours": [

18 "000",

19 "103",

20 "108",

21 "201",

22 "203",

23 "209"

24 ]

25 },

26 ...

27 ]

28 }

### 2.15 MethodetariffMetaData.

#### DerTariffMetaDataRequestliefert alle möglichen Ticket-Bereichs-Kombinationen zurück.

#### 2.15.1 TariffMetaDataRequest

#### URL:/gti/public/tariffMetaData

#### ImTariffMetaDataRequestkann die anzuzeigende Sprache eingestellt werden (siehe 1.4.)

#### 2.15.2 TariffMetaDataResponse

#### DerTariffMetaDataResponsewird in Tabelle 65 beschrieben.

```
Feld Typ Beschreibung
tariffKinds Liste vonTariffKind Liste der Kartenarten.
tariffLevels Liste vonTariffLevel Liste der Tariflevel.
tariffCounties Liste von
TariffCounty
```
```
Liste der Landkreise.
```
```
tariffZones Liste vonTariffZone Liste der Tarifzonen.
tariffRings Liste vonstring Liste der Tarifringe.
Tabelle 65:TariffMetaDataResponse
```
#### Der TypTariffKindwird in Tabelle 66 beschrieben.

HBT GmbH; Version 63.1

24. November 2025 Seite 81 von 107


```
Feld Typ Beschreibung
id integer Id der Kartenart.
label string Name der Kartenart.
requiresPersonType boolean Gibt an ob weitere Informationen bezüglich der Person, welche
dieses Ticket benutzt, benötigt werden, optional.
ticketType TicketType Gibt an ob das Ticket eine Einzelkarte oder eine Zeitkarte ist
(enumsSINGLE_TICKET, SEASON_TICKET, optional.
levelCombinations Liste voninteger Liste der möglichen Tariflevel-Kombinationen für dieses
Ticket, optional.
Tabelle 66:TariffKind
```
#### Der TypTariffLevelwird in Tabelle 67 beschrieben.

```
Feld Typ Beschreibung
id integer Id des Tariflevels.
label string Name der Tariflevels.
requiredRegionType RequiredRegionType Gibt an, was für dieses Tariflevel an weiteren Informationen
benötigt werden (z.B. 2 Zonen o.Ä.)
Tabelle 67:TariffLevel
```
#### Der TypRequiredRegionTypewird in Tabelle 68 beschrieben.

```
Feld Typ Beschreibung
type TariffRegionType Typ der benötigten Bereiche (enumsZONE, GH_ZONE, RING,
COUNTY).
count integer Anzahl der benötigten Bereiche.
Tabelle 68:RequiredRegionType
```
#### Der TypTariffCountywird in Tabelle 69 beschrieben.

```
Feld Typ Beschreibung
id string Id des Landkreises.
label string Name des Landkreises.
Tabelle 69:TariffCounty
```
HBT GmbH; Version 63.1

24. November 2025 Seite 82 von 107


#### Der TypTariffZonewird in Tabelle 70 beschrieben.

```
Feld Typ Beschreibung
zone string Die Nummer der Tarifzone.
ring string Der ring, der die Zone beinhaltet.
neighbours Liste vonstring Liste der benachbarten Zonen.
Tabelle 70:TariffZone
```
#### 2.15.3 Beispiel

#### Nachfolgend wird ein Beispiel-Request dargestellt.

#### Listing 37:TariffMetaDataRequest

```
1 {
2 "version":63,
3 "language": "de"
4 }
```
#### Listing 38:TariffMetaDataResponse

```
1 {
2 "tariffKinds": [
3 {
4 "id": 1,
5 "label": "Einzelkarte",
6 "ticketType": "SIBGLE_TICKET",
7 "levelCombinations": [1, 66, 2, 8, 9, 14, 15, 22, 23, 24, 100, 38, 40, 41, 42, 43,
44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54]
8 }, ...
9 {
```
10 "id": 56,

11 "label": "ProfiTicket",

12 "ticketType": "SEASON_TICKET",

13 "levelCombinations": [22, 23 15]

14 },

15 ...

16 ],

17 "tariffLevels": [

18 {

19 "id": 1,

20 "label": "1 Tarifzone",

21 "requiredRegionType": {

22 "type": "ZONE",

23 "count": 1

24 }
25 }, ...

26 {

HBT GmbH; Version 63.1

24. November 2025 Seite 83 von 107


27 "id": 23,

28 "label": "3 Ringe",

29 "requiredRegionType": {

30 "type": "RING",

31 "count": 3

32 }

33 }, ...

34 {

35 "id": 44,

36 "label": "Stadtverkehr Wahlstedt"

37 },

38 ...

39 ],

40 "tariffCounties": [

41 {

42 "id": "PI",

43 "label": "Kreis Pinneberg"

44 },

45 ...

46 ],

47 "tariffZones": [
48 {

49 "zone": "307",

50 "ring": "B"

51 },

52 ...

53 ],

54 "tariffRings": [

55 "A",

56 "B",

57 "C",

58 "D",

59 "E"

60 ]

61 }

### 2.16 MethodesingleTicketOptimizer.

#### Die MethodesingleTicketOptimizer berechnet unter Berücksichtigung von vorhandenen

#### Zeitkarten für eine Gruppe von Personen die optimale Ticketkombination für eine bestimmte

#### Fahrt (Tarifberater).

#### 2.16.1 SingleTicketOptimizerRequest

#### URL:/gti/public/singleTicketOptimizer

#### Der Request wird in Tabelle 71 beschrieben.

HBT GmbH; Version 63.1

24. November 2025 Seite 84 von 107


```
Feld Typ Beschreibung
withReturnJourney boolean Fahrkarten für den Rückweg mit einbeziehen
numberOfAdults int Anzahl der mitfahrenden Erwachsenen
numberOfChildren int Anzahl der mitfahrenden Kinder
tickets Liste vonTariffOptimizerTicket Liste der vorhandenen Zeitkarten
route Liste vonSingleTicketOptimizerRequestRoute Die Route für die die Fahrkarten berechnet
werden soll
Tabelle 71:SingleTicketOptimizerRequest
```
```
Feld Typ Beschreibung
tariffKindId int ID der Fahrkartenart
tariffKindLabel string Name der Fahrkartenart
tariffLevelId int ID der Tarifstufe
tariffLevelLabel string Name der Tarifstufe
tariffRegions string Tarifbereiche die von dieser Fahrkarte abgedeckt werden
regionType enumTicketRegionType Typ der Tarifbereiche (z.B. Tarifzone oder Tarifringe)
count int Anzahl Fahrkarten
extraFare boolean Gibt an, ob es sich um eine Zuschlagskarte handelt
personType enumTariffPersonType Personentyp für den diese Fahrkarte gültig ist
centPrice int Fahrkartenpreis in Cent
Tabelle 72: Die Felder vonTariffOptimizerTicket
```
```
Feld Typ Beschreibung
trip SingleTicketOptimizerRequestTrip Teil der Route mit Start, Ziel und Linie
departure dateTime Abfahrtszeit der Route
arrival dateTime Ankunftszeit der Route
tariffRegions TariffOptimizerRegions durchfahrene Tarifbereiche
singleTicketTariffLevelId int Einzelkartentarifstufe für die Route
extraFareType TariffExtraFareType Zuschlagstyp
Tabelle 73: Die Felder vonSingleTicketOptimizerRequestRoute
```
#### 2.16.2 SingleTicketOptimizerResponse

#### DieSingleTicketOptimizerResponseenthält nur die zu kaufenden Tickets (Tabelle 71).

```
Feld Typ Beschreibung
tickets TariffOptimizerTicket Liste der Ergebnistickets
Tabelle 74:SingleTicketOptimizerResponse
```
HBT GmbH; Version 63.1

24. November 2025 Seite 85 von 107


### 2.17 MethodeticketList

#### Die Methode ermöglicht es dem Client, eine Liste aller HVV Tickets abzufragen. Es ist zudem

#### möglich nur die HVV Tickets abzufragen, die an einer, per StationKey übergebenen, Station

#### verkauft werden.

#### 2.17.1 TLRequest

#### URL:/gti/public/ticketList

#### Der Request wird in Tabelle 75 beschrieben.

```
Feld Typ Beschreibung
stationKey string Legt fest für welche Station (Ein Geofox typischer
StationKey hat beispielsweise die Form:
Master:12345) die HVV Tickets abgefragt
werden. Optional, wenn nicht angegeben,
werden alle Tickets zurückgeliefert.
Tabelle 75:TLRequest
```
#### 2.17.2 TLResponse

#### Die Response wird in Tabelle 76 beschrieben.

```
Feld Typ Beschreibung
ticketInfos Liste von
TicketListTicketInfos
```
```
Liste aller Tickets.
```
Tabelle 76:TLResponse

#### Der TypTicketListTicketInfoswird in Tabelle 77 beschrieben.

HBT GmbH; Version 63.1

24. November 2025 Seite 86 von 107


```
Feld Typ Beschreibung
tariffKindID int ID der Kartenart
tariffKindLabel string Name der Kartenart
tariffLevelID int ID der Tarifstufe
tariffLevelLabel string Name der Tarifstufe
tariffGroupID int ID der Tarifgruppe
tariffGroupLabel string Name der Tarifgruppe
regionType Enum Werte:ZONE,GH_ZONE,RING,COUNTY,ZG,NET
selectableRegions int Anzahl der auswählbaren Regionen des
Tickets. Für ’2 Tarifzonen’ wäre es bspw. 2
requiredStartStation boolean Wenn true wird die Startstation benötigt, um
die Gültigkeit zu verifizieren.
personInfos Liste vonPersonInfo Enthält Informationen darüber wieviele
Personen von einem bestimmten Typ mit der
Karte fahren dürfen.
validityPeriods Liste von
ValidityPeriod
```
```
Enthält Informationen über die Gültigkeit
des Tickets.
variants Liste vonTicketList-
TicketVariant
```
```
Enthält Informationen über die
Ticketvarianten. (Beispiel: 1. Klasse Ticket
und 2. Klasse Ticket wären zwei verschiedene
Ticketvarianten)
Tabelle 77:TicketListTicketInfos
```
#### Der TypPersonInfowird in Tabelle 78 beschrieben.

```
Feld Typ Beschreibung
personType Enum Werte:ALL,ELDERLY,APPRENTICE,PUPIL,
STUDENT,CHILD
personCount int Anzahl der Personen die mit dem Ticket
fahren dürfen.
Tabelle 78:PersonInfo
```
#### Der TypValidityPeriodwird in Tabelle 79 beschrieben.

```
Feld Typ Beschreibung
day Enum Werte:WEEKDAY,WEEKEND
timeValidities Liste vonTimePeriod Die Zeit in der das Ticket gültig ist
Tabelle 79:ValidityPeriod
```
#### Der TypTimePeriodwird in Tabelle 80 beschrieben.

HBT GmbH; Version 63.1

24. November 2025 Seite 87 von 107


```
Feld Typ Beschreibung
begin string Beginn der Gültigkeitsperiode. Format: HH:mm
(Enthält ggf. Stunden-Werte > 24. 30:00 Uhr
entspricht 06:00 Uhr am nächsten Tag)
end string Ende der Gültigkeitsperiode. Format: HH:mm
(Enthält ggf. Stunden-Werte > 24. 30:00 Uhr
entspricht 06:00 Uhr am nächsten Tag)
Tabelle 80:TimePeriod
```
#### Der TypTicketListTicketVariantwird in Tabelle 81 beschrieben.

```
Feld Typ Beschreibung
ticketId int Eindeutige ID der Ticketvariante. Für HVV
die eindeutige 8-stellige HVV ticket ID.
kaNummer int KA-Nummer des Tickets.
price double Der Ticketpreis. (Brutto)
currency string Die Währung des Preises. Wenn nicht
angegeben ist EUR gemeint.
ticketClass Enum Werte:NONE,SECOND,FIRST,SCHNELL.
discount Enum Werte:NONE,ONLINE,SOCIAL.
validityBegin date Das Startdatum der Gültigkeit der
Tariffdaten dieses Tickets.
validityEnd date Das Enddatum der Gültigkeit der Tariffdaten
dieses Tickets.
Tabelle 81:TicketListTicketVariant
```
HBT GmbH; Version 63.1

24. November 2025 Seite 88 von 107


#### 2.17.3 Beispiel

#### Listing 39:TLRequest

```
1 {
2 "language": "de",
3 "version": 63,
4 "stationKey":"Master:92903"
5 }
```
#### Listing 40:TLResponse

```
1 {
2 "ticketInfos": [
3 {
4 "tariffKindID": 1,
5 "tariffKindLabel": "Einzelkarte",
6 "tariffLevelID": 14,
7 "tariffLevelLabel": "Hamburg AB",
8 "tariffGroupID": 1,
9 "tariffGroupLabel": "Einzelkarten",
```
10 "regionType": "GH",

11 "requiredStartStation": false,

12 "personCount": 1,

13 "validityPeriods": [

14 {

15 "day": "WEEKDAY",

16 "timeValidities": [

17 {

18 "begin": "00:00",

19 "end": "30:00"
20 }

21 ]

22 },

23 {

24 "day": "WEEKEND",

25 "timeValidities": [

26 {

27 "begin": "00:00",

28 "end": "30:00"

29 }

30 ]

31 }

32 ],

33 "variants": [

34 {

35 "ticketId": 11014100,

36 "kaNummer": 12027,

37 "price": 5.4,

38 "ticketClass": "FIRST",

39 "discount": "NONE",

40 "validityBegin": "2019-03-01T00:00:00.000+0100",

41 "validityEnd": "2019-12-31T00:00:00.000+0100"
42 },

43 ...

HBT GmbH; Version 63.1

24. November 2025 Seite 89 von 107


44 ]

45 },

46 ...,

47 {

48 "tariffKindID": 23,

49 "tariffKindLabel": "9-Uhr-Gruppenkarte",

50 "tariffLevelID": 24,

51 "tariffLevelLabel": "4 Ringe",

52 "tariffGroupID": 2,

53 "tariffGroupLabel": "Tageskarten",

54 "regionType": "RING",

55 "selectableRegions": 4,

56 "requiredStartStation": false,

57 "personCount": 5,

58 "validityPeriods": [

59 {

60 "day": "WEEKDAY",

61 "timeValidities": [

62 {

63 "begin": "00:00",

64 "end": "06:00"
65 },

66 {

67 "begin": "09:00",

68 "end": "30:00"

69 }

70 ]

71 },

72 {

73 "day": "WEEKEND",

74 "timeValidities": [

75 {

76 "begin": "00:00",

77 "end": "30:00"

78 }

79 ]

80 }

81 ],

82 "variants": [

83 {

84 "ticketId": 13624100,

85 "kaNummer": 20225,

86 "price": 26.5,
87 "ticketClass": "FIRST",

88 "discount": "NONE",

89 "validityBegin": "2019-03-01T00:00:00.000+0100",

90 "validityEnd": "2019-12-31T00:00:00.000+0100"

91 },

92 {

93 "ticketId": 13624107,

94 "kaNummer": 20227,

95 "price": 25.71,

96 "ticketClass": "FIRST",

97 "discount": "ONLINE",

98 "validityBegin": "2019-03-01T00:00:00.000+0100",

99 "validityEnd": "2019-12-31T00:00:00.000+0100"

HBT GmbH; Version 63.1

24. November 2025 Seite 90 von 107


100 },

101 ...

102 ]

103 },

104 ...

105 ]

106 }

HBT GmbH; Version 63.1

24. November 2025 Seite 91 von 107


## 3 Beispiele zur Implementierung von Clients

#### Die folgenden Abschnitte geben Vorschläge zur Implementierung der Signaturerstellung und

#### Verarbeitung von JSON-Nachrichten in verschiedenen Umgebungen.

### 3.1 Objective-C (iOS)

#### 3.1.1 Erstellung der Signatur

#### Es wird die Bibliothek CommonCrypto/CommonHMAC.h benötigt.

#### Listing 41: Signaturerstellung iOS/CommonCrypto

1 NSString*password = @"password";

2 NSString*data = @"Request-Message";

3

4 **const void** *bytesKey = [password cStringUsingEncoding:NSUTF8StringEncoding];

5 **const void** *bytesData = [data cStringUsingEncoding:NSUTF8StringEncoding];

6 **unsigned char** cHMAC[CC_SHA1_DIGEST_LENGTH];

7 CCHmac(kCCHmacAlgSHA1, bytesKey, strlen(bytesKey), bytesData, strlen(bytesData), cHMAC);

8 NSData*hmacSignature = [NSData dataWithBytes:cHMAC length:CC_SHA1_DIGEST_LENGTH];

9 _//Base64 Kodierung der HMACSHA1-Signatur_

#### 3.1.2 Verarbeitung von JSON

#### Die benötigten Methoden zur Serialisierung von JSON werden sowohl vom JSON-Framework

##### 2

#### als auch von TouchJSON^3 bereitgestellt, beide können mitNSDictionary-Objekten umgehen.

#### Es wird TouchJSON empfohlen.

#### Listing 42: Signaturerstellung iOS/TouchJSON

1 **#import** "CJSONSerializer.h"

2 **#import** "CJSONDeserializer.h"

3
4 _//Serialisierung_

5 NSString*jsonString = [[NSString alloc] initWithString:[[CJSONSerializer serializer]

```
serializeDictionary:request_dictionary]];
```
6

7 _//Deserialisierung_

8 NSError*error = nil;

9 NSDictionary*dictionary = [[CJSONDeserializer deserializer] deserializeAsDictionary:

```
jsonResponseString error:&error];
```
(^2) [http://code.google.com/p/json-framework/](http://code.google.com/p/json-framework/)
(^3) [http://code.google.com/p/touchcode/wiki/TouchJSON](http://code.google.com/p/touchcode/wiki/TouchJSON)
HBT GmbH; Version 63.1

24. November 2025 Seite 92 von 107


### 3.2 Java und PHP

#### Für Java und PHP gibt es Beispielimplementierungen unterhttps://github.com/HBTGmbH/

#### gti-example-clients.

### 3.3 Python

#### Listing 43: Signaturerstellung Python

1 def_get_signature(request_body: Dict) -> bytes:

2 """ Private function that creates the signature for geofox request. """

3 **key** = bytes("the given geofox password", "utf-8")

4 hashed = hmac.new( **key** , bytes(json.dumps(request_body), "utf-8"), sha1)

5 signature = base64.b64encode(hashed.digest())

6 return signature

#### Hinweis: Sowohl während der Signaturerstellung als auch für das Senden des Requests muss

#### der Request (request_body) als JSON-String (json.dumps()) vorliegen.

### 3.4 Typescript

#### Listing 44: Signaturerstellung TypeScript

1 function createSignature(requestBody: object): string {

2 const hmac = crypto.createHmac(’sha1’, ’the given geofox password’);

3 hmac.update(JSON.stringify(requestBody));

4 return hmac.digest(’base64’);

5 }

HBT GmbH; Version 63.1

24. November 2025 Seite 93 von 107


## 4 Wichtige Hinweise zur Umsetzung

#### Zur praktischen Umsetzung folgen Hinweise.

### 4.1 Das FeldidinSDName

#### Das Feldid inSDNamebezeichnet verschiedene Typen vonSDNames unterschiedlich genau.

#### SDNames vom TypSTATIONwerden über eine ID eindeutig identifiziert. Mit dem TypAD-

#### DRESSwerden Straßen identifiziert, wobei der Mittelpunkt der Straße als Punkt diesesSDNa-

#### mes betrachtet wird. Möchte man eine postalische Adresse speichern, ist zusätzlich zur ID eine

#### Hausnummer nötig, diese ist dann im Feldnamezu übergeben, von wo sie herausgeparst wird.

#### Orte vom TypPOIwerden über die ID eindeutig identifiziert. Koordinaten (TypCOORDI-

#### NATE) haben keine IDs.

#### EinSDNamewird über die Felderid,typeundcombinedNameeindeutig identifiziert, wobei

#### stattcombinedNameauch die Kombination ausnameundcitygültig ist.

### 4.2 Caching von Stationen und Linien

#### Es gibt Veränderungen an den Haltestellen des Systems, die ab und zu zusammengelegt, aufge-

#### teilt oder gestrichen werden müssen. Dies passiert nicht häufig, aber häufiger, als die Intuition

#### vermuten könnte. Um sicherzustellen, dass die Methoden stets mit aktuellen und damit ver-

#### wertbarenSDNames aufgerufen werden, gibt es zwei Möglichkeiten:

#### 1. Vor jedem Methodenaufruf werden dieSDNames der Eingabe durchcheckNameüberprüft.

#### Diese Variante sichert korrekte Daten, kostet jedoch zusätzliche Anfragen an den Server.

#### 2. Der Client pflegt einen Station Cache.

#### Der Station Cache ist aktuell zu halten und es wird empfohlen, bei jedem Start der Client-

#### anwendung mit eineminitdie aktuelle Version der Daten im FelddataIDzu erfragen. Stimmt

#### diese nicht mit der des Station Cache überein, ist dieser mittelslistStationszu aktualisieren.

#### Auch an den Linien (TypLineListEntry) kann es Veränderungen geben, die jedoch seltener

#### als die an Stationen sind. Da das Versionsfeld dataIDden gesamten Geofox-Datenbestand

#### versioniert, sind bei Änderung alle Caches des Clients zu aktualisieren. Es ist daher auch mög-

#### lich, dass trotz unterschiedlicher Versionsnummern auf Update-Anfrage für einen Cache keine

#### aktualisierten Datensätze zurückgegeben werden.

HBT GmbH; Version 63.1

24. November 2025 Seite 94 von 107


### 4.3 Implementierung: Icons vom Icon Service

#### Zusätzlich zu den Methoden wird ein Dienst bereitgestellt, über den einige Standard-Icons des

#### HVV im PNG-Format abgerufen werden können.

#### Die Icons teilen sich in die drei Arten: Vehicle Icons, Line Icons und Miscellaneous Icons. Bei

#### jedem Abruf eines Icons ist die gewünschte Höhe in Pixeln als Parameter anzugeben, zulässige

#### Werte sind zwischen 10 und 100 Pixel. Manche Pixel sind transparent.

#### 4.3.1 Vehicle Icons

#### Ein Vehicle Icon steht allgemein für Fahrzeugtypen (Verkehrsmittel) wie z.B. U- oder S-Bahn.

#### Eine Besonderheit ist, daß mehrere einzelne Vehicle Icons in einer Grafik gezeigt werden

#### können. Damit ist es mit nur einem Icon möglich, die verschiedenen Verkehrsmittel einer Hal-

#### testelle darzustellen, wie z.B. im Vorschlager von Geofox. Die erzeugten Bilder sind immer

#### quadratisch. Als Parameter ist eine Liste von Vehikeln zu übergeben, die durch Semikolon zu

#### trennen sind. Durch den ParametervarSize=truewird das Bus-Symbol größer dargestellt, als

#### die Anderen. Dies kompensiert die geringere Fläche. Da Vehicle Icons auch über die Service-

#### Types angesprochen werden können, sind in der Tabelle 83 teilweise Alternativen angegeben.

#### Es ist somit beispielsweise möglich dasAKN-Symbol über den Eintragabahn oder über den

#### ServiceTypeaanzufragen.

```
https://cloud.geofox.de/icon/vehicle?types=fbahn;sbahn;ubahn;bus&height=60
```
```
https://cloud.geofox.de/icon/vehicle?types=sbahn&height=60
```
```
https://cloud.geofox.de/icon/vehicle?types=fbahn;sbahn;ubahn;bus&height=60&varSize=true
Tabelle 82: Beispiele für Vehicle Icons
```
#### In Tabelle 83 werden die zulässigen Werte vonvehiclebeschrieben.

HBT GmbH; Version 63.1

24. November 2025 Seite 95 von 107


```
Eintrag Vehicle Icon
```
```
abahnodera AKN
```
```
sbahnoders S-Bahn
```
```
ubahnoderu U-Bahn
```
```
rbahnoderr Regionalbahn
```
```
fbahnodertrain Fernbahn
```
```
bus Bus
```
```
faehreodership Hafenfähre
```
```
ast Anruf-Sammel-Taxi
```
```
fbus Fernbus
```
```
rb Regionalbahn
```
```
re Regionalexpress
```
```
schnellbus Schnellbus
```
```
ice ICE
```
```
Fussweg Fußweg
Tabelle 83: Die zulässigen Einträge vonvehicle
```
HBT GmbH; Version 63.1

24. November 2025 Seite 96 von 107


#### 4.3.2 Line Icons

#### Ein Line Icon beinhaltet sowohl die Nummer der Linie, als auch in seiner Darstellung die Art

#### der Linie.

#### In Tabelle 84 werden einige Beispiele gezeigt.

```
Icon Linientyp URL
U-Bahn https://cloud.geofox.de/icon/line?height=14&lineKey=HHA-U:U1_HHA-U
Regionalbahn https://cloud.geofox.de/icon/line?height=14&lineKey=DB-EFZ:RB81_DB-EFZ_Z
S-Bahn https://cloud.geofox.de/icon/line?height=14&lineKey=SBH:S21_SBH_SBAHNS
Hafenfähre https://cloud.geofox.de/icon/line?height=14&lineKey=ZVU-DB:62_ZVU-DB_HADAGZ
SchnellBus https://cloud.geofox.de/icon/line?height=14&lineKey=HHA-B:37_HHA-B
Xpressbus https://cloud.geofox.de/icon/line?height=14&lineKey=HHA-B:X11_HHA-B
Stadt-/RegionalBus https://cloud.geofox.de/icon/line?height=14&lineKey=HHA-B:4_HHA-B
NachtBus https://cloud.geofox.de/icon/line?height=14&lineKey=HHA-B:600_HHA-B
Tabelle 84: Beispiele für Line Icons
```
#### Ein Linien-Icon kann mithilfe des lineKey, der DLID oder des Linien-Namens abgerufen

#### werden. Zur Verwendung des LineKey muss der/lineEndpunkt mit dem ParameterlineKey

#### aufgerufen werden, für DLIDs gibt es den /dlidEndpunkt mit dem Parameter dlidund

#### Linien-Namen können über den Endpunkt/linename mit dem Parameternameverwendet

#### werden. Alle drei Endpunkte haben zusätzlich folgende Parameter:

```
Parameter Beschreibung
height Höhe des Icons (min. 10, max. 150)
outlined(Optional) Wenn der Hintergrund transparent ist (bspw. bei Regionalbahnen), soll die
Schrift des Icons mit einem weißen Rahmen versehen werden? (default:false)
fileFormat(Optional) Format des Icons (mögliche Werte:PNG, SVG. default:PNG)
appearance(Optional) Erscheinungsbild des Icons (mögliche Werte:COLOURED, MONOCHROME. default:
COLOURED)
Tabelle 85: Parameter für Linien-Icons
```
#### 4.3.3 Miscellaneous Icons

#### Hier finden sich weitere Icons, die eventuell von Nutzen sein können. Auch sind die Fahrzeug-

#### typen aus den Vehicle Icons aufgenommen worden, da einige Icons länglich sind und diese hier,

#### anders als bei den quadratischen Vehicle Icons, auch länglich dargestellt werden. Ein Beispiel ist:

https://cloud.geofox.de/icon/misc?name=busWide&height=60

HBT GmbH; Version 63.1

24. November 2025 Seite 97 von 107


#### Die zulässigen Werte fürmiscwerden in Tabelle 86 beschrieben.

```
Parameter Bedeutung Icon
```
```
abahn AKN
```
```
sbahn S-Bahn
```
```
ubahn U-Bahn
```
```
rbahn Regionalbahn
```
```
fbahn Fernbahn
```
```
bus Bus
```
```
busWide Bus, z.B. als Symbol für viele einzelne Buslinien
```
```
faehre Hafenfähre
```
```
bike Fahrradweg
```
```
foot Fußweg
```
```
ast Anruf-Sammel-Taxi
```
```
fbus Fernbus
```
```
rb Regionalbahn
```
```
re Regionalexpress
```
```
schnellbus Schnellbus
```
```
ice ICE
Tabelle 86: Zulässige Werte fürmisc
```
HBT GmbH; Version 63.1

24. November 2025 Seite 98 von 107


## 5 Status-Codes und Error-Codes

#### Fehler werden auf zwei verschiedenen Kanälen übermittelt: Zum einen werden die HTTP-

#### Status-Codes im HTTP-Header genutzt, zum anderen hat jedeResponse(weil sie vonBase-

#### ResponseTypeerbt) Felder zur Fehlerbehandlung, die sich im HTTP-Body befinden.

#### Diese beziehen sich jedoch nur auf die Kommunikation und nicht auf den Inhalt; ein HTTP-

#### Status-Code200 OKstellt also keine erfolgreiche Verarbeitung des Request (inhaltlich) sicher.

#### Die HTTP-Status-Codes sind Tabelle 87 zu entnehmen.

```
Status-Code im
HTTP-Header
```
```
Fehlerbeschreibung
```
```
400 Bad Request Anfrage ungültig (z.B. XML-Parser-Fehler oder ungültige IDs im Request)
401 Unauthorized Authentifizierung, z.B. Signatur ungültig, IP nicht gewhitelistet
403 Forbidden Zugriff nicht erlaubt
429 Too Many Requests Zu viele Zugriffe pro Zeit. Dieser Fehler sollte im Normalbetrieb nicht
auftreten, da der Zugriffsschutz (wie auch der vongeofox.de) für eine
übliche Häufigkeit ausgelegt ist. Sollte es doch Probleme geben, kann
zusammen mit der HBT GmbH eine Lösung gefunden werden
500 Internal Server Error Programmfehler im GTI
503 Service Unavailable Backendsystem nicht erreichbar
200 OK Kommunikation zunächst fehlerfrei, evtl. jedoch inhaltliche Fehler.
Tabelle 87: HTTP-Status-Codes
```
#### Die in der Response übermittelten Fehler- und Statuscodes werden in Tabelle 88 beschrie-

#### ben.

```
Feld Wert Beschreibung
```
```
returnCode
```
```
OK Keine Fehler
ERROR_CN_TOO_MANY checkNameliefert zu viele Treffer (Suchbegriff ist zu präzisieren)
ERROR_COMM Verbindungsfehler beim Backend-Zugriff
ERROR_ROUTE Es konnte keine Route berechnet werden
ERROR_TEXT Verweis auf die zusätzlichen FeldererrorTextunderrorDevInfo
START_NOT_FOUND Starthaltestelle nicht gefunden
DEST_NOT_FOUND Zielhaltestelle nicht gefunden
VIA_NOT_FOUND Viahaltestelle nicht gefunden
FORCED_START_NOT_FOUND erzwungene Starthaltestelle nicht gefunden
FORCED_DEST_NOT_FOUND erzwungene Zielhaltestelle nicht gefunden
errorText Optionale, für den Benutzer bestimmte Volltext-Fehlermeldung (in der im Request
angegebenen Sprache, sofern vorhanden)
errorDevInfo Für den Entwickler bestimmte Fehlermeldung mit detaillierteren Informationen (z.B.
aufgetretene Exceptions)
Tabelle 88: Zu den Feldern in der Response
```
#### Im FelderrorDevInfowerden oft technische Details geantwortet, im Fehlerfall immer –

#### auch im Fall von Fehlern, die per HTTP-Status gemeldet werden. In Tabelle 89 werden Beispiele

#### für mögliche Kombinationen Fehler/HTTP Code gegeben.

HBT GmbH; Version 63.1

24. November 2025 Seite 99 von 107


```
Fehler HTTP-Code und Felder des Bodies
Programmierfehler im Client: In der
Anfrage ist ein Syntaxfehler, der zu
einem Fehler beim Unmarshalling
(von JSON oder XML) führt
```
```
Status Code:400 Bad Request
Im Body:
"returnCode": "ERROR_TEXT",
"errorDevInfo": "Can not instantiate value of type [simple
type, class ...] from JSON String; no single-String
constructor/factory method"(Fehlermeldung des Unmarshallers)
Programmierfehler im Client: Die
Anfrage ist syntaktisch wohlgeformt,
aber semantisch fehlerhaft, z.B. ein
checkNamemit leerem FeldtheName
(TypSDName)
```
```
Status Code:400 Bad Request
Im Body:
"returnCode": "ERROR_TEXT",
"errorDevInfo": "invalid SDName"
```
```
Programmierfehler im GTI-Server, es
tritt eine interne Exception auf
```
```
Status Code:500 Internal Server Error
Im Body:
"returnCode": "ERROR_TEXT",
errorDevInfoenthält Details zur Exception
Ungültige Haltestellen-ID im Request Status Code:400 Bad Request
Im Body:
"returnCode": "START_NOT_FOUND",
"errorText": "Starthaltestelle nicht gefunden",
"errorDevInfo": "15401 Starthaltestelle nicht gefunden"
Tabelle 89: Beispiele für mögliche Kombinationen Fehler/HTTP Code
```
HBT GmbH; Version 63.1

24. November 2025 Seite 100 von 107


## A Tabellen

#### 1 Felder eines Geofox-HTTP-Paketes......................... 5

#### 2 Mögliche Werte fürX-Platform........................... 5

#### 3 Methoden des aktuellen APIs............................ 12

#### 4 CNRequest...................................... 16

#### 5 Der EnumSDType.................................. 17

#### 6 Die Felder vonSDName................................ 17

#### 7 Die Felder des TypsTariffDetails(inSDName)................. 18

#### 8 GRRequest...................................... 21

#### 9 ContSearch-TimeIsDeparture Zusammenhang................. 23

#### 10 TariffInfoSelector................................ 23

#### 11 Liste der verfügbaren HVV-Karten......................... 24

#### 12 Die Penalties..................................... 24

#### 13 Mögliche Penaltytypen und ihre Werte....................... 25

#### 14 DesiredTypeFahrzeugtypen............................ 26

#### 15 Vergleich http://geofox.hvv.de-Optionen/Penalties................. 28

#### 16 GRResponse..................................... 28

#### 17 Schedule....................................... 29

#### 18 ScheduleElement.................................. 30

#### 19 ContSearchByServiceId.............................. 30

#### 20 Service........................................ 31

#### 21 JourneySDName.................................... 31

#### 22 Vehicle........................................ 32

#### 23 TariffInfo...................................... 32

#### 24 TicketInfo...................................... 33

#### 25 DLRequest...................................... 39

#### 26 DLResponse...................................... 39

#### 27 Departure...................................... 40

#### 28 FilterEntry..................................... 40

#### 29 Fahrzeugtypen für den Verkehrsmittelfilter............... 41

#### 30 TariffRequest.................................... 45

#### 31 Die Felder vonScheduleElementLight...................... 45

#### 32 TariffInfo...................................... 46

#### 33 DCRequest...................................... 49

HBT GmbH; Version 63.1

24. November 2025 Seite 101 von 107


#### 34 CourseElement.................................... 50

#### 35 Vehicle........................................ 50

#### 36 LSRequest...................................... 53

#### 37 LSResponse...................................... 54

#### 38 StationListEntry................................. 54

#### 39 LLRequest...................................... 56

#### 40 LLResponse...................................... 57

#### 41 LineListEntry.................................... 57

#### 42 SublineListEntry................................. 57

#### 43 StationLight.................................... 58

#### 44 AnnouncementRequest............................... 60

#### 45 AnnouncementResponse............................... 60

#### 46 Announcement.................................... 61

#### 47 Location....................................... 62

#### 48 Announcement.Reason............................... 63

#### 49 IndividualRouteRequest............................. 66

#### 50 IndividualProfileType.............................. 66

#### 51 IndiviualRoute................................... 67

#### 52 VehicleMapRequest................................. 69

#### 53 Journey........................................ 70

#### 54 Service........................................ 70

#### 55 ServiceType..................................... 70

#### 56 SimpleServiceType................................. 70

#### 57 VehicleType..................................... 71

#### 58 PathSegment..................................... 71

#### 59 VehicleMapPath................................... 71

#### 60 TrackCoordinatesRequest............................. 74

#### 61 StationInformationResponse.......................... 77

#### 62 PartialStation................................... 77

#### 63 Elevator....................................... 78

#### 64 TariffZoneNeighboursResponse......................... 80

#### 65 TariffMetaDataResponse............................. 81

#### 66 TariffKind...................................... 82

#### 67 TariffLevel..................................... 82

#### 68 RequiredRegionType................................ 82

#### 69 TariffCounty.................................... 82

HBT GmbH; Version 63.1

24. November 2025 Seite 102 von 107


#### 70 TariffZone...................................... 83

#### 71 SingleTicketOptimizerRequest......................... 85

#### 72 Die Felder vonTariffOptimizerTicket..................... 85

#### 73 Die Felder vonSingleTicketOptimizerRequestRoute............. 85

#### 74 SingleTicketOptimizerResponse........................ 85

#### 75 TLRequest...................................... 86

#### 76 TLResponse...................................... 86

#### 77 TicketListTicketInfos.............................. 87

#### 78 PersonInfo...................................... 87

#### 79 ValidityPeriod................................... 87

#### 80 TimePeriod...................................... 88

#### 81 TicketListTicketVariant............................. 88

#### 82 Beispiele für Vehicle Icons.............................. 95

#### 83 Die zulässigen Einträge vonvehicle........................ 96

#### 84 Beispiele für Line Icons................................ 97

#### 85 Parameter für Linien-Icons.............................. 97

#### 86 Zulässige Werte fürmisc............................... 98

#### 87 HTTP-Status-Codes................................. 99

#### 88 Zu den Feldern in der Response........................... 99

#### 89 Beispiele für mögliche Kombinationen Fehler/HTTP Code............ 100

## B Listings

#### 1 HTTP-Post...................................... 6

#### 2 CNRequestfür Haltestelle „Altona“......................... 6

#### 3 CNResponsefür Haltestelle „Altona“........................ 6

#### 4 CNRequestfür Haltestelle „Altona“......................... 7

#### 5 CNResponsefür Haltestelle „Altona“........................ 7

#### 6 InitRequest..................................... 15

#### 7 InitResponse.................................... 15

#### 8 CNRequestzum Begriff „Christuskirche“...................... 18

#### 9 CNResponsezum Begriff „Christuskirche“..................... 19

#### 10 GRRequest...................................... 34

#### 11 GRResponse...................................... 35

HBT GmbH; Version 63.1

24. November 2025 Seite 103 von 107


#### 12 DLRequest...................................... 42

#### 13 DLResponse...................................... 42

#### 14 DLRequest...................................... 44

#### 15 TariffRequest.................................... 46

#### 16 TariffResponse................................... 46

#### 17 DCRequest...................................... 50

#### 18 DCResponse...................................... 51

#### 19 LSRequest...................................... 55

#### 20 LSResponse...................................... 55

#### 21 LLRequest...................................... 59

#### 22 LLResponse...................................... 59

#### 23 AnnouncementRequest............................... 64

#### 24 AnnouncementResponse............................... 64

#### 25 IndividualRouteRequest............................. 67

#### 26 IndividualRouteRespose............................. 68

#### 27 VehicleMapRequest................................. 72

#### 28 VehicleMapResponse................................ 72

#### 29 TrackCoordinatesRequest............................. 74

#### 30 TrackCoordinatesResponse............................ 75

#### 31 PCRequest...................................... 76

#### 32 PCResponse...................................... 76

#### 33 StationInformationRequestzur Haltestelle „Berliner Tor“.......... 78

#### 34 StationInformationResponsezur Haltestelle „Berliner Tor“.......... 78

#### 35 TariffZoneNeighboursRequest.......................... 80

#### 36 TariffZoneNeighboursResponse......................... 80

#### 37 TariffMetaDataRequest.............................. 83

#### 38 TariffMetaDataResponse............................. 83

#### 39 TLRequest...................................... 89

#### 40 TLResponse...................................... 89

#### 41 Signaturerstellung iOS/CommonCrypto....................... 92

#### 42 Signaturerstellung iOS/TouchJSON......................... 92

#### 43 Signaturerstellung Python.............................. 93

#### 44 Signaturerstellung TypeScript............................ 93

HBT GmbH; Version 63.1

24. November 2025 Seite 104 von 107


## C Versionshistorie

```
Datum API -
Version
```
```
Doc -
Version
```
```
Autor Änderung
```
```
24.11.2025 63 1 af, jwi vehicles in DepartureCourse ergänzt.
07.07.2025 62 1 loj,
tkr
```
```
vehicles in Departure ergänzt.
```
```
26.05.2025 61 1 tkr,
jma
```
```
stopPoint in Departure ergänzt und coordinateType in DLRequest
ergänzt.
28.04.2025 60 1 jma Felder für hvv TicketID ergänzt
23.08.2024 59 2 jma starts und dests müssen nun gefüllt sein bei getIndividualRoute
15.08.2024 59 1 km,
bas
```
```
SDNameenthält nun das Feldaddress. Wird nur für POIs gefüllt.
```
```
29.07.2024 58 2 jma,
bas
```
```
SDNameenthält nun das Feld provider, welches bei Activity-Stations
gefüllt ist. BeiACTIVITY_BIKE_AND_RIDEsteht die Provider-Info nun
auch in dem line-Element.
10.07.2024 58 1 jma,
bas
```
```
SimpleServiceTypeenthält nun den TypACTIVITY_BIKE_AND_RIDE.
getRoutekann nun Bike and Ride Stationen bei der Suche
berücksichtigen
21.05.2024 57 1 bas getRouteliefert nun Informationen zu den Fahrzeugen, die eine Fahrt
durchführen
30.04.2024 56 3 bas (zu Version 58.1 verschoben)
30.04.2024 56 2 bas (zu Version 57.1 verschoben)
06.03.2024 56 1 jma Zonen werden nur für Ergebnisse außerhalb Hamburg AB und bei
maximal 2 Zonen ausgegeben
20.11.2023 55 5 bw Neue returnCodes START_NOT_FOUND, DEST_NOT_FOUND,
VIA_NOT_FOUND, FORCED_START_NOT_FOUND,
FORCED_DEST_NOT_FOUND
29.08.2023 55 4 jsc IntermediateStops zu ScheduleElementLight in getTariff hinzugefügt
04.08.2023 55 3 kd Code-Beispiele für Java und PHP durch Link zum Beispiel-Repository
ersetzt
24.07.2023 55 2 bw travelTimetable entfernt
06.04.2023 55 1 kd,
bas
```
```
neues FeldannouncementszuScheduleElementhinzugefügt. Ab Version
55 werden Announcements in diesem neuen Feld ausgeliefert, und nicht
mehr überattributes
31.03.2023 54 1 kd,
jma
```
```
neue Felderblacklistundgroupsin den
TariffInfoSelector-Objekten hinzugefügt. Neues Feld
tariffInfoSelectorzuTariffRequesthinzugefügt
05.08.2022 53 1 kd neues Feldlayerin denSDName-Objekten hinzugefügt
05.08.2022 52 1 jma neues Felddlidin denService-Objekten ingetAnnouncements
28.07.2022 51 1 jek neues FeldwithPathsingetRoute
07.03.2022 50 1 jp neues FeldregionTextsinTariffResponse
07.03.2022 49 2 mag neue URL für Soll Fahrplan
07.03.2022 49 1 jma IDs für Start/Ziel-Haltestellen bei Tickets ergänzt
07.03.2022 48 1 jfo SH-Tarif Überwege ergänzt
08.11.2021 47 1 mag Aussagekräftigere Fehlercodes
06.09.2021 46 2 hvo Korrektur GTI URL
25.08.2021 46 1 mag Neues Feld für für den öffentlichen Rundfunk relevante Meldungen in
getAnnouncement
18.08.2021 45 1 mag line ingetRoutehat neue Felder für Betreibernamen
22.07.2021 44 1 mag,
bw,
sth
```
```
Tarifzonen und Orts-Ids für den SH-Tarif incheckName-Response
ergänzt, geplante und tatsächliche Abfahrts- und Ankunftszeiten in den
Schedules dergetRoute-Responsehinzugefügt.
16.06.2021 43 1 mag Attributes ingetRoutehaben neues Feld id
26.04.2021 42 1 sth CheckName-Request unterstützt jetzt Deutschlandweite Haltestellen-IDs
(DHID)
12.04.2021 41 1 hvo Tags von Fußwegen werden inIndividualRoutezurückgeliefert.
12.04.2021 40 1 hvo Zeiten vonIntermediateStopswerden immer im Format HH:mm
zurückgeliefert.
10.03.2021 39 1 jma direction-Feld bei Departures in der DLResponse hinzugefügt.
02.03.2020 38 1 bw,jma XpressBus hinzugefügt.
17.01.2020 37 5 bw singleTicketTariffOptimizer ergänzt, Fehler korrigiert.
08.01.2020 37 4 bw TariffOptimizer entfernt.
22.10.2019 37 3 fj Abschnitte zur Zugriffsbeschränkung und Inaktivität hinzugefügt.
21.08.2019 37 2 ie Maximale Distanz für Reverse Geocoding ergänzt.
08.08.2019 37 1 chb Neue MethodeticketListhinzugefügt.
```
HBT GmbH; Version 63.1

24. November 2025 Seite 105 von 107


```
01.07.2019 36 2 bw Codebeispiele Python und Typescript ergänzt. CNRequest max Werte
ergänzt.
23.01.2019 36 1 bw FeldshopInfozumScheduleElementhinzugefügt.
23.01.2019 35 1 ie, bw Neuen RequestTariffZoneNeighboursRequesthinzugefügt.
18.12.2018 34 1 fp Neuer Wert für Gleisgleiche Umstiege in EnumSimpleServiceType
hinzugefügt.
22.10.2018 33 1 lj Neues Feldversionin Announcement (Tabelle 46) hinzugefügt.
01.06.2018 32 1 ie Neue FeldernotRecommendedundshopLinkin TicketInfo (Tabelle 24)
hinzugefügt.
04.05.2018 31 5 chb Icons wurden aktualisiert. Tabelle 83 beinhaltet nun ServiceTypes als
Alternative (a,s,r,u,Fussweg,ship)
23.01.2018 31 4 chb Zusätzliche Erklärung zurcontSearchmitcontSearchByServiceIdin
Abhängigkeit dertimeIsDeparturehinzugefügt.
12.10.2017 31 3 chb GRResponse lieft nun auch die Linien-Richtung als DirectionId.
12.10.2017 31 2 chb Beispiele aktualisiert. Java Signaturerstellung verbessert. Allgemeine
Verbesserung der Übersichtlichkeit.
07.08.2017 31 1 ie Koordinaten in getIndividualRoute korrigiert. KM-Methoden entfernt.
07.04.2017 30 7 lj Neues Feld in DLRequest für mehrere Haltestellen hinzugefügt.
26.10.2016 30 6 kd Neue Attributstypen für Echtzeitprognosen hinzugefügt.
06.09.2016 30 5 kd Fehler in der Beschreibung der neuen Suchoptionen behoben.
29.08.2016 30 4 kd Fehler im EnumVehicleTypebehoben.
23.08.2016 30 3 ie getVehicleMapundgetTrackCoordinatesveröffentlicht.
13.07.2016 30 2 kd icon_serviceum ParametervarSizeergänzt.
06.07.2016 30 1 kd AnnouncementundAnnouncementRequestum zusätzliche
Filtermöglichkeiten erweitert
08.06.2016 29 1 kd GRRequestundGRResponseerweitert für besseres Cont-Search Verhalten
unter Echtzeit.
31.03.2016 28 1 kd MethodegetStationInformationmitStationInformationRequestund
StationInformationResponseimplementiert.
14.01.2016 27 1 kd „Neue Suchoptionen” fürwww.geofox.deimplementiert.
07.12.2015 26 2 kd,bw „X-Platform”-HTTP-Header hinzugefügt. WADL-Adresse korrigiert.
25.11.2015 26 1 kd MethodecheckPostalCodemitPCRequestundPCResponsehinzugefügt.
21.09.2015 25 1 sku,kd Hinweis auf Individualprofile und attributierte Pfade in Abschnitt 2.10
hinzugefügt.
21.08.2015 24 1 kd,ie Attributmodelzu den TypenServiceTypeundCourseElement
hinzugefügt.IntermediateStopsinGRRequest/GRResponsehinzugefügt.
07.07.2015 23 1 bw Attribute zum DepartureCourse (DCResponse) und zum Departure
(DLResponse) hinzugefügt
03.03.2015 22 6 bw Dokumentation zu Echtzeit in öffentliche Doku übernommen,
PHP-Beispiel ergänzt, Layout verbessert
03.03.2015 22 5 bw HVVGTI und GTI zu einer Anwendung mit unterschiedlichen URLs
zusammen geführt.
09.12.2014 22 4 bw Dokumentation zum Verkehrsmittelfilter in departureList hinzugefügt.
12.11.2014 22 3 kd Methode getVehicleMap aufgeteilt in getVehicleMap und
getTrackCoordinates.
19.08.2014 22 2 bw Veralteten Fehlercode START_DEST_TOO_CLOSE entfernt.
19.08.2014 22 1 bw Verkehrsmittelfilter zur Abfahrtstafel hinzugefügt, Methode
getAnnouncements erweitert.
14.08.2014 21 3 kd Dokumentation füricon_serviceum Line Icons erweitert.
11.08.2014 21 2 bw Flag returnPartialTickets hinzugefügt.
06.06.2014 21 1 bw Echtzeit Gleisangaben eingefügt.
10.01.2014 20 1 kd,bw Abschnitt 2.4.3 zur Filterung des DLRequests hinzugefügt.
10.01.2014 19 1 ie MethodegetIndividualRoutein HVVGTI hinzugefügt. Optionmit
Fahrrad auch am Zielhinzugefügt. ReturnCode
START_DEST_TOO_CLOSEhinzugefügt.
18.12.2013 19 X bw Echtzeit Erweiterung (getRoute, departureList, departureCourse)
05.12.2013 18 4 kd Neuformatierung in LaTeX
20.11.2013 18 3 tw getRoute-Beschreibung berichtigt, Icon Service berichtigt
04.11.2013 18 2 jp getVehicleMaphinzugefügt
27.08.2013 18 1 pk ticketRemarkshinzugefügt,Ticketdeprecated gesetzt
20.08.2013 17 2 pk Icon Service hinzugefügt
15.08.2013 17 1 bw ListStationsÄquivalenzfilter,VehicleTypeFernbahn,
SimpleServiceTypeBicycle
29.07.2013 16 3 bw Beschreibung zupenalties DesiredTypeundDesiredCarrier
verbessert
24.05.2013 16 2 pk Neuverfassung der Dokumentation in zwei Subversionen (hvvgti und gti)
```
HBT GmbH; Version 63.1

24. November 2025 Seite 106 von 107


```
23.01.2012 16 1 bw ermäßigte Preise für elektronische Fahrkarten &vehicleTypesim
CNRequest
08.01.2012 15 2 bw ReturnCodes ERROR_XXentfernt
05.12.2012 15 1 bw Neues Fehlerkonzept für KM, Properties imKMRouteRequest,TraceID
15.11.2012 14 3 bw MobilityProviderUNSPECIFIED eingefügt
24.10.2012 14 2 bw Komplementäre Mobilität undIndividualRoutehinzugefügt
31.08.2012 14 1 bw regionTypeinTicketInfo,TariffRegionType„GH_ZONE” eingefügt.
23.08.2012 13 3 fw DCRequest/DCResponsehinzugefügt
21.08.2012 13 2 bw Feld-Typ f.tariffInfoSelectorkorrigiert
19.07.2012 13 1 bw Tarifinformationen aus Tarif Response in Get Route Response
integrieren.
14.06.2012 12 1 bw ScheduleElements als Umstiegsfußwege zwischen den normalen
ScheduleElements eingefügt.
13.06.2012 11 1 bw Gleisinformationen inplatformumbenannt (vorhertrack)
31.05.2012 10 1 bw Track (Gleis) zuDeparturehinzugefügt.track(Gleis) ausSDNamenach
JourneySDNameverschoben.
16.03.2012 9 1 ie track(Gleis) zuSDNamehinzugefügt.
14.03.2012 8 2 cg Einleitung neu formuliert und auf IP-Authentifizierung hingewiesen.
23.01.2012 8 1 ie schedulesBeforeundschedulesAfteringetRoutehinzugefügt.
01.09.2011 7 1 bw AnnouncementRequestimplementiert, Fahrt-ID, Linien-IDs und
Haltestelle in Abfahrtstafel.
05.08.2011 6 1 bw Einfeldsuche und typenlose Suche
01.08.2011 5 1 bw Auswechslung des JSON Parsers und damit nicht Abwärtskompatible
Änderung des JSON-Formats. Einfügen einiger Beispiele.
07.07.2011 4 1 bw Linien IDs für dieTariffRequestseingefügt
19.05.2011 3 1 rei TypezumAttributehinzugefügt
04.05.2011 2 1 bw ScheduleElementum einenPatherweitert, sodass Fußwege übertragen
werden können.
24.06.2010 1 1 kha Initialversion
```
HBT GmbH; Version 63.1

24. November 2025 Seite 107 von 107


