# 🤖 V.E.N.U.S. — Cybernetic Desktop Companion 
 
[![Language: Python 3](https://img.shields.io/badge/Language-Python%203-blue.svg?style=flat-square)](#)
[![GUI Toolkit: PyQt5](https://img.shields.io/badge/Toolkit-PyQt5-darkgreen.svg?style=flat-square)](#)
[![Platform: Linux / X11](https://img.shields.io/badge/Platform-Linux%20%2F%20X11-purple.svg?style=flat-square)](#)



**HACKING DOES NOT HAVE TO BE BOORRRRIINNNGGG ( AND LONELY )**

V.E.N.U.S. (**Virtual Electronic Neural Utility System**) is a context-aware, desktop mascot and system utility companion built with **PyQt5**. Designed to sit alongside minimalist window managers (specifically optimized for tiling setups like i3wm), the application features custom transparency-masked graphics, a live resource-monitor HUD, cyber security quizzes, word-guessing games, and automated dialogue commentary mapped to active window workspaces.

---

## 🎭 Application Interface Gallery


| 🧍 Idle Mascot Position | 📊 System HUD Metrics Active | 💬 Conversation Dialogue |
| :---: | :---: | :---: |
| ![Idle Mascot](assets/idle_preview.png) | ![Metrics Active](assets/hud_preview.png) | ![Conversation Bubble](assets/banter_preview.png) |

---

## ✨ Features Breakdown

* **🖼️ Translucent Sprite Alpha Masking:** Leverages X11 visual masks and custom PyQt regions to render frameless, transparent-background character frames that float above terminal windows.
* **💾 Configuration-Driven Personality:** Core dialogues, trivia systems, and target triggers are extracted into a separate [config.json](config.json) file.
* **📈 Resource HUD Diagnostics:** Draws hardware status rings for CPU load, RAM utilization, and battery remaining directly on the desktop.
* **🎮 Integrated Hacker Games:** Features an interactive cybersecurity trivia engine with hint generation and a word-guessing challenge (Hangman) inside the chat box.
* **👀 Active Workspace Observer:** Scans the active window title and triggers commentary when working in VS Code, terminals, CTF rooms, or when distracted by YouTube.
* **🔒 Safe State Serialization:** Saves companion state (affinity level, active companion name, notes memory log, quiz high scores) dynamically to `~/.config/venus_save.txt` on a background thread.

---

## ⚙️ Configuration Schema (`config.json`)

V.E.N.U.S. adapts its identity based on the parameters defined inside [config.json](config.json). Here is the schema reference:

| Configuration Parameter | Data Type | Default Value | Description |
| :--- | :--- | :--- | :--- |
| **`username`** | `String` | `"Operator"` | User's name. Replaces `{username}` tokens in dialogues. |
| **`companion_name`** | `String` | `"Reze"` | Companion name. Replaces `{companion_name}` tokens in dialogues. |
| **`assets_dir`** | `String` | `"assets"` | Folder containing character folders (e.g. `lara`, `lucy`, `reze`). |
| **`banter`** | `Array of String` | `[...]` | Dialogues selected randomly when clicking/interacting. |
| **`comforts`** | `Array of String` | `[...]` | Messages triggered during compile crashes or debugging blocks. |
| **`jokes`** | `Array of String` | `[...]` | List of programming/IT riddles. |
| **`tips`** | `Array of String` | `[...]` | Cybersecurity, pentesting, and Linux shortcuts tips. |
| **`hack_words`** | `Array of String` | `[...]` | Target words database for the guess game. |
| **`trivia_questions`** | `Array of Object` | `[...]` | Databases containing `q`, `options`, `answer`, and `hint`. |
| **`window_pokes`** | `Object` | `{"code": [], ...}` | Context-aware responses mapped to active window categories. |

---

## 🚀 Installation & Quickstart

### 1. Install Required Python Packages
Make sure you have python installed. Install the PyQt5 library:
```bash
pip install -r requirements.txt
```

### 2. Configure i3wm Floating Rules
To prevent the window manager from tiling the companion, add these rules to `~/.config/i3/config`:
```text
# Ensure the AI Companion stays floating and borderless
for_window [title="AI Companion"] floating enable, border none, sticky enable

# Bind trigger toggle script to Mod+Shift+v
bindsym $mod+Shift+v exec --no-startup-id ~/.local/bin/toggle_companion.sh
```

### 3. Verify Background Daemon Execution
The toggle controller script (`toggle_companion.sh`) daemonizes the PyQt5 process using `setsid` and routes standard streams to files, avoiding SIGHUP crashes on window reloads:
```bash
chmod +x toggle_companion.sh
./toggle_companion.sh
```

---

## 🧩 Adding Custom Sprites
To add new character sprite sets, place them inside your assets directory (`assets/character_name/`):
* `idle.png` — Baseline state sprite.
* `wink.png` — Interactivity click animation sprite.
* `blush.png` — High affinity state/banter response sprite.
* `shower.png` — State active during diagnostics/cleaning cycles.

Ensure images are exported with transparent PNG backgrounds (optimal layout size is `220x220` pixels).
