from bluer_objects.README.items import ImageItems

from bluer_ugv.README.swallow.consts import (
    swallow_assets2,
    swallow_electrical_designs,
)

items = ImageItems(
    {
        f"{swallow_electrical_designs}/nuts-bolts-spacers.png": f"{swallow_electrical_designs}/nuts-bolts-spacers.svg",
        f"{swallow_assets2}/20251018_133202.jpg": "",
        f"{swallow_assets2}/20251018_133349.jpg": "",
        f"{swallow_assets2}/20251008_114557.jpg": "",
        f"{swallow_assets2}/20251008_133418.jpg": "",
        f"{swallow_assets2}/20251008_124129.jpg": "",
        f"{swallow_assets2}/20251008_124932.jpg": "",
    }
)

docs = [
    {
        "path": "../docs/swallow/digital/design/computer/box.md",
        "items": items,
    }
]
