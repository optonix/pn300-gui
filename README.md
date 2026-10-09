# pn300-gui

Programm zum Bedienen eines Digimess / Grundig PN 300 vom Windows-Rechner aus. Die Oberfläche sieht aus wie das Frontpanel des Geräts. Spannung, Strom, Betriebsart und die Ausgänge gehen über die serielle Schnittstelle an das Netzteil. Ohne angeschlossenes Gerät läuft dasselbe Fenster gegen einen Simulator.

Die Tasten kennen die serielle Leitung nicht. Sie rufen nur `pn300/device.py` auf. Dahinter sitzt entweder der Simulator oder ein COM-Port.

## Starten

Python 3.10 oder neuer, im Projektordner:

```bash
pip install -r requirements.txt
python main.py
```

Flet 1.0 hat `ft.app` entfernt. Das Projekt bleibt deshalb bei `flet==0.28.3`.

Die Tests prüfen Displayformat, Befehlstexte und die Fehlercodes:

```bash
python -m unittest tests/test_protocol.py
```

## Bedienung

Oben im Fenster ist das Panel. Unten die Zeile für die Leitung.

Ohne Gerät bleibt die Schnittstelle auf Simulator. Die Werte ändern sich nur lokal, die Befehle werden aber so gebaut wie in der Gebrauchsanweisung, Abschnitt 7.4.

Am Gerät einen COM-Port wählen. Baudrate 1200, 2400, 4800 oder 9600, 8 Datenbit, keine Parität, ein Stoppbit. Handshake keines oder RTS/CTS, passend zu dem, was am PN 300 unter SYST steht. Suchen liest die Ports neu ein. Die Leitung muss laut Anleitung schon vor dem Einschalten des Geräts stecken.

Beim Öffnen eines Ports geht Device Clear raus, danach das Steuerzeichen für Fernbedienung (HT) und `*CLS`. LOCAL schickt Go To Local (SOH). Sperre schickt Local Lockout (EM), dann reagiert die LOCAL-Taste am Gerät nicht mehr.

ENTER übernimmt Spannung oder Strom für den gewählten Kanal, als eine Zeile `SEL_A;VSET 12.50` beziehungsweise `ISET`. Die Zeile endet mit LF. Antworten kommen mit CR und LF.

OUT A/B schickt `OUT_ON` oder `OUT_OFF` und fragt `OUT?` ab. Bei eingeschaltetem Ausgang zeigt das Display die Messwerte aus `VOUT?` und `IOUT?`, sonst die Sollwerte. Die CV- und CC-LEDs folgen `CONT?`.

CV/CC und Schutz sitzen in der unteren Zeile, weil das Frontpanel dafür keine eigene Taste hat. Schutz wechselt zwischen LIMITING und CUT-OUT. Reset schickt `*RST`. SYST fragt `*IDN?` ab und zeigt die Kennung im Display.

MEM öffnet den Speicher. Pfeil hoch und runter wählen Platz 0 bis 5, ein zweites MEM wechselt von Speichern auf Laden. ENTER schickt `*SAV` oder `*RCL`. Das Gerät hat sechs Plätze, nicht acht.

Nach jedem Befehl kommt `ERR?`. Der Text steht unten, zum Beispiel Stromgrenze, Spannungsgrenze, Local oder ein unbekannter Befehl. Bei der Schutzart LIMITING meldet das Gerät die Grenzen 21 und 22 nicht als Text, sondern über die LEDs.

Quelle C ist fest 5 V / 2 A und hat keine Fernsteuerbefehle.

## Aufbau

```
main.py              Fenster starten
pn300_gui/panel.py   Frontpanel und untere Zeile
pn300_gui/display.py die zwei Zeilen, je 16 Zeichen
pn300_gui/ports.py   COM-Ports
pn300/model.py       Kanäle, Betriebsart, Speicher
pn300/protocol.py    Befehlstexte aus der Anleitung
pn300/errors.py      Codes aus Abschnitt 7.3.3
pn300/transport.py   serielle Leitung
pn300/simulator.py   dieselben Aufrufe ohne Gerät
pn300/device.py      Fassade für die Oberfläche
```

## Windows-Programm

Auf dem Rechner, an dem das PN 300 hängt:

```bash
pip install -r requirements.txt pyinstaller
flet pack main.py -n PN300 --product-name "Digimess PN 300"
```

Die Datei liegt danach unter `dist/`. Gegen das echte Gerät ist der Stand noch nicht gelaufen.

Ein Tag `v0.1.0` startet den Workflow unter `.github/workflows/windows-release.yml`. Der baut auf einem Windows-Runner dasselbe Paket und hängt `PN300-windows.zip` an das Release.
