from bluer_ugv.README.ugvs.comparison.features.classes import Feature


class SpeedFeature(Feature):
    nickname = "speed"
    long_name = "سرعت"

    @property
    def score_as_str_(self) -> str:
        return f"{self.score} کیلومتر بر ساعت"
