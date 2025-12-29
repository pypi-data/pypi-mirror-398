from bluer_ugv.README.ravin import ravin3, ravin4
from bluer_ugv.README.ravin.items import items

docs = (
    [
        {
            "items": items,
            "path": "../docs/ravin",
        },
    ]
    + ravin3.docs
    + ravin4.docs
)
