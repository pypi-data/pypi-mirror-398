from typing import List, Iterable, Iterator
from bluer_ugv.swallow.session.classical.ultrasonic_sensor.detection import (
    Detection,
    DetectionState,
)


class DetectionList:
    def __init__(
        self,
        list_of_detections: Iterable[Detection] | None = None,
    ):
        self._content: List[Detection] = (
            list(list_of_detections) if list_of_detections else []
        )

    def __iter__(self) -> Iterator[Detection]:
        return iter(self._content)

    def __len__(self) -> int:
        return len(self._content)

    def __getitem__(self, index: int) -> Detection:
        return self._content[index]

    def append(self, detection: Detection) -> None:
        self._content.append(detection)

    def as_str(
        self,
        short: bool = False,
    ) -> List[str]:
        return [detection.as_str(short=short) for detection in self._content]

    @property
    def state(self) -> DetectionState:
        if any(detection.state == DetectionState.DANGER for detection in self._content):
            return DetectionState.DANGER

        if any(
            detection.state == DetectionState.WARNING for detection in self._content
        ):
            return DetectionState.WARNING

        return DetectionState.CLEAR
