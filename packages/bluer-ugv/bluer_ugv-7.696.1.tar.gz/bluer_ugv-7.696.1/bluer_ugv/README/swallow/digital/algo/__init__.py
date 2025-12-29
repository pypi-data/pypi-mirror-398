from bluer_objects.README.items import ImageItems

from bluer_ugv.README.consts import algo_docs
from bluer_ugv.README.swallow.consts import swallow_assets2
from bluer_ugv.README.swallow.digital.algo import driving, navigation, tracking, yolo

docs = (
    [
        {
            "path": "../docs/swallow/digital/algo",
        },
    ]
    + driving.docs
    + navigation.docs
    + tracking.docs
    + yolo.docs
)
