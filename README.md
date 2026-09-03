# pn300-gui

Steuersoftware / Simulator fuer das Digimess / Grundig PN 300.

## Start

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
python main.py --web
```

Die App oeffnet sich im Browser (Port 8501).

## Bedienung

- Simulator ist Standard.
- Schalter **Real Device (RS-232)** aktiviert das echte Geraet.
- COM-Port im Feld anpassen (`COM3` unter Windows, `/dev/ttyUSB0` unter Linux).
- **V** / **I** oeffnen den Zahlen-Dialog und rufen `set_voltage` / `set_current` auf.
- **OUT A/B**, **MODE** und **MEM** senden ebenfalls an das Geraet, wenn Real Device aktiv ist.
