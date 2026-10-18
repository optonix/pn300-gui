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

Die Tests prüfen Displayformat, Befehlstexte, den Simulator und die Tastenfolgen:

```bash
python -m unittest discover -s tests
```

## Bedienung

Oben im Fenster ist das Panel. Unten die Zeile für die Leitung: Port, Baudrate, Handshake und der Verbindungsstatus.

Ohne Gerät bleibt die Schnittstelle auf Simulator. Dieselben Befehle wie in der Gebrauchsanweisung, Abschnitt 7.4, laufen dann gegen den Simulator.

Am Gerät einen COM-Port wählen. Baudrate 1200, 2400, 4800 oder 9600, 8 Datenbit, keine Parität, ein Stoppbit. Handshake keines oder RTS/CTS. Dieselben Werte stehen im Menü SYST. Die Leitung muss laut Anleitung schon vor dem Einschalten des Geräts stecken.

Beim Öffnen eines echten Ports geht Device Clear raus, danach das Steuerzeichen für Fernbedienung (HT) und `*CLS`. Die Ausgänge gehen dabei aus. LOCAL schickt Go To Local (SOH). Ist Local Lockout gesetzt, bleibt LOCAL ohne Wirkung. Der Simulator führt Einstellbefehle im Local nicht aus. Erlaubt bleiben dort nur die Statusabfragen aus Abschnitt 7.2.

Nach dem Einschalten am Simulator läuft der Selbsttest über CPU, ROM, RAM, KEY, BATTERY und DISPLAY. Danach stehen die bisherigen Sollwerte wieder da, die Ausgänge sind aus. Der Anfangszustand entspricht `*RST`: 0,00 V, 2,300 A, INDEPEND, CV, LIMITING.

Jede Taste wiederholt, solange sie gehalten wird. Pfeil hoch und runter blättern in den Menüs. Bei der Zahleneingabe schieben links und rechts die Stelle, hoch und runter ändern die Ziffer. Die Voreinstellung ist die letzte Stelle.

MODE öffnet OPERATION, CONTROL, ADJUSTMENT und PROTECTION. ENTER übernimmt den Eintrag, ESC verwirft ihn. OPERATION schickt `OPER_IND`, `OPER_TRAC` oder `OPER_PAR`. In PARALLEL liegt der Strom zwischen 0,300 A und 4,600 A. CONTROL schickt `CONT_CV` oder `CONT_CC` für den gewählten Kanal. PROTECTION schickt `PROT_LIM` oder `PROT_CUT`. ADJUSTMENT gilt nur an der Oberfläche: DIRECT oder INDIRECT.

V und I öffnen bei INDIRECT die Anzeige `VOLTAGE_` oder `CURRENT_` mit SET oder LIM. ENTER schickt `SEL_A;VSET 12.50` beziehungsweise `ISET`. Die Zeile endet mit LF, Antworten kommen mit CR und LF. ESC verwirft den Entwurf. Bei DIRECT und eingeschaltetem Ausgang ändert die gewählte Stelle den Wert sofort. ESC zeigt dann die Messwerte.

OUT A/B schickt `OUT_ON` oder `OUT_OFF` und fragt `OUT?` ab. Bei eingeschaltetem Ausgang und INDIRECT zeigt das Display die Messwerte aus `VOUT?` und `IOUT?`. Solange Netz an ist, leuchtet bei CV-Regelung die CV-LED grün und die CC-LED rot, bei CC-Regelung umgekehrt. REMOTE leuchtet rot. IND, TRACK und PAR leuchten grün für die aktive Betriebsart. OUT leuchtet grün, solange die Ausgänge an sind.

LIMITING wechselt bei Überlast zwischen CV und CC und meldet die Grenzen 21 und 22 nicht. CUT-OUT schaltet die Ausgänge aus und zeigt im Display „Exceeded I limit“ oder „Exceeded V limit“.

MEM bietet STORE und LOAD. Danach den Platz 0 bis 5 und die Rückfrage „Are you sure ?“. ENTER schickt `*SAV` oder `*RCL`.

SYST stellt die Schnittstelle ein. Unter RS 232C gelten Baudrate und Handshake für den geöffneten Port. Unter GPIB wird die Adresse 0 bis 30 gespeichert. Ein GPIB-Bus ist nicht angebunden.

Der Netzschalter am Simulator macht den Selbsttest, schaltet die Ausgänge aus, behält die Sollwerte und löscht Local Lockout. Auf einer echten Leitung schickt diese Taste kein `OUT_OFF`. Einschalten liest das Gerät dann neu ein.

Nach jedem Befehl kommt `ERR?`. Der deutsche Text steht unten in der Statuszeile. Gemeldet werden höchstens die ersten zwei Codes. Quelle C ist fest 5 V / 2 A und hat keine Fernsteuerbefehle.

## Aufbau

```
main.py              Fenster starten
pn300_gui/panel.py   Frontpanel und untere Zeile
pn300_gui/display.py die zwei Zeilen, je 16 Zeichen
pn300_gui/ports.py   COM-Ports
pn300/model.py       Kanäle, Betriebsart, Speicher
pn300/face.py        Tasten und Anzeigen nach Kapitel 5 und 6
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
