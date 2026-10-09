# pn300-gui

Bedienoberfläche für das Digimess / Grundig PN 300. Das Fenster folgt dem Frontpanel: Netzschalter, CV- und CC-LEDs, zweizeiliges LC-Display, IND / TRACK / PAR, Buchsen A, B und C sowie die Tastenfelder SET, SELECT und ADJUST.

Stand jetzt spricht die Oberfläche nur den eingebauten Simulator an. RS-232 kommt im nächsten Schritt.

## Starten

```bash
pip install -r requirements.txt
python main.py
```

Flet 1.0 hat `ft.app` entfernt. Deshalb bleibt das Projekt auf `flet==0.28.3`.

## Windows-Programm

Auf einem Windows-Rechner, im Projektordner:

```bash
pip install flet==0.28.3
flet pack main.py -n PN300 --product-name "Digimess PN 300"
```

Die ausführbare Datei liegt danach unter `dist/`.
