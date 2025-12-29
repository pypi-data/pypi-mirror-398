import shlex
from enum import Enum, auto
import subprocess
import time
import socket

from bluer_objects.graphics.screen import get_size
from bluer_ugv.logger import logger


class VideoEngine(Enum):
    MPV = auto()
    VLC = auto()

    def pause(self, process: subprocess.Popen):
        # MPV: use stdin
        if self == VideoEngine.MPV:
            try:
                if not process.stdin:
                    logger.error("mpv pause failed: no stdin")
                    return False
                process.stdin.write(b"p")
                process.stdin.flush()
            except Exception as e:
                logger.error(f"mpv pause exception: {e}")
                return False
            return True

        # VLC: use RC TCP
        if self == VideoEngine.VLC:
            try:
                s = socket.create_connection(("127.0.0.1", 41940), 0.5)
                s.sendall(b"pause\n")
                s.close()
                return True
            except Exception as e:
                logger.error(f"vlc pause failed: {e}")
                return False

        logger.error(f"{self}: unknown video engine.")
        return False

    def play_command(
        self,
        filename: str,
        fullscreen: bool = True,
        loop: bool = False,
        audio: bool = False,
    ) -> str:
        screen_height, screen_width = get_size()
        logger.info("screen size: {}x{}".format(screen_height, screen_width))

        if self == VideoEngine.MPV:
            logger.info('press "q" to quit mpv.')

            return " ".join(
                [
                    "mpv",
                    "--no-border",
                    "--background=black",  # FIXED
                    "--keepaspect=yes",
                    "--no-keepaspect-window",
                    "--geometry=0:0",
                    (f"--autofit={screen_width}x{screen_height}" if fullscreen else ""),
                    "--loop" if loop else "",
                    "--no-audio" if not audio else "",
                    shlex.quote(filename),
                ]
            )

        if self == VideoEngine.VLC:
            logger.info('press "Enter" to quit vlc.')

            return " ".join(
                [
                    "sudo -u pi",
                    "cvlc",
                    "--fullscreen",
                    "--no-video-title-show",
                    "--no-audio-capture",
                    "--video-on-top",
                    "--no-osd",
                    "--loop" if loop else "",
                    "--no-audio" if not audio else "",
                    "--extraintf",
                    "rc",
                    "--rc-host=127.0.0.1:41940",
                    shlex.quote(filename),
                ]
            )

        return "this-should-not-happen"

    def stop(
        self,
        process: subprocess.Popen,
    ) -> bool:
        if self == VideoEngine.MPV:
            try:
                if process.stdin:
                    process.stdin.write(b"q")
                    process.stdin.flush()
            except Exception as e:
                logger.error(f"mpv quit failed: {e}")
                return False

        if self == VideoEngine.VLC:
            try:
                s = socket.create_connection(("127.0.0.1", 41940), 0.5)
                s.sendall(b"quit\n")
                s.close()
                logger.info("vlc: sent 'quit' via TCP RC.")
            except Exception as e:
                logger.error(f"vlc rc quit failed: {e}")
                return False

        time.sleep(0.3)

        try:
            if process.poll() is None:
                process.kill()
        except Exception as e:
            logger.warning(f"process.kill failed: {e}")
            return False

        return True
