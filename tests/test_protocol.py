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

    def test_output_commands(self) -> None:
        self.assertEqual(protocol.output_on(), "OUT_ON")
        self.assertEqual(protocol.output_off(), "OUT_OFF")
        self.assertEqual(protocol.output_query(), "OUT?")
        self.assertTrue(protocol.parse_output("OUT_ON"))
        self.assertFalse(protocol.parse_output("OUT_OFF"))
        self.assertIsNone(protocol.parse_output("ERR"))
        self.assertEqual(protocol.join_commands("SEL_A", "VSET 10.00", "ISET 0.100"), "SEL_A;VSET 10.00;ISET 0.100")
        self.assertEqual(protocol.save_preset(1), "*SAV 1")
        self.assertEqual(protocol.recall_preset(0), "*RCL 0")
        self.assertEqual(protocol.REN, "\t")
        self.assertEqual(protocol.GTL, "\x01")


if __name__ == "__main__":
    unittest.main()
