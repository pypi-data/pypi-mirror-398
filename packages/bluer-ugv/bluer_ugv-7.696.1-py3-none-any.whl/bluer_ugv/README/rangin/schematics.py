from bluer_objects.README.items import ImageItems

from bluer_ugv.README.rangin.consts import rangin_electrical_design

docs = [
    {
        "path": "../docs/rangin/schematics.md",
        "items": ImageItems(
            {
                f"{rangin_electrical_design}/electrical.png?raw=true": f"{rangin_electrical_design}/electrical.svg",
            },
        ),
    },
]
