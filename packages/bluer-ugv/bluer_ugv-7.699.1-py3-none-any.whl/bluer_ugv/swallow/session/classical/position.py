from filelock import FileLock

from bluer_objects import file, objects

from bluer_algo.bps.position import Position
from bluer_algo.logger import logger


class ClassicalPosition:
    def __init__(self, object_name):
        self.object_name: str = object_name
        self.updated: bool = False
        self.position: Position = Position()

        logger.info(f"{self.__class__.__name__}: {object_name}")

    def initialize(self) -> bool:
        return self.update()

    def update(self) -> bool:
        self.updated = False

        filename = objects.path_of(
            object_name=self.object_name,
            filename="position.yaml",
        )

        if not file.exists(filename):
            return True

        self.updated, self.position = Position.load(self.object_name)

        lock = FileLock(filename + ".lock")

        with lock:
            file.delete(filename)

        return True
