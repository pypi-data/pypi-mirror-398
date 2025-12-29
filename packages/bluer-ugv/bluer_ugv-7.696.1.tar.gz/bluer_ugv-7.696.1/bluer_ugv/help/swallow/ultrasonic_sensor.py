from typing import List

from bluer_options.terminal import show_usage, xtra

from bluer_ugv import env

review_args = [
    "[--frame_count <-1>]",
    "[--gif 0]",
    "[--rm_blank 0]",
]


def help_review(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("~download,upload", mono=mono)

    args = review_args

    return show_usage(
        [
            "@swallow",
            "ultrasonic",
            "review",
            f"[{options}]",
            "[.|<object-name>]",
        ]
        + args,
        "review ultrasonic sensor data.",
        mono=mono,
    )


def help_test(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("~upload", mono=mono)

    args = sorted(
        review_args
        + [
            "[--export 0]",
            "[--log 0]",
            "[--max_m {:.2f}]".format(env.BLUER_UGV_ULTRASONIC_SENSOR_MAX_M),
        ]
    )

    return show_usage(
        [
            "@swallow",
            "ultrasonic",
            "test",
            f"[{options}]",
            "[-|<object-name>]",
        ]
        + args,
        "test ultrasonic sensors.",
        mono=mono,
    )


help_functions = {
    "review": help_review,
    "test": help_test,
}
