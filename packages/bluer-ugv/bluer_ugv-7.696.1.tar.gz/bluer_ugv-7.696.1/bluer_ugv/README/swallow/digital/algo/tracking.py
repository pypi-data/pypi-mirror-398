from bluer_objects.README.items import ImageItems
from bluer_objects.README.consts import assets
from bluer_objects.README.consts import assets_url

from bluer_ugv.README.consts import algo_docs
from bluer_ugv.README.swallow.consts import swallow_assets2

tracker_assets2 = assets_url(
    "tracker",
    volume=2,
)

docs = [
    {
        "path": "../docs/swallow/digital/algo/tracking",
    },
    {
        "path": "../docs/swallow/digital/algo/tracking/validations",
    },
    {
        "path": "../docs/swallow/digital/algo/tracking/validations/one.md",
        "items": ImageItems(
            {
                f"{swallow_assets2}/target-selection.png": f"{algo_docs}/socket.md",
            }
        ),
    },
    {
        "path": "../docs/swallow/digital/algo/tracking/validations/two.md",
        "items": ImageItems(
            {
                f"{tracker_assets2}/validations/two/socket-3.png": f"{algo_docs}/socket.md",
                "{}/{}/{}.gif".format(
                    assets,
                    "swallow-debug-2025-12-11-17-23-59-6bhm5n",
                    "swallow-debug-2025-12-11-17-23-59-6bhm5n",
                ): "",
            }
        ),
    },
    {
        "path": "../docs/swallow/digital/algo/tracking/validations/three.md",
        "items": ImageItems(
            {
                "{}/{}/{}.gif".format(
                    assets,
                    "swallow-debug-2025-12-12-14-46-34-m8ahlp",
                    "swallow-debug-2025-12-12-14-46-34-m8ahlp",
                ): "",
            }
        ),
    },
]
