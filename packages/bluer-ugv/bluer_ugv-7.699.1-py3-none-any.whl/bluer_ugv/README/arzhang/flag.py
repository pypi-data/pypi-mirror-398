from bluer_objects.README.items import ImageItems
from bluer_objects.README.consts import designs_url

from bluer_ugv.README.rangin.consts import rangin_assets2

docs = [
    {
        "path": "../docs/rangin/flag.md",
        "cols": 2,
        "items": ImageItems(
            {
                f"{rangin_assets2}/flag/sketch.jpg": "",
                designs_url(
                    "rangin/flag/design.png?raw=true",
                ): designs_url(
                    "rangin/flag/design.svg",
                ),
            }
        ),
    },
]
