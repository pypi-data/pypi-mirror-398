from bluer_ugv.help.swallow.dataset import help_functions as help_dataset
from bluer_ugv.help.swallow.debug import help_debug
from bluer_ugv.help.swallow.env import help_functions as help_env
from bluer_ugv.help.swallow.git import help_functions as help_git
from bluer_ugv.help.swallow.keyboard import help_functions as help_keyboard
from bluer_ugv.help.swallow.select_target import help_select_target
from bluer_ugv.help.swallow.ultrasonic_sensor import (
    help_functions as help_ultrasonic_sensor,
)
from bluer_ugv.help.swallow.video.functions import help_functions as help_video

help_functions = {
    "dataset": help_dataset,
    "debug": help_debug,
    "env": help_env,
    "git": help_git,
    "keyboard": help_keyboard,
    "select_target": help_select_target,
    "ultrasonic": help_ultrasonic_sensor,
    "video": help_video,
}
