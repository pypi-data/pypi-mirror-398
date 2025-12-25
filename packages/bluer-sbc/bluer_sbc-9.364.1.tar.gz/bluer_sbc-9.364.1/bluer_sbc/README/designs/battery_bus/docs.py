from bluer_sbc.README.designs.battery_bus import parts
from bluer_sbc.README.designs.battery_bus.items import items
from bluer_sbc.README.designs.battery_bus.body import docs as body

docs = (
    [
        {
            "path": "../docs/battery_bus",
            "cols": 2,
            "items": items,
        }
    ]
    + body.docs
    + parts.docs
)
