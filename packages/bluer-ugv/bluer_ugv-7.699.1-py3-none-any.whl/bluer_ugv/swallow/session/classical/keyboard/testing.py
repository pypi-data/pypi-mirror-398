import keyboard

from blueness import module

from bluer_ugv import NAME
from bluer_ugv.logger import logger

NAME = module.name(__file__, NAME)


def test(list_of_keys: str = "") -> bool:
    logger.info("{}.testing({}): ^C to stop".format(NAME, list_of_keys))

    try:
        while True:
            for key in list_of_keys:
                if keyboard.is_pressed(key):
                    logger.info(f"{key} is pressed.")
    except KeyboardInterrupt:
        logger.info("^C detected.")

    return True
