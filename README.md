# pn300-gui

Bedienoberfläche für das Digimess / Grundig PN 300. Das Fenster folgt dem Frontpanel. Die Oberfläche spricht nur mit der Gerätefassade.

## Funktionsumfang

Die Fassade spricht den Simulator oder eine RS-232-Leitung mit 1200 bis 9600 Baud, 8N1, wahlweise RTS/CTS. Befehlszeilen enden mit LF.

Umgesetzt sind Betriebsart, Kanalwahl, Spannung, Strom, CV/CC, Schutzart LIMITING oder CUT-OUT, Ausgang, Messung über `VOUT?` und `IOUT?`, Fehlerabfrage `ERR?`, Speicher 0 bis 5, Reset, Identifikation, Fernbedienung und die Sperre der LOCAL-Taste.

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
