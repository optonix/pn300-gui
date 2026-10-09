"""Frontpanel-GUI für das Digimess / Grundig PN 300.

Die Anordnung folgt dem Gerät: Netzschalter, CV-LEDs, 2x16-LC-Display,
CC- und Betriebsart-LEDs, Buchsen A/B/C und die Tastenfelder SET, SELECT, ADJUST.
Die Tasten ändern vorerst nur den lokalen Zustand. Die RS-232-Anbindung kommt danach.
"""

from __future__ import annotations

import flet as ft

LCD_COLS = 16
V_MAX = 30.0
I_MAX = 2.3
I_MAX_PAR = 4.6


def fit16(text: str) -> str:
    return text[:LCD_COLS].ljust(LCD_COLS)


class PanelState:
    def __init__(self) -> None:
        self.mains = True
        self.channel = "A"
        self.mode = "IND"  # IND, TRACK, PAR
        self.output_on = False
        self.remote = False
        self.va = 5.00
        self.ia = 0.500
        self.vb = 5.00
        self.ib = 0.500
        self.edit: str | None = None  # "V" or "I"
        self.draft = ""
        self.mem_slot = 1
        self.memories: dict[int, tuple[float, float, float, float, str]] = {}
        self.message = ""

    def selected_v(self) -> float:
        return self.va if self.channel == "A" else self.vb

    def selected_i(self) -> float:
        return self.ia if self.channel == "A" else self.ib

    def i_limit(self) -> float:
        return I_MAX_PAR if self.mode == "PAR" else I_MAX


