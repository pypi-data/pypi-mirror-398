# continues /sandbox/ultrasonic_sensor-v7.py

from bluer_ugv import env
from bluer_ugv.logger import logger
from bluer_ugv.swallow.session.classical.ultrasonic_sensor.log import (
    UltrasonicSensorDetectionLog,
)


def test(
    object_name: str,
    export: bool = True,
    export_gif: bool = False,
    frame_count: int = -1,
    line_width: int = 80,
    log: bool = True,
    max_m: float = env.BLUER_UGV_ULTRASONIC_SENSOR_MAX_M,
    rm_blank: bool = True,
) -> bool:
    from RPi import GPIO

    from bluer_ugv.swallow.session.classical.ultrasonic_sensor.pack import (
        UltrasonicSensorPack,
    )

    ultrasonic_sensor_pack = UltrasonicSensorPack(max_m=max_m)
    if not ultrasonic_sensor_pack.valid:
        return False

    detection_log = UltrasonicSensorDetectionLog()

    success = True
    try:
        while True:
            success, detection_list = ultrasonic_sensor_pack.detect(log=log)
            if not success:
                break

            if export:
                detection_log.append(detection_list)
    except KeyboardInterrupt:
        logger.info("^C detected.")
    finally:
        GPIO.cleanup()

    if not export:
        return success

    if not success:
        return success

    if not detection_log.export(
        object_name=object_name,
        export_gif=export_gif,
        frame_count=frame_count,
        line_width=line_width,
        log=log,
        rm_blank=rm_blank,
    ):
        return False

    return detection_log.save(object_name=object_name)
