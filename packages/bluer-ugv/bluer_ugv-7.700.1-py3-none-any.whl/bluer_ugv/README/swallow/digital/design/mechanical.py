from bluer_objects.README.items import ImageItems

from bluer_ugv.README.swallow.consts import swallow_mechanical_designs

docs = [
    {
        "path": "../docs/swallow/digital/design/mechanical",
        "items": ImageItems(
            {
                f"{swallow_mechanical_designs}/robot.png": f"{swallow_mechanical_designs}/robot.stl",
                f"{swallow_mechanical_designs}/cage.png": f"{swallow_mechanical_designs}/cage.stl",
                f"{swallow_mechanical_designs}/measurements.png": "",
            }
        ),
    },
    {
        "path": "../docs/swallow/digital/design/mechanical/v1.md",
        "items": ImageItems(
            {
                f"{swallow_mechanical_designs}/v1/robot.png": f"{swallow_mechanical_designs}/v1/robot.stl",
                f"{swallow_mechanical_designs}/v1/cage.png": f"{swallow_mechanical_designs}/v1/cage.stl",
                f"{swallow_mechanical_designs}/v1/measurements.png": "",
            }
        ),
    },
]
