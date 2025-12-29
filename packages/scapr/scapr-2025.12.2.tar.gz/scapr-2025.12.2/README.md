# scapr

![PyPI - Version](https://img.shields.io/pypi/v/scapr)

## Screen Capture in Python

A script that uses Pillow's ImageGrab to capture screenshots.

## Usage

```shell
usage: scapr [-h] [--auto] [--seconds SLEEP_SEC] [--count STOP_COUNT]
             [--folder OUTPUT_DIR] [--region REGION_BOX] [--flat]

Command-line utility to capture screenshots.

options:
  -h, --help           show this help message and exit
  --auto               Do not prompt to start capturing screenshots. Begin
                       right away.
  --seconds SLEEP_SEC  Number of seconds to pause between screenshots.
  --count STOP_COUNT   Number of screenshots to take before stopping.
  --folder OUTPUT_DIR  Name of folder for saving captured screenshots.
  --region REGION_BOX  Region to capture (instead of full screen). Specify box
                       coordinates, separated by commas (no spaces between),
                       as 'x1,y1,x2,y2' where x1 and y1 are the left-top pixel
                       coordinates, and x2 and y2 are the right-bottom pixel
                       coordinates. Example: '--region 100,100,600,600' to
                       capture a 500 x 500 image starting at 100 pixels from
                       top and left.
  --flat               Do not create a sub-folder for each capture session (a
                       'flat' output folder structure).
```

## Reference

[Pillow](https://pypi.org/project/Pillow/)

Pillow - [ImageGrab](https://pillow.readthedocs.io/en/stable/reference/ImageGrab.html)

Python - [KeyboardInterrupt](https://docs.python.org/3/library/exceptions.html#KeyboardInterrupt)

