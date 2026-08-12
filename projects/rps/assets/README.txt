Assets folder — place optional images and sounds here

Files the app will look for (optional):
- RPS.icns           (macOS icon file for the .app)
- rock.png           (button image for Rock, recommended ~128x128 PNG)
- paper.png          (button image for Paper)
- scissors.png       (button image for Scissors)
- win.wav            (sound played when player wins)
- lose.wav           (sound played when computer wins)
- tie.wav            (sound played for ties)

Create a .icns file (example):
1. Make a folder called MyIcon.iconset and put PNGs named like:
   icon_16x16.png, icon_32x32.png, icon_128x128.png, icon_256x256.png, icon_512x512.png
2. Run:
   iconutil -c icns MyIcon.iconset
3. Move the produced MyIcon.icns to assets/RPS.icns

Notes
- Button images should be square PNG with transparency for best appearance.
- Sound files should be short WAV files; macOS 'afplay' is used by the app to play them.
