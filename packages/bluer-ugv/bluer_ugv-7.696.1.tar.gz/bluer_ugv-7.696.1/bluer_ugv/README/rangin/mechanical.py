from bluer_objects.README.items import Items

from bluer_ugv.README.rangin.consts import rangin_mechanical_design


docs = [
    {
        "path": "../docs/rangin/mechanical.md",
        "cols": 2,
        "items": Items(
            [
                {
                    "name": "arzhang",
                    "marquee": f"{rangin_mechanical_design}/robot.png?raw=true",
                    "url": f"{rangin_mechanical_design}/robot.stl",
                },
                {
                    "name": "90",
                    "marquee": f"{rangin_mechanical_design}/robot-90.png?raw=true",
                    "url": f"{rangin_mechanical_design}/robot-90.stl",
                },
                {
                    "name": "90 (without the cage)",
                    "marquee": f"{rangin_mechanical_design}/robot-90-2.png?raw=true",
                    "url": f"{rangin_mechanical_design}/robot-90.stl",
                },
                {
                    "name": "90c (curved)",
                    "marquee": f"{rangin_mechanical_design}/robot-90c.png?raw=true",
                    "url": f"{rangin_mechanical_design}/robot-90c.stl",
                },
            ]
        ),
    },
]
