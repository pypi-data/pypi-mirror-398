from bluer_objects import README
from bluer_objects.README.items import ImageItems
from bluer_objects.README.consts import assets_url, designs_url

from bluer_sbc.README.design import design_doc


assets2 = assets_url(
    suffix="regulated-bus",
    volume=2,
)

marquee = README.Items(
    [
        {
            "name": "regulated bus",
            "marquee": f"{assets2}/20251113_113332.jpg",
            "url": "./bluer_sbc/docs/regulated-bus.md",
        }
    ]
)

items = ImageItems(
    {
        designs_url(
            "regulated-bus/wiring.png?raw=true",
        ): designs_url(
            "regulated-bus/wiring.svg",
        ),
        **{
            f"{assets2}/{timestamp}.jpg": ""
            for timestamp in [
                "20251112_214845",
                "20251113_103345",
                "20251113_103404",
                "20251113_103646",
                "20251113_103653",
                "20251113_103659",
                "20251113_103703",
                "20251113_103713",
                "20251113_103722",
                "20251113_104805",
                "20251113_113332",
                "20251116_234737",
            ]
        },
    }
)

parts = {
    "dc-power-plug": "",
    "dsn-vc288": "",
    "XL4015": "",
    "white-terminal": "2 x",
    "pin-headers": "2 x (2 x 3, 90 degree)",
    "PCB-double-9x7": "10 x 15 holes",
    "nuts-bolts-spacers": "M3: ({})".format(
        " + ".join(
            [
                "7 x bolt",
                "7 x nut",
                "1 x 5 mm spacer",
                "7 x 15 mm spacer",
                "2 x 25 mm spacer",
                "3 x 35 mm spacer",
            ]
        )
    ),
    "plexiglass": "2 x 88 cm x 88 cm",
}


docs = [
    design_doc(
        "regulated-bus",
        items,
        parts,
    )
]
