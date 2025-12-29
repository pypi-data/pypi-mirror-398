from bluer_objects.README.items import ImageItems
from bluer_objects.README.consts import assets

from bluer_ugv.README.consts import algo_docs
from bluer_ugv.README.swallow.consts import swallow_assets2

docs = [
    {
        "path": "../docs/swallow/digital/algo/navigation",
    },
    {
        "path": "../docs/swallow/digital/algo/navigation/dataset",
        "items": ImageItems(
            {
                f"{assets}/swallow-dataset-2025-07-11-10-53-04-n3oybs/grid.png": "./digital/dataset/combination/validation.md",
            }
        ),
    },
    {
        "path": "../docs/swallow/digital/algo/navigation/dataset/collection",
        "items": ImageItems(
            {
                f"{swallow_assets2}/2025-07-08-13-09-38-so54ao.png": "",
                f"{swallow_assets2}/2025-07-09-11-20-27-4qf255-000-2.png": "",
                f"{swallow_assets2}/2025-07-09-11-18-07-azy27w.png": f"{algo_docs}/image_classifier/dataset/sequence.md",
            }
        ),
    },
    {
        "path": "../docs/swallow/digital/algo/navigation/dataset/collection/validation.md"
    },
    {"path": "../docs/swallow/digital/algo/navigation/dataset/collection/one.md"},
    {"path": "../docs/swallow/digital/algo/navigation/dataset/combination"},
    {
        "path": "../docs/swallow/digital/algo/navigation/dataset/combination/validation.md"
    },
    {"path": "../docs/swallow/digital/algo/navigation/dataset/combination/one.md"},
    {
        "path": "../docs/swallow/digital/algo/navigation/dataset/review.md",
    },
    {
        "path": "../docs/swallow/digital/algo/navigation/model",
    },
    {"path": "../docs/swallow/digital/algo/navigation/model/validation.md"},
    {
        "path": "../docs/swallow/digital/algo/navigation/model/one.md",
    },
]
