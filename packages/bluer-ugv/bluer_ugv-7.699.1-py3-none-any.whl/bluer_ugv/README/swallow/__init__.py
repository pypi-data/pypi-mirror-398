from bluer_ugv.README.swallow.items import items
from bluer_ugv.README.swallow import analog, digital

docs = (
    [
        {
            "items": items,
            "path": "../docs/swallow",
        },
    ]
    + analog.docs
    + digital.docs
)
