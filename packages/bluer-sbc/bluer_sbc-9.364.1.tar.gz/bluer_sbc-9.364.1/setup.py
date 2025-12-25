from blueness.pypi import setup

from bluer_sbc import NAME, VERSION, DESCRIPTION, REPO_NAME

setup(
    filename=__file__,
    repo_name=REPO_NAME,
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    packages=[
        NAME,
        f"{NAME}.algo",
        f"{NAME}.hardware",
        f"{NAME}.hardware.hat",
        f"{NAME}.hardware.sparkfun_top_phat",
        f"{NAME}.help",
        f"{NAME}.imager",
        f"{NAME}.imager.camera",
        f"{NAME}.imager.lepton",
        f"{NAME}.parts",
        f"{NAME}.parts.classes",
        f"{NAME}.README",
        f"{NAME}.README.designs",
        f"{NAME}.README.designs.battery_bus",
        f"{NAME}.README.designs.battery_bus.body",
        f"{NAME}.README.designs.anchor",
        f"{NAME}.README.designs.anchor.body",
        f"{NAME}.README.designs.cheshmak",
        f"{NAME}.README.designs.cheshmak.body",
        f"{NAME}.README.designs.swallow",
        f"{NAME}.README.designs.swallow_head",
        f"{NAME}.ROS",
        f"{NAME}.session",
    ],
    include_package_data=True,
    package_data={
        NAME: [
            "config.env",
            "sample.env",
            ".abcli/**/*.sh",
        ],
    },
)
