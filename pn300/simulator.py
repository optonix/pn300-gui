"""Dieselbe Aufrufseite wie die serielle Leitung, ohne Gerät."""

from __future__ import annotations

from pn300.model import SupplyState


class Simulator:
    def __init__(self, state: SupplyState | None = None) -> None:
        self.state = state or SupplyState()
        self.sent: list[str] = []

    def send(self, command: str) -> str:
        self.sent.append(command)
        if command == "OUT_ON":
            self.state.output_on = True
            return "OUT_ON"
        if command == "OUT_OFF":
            self.state.output_on = False
            return "OUT_OFF"
        if command == "OUT?":
            return "OUT_ON" if self.state.output_on else "OUT_OFF"
        return "OK"

    def close(self) -> None:
        return None
