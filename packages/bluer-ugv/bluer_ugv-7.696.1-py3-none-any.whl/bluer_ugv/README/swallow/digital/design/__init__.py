from bluer_objects.README.items import ImageItems

from bluer_ugv.README.swallow.consts import (
    swallow_assets2,
    swallow_electrical_designs,
)
from bluer_ugv.README.swallow.digital.design import (
    mechanical,
    parts,
    ultrasonic_sensor,
)
from bluer_ugv.swallow.session.classical.keyboard.keys import ControlKeys


docs = (
    [
        {
            "path": "../docs/swallow/digital/design",
        },
        {
            "path": "../docs/swallow/digital/design/operation.md",
            "cols": 2,
            "items": ImageItems(
                {
                    f"{swallow_assets2}/20251019_121811.jpg": "",
                    f"{swallow_assets2}/20251019_121842.jpg": "",
                }
            ),
            "macros": {
                "keys:::": ControlKeys.as_table(),
            },
        },
        {
            "path": "../docs/swallow/digital/design/terraform.md",
            "items": ImageItems(
                {
                    f"{swallow_assets2}/20250611_100917.jpg": "",
                    f"{swallow_assets2}/lab.png": "",
                    f"{swallow_assets2}/lab2.png": "",
                }
            ),
        },
        {
            "path": "../docs/swallow/digital/design/steering-over-current-detection.md",
            "items": ImageItems(
                {
                    f"{swallow_electrical_designs}/steering-over-current.png": f"{swallow_electrical_designs}/steering-over-current.svg",
                }
            ),
        },
        {
            "path": "../docs/swallow/digital/design/rpi-pinout.md",
        },
        {
            "path": "../docs/swallow/digital/design/testing.md",
            "items": ImageItems(
                {
                    f"{swallow_assets2}/20251201_172535~2_1.gif": "",
                    f"{swallow_assets2}/20251203_112604.jpg": "",
                }
            ),
        },
    ]
    + mechanical.docs
    + parts.docs
    + ultrasonic_sensor.docs
)
