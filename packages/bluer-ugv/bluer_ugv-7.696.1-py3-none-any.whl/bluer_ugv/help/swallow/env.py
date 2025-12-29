from typing import List

from bluer_options.terminal import show_usage
from bluer_sbc import env


def help_cp(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@swallow",
            "env",
            "cp",
            "[<env-name>]",
        ],
        "cp swallow-raspbian-<env-name>.env.",
        mono=mono,
    )


def help_list(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@swallow",
            "env",
            "list",
        ],
        "list swallow envs.",
        mono=mono,
    )


def help_set(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@swallow",
            "env",
            "set",
            "bps | camera | full_keyboard | screen | steering",
            "0 | 1",
        ],
        "set env.",
        {
            f"bps: BLUER_SBC_SWALLOW_HAS_BPS (currently: {env.BLUER_SBC_SWALLOW_HAS_BPS})": "",
            f"camera: BLUER_SBC_SWALLOW_HAS_CAMERA (currently: {env.BLUER_SBC_SWALLOW_HAS_CAMERA})": "",
            f"full_keyboard: BLUER_SBC_SWALLOW_HAS_FULL_KEYBOARD (currently: {env.BLUER_SBC_SWALLOW_HAS_FULL_KEYBOARD})": "",
            f" screen: BLUER_SBC_ENABLE_SCREEN (currently: {env.BLUER_SBC_ENABLE_SCREEN})"
            f"steering: BLUER_SBC_SWALLOW_HAS_STEERING (currently: {env.BLUER_SBC_SWALLOW_HAS_STEERING})": "",
        },
        mono=mono,
    )


help_functions = {
    "cp": help_cp,
    "list": help_list,
    "set": help_set,
}
