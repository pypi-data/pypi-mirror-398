from typing import List

from bluer_options.terminal import show_usage, xtra


def help_debug(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("~upload", mono=mono)

    args = [
        "[--generate_gif 0]",
        "[--save_images 0]",
    ]

    return show_usage(
        [
            "@swallow",
            "debug",
            f"[{options}]",
            "[-|<object-name>]",
        ]
        + args,
        "debug swallow.",
        mono=mono,
    )
