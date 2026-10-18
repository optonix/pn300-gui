"""Tasten des Frontpanels nach Kapitel 5 und 6 der Gebrauchsanweisung."""

from __future__ import annotations

from pn300.device import Device
from pn300.model import SupplyState
from pn300.protocol import BAUD_RATES

MODE_ITEMS = ("OPERATION", "CONTROL", "ADJUSTMENT", "PROTECTION")
OPER_ORDER = ("IND", "TRACK", "PAR")
OPER_TEXT = {"IND": "INDEPEND", "TRACK": "A-B TRAC", "PAR": "A-B PAR"}
MEM_ITEMS = ("STORE", "LOAD")
BOOT_UNITS = ("CPU", "ROM", "RAM", "KEY", "BATTERY", "DISPLAY")
LED_GREEN = "#43c45a"
LED_RED = "#e23b3b"
LED_NAMES = ("ind", "track", "par", "remote", "out", "cv_a", "cv_b", "cc_a", "cc_b")


def pad(text: str) -> str:
    return text[:16].ljust(16)


def bracket(prefix: str, value: str) -> str:
    inner = 16 - len(prefix) - 1
    return pad(f"{prefix}{value[:inner]:<{inner}}]")


class Face:
    def __init__(self, device: Device) -> None:
        self.device = device
        self.phase = "boot"
        self.boot_at = 0
        self.menu: dict | None = None
        self.edit: dict | None = None
        self.showing_measured = False

    @property
    def state(self) -> SupplyState:
        return self.device.state

    def skip_boot(self) -> None:
        self.phase = "run"

    def advance_boot(self) -> bool:
        if self.phase != "boot":
            return False
        self.boot_at += 1
        if self.boot_at >= len(BOOT_UNITS):
            self.phase = "run"
            if self.device.port_name != "Simulator":
                self.device.poll()
            return False
        return True

    def power(self, on: bool) -> None:
        state = self.state
        self.menu = None
        self.edit = None
        self.showing_measured = False
        state.alert = None
        if not on:
            state.mains = False
            state.lockout = False
            if self.device.port_name == "Simulator":
                self.device.simulator_mains(False)
            else:
                state.output_on = False
                state.measured_va = state.measured_vb = 0.0
                state.measured_ia = state.measured_ib = 0.0
            self.phase = "off"
            return
        state.mains = True
        if self.device.port_name == "Simulator":
            self.device.simulator_mains(True)
            self.phase = "boot"
            self.boot_at = 0
            return
        self.phase = "run"
        self.device.poll()

    def lines(self) -> tuple[str, str]:
        if not self.state.mains or self.phase == "off":
            return pad(""), pad("")
        if self.phase == "boot":
            unit = BOOT_UNITS[min(self.boot_at, len(BOOT_UNITS) - 1)]
            return pad(f"Testing: {unit}"), pad(".......Passed")
        if self.menu:
            return self._menu_lines()
        if self.edit and not self.edit["direct"]:
            return self._indirect_lines()
        if self.state.alert:
            return pad(self.state.alert[0]), pad(self.state.alert[1])
        return self._readings(self._show_measured())

    def cursor_mark(self) -> tuple[int, int] | None:
        if self.phase != "run" or self.edit is None:
            return None
        line_no = 1
        if self.edit["direct"]:
            line_no = 0 if self.state.channel == "A" else 1
        text = self.lines()[line_no]
        places = digit_places(text, self.edit["kind"], self.edit["direct"])
        if not places:
            return None
        cursor = min(self.edit["cursor"], len(places) - 1)
        return line_no, places[cursor]

    def led_colors(self) -> dict[str, str | None]:
        state = self.state
        if not state.mains or self.phase != "run":
            return {name: None for name in LED_NAMES}
        cv_a, cc_a = _regulation_colors(state.cont_a)
        cv_b, cc_b = _regulation_colors(state.cont_b)
        return {
            "ind": LED_GREEN if state.mode == "IND" else None,
            "track": LED_GREEN if state.mode == "TRACK" else None,
            "par": LED_GREEN if state.mode == "PAR" else None,
            "remote": LED_RED if state.remote else None,
            "out": LED_GREEN if state.output_on else None,
            "cv_a": cv_a,
            "cc_a": cc_a,
            "cv_b": cv_b,
            "cc_b": cc_b,
        }

    def press(self, key: str) -> None:
        if key == "power":
            self.power(not self.state.mains)
            return
        if not self.state.mains or self.phase != "run":
            return
        handler = {
            "v": self._voltage,
            "i": self._current,
            "mode": self._mode,
            "mem": self._memory,
            "syst": self._system,
            "ab": self._channel,
            "enter": self._enter,
            "esc": self._escape,
            "up": lambda: self._arrow(1),
            "down": lambda: self._arrow(-1),
            "left": lambda: self._move(-1),
            "right": lambda: self._move(1),
            "local": self._local,
            "out": self._output,
        }.get(key)
        if handler:
            handler()

    def _show_measured(self) -> bool:
        if not self.state.output_on:
            return False
        if self.state.adjustment == "DIRECT":
            return self.edit is None
        return True

    def _readings(self, measured: bool) -> tuple[str, str]:
        state = self.state
        if measured:
            return (
                pad(_reading(state.measured_va, state.measured_ia)),
                pad(_reading(state.measured_vb, state.measured_ib)),
            )
        return pad(_reading(state.va, state.ia)), pad(_reading(state.vb, state.ib))

    def _home(self) -> None:
        self.menu = None
        self.edit = None

    def _voltage(self) -> None:
        self._open_value("V")

    def _current(self) -> None:
        self._open_value("I")

    def _open_value(self, kind: str) -> None:
        if self.menu:
            return
        self.state.alert = None
        direct = self.state.adjustment == "DIRECT" and self.state.output_on
        self.showing_measured = False
        self.edit = {
            "kind": kind,
            "cursor": 3,
            "direct": direct,
            "draft": self._selected_value(kind),
        }

    def _mode(self) -> None:
        self.edit = None
        self.menu = {"kind": "mode", "index": 0}

    def _memory(self) -> None:
        self.edit = None
        self.menu = {"kind": "mem", "index": 0}

    def _system(self) -> None:
        self.edit = None
        self.menu = {"kind": "syst"}

    def _channel(self) -> None:
        state = self.state
        if state.mode == "PAR":
            return
        state.channel = "B" if state.channel == "A" else "A"
        if self.edit is None:
            return
        self.edit["cursor"] = 3
        if not self.edit["direct"]:
            self.edit["draft"] = self._selected_value(self.edit["kind"])

    def _enter(self) -> None:
        menu = self.menu
        if menu:
            self._enter_menu(menu)
            return
        if self.edit and not self.edit["direct"]:
            self._commit_draft()
            self._home()

    def _escape(self) -> None:
        if self.menu or (self.edit and not self.edit["direct"]):
            self._home()
            return
        if self.state.adjustment == "DIRECT" and self.state.output_on:
            self.edit = None
            self.showing_measured = True

    def _local(self) -> None:
        if self.state.lockout or not self.state.remote:
            return
        self.device.set_local()
        self._home()

    def _output(self) -> None:
        enable = not self.state.output_on
        self.state.alert = None
        self.device.set_output(enable)
        self.menu = None
        if self.state.output_on and self.state.adjustment == "DIRECT":
            self.showing_measured = False
            self.edit = {
                "kind": "V",
                "cursor": 3,
                "direct": True,
                "draft": self._selected_value("V"),
            }
            return
        self.edit = None
        self.showing_measured = False

    def _arrow(self, step: int) -> None:
        menu = self.menu
        if menu:
            self._scroll(menu, step)
            return
        if self.edit:
            self._bump(step)

    def _move(self, step: int) -> None:
        if self.menu or self.edit is None:
            return
        self.edit["cursor"] = min(3, max(0, self.edit["cursor"] + step))

    def _bump(self, sign: int) -> None:
        assert self.edit is not None
        kind = self.edit["kind"]
        cursor = self.edit["cursor"]
        current = self._selected_value(kind) if self.edit["direct"] else self.edit["draft"]
        weight = (1000, 100, 10, 1)[cursor]
        if kind == "V":
            unit = int(round(current * 100))
            unit = min(3000, max(0, unit + sign * weight))
            value = unit / 100
        else:
            unit = int(round(current * 1000))
            floor = int(round(self.state.i_floor() * 1000))
            limit = int(round(self.state.i_limit() * 1000))
            unit = min(limit, max(floor, unit + sign * weight))
            value = unit / 1000
        if self.edit["direct"]:
            self._send_value(kind, value)
            return
        self.edit["draft"] = value

    def _commit_draft(self) -> None:
        assert self.edit is not None
        self._send_value(self.edit["kind"], self.edit["draft"])

    def _send_value(self, kind: str, value: float) -> None:
        if kind == "V":
            self.device.set_voltage(self.state.channel, value)
        else:
            self.device.set_current(self.state.channel, value)

    def _selected_value(self, kind: str) -> float:
        state = self.state
        if kind == "V":
            return state.va if state.channel == "A" else state.vb
        return state.ia if state.channel == "A" else state.ib

    def _scroll(self, menu: dict, step: int) -> None:
        kind = menu["kind"]
        if kind == "mode":
            menu["index"] = (menu["index"] + step) % len(MODE_ITEMS)
        elif kind == "oper":
            menu["value"] = _cycle(OPER_ORDER, menu["value"], step)
        elif kind == "cont":
            menu["value"] = "CC" if menu["value"] == "CV" else "CV"
        elif kind == "adj":
            menu["value"] = "DIRECT" if menu["value"] == "INDIRECT" else "INDIRECT"
        elif kind == "prot":
            menu["value"] = "CUT" if menu["value"] == "LIM" else "LIM"
        elif kind == "mem":
            menu["index"] = (menu["index"] + step) % len(MEM_ITEMS)
        elif kind == "slot":
            menu["slot"] = (menu["slot"] + step) % 6
        elif kind == "iface":
            menu["value"] = "GPIB" if menu["value"] == "RS232" else "RS232"
        elif kind == "baud":
            menu["value"] = _cycle(BAUD_RATES, menu["value"], step)
        elif kind == "handshake":
            menu["value"] = not menu["value"]
        elif kind == "addr":
            menu["value"] = (menu["value"] + step) % 31

    def _enter_menu(self, menu: dict) -> None:
        kind = menu["kind"]
        state = self.state
        if kind == "mode":
            item = MODE_ITEMS[menu["index"]]
            if item == "OPERATION":
                self.menu = {"kind": "oper", "value": state.mode}
            elif item == "CONTROL":
                cont = state.cont_a if state.channel == "A" else state.cont_b
                self.menu = {"kind": "cont", "value": cont}
            elif item == "ADJUSTMENT":
                self.menu = {"kind": "adj", "value": state.adjustment}
            else:
                self.menu = {"kind": "prot", "value": state.protection}
            return
        if kind == "oper":
            self.device.set_mode(menu["value"])
        elif kind == "cont":
            self.device.set_function(menu["value"])
        elif kind == "adj":
            state.adjustment = menu["value"]
        elif kind == "prot":
            self.device.set_protection(menu["value"])
        elif kind == "mem":
            self.menu = {"kind": "slot", "action": MEM_ITEMS[menu["index"]], "slot": 0}
            return
        elif kind == "slot":
            self.menu = {"kind": "sure", "action": menu["action"], "slot": menu["slot"]}
            return
        elif kind == "sure":
            if menu["action"] == "STORE":
                self.device.save(menu["slot"])
            else:
                self.device.recall(menu["slot"])
        elif kind == "syst":
            self.menu = {"kind": "iface", "value": state.iface}
            return
        elif kind == "iface":
            if menu["value"] == "GPIB":
                self.menu = {"kind": "addr", "value": state.gpib_address}
            else:
                self.menu = {"kind": "baud", "value": state.baudrate}
            return
        elif kind == "baud":
            self.menu = {"kind": "handshake", "value": state.rtscts, "baud": menu["value"]}
            return
        elif kind == "handshake":
            state.iface = "RS232"
            state.baudrate = menu.get("baud", state.baudrate)
            state.rtscts = bool(menu["value"])
            self.device.use_port(self.device.port_name, baudrate=state.baudrate, rtscts=state.rtscts)
        elif kind == "addr":
            state.iface = "GPIB"
            state.gpib_address = menu["value"]
        self._home()

    def _menu_lines(self) -> tuple[str, str]:
        menu = self.menu or {}
        kind = menu["kind"]
        state = self.state
        if kind == "mode":
            return pad("MODE"), bracket("[", MODE_ITEMS[menu["index"]])
        if kind == "oper":
            return pad("MODE"), bracket("OPER:[", OPER_TEXT[menu["value"]])
        if kind == "cont":
            return pad(f"MODE_{state.channel}"), bracket("CONT:[", menu["value"])
        if kind == "adj":
            return pad("MODE"), bracket("ADJ :[", menu["value"])
        if kind == "prot":
            label = "LIMITING" if menu["value"] == "LIM" else "CUT-OUT"
            return pad("MODE"), bracket("PROT:[", label)
        if kind == "mem":
            return pad("MMEM"), bracket("[", MEM_ITEMS[menu["index"]])
        if kind == "slot":
            title = "STORE" if menu["action"] == "STORE" else "LOAD"
            return pad(title), bracket("SET#:[", str(menu["slot"]))
        if kind == "sure":
            return pad("Are you sure ?"), pad("")
        if kind == "syst":
            return pad("SYSTEM"), bracket("[", "INTERFACE")
        if kind == "iface":
            label = "RS 232C" if menu["value"] == "RS232" else "GPIB"
            return pad("INTERFACE"), bracket("SEL :[", label)
        if kind == "baud":
            return pad("RS 232C"), bracket("RATE:[", f"{menu['value']} Bd")
        if kind == "handshake":
            label = "RTS/CTS" if menu["value"] else "without"
            return pad("RS 232C"), bracket("PROT:[", label)
        if kind == "addr":
            return pad("GPIB"), bracket("ADDR:[", str(menu["value"]))
        return pad(""), pad("")

    def _indirect_lines(self) -> tuple[str, str]:
        assert self.edit is not None
        kind = self.edit["kind"]
        state = self.state
        value = self.edit["draft"]
        cont = state.cont_a if state.channel == "A" else state.cont_b
        if kind == "V":
            title = f"VOLTAGE_{state.channel}"
            label = "SET" if cont == "CV" else "LIM"
            text = f"{value:05.2f}"
        else:
            title = f"CURRENT_{state.channel}"
            label = "SET" if cont == "CC" else "LIM"
            text = f"{value:6.3f}"
        return pad(title), bracket(f"{label} :[", text)


def _reading(volts: float, amps: float) -> str:
    return f"{volts:05.2f}V {amps:6.3f}A"


def _regulation_colors(cont: str) -> tuple[str, str]:
    if cont == "CV":
        return LED_GREEN, LED_RED
    return LED_RED, LED_GREEN


def digit_places(text: str, kind: str, direct: bool) -> list[int]:
    if not direct:
        if "[" not in text or "]" not in text:
            return []
        start = text.index("[") + 1
        end = text.index("]", start)
        return [index for index in range(start, end) if text[index].isdigit()]
    if kind == "V":
        end = text.index("V") if "V" in text else len(text)
        return [index for index in range(end) if text[index].isdigit()]
    start = text.index("V") + 1 if "V" in text else 0
    return [index for index in range(start, len(text)) if text[index].isdigit()]


def _cycle(options: tuple, current, step: int):
    index = options.index(current)
    return options[(index + step) % len(options)]
