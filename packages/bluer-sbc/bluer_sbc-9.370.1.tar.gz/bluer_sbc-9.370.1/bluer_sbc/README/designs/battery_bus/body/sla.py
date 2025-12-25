from bluer_objects.README.items import ImageItems

from bluer_sbc.README.designs.battery_bus import image_template

docs = [
    {
        "path": "../docs/battery_bus/body/sla.md",
        "items": ImageItems(
            {
                image_template.format("20251007_221902.jpg"): "",
                image_template.format("20251007_220642.jpg"): "",
                image_template.format("20251007_220520.jpg"): "",
                image_template.format("20251007_220601.jpg"): "",
            }
        ),
    }
]
