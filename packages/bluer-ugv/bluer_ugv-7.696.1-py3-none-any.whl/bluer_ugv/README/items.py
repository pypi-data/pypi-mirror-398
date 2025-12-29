from bluer_objects import README

from bluer_ugv.README.consts import bluer_ugv_assets
from bluer_ugv.README.arzhang.consts import arzhang_assets2
from bluer_ugv.README.eagle.consts import eagle_assets2
from bluer_ugv.README.rangin.consts import rangin_assets2
from bluer_ugv.README.ravin.ravin3.consts import assets as ravin3_assets2
from bluer_ugv.README.ravin.consts import description as ravin_description
from bluer_ugv.README.swallow.consts import swallow_assets2

items = README.Items(
    [
        {
            "name": "swallow",
            "marquee": f"{swallow_assets2}/20250913_203635~2_1.gif?raw=true",
            "description": "based on power wheels.",
            "url": "./bluer_ugv/docs/swallow",
        },
        {
            "name": "arzhang",
            "marquee": f"{arzhang_assets2}/VID-20250905-WA0014_1.gif?raw=true",
            "description": "[swallow](./bluer_ugv/docs/swallow)'s little sister.",
            "url": "./bluer_ugv/docs/arzhang",
        },
        {
            "name": "rangin",
            "marquee": f"{rangin_assets2}/20251224_182306~3_1.gif",
            "description": "[swallow](./bluer_ugv/docs/swallow)'s ad robot.",
            "url": "./bluer_ugv/docs/rangin",
        },
        {
            "name": "ravin",
            "marquee": f"{ravin3_assets2}/20250723_095155~2_1.gif?raw=true",
            "description": ravin_description,
            "url": "./bluer_ugv/docs/ravin",
        },
        {
            "name": "eagle",
            "marquee": f"{eagle_assets2}/file_0000000007986246b45343b0c06325dd.png?raw=true",
            "description": "a remotely controlled ballon.",
            "url": "./bluer_ugv/docs/eagle",
        },
        {
            "name": "fire",
            "marquee": f"{bluer_ugv_assets}/fire.png?raw=true",
            "description": "based on a used car.",
            "url": "./bluer_ugv/docs/fire",
        },
        {
            "name": "beast",
            "marquee": "https://github.com/waveshareteam/ugv_rpi/raw/main/media/UGV-Rover-details-23.jpg",
            "description": "based on [UGV Beast PI ROS2](https://www.waveshare.com/wiki/UGV_Beast_PI_ROS2).",
            "url": "./bluer_ugv/docs/beast",
        },
    ]
)
