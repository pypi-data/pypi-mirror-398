from typing import List

from bluer_options.terminal import show_usage, xtra


def help_rm_keys(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "~dryrun,undo"

    return show_usage(
        [
            "@swallow",
            "git",
            "rm_keys",
            f"[{options}]",
        ],
        "(undo) rm github keys.",
        mono=mono,
    )


help_functions = {
    "rm_keys": help_rm_keys,
}
