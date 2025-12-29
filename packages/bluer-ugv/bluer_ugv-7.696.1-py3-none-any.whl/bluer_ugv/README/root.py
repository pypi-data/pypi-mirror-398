from bluer_ugv.README.items import items
from bluer_ugv.README.shortcuts import items as shortcuts_items


docs = [
    {
        "path": "../..",
        "items": items,
        "macros": {
            "shortcuts:::": shortcuts_items,
        },
    },
    {
        "path": "../docs",
    },
]
