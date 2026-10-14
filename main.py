"""Startet nur das Fenster."""

from __future__ import annotations

import flet as ft

from pn300.device import Device
from pn300_gui.panel import PN300Panel


def main(page: ft.Page) -> None:
    page.title = "Digimess PN300 Remote Control v1.2"
    page.window_width = 1140
    page.window_height = 560
    page.window_min_width = 1140
    page.window_min_height = 560
    page.padding = 12
    page.bgcolor = "#2f6fbe"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.add(PN300Panel(page, Device()).build())


if __name__ == "__main__":
    ft.app(target=main)
