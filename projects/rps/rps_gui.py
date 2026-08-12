#!/usr/bin/env python3
"""Tkinter GUI wrapper for the rock-paper-scissors game with enhancements:
- persistent state (~Library/Application Support/RPS/state.json)
- keyboard shortcuts (r/p/s, q or Cmd+Q to quit)
- About dialog, Reset scores
- optional button images and sounds from ./assets
- small status animation on round result
"""
import json
import os
import subprocess
import shutil
import sys
import time
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

import rps


APP_ID = "com.example.rps"
STATE_DIR = Path.home() / "Library" / "Application Support" / "RPS"
STATE_FILE = STATE_DIR / "state.json"
ASSETS_DIR = Path(__file__).parent / "assets"


class RPSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Rock Paper Scissors")
        self.resizable(False, False)

        # Disable menubar in some bundled macOS contexts where Tk + NS menu creation crashes
        self._allow_menubar = True
        try:
            if sys.platform == 'darwin' and ('/Contents/MacOS/' in os.path.abspath(sys.executable) or getattr(sys, 'frozen', False)):
                self._allow_menubar = False
        except Exception:
            pass

        self.player_score = 0
        self.computer_score = 0
        self.rounds = 0
        self.history = []

        self._load_state()
        self._build_ui()
        self._bind_keys()

    # ----- state persistence -----
    def _ensure_state_dir(self):
        try:
            STATE_DIR.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    def _load_state(self):
        try:
            if STATE_FILE.exists():
                data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                self.player_score = int(data.get("player_score", 0))
                self.computer_score = int(data.get("computer_score", 0))
                self.rounds = int(data.get("rounds", 0))
                self.history = data.get("history", [])
                self.sounds_enabled = bool(data.get("sounds_enabled", True))
            else:
                self.history = []
                self.sounds_enabled = True
        except Exception:
            # if loading fails, start fresh
            self.player_score = 0
            self.computer_score = 0
            self.rounds = 0
            self.history = []
            self.sounds_enabled = True

    def _save_state(self):
        try:
            self._ensure_state_dir()
            data = {
                "player_score": self.player_score,
                "computer_score": self.computer_score,
                "rounds": self.rounds,
                "history": self.history[:1000],
                "sounds_enabled": bool(getattr(self, 'sounds_enabled', True)),
                "updated_at": time.time(),
            }
            STATE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    # ----- UI -----
    def _build_ui(self):
        # Menu - skip building on macOS bundle contexts known to crash
        if self._allow_menubar:
            try:
                menubar = tk.Menu(self)
                game_menu = tk.Menu(menubar, tearoff=0)
                game_menu.add_command(label="Save Log...", command=self.save_log)
                game_menu.add_command(label="Settings...", command=self.show_settings)
                game_menu.add_command(label="Reset Scores", command=self.reset_scores)
                game_menu.add_separator()
                game_menu.add_command(label="Quit", command=self.quit_app)
                menubar.add_cascade(label="Game", menu=game_menu)

                help_menu = tk.Menu(menubar, tearoff=0)
                help_menu.add_command(label="About", command=self.show_about)
                menubar.add_cascade(label="Help", menu=help_menu)
                self.config(menu=menubar)
            except Exception as e:
                # Log the menu-building error for debugging, but continue without a menubar
                try:
                    self._ensure_state_dir()
                    (STATE_DIR / 'menu_error.log').write_text(f"Menu build failed: {e}\n")
                except Exception:
                    pass
                tk.Label(self, text="(menu unavailable on this machine)").pack()
        else:
            # intentionally skip menu creation in certain macOS bundle contexts
            tk.Label(self, text="(menu disabled in bundled app)").pack()

        top = tk.Frame(self, padx=10, pady=10)
        top.pack()

        self.status_label = tk.Label(top, text="Make your move:", font=(None, 12), width=48)
        self.status_label.grid(row=0, column=0, columnspan=3, pady=(0, 8))

        # Load optional button images
        self.img_rock = self._load_image("rock.png")
        self.img_paper = self._load_image("paper.png")
        self.img_scissors = self._load_image("scissors.png")

        btn_rock = tk.Button(top, text="Rock", width=12, command=lambda: self.play('rock'))
        btn_paper = tk.Button(top, text="Paper", width=12, command=lambda: self.play('paper'))
        btn_scissors = tk.Button(top, text="Scissors", width=12, command=lambda: self.play('scissors'))

        if self.img_rock:
            btn_rock.config(image=self.img_rock, compound='top')
        if self.img_paper:
            btn_paper.config(image=self.img_paper, compound='top')
        if self.img_scissors:
            btn_scissors.config(image=self.img_scissors, compound='top')

        btn_rock.grid(row=1, column=0, padx=4)
        btn_paper.grid(row=1, column=1, padx=4)
        btn_scissors.grid(row=1, column=2, padx=4)

        score_frame = tk.Frame(self, padx=10, pady=6)
        score_frame.pack(fill='x')
        self.score_label = tk.Label(score_frame, text=self._score_text(), font=(None, 11))
        self.score_label.pack()

        hist_frame = tk.Frame(self, padx=10, pady=6)
        hist_frame.pack()
        tk.Label(hist_frame, text="Round history (most recent first):").pack(anchor='w')
        self.hist_listbox = tk.Listbox(hist_frame, width=60, height=10)
        self.hist_listbox.pack()
        self._refresh_history()

        ctrl_frame = tk.Frame(self, padx=10, pady=10)
        ctrl_frame.pack(fill='x')
        save_btn = tk.Button(ctrl_frame, text="Save Log", command=self.save_log)
        reset_btn = tk.Button(ctrl_frame, text="Reset Scores", command=self.reset_scores)
        quit_btn = tk.Button(ctrl_frame, text="Quit", command=self.quit_app)
        save_btn.pack(side='left')
        reset_btn.pack(side='left', padx=8)
        quit_btn.pack(side='right')

    def _load_image(self, name: str):
        path = ASSETS_DIR / name
        try:
            if path.exists():
                return tk.PhotoImage(file=str(path))
        except Exception:
            pass
        return None

    def _score_text(self):
        return f"Score — You: {self.player_score}  Computer: {self.computer_score}  Rounds: {self.rounds}"

    # ----- gameplay -----
    def play(self, player_choice: str):
        computer_choice = rps.get_computer_choice()
        self.rounds += 1
        result = rps.compare(player_choice, computer_choice)

        if result == 'player':
            self.player_score += 1
            res_text = 'You win this round!'
            if getattr(self, 'sounds_enabled', True):
                self._play_sound('win.wav')
            self._flash_status('green')
        elif result == 'computer':
            self.computer_score += 1
            res_text = 'Computer wins this round.'
            if getattr(self, 'sounds_enabled', True):
                self._play_sound('lose.wav')
            self._flash_status('red')
        else:
            res_text = "Tie."
            if getattr(self, 'sounds_enabled', True):
                self._play_sound('tie.wav')
            self._flash_status('gray')

        status = f"You: {player_choice}  —  Computer: {computer_choice}. {res_text}"
        self.status_label.config(text=status)
        self.score_label.config(text=self._score_text())

        entry = f"Round {self.rounds}: You {player_choice} | Computer {computer_choice} | {res_text}"
        # keep most recent first
        self.history.insert(0, entry)
        self._refresh_history()
        self._save_state()

    def _refresh_history(self):
        self.hist_listbox.delete(0, tk.END)
        for line in self.history[:1000]:
            self.hist_listbox.insert(tk.END, line)

    # ----- sounds & animation -----
    def _play_sound(self, filename: str):
        # Respect user setting
        if not getattr(self, 'sounds_enabled', True):
            return
        path = ASSETS_DIR / filename
        if not path.exists():
            return
        # Try mac's afplay, then system 'play' (sox), otherwise no-op
        player = shutil.which('afplay') or shutil.which('play') or shutil.which('aplay')
        if player:
            try:
                subprocess.Popen([player, str(path)])
            except Exception:
                pass

    def _flash_status(self, color: str, ms: int = 180):
        orig = self.status_label.cget('bg')
        try:
            self.status_label.config(bg=color)
            self.after(ms, lambda: self.status_label.config(bg=orig))
        except Exception:
            # some platforms may not support changing bg; ignore
            pass

    def _toggle_mute(self):
        self.sounds_enabled = not getattr(self, 'sounds_enabled', True)
        self._save_state()
        state = "unmuted" if self.sounds_enabled else "muted"
        # brief status feedback
        prev = self.status_label.cget('text')
        self.status_label.config(text=f"(Sound {state}) {prev}")
        self.after(1200, lambda: self.status_label.config(text=prev))

    # ----- controls -----
    def save_log(self):
        if not self.history:
            messagebox.showinfo("Save Log", "No rounds to save yet.")
            return
        path = filedialog.asksaveasfilename(defaultextension='.txt',
                                            filetypes=[('Text files', '*.txt'), ('All files', '*.*')],
                                            title='Save round history')
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write('Rock Paper Scissors — Round Log\n')
                f.write(self._score_text() + '\n\n')
                for line in reversed(self.history):  # oldest first in file
                    f.write(line + '\n')
            messagebox.showinfo("Save Log", f"Saved {len(self.history)} rounds to {path}")
        except Exception as e:
            messagebox.showerror("Save Log", f"Failed to save: {e}")

    def reset_scores(self):
        if not messagebox.askyesno("Reset", "Reset scores and clear history?"):
            return
        self.player_score = 0
        self.computer_score = 0
        self.rounds = 0
        self.history = []
        self.score_label.config(text=self._score_text())
        self._refresh_history()
        self._save_state()

    def quit_app(self):
        summary = f"Final score — You: {self.player_score} | Computer: {self.computer_score} | Rounds: {self.rounds}"
        if messagebox.askokcancel("Quit", summary + "\n\nQuit the game?"):
            self._save_state()
            self.destroy()

    def show_about(self):
        messagebox.showinfo("About Rock Paper Scissors",
                            "Rock Paper Scissors\n\nA small learning project.\n\nKeyboard: r/p/s to play, q to quit.\nBuilt with Python + Tkinter.")

    def show_settings(self):
        # Simple settings dialog to toggle sounds
        dlg = tk.Toplevel(self)
        dlg.title("Settings")
        dlg.resizable(False, False)
        var = tk.BooleanVar(value=getattr(self, 'sounds_enabled', True))

        def save_and_close():
            self.sounds_enabled = var.get()
            self._save_state()
            dlg.destroy()
            # update status to show mute state briefly
            if not self.sounds_enabled:
                self.status_label.config(text="(Muted) " + self.status_label.cget('text'))

        chk = tk.Checkbutton(dlg, text="Enable sounds", variable=var)
        chk.pack(padx=12, pady=8)
        btn_frame = tk.Frame(dlg)
        btn_frame.pack(pady=6)
        tk.Button(btn_frame, text="Save", command=save_and_close).pack(side='left', padx=6)
        tk.Button(btn_frame, text="Cancel", command=dlg.destroy).pack(side='right', padx=6)

    # ----- key bindings -----
    def _bind_keys(self):
        # lowercase and uppercase
        for k, choice in (('r', 'rock'), ('p', 'paper'), ('s', 'scissors')):
            self.bind(k, lambda e, c=choice: self.play(c))
            self.bind(k.upper(), lambda e, c=choice: self.play(c))
        # quit keys
        self.bind('q', lambda e: self.quit_app())
        # mute toggle
        self.bind('m', lambda e: self._toggle_mute())
        self.bind('M', lambda e: self._toggle_mute())
        # Command-Q on mac
        try:
            self.bind('<Command-q>', lambda e: self.quit_app())
            self.bind('<Control-q>', lambda e: self.quit_app())
        except Exception:
            pass


def main():
    app = RPSApp()
    app.mainloop()


if __name__ == '__main__':
    main()
