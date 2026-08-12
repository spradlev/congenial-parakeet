Platypus instructions — Wrap the RPS launcher into a macOS app

1) Install Platypus
   - Download from https://sveinbjorn.org/platypus and install (free).  

2) Prepare the project
   - Ensure the project folder is at ~/projects/rps or wherever you keep it.
   - Confirm run_rps.sh exists at projects/rps/run_rps.sh and is executable.

3) Create a new Platypus app
   - Open Platypus -> New App.
   - Script Type: /bin/sh (or use the bundled Shell option)
   - Script: choose the run_rps.sh file in the project (Projects/rps/run_rps.sh)
   - Interface: None (the script launches a GUI app — choose "None" so Platypus doesn't show a separate UI)
   - Output: None
   - Accepts dropped items: No
   - Remain running after execution: No
   - Name: RPS
   - Identifier: com.yourname.rps (optional)
   - App Icon: Optional — pick an .icns if you have one
   - Destination: choose "Applications Folder" and select the user Applications folder (~/Applications) to avoid managed-device restrictions.

4) Build
   - Click Create App. Platypus will generate RPS.app. Move it to ~/Applications if not already placed there.

5) Run
   - Double-click RPS.app in Finder or run from Terminal: open "~/Applications/RPS.app"
   - On first run Platypus may prompt about where Python is; the embedded run_rps.sh looks for python.org's python at /usr/local/bin/python3, falls back to PATH, and uses a .venv/python if present.

Notes and troubleshooting
- If the app fails to start, run the script directly from Terminal to see stdout/stderr:
    cd ~/projects/rps
    ./run_rps.sh
- If Python/Tk isn't cooperating, install the official python.org installer from https://www.python.org/downloads/mac-osx/ and reinstall. Platypus just launches the script; it doesn't bundle Python unless you ask it to.
- To update the app after code changes, re-run Platypus Create or replace the script inside the existing app bundle.
