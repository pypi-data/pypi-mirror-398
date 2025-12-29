from typing import Dict, Tuple

from bluer_sbc.env import BLUER_SBC_SWALLOW_HAS_FULL_KEYBOARD

from bluer_ugv.logger import logger


class ControlKeys:
    def __init__(
        self,
        is_numpad: bool = BLUER_SBC_SWALLOW_HAS_FULL_KEYBOARD == 0,
        log: bool = True,
    ):
        self.is_numpad = is_numpad

        if log:
            logger.info(
                "{}: {}".format(
                    self.__class__.__name__,
                    "numpad" if self.is_numpad else "full",
                )
            )

        self._keys: Dict[str, Tuple[str, str]] = {
            "ultrasonic off": ("n", "-"),
            "ultrasonic on": ("m", "+"),
            "debug off": ("v", "9"),
            "debug on": ("b", "7"),
            "mode = none": ("y", "5"),
            "mode = action": ("g", "1"),
            "mode = training": ("t", "3"),
            "special key": ("z", "."),
            "speed backward": ("s", "2"),
            "speed forward": ("w", "8"),
            "steer left": ("a", "4"),
            "steer right": ("d", "6"),
            "stop": (" ", "0"),
        }

    @staticmethod
    def as_table():
        keys = ControlKeys(log=False)
        table = keys._keys.copy()  # pylint: disable=protected-access

        for is_numpad in [False, True]:
            keys.is_numpad = is_numpad

            special_keys = keys.special_keys
            for key, event in special_keys.items():
                if event not in table:
                    table[event] = ["", ""]

                table[event][int(is_numpad)] = f"*{key}"

        return [
            "| event | full keyboard | numpad |",
            "|-|-|-|",
        ] + sorted(
            [
                " | ".join(["", event] + list(keys) + [""])
                for event, keys in table.items()
            ]
        )

    def get(self, event: str) -> str:
        return self._keys[event][int(self.is_numpad)]

    @property
    def special_keys(self) -> Dict[str, str]:
        return (
            {
                "7": "exit",
                "9": "shutdown",
                "5": "reboot",
                "1": "update",
            }
            if self.is_numpad
            else {
                "i": "exit",
                "o": "shutdown",
                "p": "reboot",
                "u": "update",
            }
        )
