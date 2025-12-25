from bluer_objects import README
from bluer_objects.README.items import ImageItems
from bluer_objects.README.consts import assets_url

from bluer_sbc.README.design import design_doc


assets2 = assets_url(
    suffix="shelter",
    volume=2,
)

image_template = assets2 + "/{}?raw=true"


marquee = README.Items(
    [
        {
            "name": "shelter",
            "marquee": f"{assets2}/20251104_000755.jpg",
            "url": "./bluer_sbc/docs/shelter",
        }
    ]
)

items = ImageItems(
    {image_template.format(f"{index+1:02}.png"): "" for index in range(4)}
) + ImageItems(
    {
        f"{assets2}/20251005_180841.jpg": "",
        f"{assets2}/20251006_181432.jpg": "",
        f"{assets2}/20251006_181509.jpg": "",
        f"{assets2}/20251006_181554.jpg": "",
        f"{assets2}/20251028_113245.jpg": "",
        f"{assets2}/20251103_182323.jpg": "",
        f"{assets2}/20251104_000755.jpg": "",
        f"{assets2}/20251109_000501.jpg": "",
        f"{assets2}/20251109_000641.jpg": "",
        f"{assets2}/20251109_002124.jpg": "",
        f"{assets2}/20251109_002639.jpg": "",
        f"{assets2}/20251124_094744.jpg": "",
        f"{assets2}/20251202_101949.jpg": "",
        f"{assets2}/20251202_102912.jpg": "",
    }
)

parts = {
    "220VAC-dimmer": "",
    "resistance-heating-wire": "1.59 kΩ",
    "ceramic-terminal": "",
    "mountable-digital-thermometer": "",
}


docs = [
    design_doc(
        "shelter",
        items,
        parts,
        own_folder=True,
        parts_reference="../parts",
    ),
    {
        "path": "../docs/shelter/parts-v1.md",
    },
]
