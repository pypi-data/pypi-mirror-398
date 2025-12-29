from bluer_options.host.functions import is_headless

from bluer_sbc.env import BLUER_SBC_ENABLE_SCREEN

from bluer_ugv import env
from bluer_ugv.swallow.session.classical.screen.video.player import VideoPlayer
from bluer_ugv.swallow.session.classical.screen.video.playlist import PlayList
from bluer_ugv.logger import logger


class ClassicalScreen:
    def __init__(self):
        self.video_player = (
            None if (is_headless() or BLUER_SBC_ENABLE_SCREEN == 0) else VideoPlayer()
        )

        self.playlist = PlayList(env.RANGIN_VIDEO_LIST_OBJECT)

        logger.info(f"{self.__class__.__name__} created.")

    def cleanup(self):
        logger.info(f"{self.__class__.__name__}.cleanup")
        if self.video_player is not None:
            self.video_player.stop()

    def initialize(self) -> bool:
        if self.video_player is None:
            return True

        return self.video_player.play(
            self.playlist.get("loading"),
            loop=True,
        )

    def update(self) -> bool:
        if self.video_player is None:
            return True

        if self.video_player.process:
            return True

        self.playlist.next()

        return self.video_player.play(
            self.playlist.get(self.playlist.index),
            loop=False,
        )
