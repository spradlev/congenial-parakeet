Rock Paper Scissors (RPS)
=========================

Plan summary
------------
This small learning project provides a GUI rock-paper-scissors game with these features:

- Play vs a computer that selects moves randomly (existing rps.py logic)
- Tkinter GUI (rps_gui.py) with buttons, keyboard shortcuts, and live score
- Persistent state saved to ~/Library/Application Support/RPS/state.json
- Optional assets support (icons, button images, sounds) in assets/
- Build as a native macOS .app via py2app (build_py2app.sh)
- Guidance for codesigning, notarization, and DMG packaging

Quick run (developer)
---------------------
1. Ensure python.org Python 3 is installed (recommended for Tk support).
2. From project directory run:
   python3 rps_gui.py

Build a native macOS .app (py2app)
---------------------------------
1. Ensure python.org Python 3 is active in your PATH.
2. Make the build script executable and run it:
   chmod +x build_py2app.sh
   ./build_py2app.sh
3. The built app will be at ~/Documents/RPS.app

Adding an app icon and assets
----------------------------
- Place a Mac .icns file at assets/RPS.icns
- Optionally add images: assets/rock.png, assets/paper.png, assets/scissors.png
- Optionally add sounds: assets/win.wav, assets/lose.wav, assets/tie.wav

See assets/README.txt for commands to create an .icns from PNGs.

Persistence and logs
--------------------
State (scores and recent history) is saved automatically to:
  ~/Library/Application Support/RPS/state.json

You can also use Save Log in the app to export a text log.

Distribution notes (codesign & notarize)
---------------------------------------
- To distribute outside your machine you'll need to codesign and notarize the app.
- Basic commands (replace placeholders):
  codesign --deep --force --options runtime --sign "Developer ID Application: YOUR NAME (TEAMID)" "~/Documents/RPS.app"
  xcrun altool --notarize-app -f "RPS.zip" --primary-bundle-id "com.example.rps" -u "APPLE_ID" -p "APP_SPECIFIC_PASSWORD"
- Notarization is beyond this README; see Apple's docs for details.

Development notes
-----------------
- The GUI tries to use macOS 'afplay' to play sounds if present.
- Button images are optional; the app falls back to text buttons.
- Keyboard: r/p/s to play, q to quit. Cmd+Q is mapped on macOS.

Want me to prepare a codesign + notarize helper script, add an .icns file, or produce a DMG automatically? Open an issue or ask here.
