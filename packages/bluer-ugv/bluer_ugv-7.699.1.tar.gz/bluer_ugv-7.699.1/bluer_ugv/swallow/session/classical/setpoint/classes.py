import threading
from typing import Union, Dict
import time

from bluer_options import string

from bluer_ugv.swallow.session.classical.leds import ClassicalLeds
from bluer_ugv.swallow.session.classical.setpoint.steering import (
    generate_left_and_right,
)
from bluer_ugv.logger import logger


class ClassicalSetPoint:
    def __init__(
        self,
        leds: ClassicalLeds,
    ):
        self.speed = 0
        self.steering = 0

        self.steering_expiry = time.time()

        self.started = False

        self.leds = leds

        self._lock = threading.Lock()

    def get(
        self,
        what: str = "all",
    ) -> Union[int, bool, Dict[str, Union[int, bool]]]:
        with self._lock:
            if what == "all":
                return {
                    "speed": self.speed,
                    "started": self.started,
                    "steering": self.steering,
                }

            if what == "left":
                return generate_left_and_right(self.speed, self.steering)[0]

            if what == "right":
                return generate_left_and_right(self.speed, self.steering)[1]

            if what == "speed":
                return self.speed

            if what == "started":
                return self.started

            if what == "steering":
                return self.steering

            logger.error(f"{self.__class__.__name__}.get: {what} not found.")
            return 0

    def check_steering_expiry(
        self,
        log: bool = True,
    ):
        with self._lock:
            if self.steering == 0:
                return

            if self.steering_expiry > time.time():
                if log:
                    logger.info(
                        "setpoint will expire in {}.".format(
                            string.pretty_duration(
                                self.steering_expiry - time.time(),
                                largest=True,
                                short=True,
                                include_ms=True,
                            )
                        )
                    )
                return

        if log:
            logger.info("setpoint expired.")

        self.put(
            what="steering",
            value=0,
        )

    def put(
        self,
        value: Union[int, bool, Dict[str, Union[int, bool]]],
        what: str = "all",
        log: bool = True,
        steering_expires_in: float = 0,
    ):
        with self._lock:
            if what == "all":
                self.speed = min(100, max(-100, int(value["speed"])))
                self.started = bool(value["started"])
                self.steering = min(100, max(-100, int(value["steering"])))
                self.steering_expiry = time.time() + steering_expires_in
                return

            if what == "speed":
                self.speed = min(100, max(-100, int(value)))
                if log:
                    logger.info(
                        "{}.put: speed={}".format(
                            self.__class__.__name__,
                            self.speed,
                        )
                    )
                return

            if what == "started":
                self.started = bool(value)
                if log:
                    logger.info(
                        "{}.put: {}".format(
                            self.__class__.__name__,
                            "started" if value else "stopped",
                        )
                    )
                return

            if what == "steering":
                self.steering = min(100, max(-100, int(value)))
                self.steering_expiry = time.time() + steering_expires_in
                if log:
                    logger.info(
                        "{}.put: steering={}, expires in {}".format(
                            self.__class__.__name__,
                            self.steering,
                            string.pretty_duration(
                                steering_expires_in,
                                largest=True,
                                short=True,
                                include_ms=True,
                            ),
                        )
                    )
                return

            logger.error(f"{self.__class__.__name__}.put: {what} not found.")

    def start(self):
        self.put(
            {
                "speed": 0,
                "started": True,
                "steering": 0,
            }
        )

        logger.info(f"{self.__class__.__name__}.start")

    def stop(self):
        self.put(
            {
                "speed": 0,
                "started": False,
                "steering": 0,
            }
        )

        logger.info(f"{self.__class__.__name__}.stop")

        self.leds.set("red", False)
        self.leds.set("yellow", False)

    def update(self) -> bool:
        with self._lock:
            if self.started:
                self.leds.flash("red")

        return True
