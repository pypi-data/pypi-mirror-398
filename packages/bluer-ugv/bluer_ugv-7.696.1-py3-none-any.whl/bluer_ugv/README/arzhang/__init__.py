from bluer_ugv.README.arzhang.items import items
from bluer_ugv.README.arzhang import design, algo, flag
from bluer_ugv.README.validations import docs as validations

docs = (
    [
        {
            "items": items,
            "path": "../docs/arzhang",
        }
    ]
    + algo.docs
    + design.docs
    + flag.docs
    + validations.docs
)
