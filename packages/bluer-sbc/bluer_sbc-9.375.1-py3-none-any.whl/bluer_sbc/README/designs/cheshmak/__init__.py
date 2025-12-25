from bluer_objects import README
from bluer_sbc.README.designs.consts import assets2

image_template = assets2 + "cheshmak/{}?raw=true"

marquee = README.Items(
    [
        {
            "name": "cheshmak",
            "marquee": image_template.format("20251203_190131.jpg"),
            "url": "./bluer_sbc/docs/cheshmak",
        }
    ]
)
