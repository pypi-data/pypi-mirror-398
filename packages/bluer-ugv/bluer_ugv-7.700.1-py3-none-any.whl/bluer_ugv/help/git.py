from typing import List

from bluer_options.terminal import show_usage


def help_git(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "designs"

    return show_usage(
        [
            "@ugv",
            "git",
            f"[{options}]",
        ],
        "@git @ugv.",
        mono=mono,
    )
