from bluer_objects.README.items import ImageItems
from bluer_objects.README.consts import assets2

from bluer_ugv.README.swallow.consts import (
    swallow_assets2,
    swallow_ultrasonic_sensor_designs,
)

docs = [
    {
        "path": "../docs/swallow/digital/design/ultrasonic-sensor",
        "items": ImageItems(
            {
                f"{swallow_ultrasonic_sensor_designs}/geometry.png?raw=true": f"{swallow_ultrasonic_sensor_designs}/geometry.svg",
            }
        ),
    },
    {
        "path": "../docs/swallow/digital/design/ultrasonic-sensor/dev.md",
        "cols": 1,
        "items": ImageItems(
            {
                f"{swallow_assets2}/20251001_203056_1.gif": "",
                f"{swallow_assets2}/20251001_185852.jpg": "",
            }
        ),
    },
    {
        "path": "../docs/swallow/digital/design/ultrasonic-sensor/tester.md",
        "cols": 2,
        "items": ImageItems(
            {
                f"{swallow_assets2}/20250918_122725.jpg": "",
                f"{swallow_assets2}/20250918_194715-2.jpg": "",
                f"{swallow_assets2}/20250918_194804_1.gif": "",
                f"{assets2}/ultrasonic-sensor-tester/00.jpg": "",
            }
        ),
    },
    {
        "path": "../docs/swallow/digital/design/ultrasonic-sensor/shield.md",
        "items": ImageItems(
            {
                f"{swallow_assets2}/20250923_142200.jpg": "",
                f"{swallow_assets2}/20250923_145111.jpg": "",
            }
        ),
    },
]
