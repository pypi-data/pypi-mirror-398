from typing import List

from bluer_options.terminal import show_usage, xtra
from bluer_objects.help.download import options as download_options
from bluer_objects.help.upload import options as upload_options


def help_cat(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("download", mono=mono)

    return show_usage(
        [
            "@swallow",
            "video",
            "playlist",
            "cat",
            f"[{options}]",
        ],
        "cat swallow playlist.",
        mono=mono,
    )


def help_download(
    tokens: List[str],
    mono: bool,
) -> str:
    options = download_options(mono=mono)

    return show_usage(
        [
            "@swallow",
            "video",
            "playlist",
            "download",
            f"[{options}]",
        ],
        "download swallow playlist.",
        mono=mono,
    )


def help_edit(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("download", mono=mono)

    return show_usage(
        [
            "@swallow",
            "video",
            "playlist",
            "edit",
            f"[{options}]",
        ],
        "edit swallow playlist.",
        mono=mono,
    )


def help_upload(
    tokens: List[str],
    mono: bool,
) -> str:
    options = upload_options(mono=mono)

    return show_usage(
        [
            "@swallow",
            "video",
            "playlist",
            "upload",
            f"[{options}]",
        ],
        "upload swallow playlist.",
        mono=mono,
    )


help_functions = {
    "cat": help_cat,
    "download": help_download,
    "edit": help_edit,
    "upload": help_upload,
}
