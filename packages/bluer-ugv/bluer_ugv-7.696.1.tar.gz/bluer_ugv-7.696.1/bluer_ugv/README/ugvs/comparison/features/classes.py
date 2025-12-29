from typing import List, Any, Union, Tuple, Dict
from enum import Enum, auto

from bluer_ugv.logger import logger


class Feature_Enum(Enum):
    @property
    def as_str(self):
        return self.name


class Feature_Comparison(Feature_Enum):
    SIMILAR = auto()
    HIGHER = auto()
    LOWER = auto()

    UNKNOWN = auto()


class Feature:
    nickname: str
    long_name: str

    comparison_as_str: Dict[Feature_Comparison, str] = {
        Feature_Comparison.HIGHER: "بیشتر",
        Feature_Comparison.LOWER: "کمتر",
        Feature_Comparison.SIMILAR: "مشابه",
    }

    def __init__(
        self,
        score: Any,
    ):
        self.score = score

    def compare(
        self,
        feature: Union["Feature", None],
        ugv_name: str,
        log: bool = False,
    ) -> Tuple[Feature_Comparison, str]:
        comparison: Feature_Comparison = Feature_Comparison.HIGHER
        if feature is None:
            if isinstance(self.score, bool):
                comparison = (
                    Feature_Comparison.HIGHER
                    if self.score
                    else Feature_Comparison.LOWER
                )
            else:
                comparison = Feature_Comparison.UNKNOWN
        elif feature.score is Ellipsis:
            comparison = Feature_Comparison.UNKNOWN
        elif self.score_index == feature.score_index:
            comparison = Feature_Comparison.SIMILAR
        elif self.score_index < feature.score_index:
            comparison = Feature_Comparison.LOWER

        if log:
            logger.info(
                "{}: {} ({}) vs. {} ({}): {}".format(
                    self.__class__.__name__,
                    self.score,
                    self.score_index,
                    "-" if feature is None else feature.score,
                    "-" if feature is None else feature.score_index,
                    comparison.name,
                )
            )

        return comparison, self.describe_status(
            comparison,
            ugv_name,
        )

    def describe_status(
        self,
        comparison: Feature_Comparison,
        ugv_name: str,
    ) -> str:
        return "{} {}{}{}".format(
            self.long_name,
            self.__class__.comparison_as_str.get(comparison, ""),
            (
                " در {} ".format(ugv_name)
                if comparison != Feature_Comparison.SIMILAR
                else ""
            ),
            (lambda info: f" ({info})" if info else "")(self.score_as_str()),
        )

    @property
    def description(self) -> str:
        return "{} {}".format(
            self.long_name,
            self.score_as_str(force=True),
        )

    def score_as_str(
        self,
        force: bool = False,
    ) -> str:
        return (
            self.score.as_str
            if isinstance(self.score, Feature_Enum) and force
            else self.score_as_str_
        )

    @property
    def score_as_str_(self) -> str:
        return ""

    @property
    def score_index(self):
        return (
            int(self.score)
            if isinstance(self.score, bool)
            else self.score.value if isinstance(self.score, Enum) else self.score
        )


class FeatureList:
    def __init__(self):
        self.db: List[Feature] = []

    def add(self, feature: Feature):
        self.db.append(feature)

    def get(
        self,
        feature_name: str,
    ) -> Union[Feature, None]:
        for feature in self.db:
            if feature_name == feature.nickname:
                return feature

        return None
