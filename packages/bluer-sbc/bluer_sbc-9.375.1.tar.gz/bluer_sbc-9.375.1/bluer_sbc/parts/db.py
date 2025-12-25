from bluer_sbc.parts.classes.part import Part
from bluer_sbc.parts.classes.db import PartDB

db_of_parts: PartDB = PartDB()

db_of_parts["resistor"] = Part(
    info=[
        "Resistor, 1/4 watt, 5% tolerance",
    ],
    images=["resistor.png"],
)

db_of_parts["4-ch-transceiver"] = Part(
    info=[
        "4-channel transmitter and receiver",
        "source: [digikala](https://www.digikala.com/product/dkp-11037586/%DA%AF%DB%8C%D8%B1%D9%86%D8%AF%D9%87-%D9%88-%D9%81%D8%B1%D8%B3%D8%AA%D9%86%D8%AF%D9%87-%D9%85%D8%A7%D8%B4%DB%8C%D9%86-%DA%A9%D9%86%D8%AA%D8%B1%D9%84%DB%8C-%D9%85%D8%AF%D9%84-4ch-led/)",
        "voltages: receiver 6 VDC,  transmitter 3 VDC",
    ],
    images="4-channel-remote-control.png",
)

db_of_parts["470-mF"] = Part(
    info=[
        "capacitor, 470 μF to 1000 μF, 16 V or 25 V, Electrolytic, 105 °C rated if possible."
    ],
    images=["capacitor.png"],
)

db_of_parts["BTS7960"] = Part(
    info=[
        "43 A, H-Bridge Motor Driver",
        "specs: [BTS7960](https://www.handsontec.com/dataspecs/module/BTS7960%20Motor%20Driver.pdf)",
    ],
    images="bts7960.jpg",
)

db_of_parts["dc-motor-12-VDC-45W"] = Part(
    info=[
        "12 VDC motor, 20-45 W",
        "type 1: 9,000 RPM, output ~60 RPM",
        "type 2: 10,000 RPM, output 72 RPM",
        "https://parsbike.com/product/%D9%85%D9%88%D8%AA%D9%88%D8%B1-%DA%AF%DB%8C%D8%B1%D8%A8%DA%A9%D8%B3-%D9%85%D8%A7%D8%B4%DB%8C%D9%86-%D8%B4%D8%A7%D8%B1%DA%98%DB%8C-%D9%88-%D9%85%D9%88%D8%AA%D9%88%D8%B1-%D8%B4%D8%A7%D8%B1%DA%98%DB%8C/",
    ],
    images=[
        "gearbox1.jpg",
        "gearbox2.jpg",
        "gearbox3.jpg",
        "gearbox4.jpg",
        "gearbox5.jpg",
        "gearbox6.jpg",
        "gearbox7.jpg",
        "gearbox8.jpg",
    ],
)

db_of_parts["LED"] = Part(
    info=[
        "LED, ~2 V forward voltage, 10-20 mA",
    ],
    images=["led.png"],
)

db_of_parts["Polyfuse"] = Part(
    info=[
        "Polyfuse, 1.1 A hold, 2.2 A trip, 16 V, resettable, through-hole, e.g., MF-R110",
    ],
    images=["polyfuse.png"],
)

db_of_parts["rpi"] = Part(
    info=[
        "Raspberry Pi.",
        "3B+/4B.",
    ],
    images=[
        "rpi3bplus.png",
        "gpio-pinout.png",
        "rpi-measurements.png",
    ],
)

db_of_parts["SLA-Battery"] = Part(
    info=[
        "Rechargeable sealed lead acid battery",
    ],
    images=[
        "battery.png",
    ],
)

db_of_parts["li-ion-battery"] = Part(
    info=[
        "Li-Ion battery",
    ],
    images=[
        "lithium-battery.jpg",
    ],
)

db_of_parts["TVS-diode"] = Part(
    info=[
        "TVS diode, unidirectional, 600 W, 6.8 V clamp, e.g. P6KE6.8A, DO-15 package",
    ],
    images=[
        "TVSdiode.png",
    ],
)

