from bluer_sbc.README.design import design_doc_parts

parts = {
    "BTS7960": "2 x",
    "connector": "3 females",
    "white-terminal": "8 x",
    "nuts-bolts-spacers": "M3: ({})".format(
        " + ".join(
            [
                "4 x nut",
                "8 x 25 mm spacer",
                "4 x 30 mm spacer",
            ]
        )
    ),
    "solid-cable-1-15": "20 cm x (red + black/blue)",
    "PCB-single-14x9_5": "",
}

docs = [
    {
        "path": "../docs/swallow/parts.md",
        "macros": design_doc_parts(
            dict_of_parts=parts,
            parts_reference="../parts",
        ),
    }
]
