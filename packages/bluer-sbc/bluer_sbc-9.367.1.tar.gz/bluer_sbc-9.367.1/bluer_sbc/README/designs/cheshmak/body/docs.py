from bluer_objects.README.items import ImageItems

from bluer_sbc.README.designs.cheshmak import image_template
from bluer_sbc.README.designs.cheshmak.body import v1

docs = [
    {
        "path": "../docs/cheshmak/body",
        "items": ImageItems(
            {
                image_template.format("20251203_184658.jpg"): "",
                image_template.format("20251203_184702.jpg"): "",
                image_template.format("20251203_184706.jpg"): "",
                image_template.format("20251203_184712.jpg"): "",
                image_template.format("20251203_184717.jpg"): "",
                image_template.format("20251203_184723.jpg"): "",
                image_template.format("20251203_190023.jpg"): "",
                image_template.format("20251203_190131.jpg"): "",
                image_template.format("20251203_190344.jpg"): "",
            }
        ),
    }
] + v1.docs