db_of_parts["XL4015"] = Part(
    info=[
        "XL4015: 8 - 36 VDC -> 1.25 - 32 VDC, 5A",
        "specs: [XL4015](https://www.handsontec.com/dataspecs/module/XL4015-5A-PS.pdf)",
    ],
    images=[
        "XL4015.png",
    ],
)

db_of_parts["rpi-camera"] = Part(
    info=[
        "Raspberry Pi Camera, V1.3",
        "https://www.raspberrypi.com/documentation/accessories/camera.html",
        "https://shop.sb-components.co.uk/products/raspberry-pi-camera",
    ],
    images=[
        "rpi-camera.jpg",
    ],
)

db_of_parts["DC-gearboxed-motor-12V-120RPM"] = Part(
    info=[
        "Gearboxed DC Motor, 12 V (3-24 V), 3A, 120 RPM, 1:91, 15 Kg cm",
        "[GM6558](https://www.landaelectronic.com/product/%d9%85%d9%88%d8%aa%d9%88%d8%b1-dc-%da%af%db%8c%d8%b1%d8%a8%da%a9%d8%b3-%d8%ad%d9%84%d8%b2%d9%88%d9%86%db%8c-gm6558/)",
    ],
    images=[
        "GM6558/01.jpg",
        "GM6558/02.jpg",
        "GM6558/03.jpg",
        "GM6558/04.jpg",
        "GM6558/measurements.jpg",
        "GM6558/specs.png",
    ],
)

db_of_parts["2xAA-battery-holder"] = Part(
    info=[
        "2 x AA battery holder",
    ],
    images=[
        "2xAA-battery-holder.jpg",
    ],
)

db_of_parts["4xAA-battery-holder"] = Part(
    info=[
        "4 x AA battery holder",
    ],
    images=[
        "4xAA-battery-holder.jpg",
    ],
)

db_of_parts["PCB-double-9x7"] = Part(
    info=[
        "double-sided PCB, 9 cm x 7 cm",
    ],
    images=[
        "PCB-double-9x7.jpeg",
    ],
)

db_of_parts["PCB-single-14x9_5"] = Part(
    info=[
        "single-sided PCB, 14 cm x 9.5 cm",
    ],
    images=[
        "pcb-14x9_5cm.jpg",
    ],
)

db_of_parts["pushbutton"] = Part(
    info=[
        "push button",
    ],
    images=[
        "pushbutton.png",
    ],
)

db_of_parts["yellow-gearbox-dc-motor"] = Part(
    info=[
        "gearboxed DC motor, 6V DC",
    ],
    images=[
        "yellow-gearbox-dc-motor.png",
    ],
)

db_of_parts["yellow-wheels"] = Part(
    info=[
        "wheels for gearboxed DC motor",
    ],
    images=[
        "yellow-wheels.jpg",
    ],
)

db_of_parts["36v-hub-motor"] = Part(
    info=[
        "36V DC hub motor, 350 W, front, no gearbox",
        "[source](https://samamotor.ir/%D9%87%D8%A7%D8%A8-%D9%85%D9%88%D8%AA%D9%88%D8%B1/5105-%D9%87%D8%A7%D8%A8-%D9%85%D9%88%D8%AA%D9%88%D8%B1-350-%D9%88%D8%A7%D8%AA-36-%D9%88%D9%84%D8%AA-%D8%A8%D8%AF%D9%88%D9%86-%DA%AF%DB%8C%D8%B1%D8%A8%DA%A9%D8%B3-%D8%AF%D9%88%DA%86%D8%B1%D8%AE%D9%87-%D9%85%D8%AE%D8%B5%D9%88%D8%B5-%DA%86%D8%B1%D8%AE-%D8%AC%D9%84%D9%88-.html)",
    ],
    images=[
        "36v-hub-motor.jpg",
    ],
)

