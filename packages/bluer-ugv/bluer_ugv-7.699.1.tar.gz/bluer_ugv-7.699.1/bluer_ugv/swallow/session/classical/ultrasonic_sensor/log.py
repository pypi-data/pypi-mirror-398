from typing import List
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from tqdm import tqdm
import numpy as np
import cv2

from bluer_objects.graphics.signature import justify_text
from bluer_objects import objects
from bluer_objects import file, path
from bluer_objects.graphics.gif import generate_animated_gif
from bluer_objects.graphics.signature import add_signature

from bluer_ugv import env
from bluer_ugv.swallow.session.classical.ultrasonic_sensor.detection import Detection
from bluer_ugv.swallow.session.classical.ultrasonic_sensor.detection_list import (
    DetectionList,
)
from bluer_ugv.host import signature
from bluer_ugv.logger import logger


class UltrasonicSensorDetectionLog:
    def __init__(self):
        self.log: List[DetectionList] = []

    def append(self, detection_list: DetectionList):
        self.log.append(detection_list)

    def export(
        self,
        object_name: str,
        export_gif: bool = False,
        frame_count: int = -1,
        line_width: int = 80,
        log: bool = True,
        rm_blank: bool = True,
        max_m: float = env.BLUER_UGV_ULTRASONIC_SENSOR_MAX_M,
    ) -> bool:
        for func, name, filename in zip(
            [
                lambda detection: int(detection.detection),
                lambda detection: int(detection.echo_detected),
                lambda detection: detection.pulse_ms,
                lambda detection: detection.distance_mm,
            ],
            [
                "detection",
                "echo detection",
                "pulse (ms)",
                "distance(mm)",
            ],
            [
                "ultrasonic-sensor-detection",
                "ultrasonic-sensor-echo-detection",
                "ultrasonic-sensor-pulse-ms",
                "ultrasonic-sensor-distance-mm",
            ],
        ):
            plt.figure(figsize=(10, 5))

            if "distance" in name:
                plt.plot(
                    [0, len(self.log) - 1],
                    2 * [env.BLUER_UGV_ULTRASONIC_SENSOR_WARNING_THRESHOLD],
                    color="yellow",
                    linestyle=":",
                    label="warning threshold",
                )
                plt.plot(
                    [0, len(self.log) - 1],
                    2 * [env.BLUER_UGV_ULTRASONIC_SENSOR_DANGER_THRESHOLD],
                    color="red",
                    linestyle=":",
                    label="danger threshold",
                )

            plt.plot(
                [func(detection_list[0]) for detection_list in self.log],
                color="green",
                label="left sensor",
            )
            plt.plot(
                [func(detection_list[1]) for detection_list in self.log],
                color="blue",
                label="right sensor",
            )

            plt.xlim([0, len(self.log) - 1])
            if "distance" in name:
                plt.ylim([0, max_m * 1000])

            plt.title(
                justify_text(
                    " | ".join(
                        [
                            "ultrasonic-sensor",
                            name,
                        ]
                        + objects.signature(object_name=object_name)
                    ),
                    line_width=line_width,
                    return_str=True,
                )
            )
            plt.xlabel(
                justify_text(
                    " | ".join(signature()),
                    line_width=line_width,
                    return_str=True,
                )
            )
            plt.ylabel(name)
            plt.legend()
            plt.tight_layout()
            plt.grid(True)
            if not file.save_fig(
                objects.path_of(
                    object_name=object_name,
                    filename=f"{filename}.png",
                ),
                log=log,
            ):
                return False

        if not self.export_state(
            object_name=object_name,
            line_width=line_width,
            log=log,
            max_m=max_m,
        ):
            return False

        if export_gif:
            if not self.export_gif(
                object_name=object_name,
                frame_count=frame_count,
                line_width=line_width,
                log=log,
                max_m=max_m,
                rm_blank=rm_blank,
            ):
                return False

        return True

    def export_state(
        self,
        object_name: str,
        line_width: int = 80,
        height=512,
        max_m: float = env.BLUER_UGV_ULTRASONIC_SENSOR_MAX_M,
        log: bool = True,
    ) -> bool:
        image = np.zeros((len(self.log[0]), len(self.log), 3), dtype=np.uint8)

        for detection_index, detection_list in enumerate(self.log):
            for sensor_index, detection in enumerate(detection_list):
                assert isinstance(detection, Detection)

                for channel in range(3):
                    image[sensor_index, detection_index, channel] = (
                        detection.state.color_code[channel]
                    )

        image = cv2.resize(
            image,
            (
                int(image.shape[1]),
                int(image.shape[0] * (height / image.shape[0])),
            ),
            interpolation=cv2.INTER_NEAREST_EXACT,
        )

        image = add_signature(
            image,
            header=[
                " | ".join(
                    [
                        "ultrasonic sensor state",
                    ]
                    + objects.signature(object_name=object_name)
                ),
            ],
            footer=[" | ".join(signature())],
            line_width=line_width,
        )

        return file.save_image(
            objects.path_of(
                filename="ultrasonic-sensor-state.png",
                object_name=object_name,
            ),
            image,
            log=log,
        )

    def export_gif(
        self,
        object_name: str,
        line_width: int = 80,
        frame_count: int = -1,
        height: int = 512,
        width: int = 512,
        max_m: float = env.BLUER_UGV_ULTRASONIC_SENSOR_MAX_M,
        log: bool = True,
        rm_blank: bool = True,
    ) -> bool:
        image_list: List[str] = []

        rm_blank_count: int = 0

        temp_folder = objects.path_of(
            object_name=object_name,
            filename="frames",
        )
        if not path.create(temp_folder):
            return False

        for index, detection_list in tqdm(enumerate(self.log)):
            if frame_count != -1 and len(image_list) >= frame_count:
                rm_blank_count += 1
                break

            if rm_blank and all(detection.is_blank for detection in detection_list):
                continue

            filename = objects.path_of(
                object_name=object_name,
                filename=f"frames/{index:010d}.png",
            )

            image = np.concatenate(
                [
                    detection.as_image(
                        height=height,
                        width=int(width / len(detection_list)),
                        max_m=max_m,
                        line_width=int(line_width / len(detection_list)),
                        sign=False,
                    )
                    for detection in detection_list
                ],
                axis=1,
            )

            image = add_signature(
                image,
                header=[
                    " | ".join(
                        [
                            "ultrasonic-sensor",
                            "max distance: {:.2f} mm".format(max_m * 1000),
                            "warning: {:.2f} mm".format(
                                env.BLUER_UGV_ULTRASONIC_SENSOR_WARNING_THRESHOLD
                            ),
                            "danger: {:.2f} mm".format(
                                env.BLUER_UGV_ULTRASONIC_SENSOR_DANGER_THRESHOLD
                            ),
                        ]
                        + detection_list.as_str(short=True)
                        + objects.signature(
                            "frame #{:04d}/{}".format(
                                index,
                                len(self.log),
                            ),
                            object_name,
                        ),
                    )
                ],
                footer=[" | ".join(signature())],
                line_width=line_width,
            )

            if not file.save_image(filename, image):
                return False

            image_list.append(filename)

        if not generate_animated_gif(
            image_list,
            objects.path_of(
                filename="ultrasonic-sensor-detections.gif",
                object_name=object_name,
            ),
            log=log,
        ):
            return False

        if rm_blank:
            logger.info("removed {} blank frame(s).".format(rm_blank_count))

        return path.delete(temp_folder)

    def load(
        self,
        object_name: str,
    ) -> bool:
        success, self.log = file.load(
            objects.path_of(
                object_name=object_name,
                filename="detections.dill",
            ),
        )

        if success:
            logger.info("loaded {} detection(s).".format(len(self.log)))

        return success

    def save(
        self,
        object_name: str,
        log: bool = True,
    ) -> bool:
        if not file.save_yaml(
            objects.path_of(
                object_name=object_name,
                filename="detections.yaml",
            ),
            {
                "detections": [
                    [detection.as_dict() for detection in detection_list]
                    for detection_list in self.log
                ]
            },
            log=log,
        ):
            return False

        if not file.save(
            objects.path_of(
                object_name=object_name,
                filename="detections.dill",
            ),
            self.log,
            log=log,
        ):
            return False

        return True
