from bluer_objects.README.items import ImageItems

from bluer_ugv.README.swallow.consts import swallow_assets2

items = ImageItems(
    {
        f"{swallow_assets2}/20251116_145939.jpg": "",
        f"{swallow_assets2}/20251116_150940.jpg": "",
        f"{swallow_assets2}/20251116_151611.jpg": "",
        f"{swallow_assets2}/20251116_152801.jpg": "",
        f"{swallow_assets2}/20251116_152832_1.gif": "",
    }
)

docs = [
    {
        "path": "../docs/swallow/digital/design/computer/testing.md",
        "items": items,
    },
]
