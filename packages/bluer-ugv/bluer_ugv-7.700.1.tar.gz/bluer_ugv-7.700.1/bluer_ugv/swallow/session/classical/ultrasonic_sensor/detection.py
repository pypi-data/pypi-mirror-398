from typing import Dict, Tuple
import numpy as np
import time
from enum import Enum, auto

from bluer_objects.graphics.signature import add_signature

from bluer_ugv import env


class DetectionState(Enum):
    CLEAR = auto()
    WARNING = auto()
    DANGER = auto()

    @property
    def color_code(self) -> Tuple[int, int, int]:
        return (
            [0, 255, 0]
            if self == DetectionState.CLEAR
            else ([255, 255, 0] if self == DetectionState.WARNING else [255, 0, 0])
        )


class Detection:
    def __init__(
        self,
        side: str,
        detection: bool = False,
        reason: str = "",
        echo_detected: bool = False,
        pulse_ms: float = 0.0,
        distance_mm: float = 0.0,
    ) -> None:
        self.time = time.time()
        self.side = side

        self.detection = detection
        self.reason = reason

        self.echo_detected = echo_detected
        self.pulse_ms = pulse_ms
        self.distance_mm = distance_mm

    def as_image(
        self,
        height: int = 512,
        width: int = 256,
        max_m: float = env.BLUER_UGV_ULTRASONIC_SENSOR_MAX_M,
        sign: bool = True,
        line_width: int = 80,
    ) -> np.ndarray:
        image = np.zeros((height, width, 3), dtype=np.uint8)

        if not self.detection:
            image[:, :, :] = 0
        elif not self.echo_detected:
            image[:, :, :] = 64
        else:
            distance = max(
                min(
                    int(self.distance_mm / 1000 / max_m * height),
                    height,
                ),
                0,
            )

            color_code = self.state.color_code
            for channel in range(3):
                image[:, :, channel] = color_code[channel]

            image[height - distance :, :, :] = 128

        if sign:
            image = add_signature(
                image,
                header=[self.as_str(short=True)],
                line_width=line_width,
            )

        return image

    def as_dict(self) -> Dict:
        return {
            "side": self.side,
            "detection": self.detection,
            "reason": self.reason,
            "echo_detected": self.echo_detected,
            "pulse_ms": self.pulse_ms,
            "distance_mm": self.distance_mm,
        }

    def as_str(
        self,
        short: bool = False,
    ) -> str:
        if self.detection:
            return ("{}: {}: {}" if short else "{:8}: {}: {:7}").format(
                self.side,
                (
                    (
                        "{:.0f} mm".format(self.distance_mm)
                        if short
                        else "{:6.2f} ms == {:5.0f} mm".format(
                            self.pulse_ms,
                            self.distance_mm,
                        )
                    )
                    if self.echo_detected
                    else "no echo" if self.detection else "no detection"
                ),
                self.state.name.lower(),
            )

        return "{}: no detection{}".format(
            self.side,
            f" ({self.reason})" if self.reason else "",
        )

    @property
    def is_blank(self) -> bool:
        return not self.detection or not self.echo_detected

    @property
    def state(self) -> DetectionState:
        if not self.echo_detected or not self.detection:
            return DetectionState.CLEAR

        if self.distance_mm < env.BLUER_UGV_ULTRASONIC_SENSOR_DANGER_THRESHOLD:
            return DetectionState.DANGER

        if self.distance_mm < env.BLUER_UGV_ULTRASONIC_SENSOR_WARNING_THRESHOLD:
            return DetectionState.WARNING

        return DetectionState.CLEAR
