import subprocess
import signal
import json
import sys
import os

def fix(input_file=None, output_file=None, preset="ultrafast"):
    try:
        if not input_file:
            return "input file is not given"
            sys.exit(1)
        # Default output
        if not output_file:
            output_file = f"fixed_{os.path.basename(input_file)}"
            output_file = f"{os.path.dirname(input_file)}/{output_file}"

        # Preset validation
        vps = ["ultrafast","superfast","veryfast","faster","fast","medium","slow","slower","veryslow","placebo"]
        if preset not in vps:
            return f"ERR: Given preset is not valid. Valid presets: {vps}"
            sys.exit(1)
        # Check paths
        if not os.path.isfile(input_file):
            return "ERR: Input file does not exist"
            sys.exit(1)
        if not os.path.isdir(os.path.dirname(output_file)):
            return "ERR: Output folder does not exist"
            sys.exit(1)
        if not output_file.endswith(".mp4"):
            if not os.path.exists(output_file):
                if os.path.isfile(output_file):
                    return "ERR: Output folder does not exist"
                    sys.exit(1)
                return "ERR: Output folder does not exist"
                sys.exit(1)
            if not os.path.isfile(output_file):
                output_file = os.path.join(output_file,f"fixed_{os.path.basename(input_file)}")
        # Start ffmpeg process
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
        return "OK"

    except KeyboardInterrupt:
        prc.stdin.write(b"q\n")
        prc.stdin.flush()
        prc.wait()
        return "Re-Encoding stopped cleanly"
    except Exception as e:
        return f"ERR: {e}"

def analyze(file_path):
    try:
        if not os.path.isfile(file_path):
            return "File not found"
        if not file_path.endswith(".mp4"):
            return "File is not mp4"
        issues = []
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


        if not streams:
            issues.append("No audio or video streams found")

        video_streams = [s for s in streams if s.get("codec_type") == "video"]
        audio_streams = [s for s in streams if s.get("codec_type") == "audio"]

        if not video_streams:
            issues.append("No video stream found")
        if not audio_streams:
            issues.append("No audio stream found")


        for s in streams:
            codec = s.get("codec_name")
            if not codec:
                issues.append(f"{s.get('codec_type')} stream missing codec")
            if "duration" not in s:
                issues.append(f"{s.get('codec_type')} stream missing duration")


        if "duration" not in format_info:
            issues.append("General format missing duration")
        if "format_name" not in format_info:
            issues.append("Format name missing")


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

            if "time=" in line:
                try:
                    time_str = [part for part in line.split() if part.startswith("time=")][0].split("=")[1]
                    h, m, s = time_str.split(":")
                    seconds = float(h)*3600 + float(m)*60 + float(s)
                    if total_duration:
                        percent = (seconds / total_duration) * 100
                        sys.stdout.write(f"\rAnalyzing : {percent:.2f}% • Hit Ctrl+C to stop")
                        sys.stdout.flush()
                except:
                    pass

            if "error" in line.lower() or "invalid" in line.lower() or "missing" in line.lower():
                issues.append(f"Decoding error : {line}")

        process.wait()
        sys.stdout.write("\n")

        if process.returncode != 0:
            issues.append("FFmpeg returned an error during decoding")

        if video_streams and audio_streams:
            try:
                v_duration = float(video_streams[0].get("duration", 0))
                a_duration = float(audio_streams[0].get("duration", 0))
                if abs(v_duration - a_duration) > 1.0:  # more than 1 second
                    issues.append("Video and audio durations mismatch")
            except:
                issues.append("Failed to compare audio/video durations")

        return issues
    except Exception as e:
        return f"CRITICAL ERROR : {e}"
    except KeyboardInterrupt:
        return "Stopping analysis"
        sys.exit(1)