db_of_parts["brushless-350w-drive"] = Part(
    info=[
        "brushless drive, 36 - 48 V DC, 350 W, sine wave, silent",
        "[source](https://samamotor.ir/%D8%AF%D8%B1%D8%A7%DB%8C%D9%88%D8%B1-%D9%85%D9%88%D8%AA%D9%88%D8%B1-%D8%A8%D8%B1%D8%A7%D8%B4%D9%84%D8%B3-bldc/4821-%D8%AF%D8%B1%D8%A7%DB%8C%D9%88%D8%B1-%D8%A8%D8%B1%D8%A7%D8%B4%D9%84%D8%B3-36-48-%D9%88%D9%84%D8%AA-350-%D9%88%D8%A7%D8%AA-sine-wave-silent.html)",
    ],
    images=[
        "brushless-350w-drive.jpg",
    ],
)

db_of_parts["LJ-6V-battery"] = Part(
    info=[
        "6V DC (4 cell) NICD battery",
        "https://www.digikala.com/product/dkp-3213588/%C3%98/",
    ],
    images=[
        "LJ-6V-battery.jpg",
    ],
)


db_of_parts["USB-charger-NICD-6V"] = Part(
    info=[
        "6V DC charger for NICD batteries",
        "https://www.digikala.com/product/dkp-5977954/%D8%B4%D8%A7%D8%B1%DA%98%D8%B1-%D8%A8%D8%A7%D8%AA%D8%B1%DB%8C-%D9%85%D8%A7%D8%B4%DB%8C%D9%86-%DA%A9%D9%86%D8%AA%D8%B1%D9%84%DB%8C-%D9%85%D8%AF%D9%84-6-%D9%88%D9%84%D8%AA-%DA%A9%D8%AF-6v-usb-sm-%D8%A8%D9%87-%D9%87%D9%85%D8%B1%D8%A7%D9%87-%D8%B3%D9%88%DA%A9%D8%AA-sm-%D8%AF%D9%88-%D9%BE%DB%8C%D9%86/",
    ],
    images=[
        "USB-charger-NICD-6V-1.jpg",
        "USB-charger-NICD-6V-2.jpg",
    ],
)

db_of_parts["L-1x2"] = Part(
    info=[
        "L 1x2",
        "https://robotexiran.com/product/%d8%a8%d8%b3%d8%aa-21-l/",
    ],
    images=[
        "L-1x2-1.jpg",
        "L-1x2-2.jpg",
    ],
)

db_of_parts["shaft-10cm"] = Part(
    info=[
        "shaft, 10 cm",
        "https://robotexiran.com/product/%d9%85%d8%ad%d9%88%d8%b1-10cm/",
    ],
    images=[
        "shaft-10cm.jpg",
    ],
)

db_of_parts["M3"] = Part(
    info=[
        "M3 nuts and bolts",
    ],
    images=[
        "M3.jpg",
    ],
)

db_of_parts["front-connector"] = Part(
    info=[
        "front connector",
    ],
    images=[
        "front-connector.jpg",
    ],
)

db_of_parts["front-wheels"] = Part(
    info=[
        "front wheels",
    ],
    images=[
        "front-wheels.jpg",
    ],
)

db_of_parts["wheel"] = Part(
    info=[
        "power wheel wheels",
        "https://sarobatic.ir/product/%DA%86%D8%B1%D8%AE-%D8%A8%D8%B2%D8%B1%DA%AF-%D8%B9%D9%82%D8%A8-%D9%85%D8%A7%D8%B4%DB%8C%D9%86-%D8%B4%D8%A7%D8%B1%DA%98%DB%8C-%D8%A7%D8%B3%D8%AA%D9%88%DA%A9/",
        "https://toys-repair.ir/product/2768/",
    ],
    images=[
        "wheel1.jpg",
        "wheel4.jpg",
        "wheel3.jpg",
    ],
)

db_of_parts["ultrasonic-sensor"] = Part(
    info=[
        "HC-SR04: ultrasonic-sensor",
        "[datasheet](https://cdn.sparkfun.com/datasheets/Sensors/Proximity/HCSR04.pdf)",
        "1m ~= 6ms",
        "fov = 15 - 30 deg",
    ],
    images=[
        "HC-SR04.jpg",
    ],
)

db_of_parts["connector"] = Part(
    info=[
        "auto power connectors",
    ],
    images=[
        "connector.jpg",
    ],
)

