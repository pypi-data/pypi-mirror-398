from bluer_objects.README.items import ImageItems

from bluer_ugv.README.arzhang.consts import arzhang_mechanical_design, arzhang_assets2

docs = [
    {
        "path": "../docs/arzhang/design",
    },
    {
        "path": "../docs/arzhang/design/specs.md",
    },
    {
        "path": "../docs/arzhang/design/power.md",
    },
    {
        "path": "../docs/arzhang/design/mechanical",
        "cols": 2,
        "items": ImageItems(
            {
                f"{arzhang_mechanical_design}/robot-with-cover-v2.png": f"{arzhang_mechanical_design}/robot.stl",
                f"{arzhang_mechanical_design}/robot.png": f"{arzhang_mechanical_design}/robot.stl",
                f"{arzhang_mechanical_design}/cage.png": f"{arzhang_mechanical_design}/cage.stl",
                f"{arzhang_mechanical_design}/measurements.png": "",
                f"{arzhang_assets2}/20251128_122828-2.jpg": "",
                f"{arzhang_assets2}/20251128_155615.jpg": "",
                f"{arzhang_assets2}/20251130_134005.jpg": "",
                f"{arzhang_assets2}/20251130_140054.jpg": "",
                f"{arzhang_assets2}/20251201_132846.jpg": "",
            }
        ),
    },
    {
        "path": "../docs/arzhang/design/mechanical/v1.md",
        "items": ImageItems(
            {
                f"{arzhang_mechanical_design}/v1/robot.png": f"{arzhang_mechanical_design}/v1/robot.stl",
                f"{arzhang_mechanical_design}/v1/cage.png": f"{arzhang_mechanical_design}/v1/cage.stl",
                f"{arzhang_mechanical_design}/v1/measurements.png": "",
            }
        ),
    },
]
