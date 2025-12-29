#!/usr/bin/env python3

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

from PIL import ImageGrab
from rich import print as rprint

#  Using calver (YYYY.0M.MICRO).
__version__ = "2025.12.2"

app_title = f"scapr - Screen Capture utility (v{__version__})"


class AppOptions(NamedTuple):
    out_path: Path
    sleep_seconds: int
    stop_count: int
    auto: bool
    region: tuple
    do_flat: bool = False
    do_log: bool = False


DEFAULT_SECONDS = 3

MAX_SECONDS = 60 * 60
#  Maximum interval between screenshots. An hour is already unlikely
#  to be useful.


def get_args(arglist=None):
    ap = argparse.ArgumentParser(
        description="Command-line utility to capture screenshots."
    )

    ap.add_argument(
        "--auto",
        dest="auto",
        action="store_true",
        help="Do not prompt to start capturing screenshots. Begin right away.",
    )

    ap.add_argument(
        "--seconds",
        dest="sleep_sec",
        type=int,
        action="store",
        help="Number of seconds to pause between screenshots.",
    )

    ap.add_argument(
        "--count",
        dest="stop_count",
        type=int,
        action="store",
        help="Number of screenshots to take before stopping.",
    )

    ap.add_argument(
        "--folder",
        dest="output_dir",
        type=str,
        action="store",
        help="Name of folder for saving captured screenshots. ",
    )

    ap.add_argument(
        "--region",
        dest="region_box",
        type=str,
        action="store",
        help="Region to capture (instead of full screen). "
        "Specify box coordinates, separated by commas (no spaces between), "
        "as 'x1,y1,x2,y2' where x1 and y1 are the left-top pixel "
        "coordinates, and x2 and y2 are the right-bottom pixel "
        "coordinates. Example: '--region 100,100,600,600' to capture a "
        "500 x 500 image starting at 100 pixels from top and left.",
    )

    ap.add_argument(
        "--flat",
        dest="do_flat",
        action="store_true",
        help="Do not create a sub-folder for each capture session "
        "(a 'flat' output folder structure).",
    )

    ap.add_argument(
        "--do-log",
        dest="do_log",
        action="store_true",
        help="Optional. Write a text log file to the same folder as the screenshots.",
    )

    return ap.parse_args(arglist)


def get_opts(arglist=None):  # noqa: PLR0912
    args = get_args(arglist)

    if args.output_dir is None:
        out_path = Path.home() / "Pictures" / "Screenshots"
        if not out_path.exists():
            out_path = Path.home() / "Pictures"
            if not out_path.exists():
                out_path = Path.cwd()
    else:
        out_path = Path(args.output_dir).expanduser().resolve()
        if not (out_path.exists() and out_path.is_dir()):
            sys.stderr.write(f"\nERROR: Folder not found: '{out_path}'\n")
            sys.exit(1)

    if args.sleep_sec is None:
        sleep_seconds = DEFAULT_SECONDS
    else:
        sleep_seconds = args.sleep_sec
        if sleep_seconds < 1 or sleep_seconds > MAX_SECONDS:
            sleep_seconds = DEFAULT_SECONDS

    region = None
    if args.region_box is not None:
        reg_err = ""
        a = args.region_box.split(",")
        expect_n_items = 4
        if len(a) == expect_n_items:
            b = [int(s.strip()) for s in a]
            if (b[2] < b[0]) or (b[3] < b[1]):
                reg_err = "x2 and y2 must be greater than x1 and y1 respectively."
            else:
                region = (b[0], b[1], b[2], b[3])
        else:
            reg_err = "Expecting four integers separated by commas (no spaces)."

        if len(reg_err) > 0:
            sys.stderr.write(
                f"\nERROR: Invalid region coordinates '{args.region_box}'.\n"
            )
            sys.stderr.write(f"{reg_err}\n")
            sys.exit(1)

    return AppOptions(
        out_path,
        sleep_seconds,
        args.stop_count,
        args.auto,
        region,
        args.do_flat,
        args.do_log,
    )


def write_log(log_file: Path | None, msg: str) -> None:
    if log_file:
        msg = f"[{datetime.now():%Y%m%d_%H%M%S_%f}] {msg}"
        with log_file.open("a") as f:
            f.write(f"{msg}\n")


def print_log(log_file: Path | None, msg: str) -> None:
    rprint(msg)
    write_log(log_file, msg)


def main(arglist=None):  # noqa: PLR0912
    rprint(f"\n{app_title}\n")

    opts = get_opts(arglist)

    rprint('  Run "scap.py -h" (or --help) to see available options.\n')

    if opts.do_flat:
        session_out_path = opts.out_path
    else:
        session_dt = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_out_path = opts.out_path / f"scapr_{session_dt}"
        if not session_out_path.exists():
            session_out_path.mkdir()

    log_file = session_out_path / "scapr-log.txt" if opts.do_log else None

    write_log(log_file, app_title)

    if opts.region is None:
        print_log(log_file, "Capture full screen.")
    else:
        print_log(log_file, f"Capture screen region {opts.region}.")

    if opts.stop_count is None:
        counter = -1
    else:
        counter = opts.stop_count
        rprint(f"Number of screenshots to take is {counter}.")

    rprint(f"Number of seconds between screenshots is {opts.sleep_seconds}.")
    rprint(f"Screenshots will be saved to '{opts.out_path}'.")

    if not opts.auto:
        answer = input("\nContinue [Y,n]? ")
        if answer.lower() not in ["y", ""]:
            sys.exit(0)

    while counter != 0:
        remaining = f" ({counter} remaining)" if counter > 0 else ""

        rprint(f"\nCapturing screen{remaining}. Press [Ctrl]+[C] to stop.\n")

        counter -= 1

        try:
            dt = datetime.now().strftime("%y%m%d_%H%M%S")
            save_path = session_out_path / f"screenshot-{dt}.jpg"

            try:
                img = ImageGrab.grab(opts.region)
            except OSError:
                rprint(
                    "[red]ERROR: Failed to capture image.[/red]\n\nIf "
                    "running on Ubuntu, installing gnome-screenshot may fix "
                    "this problem.\n\n"
                    "[green]sudo apt install gnome-screenshot[/green]\n\n"
                    "Note: When using gnome-screenshot there is a "
                    "screen flash and shutter-click sound with each "
                    "screenshot.\n"
                )
                write_log(log_file, "Failed to capture image.")
                return 1

            #  If ImageGrab.grab() uses gnome-screenshot (a work-around for
            #  Wayland), it will return a PIL.Image.Image object with mode
            # "RGBA". Convert to "RGB" to avoid an error when saving as JPEG.
            if img.mode != "RGB":
                img = img.convert("RGB")

            write_log(log_file, f"Save '{save_path}'")
            img.save(save_path)
            time.sleep(opts.sleep_seconds)

        except KeyboardInterrupt:
            rprint("\n\nStopped.\n")
            return 0
    return None


if __name__ == "__main__":
    sys.exit(main())
