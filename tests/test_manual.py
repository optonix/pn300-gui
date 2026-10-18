import unittest

from pn300 import protocol
from pn300.device import Device
from pn300.errors import LCD_ALERTS
from pn300.face import Face, digit_places
from pn300.simulator import LOAD_BIT, Simulator


def running_face() -> Face:
    face = Face(Device())
    face.skip_boot()
    return face


class SimulatorManual(unittest.TestCase):
    def test_identity_and_reset_defaults(self) -> None:
        device = Device()
        self.assertEqual(device.identify(), "GRUNDIG,PN300,0,0")
        state = device.state
        self.assertEqual(state.va, 0.0)
        self.assertEqual(state.ia, 2.3)
        self.assertEqual(state.mode, "IND")
        self.assertEqual(state.cont_a, "CV")
        self.assertEqual(state.protection, "LIM")
        self.assertFalse(state.output_on)
        self.assertTrue(state.remote)

    def test_reset_restores_zero_volts(self) -> None:
        device = Device()
        device.set_voltage("A", 12.5)
        device.set_output(True)
        device.reset()
        self.assertEqual(device.state.va, 0.0)
        self.assertEqual(device.state.ia, 2.3)
        self.assertEqual(device.state.mode, "IND")
        self.assertFalse(device.state.output_on)

    def test_ren_drops_outputs_and_local_rejects_settings(self) -> None:
        device = Device()
        device.set_voltage("A", 5)
        device.set_output(True)
        self.assertTrue(device.state.output_on)
        device.enter_remote()
        self.assertFalse(device.state.output_on)
        device.set_local()
        device.set_voltage("A", 9)
        self.assertEqual(device.state.va, 5)
        self.assertIn("Local", device.state.error)
        self.assertEqual(device.identify(), "GRUNDIG,PN300,0,0")

    def test_parallel_current_floor(self) -> None:
        device = Device()
        device.set_current("A", 0.05)
        device.set_mode("PAR")
        self.assertEqual(device.state.mode, "PAR")
        self.assertEqual(device.state.ia, 0.3)
        self.assertEqual(device.state.ib, 0.3)
        device.set_current("A", 0.05)
        self.assertEqual(device.state.ia, 0.3)
        self.assertIn("Bereich", device.state.error)

    def test_limiting_switches_without_error_and_cutout_trips(self) -> None:
        device = Device()
        device.set_voltage("A", 5)
        device.set_current("A", 0.05)
        device.set_output(True)
        self.assertTrue(device.state.output_on)
        self.assertEqual(device.state.cont_a, "CC")
        self.assertEqual(device.state.error, "")
        self.assertIsNone(device.state.alert)

        device.set_output(False)
        device.set_function("CV")
        device.set_protection("CUT")
        device.set_output(True)
        self.assertFalse(device.state.output_on)
        self.assertEqual(device.state.alert, LCD_ALERTS[21])
        self.assertIn("Stromgrenze", device.state.error)

    def test_error_queue_keeps_two_codes_and_rejects_unknown(self) -> None:
        link = Simulator()
        link.state.remote = True
        link.send("NOPE;VSET 99;ALSO")
        self.assertEqual(link.send("ERR?"), "151")
        self.assertEqual(link.send("ERR?"), "134")
        self.assertEqual(link.send("ERR?"), "0")
        link.send("X" * 65)
        self.assertEqual(link.send("ERR?"), "181")
        self.assertEqual(link.send("*IDN?"), "GRUNDIG,PN300,0,0")

    def test_status_commands_and_empty_recall(self) -> None:
        link = Simulator()
        link.state.remote = True
        self.assertEqual(link.send("*TST?"), "0")
        self.assertEqual(link.send("*OPC?"), "1")
        link.send("*ESE 128")
        self.assertEqual(link.send("*ESE?"), "128")
        link.send("*SRE 32")
        self.assertEqual(link.send("*SRE?"), "32")
        self.assertEqual(link.send("*STB?"), "STB 96")
        self.assertTrue(link.send("*ESR?").startswith("ESR "))
        self.assertEqual(link.send("*ESR?"), "ESR 0")
        link.send("*WAI")
        link.send("*RCL 3")
        self.assertEqual(link.state.alert, LCD_ALERTS[96])
        self.assertEqual(link.der & LOAD_BIT, LOAD_BIT)
        self.assertEqual(link.send("ERR?"), "96")
        link.send("*SAV 6")
        self.assertEqual(link.send("ERR?"), "134")
        link.send("*CLS")
        self.assertEqual(link.errors, [])
        self.assertEqual(link.sre, 0)

    def test_save_roundtrip_keeps_mode(self) -> None:
        device = Device()
        device.set_voltage("A", 3.5)
        device.set_mode("TRACK")
        device.save(2)
        device.set_voltage("A", 1)
        device.set_mode("IND")
        device.recall(2)
        self.assertEqual(device.state.mode, "TRACK")
        self.assertEqual(device.state.va, 3.5)
        self.assertEqual(device.state.vb, 3.5)


