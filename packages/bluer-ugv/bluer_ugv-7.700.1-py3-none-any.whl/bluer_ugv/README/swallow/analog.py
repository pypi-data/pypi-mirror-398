from bluer_objects.README.items import ImageItems

from bluer_ugv.README.swallow.consts import swallow_electrical_designs

docs = [
    {
        "path": "../docs/swallow/analog",
        "items": ImageItems(
            {
                f"{swallow_electrical_designs}/analog.png": f"{swallow_electrical_designs}/analog.svg",
            }
        ),
    }
]