db_of_parts["1N4148"] = Part(
    info=[
        "1N4148 diode",
    ],
    images=[
        "TVSdiode.png",
    ],
)

db_of_parts["TV"] = Part(
    info=[
        "TV",
    ],
    images=[
        "tv.jpg",
    ],
)

db_of_parts["power-inverter"] = Part(
    info=[
        "power inverter, 12 VDC -> 220 VAC.",
        "pure sine wave.",
    ],
    images=[
        "power-inverter.jpg",
    ],
)

db_of_parts["TV-bracket"] = Part(
    info=[
        "TV bracket",
    ],
    images=[
        "tv-bracket.jpeg",
    ],
)

db_of_parts["dc-switch"] = Part(
    info=[
        "on/off DC switch with indicator led",
    ],
    images=[
        "on-off-switch.png",
    ],
)

db_of_parts["dc-power-plug"] = Part(
    info=[
        "DC power plug, 5.5 mm",
    ],
    images=[
        "charging-port.jpg",
    ],
)

db_of_parts["dsn-vc288"] = Part(
    info=[
        "DSN-VC288, panel mount, 4-30 VDC, 10A, voltmeter ammeter",
        "https://hamguyparts.com/files/Download/Chinese%20DVA.pdf",
        "https://www.skytech.ir/DownLoad/File/11515_DSN-VC288.pdf",
    ],
    images=[
        "dsn-vc288.jpg",
        "dsn-vc288-connection.jpg",
        "dsn-vc288-measurements.jpeg",
    ],
)

db_of_parts["dc-volt-meter"] = Part(
    info=[
        "DC volt meter",
    ],
    images=[
        "dsn-vc288.jpg",
    ],
)

db_of_parts["nuts-bolts-spacers"] = Part(
    info=[
        "nuts, bolts, and spacers",
    ],
    images=[
        "nuts-bolts-spacers.jpg",
    ],
)

db_of_parts["plexiglass"] = Part(
    info=[
        "plexiglass, 2 mm or 2.5 mm thickness",
    ],
    images=[
        "plexiglass.jpg",
    ],
)

db_of_parts["white-terminal"] = Part(
    info=[
        "white terminal",
    ],
    images=[
        "white-terminal.jpg",
    ],
)

db_of_parts["green-terminal"] = Part(
    info=[
        "green terminal",
    ],
    images=[
        "green-terminal.jpg",
    ],
)

db_of_parts["dupont-cables"] = Part(
    info=[
        "dupont cables, female to female",
    ],
    images=[
        "dupont-cables.jpg",
    ],
)

db_of_parts["16-awg-wire"] = Part(
    info=[
        "16 AWG wire",
    ],
    images=[
        "16-awg-wire.jpeg",
    ],
)

db_of_parts["solid-cable-1-15"] = Part(
    info=[
        "solid cable 1-1.5 mm^2",
    ],
    images=[
        "solid-cable-1-15.jpg",
    ],
)

db_of_parts["strong-thread"] = Part(
    info=[
        "strong thread",
    ],
    images=[
        "strong-thread.jpg",
    ],
)

db_of_parts["pin-headers"] = Part(
    info=[
        "pin headers",
    ],
    images=[
        "pin-headers.jpg",
    ],
)

db_of_parts["ni-mh-battery"] = Part(
    info=[
        "Ni-MH AA, 2400 mAh, 1.2 VDC",
    ],
    images=[
        "ni-mh-battery.jpg",
    ],
)

db_of_parts["mt-3608"] = Part(
    info=[
        "MT-3608, step up module.",
        "maximum voltage: 28 VDC, maximum current: 2 A",
        "https://eshop.eca.ir/%D9%85%D8%A7%DA%98%D9%88%D9%84-%D8%AA%D8%BA%D8%B0%DB%8C%D9%87-%D9%88%D9%84%D8%AA%D8%A7%DA%98-%D9%88-%D8%B4%D8%A7%D8%B1%DA%98/6898-%D9%85%D8%A7%DA%98%D9%88%D9%84-%D8%A7%D9%81%D8%B2%D8%A7%DB%8C%D9%86%D8%AF%D9%87-%D9%88%D9%84%D8%AA%D8%A7%DA%98-2-%D8%A2%D9%85%D9%BE%D8%B1-mt3608.html",
    ],
    images=[
        "mt-3608.jpg",
    ],
)


