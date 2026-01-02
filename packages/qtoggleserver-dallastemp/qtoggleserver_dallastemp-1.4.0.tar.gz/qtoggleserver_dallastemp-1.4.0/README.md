## About

This is an addon for [qToggleServer](https://github.com/qtoggle/qtoggleserver).

It provides Dallas DS18B20 temperature sensor support for qToggleServer.


## Install

Install using pip:

    pip install qtoggleserver-dallastemp


## Usage

##### `qtoggleserver.conf:`
``` ini
...
peripherals = [
    ...
    {
        driver = "qtoggleserver.dallastemp.DallasTemperatureSensor"
        name = "livingroom"         # a name of your choice
        address = "28-00000B247706" # the 1-wire address 
    }
    ...
]
...
```
