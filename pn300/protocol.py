"""Fernsteuerbefehle des PN 300. Nur die Zeichenketten, kein Versand."""

from __future__ import annotations


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


def local() -> str:
    return "LOCAL"
