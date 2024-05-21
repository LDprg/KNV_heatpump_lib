# KNV_heatpump_lib
A reverse engineered python libary for accessing KNV heatpumps. Its primary for [this](https://github.com/LDprg/KNV_heatpump_ha) homeassistant integration.

## Todo
- Make serial number not hardcoded

## Disclaimer
!! USE AT YOU OWN RISK !!
I am not responsible for any damage done by the usage of this library. So use it carefully and don't change values you don't understand! It is absolutely possible to damage or reduce the lifetime of your heatpump with the change of some values in a non controlled way.

## Status
In general this library should work now fine. However it is only tested on my KNV heatpump and specifically exposes values I use. The communication starts with a serial number which is currently hardcoded, so it is possible that it won't work on other heatpumps. Fell free to test it and make suggesstions or even better a pr.
