import importlib
import pathlib
import sys
import types
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))


class FakeSBC:
    instances = []

    def __init__(self, host="localhost", port=8889):
        self.host = host
        self.port = port
        self.connected = True
        self.calls = []
        FakeSBC.instances.append(self)

    def gpiochip_open(self, gpiochip):
        self.calls.append(("gpiochip_open", gpiochip))
        return 100

    def gpiochip_close(self, handle):
        self.calls.append(("gpiochip_close", handle))
        return 0

    def gpio_claim_output(self, handle, gpio, level=0, lFlags=0):
        self.calls.append(("gpio_claim_output", handle, gpio, level, lFlags))
        return 0

    def gpio_free(self, handle, gpio):
        self.calls.append(("gpio_free", handle, gpio))
        return 0

    def gpio_write(self, handle, gpio, level):
        self.calls.append(("gpio_write", handle, gpio, level))
        return 0

    def tx_pwm(self, handle, gpio, frequency, duty_cycle):
        self.calls.append(("tx_pwm", handle, gpio, frequency, duty_cycle))
        return 0

    def stop(self):
        self.calls.append(("stop",))


class DisconnectedSBC(FakeSBC):
    def __init__(self, host="localhost", port=8889):
        super().__init__(host=host, port=port)
        self.connected = False


def load_module_with(fake_sbc_class):
    FakeSBC.instances.clear()
    sys.modules.pop("dual_mc33926", None)
    sys.modules["rgpio"] = types.SimpleNamespace(sbc=fake_sbc_class)
    return importlib.import_module("dual_mc33926")


class MotorsTests(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop("dual_mc33926", None)
        sys.modules.pop("rgpio", None)

    def test_claims_outputs_for_both_motors(self):
        module = load_module_with(FakeSBC)

        with module.Motors() as motors:
            self.assertEqual(motors.motor1.pins.pwm, 12)
            self.assertEqual(motors.motor2.pins.pwm, 13)

        calls = FakeSBC.instances[0].calls
        claimed = [call[2] for call in calls if call[0] == "gpio_claim_output"]
        self.assertEqual(claimed, [12, 24, 22, 13, 25, 23])

    def test_set_speed_clamps_and_flips_direction(self):
        module = load_module_with(FakeSBC)

        with module.Motors() as motors:
            motors.motor1.set_speed(-150)

        calls = FakeSBC.instances[0].calls
        self.assertIn(("gpio_write", 100, 24, 1), calls)
        self.assertIn(("tx_pwm", 100, 12, module.DEFAULT_PWM_FREQUENCY, 100.0), calls)

    def test_zero_speed_stops_pwm(self):
        module = load_module_with(FakeSBC)

        with module.Motors() as motors:
            motors.motor2.set_speed(0)

        calls = FakeSBC.instances[0].calls
        self.assertIn(("gpio_write", 100, 25, 0), calls)
        self.assertIn(("tx_pwm", 100, 13, 0, 0), calls)

    def test_requires_rgpiod_connection(self):
        module = load_module_with(DisconnectedSBC)

        with self.assertRaisesRegex(RuntimeError, "Could not connect to rgpiod"):
            module.Motors()


if __name__ == "__main__":
    unittest.main()
