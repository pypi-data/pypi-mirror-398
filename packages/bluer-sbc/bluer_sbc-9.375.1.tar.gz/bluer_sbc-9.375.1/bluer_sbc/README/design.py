from typing import Dict, List, Any

from bluer_objects import markdown

from bluer_sbc.parts.db import db_of_parts


def design_doc(
    design_name: str,
    items: List[str] = [],
    dict_of_parts: Dict = {},
    macros: Dict[str, Dict] = {},
    own_folder: bool = False,
    parts_reference: str = "./parts",
    cols: int = 3,
) -> Dict[str, Any]:
    macros_ = {}
    if dict_of_parts:
        macros_ = design_doc_parts(
            dict_of_parts,
            parts_reference,
        )

    macros_.update(macros)

    return {
        "path": "../docs/{}{}".format(design_name, "" if own_folder else ".md"),
        "cols": cols,
        "items": items,
        "macros": macros_,
    }


def design_doc_parts(
    dict_of_parts: Dict,
    parts_reference: str = "./parts",
) -> Dict[str, Dict]:
    return {
        "parts_images:::": markdown.generate_table(
            db_of_parts.as_images(
                dict_of_parts,
                reference=parts_reference,
            ),
            cols=10,
            log=False,
        ),
        "parts_list:::": db_of_parts.as_list(
            dict_of_parts,
            reference=parts_reference,
            log=False,
        ),
    }
