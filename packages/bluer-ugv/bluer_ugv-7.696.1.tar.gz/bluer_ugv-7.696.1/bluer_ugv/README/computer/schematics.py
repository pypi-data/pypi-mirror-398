from bluer_objects.README.items import ImageItems

from bluer_ugv.README.swallow.consts import swallow_electrical_designs


items = ImageItems(
    {
        f"{swallow_electrical_designs}/digital.png": f"{swallow_electrical_designs}/digital.svg",
    }
)

docs = [
    {
        "path": "../docs/swallow/digital/design/computer/schematics.md",
        "items": items,
    },
]
