from bluer_objects.README.items import Items
from bluer_objects import markdown

from bluer_sbc.parts.db import db_of_parts


items = markdown.generate_table(
    Items(
        [
            {
                "name": "parts",
                "url": "./bluer_sbc/docs/parts",
                "marquee": f"{db_of_parts.url_prefix}/grid.png",
            },
        ]
    ),
    log=False,
)
