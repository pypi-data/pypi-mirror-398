from bluer_sbc.README.designs.adapter_bus import marquee as adapter_bus_marquee
from bluer_sbc.README.designs.anchor import marquee as anchor_marquee
from bluer_sbc.README.designs.battery_bus import marquee as battery_bus_marquee
from bluer_sbc.README.designs.blue_bracket import items as blue_bracket_items
from bluer_sbc.README.designs.nafha import marquee as nafha_marquee
from bluer_sbc.README.designs.cheshmak import marquee as cheshmak_marquee
from bluer_sbc.README.designs.pwm_generator import marquee as pwm_generator_marquee
from bluer_sbc.README.designs.regulated_bus import marquee as regulated_bus_marquee
from bluer_sbc.README.designs.shelter import marquee as shelter_marquee
from bluer_sbc.README.designs.swallow import marquee as swallow_marquee
from bluer_sbc.README.designs.swallow_head import marquee as swallow_head_marquee
from bluer_sbc.README.designs.ultrasonic_sensor_tester import (
    marquee as ultrasonic_sensor_tester_marquee,
)
from bluer_sbc.README.shortcuts import items as shortcuts_items

docs = [
    {
        "items": []
        + swallow_head_marquee
        + swallow_marquee
        + anchor_marquee
        + pwm_generator_marquee
        + regulated_bus_marquee
        + battery_bus_marquee
        + adapter_bus_marquee
        + ultrasonic_sensor_tester_marquee
        + cheshmak_marquee
        + nafha_marquee
        + shelter_marquee
        + blue_bracket_items,
        "path": "../..",
        "macros": {
            "shortcuts:::": shortcuts_items,
        },
    },
]
