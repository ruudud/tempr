# Send temperature to Graphite

Uses connected USB TEMPer device to do room temperature reading, and optionally
sends data to a graphite instance.

Tested using [this device][], but others may work as long as they identify them
selves using a USB ID matching **0c45:7401 Microdia** (check using `lsusb`).

## Using
```
$ ./tempr.py -h
usage: tempr.py [-h] [--no-send] [--host host] [--port port] [--metric metric]

Send temperature to graphite using TEMPer device.

optional arguments:
    -h, --help       show this help message and exit
    --no-send        do not send reading to graphite server (default: Do send)
    --host host      address of graphite server (default: localhost)
    --port port      port of graphite server (default: 2003)
    --metric metric  graphite metric name (default: local.temp)
```

Do reading and send to remote graphite server (**NOTE** `sudo`):
```
$ sudo ./tempr.py --host graphite.local --metric kitchen.temp
Got temperature reading of 27.6°C
Sending to Graphite on graphite.local:2003...
```

## Requirements
**pyusb** (libusb bindings for Python) is required for reading temperatures.
Use `pip install`, or install equivalent system package, eg. `apt-get install
python-usb` on Debian/Ubuntu.


## Caveats
Escalated privileges are often required for communicating with the USB device.
To easen up this requirement, create `/etc/udev/rules.d/99-tempsensor.rules`
with the following content:

```
SUBSYSTEMS=="usb", ACTION=="add", ATTRS{idVendor}=="0c45", ATTRS{idProduct}=="7401", MODE="666"
```

  


## Credits
Magic values stolen from https://github.com/padelt/temper-python


## License
MIT


[this device]: http://www.dx.com/p/temper-usb-thermometer-temperature-recorder-for-pc-laptop-81105
