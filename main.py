import flet as ft
from pn300_simulator import PN300State

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
        self.page.window_width = 850
        self.page.window_height = 720

        # Display
        self.display_line1 = ft.Text("", size=22, color="#00ff41", font_family="Courier New", weight=ft.FontWeight.BOLD)
        self.display_line2 = ft.Text("", size=20, color="#00ff41", font_family="Courier New")

        self.display = ft.Container(
            content=ft.Column([self.display_line1, self.display_line2], spacing=4),
            bgcolor="#000000",
            border=ft.border.all(5, "#00cc00"),
            padding=25,
            width=620,
            height=130,
            border_radius=8
        )

        # LEDs
        self.led_ind = ft.Text("IND", color="#ffff00", size=15, weight="bold", visible=True)
        self.led_track = ft.Text("TRACK", color="#ffff00", size=15, weight="bold", visible=False)
        self.led_par = ft.Text("PAR", color="#ffff00", size=15, weight="bold", visible=False)
        self.led_remote = ft.Text("REMOTE", color="red", size=15, weight="bold", visible=False)

        leds_row = ft.Row([self.led_ind, self.led_track, self.led_par, self.led_remote], spacing=20)

        # Buttons
        def make_btn(text, width=70, color=None, on_click=None):
            return ft.ElevatedButton(text, width=width, height=55, bgcolor=color, on_click=on_click)

        buttons = ft.GridView(
            controls=[
                make_btn("V", on_click=lambda e: self.set_mode("V")),
                make_btn("I", on_click=lambda e: self.set_mode("I")),
                make_btn("MODE", width=90, on_click=lambda e: self.show_mode_menu()),
                make_btn("MEM", width=90, on_click=lambda e: self.show_mem_menu()),
                make_btn("↑", on_click=lambda e: self.cursor_up()),
                make_btn("A/B", on_click=lambda e: self.toggle_channel()),
                make_btn("ENTER", width=90, bgcolor="#00cc00"),
                make_btn("ESC", width=90),
                make_btn("←"), make_btn("→"), make_btn("↓"),
                make_btn("LOCAL", on_click=lambda e: self.toggle_remote()),
                make_btn("OUT A/B", width=130, bgcolor="#00ff88", on_click=lambda e: self.toggle_output()),
            ],
            runs_count=4,
            spacing=10,
            max_extent=90,
            height=300
        )

        self.page.add(
            ft.Column([
                ft.Text("DIGIMESS PN 300", size=28, weight="bold"),
                self.display,
                leds_row,
                buttons
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)
        )

        self.update_ui()

    def update_ui(self):
        ch = self.state.selected_channel
        v = self.state.voltage_a if ch == "A" else self.state.voltage_b
        i = self.state.current_a if ch == "A" else self.state.current_b
        status = self.state.cv_cc_a if ch == "A" else self.state.cv_cc_b

        self.display_line1.value = f"   {v:5.2f}V    {i:6.3f}A   {status}"
        self.display_line2.value = f"   Channel {ch}   {'ON ' if self.state.output_on else 'OFF'}   {self.state.mode} MODE"

        self.led_ind.visible = self.state.mode == "IND"
        self.led_track.visible = self.state.mode == "TRAC"
        self.led_par.visible = self.state.mode == "PAR"
        self.led_remote.visible = self.state.remote

        self.page.update()

    def toggle_channel(self):
        self.state.selected_channel = "B" if self.state.selected_channel == "A" else "A"
        self.update_ui()

    def toggle_output(self):
        self.state.output_on = not self.state.output_on
        self.update_ui()

    def toggle_remote(self):
        self.state.remote = not self.state.remote
        self.update_ui()

    def cursor_up(self):
        if self.state.selected_channel == "A":
            self.state.voltage_a = min(30.0, self.state.voltage_a + 0.1)
        else:
            self.state.voltage_b = min(30.0, self.state.voltage_b + 0.1)
        self.update_ui()

    def set_mode(self, m):
        print(f"Mode {m} selected - Number input coming soon")
        self.update_ui()

    def show_mode_menu(self):
        self.state.mode = "PAR" if self.state.mode == "IND" else "IND"
        self.update_ui()

    def show_mem_menu(self):
        print("Memory function")
        self.update_ui()

if __name__ == "__main__":
    ft.app(target=PN300GUI, view=ft.AppView.WEB_BROWSER, port=8501)
