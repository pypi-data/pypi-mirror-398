from RPi import GPIO  # type: ignore
import threading

from bluer_ugv.logger import logger


class ClassicalLeds:
    def __init__(self):
        self._leds = {
            "yellow": {"pin": 17, "state": True},
            "red": {"pin": 27, "state": False},
            "green": {"pin": 22, "state": True},
        }

        self._lock = threading.Lock()

        logger.info(
            "{}: {}.".format(
                self.__class__.__name__,
                ", ".join(
                    [
                        "{}:GPIO#{}".format(
                            led_name,
                            led_info["pin"],
                        )
                        for led_name, led_info in self._leds.items()
                    ]
                ),
            )
        )

    def flash(self, color: str):
        with self._lock:
            self._leds[color]["state"] = not self._leds[color]["state"]

    def flash_all(self):
        with self._lock:
            for led in self._leds.values():
                led["state"] = not led["state"]

    def initialize(self) -> bool:
        try:
            for led in self._leds.values():
                GPIO.setup(
                    led["pin"],
                    GPIO.OUT,
                )
        except Exception as e:
            logger.error(e)
            return False

        return True

    def get(self, color: str) -> bool:
        with self._lock:
            return self._leds[color]["state"]

    def set(self, color: str, value: bool):
        with self._lock:
            self._leds[color]["state"] = value

    def set_all(
        self,
        state: bool = True,
    ) -> bool:
        with self._lock:
            for led in self._leds.values():
                led["state"] = state

        return self.update(flash_green=False)

    def update(
        self,
        flash_green: bool = True,
    ) -> bool:
        with self._lock:
            if flash_green:
                self._leds["green"]["state"] = not self._leds["green"]["state"]

            for led in self._leds.values():
                GPIO.output(
                    led["pin"],
                    GPIO.HIGH if led["state"] else GPIO.LOW,
                )

        return True
