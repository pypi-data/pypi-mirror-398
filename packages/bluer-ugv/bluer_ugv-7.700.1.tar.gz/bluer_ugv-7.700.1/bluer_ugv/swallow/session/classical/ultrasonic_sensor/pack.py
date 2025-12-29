from typing import List, Tuple

from bluer_ugv import env
from bluer_ugv.swallow.session.classical.ultrasonic_sensor.sensor import (
    lUltrasonicSensor,
)
from bluer_ugv.swallow.session.classical.ultrasonic_sensor.detection_list import (
    DetectionList,
)
from bluer_ugv.logger import logger


class UltrasonicSensorPack:
    def __init__(
        self,
        setmode: bool = True,
        max_m: float = env.BLUER_UGV_ULTRASONIC_SENSOR_MAX_M,
    ) -> None:
        self.left = lUltrasonicSensor(
            side="left",
            setmode=setmode,
            max_m=max_m,
        )
        self.right = lUltrasonicSensor(
            side="right",
            setmode=False,
            max_m=max_m,
        )

        self.valid = self.left.valid and self.right.valid

    def detect(
        self,
        log: bool = True,
    ) -> Tuple[bool, DetectionList]:
        success_left, detection_left = self.left.detect(log=False)
        success_right, detection_right = self.right.detect(log=False)

        if log:
            logger.info(
                " | ".join(
                    [
                        detection_left.as_str(),
                        detection_right.as_str(),
                    ]
                )
            )

        return (
            all(
                [
                    success_left,
                    success_right,
                ]
            ),
            DetectionList(
                [
                    detection_left,
                    detection_right,
                ],
            ),
        )
