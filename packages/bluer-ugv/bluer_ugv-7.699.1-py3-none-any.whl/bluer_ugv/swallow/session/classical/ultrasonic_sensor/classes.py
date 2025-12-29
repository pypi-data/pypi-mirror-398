import threading
import time

from bluer_objects.env import abcli_object_name

from bluer_ugv import env
from bluer_ugv.swallow.session.classical.ultrasonic_sensor.pack import (
    UltrasonicSensorPack,
)
from bluer_ugv.swallow.session.classical.ultrasonic_sensor.detection import (
    DetectionState,
)
from bluer_ugv.swallow.session.classical.ultrasonic_sensor.detection_list import (
    DetectionList,
)
from bluer_ugv.swallow.session.classical.ultrasonic_sensor.log import (
    UltrasonicSensorDetectionLog,
)
from bluer_ugv.swallow.session.classical.keyboard.classes import ClassicalKeyboard
from bluer_ugv.swallow.session.classical.setpoint.classes import ClassicalSetPoint
from bluer_ugv.logger import logger


class ClassicalUltrasonicSensor:
    def __init__(
        self,
        setpoint: ClassicalSetPoint,
        keyboard: ClassicalKeyboard,
    ):
        self.enabled = env.BLUER_UGV_ULTRASONIC_SENSOR_ENABLED == 1
        logger.info(
            "{}: {}".format(
                self.__class__.__name__,
                (
                    "enabled: warning<{:.2f} mm, danger<{:.2f} mm".format(
                        env.BLUER_UGV_ULTRASONIC_SENSOR_WARNING_THRESHOLD,
                        env.BLUER_UGV_ULTRASONIC_SENSOR_DANGER_THRESHOLD,
                    )
                    if self.enabled
                    else "disabled"
                ),
            )
        )

        self.setpoint = setpoint
        self.keyboard = keyboard

        self.detection_list = DetectionList()

        self.pack = None
        self.log = None
        self.running = False

        if not self.enabled:
            return

        self.pack = UltrasonicSensorPack(
            setmode=False,
            max_m=env.BLUER_UGV_ULTRASONIC_SENSOR_MAX_M,
        )

        if not self.pack.valid:
            raise NameError("valid ultrasonic sensor pack.")

        if env.BLUER_UGV_ULTRASONIC_SENSOR_KEEP_LOG == 1:
            self.log = UltrasonicSensorDetectionLog()

        self.running = True
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    def stop(self):
        if not self.enabled:
            return

        self.running = False
        self.thread.join()

        logger.info(f"{self.__class__.__name__}.stopped.")

        if self.log is not None:
            self.log.save(object_name=abcli_object_name)
            self.log.export(object_name=abcli_object_name)

    def loop(self):
        logger.info(f"{self.__class__.__name__}.loop started.")

        while self.running:
            if not self.keyboard.get("ultrasound_enabled", True):
                time.sleep(0.01)
                continue

            success, self.detection_list = self.pack.detect(
                log=env.BLUER_UGV_ULTRASONIC_SENSOR_LOG == 1,
            )
            if not success:
                raise NameError("failed to detect ultrasonic sensor.")

            if self.log is not None:
                self.log.append(self.detection_list)

            log_detections: bool = False
            speed = self.setpoint.get(what="speed")
            if self.detection_list.state == DetectionState.DANGER:
                self.setpoint.stop()
                log_detections = True
                logger.info("⛔️ danger detected, stopping.")
            elif self.detection_list.state == DetectionState.WARNING and speed > 0:
                self.setpoint.put(
                    what="speed",
                    value=speed // 2,
                )
                log_detections = True
                logger.info("⚠️ warning detected, lowering speed.")

            if env.BLUER_UGV_ULTRASONIC_SENSOR_LOG == 1:
                log_detections = False

            if log_detections:
                logger.info(
                    "{}: {}".format(
                        self.__class__.__name__,
                        ", ".join(self.detection_list.as_str(short=True)),
                    )
                )
