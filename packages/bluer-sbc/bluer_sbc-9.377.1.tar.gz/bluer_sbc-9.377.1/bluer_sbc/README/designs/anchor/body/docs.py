from bluer_objects.README.items import ImageItems

from bluer_sbc.README.designs.anchor import image_template
from bluer_sbc.README.designs.anchor.body import v1, v2

docs = (
    [
        {
            "path": "../docs/anchor/body",
            "items": ImageItems(
                {
                    image_template.format("v3/20251211_121404.jpg"): "",
                    image_template.format("v3/20251211_121414.jpg"): "",
                    image_template.format("v3/20251211_121420.jpg"): "",
                    image_template.format("v3/20251211_121423.jpg"): "",
                    image_template.format("v3/20251211_121427.jpg"): "",
                    image_template.format("v3/20251211_121435.jpg"): "",
                    image_template.format("v3/20251211_121452.jpg"): "",
                }
            ),
        }
    ]
    + v1.docs
    + v2.docs
)
