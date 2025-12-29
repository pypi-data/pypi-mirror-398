from typing import List

from bluer_options.terminal import show_usage, xtra

from bluer_ugv import env
from bluer_ugv.help.swallow.video.playlist import help_functions as help_playlist
from bluer_ugv.swallow.session.classical.screen.video.engine import VideoEngine


def help_play(
    tokens: List[str],
    mono: bool,
) -> str:
    args = [
        "[--dryrun 1]",
        "[--download 0]",
        "[--engine {}]".format(
            " | ".join(sorted([engine.name.lower() for engine in VideoEngine]))
        ),
        "[--loop 0]",
        f"[--object_name <{env.RANGIN_VIDEO_LIST_OBJECT}>]",
        "[--timeout <-1 | 10>]",
        "[--video <loading|1>]",
    ]

    return show_usage(
        [
            "@swallow",
            "video",
            "play",
        ]
        + args,
        "play <object-name>/<video>.",
        mono=mono,
    )


help_functions = {
    "play": help_play,
    "playlist": help_playlist,
}
