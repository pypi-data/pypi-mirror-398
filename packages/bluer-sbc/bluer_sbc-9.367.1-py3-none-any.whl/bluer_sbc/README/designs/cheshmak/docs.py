from bluer_sbc.README.design import design_doc
from bluer_sbc.README.designs.cheshmak import operation, parts, validations
from bluer_sbc.README.designs.cheshmak.items import items
from bluer_sbc.README.designs.cheshmak.body import docs as body


docs = (
    [
        {
            "path": "../docs/cheshmak",
            "items": items,
        }
    ]
    + body.docs
    + operation.docs
    + parts.docs
    + validations.docs
)
