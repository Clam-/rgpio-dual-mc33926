This module is derived from:
https://github.com/pololu/dual-mc33926-motor-driver-rpi

It now targets `rgpio` rather than `pigpio`.

Setup:

* Install and start the `rgpiod` daemon on the target machine.
* Create a virtual environment, for example: `python3 -m venv ~/env`
* Install this package, which will also install the Python `rgpio` dependency:

```sh
git clone <this URL>
cd dual-mc33926
~/env/bin/pip install .
```

For editable installs:

```sh
~/env/bin/pip install -e .
```

Usage:

```python
from dual_mc33926 import MAX_SPEED, Motors

with Motors() as motors:
    motors.enable()
    motors.set_speeds(MAX_SPEED, MAX_SPEED / 2)
```

Notes:

* Speed is expressed as a percentage from `-100` to `100`.
* `rgpio` PWM uses duty-cycle percentages, so the old `0..1000000` pigpio scale is gone.
* This library defaults to `gpiochip0` and the original Pololu pin mapping.
* `rgpio` software PWM tops out below the old pigpio hardware-PWM setup, so this port uses a 10 kHz default PWM frequency.
