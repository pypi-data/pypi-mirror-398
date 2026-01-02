from lolpython import lol_py
import pyfiglet
from colorama import init, Fore, Style
import subprocess
import sys
import os
import argparse

init(autoreset=True)

def fix(input_file, output_file, preset):
    prc = None
    try:
        vps = [
            "ultrafast","superfast","veryfast","faster","fast",
            "medium","slow","slower","veryslow","placebo"
        ]
        if preset not in vps:
            print(Fore.RED+Style.BRIGHT+f"[!] ERROR: Invalid preset. Valid: {vps}")
            sys.exit(1)
        print(Fore.BLUE+Style.BRIGHT+f"[•] Set preset to {preset}")
        prc = subprocess.Popen([
            os.path.join(os.path.dirname(__file__),"mf"),
            "-hide_banner",         # hides copyright/info
            "-loglevel", "warning", # only warnings & errors
            "-stats",               # show progress line
            "-i", input_file,
            "-c:v", "libx264",
            "-preset", preset,
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            "-y",
            output_file
            ], stdin=subprocess.PIPE)

        prc.wait()
        print(Style.BRIGHT+Fore.GREEN+"[✓] Your file is fixed successfully!")
        sys.exit(0)

    except KeyboardInterrupt:
        if prc and prc.stdin:
            prc.stdin.write(b"q\n")
            prc.stdin.flush()
            prc.wait()
        print(Style.BRIGHT+Fore.BLUE+"[~] Re-Encoding stopped cleanly")
        sys.exit(0)

    except Exception as e:
        print(Style.BRIGHT+Fore.RED+f"[!] ERROR: {e}")
        sys.exit(1)


def main():
    try:
        ascii_art = pyfiglet.figlet_format("MP4-Fixer")
        lol_py(ascii_art)
        lol_py("Fix any MP4 file | Created by Abdul Moeez")
        print()

        parser = argparse.ArgumentParser(description="MP4 Fixer")
        parser.add_argument("inp", type=str, help="Input file path")
        parser.add_argument("--output_path", type=str, default=None, help="Output file path")
        parser.add_argument("--preset", type=str, default="ultrafast", help="FFmpeg preset")
        args = parser.parse_args()

        if not os.path.isfile(args.inp):
            print(Fore.RED+Style.BRIGHT+"[#] Input file not found.")
            sys.exit(1)

        if args.output_path is None:
            pop = os.path.dirname(args.inp)
            fn = os.path.basename(args.inp)
            args.output_path = f"{pop}/fixed_{fn}"
            print(Fore.BLUE+Style.BRIGHT+f"[•] Using default output path: {args.output_path}")

        if not os.path.isdir(os.path.dirname(args.output_path)):
            print(Fore.RED+Style.BRIGHT+"[!] Output path folder is not exists")
            sys.exit(1)

        fix(args.inp, args.output_path, args.preset)

    except Exception as e:
        print(Style.BRIGHT+Fore.RED+f"[!] ERROR: {e}")
