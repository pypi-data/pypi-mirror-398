from bluer_objects import README

from bluer_sbc.README.designs.consts import assets2

image_template = assets2 + "battery-bus/{}?raw=true"

marquee = README.Items(
    [
        {
            "name": "battery bus",
            "marquee": image_template.format("20251007_221902.jpg"),
            "url": "./bluer_sbc/docs/battery_bus",
        }
    ]
)
