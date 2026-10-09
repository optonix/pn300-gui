"""Fassade für die Oberfläche. Simulator oder COM-Port, gleiche Aufrufe."""

from __future__ import annotations

from pn300 import protocol
from pn300.model import SupplyState
from pn300.simulator import Simulator
from pn300.transport import SerialTransport


class Device:
    def __init__(self) -> None:
        self.state = SupplyState()
        self.port_name = "Simulator"
        self._link: Simulator | SerialTransport = Simulator(self.state)
        self.last_error = ""

    def use_port(self, name: str) -> None:
        self.close()
        self.port_name = name or "Simulator"
        self.last_error = ""
        if self.port_name == "Simulator":
            self._link = Simulator(self.state)
            return
        try:
            self._link = SerialTransport(self.port_name)
        except Exception as exc:
            self.last_error = str(exc)
            self.port_name = "Simulator"
            self._link = Simulator(self.state)

    def close(self) -> None:
        self._link.close()

    def _send(self, command: str) -> str:
        try:
            answer = self._link.send(command)
            self.last_error = ""
            return answer
        except Exception as exc:
            self.last_error = str(exc)
            return ""

    def set_voltage(self, channel: str, value: float) -> None:
        self._send(protocol.select_channel(channel))
        self._send(protocol.voltage_set(value))

    def set_current(self, channel: str, value: float) -> None:
        self._send(protocol.select_channel(channel))
        self._send(protocol.current_set(value))

    def set_mode(self, mode: str) -> None:
        self._send(protocol.operating_mode(mode))

    def set_output(self, enabled: bool) -> bool:
        self._send(protocol.output_on() if enabled else protocol.output_off())
        answer = self._send(protocol.output_query())
        parsed = protocol.parse_output(answer)
        if parsed is None:
            self.state.output_on = enabled
            return enabled
        self.state.output_on = parsed
        return parsed

    def set_local(self) -> None:
        self._send(protocol.local())
