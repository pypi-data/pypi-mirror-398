from bluer_objects import README

from bluer_sbc.README.designs.consts import assets2

image_template = assets2 + "anchor/{}?raw=true"

marquee = README.Items(
    [
        {
            "name": "anchor ⚓️",
            "marquee": image_template.format("20251205_175953.jpg"),
            "url": "./bluer_sbc/docs/anchor",
        }
    ]
)
