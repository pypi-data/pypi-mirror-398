from blueness.pypi import setup

from bluer_ugv import NAME, VERSION, DESCRIPTION, REPO_NAME

setup(
    filename=__file__,
    repo_name=REPO_NAME,
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    packages=[
        NAME,
        f"{NAME}.help",
        f"{NAME}.help.swallow",
        f"{NAME}.help.swallow.video",
        #
        f"{NAME}.README",
        f"{NAME}.README.arzhang",
        f"{NAME}.README.eagle",
        f"{NAME}.README.fire",
        f"{NAME}.README.rangin",
        f"{NAME}.README.ravin",
        f"{NAME}.README.computer",
        f"{NAME}.README.computer.shield",
        f"{NAME}.README.swallow",
        f"{NAME}.README.swallow.digital",
        f"{NAME}.README.swallow.digital.algo",
        f"{NAME}.README.swallow.digital.design",
        f"{NAME}.README.ugvs",
        f"{NAME}.README.ugvs.comparison",
        f"{NAME}.README.ugvs.comparison.features",
        f"{NAME}.README.ugvs.comparison.references",
        f"{NAME}.README.ugvs.comparison.ugvs",
        # designs
        f"{NAME}.designs",
        f"{NAME}.designs.eagle",
        f"{NAME}.designs.fire",
        f"{NAME}.designs.rangin",
        f"{NAME}.designs.ravin",
        f"{NAME}.designs.ravin.ravin3",
        f"{NAME}.designs.ravin.ravin4",
        #
        f"{NAME}.swallow",
        f"{NAME}.swallow.dataset",
        f"{NAME}.swallow.session",
        f"{NAME}.swallow.session.classical",
        f"{NAME}.swallow.session.classical.camera",
        f"{NAME}.swallow.session.classical.keyboard",
        f"{NAME}.swallow.session.classical.motor",
        f"{NAME}.swallow.session.classical.screen",
        f"{NAME}.swallow.session.classical.screen.video",
        f"{NAME}.swallow.session.classical.setpoint",
        f"{NAME}.swallow.session.classical.ultrasonic_sensor",
    ],
    include_package_data=True,
    package_data={
        NAME: [
            "config.env",
            "sample.env",
            ".abcli/**/*.sh",
            "assets/**/*",
        ],
    },
)
