from bluer_objects.README.items import ImageItems

from bluer_sbc.README.designs.swallow.consts import swallow_assets2
from bluer_sbc.README.designs.swallow import image_template, latest_version

docs = (
    [
        {
            "path": "../docs/swallow/body",
            "items": ImageItems(
                {
                    image_template(latest_version).format(f"{index+1:02}.jpg"): ""
                    for index in range(6)
                }
            ),
        }
    ]
    + [
        {
            "path": "../docs/swallow/body/v1.md",
            "items": ImageItems(
                {
                    f"{swallow_assets2}/20250609_164433.jpg": "",
                    f"{swallow_assets2}/20250614_114954.jpg": "",
                    f"{swallow_assets2}/20250615_192339.jpg": "",
                }
            ),
        }
    ]
    + [
        {
            "path": f"../docs/swallow/body/v{version}.md",
            "items": ImageItems(
                {
                    image_template(version).format(
                        f"{index+1:02}.jpg",
                    ): ""
                    for index in range(6)
                }
            ),
        }
        for version in range(2, latest_version)
    ]
)
