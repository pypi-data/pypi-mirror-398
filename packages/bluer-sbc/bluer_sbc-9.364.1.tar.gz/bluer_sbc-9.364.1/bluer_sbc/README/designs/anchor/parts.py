from bluer_sbc.README.design import design_doc_parts

parts = {
    "sd-card-32-gb": "",
    "rpi": "",
    "XL4015": "",
    "470-mF": "",
    "Polyfuse": "optional",
    "TVS-diode": "",
    "resistor": "7 x 330-470 Ω + 4 x 2.2 kΩ + 4 x 3.3 kΩ",
    "LED": "green + red + yellow + 4 x blue",
    "PCB-single-14x9_5": "",
    "pushbutton": "",
    "connector": "1 female",
    "nuts-bolts-spacers": " + ".join(
        [
            "M2.5: ({})".format(
                " + ".join(
                    [
                        "4 x bolt",
                        "4 x nut",
                        "8 x 10 mm spacer",
                    ]
                )
            ),
            "M3: ({})".format(
                " + ".join(
                    [
                        "1 x bolt",
                        "5 x nut",
                        "4 x 5 mm spacer",
                        "4 x 15 mm spacer",
                        "5 x 25 mm spacer",
                    ]
                )
            ),
        ]
    ),
    "plexiglass": "14 cm x 9.5 cm",
    "green-terminal": "2 x",
    "16-awg-wire": "40 cm x (red + black/blue)",
    "solid-cable-1-15": "10 cm x (red + black/blue)",
    "pin-headers": "1 x (female, 2 x 40) -> 2 x 20 + 2 x (male, 1 x 40) -> 4 x 1 + 2 x 20 + 1 x (male, 2 x 40) -> 2 x 2 x 6",
    "sx1276": "",
    "whip-antenna": "",
}

docs = [
    {
        "path": "../docs/anchor/parts.md",
        "macros": design_doc_parts(
            dict_of_parts=parts,
            parts_reference="../parts",
        ),
    }
]
