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


def output(enabled: bool) -> str:
    return "OUT_ON" if enabled else "OUT_OFF"


def local() -> str:
    return "LOCAL"
