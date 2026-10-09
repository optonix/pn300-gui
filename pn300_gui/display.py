"""Zwei Zeilen des PN-300-Displays, je 16 Zeichen."""

LCD_COLS = 16


def fit16(text: str) -> str:
    return text[:LCD_COLS].ljust(LCD_COLS)


def reading(volts: float, amps: float) -> str:
    return f"{volts:5.2f}V {amps:6.3f}A"
