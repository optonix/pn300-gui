"""Fehlercodes aus Abschnitt 7.3.3 der Gebrauchsanweisung."""

from __future__ import annotations

ERRORS = {
    0: "",
    21: "Stromgrenze überschritten",
    22: "Spannungsgrenze überschritten",
    91: "Gerät überhitzt",
    96: "Speicher nicht lesbar",
    111: "Abfrage ohne Programmierung",
    114: "Programmiert, aber nicht gelesen",
    117: "Schnittstelle blockiert",
    120: "Falsche Abfrage",
    132: "Im Local nicht ausführbar",
    134: "Wert außerhalb des Bereichs",
    151: "Unbekannter Befehl",
    181: "Eingabepuffer voll",
}


def parse_error(answer: str) -> tuple[int, str]:
    text = answer.strip()
    if not text or text.upper() in {"OK", "0", "Ø"}:
        return 0, ""
    digits = "".join(ch for ch in text if ch.isdigit())
    code = int(digits) if digits else 0
    return code, ERRORS.get(code, text)
