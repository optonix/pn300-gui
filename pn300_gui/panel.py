"""Frontpanel nach dem PN-300-Vorbild."""

from __future__ import annotations

import flet as ft

from pn300.device import Device
from pn300.model import MODES, V_MAX
from pn300.protocol import BAUD_RATES
from pn300_gui.display import fit16, reading
from pn300_gui.ports import list_serial_ports

FACE = "#eceae4"
INK = "#1c2430"
BLUE = "#1e3a8a"
KEY = "#d7d7d7"
KEY_INK = "#2a2a2a"


class PN300Panel:
    def __init__(self, page: ft.Page, device: Device | None = None) -> None:
        self.page = page
        self.device = device or Device()
        self.lcd_1 = ft.Text(fit16(""), font_family="Consolas", size=26, color="#1a1a1a", weight=ft.FontWeight.W_700)
        self.lcd_2 = ft.Text(fit16(""), font_family="Consolas", size=26, color="#1a1a1a", weight=ft.FontWeight.W_700)
        self.leds: dict[str, ft.Container] = {}
        self.link_mark = ft.Container(width=14, height=14, bgcolor="#9aa09a", border_radius=2)
        self.link_text = ft.Text("Nicht verbunden", size=13, color="#333")
        self.port = ft.Dropdown(
            width=130,
            value="Simulator",
            options=[ft.dropdown.Option("Simulator")],
            text_size=13,
            content_padding=6,
            on_change=self.on_port,
        )
        self.baud = ft.Dropdown(
            width=90,
            value="9600",
            options=[ft.dropdown.Option(str(rate)) for rate in BAUD_RATES],
            text_size=13,
            content_padding=6,
            on_change=self.on_baud,
        )
        self.handshake = ft.Dropdown(
            width=110,
            value="keines",
            options=[ft.dropdown.Option("keines"), ft.dropdown.Option("RTS/CTS")],
            text_size=13,
            content_padding=6,
            on_change=self.on_handshake,
        )

    @property
    def state(self):
        return self.device.state

    def led(self, key: str, on: str) -> ft.Container:
        dot = ft.Container(
            width=14,
            height=14,
            border_radius=7,
            bgcolor="#8d8d8d",
            border=ft.border.all(1, "#6a6a6a"),
            data=on,
        )
        self.leds[key] = dot
        return dot

    def set_led(self, key: str, lit: bool) -> None:
        dot = self.leds[key]
        dot.bgcolor = dot.data if lit else "#8d8d8d"

    def key_button(self, label: str, on_click, width: int = 58, height: int = 32) -> ft.ElevatedButton:
        return ft.ElevatedButton(
            content=ft.Text(label, size=12, weight=ft.FontWeight.W_600, color=KEY_INK),
            width=width,
            height=height,
            style=ft.ButtonStyle(
                bgcolor=KEY,
                color=KEY_INK,
                overlay_color="#c0c0c0",
                shape=ft.RoundedRectangleBorder(radius=3),
                side=ft.BorderSide(1, "#9a9a9a"),
                padding=0,
                elevation=1,
            ),
            on_click=on_click,
        )

    def group(self, title: str, body: ft.Control, width: int) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(title, size=12, color="#4a4a4a", weight=ft.FontWeight.W_600),
                    body,
                ],
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=width,
            padding=ft.padding.only(left=8, right=8, top=6, bottom=10),
            border=ft.border.all(1, "#b7b7b7"),
            border_radius=4,
            bgcolor="#f4f3ef",
        )

    def banana(self, red: bool) -> ft.Container:
        return ft.Container(
            width=36,
            height=36,
            border_radius=18,
            bgcolor="#d32f2f" if red else "#2b2b2b",
            border=ft.border.all(4, "#9a1c1c" if red else "#111"),
            alignment=ft.alignment.center,
            content=ft.Container(width=10, height=10, border_radius=5, bgcolor="#111"),
        )

    def socket(self, spec_left: str, spec_right: str, name: str, note: str = "") -> ft.Control:
        row = ft.Row(
            [
                ft.Text("–", size=16, color="#444"),
                self.banana(False),
                ft.Text(name, size=14, weight=ft.FontWeight.W_700, color=INK),
                self.banana(True),
                ft.Text("+", size=16, color="#444"),
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
        )
        bits = [
            ft.Row(
                [
                    ft.Text(spec_left, size=13, color="#333"),
                    ft.Container(width=28),
                    ft.Text(spec_right, size=13, color="#333"),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            row,
        ]
        if note:
            bits.append(ft.Text(note, size=11, color="#555", text_align=ft.TextAlign.CENTER))
        return ft.Column(bits, spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def build(self) -> ft.Control:
        cv_block = ft.Column(
            [
                ft.Row(
                    [ft.Text("A", size=16, weight=ft.FontWeight.W_700), self.led("cv_a", "#43c45a"), ft.Text("CV", size=13)],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=1, bgcolor="#c8c8c8", width=78),
                ft.Row(
                    [ft.Text("B", size=16, weight=ft.FontWeight.W_700), self.led("cv_b", "#43c45a"), ft.Text("CV", size=13)],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=8,
        )
        lcd = ft.Container(
            content=ft.Column([self.lcd_1, self.lcd_2], spacing=4),
            width=300,
            height=86,
            bgcolor="#b6e24a",
            border_radius=2,
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            border=ft.border.all(1, "#8aa83a"),
        )
        cc_block = ft.Column(
            [
                ft.Row([ft.Text("CC", size=12), self.led("cc_a", "#e23b3b")], spacing=6),
                ft.Container(height=1, bgcolor="#c8c8c8", width=52),
                ft.Row([ft.Text("CC", size=12), self.led("cc_b", "#e23b3b")], spacing=6),
            ],
            spacing=8,
        )
        mode_block = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("IND", size=12, width=42, text_align=ft.TextAlign.CENTER),
                        ft.Text("TRACK", size=12, width=52, text_align=ft.TextAlign.CENTER),
                        ft.Text("PAR", size=12, width=42, text_align=ft.TextAlign.CENTER),
                    ],
                    spacing=6,
                ),
                ft.Row(
                    [
                        ft.Container(self.led("ind", "#43c45a"), width=42, alignment=ft.alignment.center),
                        ft.Container(self.led("track", "#43c45a"), width=52, alignment=ft.alignment.center),
                        ft.Container(self.led("par", "#43c45a"), width=42, alignment=ft.alignment.center),
                    ],
                    spacing=6,
                ),
            ],
            spacing=6,
        )
        sockets = ft.Column(
            [
                self.socket("0 – 30V", "0 – 2.3A", "A"),
                self.socket("–", "", "B", "250Vmax   MAX TO ⊥"),
                self.socket("5V", "2A", "⊥"),
            ],
            spacing=6,
        )
        power = ft.Column(
            [
                ft.Text("I  O", size=11, color="#666"),
                self.key_button("", self.toggle_mains, width=36, height=28),
            ],
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        set_keys = self.group(
            "SET",
            ft.Column(
                [
                    ft.Row([self.key_button("V", self.on_v), self.key_button("I", self.on_i)], spacing=6),
                    ft.Row([self.key_button("MODE", self.on_mode), self.key_button("MEM", self.on_mem)], spacing=6),
                    ft.Row([self.key_button("SYST", self.on_syst)], spacing=6),
                ],
                spacing=6,
            ),
            150,
        )
        select_keys = self.group(
            "SELECT",
            ft.Column(
                [
                    self.key_button("A/B", self.on_ab, width=64),
                    self.key_button("ENTER", self.on_enter, width=64),
                    self.key_button("ESC", self.on_esc, width=64),
                ],
                spacing=6,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            96,
        )
        adjust_keys = self.group(
            "ADJUST",
            ft.Column(
                [
                    self.key_button("▲", self.on_up, width=40),
                    ft.Row(
                        [
                            self.key_button("◄", self.on_left, width=40),
                            self.key_button("►", self.on_right, width=40),
                        ],
                        spacing=6,
                    ),
                    self.key_button("▼", self.on_down, width=40),
                ],
                spacing=6,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            120,
        )
        remote_block = ft.Column(
            [
                ft.Text("REMOTE", size=11, color="#555"),
                self.led("remote", "#d7a21a"),
                self.key_button("LOCAL", self.on_local, width=72),
            ],
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        out_block = ft.Column(
            [
                ft.Text("ON", size=11, color="#555"),
                self.led("out", "#43c45a"),
                self.key_button("OUT A/B", self.on_out, width=78),
            ],
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        header = ft.Container(
            content=ft.Row(
                [
                    ft.Text("Digimess", size=22, weight=ft.FontWeight.W_700, color=BLUE),
                    ft.Container(expand=True),
                    ft.Text("PN 300", size=20, weight=ft.FontWeight.W_700, color=BLUE),
                    ft.Text("PROGRAMMABLE POWER SUPPLY", size=16, color=BLUE),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            padding=ft.padding.only(left=16, right=16, top=10, bottom=6),
        )
        face = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [cv_block, lcd, cc_block, mode_block, ft.Container(expand=True), sockets],
                        spacing=16,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=8),
                    ft.Row(
                        [power, set_keys, select_keys, adjust_keys, ft.Container(expand=True), remote_block, out_block],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.END,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=FACE,
            padding=ft.padding.only(left=16, right=16, top=8, bottom=14),
            border=ft.border.all(1, "#cfcfcf"),
            border_radius=6,
            margin=ft.margin.symmetric(horizontal=10),
        )
        status = ft.Container(
            content=ft.Row(
                [
                    ft.Text("Port:", size=13, color="#222"),
                    self.port,
                    ft.Container(width=16),
                    ft.Text("Baud:", size=13, color="#222"),
                    self.baud,
                    ft.Container(width=16),
                    self.link_mark,
                    self.link_text,
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor="#ffffff",
            padding=ft.padding.symmetric(horizontal=10, vertical=4),
            border=ft.border.only(top=ft.BorderSide(1, "#d0d0d0")),
        )
        shell = ft.Container(
            content=ft.Column([header, face, status], spacing=0),
            bgcolor="#f3f1ec",
            border_radius=8,
            border=ft.border.all(1, "#d5d2cb"),
            width=1080,
        )
        self.scan_ports()
        self.refresh()
        return shell

    def refresh(self) -> None:
        s = self.state
        if not s.mains:
            self.lcd_1.value = fit16("")
            self.lcd_2.value = fit16("")
            self.lcd_1.color = "#7ea33a"
            self.lcd_2.color = "#7ea33a"
        else:
            self.lcd_1.color = "#1a1a1a"
            self.lcd_2.color = "#1a1a1a"
            self.lcd_1.value = fit16(self._line1())
            self.lcd_2.value = fit16(self._line2())
        self.set_led("ind", s.mains and s.mode == "IND")
        self.set_led("track", s.mains and s.mode == "TRACK")
        self.set_led("par", s.mains and s.mode == "PAR")
        self.set_led("remote", s.mains and s.remote)
        self.set_led("out", s.mains and s.output_on)
        self.set_led("cv_a", s.mains and s.output_on and s.cont_a == "CV")
        self.set_led("cv_b", s.mains and s.output_on and s.cont_b == "CV")
        self.set_led("cc_a", s.mains and s.output_on and s.cont_a == "CC")
        self.set_led("cc_b", s.mains and s.output_on and s.cont_b == "CC")
        connected = self.device.port_name != "Simulator" and not self.device.last_error
        self.link_mark.bgcolor = "#3cba54" if connected else "#9aa09a"
        if connected:
            self.link_text.value = "Connected"
        elif self.device.last_error:
            self.link_text.value = self.device.last_error[:42]
        else:
            self.link_text.value = "Simulator"
        self.page.update()

    def _line1(self) -> str:
        s = self.state
        if s.message:
            return s.message
        if s.edit == "V":
            return f"VOLTAGE_{s.channel}"
        if s.edit == "I":
            return f"CURRENT_{s.channel}"
        volts = s.measured_va if s.output_on else s.va
        amps = s.measured_ia if s.output_on else s.ia
        return reading(volts, amps)

    def _line2(self) -> str:
        s = self.state
        if s.message:
            return ""
        if s.edit in ("V", "I"):
            return f"  SET:[{s.draft:>7}]"
        volts = s.measured_vb if s.output_on else s.vb
        amps = s.measured_ib if s.output_on else s.ib
        return reading(volts, amps)

    def scan_ports(self, _e=None) -> None:
        found = list_serial_ports()
        current = self.port.value if self.port.value in found else "Simulator"
        self.port.options = [ft.dropdown.Option(name) for name in found]
        self.port.value = current
        if _e is not None:
            self.refresh()

    def on_port(self, e) -> None:
        self.device.use_port(e.control.value)
        self.port.value = self.device.port_name
        self.state.message = ""
        self.refresh()

    def toggle_mains(self, _e) -> None:
        self.state.mains = not self.state.mains
        if not self.state.mains:
            self.state.output_on = False
            self.state.edit = None
            self.state.message = ""
            self.device.set_output(False)
        self.refresh()

    def on_v(self, _e) -> None:
        if not self.state.mains:
            return
        self.state.edit = "V"
        self.state.message = ""
        self.state.draft = f"{self.state.selected_v():5.2f}"
        self.refresh()

    def on_i(self, _e) -> None:
        if not self.state.mains:
            return
        self.state.edit = "I"
        self.state.message = ""
        self.state.draft = f"{self.state.selected_i():5.3f}"
        self.refresh()

    def on_mode(self, _e) -> None:
        if not self.state.mains:
            return
        s = self.state
        s.mode = MODES[(MODES.index(s.mode) + 1) % 3]
        s.edit = None
        s.message = ""
        if s.mode == "TRACK":
            s.vb = s.va
        self.device.set_mode(s.mode)
        self.refresh()

    def on_mem(self, _e) -> None:
        if not self.state.mains:
            return
        self.state.edit = None
        if self.state.message.startswith("MEMORY"):
            self.state.message = f"RECALL {self.state.mem_slot}"
        else:
            self.state.message = f"MEMORY {self.state.mem_slot}"
        self.refresh()

    def on_syst(self, _e) -> None:
        if not self.state.mains:
            return
        self.scan_ports()
        identity = self.device.identify() or self.device.port_name
        self.state.message = identity[:16]
        self.refresh()

    def on_baud(self, e) -> None:
        self.device.use_port(self.device.port_name, baudrate=int(e.control.value), rtscts=self.state.rtscts)
        self.refresh()

    def on_handshake(self, e) -> None:
        self.device.use_port(self.device.port_name, rtscts=e.control.value == "RTS/CTS")
        self.refresh()

    def on_function(self, _e) -> None:
        if not self.state.mains:
            return
        kind = "CC" if (self.state.cont_a if self.state.channel == "A" else self.state.cont_b) == "CV" else "CV"
        self.device.set_function(kind)
        self.refresh()

    def on_protection(self, _e) -> None:
        if not self.state.mains:
            return
        self.device.set_protection("CUT" if self.state.protection == "LIM" else "LIM")
        self.refresh()

    def on_reset(self, _e) -> None:
        if not self.state.mains:
            return
        self.device.reset()
        self.state.message = "RESET"
        self.refresh()

    def on_lock(self, _e) -> None:
        if not self.state.mains:
            return
        self.device.lock_local()
        self.refresh()

    def on_ab(self, _e) -> None:
        s = self.state
        if not s.mains or s.mode == "PAR":
            return
        s.channel = "B" if s.channel == "A" else "A"
        s.message = ""
        if s.edit == "V":
            s.draft = f"{s.selected_v():5.2f}"
        elif s.edit == "I":
            s.draft = f"{s.selected_i():5.3f}"
        self.refresh()

    def on_enter(self, _e) -> None:
        if not self.state.mains:
            return
        s = self.state
        if s.message.startswith("MEMORY"):
            self.device.save(s.mem_slot)
            s.message = f"SAVED  {s.mem_slot}"
            self.refresh()
            return
        if s.message.startswith("RECALL"):
            self.device.recall(s.mem_slot)
            s.message = f"LOADED {s.mem_slot}"
            self.refresh()
            return
        if s.edit is None:
            return
        try:
            value = float(s.draft)
        except ValueError:
            s.message = "EINGABE FEHLER"
            s.edit = None
            self.refresh()
            return
        if s.edit == "V":
            value = min(max(value, 0.0), V_MAX)
            if s.channel == "A" or s.mode in ("TRACK", "PAR"):
                s.va = value
            if s.channel == "B" or s.mode in ("TRACK", "PAR"):
                s.vb = value
            self.device.set_voltage(s.channel, value)
        else:
            value = min(max(value, s.i_floor()), s.i_limit())
            if s.channel == "A" or s.mode == "PAR":
                s.ia = value
            if s.channel == "B" or s.mode == "PAR":
                s.ib = value
            self.device.set_current(s.channel, value)
        s.edit = None
        s.message = ""
        self.refresh()

    def on_esc(self, _e) -> None:
        self.state.edit = None
        self.state.message = ""
        self.refresh()

    def _nudge(self, delta: float) -> None:
        s = self.state
        if not s.mains or s.edit is None:
            return
        try:
            value = float(s.draft)
        except ValueError:
            value = 0.0
        step = 0.01 if s.edit == "V" else 0.001
        limit = V_MAX if s.edit == "V" else s.i_limit()
        value = min(max(value + delta * step, 0.0), limit)
        s.draft = f"{value:5.2f}" if s.edit == "V" else f"{value:5.3f}"
        self.refresh()

    def on_up(self, _e) -> None:
        if self.state.message.startswith(("MEMORY", "RECALL")):
            self.state.mem_slot = 0 if self.state.mem_slot == 5 else self.state.mem_slot + 1
            prefix = "RECALL" if self.state.message.startswith("RECALL") else "MEMORY"
            self.state.message = f"{prefix} {self.state.mem_slot}"
            self.refresh()
            return
        self._nudge(1)

    def on_down(self, _e) -> None:
        if self.state.message.startswith(("MEMORY", "RECALL")):
            self.state.mem_slot = 5 if self.state.mem_slot == 0 else self.state.mem_slot - 1
            prefix = "RECALL" if self.state.message.startswith("RECALL") else "MEMORY"
            self.state.message = f"{prefix} {self.state.mem_slot}"
            self.refresh()
            return
        self._nudge(-1)

    def on_left(self, _e) -> None:
        self._nudge(-10)

    def on_right(self, _e) -> None:
        self._nudge(10)

    def on_local(self, _e) -> None:
        if not self.state.mains:
            return
        if self.state.remote:
            self.device.set_local()
        else:
            self.device.enter_remote()
        self.refresh()

    def on_out(self, _e) -> None:
        if not self.state.mains:
            return
        self.state.output_on = self.device.set_output(not self.state.output_on)
        self.state.message = ""
        self.refresh()
