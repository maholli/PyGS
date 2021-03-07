# PyGS
Simple wifi ground station running circuitpython 

<img src="https://user-images.githubusercontent.com/29153441/110256112-fbe07c80-7f4b-11eb-9c6c-1eda8e213f39.png" width="600">

## Example Hardware Setup
As opposed to using an antenna+rotator for receiving satellites moving across the sky, another option is to use multiple antennas like this:
<img src="https://user-images.githubusercontent.com/29153441/110256188-62fe3100-7f4c-11eb-9c8b-7ef9e2acd3e6.png" width="700">

attached to multiple low-cost radios.

# Detailed Instructions
To replicate the above example, you'll need the following:

## Items Required
- [ ] 1ea [FeatherS2](https://www.adafruit.com/product/4769)
- [ ] 3ea RFM9x Featherwing [900 MHz](https://www.adafruit.com/product/3231) or [433MHz](https://www.adafruit.com/product/3232)
- [ ] 3ea edge-mount [SMA connectors ](https://www.adafruit.com/product/1865)
- [ ] 4ea [Stacking headers](https://www.adafruit.com/product/2830)
- [ ] Directional antennas for each of your radios. [Log Periodic](https://www.wa5vjb.com/products1.html) antennas work well. The LP400 covers 433MHz and 915MHz.
- [ ] Coax cables for each radio+antenna. Each cable should be about 450mm.
- [ ] Battery for the FeatherS2. [This would work well ](https://www.adafruit.com/product/353)
- [ ] Husky storage bin (overkill but convenient) [from Home Depot](https://www.homedepot.com/p/Husky-20-Gal-Professional-Duty-Waterproof-Storage-Container-with-Hinged-Lid-in-Black-246841/312898941)
- [ ] OPTIONAL: 2ea 100kΩ resistors (0603 work well) for battery voltage monitor

## Hardware Setup
### Antennas
1. 3D print the antenna spacer: 
2. Connect your coax and tape at the base. Ensure the coax runs on top of the center trace of the LP antenna.

### Radios & MCU
The hardware from Adafruit needs to be assembled as described below. Keep in mind you can always adapt the pin definitions in `radio_helpers.py` to meet a different hardware configuration. 
1. Assemble the radio boards with stacking headers and your edge-mount SMA connectors. Use [Adafruit's guide](https://learn.adafruit.com/radio-featherwing/assembly) as a reference.
2. Solder wires for the radio CS, RST, and IRQ signals as described below:
<img src="https://user-images.githubusercontent.com/29153441/110256995-b1adca00-7f50-11eb-8c08-e22b6adfd10c.png" width="500">

| Radio     |    CS     |   RST     |   IRQ     |
|:-----:    |:-------:  |:-------:  |:-------:  |
|   1       |   "C"     |   "B"     | See pic   |
|   2       |   "E"     |   "D"     | See pic   |
|   3       | See pic   | See pic   | See pic   | 

3. Now assemble the FeatherS2 with stacking headers
4. In order to monitor battery voltage, we need to add a voltage divider. Solder your two 100kΩ resistors as shown below.

![image](https://user-images.githubusercontent.com/29153441/110257961-12d79c80-7f55-11eb-8bbd-51a03e2a1d0d.png)

### Software
1. Update the FeatherS2 firmware using the .UF2 file in this repo's firmware directory. This can be done by putting the board into bootloader mode (plug into computer, click reset button, then click boot button) and then dragging the UF2 file onto the `FeatherS2` drive that should mount shortly. It will likely have an error while copying the file. Don't worry about it.
2. Unplug and plug the board back into your computer
3. Copy the contents of the `code` directory from this repo to the CIRCUITPY drive
4. On the CIRCUITPY drive, open the `RENAME_ME.py` file in the lib folder and update the mqtt broker info and save
5. Now rename the `RENAME_ME.py` file to: `secrets.py`
6. Open `code.py` and edit line 32 to your respective WiFi SSID
