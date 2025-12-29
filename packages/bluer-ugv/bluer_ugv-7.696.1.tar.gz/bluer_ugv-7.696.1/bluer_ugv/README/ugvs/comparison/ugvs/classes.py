from typing import List, Dict, Any, Union

from bluer_ugv.README.ugvs.comparison.features.classes import (
    FeatureList,
    Feature_Comparison,
)
from bluer_ugv.README.ugvs.comparison.features.db import dict_of_feature_classes
from bluer_ugv.logger import logger


class UGV:
    def __init__(
        self,
        nickname: str,
        name: str,
        features: Dict[str, Any],
        deficiencies: List[str] = [],
        image: str = "",
        comments: List[str] = [],
    ):
        self.nickname = nickname
        self.name = name

        self.feature_list: FeatureList = FeatureList()

        for feature_name in features:
            if feature_name not in dict_of_feature_classes:
                logger.error(f"{feature_name}: feature not found.")
                assert False

        for feature_name in dict_of_feature_classes:
            if feature_name not in features:
                continue

            self.feature_list.add(
                dict_of_feature_classes[feature_name](
                    score=features[feature_name],
                )
            )

        self.deficiencies = deficiencies

        self.image = image

        self.comments = comments

    def compare(
        self,
        ugv: "UGV",
        verbose: bool = False,
    ) -> List[str]:
        similarities: List[str] = []
        differences: List[str] = []

        for feature in self.feature_list.db:
            comparison, message = feature.compare(
                ugv.feature_list.get(feature.nickname),
                self.name,
                log=verbose,
            )

            if comparison == Feature_Comparison.SIMILAR:
                similarities.append(message)
            elif comparison == Feature_Comparison.UNKNOWN:
                pass
            else:
                differences.append(
                    '<p style="color:{};">{}</p>'.format(
                        "green" if comparison == Feature_Comparison.HIGHER else "red",
                        message,
                    )
                )

        return (
            [
                '<p dir="rtl" style="text-align:right;">مشابهت: </p>',
                "<ol>",
            ]
            + [
                f'<li dir="rtl" style="text-align:right;">{line}</li>'
                for line in similarities
            ]
            + [
                "</ol>",
                '<p dir="rtl" style="text-align:right;">تفاوت‌ها:</p>',
                "<ol>",
            ]
            + [
                f'<li dir="rtl" style="text-align:right;">{line}</li>'
                for line in differences
            ]
            + [
                "</ol>",
            ]
        )

    @property
    def description(self) -> List[str]:
        return (
            [
                '<b><p dir="rtl" style="text-align:right;">{}</p></b>'.format(
                    self.name
                ),
                "<ol>",
            ]
            + [
                '<li dir="rtl" style="text-align:right;">{}</li>'.format(
                    feature.description
                )
                for feature in self.feature_list.db
            ]
            + ["</ol>"]
        )


class List_of_UGVs:
    def __init__(self):
        self.db: List[UGV] = []

    def add(
        self,
        **kw_args,
    ):
        ugv = UGV(**kw_args)
        self.db.append(ugv)

    def get(
        self,
        ugv_name: str,
    ) -> Union[UGV, None]:
        for ugv in self.db:
            if ugv_name == ugv.nickname:
                return ugv

        return None
