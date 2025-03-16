(deutsche Übersetzung unten)

# E3DC Control
Control the charging of an E3DC system (wallbox and battery) via RSCP (using the Python package "pye3dc")
Targeted goals:
- to charge the car battery
  - with excess solar power (adapted to the power drawn by the car, which often does not correspond to the permitted charging current)
  - during the period of low tariffs
- to avoid the derating of grid feed-in power (70% of the peak rated power) through delayed charging of the E3DC battery

## Configuration
* Move and rename the folder `control/_config/e3dc_config.sample/` to `../e3dc_config/`
  so that `e3dc_config` is on the same level as the checked out repo
* Enter the IP address, the user password and the RSCP secret of your E3DC in `e3dc_config/e3dc_config.py`
* Adjust the settings in `control/_config/config.py`

## Get info from E3DC
* Run `python -u control/main.py --verbose --num-loops=1 --info`

## Control E3DC
* Run `python -u 'control/main.py' --dry-run`
  (The "--dry-run" parameter ensures that no E3DC settings are changed during test runs.)
* Control the charging strategy at runtime by editing `e3dc_config/e3dc_directives.yaml`

Sample output / explanation:

| 2025-03-16 11:03:48 | 81%                     | 2952>b               | 16>g              | 10068<s-10                         | 685>h            | 6415>w  | 9383           | +2968         | 14A              | >10.0  91.751 -1.03 kWh   | 4500<b<4500          | =                    | 10.1       | 4042bf      | 10068 709 6415        |
| ------------------- | ----------------------- | -------------------- | ----------------- | ---------------------------------- | ---------------- | ------- | -------------- | ------------- | ---------------- | ------------------------- | -------------------- | -------------------- | ---------- | ----------- | --------------------- |
| timestamp UTC       | battery state of charge | power in/out battery | power in/out grid | power solar,                       | home consumption | wallbox | wallbox budget | unused budget | charging current | wallbox charged           | battery power limits | control intervention | max. solar | E3DC states | average values        |
|                     |                         |                      |                   | difference of the 2 solar circuits |                  |         |                |               |                  | current, month solar/grid |                      |                      | today      |             | solar, house, wallbox |

## Kudos
Many thanks go to
* [fsantini](https://github.com/fsantini) for  [fsantini/python-e3dc](https://github.com/fsantini/python-e3dc) / https://pypi.org/project/pye3dc
* [mdhom](https://github.com/mdhom) for https://github.com/fsantini/python-e3dc/pull/59

who enabled the development of this control script.


# E3DC-Steuerung
Steuerung des Ladevorgangs eines E3DC-Systems (Wallbox und Batterie) über RSCP (mittels Python-Paket "pye3dc")
Ziele:
- Laden der Auto-Batterie
  - mit Solarüberschuss (angepasst an vom Auto abgenommene Leistung, die oft nicht dem erlaubtem Ladestrom entspricht)
  - während der Niedrigtarifzeit
- Vermeidung der Einspeiseleistungsreduzierung (70% der Peak-Nennleistung) durch verzögertes Laden der E3DC-Batterie

## Konfiguration
* Ordner `control/_config/e3dc_config.sample/` umbenennen und verschieben nach `../e3dc_config/`,
  so dass `e3dc_config` auf der gleichen Ebene wie das ausgecheckte Repo liegt
* die IP-Adresse, das Benutzerpasswort und das RSCP-Geheimnis Ihrer E3DC in `e3dc_config/e3dc_config.py` eintragen
* Einstellungen in `control/_config/config.py` anpassen

## Informationen vom E3DC erhalten
* Ausführen von `python -u control/main.py --verbose --num-loops=1 --info`

## E3DC kontrollieren
* Ausführen von `python -u control/main.py --dry-run`
  (Der Parameter "--dry-run" sorgt dafür, dass für Testläufe vorerst keine Einstellungen der E3DC geändert werden.)
* Steuerung der Ladestrategie zur Laufzeit durch Editieren von `e3dc_config/e3dc_directives.yaml`

Beispielausgabe / Erklärung:

| 2025-03-16 11:03:48 | 81%               | 2952>b                   | 16>g                 | 10068<s-10                  | 685>h         | 6415>w  | 9383           | +2968              | 14A       | >10.0  91.751 -1.03 kWh   | 4500<b<4500             | =                  | 10.1       | 4042bf        | 10068 709 6415       |
| ------------------- | ----------------- | ------------------------ | -------------------- | --------------------------- | ------------- | ------- | -------------- | ------------------ | --------- | ------------------------- | ----------------------- | ------------------ | ---------- | ------------- | -------------------- |
| Zeitstempel UTC     | Batterieladestand | Leistung in/aus Batterie | Leistung in/aus Netz | Leistung solar,             | Hausverbrauch | Wallbox | Wallbox-Budget | ungenutztes Budget | Ladestrom | Wallbox geladen           | Batterieleistungslimits | Steuerungseingriff | max. solar | E3DC-Zustände | Mittelwerte          |
|                     |                   |                          |                      | Differenz der 2 Solarkreise |               |         |                |                    |           | aktuell, Monat solar/Netz |                         |                    | heute      |               | solar, Haus, Wallbox |

## Kudos
Großer Dank geht an
* [fsantini](https://github.com/fsantini) für [fsantini/python-e3dc](https://github.com/fsantini/python-e3dc) / https://pypi.org/project/pye3dc und
* [mdhom](https://github.com/mdhom) für https://github.com/fsantini/python-e3dc/pull/59,

die die Entwicklung dieses Steuerungsskripts ermöglicht haben.
