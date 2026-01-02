**MP4Fixer**

---

MP4Fixer is a simple and powerful tool that repairs broken / corrupted MP4 videos by re-encoding them using FFmpeg.
It can successfully fix 70% – 90% of damaged MP4 files, depending on corruption level.
It uses:
libx264 for video
aac for audio
and applies -movflags +faststart so even partially processed files are more playable.

---

**What's new in 0.2.0!**

A powerful analyzer is added contain a cli command and a new python function thats detailed in CLI usage and Python usage.

---

✨ Features
Fix broken & unplayable MP4 files
Simple CLI usage
Python API available
Safe graceful stop using Ctrl + C
Supports all FFmpeg speed presets
Works on Linux, Termux, Windows, and macOS
⚙️ Requirements
Python 3.7+
FFmpeg binary
Either provide a binary named mf inside the package folder
OR modify to use system ffmpeg
**New of 0.2.0**
Analyzer give issues report with your mp4 file.

---

📦 Installation

This is not require to install ffmpeg because that was inbuilt inside it.

pip install mp4fixer

---

🚀 CLI Usage


**Basic usage**


mp4fixer <input-file>


With output path

mp4fixer <input-file> --output_path <path>


With preset
Copy code

mp4fixer <input-file> --output <path> --preset medium

if you not provide output path so that automatically make fixed file in same folder where input file.
if you not provide preset so that automatically set preset to ultrafast.

mp4analyzer <input-file>

This is show problems with your mp4 file.

---

🎛️ Supported Presets

ultrafast
superfast
veryfast
faster
fast
medium
slow
slower
veryslow
placebo
ultrafast = fastest, larger file
veryslow = slow but best compression
Default = ultrafast

---

**Python Usage**


from mp4fixer import fix

print(
    fix(
        input_file="video.mp4",
        output_file="fixed_video.mp4",
        preset="fast"
    )
)

Returns:
"OK" if success
"ERR: message" if something failed
"Re-Encoding stopped cleanly" if cancelled
🛑 Stopping Encoding (Ctrl + C)
If you press Ctrl + C, MP4Fixer:
Sends q to FFmpeg
FFmpeg closes cleanly
Output file remains playable
No broken partial files 🎉

from mp4fixer import analyze

print(analyze("video.mp4"))

Returns

issues in list form like ["","",""]
if no issue mean your file is healthy
"CRITICAL ERROR : <err>" internal error thats very low chance.
"Stopping analysis" when you hit ctrl+c

---
📌 Notes
If no output path is given, output is created in same folder:

fixed_<filename>.mp4
Input must exist
Output folder must exist
Preset must be valid

---

**👑 Author**

             Abdul Moeez
