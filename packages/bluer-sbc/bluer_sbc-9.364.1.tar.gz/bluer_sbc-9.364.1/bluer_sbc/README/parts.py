from bluer_objects import markdown

from bluer_sbc.parts.db import db_of_parts

docs = [
    {
        "path": "../docs/parts",
        "macros": {
            "parts_list:::": db_of_parts.README,
            "parts_images:::": markdown.generate_table(
                db_of_parts.as_images(
                    {part.name: "" for part in db_of_parts},
                    reference="../parts",
                ),
                cols=10,
                log=False,
            ),
        },
    }
] + [
    {
        "path": part.filename(create=True),
        "macros": {
            "info:::": part.README(db_of_parts.url_prefix),
        },
    }
    for part_name, part in db_of_parts.items()
    if part_name != "template"
]
