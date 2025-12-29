from bluer_ugv.README.swallow.consts import swallow_assets2
from bluer_ugv.README.arzhang.consts import arzhang_assets, arzhang_assets2
from bluer_ugv.README.rangin.consts import rangin_assets2, rangin_mechanical_design

dict_of_ugvs = {
    "swallow": {
        "order": 1,
        "cols": 1,
        "items": [
            f"{swallow_assets2}/20250701_2206342_1.gif",
            f"{swallow_assets2}/20250913_203635~2_1.gif",
            f"{swallow_assets2}/20251216_205015.jpg",
        ],
    },
    "arzhang": {
        "order": 2,
        "items": [
            f"{arzhang_assets2}/20251209_111322.jpg",
        ],
    },
    "arzhang2": {
        "order": 3,
        "items": [
            f"{arzhang_assets2}/20251210_154513.jpg",
        ],
    },
    "arzhang3": {
        "order": 4,
        "items": sorted(
            [
                f"{arzhang_assets}/20251107_175506.jpg",
                f"{arzhang_assets2}/20251128_175614.jpg",
                f"{arzhang_assets2}/20251202_100317.jpg",
                f"{arzhang_assets2}/20251202_101031.jpg",
                f"{arzhang_assets2}/20251128_113314.jpg",
                f"{arzhang_assets2}/20251128_151952.jpg",
                f"{arzhang_assets2}/20251128_155616.jpg",
                f"{arzhang_assets2}/20251130_140103.jpg",
                f"{arzhang_assets2}/20251203_112602.jpg",
                f"{arzhang_assets2}/20251210_154654.jpg",
            ]
        ),
    },
    "rangin": {
        "order": 5,
        "items": [
            f"{rangin_mechanical_design}/robot.png",
            f"{rangin_assets2}/20251221_125120.jpg",
            f"{rangin_assets2}/20251222_104404.jpg",
            f"{rangin_assets2}/20251222_110634.jpg",
            f"{rangin_assets2}/20251222_160737.jpg",
            f"{rangin_assets2}/20251222_165829.jpg",
            f"{rangin_assets2}/20251222_173509.jpg",
            f"{rangin_assets2}/IMG-20251223-WA0001.jpg",
            f"{rangin_assets2}/IMG-20251223-WA0009.jpg",
            f"{rangin_assets2}/IMG-20251223-WA0010.jpg",
            f"{rangin_assets2}/20251224_180302.jpg",
            f"{rangin_assets2}/20251224_180308.jpg",
            f"{rangin_assets2}/20251224_180319.jpg",
            f"{rangin_assets2}/20251224_182306~3_1.gif",
            f"{rangin_assets2}/2025-12-25-lab.png",
        ],
    },
}
