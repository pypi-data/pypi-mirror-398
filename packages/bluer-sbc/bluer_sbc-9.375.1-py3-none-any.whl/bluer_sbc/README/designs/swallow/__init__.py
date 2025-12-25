from bluer_objects import README

from bluer_sbc.README.designs.consts import assets2

latest_version: int = 6


def image_template(version: int) -> str:
    return assets2 + f"swallow/design/v{version}/{{}}?raw=true"


marquee = README.Items(
    [
        {
            "name": "swallow",
            "marquee": image_template(latest_version).format("01.jpg"),
            "url": "./bluer_sbc/docs/swallow",
        }
    ]
)
