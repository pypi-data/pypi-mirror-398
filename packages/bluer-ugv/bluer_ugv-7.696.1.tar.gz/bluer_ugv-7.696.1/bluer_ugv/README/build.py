import os

from bluer_options.help.functions import get_help
from bluer_objects import file, README

from bluer_ugv import NAME, VERSION, ICON, REPO_NAME
from bluer_ugv.help.functions import help_functions
from bluer_ugv.README import (
    alias,
    beast,
    eagle,
    fire,
    ravin,
    root,
    arzhang,
    rangin,
    releases,
    swallow,
)
from bluer_ugv.README.computer import docs as computer
from bluer_ugv.README.ugvs import docs as ugvs
from bluer_ugv.README.ugvs.comparison.build import build as build_comparison


def build() -> bool:
    return (
        all(
            README.build(
                items=readme.get("items", []),
                path=os.path.join(file.path(__file__), readme["path"]),
                cols=readme.get("cols", 3),
                ICON=ICON,
                NAME=NAME,
                VERSION=VERSION,
                REPO_NAME=REPO_NAME,
                help_function=lambda tokens: get_help(
                    tokens,
                    help_functions,
                    mono=True,
                ),
                macros=readme.get("macros", {}),
            )
            for readme in root.docs
            + alias.docs
            + arzhang.docs
            + beast.docs
            + eagle.docs
            + fire.docs
            + rangin.docs
            + ravin.docs
            + releases.docs
            + computer.docs
            + ugvs.docs
            + swallow.docs
        )
        and build_comparison()
    )