class FaceManual(unittest.TestCase):
    def test_boot_then_readings(self) -> None:
        face = Face(Device())
        self.assertIn("CPU", face.lines()[0])
        self.assertIn("Passed", face.lines()[1])
        seen = [face.lines()[0].strip()]
        while face.advance_boot():
            seen.append(face.lines()[0].strip())
        self.assertEqual(face.phase, "run")
        self.assertIn("Testing: DISPLAY", seen)
        self.assertTrue(face.lines()[0].startswith("00.00V"))
        colors = face.led_colors()
        self.assertEqual(colors["remote"], "#e23b3b")
        self.assertEqual(colors["cv_a"], "#43c45a")
        self.assertEqual(colors["cc_a"], "#e23b3b")
        self.assertEqual(colors["ind"], "#43c45a")
        self.assertIsNone(colors["out"])

    def test_power_keeps_settings_and_sends_no_output_command(self) -> None:
        face = running_face()
        face.device.set_voltage("A", 8)
        sent = list(face.device._link.sent)
        face.press("power")
        self.assertFalse(face.state.mains)
        self.assertEqual(face.lines(), (" " * 16, " " * 16))
        self.assertEqual(face.device._link.sent, sent)
        self.assertFalse(face.state.output_on)
        face.press("power")
        self.assertEqual(face.phase, "boot")
        self.assertEqual(face.state.va, 8)
        self.assertFalse(face.state.output_on)

    def test_mode_menu_switches_cv_cc_once(self) -> None:
        face = running_face()
        face.press("mode")
        face.press("up")
        face.press("enter")
        self.assertIn("CV", face.lines()[1])
        face.press("up")
        self.assertIn("CC", face.lines()[1])
        face.press("enter")
        self.assertEqual(face.state.cont_a, "CC")
        colors = face.led_colors()
        self.assertEqual(colors["cv_a"], "#e23b3b")
        self.assertEqual(colors["cc_a"], "#43c45a")

    def test_parallel_from_menu_clamps_current(self) -> None:
        face = running_face()
        face.device.set_current("A", 0.05)
        face.press("mode")
        face.press("enter")
        face.press("up")
        face.press("up")
        face.press("enter")
        self.assertEqual(face.state.mode, "PAR")
        self.assertEqual(face.state.ia, 0.3)

    def test_indirect_edit_discards_on_escape_and_commits_on_enter(self) -> None:
        face = running_face()
        face.press("v")
        self.assertTrue(face.lines()[0].startswith("VOLTAGE_A"))
        self.assertIn("SET", face.lines()[1])
        places = digit_places(face.lines()[1], "V", False)
        self.assertEqual(len(places), 4)
        mark = face.cursor_mark()
        self.assertEqual(mark, (1, places[3]))
        face.press("up")
        self.assertAlmostEqual(face.edit["draft"], 0.01)
        self.assertEqual(face.state.va, 0.0)
        face.press("esc")
        self.assertIsNone(face.edit)
        self.assertEqual(face.state.va, 0.0)
        face.press("v")
        face.press("up")
        face.press("enter")
        self.assertAlmostEqual(face.state.va, 0.01)
        self.assertTrue(face.lines()[0].startswith("00.01V"))

    def test_direct_edit_is_live_and_escape_shows_measured(self) -> None:
        face = running_face()
        face.press("mode")
        face.press("up")
        face.press("up")
        face.press("enter")
        face.press("up")
        face.press("enter")
        self.assertEqual(face.state.adjustment, "DIRECT")
        face.press("out")
        self.assertTrue(face.state.output_on)
        self.assertTrue(face.edit["direct"])
        face.press("up")
        self.assertAlmostEqual(face.state.va, 0.01)
        face.press("esc")
        self.assertIsNone(face.edit)
        self.assertTrue(face.lines()[0].startswith("00.01V"))

    def test_local_does_not_enter_remote_and_lockout_blocks_it(self) -> None:
        face = running_face()
        face.press("local")
        self.assertFalse(face.state.remote)
        face.press("local")
        self.assertFalse(face.state.remote)
        face.device.enter_remote()
        face.state.lockout = True
        face.press("local")
        self.assertTrue(face.state.remote)

    def test_memory_store_and_failed_load(self) -> None:
        face = running_face()
        face.device.set_voltage("A", 4)
        face.press("mem")
        self.assertIn("STORE", face.lines()[1])
        face.press("enter")
        face.press("up")
        face.press("enter")
        self.assertTrue(face.lines()[0].startswith("Are you sure"))
        face.press("enter")
        self.assertIn(1, face.state.memories)
        face.press("mem")
        face.press("up")
        face.press("enter")
        face.press("up")
        face.press("up")
        face.press("enter")
        face.press("enter")
        self.assertEqual(face.state.alert, LCD_ALERTS[96])
        self.assertIn("Load failed", face.lines()[1])

    def test_system_baud_applies_on_confirm(self) -> None:
        face = running_face()
        face.press("syst")
        face.press("enter")
        face.press("enter")
        face.press("down")
        face.press("esc")
        self.assertEqual(face.state.baudrate, 9600)
        face.press("syst")
        face.press("enter")
        face.press("enter")
        face.press("down")
        face.press("enter")
        face.press("up")
        face.press("enter")
        self.assertEqual(face.state.baudrate, 4800)
        self.assertTrue(face.state.rtscts)
        self.assertIsNone(face.menu)

    def test_channel_switch_reloads_indirect_draft(self) -> None:
        face = running_face()
        face.device.set_voltage("B", 6)
        face.device._send(protocol.select_channel("A"))
        face.press("v")
        face.press("up")
        self.assertAlmostEqual(face.edit["draft"], 0.01)
        face.press("ab")
        self.assertEqual(face.state.channel, "B")
        self.assertAlmostEqual(face.edit["draft"], 6)
        self.assertEqual(face.state.va, 0.0)
        self.assertTrue(face.lines()[0].startswith("VOLTAGE_B"))

    def test_cutout_message_on_output(self) -> None:
        face = running_face()
        face.device.set_voltage("A", 5)
        face.device.set_current("A", 0.05)
        face.device.set_protection("CUT")
        face.press("out")
        self.assertFalse(face.state.output_on)
        self.assertEqual(face.lines()[0].strip(), "Error")
        self.assertIn("Exceeded I limit", face.lines()[1])


class ProtocolStillMatches(unittest.TestCase):
    def test_join_and_controls(self) -> None:
        self.assertEqual(protocol.REN, "\t")
        self.assertEqual(protocol.LLO, "\x19")
        self.assertEqual(protocol.join_commands("SEL_B", "VSET_MAX"), "SEL_B;VSET_MAX")


if __name__ == "__main__":
    unittest.main()
