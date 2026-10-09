"""Dieselbe Aufrufseite wie die serielle Leitung, ohne Gerät."""

from __future__ import annotations

from pn300.model import SupplyState


class Simulator:
    def __init__(self, state: SupplyState | None = None) -> None:
        self.state = state or SupplyState()
        self.sent: list[str] = []

    def send(self, command: str) -> str:
        self.sent.append(command)
        return "OK"

    def close(self) -> None:
        return None
