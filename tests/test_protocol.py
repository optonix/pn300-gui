import unittest

from pn300 import protocol
from pn300_gui.display import fit16, reading


class DisplayAndProtocol(unittest.TestCase):
    def test_reading_matches_front_panel(self) -> None:
        self.assertEqual(reading(30.0, 2.3), "30.00V  2.300A")
        self.assertEqual(len(fit16(reading(30.0, 2.3))), 16)

    def test_mode_commands(self) -> None:
        self.assertEqual(protocol.operating_mode("IND"), "OPER_IND")
        self.assertEqual(protocol.operating_mode("TRACK"), "OPER_TRAC")
        self.assertEqual(protocol.operating_mode("PAR"), "OPER_PAR")
        self.assertEqual(protocol.voltage_set(12.5), "VSET 12.50")
        self.assertEqual(protocol.current_set(1), "ISET 1.000")


if __name__ == "__main__":
    unittest.main()
