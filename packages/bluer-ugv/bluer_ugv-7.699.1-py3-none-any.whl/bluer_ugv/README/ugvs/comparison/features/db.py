from typing import Dict, Type, List

from bluer_ugv.README.ugvs.comparison.features.classes import Feature
from bluer_ugv.README.ugvs.comparison.features.concealment import ConcealmentFeature
from bluer_ugv.README.ugvs.comparison.features.control import ControlFeature
from bluer_ugv.README.ugvs.comparison.features.cost import CostFeature
from bluer_ugv.README.ugvs.comparison.features.DYI import DYIFeature
from bluer_ugv.README.ugvs.comparison.features.payload import PayloadFeature
from bluer_ugv.README.ugvs.comparison.features.ps import PSFeature
from bluer_ugv.README.ugvs.comparison.features.range import RangeFeature
from bluer_ugv.README.ugvs.comparison.features.sanction_proof import (
    SanctionProofFeature,
)
from bluer_ugv.README.ugvs.comparison.features.size import SizeFeature
from bluer_ugv.README.ugvs.comparison.features.speed import SpeedFeature
from bluer_ugv.README.ugvs.comparison.features.swarm import SwarmFeature
from bluer_ugv.README.ugvs.comparison.features.uv_delivery import UVDeliveryFeature

list_of_feature_classes: List[Type[Feature]] = [
    PayloadFeature,
    SpeedFeature,
    SizeFeature,
    CostFeature,
    ControlFeature,
    RangeFeature,
    DYIFeature,
    SanctionProofFeature,
    UVDeliveryFeature,
    ConcealmentFeature,
    PSFeature,
    SwarmFeature,
]

dict_of_feature_classes: Dict[str, Type[Feature]] = {
    feature_class.nickname: feature_class for feature_class in list_of_feature_classes
}
