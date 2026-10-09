# pn300-gui

Bedienoberfläche für das Digimess / Grundig PN 300. Das Fenster folgt dem Frontpanel. Die Oberfläche kennt die serielle Leitung nicht, sie spricht nur mit der Gerätefassade.

## Aufbau

- `main.py` startet das Fenster.
- `pn300_gui/` ist die Oberfläche: Panel, Display, COM-Liste.
- `pn300/` ist das Gerät: Zustand, Befehle, Simulator, serielle Leitung, Fassade.
- `tests/` prüft Displayformat und Befehlstexte.

Simulator ist die Voreinstellung. Ein COM-Port in der Zeile Schnittstelle öffnet die Leitung mit 9600 8N1.

## Starten

```bash
pip install -r requirements.txt
python main.py
python -m unittest tests/test_protocol.py
```

Flet 1.0 hat `ft.app` entfernt. Deshalb bleibt das Projekt auf `flet==0.28.3`.

## Windows-Programm

Auf einem Windows-Rechner, im Projektordner:

```bash
pip install -r requirements.txt
flet pack main.py -n PN300 --product-name "Digimess PN 300"
```

Die ausführbare Datei liegt danach unter `dist/`.
