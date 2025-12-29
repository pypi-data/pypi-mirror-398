from bluer_ugv.README.ugvs.comparison.features.classes import (
    Feature,
    Feature_Comparison,
    Feature_Enum,
)


class UGV_Cost(Feature_Enum):
    LOW = 100  # < 100 mT ~= $100
    MEDIUM = 10  # < 1 MT ~= $10k
    HIGH = 1  #

    @property
    def as_str(self):
        return {
            UGV_Cost.LOW: "کم",
            UGV_Cost.MEDIUM: "متوسط",
            UGV_Cost.HIGH: "زیاد",
        }[self]


class CostFeature(Feature):
    nickname = "cost"
    long_name = "هزینه"

    comparison_as_str = {
        Feature_Comparison.HIGHER: "پایین‌تر",
        Feature_Comparison.LOWER: "بالاتر",
        Feature_Comparison.SIMILAR: "مشابه",
    }
