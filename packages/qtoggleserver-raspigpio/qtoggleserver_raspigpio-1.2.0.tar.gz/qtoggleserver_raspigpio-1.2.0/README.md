## About

This is an addon for [qToggleServer](https://github.com/qtoggle/qtoggleserver).

It provides a qToggleServer driver for Raspberry Pi GPIOs based on the
[raspi-gpio](https://github.com/RPi-Distro/raspi-gpio) command.


## Install

Install using pip:

    pip install qtoggleserver-raspigpio


## Usage

##### `qtoggleserver.conf:`
``` ini
...
ports = [
    ...
    {
        driver = "qtoggleserver.raspigpio.GPIO"
        no = 18             # GPIO number
        def_value = true    # default value at startup
        def_output = true   # default output/input GPIO mode at startup
    }
    ...
]
...
```
