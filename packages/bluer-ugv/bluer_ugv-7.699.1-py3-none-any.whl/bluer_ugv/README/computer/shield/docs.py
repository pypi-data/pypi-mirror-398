from bluer_objects.README.items import ImageItems

from bluer_ugv.README.swallow.consts import swallow_assets2, swallow_designs
from bluer_ugv.README.computer.shield import testing, v1, v2

items = ImageItems(
    {
        f"{swallow_designs}/kicad/swallow/exports/swallow.png": f"{swallow_designs}/kicad/swallow/exports/swallow.pdf",
        f"{swallow_designs}/kicad/swallow/exports/swallow-3d.png": "",
        f"{swallow_designs}/kicad/swallow/exports/swallow-3d-back.png": "",
        f"{swallow_designs}/kicad/swallow/exports/swallow-pcb.png": "",
        f"{swallow_assets2}/20251112_085331.jpg": "",
        f"{swallow_assets2}/20251112_181047.jpg": "",
        f"{swallow_assets2}/20251112_181053.jpg": "",
        f"{swallow_assets2}/20251205_171731.jpg": "",
    }
)


docs = (
    [
        {
            "path": "../docs/swallow/digital/design/computer/shield",
            "items": items,
        },
    ]
    + testing.docs
    + v1.docs
    + v2.docs
)
