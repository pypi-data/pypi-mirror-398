from bluer_objects.README.items import ImageItems
from bluer_objects.README.consts import assets

from bluer_ugv.README.swallow.consts import swallow_assets2

docs = [
    {
        "path": "../docs/swallow/digital/algo/yolo",
        "items": ImageItems(
            {
                f"{swallow_assets2}/yolo-debug.png": "",
            }
        ),
    },
    {
        "path": "../docs/swallow/digital/algo/yolo/train.md",
        "items": ImageItems(
            {
                f"{swallow_assets2}/yolo-debug-{0}.png": "",
                f"{swallow_assets2}/yolo-debug-{2}.png": "",
                f"{swallow_assets2}/yolo-debug-{3}.png": "",
                f"{swallow_assets2}/yolo-debug-{4}.png": "",
                f"{swallow_assets2}/yolo-debug-{5}.png": "",
                f"{assets}/swallow-debug-2025-09-16-19-53-19-4yzsp8/swallow-debug-2025-09-16-19-53-19-4yzsp8-2.gif": "",
            }
        ),
    },
]
