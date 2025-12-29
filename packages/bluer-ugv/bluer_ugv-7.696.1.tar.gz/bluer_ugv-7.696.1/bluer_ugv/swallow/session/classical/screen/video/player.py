from typing import List, Optional
import subprocess
import shlex
import time

from bluer_options.logger import crash_report
from bluer_options.logger.config import log_list
from bluer_objects import file

from bluer_ugv.swallow.session.classical.screen.video.engine import VideoEngine
from bluer_ugv.logger import logger


class VideoPlayer:
    def __init__(
        self,
        dryrun: bool = False,
        engine: VideoEngine = VideoEngine.VLC,
    ):
        self.process: Optional[subprocess.Popen] = None
        self.current_file: Optional[str] = None

        self.paused = False
        self.dryrun = dryrun
        assert isinstance(engine, VideoEngine)
        self.engine: VideoEngine = engine

        logger.info(
            "{} created on {}{}.".format(
                self.__class__.__name__,
                self.engine.name.lower(),
                " [dryrun]" if dryrun else "",
            )
        )

    def pause(self) -> bool:
        if not self.dryrun:
            if self.process and self.process.poll() is None:
                if not self.engine.pause(self.process):
                    return False

        logger.info(
            "{}.{}".format(
                self.__class__.__name__,
                "resume" if self.paused else "pause",
            )
        )
        self.paused = not self.paused

        return True

    def play(
        self,
        filename: str,
        loop: bool = False,
        audio: bool = False,
        fullscreen: bool = True,
        verbose: bool = True,
    ) -> bool:
        if not file.exists(filename):
            logger.error(f"file not found: {filename}")
            return False

        self.stop()

        command = self.engine.play_command(
            filename=filename,
            fullscreen=fullscreen,
            loop=loop,
            audio=audio,
        )
        logger.info(f"running on {self.engine.name.lower()}: {command}")

        if not self.dryrun:
            try:
                # pylint: disable=consider-using-with
                self.process = subprocess.Popen(
                    shlex.split(command),
                    stdin=subprocess.PIPE if self.engine == VideoEngine.MPV else None,
                    stdout=None if verbose else subprocess.DEVNULL,
                    stderr=None if verbose else subprocess.DEVNULL,
                )

                logger.info(
                    f"pid={self.process.pid}, "
                    f"stdin={self.process.stdin}, returncode={self.process.returncode}"
                )

            except Exception as e:
                crash_report(f"failed to run: {e}")
                self.process = None
                return False

            if not self.process:
                logger.error("process is None.")
                return False

        self.current_file = filename

        logger.info(
            "{}.play({}{})".format(
                self.__class__.__name__,
                "loop: " if loop else "",
                filename,
            )
        )

        return True

    def stop(self) -> bool:
        if not self.dryrun and self.process and self.process.poll() is None:
            if not self.engine.stop(self.process):
                return False

        self.process = None
        logger.info(f"{self.__class__.__name__}.stop")
        return True
