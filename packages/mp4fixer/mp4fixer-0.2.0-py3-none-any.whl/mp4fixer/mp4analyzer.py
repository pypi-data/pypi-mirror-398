from colorama import init, Fore, Style
from lolpython import lol_py
import subprocess
import pyfiglet
import signal
import json
import sys
import os

init(autoreset=True)

b = Style.BRIGHT
gr = Fore.GREEN+b
bl = Fore.BLUE+b
yl = Fore.YELLOW+b
cy = Fore.CYAN+b
rd = Fore.RED+b

def handle(a,b):
    print()
    print(Fore.YELLOW+"[•] Stopping analyzing ...")
    sys.exit(1)

def analyze_mp4(file_path):
    issues = []
    # --- 2. FFprobe metadata ---
    try:
        cmd = [
            os.path.join(os.path.dirname(__file__),"./fp"),
            "-v", "error",
            "-show_format",
            "-show_streams",
            "-print_format", "json",
            file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
    except Exception as e:
        issues.append(f"FFprobe failed : {e}")
        return issues

    streams = data.get("streams", [])
    format_info = data.get("format", {})

    # --- 3. Check for missing tracks ---
    if not streams:
        issues.append("No audio or video streams found")

    video_streams = [s for s in streams if s.get("codec_type") == "video"]
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]

    if not video_streams:
        issues.append("No video stream found")
    if not audio_streams:
        issues.append("No audio stream found")

    # --- 4. Check duration and codec ---
    for s in streams:
        codec = s.get("codec_name")
        if not codec:
            issues.append(f"{s.get('codec_type')} stream missing codec")
        if "duration" not in s:
            issues.append(f"{s.get('codec_type')} stream missing duration")

    # --- 5. Check format info ---
    if "duration" not in format_info:
        issues.append("General format missing duration")
    if "format_name" not in format_info:
        issues.append("Format name missing")

    # --- 6. FFmpeg decoding errors with progress ---
    total_duration = float(format_info.get("duration", 0))
    if total_duration == 0:
        issues.append("Cannot determine total duration for progress")
        total_duration = None

    ffmpeg_cmd = [os.path.join(os.path.dirname(__file__),"./mf"), "-i", file_path, "-f", "null", "-"]
    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    while True:
        line = process.stdout.readline()
        if not line:
            break
        line = line.strip()

        # Show progress
        if "time=" in line:
            try:
                time_str = [part for part in line.split() if part.startswith("time=")][0].split("=")[1]
                h, m, s = time_str.split(":")
                seconds = float(h)*3600 + float(m)*60 + float(s)
                if total_duration:
                    percent = (seconds / total_duration) * 100
                    sys.stdout.write(yl+f"\r[•] Analyzing : {percent:.2f}% • Hit Ctrl+C to stop")
                    sys.stdout.flush()
            except:
                pass

        # Capture FFmpeg errors
        if "error" in line.lower() or "invalid" in line.lower() or "missing" in line.lower():
            issues.append(f"[~] Decoding error : {line}")

    process.wait()
    sys.stdout.write("\n")

    if process.returncode != 0:
        issues.append("FFmpeg returned an error during decoding")

    # --- 7. Advanced: check duration mismatch ---
    if video_streams and audio_streams:
        try:
            v_duration = float(video_streams[0].get("duration", 0))
            a_duration = float(audio_streams[0].get("duration", 0))
            if abs(v_duration - a_duration) > 1.0:  # more than 1 second
                issues.append("Video and audio durations mismatch")
        except:
            issues.append("Failed to compare audio/video durations")

    return issues

signal.signal(signal.SIGINT, handle)

def main():
    try:
        ascii_art = pyfiglet.figlet_format("MP4-Fixer")
        lol_py(ascii_art)
        print()
        lol_py("MP4 analyzer | Created by Abdul Moeez")
        print()
        if len(sys.argv) < 2:
            print(bl+"[USAGE] mp4analyzer <file-path>")
            sys.exit(1)
        file_path = sys.argv[1]
        if not file_path.endswith(".mp4"):
            print(rd+"[!] Given file is not .mp4")
            sys.exit(1)
        if not os.path.isfile(file_path):
            # 1
            print(rd+"[!] File not found")
            sys.exit(1)
        problems = analyze_mp4(file_path)
        if problems:
            print()
            print(Fore.CYAN+"Problems detected : ")
            print()
            for p in problems:
                print(bl+"-", cy+p)
        else:
            print(gr+"No problems detected. File looks healthy.")
    except Exception as s:
        print(rd+f"[!] ERROR : {e}")
        sys.exit(1)
