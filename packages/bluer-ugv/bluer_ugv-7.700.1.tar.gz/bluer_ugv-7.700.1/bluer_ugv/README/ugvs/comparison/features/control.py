from enum import Enum

from bluer_ugv.README.ugvs.comparison.features.classes import (
    Feature,
    Feature_Enum,
    Feature_Comparison,
)


class UGV_Control(Feature_Enum):
    AI = 2
    RC = 1

    @property
    def as_str(self):
        return {
            UGV_Control.AI: "هوش مصنوعی",
            UGV_Control.RC: "رادیویی",
        }[self]


class ControlFeature(Feature):
    nickname = "control"
    long_name = "سامانه‌ی کنترلی"

    comparison_as_str = {
        Feature_Comparison.HIGHER: "هوش مصنوعی",
        Feature_Comparison.LOWER: "رادیویی",
        Feature_Comparison.SIMILAR: "مشابه",
    }
