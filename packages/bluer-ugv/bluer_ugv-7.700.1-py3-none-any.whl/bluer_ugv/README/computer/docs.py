from bluer_objects.README.items import ImageItems

from bluer_ugv.README.swallow.consts import swallow_assets2
from bluer_ugv.README.computer import box, power, schematics, testing
from bluer_ugv.README.computer.shield import docs as shield


docs = (
    [
        {
            "path": "../docs/swallow/digital/design/computer",
            "items": ImageItems(
                {
                    f"{swallow_assets2}/20251121_124335.jpg": "",
                }
            ),
        },
        {
            "path": "../docs/swallow/digital/design/computer/naming.md",
        },
        {
            "path": "../docs/swallow/digital/design/computer/terraform.md",
        },
        {
            "path": "../docs/swallow/digital/design/computer/connectors-v1.md",
        },
    ]
    + box.docs
    + shield.docs
    + power.docs
    + schematics.docs
    + testing.docs
)
