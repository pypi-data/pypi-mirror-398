from bluer_objects import README
from bluer_objects.README.items import ImageItems

from bluer_sbc.README.designs.consts import assets2
from bluer_sbc.README.designs.battery_bus.parts import parts as battery_bus_parts
from bluer_sbc.README.designs.pwm_generator import parts as pwm_generator_parts
from bluer_sbc.README.design import design_doc

image_template = assets2 + "nafha/{}?raw=true"

marquee = README.Items(
    [
        {
            "name": "nafha",
            "marquee": image_template.format("20251116_224456.jpg"),
            "url": "./bluer_sbc/docs/nafha",
        }
    ]
)

items = ImageItems(
    {
        image_template.format(f"{filename}"): ""
        for filename in [f"{index+1:02}.png" for index in range(4)]
        + [
            "20251028_123428.jpg",
            "20251028_123438.jpg",
            "20251103_215221.jpg",
            "20251103_215248.jpg",
            "20251103_215253.jpg",
            "20251103_215257.jpg",
            "20251103_215301.jpg",
            "20251103_215319.jpg",
            "20251116_224456.jpg",
            "20251124_094940.jpg",
            "20251125_203403.jpg",
        ]
    },
)

parts = {
    **battery_bus_parts,
    **pwm_generator_parts,
    **{
        "heater-element": "12 V, 4.5 Ω, 32 w",
    },
}

docs = [
    design_doc(
        "nafha",
        items,
        parts,
        own_folder=True,
        parts_reference="../parts",
    ),
    {
        "path": "../docs/nafha/parts-v1.md",
    },
    {
        "path": "../docs/nafha/parts-v2.md",
    },
]
