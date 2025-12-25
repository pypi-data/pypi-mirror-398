from bluer_sbc.README.designs.swallow import parts
from bluer_sbc.README.designs.swallow import body
from bluer_sbc.README.designs.swallow.items import items


docs = (
    [
        {
            "path": "../docs/swallow",
            "items": items,
        }
    ]
    + body.docs
    + parts.docs
)
