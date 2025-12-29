from blueness import module

from bluer_ugv import NAME
from bluer_ugv.swallow.session.classical.ultrasonic_sensor.log import (
    UltrasonicSensorDetectionLog,
)
from bluer_ugv.logger import logger


NAME = module.name(__file__, NAME)


def review(
    object_name: str,
    export_gif: bool = False,
    frame_count: int = -1,
    log: bool = True,
    rm_blank: bool = True,
) -> bool:
    logger.info(
        "{}.review{}: {}".format(
            NAME,
            f" [{frame_count} frame(s)]" if frame_count == -1 else "",
            object_name,
        )
    )

    detection_log = UltrasonicSensorDetectionLog()

    if not detection_log.load(
        object_name=object_name,
    ):
        return False

    if not detection_log.export(
        object_name=object_name,
        line_width=80,
        export_gif=export_gif,
        frame_count=frame_count,
        log=log,
        rm_blank=rm_blank,
    ):
        return False

    return True
