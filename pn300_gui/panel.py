"""Frontpanel nach dem PN-300-Vorbild."""

from __future__ import annotations

import asyncio

import flet as ft

from pn300.device import Device
from pn300.face import Face
from pn300.protocol import BAUD_RATES
from pn300_gui.ports import list_serial_ports

FACE = "#eceae4"
INK = "#1c2430"
BLUE = "#1e3a8a"
KEY = "#d7d7d7"
KEY_INK = "#2a2a2a"
LED_OFF = "#8d8d8d"


class PN300Panel:
    def __init__(self, page: ft.Page, device: Device | None = None) -> None:
        self.page = page
        self.device = device or Device()
        self.face = Face(self.device)
        self._blink_on = True
        self._boot_token = 0
        self._ignore_link = False
        self.lcd_1 = ft.Text("", font_family="Consolas", size=26, color="#1a1a1a", weight=ft.FontWeight.W_700)
        self.lcd_2 = ft.Text("", font_family="Consolas", size=26, color="#1a1a1a", weight=ft.FontWeight.W_700)
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
            bgcolor=LED_OFF,
            border=ft.border.all(1, "#6a6a6a"),
            data=on,
        )
        self.leds[key] = dot
        return dot

    def set_led(self, key: str, color: str | None) -> None:
        self.leds[key].bgcolor = color or LED_OFF

    def key_button(self, label: str, on_click, width: int = 58, height: int = 32) -> ft.Control:
        token = {"holding": False}

        async def repeat() -> None:
            await asyncio.sleep(0.4)
            while token["holding"]:
                on_click(None)
                await asyncio.sleep(0.12)

        def down(_e) -> None:
            token["holding"] = True
            on_click(None)
            self.page.run_task(repeat)

        def up(_e) -> None:
            token["holding"] = False

        return ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.CLICK,
            on_tap_down=down,
            on_tap_up=up,
            on_exit=up,
            content=ft.Container(
                content=ft.Text(label, size=12, weight=ft.FontWeight.W_600, color=KEY_INK),
                width=width,
                height=height,
                bgcolor=KEY,
                border_radius=3,
                border=ft.border.all(1, "#9a9a9a"),
                alignment=ft.alignment.center,
            ),
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

    def socket_row(self, left_label: str, right_label: str, center: str) -> ft.Control:
        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(left_label, size=12, color="#333", width=58, text_align=ft.TextAlign.RIGHT),
                        ft.Container(width=36),
                        ft.Text(right_label, size=12, color="#333", width=58),
                    ],
                    spacing=6,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Row(
                    [
                        ft.Text("–", size=14, color="#444"),
                        self.banana(False),
                        ft.Text(center, size=14, weight=ft.FontWeight.W_700, color=INK, width=22, text_align=ft.TextAlign.CENTER),
                        self.banana(True),
                        ft.Text("+", size=14, color="#444"),
                    ],
                    spacing=6,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

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
            content=ft.Column([self.lcd_1, self.lcd_2], spacing=2),
            width=340,
            height=92,
            bgcolor="#b6e24a",
            border_radius=2,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            border=ft.border.all(1, "#7a9a30"),
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
                self.socket_row("0 – 30V", "0 – 2.3A", "A"),
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text("–", size=14, color="#444"),
                                self.banana(False),
                                ft.Text("B", size=14, weight=ft.FontWeight.W_700, width=22, text_align=ft.TextAlign.CENTER),
                                self.banana(True),
                                ft.Text("+", size=14, color="#444"),
                            ],
                            spacing=6,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        ft.Text("250Vmax   MAX TO ⊥", size=10, color="#555"),
                    ],
                    spacing=2,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text("5V", size=12, color="#333", width=58, text_align=ft.TextAlign.RIGHT),
                                ft.Container(width=36),
                                ft.Text("2A", size=12, color="#333", width=58),
                            ],
                            spacing=6,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        ft.Row(
                            [
                                ft.Text("–", size=14, color="#444"),
                                self.banana(False),
                                ft.Text("⊥", size=14, weight=ft.FontWeight.W_700, width=22, text_align=ft.TextAlign.CENTER),
                                self.banana(True),
                                ft.Text("+", size=14, color="#444"),
                            ],
                            spacing=6,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=2,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=8,
        )
        power = ft.Column(
            [
                ft.Text("I  O", size=11, color="#666"),
                self.key_button("", self._press("power"), width=36, height=28),
            ],
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        set_keys = self.group(
            "SET",
            ft.Column(
                [
                    ft.Row([self.key_button("V", self._press("v")), self.key_button("I", self._press("i"))], spacing=6),
                    ft.Row([self.key_button("MODE", self._press("mode")), self.key_button("MEM", self._press("mem"))], spacing=6),
                    ft.Row([self.key_button("SYST", self._press("syst"))], spacing=6),
                ],
                spacing=6,
            ),
            150,
        )
        select_keys = self.group(
            "SELECT",
            ft.Column(
                [
                    self.key_button("A/B", self._press("ab"), width=64),
                    self.key_button("ENTER", self._press("enter"), width=64),
                    self.key_button("ESC", self._press("esc"), width=64),
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
                    self.key_button("▲", self._press("up"), width=40),
                    ft.Row(
                        [
                            self.key_button("◄", self._press("left"), width=40),
                            self.key_button("►", self._press("right"), width=40),
                        ],
                        spacing=6,
                    ),
                    self.key_button("▼", self._press("down"), width=40),
                ],
                spacing=6,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            120,
        )
        remote_block = ft.Column(
            [
                ft.Text("REMOTE", size=11, color="#555"),
                self.led("remote", "#e23b3b"),
                self.key_button("LOCAL", self._press("local"), width=72),
            ],
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        out_block = ft.Column(
            [
                ft.Text("ON", size=11, color="#555"),
                self.led("out", "#43c45a"),
                self.key_button("OUT A/B", self._press("out"), width=78),
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
                    ft.Text("Handshake:", size=13, color="#222"),
                    self.handshake,
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
        self._boot_token += 1
        self.page.run_task(self._animate_boot, self._boot_token)
        self.page.run_task(self._blink)
        return shell

    def _press(self, key: str):
        def handler(_e=None) -> None:
            self.face.press(key)
            if key == "power" and self.face.phase == "boot":
                self._boot_token += 1
                self.page.run_task(self._animate_boot, self._boot_token)
            self.refresh()

        return handler

    async def _animate_boot(self, token: int) -> None:
        while self.face.phase == "boot" and token == self._boot_token:
            self.refresh()
            await asyncio.sleep(0.3)
            if token != self._boot_token or self.face.phase != "boot":
                break
            if not self.face.advance_boot():
                break
        if token == self._boot_token:
            self.refresh()

    async def _blink(self) -> None:
        while True:
            await asyncio.sleep(0.4)
            self._blink_on = not self._blink_on
            if self.face.cursor_mark():
                self.refresh()

    def refresh(self) -> None:
        first, second = self.face.lines()
        self._paint_line(self.lcd_1, first, 0)
        self._paint_line(self.lcd_2, second, 1)
        for name, color in self.face.led_colors().items():
            self.set_led(name, color)
        connected = self.device.port_name != "Simulator" and not self.device.last_error
        self.link_mark.bgcolor = "#3cba54" if connected else "#9aa09a"
        if connected:
            self.link_text.value = "Connected"
        elif self.device.last_error:
            self.link_text.value = self.device.last_error[:42]
        else:
            self.link_text.value = "Simulator"
        self._ignore_link = True
        self.baud.value = str(self.state.baudrate)
        self.handshake.value = "RTS/CTS" if self.state.rtscts else "keines"
        if self.port.options and any(option.key == self.device.port_name for option in self.port.options):
            self.port.value = self.device.port_name
        self._ignore_link = False
        self.page.update()

    def _paint_line(self, control: ft.Text, text: str, line_no: int) -> None:
        mark = self.face.cursor_mark() if self.state.mains else None
        base = "#1a1a1a" if self.state.mains else "#7ea33a"
        spans: list[ft.TextSpan] = []
        for index, char in enumerate(text):
            highlighted = bool(mark and mark[0] == line_no and mark[1] == index and self._blink_on)
            if highlighted:
                style = ft.TextStyle(
                    bgcolor="#1a1a1a",
                    color="#b6e24a",
                    font_family="Consolas",
                    size=26,
                    weight=ft.FontWeight.W_700,
                )
            else:
                style = ft.TextStyle(color=base, font_family="Consolas", size=26, weight=ft.FontWeight.W_700)
            spans.append(ft.TextSpan(char, style))
        control.value = ""
        control.spans = spans
        control.color = base

    def scan_ports(self, _e=None) -> None:
        found = list_serial_ports()
        current = self.port.value if self.port.value in found else "Simulator"
        self.port.options = [ft.dropdown.Option(name) for name in found]
        self.port.value = current
        if _e is not None:
            self.refresh()

    def on_port(self, e) -> None:
        if self._ignore_link:
            return
        self.device.use_port(e.control.value)
        self.face._home()
        self.refresh()

    def on_baud(self, e) -> None:
        if self._ignore_link:
            return
        self.device.use_port(self.device.port_name, baudrate=int(e.control.value), rtscts=self.state.rtscts)
        self.face._home()
        self.refresh()

    def on_handshake(self, e) -> None:
        if self._ignore_link:
            return
        self.device.use_port(self.device.port_name, rtscts=e.control.value == "RTS/CTS")
        self.face._home()
        self.refresh()
