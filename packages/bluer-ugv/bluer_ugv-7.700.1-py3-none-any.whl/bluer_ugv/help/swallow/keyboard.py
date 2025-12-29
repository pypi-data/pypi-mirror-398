from typing import List

from bluer_options.terminal import show_usage, xtra

from bluer_ugv import env


def help_test(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("dryrun", mono=mono)

    args = [
        "[--keys 1234567890-+/.]",
    ]

    return show_usage(
        [
            "@swallow",
            "keyboard",
            "test",
            f"[{options}]",
        ]
        + args,
        "test keyboard.",
        mono=mono,
    )


help_functions = {
    "test": help_test,
}
