from bluer_objects.README.items import Items
from bluer_objects import markdown
from bluer_objects.README.consts import assets_url

from bluer_ugv.README.swallow.consts import (
    swallow_assets2,
    swallow_electrical_designs,
)

items = markdown.generate_table(
    Items(
        [
            {
                "name": "computer",
                "url": "./bluer_ugv/docs/swallow/digital/design/computer",
                "marquee": f"{swallow_electrical_designs}/digital.png?raw=true",
            },
            {
                "name": "UGVs",
                "url": "./bluer_ugv/docs/UGVs",
                "marquee": f"{swallow_assets2}/20250912_211652.jpg?raw=true",
            },
            {
                "name": "terraform",
                "url": "./bluer_ugv/docs/swallow/digital/design/terraform.md",
                "marquee": f"{swallow_assets2}/20250611_100917.jpg?raw=true",
            },
            {
                "name": "validations",
                "url": "./bluer_ugv/docs/validations",
                "marquee": assets_url(
                    suffix="{object_name}/{object_name}.gif".format(
                        object_name="swallow-debug-2025-09-25-13-16-59-rnm7jd"
                    )
                ),
            },
        ]
    ),
    cols=2,
    log=False,
)
