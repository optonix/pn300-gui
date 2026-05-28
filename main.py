import flet as ft
from pn300_simulator import PN300State
from pn300_device import PN300Device

class PN300GUI:
    def __init__(self, page: ft.Page):
        self.page = page
        self.state = PN300State()
        self.device = PN300Device(port="COM3")
        self.use_real_device = False
        self.current_edit = None
        self.build_interface()

    def build_interface(self):
        self.page.title = "Digimess PN 300 - Control"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = "#0a0a0a"
        self.page.padding = 30
        self.page.window_width = 920
        self.page.window_height = 740

        # Display
        self.display_line1 = ft.Text("", size=26, color="#00ff41", font_family="Courier New", weight=ft.FontWeight.BOLD)
        self.display_line2 = ft.Text("", size=22, color="#00ff41", font_family="Courier New")

        self.display = ft.Container(
            content=ft.Column([self.display_line1, self.display_line2], spacing=8),
            bgcolor="#000000",
            border=ft.border.Border(
                left=ft.border.BorderSide(6, "#00cc00"),
                top=ft.border.BorderSide(6, "#00cc00"),
                right=ft.border.BorderSide(6, "#00cc00"),
                bottom=ft.border.BorderSide(6, "#00cc00")
            ),
            padding=35,
            width=680,
            height=155,
            border_radius=10,
        )

        # LEDs
        self.leds = {
            "ind": ft.Text("IND", color="#ffff00", size=17, weight="bold"),
            "track": ft.Text("TRACK", color="#ffff00", size=17, weight="bold", visible=False),
            "par": ft.Text("PAR", color="#ffff00", size=17, weight="bold", visible=False),
            "remote": ft.Text("REMOTE", color="#ff3333", size=17, weight="bold", visible=False),
        }
        led_row = ft.Row(list(self.leds.values()), spacing=30)

        # Buttons - Korrigierte Syntax
        def make_btn(text, width=75, color=None, on_click=None):
            return ft.ElevatedButton(
                text=text,          # explizit 'text'
                width=width, 
                height=62, 
                bgcolor=color, 
                on_click=on_click
            )

        buttons = ft.GridView(
            controls=[
                make_btn("V", on_click=lambda e: self.start_edit("V")),
                make_btn("I", on_click=lambda e: self.start_edit("I")),
                make_btn("MODE", width=100, on_click=lambda e: self.show_mode_menu()),
                make_btn("MEM", width=100, on_click=lambda e: self.show_mem_menu()),
                make_btn("↑", on_click=lambda e: self.cursor_up()),
                make_btn("A/B", on_click=lambda e: self.toggle_channel()),
                make_btn("ENTER", width=100, bgcolor="#00cc00", on_click=lambda e: self.enter_value()),
                make_btn("ESC", width=100, on_click=lambda e: self.cancel_edit()),
                make_btn("←", width=60), 
                make_btn("→", width=60), 
                make_btn("↓", width=60),
                make_btn("LOCAL", width=100, on_click=lambda e: self.toggle_remote()),
                make_btn("OUT A/B", width=150, bgcolor="#00ff88", on_click=lambda e: self.toggle_output()),
            ],
            runs_count=4,
            spacing=10,
            max_extent=100,
            height=340
        )

        self.page.add(
            ft.Column([
                ft.Text("DIGIMESS PN 300", size=32, weight="bold", color="white"),
                self.display,
                led_row,
                buttons
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=30)
        )

        self.update_ui()

    def update_ui(self):
        v, i, status = self.state.get_display_values()
        ch = self.state.selected_channel
        self.display_line1.value = f"   {v:5.2f} V     {i:6.3f} A    {status}"
        self.display_line2.value = f"   Channel {ch}     {'ON ' if self.state.output_on else 'OFF'}     {self.state.mode}"

        self.leds["ind"].visible = self.state.mode == "IND"
        self.leds["track"].visible = self.state.mode == "TRAC"
        self.leds["par"].visible = self.state.mode == "PAR"
        self.leds["remote"].visible = self.state.remote

        self.page.update()

    # Rest der Methoden (vereinfacht)
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
            self.state.voltage_a = min(30.0, round(self.state.voltage_a + 0.1, 2))
        else:
            self.state.voltage_b = min(30.0, round(self.state.voltage_b + 0.1, 2))
        self.update_ui()

    def start_edit(self, mode):
        self.current_edit = mode
        self.show_number_input(mode)

    def show_number_input(self, mode):
        print(f"Dialog für {mode} geöffnet (noch vereinfacht)")

    def show_mode_menu(self):
        modes = ["IND", "TRAC", "PAR"]
        idx = modes.index(self.state.mode)
        self.state.mode = modes[(idx + 1) % 3]
        self.update_ui()

    def show_mem_menu(self):
        print("Memory Menu")

if __name__ == "__main__":
    ft.app(target=PN300GUI, view=ft.AppView.WEB_BROWSER, port=8501)
