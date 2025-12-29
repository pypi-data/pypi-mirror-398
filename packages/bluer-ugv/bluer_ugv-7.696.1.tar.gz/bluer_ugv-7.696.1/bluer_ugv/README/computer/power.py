from bluer_objects.README.items import ImageItems

from bluer_ugv.README.swallow.consts import swallow_assets2, swallow_designs


items = ImageItems(
    {
        f"{swallow_assets2}/20251119_193930.jpg": "",
        f"{swallow_assets2}/20251119_193954.jpg": "",
    }
)


docs = [
    {
        "path": "../docs/swallow/digital/design/computer/power.md",
        "items": items,
    },
]
