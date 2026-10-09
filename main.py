"""Startet nur das Fenster."""

from __future__ import annotations

import flet as ft

from pn300.device import Device
from pn300_gui.panel import PN300Panel


def main(page: ft.Page) -> None:
    page.title = "Digimess PN 300"
    page.window_width = 1100
    page.window_height = 600
    page.window_min_width = 1100
    page.window_min_height = 600
    page.padding = 18
    page.bgcolor = "#d9d3c6"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.add(PN300Panel(page, Device()).build())


if __name__ == "__main__":
    ft.app(target=main)
