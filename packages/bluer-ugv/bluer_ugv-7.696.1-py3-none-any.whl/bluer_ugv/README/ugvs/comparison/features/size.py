from enum import Enum

from bluer_ugv.README.ugvs.comparison.features.classes import (
    Feature,
    Feature_Comparison,
    Feature_Enum,
)


class UGV_Size(Feature_Enum):
    SMALL = 100  # < 20 kg
    MEDIUM = 10  # < 50 kg
    LARGE = 1

    @property
    def as_str(self):
        return {
            UGV_Size.SMALL: "کوچک",
            UGV_Size.MEDIUM: "متوسط",
            UGV_Size.LARGE: "بزرگ",
        }[self]


class SizeFeature(Feature):
    nickname = "size"
    long_name = "اندازه"

    comparison_as_str = {
        Feature_Comparison.HIGHER: "کوچکتر",
        Feature_Comparison.LOWER: "بزرگتر",
        Feature_Comparison.SIMILAR: "مشابه",
    }
