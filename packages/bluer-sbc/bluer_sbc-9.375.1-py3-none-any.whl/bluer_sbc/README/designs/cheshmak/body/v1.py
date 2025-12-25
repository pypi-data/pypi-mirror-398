from bluer_objects.README.items import ImageItems

from bluer_sbc.README.designs.consts import assets2


docs = [
    {
        "path": "../docs/cheshmak/body/v1.md",
        "items": ImageItems(
            {
                **{
                    (assets2 + "bryce/{}?raw=true").format(f"{index+1:02}.jpg"): ""
                    for index in range(8)
                }
            }
        ),
    },
]
