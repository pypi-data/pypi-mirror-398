from bluer_objects import README
from bluer_objects.README.items import ImageItems
from bluer_objects.README.consts import assets_url, designs_url

from bluer_sbc.README.design import design_doc


assets2 = assets_url(
    suffix="adapter-bus",
    volume=2,
)

marquee = README.Items(
    [
        {
            "name": "adapter bus",
            "marquee": f"{assets2}/20251017_222911.jpg",
            "url": "./bluer_sbc/docs/adapter-bus.md",
        }
    ]
)

items = ImageItems(
    {
        designs_url(
            "adapter-bus/wiring.png?raw=true",
        ): designs_url(
            "adapter-bus/wiring.svg",
        ),
        **{
            f"{assets2}/{timestamp}.jpg": ""
            for timestamp in [
                "20251017_222911",
                "20251017_222929",
                "20251017_222938",
                "20251017_222943",
                "20251017_222949",
                "20251017_223017",
                "20251017_223034",
                "20251018_213244",
            ]
        },
    }
)

parts = {
    "dc-power-plug": "",
    "dsn-vc288": "",
    "dc-power-jack": "",
}


docs = [
    design_doc(
        "adapter-bus",
        items,
        parts,
    )
]
