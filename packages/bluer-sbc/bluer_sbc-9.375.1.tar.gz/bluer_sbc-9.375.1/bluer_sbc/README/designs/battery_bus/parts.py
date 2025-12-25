from bluer_sbc.README.design import design_doc_parts

parts = {
    "SLA-Battery": "option 1️⃣, e.g. 12 V, 7.2 Ah",
    "li-ion-battery": "option 2️⃣, e.g. 3 x 26650, 5000 mAh 5C, 3.7 V/4.2V",
    "dc-switch": "12V DC 10 A",
    "dc-power-plug": "",
    "dsn-vc288": "",
    "connector": "1 male",
}

docs = [
    {
        "path": "../docs/battery_bus/parts.md",
        "macros": design_doc_parts(
            dict_of_parts=parts,
            parts_reference="../parts",
        ),
    }
]
