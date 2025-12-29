from RPi import GPIO
from typing import Tuple
import time

from bluer_ugv import env
from bluer_ugv.logger import logger
from bluer_ugv.swallow.session.classical.ultrasonic_sensor.consts import (
    C,
    CYCLE_MIN_S,
    WAIT_LOW_TIMEOUT_S,
    WAIT_HIGH_TIMEOUT_S,
    TRIG_PULSE_S,
)
from bluer_ugv.swallow.session.classical.ultrasonic_sensor.detection import Detection


def monotonic_s():
    return time.monotonic_ns() * 1e-9


class lUltrasonicSensor:
    def __init__(
        self,
        side: str,
        setmode: bool = True,
        max_m: float = env.BLUER_UGV_ULTRASONIC_SENSOR_MAX_M,
    ):
        self.side = side
        self.valid = True

        self.max_m = max_m
        self.THRESH_S = (2 * max_m) / C  # round-trip time threshold

        # Pin definitions
        if side == "left":
            self.TRIG = 23  # GPIO 23, pin 16
            self.ECHO = 24  # GPIO 24, pin 18
        elif side == "right":  # right
            self.TRIG = 5  # GPIO 5,  pin 29
            self.ECHO = 25  # GPIO 25, pin 22
        else:
            logger.error(f"{side}: ultrasonic sensor not found.")
            self.valid = False

        if not self.valid:
            return

        if setmode:
            GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.TRIG, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.ECHO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        logger.info(
            "{}: {} ultrasonic sensor initialized on TRIG=GPIO#{}, ECHO=GPIO#{} at max distance={:6.2f} mm == {:6.2} ms.".format(
                self.__class__.__name__,
                self.side,
                self.TRIG,
                self.ECHO,
                self.max_m * 1000,
                self.THRESH_S * 1000,
            )
        )

    def detect(
        self,
        log: bool = True,
    ) -> Tuple[bool, Detection]:
        if not self.valid:
            logger.error("invalid ultrasonic sensor")
            return False, Detection(
                side=self.side,
                reason="invalid sensor",
            )

        detection = Detection(side=self.side)

        cycle_start = monotonic_s()

        # Trigger pulse
        GPIO.output(self.TRIG, GPIO.LOW)
        time.sleep(200e-6)  # settle
        GPIO.output(self.TRIG, GPIO.HIGH)
        time.sleep(TRIG_PULSE_S)  # 30 µs
        GPIO.output(self.TRIG, GPIO.LOW)

        # Wait for rising edge
        t0 = monotonic_s()
        while GPIO.input(self.ECHO) == 0 and (monotonic_s() - t0) < WAIT_HIGH_TIMEOUT_S:
            pass
        if GPIO.input(self.ECHO) == 0:
            detection = Detection(
                side=self.side,
                detection=False,
                reason="no echo high",
            )
        else:
            t_rise = monotonic_s()

            # Wait for falling edge
            t_fall_deadline = t_rise + WAIT_LOW_TIMEOUT_S
            while GPIO.input(self.ECHO) == 1 and monotonic_s() < t_fall_deadline:
                pass

            if GPIO.input(self.ECHO) == 1:
                detection = Detection(
                    side=self.side,
                    detection=False,
                    reason="pulse timeout",
                )
            else:
                t_fall = monotonic_s()
                pulse_s = t_fall - t_rise
                pulse_ms = pulse_s * 1000
                distance_m = (pulse_s * C) / 2
                distance_mm = distance_m * 1000

                echo_detected = 0 < pulse_s < self.THRESH_S

                detection = Detection(
                    side=self.side,
                    detection=True,
                    echo_detected=echo_detected,
                    pulse_ms=pulse_ms,
                    distance_mm=distance_mm,
                )

        if log:
            logger.info(detection.as_str())

        # Keep cycle rate sane
        elapsed = monotonic_s() - cycle_start
        if elapsed < CYCLE_MIN_S:
            time.sleep(CYCLE_MIN_S - elapsed)

        return True, detection
