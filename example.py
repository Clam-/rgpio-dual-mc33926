from __future__ import print_function
import time
from dual_mc33926 import MAX_SPEED, Motors

# Set up sequences of motor speeds.
test_forward_speeds = list(range(0, int(MAX_SPEED), 1)) + \
  [MAX_SPEED] * 200 + list(range(int(MAX_SPEED), 0, -1)) + [0]

test_reverse_speeds = list(range(0, -int(MAX_SPEED), -1)) + \
  [-MAX_SPEED] * 200 + list(range(-int(MAX_SPEED), 0, 1)) + [0]

with Motors() as motors:
    motors.enable()
    motors.set_speeds(0, 0)

    print("\nMotor 1 forward: ")
    for s in test_forward_speeds:
        motors.motor1.set_speed(s)
        print(f"\r{s}", end="")
        time.sleep(0.01)

    print("\nMotor 1 reverse: ")
    for s in test_reverse_speeds:
        motors.motor1.set_speed(s)
        print(f"\r{s}", end="")
        time.sleep(0.01)

    print("\nMotor 2 forward: ")
    for s in test_forward_speeds:
        motors.motor2.set_speed(s)
        print(f"\r{s}", end="")
        time.sleep(0.01)

    print("\nMotor 2 reverse: ")
    for s in test_reverse_speeds:
        motors.motor2.set_speed(s)
        print(f"\r{s}", end="")
        time.sleep(0.01)
