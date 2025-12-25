from bluer_objects.README.items import ImageItems

from bluer_sbc.README.designs.battery_bus import image_template

docs = [
    {
        "path": "../docs/battery_bus/body/li-ion.md",
        "items": ImageItems(
            {
                image_template.format("li-ion/v2/20251211_121307.jpg"): "",
                image_template.format("li-ion/v2/20251211_121319.jpg"): "",
                image_template.format("li-ion/v2/20251211_121331.jpg"): "",
                image_template.format("li-ion/v2/20251211_121339.jpg"): "",
                image_template.format("li-ion/v2/20251211_121344.jpg"): "",
                image_template.format("li-ion/v2/20251211_121349.jpg"): "",
                image_template.format("li-ion/v2/20251211_121357.jpg"): "",
                image_template.format("20251210_204219.jpg"): "",
                image_template.format("20251210_204306.jpg"): "",
            }
        ),
    },
    {
        "path": "../docs/battery_bus/body/li-ion-v1.md",
        "items": ImageItems(
            {
                image_template.format("li-ion/20251204_143912.jpg"): "",
                image_template.format("li-ion/20251204_143924.jpg"): "",
                image_template.format("li-ion/20251204_143931.jpg"): "",
                image_template.format("li-ion/20251204_143944.jpg"): "",
                image_template.format("li-ion/20251204_143949.jpg"): "",
                image_template.format("li-ion/20251204_143958.jpg"): "",
                image_template.format("li-ion/20251204_144045.jpg"): "",
            }
        ),
    },
]
