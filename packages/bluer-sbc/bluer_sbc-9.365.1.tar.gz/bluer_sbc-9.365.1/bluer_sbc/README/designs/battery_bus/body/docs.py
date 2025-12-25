from bluer_objects.README.items import ImageItems

from bluer_sbc.README.designs.battery_bus import image_template
from bluer_sbc.README.designs.battery_bus.body import li_ion, sla

docs = (
    [
        {
            "path": "../docs/battery_bus/body",
            "items": ImageItems(
                {
                    image_template.format("20251007_221902.jpg"): "./sla.md",
                    image_template.format("li-ion/20251204_144045.jpg"): "./li-ion.md",
                }
            ),
        },
    ]
    + li_ion.docs
    + sla.docs
)
