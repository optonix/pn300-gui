import flet as ft
from pn300_simulator import PN300State
import time
import threading

class PN300GUI:
    def __init__(self, page: ft.Page):
        self.page = page
        self.state = PN300State()
        self.build_interface()

    def build_interface(self):
        self.page.title = "Digimess PN 300 - Simulator"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = "#0a0a0a"
        self.page.padding = 20
        self.page.window_width = 820
        self.page.window_height = 680

        # === DISPLAY ===
        self.display_line1 = ft.Text("", size=22, color="#00ff00", font_family="Courier New", weight=ft.FontWeight.BOLD)
        self.display_line2 = ft.Text("", size=22, color="#00ff00", font_family="Courier New", weight=ft.FontWeight.BOLD)

        self.display = ft.Container(
            content=ft.Column([self.display_line1, self.display_line2], spacing=2),
            bgcolor="#000000",
            border=ft.border.all(4, "#00cc00"),
            padding=20,
            width=580,
            height=110,
            border_radius=4
        )

        # === LEDs ===
        self.led_a_cv = ft.Text("A CV", color="green", size=14, weight="bold")
        self.led_b_cv = ft.Text("B CV", color="green", size=14, weight="bold")
        self.led_ind = ft.Text("IND", color="yellow", size=14, weight="bold")
        self.led_track = ft.Text("TRACK", color="yellow", size=14, weight="bold")
        self.led_par = ft.Text("PAR", color="yellow", size=14, weight="bold")
        self.led_remote = ft.Text("REMOTE", color="red", visible=False)

        leds = ft.Row([self.led_a_cv, self.led_b_cv, self.led_ind, self.led_track, self.led_par, self.led_remote], spacing=15)

        # === BUTTONS ===
        def make_btn(text, width=65, color=None, on_click=None):
            return ft.ElevatedButton(
                text, width=width, height=50,
                bgcolor=color,
                on_click=on_click,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4))
            )

        def btn_v(e): self.set_mode("V")
        def btn_i(e): self.set_mode("I")
        def btn_mode(e): self.show_mode_menu()
        def btn_mem(e): self.show_mem_menu()
        def btn_enter(e): self.enter_value()
        def btn_esc(e): self.cancel_edit()
        def btn_out(e): self.toggle_output()
        def btn_local(e): self.state.remote = not self.state.remote; self.update_ui()

        def select_channel(e, ch):
            self.state.selected_channel = ch
            self.update_ui()

        buttons = ft.GridView(
            controls=[
                make_btn("V", on_click=btn_v),
                make_btn("I", on_click=btn_i),
                make_btn("MODE", width=85, on_click=btn_mode),
                make_btn("MEM", width=85, on_click=btn_mem),
                make_btn("↑", on_click=lambda e: self.cursor_up()),
                make_btn("A/B", on_click=lambda e: select_channel(e, "B" if self.state.selected_channel == "A" else "A")),
                make_btn("ENTER", width=85, color="#00aa00", on_click=btn_enter),
                make_btn("ESC", width=85, on_click=btn_esc),
                make_btn("←", width=50),
                make_btn("→", width=50),
                make_btn("↓", width=50),
                make_btn("LOCAL", width=85, on_click=btn_local),
                make_btn("OUT A/B", width=120, color="#00ff88", on_click=btn_out),
            ],
            runs_count=4,
            spacing=8,
            max_extent=90,
            height=280
        )

        # Layout
        self.page.add(
            ft.Column([
                ft.Text("DIGIMESS PN 300 PROGRAMMABLE POWER SUPPLY", size=26, weight="bold", color="#ffffff"),
                self.display,
                leds,
                buttons
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=25)
        )

        self.update_ui()

    def update_ui(self):
        ch = self.state.selected_channel
        v = self.state.voltage_a if ch == "A" else self.state.voltage_b
        i = self.state.current_a if ch == "A" else self.state.current_b
        status = self.state.cv_cc_a if ch == "A" else self.state.cv_cc_b

        self.display_line1.value = f"   {v:5.2f} V     {i:6.3f} A    {status}"
        self.display_line2.value = f"   {'B' if ch=='B' else 'A'}   {'ON' if self.state.output_on else 'OFF'}   {self.state.mode} MODE"
        
        # LED Updates
        self.led_ind.visible = self.state.mode == "IND"
        self.led_track.visible = self.state.mode == "TRAC"
        self.led_par.visible = self.state.mode == "PAR"
        self.led_remote.visible = self.state.remote

        self.page.update()

    def set_mode(self, mode):
        print(f"Setting {mode} mode - Implement number input here")
        self.update_ui()

    def show_mode_menu(self):
        print("Mode menu: IND / TRAC / PAR")
        # Hier könnte ein Dialog kommen
        self.state.mode = "PAR" if self.state.mode != "PAR" else "IND"
        self.update_ui()

    def show_mem_menu(self):
        print("Memory: Save / Recall")
        self.update_ui()

    def enter_value(self):
        print("ENTER gedrückt")
        self.update_ui()

    def cancel_edit(self):
        print("ESC gedrückt")
        self.update_ui()

    def toggle_output(self):
        self.state.output_on = not self.state.output_on
        self.update_ui()

    def cursor_up(self):
        if self.state.selected_channel == "A":
            self.state.voltage_a = min(30.0, self.state.voltage_a + 0.1)
        else:
            self.state.voltage_b = min(30.0, self.state.voltage_b + 0.1)
        self.update_ui()

# === START ===
def main(page: ft.Page):
    PN300GUI(page)

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8550)
