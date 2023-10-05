# Elegoo Neptune Thumbnails for PrusaSlicer

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

PrusaSlicer Post-Processing script to add thumbnails images into gcode files for Elegoo Neptune printers (only tested for 3 Pro).

For now, this package just converts the thumbnail that PrusaSlicer bakes into the gcode file into the format that is read by the Neptune printers.

<img src="images/main.jpg" width='275'>

## Installation

- Download the [latest release](https://github.com/TheJMaster28/ElegooNeptuneThumbnailPrusa/releases)
- Extract the zip to location where the exe can be executed


## How to Setup PrusaSlicer for Post-Process Scripts

> For a more detailed guide [here](https://github.com/TheJMaster28/ElegooNeptuneThumbnailPrusa/wiki/Setup-Post%E2%80%90Process-Scripts-in-PrusaSlicer)

- Go to 'Printer Settings' and change the 'G-code thumbnails' setting to be: `200x200`
  - The script defaults to finding a 200x200 thumbnail, but can take any thumbnail size with the argument `--img_size`. Make sure it is big enough to still have a quality preview image.   
- Go to 'Print Settings' and under the 'Post-processing scripts' and put the path to the exe: `"C:\ElegooNeptuneThumbnailPrusa\thumbnail.exe";`

PrusaSlicer should now run the exe when you export the gcode.

## Running from the script

If you do not want to run the exe, you can also run the script through Python. Clone the repo and change the settings for 'Post-processing scripts' to your path to Python and the path to the thumbnail.py script:

`"C:\Program Files\Python311\python.exe" "C:\ElegooNeptuneThumbnailPrusa\thumbnail.py";`

If you want to hide the terminal at execution, use `pythonw.exe` instead of python.exe:

`"C:\Program Files\Python311\pythonw.exe" "C:\ElegooNeptuneThumbnailPrusa\thumbnail.py";`
## Compatibility

Works with these printers:

- NEPTUNE 3 PRO
- NEPTUNE 3 PLUS
- NEPTUNE 3 MAX
- NEPTUNE 4
- NEPTUNE 4 PRO
- NEPTUNE 4 PLUS
- NEPTUNE 4 MAX

Use the `--old_printer` argument for these printers:

- NEPTUNE 2
- NEPTUNE 2D
- NEPTUNE 2S
- NEPTUNE X


Tested with PrusaSlicer 2.6.0 and 2.6.1

I would also believe that this package should also work on older version of PrusaSlicer.

Apple silicone will not work on the release. In order to run, you must run the script through an x86 python or else the dlls wil not work. You can does this by installing the x86 Homebrew and Rosetta 2.


## Arguments

| Argument             | Description                                                                                             |
| -------------------- | ------------------------------------------------------------------------------------------------------- |
| `--old_printer`      | To generate thumbnails for Neptune 2 series printers and older                                          |
| `--img_size 200x200` | Image size to look for in the Gcode file. This must match to what is in the 'G-code thumbnails' setting |

To add arguments to the script, make sure to wrap them around double quotes "" to have them phrase properly like this:
`"C:\ElegooNeptuneThumbnailPrusa\thumbnail.exe" "--img_size" "300x300";`


## Contribution

This repository is based on [Molodos/ElegooNeptuneThumbnails](https://github.com/Molodos/ElegooNeptuneThumbnails) and [sigathi/ElegooN3Thumbnail](https://github.com/sigathi/ElegooN3Thumbnail), therefore
released under the **AGPL v3** license.
