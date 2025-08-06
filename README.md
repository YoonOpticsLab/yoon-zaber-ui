## Scanning WFS based on Zaber motors

This Python UI mainly creates Zaber PVT (position,velocity,time) sequences that are then sent to Zaber controller for execution. Also has (Ximea) camera preview windows with rudimentary settings (exposure & gain), and named file saving.
Depending on hardware, movements may be simple linear (or rotational), or trigonometric.

PVT sequences contain digital out (DO) commands that are sent to the Ximea camera to trigger.

One difficulty is the Zaber digital output is not TTL. They have an app note describing conversion with the output signal pulled up to 5V then sent into a 74LSO4 inverter/buffer.

Ximea -S7 I/O Cable pinout: (determined empirically)
- 1/brown/ground
- 2/blue/Input
- 3/Black/Output

For our setup:
- black alligator clip (zaber ground) -> ximea ground (brown)
- red alligator clip (zaber signal) -> ximea input (blue)
