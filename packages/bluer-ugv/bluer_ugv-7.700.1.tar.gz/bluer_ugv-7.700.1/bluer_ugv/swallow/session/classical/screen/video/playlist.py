from typing import Dict, List

from bluer_options.logger.config import log_dict, log_list
from bluer_objects.metadata import get_from_object
from bluer_objects import storage, objects
from bluer_objects.storage.policies import DownloadPolicy

from bluer_ugv.logger import logger


class PlayList:
    def __init__(
        self,
        object_name: str,
        download: bool = True,
    ):
        self.index: int = -1

        self.object_name = object_name
        self.download = download

        if self.download:
            storage.download(
                self.object_name,
                filename="metadata.yaml",
            )

        self.messages: Dict[str, str] = get_from_object(
            self.object_name,
            "messages",
            default={},
        )
        log_dict(
            logger,
            "loaded",
            self.messages,
            "message(s)",
            max_count=-1,
            max_length=-1,
        )

        self.playlist: List[Dict[str, str]] = get_from_object(
            self.object_name,
            "playlist",
            default=[],
        )
        log_list(
            logger,
            "loaded",
            self.playlist,
            "playlist item(s)",
            max_count=-1,
            max_length=-1,
        )

        logger.info(
            "{} created from {}.".format(
                self.__class__.__name__,
                self.object_name,
            )
        )

    def get(
        self,
        keyword: int | str = "loading",
        what: str = "filename",
    ) -> str:
        filename = f"{keyword.__class__.__name__}-not-supported"

        if isinstance(keyword, int):
            filename = "bad-index-{}-from-{}".format(
                keyword,
                len(self.playlist),
            )

            if 0 <= keyword < len(self.playlist):
                filename = self.playlist[keyword].get(
                    what,
                    f"{what}-not-found",
                )

        if isinstance(keyword, str):
            filename = f"{keyword}-not-found"

            if keyword.isnumeric():
                return self.get(int(keyword), what=what)

            if keyword in self.messages:
                filename = self.messages[keyword].get(
                    what,
                    f"{what}-not-found",
                )

        if self.download:
            storage.download(
                self.object_name,
                filename=filename,
                policy=DownloadPolicy.DOESNT_EXIST,
            )

        return objects.path_of(
            filename=filename,
            object_name=self.object_name,
        )

    def next(self):
        self.index += 1
        if self.index >= len(self.playlist):
            self.index = 0

        logger.info(
            "{}: video #{}".format(
                self.__class__.__name__,
                self.index,
            )
        )
