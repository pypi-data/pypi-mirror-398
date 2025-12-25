from bluer_objects.README.items import ImageItems
from bluer_objects.README.consts import designs_url

from bluer_sbc.README.designs.battery_bus import image_template

items = ImageItems(
    {
        image_template.format("concept.png"): "",
        designs_url(
            "battery-bus/electrical/wiring.png?raw=true",
        ): designs_url(
            "battery-bus/electrical/wiring.svg",
        ),
        image_template.format("20251007_221902.jpg"): "./body/sla.md",
        image_template.format("li-ion/v2/20251211_121357.jpg"): "./body/li-ion.md",
    }
)