db_of_parts["arduino-nano"] = Part(
    info=[
        "Arduino Nano",
    ],
    images=[
        "arduino-nano.png",
    ],
)

db_of_parts["tb6612"] = Part(
    info=[
        "TB6612, 2-channel DC motor driver.",
        "current: average 1.2 A, peak 3.2 A",
        "voltage: maximum supply 15 V DC",
        "https://toshiba.semicon-storage.com/ap-en/semiconductor/product/motor-driver-ics/brushed-dc-motor-driver-ics/detail.TB6612FNG.html",
        "https://daneshjookit.com/module/motor-drive/2783-%D9%85%D8%A7%DA%98%D9%88%D9%84-%D8%AF%D8%B1%D8%A7%DB%8C%D9%88%D8%B1-%D9%85%D9%88%D8%AA%D9%88%D8%B1-%D8%AF%D9%88-%DA%A9%D8%A7%D9%86%D8%A7%D9%84%D9%87-%D8%A8%D8%A7-%D8%AA%D8%B1%D8%A7%D8%B4%D9%87-tb6612fng.html",
    ],
    images=[
        "tb6612.jpg",
    ],
)

db_of_parts["small-dc-switch"] = Part(
    info=[
        "small on/off switch",
    ],
    images=[
        "small-on-off-switch.jpg",
    ],
)

db_of_parts["double-sided-tape"] = Part(
    info=[
        "double-sided tape.",
    ],
    images=[
        "double-sided-tape.jpg",
    ],
)

db_of_parts["electrical-tape"] = Part(
    info=[
        "electrical tape",
    ],
    images=[
        "electrical-tape.jpg",
    ],
)

db_of_parts["micro-usb-cable"] = Part(
    info=[
        "Micro USB cable",
    ],
    images=[
        "micro-usb-cable.jpg",
    ],
)

db_of_parts["dc-power-jack"] = Part(
    info=[
        "DC power jack, 5.5 mm",
    ],
    images=[
        "charger-socket.jpg",
    ],
)

db_of_parts["220VAC-dimmer"] = Part(
    info=[
        "220VAC dimmer",
    ],
    images=[
        "220VAC-dimmer.jpeg",
    ],
)

db_of_parts["resistance-heating-wire"] = Part(
    info=[
        "resistance heating wire",
    ],
    images=[
        "resistance-heating-wire.jpg",
    ],
)

db_of_parts["ceramic-terminal"] = Part(
    info=[
        "ceramic terminal",
    ],
    images=[
        "ceramic-terminal.jpg",
    ],
)

db_of_parts["mountable-digital-thermometer"] = Part(
    info=[
        "mountable digital thermometer",
    ],
    images=[
        "mountable-digital-thermometer.jpeg",
    ],
)

db_of_parts["pwm-manual-dc-motor-controller"] = Part(
    info=[
        "pwm manual DC motor controller, 12 V, ≥ 5 A",
    ],
    images=[
        "pwm-manual-dc-motor-controller.jpg",
    ],
)

db_of_parts["heater-element"] = Part(
    info=[
        "heater element",
    ],
    images=[
        "heater-element.jpg",
    ],
)

db_of_parts["sd-card-32-gb"] = Part(
    info=[
        "SD card, 32 GB",
    ],
    images=[
        "sd-card-32-gb.jpg",
    ],
)

db_of_parts["dc-fuse"] = Part(
    info=[
        "DC fuse, ANL or MIDI type",
    ],
    images=[
        "dc-fuse.jpg",
    ],
)

db_of_parts["mcb"] = Part(
    info=[
        "miniature circuit breaker (MCB)",
    ],
    images=[
        "mcb-3.jpg",
    ],
)

db_of_parts["dc-circuit-breaker"] = Part(
    info=[
        "DC circuit breaker",
    ],
    images=[
        "mcb-3.jpg",
    ],
)

