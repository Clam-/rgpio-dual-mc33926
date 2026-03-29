from __future__ import annotations

from dataclasses import dataclass

import rgpio

MAX_SPEED = 100.0
DEFAULT_PWM_FREQUENCY = 10000
DEFAULT_GPIOCHIP = 0


@dataclass(frozen=True)
class MotorPins:
    pwm: int
    direction: int
    enable: int


DEFAULT_MOTOR1_PINS = MotorPins(pwm=12, direction=24, enable=22)
DEFAULT_MOTOR2_PINS = MotorPins(pwm=13, direction=25, enable=23)


def _check_status(operation: str, status: int) -> int:
    if status < 0:
        raise RuntimeError(f"{operation} failed with status {status}")
    return status


class Motor:
    def __init__(
        self,
        sbc: rgpio.sbc,
        gpiochip_handle: int,
        pins: MotorPins,
        pwm_frequency: int,
    ) -> None:
        self._sbc = sbc
        self._gpiochip_handle = gpiochip_handle
        self.pins = pins
        self.pwm_frequency = pwm_frequency
        self._pwm_active = False

    def enable(self) -> None:
        _check_status(
            f"gpio_write(enable={self.pins.enable})",
            self._sbc.gpio_write(self._gpiochip_handle, self.pins.enable, 1),
        )

    def disable(self) -> None:
        _check_status(
            f"gpio_write(enable={self.pins.enable})",
            self._sbc.gpio_write(self._gpiochip_handle, self.pins.enable, 0),
        )

    def stop(self) -> None:
        if not self._pwm_active:
            return

        _check_status(
            f"tx_pwm(gpio={self.pins.pwm})",
            self._sbc.tx_pwm(self._gpiochip_handle, self.pins.pwm, 0, 0),
        )
        self._pwm_active = False

    def set_speed(self, speed: float) -> None:
        clamped_speed = max(-MAX_SPEED, min(MAX_SPEED, float(speed)))
        direction = 1 if clamped_speed < 0 else 0
        duty_cycle = abs(clamped_speed)

        _check_status(
            f"gpio_write(direction={self.pins.direction})",
            self._sbc.gpio_write(self._gpiochip_handle, self.pins.direction, direction),
        )

        if duty_cycle == 0:
            self.stop()
            return

        _check_status(
            f"tx_pwm(gpio={self.pins.pwm})",
            self._sbc.tx_pwm(
                self._gpiochip_handle,
                self.pins.pwm,
                self.pwm_frequency,
                duty_cycle,
            ),
        )
        self._pwm_active = True


class Motors:
    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        gpiochip: int = DEFAULT_GPIOCHIP,
        pwm_frequency: int = DEFAULT_PWM_FREQUENCY,
        motor1_pins: MotorPins = DEFAULT_MOTOR1_PINS,
        motor2_pins: MotorPins = DEFAULT_MOTOR2_PINS,
    ) -> None:
        sbc_kwargs = {}
        if host is not None:
            sbc_kwargs["host"] = host
        if port is not None:
            sbc_kwargs["port"] = port

        self._sbc = rgpio.sbc(**sbc_kwargs)
        self._claimed_gpios: list[int] = []
        self._gpiochip_handle: int | None = None
        self._closed = False

        if not self._sbc.connected:
            target = host or "localhost"
            target_port = port if port is not None else 8889
            raise RuntimeError(f"Could not connect to rgpiod at {target}:{target_port}")

        try:
            self._gpiochip_handle = _check_status(
                f"gpiochip_open({gpiochip})", self._sbc.gpiochip_open(gpiochip)
            )

            for gpio in (
                motor1_pins.pwm,
                motor1_pins.direction,
                motor1_pins.enable,
                motor2_pins.pwm,
                motor2_pins.direction,
                motor2_pins.enable,
            ):
                _check_status(
                    f"gpio_claim_output({gpio})",
                    self._sbc.gpio_claim_output(self._gpiochip_handle, gpio, 0),
                )
                self._claimed_gpios.append(gpio)

            self.motor1 = Motor(
                self._sbc, self._gpiochip_handle, motor1_pins, pwm_frequency
            )
            self.motor2 = Motor(
                self._sbc, self._gpiochip_handle, motor2_pins, pwm_frequency
            )
        except Exception:
            self.close()
            raise

    def __enter__(self) -> "Motors":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def enable(self) -> None:
        self.motor1.enable()
        self.motor2.enable()

    def disable(self) -> None:
        self.motor1.disable()
        self.motor2.disable()

    def stop(self) -> None:
        self.motor1.stop()
        self.motor2.stop()

    def set_speeds(self, motor1_speed: float, motor2_speed: float) -> None:
        self.motor1.set_speed(motor1_speed)
        self.motor2.set_speed(motor2_speed)

    def close(self) -> None:
        if self._closed:
            return

        self._closed = True

        errors = []

        try:
            if hasattr(self, "motor1") and hasattr(self, "motor2"):
                try:
                    self.stop()
                    self.disable()
                except RuntimeError as exc:
                    errors.append(exc)
        finally:
            if self._gpiochip_handle is not None:
                for gpio in reversed(self._claimed_gpios):
                    try:
                        _check_status(
                            f"gpio_free({gpio})",
                            self._sbc.gpio_free(self._gpiochip_handle, gpio),
                        )
                    except RuntimeError as exc:
                        errors.append(exc)

                try:
                    _check_status(
                        "gpiochip_close",
                        self._sbc.gpiochip_close(self._gpiochip_handle),
                    )
                except RuntimeError as exc:
                    errors.append(exc)

            self._sbc.stop()

        if errors:
            raise errors[0]


__all__ = [
    "DEFAULT_GPIOCHIP",
    "DEFAULT_MOTOR1_PINS",
    "DEFAULT_MOTOR2_PINS",
    "DEFAULT_PWM_FREQUENCY",
    "MAX_SPEED",
    "Motor",
    "MotorPins",
    "Motors",
]
