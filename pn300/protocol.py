"""Fernsteuerbefehle des PN 300, Abschnitt 7.4 der Gebrauchsanweisung.

RS-232: Befehle mit Semikolon trennen, Zeile mit LF abschließen.
Antworten kommen mit CR+LF. Fernbetrieb ist das Steuerzeichen HT.
"""

from __future__ import annotations

REN = "\t"
LLO = "\x19"
GTL = "\x01"
DCL = "\x14"
LINE_LIMIT = 64


def join_commands(*commands: str) -> str:
    line = ";".join(command for command in commands if command)
    if len(line) > LINE_LIMIT:
        raise ValueError(f"Befehlszeile länger als {LINE_LIMIT} Zeichen")
    return line


def select_channel(channel: str) -> str:
    return "SEL_A" if channel == "A" else "SEL_B"


def operating_mode(mode: str) -> str:
    return {"IND": "OPER_IND", "TRACK": "OPER_TRAC", "PAR": "OPER_PAR"}[mode]


def voltage_set(value: float) -> str:
    return f"VSET {value:.2f}"


def current_set(value: float) -> str:
    return f"ISET {value:.3f}"


def output_on() -> str:
    return "OUT_ON"


def output_off() -> str:
    return "OUT_OFF"


def output_query() -> str:
    return "OUT?"


def parse_output(answer: str) -> bool | None:
    text = answer.strip().upper()
    if "OUT_ON" in text:
        return True
    if "OUT_OFF" in text:
        return False
    return None


def save_preset(slot: int) -> str:
    if not 0 <= slot <= 5:
        raise ValueError("Speicherplatz 0 bis 5")
    return f"*SAV {slot}"


def recall_preset(slot: int) -> str:
    if not 0 <= slot <= 5:
        raise ValueError("Speicherplatz 0 bis 5")
    return f"*RCL {slot}"
