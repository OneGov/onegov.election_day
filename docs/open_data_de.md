# Wahlen & Abstimmungen: Open Data

## Einleitung

Für jede wichtige Seite gibt es eine enstprechende JSON-Alternative.

All Respoonses enthalten den `Last-Modified` HTTP Header, welcher Auskunft über den Zeitpunkt der letzten Änderung gibt (z.B., wann zum letzten Mal Ergebnisse einer Wahl oder Abstimmung hochgeladen wurden).

## Inhalt

1. [Ergebnissübersicht](#ergebnissübersicht)
2. [Wahlresultate](#wahlresultate)
3. [Abstimmungsresultate](#abstimmungsresultate)

## Ergebnissübersicht

```
URL (latest): /json
URL (archive by year): /archive/{year}/json
URL (archive by date): /archive/{year}-{month}-{day}/json
URL (election): /election/{id}/summary
URL (vote): /vote/{id}/summary
```

Die auf der Startseite und den Archivseiten dargestellten Ergebnisse sind im JSON Format verfügbar. Die Daten enthalten neben einigen globalen Informationen für jede Wahl / Abstimmung die folgenden Informationen:

Name|Beschreibung
---|---
type|`election` für Wahlen, `vote` für Abstimmungen.
title|Ein Objekt mit den übersetzten Titeln.
date|Das Datum (ISO 8601).
domain|Einflussbereich (Bund, Kanton, ...).
url|Ein Link zur Detailansicht.
progess|Ein Objekt welches die Anzahl ausgezählter Gemeinden (`counted`) die Gesamtzahl an Gemeinden (`total`) enthält.

Wahlresultate enthalten die folgenden zusätzlichen Informationen:

Name|Beschreibung
---|---
answer|Das Abstimmungsresultat: Angenommen (`accepted`), abgelehnt (`rejected`), Initiative (`proposal`) oder Gegenvorschlag (`counter-proposal`).
yeas_percentage|Ja-Stimmen in Prozent.
nays_percentage|Nein-Stimmen in Prozent.

## Wahlresultate

### Aufbereitete Ergebnisse

```
URL: /election/{id}/json
```

Es werden dieselben Daten wie in der normalen Ansicht in einer strukturierten Form zurückgegeben.

### Rohdaten

```
URL: /election/{id}/{data-format}
```

Die Rohdaten die zur Anzeige der Resultate verwendet werden, sind in den folgenden Formaten verfügbar:

Format|URL
---|---
JSON|`/data-json`
CSV|`/data-csv`
XLSX|`/data-xlsx`

Die folgenden Felder sind in allen Formaten enthalten:

Name|Beschreibung
---|---
election_title|Titel der Wahl
election_date|Das Datum der Wahl (ein ISO 8601 String)
election_type|"proporz" falls Proporzwahl, "majorz" falls Majorzwahl
election_mandates|Die Anzahl der Sitze.
election_absolute_majority|Das absolute Mehr. Nur bei Majorzwahlen.
election_counted_municipalities|Die Anzahl ausgezählter Gemeinden.
election_total_municipalities|Die Gesamtanzahl an Gemeinden.
municipality_name|Der Name der Gemeinde/des Standorts
municipality_bfs_number|Die ID der Gemeinde/des Standorts. Besser bekannt als "BFS Nummer".
municipality_elegible_voters|Die Anzahl Stimmberechtigter der Gemeinde/des Standorts.
municipality_received_ballots|Die Anzahl abgegebener Stimmzettel der Gemeinde/des Standorts.
municipality_blank_ballots|Die Anzahl leerer Stimmzettel der Gemeinde/des Standorts.
municipality_invalid_ballots|Die Anzahl ungültiger Stimmzettel der Gemeinde/des Standorts.
municipality_unaccounted_ballots|Die Anzahl der ungültigen oder leeren Stimmzettel der Gemeinde/des Standorts.
municipality_accounted_ballots|Die Anzahl gültiger Stimmzettel der Gemeinde/des Standorts.
municipality_blank_votes|Die Anzahl leerer Stimmen der Gemeinde/des Standorts.
municipality_invalid_votes|Die Anzahl ungültiger Stimmen der Gemeinde/des Standorts. Null falls Proporzwahl.
municipality_accounted_votes|Die Anzahl gültiger Stimmen der Gemeinde/des Standorts.
list_name|Der Name der Liste des Kandidierenden. Nur bei Proporzwahlen.
list_id|Die ID der Liste, für welche der Kandidierende kandidiert. Nur bei Proporzwahlen.
list_number_of_mandates|Die Anzahl Sitze der Liste. Nur bei Proporzwahlen.
list_votes|Die Anzahl der Listenstimmen. Nur bei Proporzwahlen.
list_connection|Die ID der Listenverbindung. Nur bei Proporzwahlen.
list_connection_parent|Die ID der übergeorndeten Listenverbidnung. Nur bei Proporzwahlen und falls es sich um eine Unterlistenverbindung handelt.
candidate_family_name|Der Nachnahme des Kandidierenden.
candidate_first_name|Der Vorname des Kandidaten.
candidate_id|Die ID des Kandidierenden.
candidate_elected|True, falls der Kandidierenden gewählt wurde.
candidate_votes|Die Anzahl Kandidierendenstimmen der Gemeinde/des Standorts.

## Abstimmungsresultate

### Aufbereitete Ergebnisse

```
URL: /vote/{id}/json
```

Es werden dieselben Daten wie in der normalen Ansicht in einer strukturierten Form zurückgegeben.

### Rohdaten

```
URL: /vote/{id}/{data-format}
```

Die Rohdaten die zur Anzeige der Resultate verwendet werden, sind in den folgenden Formaten verfügbar:

Format|URL
---|---
JSON|`/data-json`
CSV|`/data-csv`
XLSX|`/data-xlsx`

Die folgenden Felder sind in allen Formaten enthalten:

Name|Beschreibung
---|---
title|Titel der Abstimmung.
date|Das Datum der Abstimmung (ein ISO 8601 String).
shortcode|Internes Kürzel (definiert die Reihenfolge von mehreren Abstimmungen an einem Tag).
domain|"federation" für Nationale Abstimmungen, "canton" für Kantonale Abstimmungen
type|"proposal" (Vorschlag), "counter-proposal" (Gegenvorschlag) or "tie-breaker" (Stichfrage).
group|Woher das Resultat kommt. Das kann der Bezirk und die Gemeinde, getrennt mittels eines Schrägstrichs, der Name der Stadt und der Name des Kreises, ebenfalls getrennt mittels eines Schrägstrichts, oder ein einfacher Gemeinde Name sein. All dies hängt vom jeweiligen Kanton ab.
municipality_id|Die ID der Gemeinde/des Standorts. Besser bekannt als "BFS Nummer".
counted|Wahr wenn das Resultat ausgezählt wurde. Falsch wenn das Resultat noch nicht bekannt ist (die Werte sind noch nicht korrekt).
yeas|Die Anzahl Ja Stimmen
nays|Die Anzahl Nein Stimmen
invalid|Die Anzahl ungültiger Stimmen
empty|Die Anzahl leerer Stimmen
elegible_voters|Die Anzahl Stimmberechtigter