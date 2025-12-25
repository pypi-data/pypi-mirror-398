from bluer_objects.README.items import ImageItems

from bluer_sbc.README.designs.swallow import image_template, latest_version

items = ImageItems({image_template(latest_version).format("01.jpg"): ""})