db_of_parts["ac-switch"] = Part(
    info=[
        "AC switch",
    ],
    images=[
        "ac-switch.jpg",
    ],
)

db_of_parts["safety-fuse"] = Part(
    info=[
        "safety fuse",
        "residual current device (RCD / GFCI)",
    ],
    images=[
        "safety-fuse.jpg",
    ],
)

db_of_parts["ac-volt-meter"] = Part(
    info=[
        "AC volt meter",
    ],
    images=[
        "ac-volt-meter.jpg",
    ],
)

db_of_parts["emergency-stop"] = Part(
    info=[
        "emergency stop switch",
    ],
    images=[
        "emergency-stop.jpg",
    ],
)

db_of_parts["power-adapter"] = Part(
    info=[
        "AC to DC power adapter",
    ],
    images=[
        "power-adapter.jpg",
    ],
)

db_of_parts["li-ion-charger"] = Part(
    info=[
        "Li-Ion battery charger, 12.6 VDC, 1 A",
    ],
    images=[
        "power-adapter.jpg",
    ],
)

db_of_parts["relay"] = Part(
    info=[
        "relay",
    ],
    images=[
        "relay.jpg",
    ],
)

db_of_parts["heavy-duty-pipe-clamp"] = Part(
    info=[
        "heavy duty pipe clamp",
    ],
    images=[
        "heavy-duty-pipe-clamp.jpg",
    ],
)

db_of_parts["sx1276"] = Part(
    info=[
        "SX1276/77/78/79 UART",
        "[datasheet](https://cdn.sparkfun.com/assets/7/7/3/2/2/SX1276_Datasheet.pdf)",
        "examples: [SX1276](https://torob.com/p/da4cd85b-79a3-446d-a624-2d0ed1aa34f6/%D9%85%D8%A7%DA%98%D9%88%D9%84-%D9%81%D8%B1%D8%B3%D8%AA%D9%86%D8%AF%D9%87-%D9%88%D8%A7%DB%8C%D8%B1%D9%84%D8%B3-sx1276-%D9%81%D8%B1%DA%A9%D8%A7%D9%86%D8%B3-868mhz/), [Sx1278](https://eshop.eca.ir/%D9%85%D8%A7%DA%98%D9%88%D9%84-%D9%87%D8%A7%DB%8C-esp-%D9%88-%D8%A7%DB%8C%D9%86%D8%AA%D8%B1%D9%86%D8%AA-%D8%A7%D8%B4%DB%8C%D8%A7/6137-%D9%85%D8%A7%DA%98%D9%88%D9%84-%D8%AA%D8%B1%D9%86%D8%B3%DB%8C%D9%88%D8%B1-%D9%88%D8%A7%DB%8C%D8%B1%D9%84%D8%B3-lora-ra02-%D8%AF%D8%A7%D8%B1%D8%A7%DB%8C-%DA%86%DB%8C%D9%BE-sx1278.html).",
    ],
    images=[
        "sx1276-1.jpg",
        "sx1276-2.jpg",
        "sx1276-3.jpg",
        "sx1276-4.jpg",
        "sx1276-5.jpg",
        "sx1276-6.jpg",
    ],
)


db_of_parts["whip-antenna"] = Part(
    info=[
        "433 MHz SMA whip antenna (small stubby or ~10–20 cm) or U.FL -> SMA pigtail if the module has a tiny U.FL connector.",
    ],
    images=[
        "whip-antenna.jpeg",
    ],
)

db_of_parts["ethernet-cable"] = Part(
    info=[
        "RJ-45, Cat5e or Cat6",
        "straight-through (normal) — NOT crossover",
    ],
    images=[
        "ethernet-cable.jpeg",
    ],
)

db_of_parts["5v-unmanaged-10-100-switch"] = Part(
    info=[
        "5V unmanaged 10/100 switch",
    ],
    images=[
        "5v-unmanaged-10-100-switch.jpg",
    ],
)

db_of_parts["template"] = Part(
    info=[
        "template",
    ],
    images=[
        "template.jpg",
    ],
)