class PN300Panel:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.state = PanelState()
        self.lcd_1 = ft.Text(fit16(""), font_family="Consolas", size=22, color="#14200c")
        self.lcd_2 = ft.Text(fit16(""), font_family="Consolas", size=22, color="#14200c")
        self.leds: dict[str, ft.Container] = {}
        self.remote_caption = ft.Text("LOCAL", size=11, weight=ft.FontWeight.W_600, color="#3c4038")
        self.out_caption = ft.Text("OUT A/B", size=11, weight=ft.FontWeight.W_600, color="#3c4038")
        self.footer = ft.Text("", size=12, color="#5c564c")

    def led(self, key: str, on: str) -> ft.Container:
        dot = ft.Container(
            width=12,
            height=12,
            border_radius=6,
            bgcolor="#2b2b2b",
            border=ft.border.all(1, "#1a1a1a"),
            data=on,
        )
        self.leds[key] = dot
        return dot

    def set_led(self, key: str, lit: bool) -> None:
        dot = self.leds[key]
        dot.bgcolor = dot.data if lit else "#2b2b2b"

    def key_button(self, label: str, on_click, width: int = 72, height: int = 36) -> ft.ElevatedButton:
        return ft.ElevatedButton(
            content=ft.Text(label, size=13, weight=ft.FontWeight.W_600, color="#f4f4f2"),
            width=width,
            height=height,
            style=ft.ButtonStyle(
                bgcolor="#6a6e72",
                color="#f4f4f2",
                overlay_color="#8a8e92",
                shape=ft.RoundedRectangleBorder(radius=3),
                padding=0,
                elevation=2,
            ),
            on_click=on_click,
        )

    def group(self, title: str, body: ft.Control) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(title, size=11, color="#8a8478", weight=ft.FontWeight.W_500),
                    body,
                ],
                spacing=6,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.only(left=8, right=8, top=4, bottom=8),
        )

    def banana(self, red: bool) -> ft.Container:
        color = "#c62828" if red else "#2a2a2a"
        ring = "#8d1c1c" if red else "#111111"
        return ft.Container(
            width=28,
            height=28,
            border_radius=14,
            bgcolor=color,
            border=ft.border.all(3, ring),
            alignment=ft.alignment.center,
            content=ft.Container(width=8, height=8, border_radius=4, bgcolor="#1a1a1a"),
        )

    def socket_row(self, name: str, spec: str) -> ft.Container:
        return ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(name, size=13, weight=ft.FontWeight.W_700, color="#3a4038"),
                            ft.Text(spec, size=10, color="#6a645c"),
                        ],
                        spacing=0,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    self.banana(False),
                    ft.Text("–", size=14, color="#444"),
                    self.banana(True),
                    ft.Text("+", size=14, color="#444"),
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            height=46,
        )

    def build(self) -> ft.Control:
        power = ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        width=34,
                        height=22,
                        border_radius=3,
                        bgcolor="#4a4e52",
                        on_click=self.toggle_mains,
                        ink=True,
                    ),
                    ft.Text("I  O", size=10, color="#6a645c"),
                ],
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=48,
        )

        cv_block = ft.Column(
            [
                ft.Row(
                    [ft.Text("A", size=16, weight=ft.FontWeight.W_700), self.led("cv_a", "#3ddc6a"), ft.Text("CV", size=12)],
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row(
                    [ft.Text("B", size=16, weight=ft.FontWeight.W_700), self.led("cv_b", "#3ddc6a"), ft.Text("CV", size=12)],
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=10,
        )

        lcd = ft.Container(
            content=ft.Column([self.lcd_1, self.lcd_2], spacing=6),
            width=280,
            height=78,
            bgcolor="#8ea85a",
            border_radius=2,
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            border=ft.border.all(6, "#d7d3c8"),
            shadow=ft.BoxShadow(blur_radius=8, color="#22000000", offset=ft.Offset(0, 1)),
        )

        status_leds = ft.Column(
            [
                ft.Row([ft.Text("CC", size=11), self.led("cc_a", "#e23b3b")], spacing=6),
                ft.Row([ft.Text("CC", size=11), self.led("cc_b", "#e23b3b")], spacing=6),
            ],
            spacing=12,
        )

        mode_leds = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("IND", size=11, width=36, text_align=ft.TextAlign.CENTER),
                        ft.Text("TRACK", size=11, width=44, text_align=ft.TextAlign.CENTER),
                        ft.Text("PAR", size=11, width=36, text_align=ft.TextAlign.CENTER),
                    ],
                    spacing=8,
                ),
                ft.Row(
                    [
                        ft.Container(self.led("ind", "#d7a21a"), width=36, alignment=ft.alignment.center),
                        ft.Container(self.led("track", "#d7a21a"), width=44, alignment=ft.alignment.center),
                        ft.Container(self.led("par", "#d7a21a"), width=36, alignment=ft.alignment.center),
                    ],
                    spacing=8,
                ),
            ],
            spacing=6,
        )

        sockets = ft.Column(
            [
                self.socket_row("A", "0–30 V   0–2,3 A"),
                self.socket_row("B", "0–30 V   0–2,3 A"),
                self.socket_row("C", "5 V   2 A"),
            ],
            spacing=4,
        )

        set_keys = self.group(
            "SET",
            ft.Column(
                [
                    ft.Row([self.key_button("V", self.on_v), self.key_button("I", self.on_i)], spacing=8),
                    ft.Row([self.key_button("MODE", self.on_mode), self.key_button("MEM", self.on_mem)], spacing=8),
                    ft.Row([self.key_button("SYST", self.on_syst)], spacing=8),
                ],
                spacing=8,
            ),
        )
        select_keys = self.group(
            "SELECT",
            ft.Column(
                [
                    self.key_button("A/B", self.on_ab, width=92),
                    self.key_button("ENTER", self.on_enter, width=92),
                    self.key_button("ESC", self.on_esc, width=92),
                ],
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
        adjust_keys = self.group(
            "ADJUST",
            ft.Column(
                [
                    self.key_button("▲", self.on_up, width=52),
                    ft.Row(
                        [
                            self.key_button("◄", self.on_left, width=52),
                            self.key_button("►", self.on_right, width=52),
                        ],
                        spacing=8,
                    ),
                    self.key_button("▼", self.on_down, width=52),
                ],
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        remote_block = ft.Column(
            [
                ft.Text("REMOTE", size=10, color="#6a645c"),
                self.led("remote", "#d7a21a"),
                self.key_button("LOCAL", self.on_local, width=92),
            ],
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        out_block = ft.Column(
            [
                ft.Text("ON", size=10, color="#6a645c"),
                self.led("out", "#3ddc6a"),
                self.key_button("OUT A/B", self.on_out, width=92),
            ],
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        header = ft.Container(
            content=ft.Row(
                [
                    ft.Text("GRUNDIG", size=16, weight=ft.FontWeight.W_700, color="#2c3340"),
                    ft.Text("electronics", size=11, italic=True, color="#5c6470"),
                    ft.Container(expand=True),
                    ft.Text("PN 300", size=20, weight=ft.FontWeight.W_700, color="#2f3f86"),
                    ft.Text("PROGRAMMABLE POWER SUPPLY", size=13, color="#2f3f86"),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            bgcolor="#e7d7b4",
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
        )

        face = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [cv_block, lcd, status_leds, mode_leds, ft.Container(expand=True), sockets],
                        spacing=18,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Divider(height=1, color="#e4e0d6"),
                    ft.Row(
                        [
                            power,
                            set_keys,
                            select_keys,
                            adjust_keys,
                            ft.Container(expand=True),
                            remote_block,
                            out_block,
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.END,
                    ),
                ],
                spacing=12,
            ),
            bgcolor="#f3f1ea",
            padding=16,
        )

        shell = ft.Container(
            content=ft.Column(
                [
                    header,
                    face,
                    ft.Container(self.footer, padding=ft.padding.only(left=16, right=16, bottom=8)),
                ],
                spacing=0,
            ),
            bgcolor="#e7d7b4",
            border_radius=8,
            border=ft.border.all(1, "#c9b58a"),
            width=1040,
        )
        self.refresh()
        return shell

    def refresh(self) -> None:
        s = self.state
        if not s.mains:
            self.lcd_1.value = fit16("")
            self.lcd_2.value = fit16("")
            self.lcd_1.color = "#6d8450"
            self.lcd_2.color = "#6d8450"
        else:
            self.lcd_1.color = "#14200c"
            self.lcd_2.color = "#14200c"
            self.lcd_1.value = fit16(self._line1())
            self.lcd_2.value = fit16(self._line2())

        self.set_led("ind", s.mains and s.mode == "IND")
        self.set_led("track", s.mains and s.mode == "TRACK")
        self.set_led("par", s.mains and s.mode == "PAR")
        self.set_led("remote", s.mains and s.remote)
        self.set_led("out", s.mains and s.output_on)
        self.set_led("cv_a", s.mains and s.output_on and s.mode != "PAR")
        self.set_led("cv_b", s.mains and s.output_on)
        self.set_led("cc_a", False)
        self.set_led("cc_b", False)
        self.footer.value = self._footer()
        self.page.update()

    def _reading(self, volts: float, amps: float) -> str:
        return f"{volts:5.2f}V {amps:6.3f}A"

    def _line1(self) -> str:
        s = self.state
        if s.message:
            return s.message
        if s.edit == "V":
            return f"VOLTAGE_{s.channel}"
        if s.edit == "I":
            return f"CURRENT_{s.channel}"
        return self._reading(s.va, s.ia)

    def _line2(self) -> str:
        s = self.state
        if s.message:
            return ""
        if s.edit == "V":
            return f"  SET:[{s.draft:>7}]"
        if s.edit == "I":
            return f"  SET:[{s.draft:>7}]"
        return self._reading(s.vb, s.ib)

    def _footer(self) -> str:
        s = self.state
        link = "Remote" if s.remote else "Local"
        power = "Netz ein" if s.mains else "Netz aus"
        return f"{power}   ·   {link}   ·   Speicher {s.mem_slot:02d}   ·   Simulator, noch ohne RS-232"

    def toggle_mains(self, _e) -> None:
        self.state.mains = not self.state.mains
        if not self.state.mains:
            self.state.output_on = False
            self.state.edit = None
            self.state.message = ""
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
        order = ["IND", "TRACK", "PAR"]
        self.state.mode = order[(order.index(self.state.mode) + 1) % 3]
        self.state.edit = None
        self.state.message = ""
        if self.state.mode == "TRACK":
            self.state.vb = self.state.va
        self.refresh()

    def on_mem(self, _e) -> None:
        if not self.state.mains:
            return
        self.state.edit = None
        self.state.message = f"MEMORY {self.state.mem_slot:02d}"
        self.refresh()

    def on_syst(self, _e) -> None:
        if not self.state.mains:
            return
        self.state.edit = None
        self.state.message = "RS232 9600 8N1"
        self.refresh()

    def on_ab(self, _e) -> None:
        if not self.state.mains or self.state.mode == "PAR":
            return
        self.state.channel = "B" if self.state.channel == "A" else "A"
        self.state.message = ""
        if self.state.edit == "V":
            self.state.draft = f"{self.state.selected_v():5.2f}"
        elif self.state.edit == "I":
            self.state.draft = f"{self.state.selected_i():5.3f}"
        self.refresh()

    def on_enter(self, _e) -> None:
        if not self.state.mains:
            return
        s = self.state
        if s.message.startswith("MEMORY"):
            s.memories[s.mem_slot] = (s.va, s.ia, s.vb, s.ib, s.mode)
            s.message = f"SAVED  {s.mem_slot:02d}"
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
        else:
            value = min(max(value, 0.001), s.i_limit())
            if s.channel == "A" or s.mode == "PAR":
                s.ia = value
            if s.channel == "B" or s.mode == "PAR":
                s.ib = value
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
        if self.state.message.startswith("MEMORY"):
            self.state.mem_slot = 1 if self.state.mem_slot == 8 else self.state.mem_slot + 1
            self.state.message = f"MEMORY {self.state.mem_slot:02d}"
            self.refresh()
            return
        self._nudge(1)

    def on_down(self, _e) -> None:
        if self.state.message.startswith("MEMORY"):
            self.state.mem_slot = 8 if self.state.mem_slot == 1 else self.state.mem_slot - 1
            self.state.message = f"MEMORY {self.state.mem_slot:02d}"
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
        self.state.remote = not self.state.remote
        self.refresh()

    def on_out(self, _e) -> None:
        if not self.state.mains:
            return
        self.state.output_on = not self.state.output_on
        self.state.message = ""
        self.refresh()


def main(page: ft.Page) -> None:
    page.title = "Digimess PN 300"
    page.window_width = 1100
    page.window_height = 560
    page.window_min_width = 1100
    page.window_min_height = 560
    page.padding = 18
    page.bgcolor = "#d9d3c6"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.fonts = {"Consolas": "Consolas"}
    panel = PN300Panel(page)
    page.add(panel.build())


if __name__ == "__main__":
    ft.app(target=main)
