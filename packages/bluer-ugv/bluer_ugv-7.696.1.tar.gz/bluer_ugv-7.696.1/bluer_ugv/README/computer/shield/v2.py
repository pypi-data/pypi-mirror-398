from bluer_objects.README.items import ImageItems

from bluer_sbc.README.designs.swallow.consts import swallow_assets2

items = ImageItems(
    {
        f"{swallow_assets2}/20250703_153834.jpg": "",
        f"{swallow_assets2}/20250925_213013.jpg": "",
        f"{swallow_assets2}/20250925_214017.jpg": "",
        f"{swallow_assets2}/20250928_160425.jpg": "",
        f"{swallow_assets2}/20250928_160449.jpg": "",
        f"{swallow_assets2}/20251002_103712.jpg": "",
        f"{swallow_assets2}/20251002_103720.jpg": "",
    }
)

docs = [
    {
        "path": "../docs/swallow/digital/design/computer/shield/v2.md",
        "items": items,
    },
]
