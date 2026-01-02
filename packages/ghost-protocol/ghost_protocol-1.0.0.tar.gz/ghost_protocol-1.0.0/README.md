<div align="center">

# 👻 Ghost Protocol

### *The silent guardian of your AI-assisted workflow*

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=for-the-badge)](http://makeapullrequest.com)

<br>

**Stop wasting tokens on garbage files.**<br>
**Stop committing 50MB SQLite databases.**<br>
**Stop explaining to AI why your project has 847 PNG files.**

<br>

[Installation](#-installation) •
[Quick Start](#-quick-start) •
[Features](#-features) •
[Configuration](#%EF%B8%8F-configuration)

<br>

<img src="https://raw.githubusercontent.com/yourusername/ghost-protocol/main/assets/demo.gif" alt="Ghost Protocol Demo" width="600">

</div>

---

## 🤔 The Problem

You're vibe-coding with Claude/Cursor/Copilot. Life is good.

Then you notice:
- 💸 Token costs are through the roof
- 🐌 AI responses are slow because context is bloated  
- 😱 You accidentally committed a 200MB video file
- 🔄 AI keeps "seeing" your `node_modules` or `__pycache__`

**Ghost Protocol fixes all of this. Automatically. In the background.**

---

## ✨ Features

| Feature | What it does |
|---------|--------------|
| 🚫 **Auto-Ignore** | Detects heavy files (images, videos, databases) and adds them to `.gitignore` + `.cursorignore` |
| 🧹 **Self-Cleaning** | Removes stale entries when you delete the original files |
| 🛡️ **Commit Guard** | Blocks `git commit` if you try to push oversized source files |
| 📊 **Live Monitor** | Beautiful TUI dashboard showing token count & estimated API cost |
| ⚡ **Zero Config** | Works out of the box. Sensible defaults. |
| 🔇 **Silent** | Runs in background. No notifications. No interruptions. |

---

## 📦 Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/ghost-protocol.git
cd ghost-protocol

# Install dependencies
pip install -r requirements.txt
```

---

## 🚀 Quick Start

**Three commands. That's it.**

```bash
# 1. Install the git hook (one time only)
python main.py --install

# 2. Start the guardian daemon
python main.py --ghost

# 3. (Optional) Open the monitor in another terminal
python main.py --monitor
```

Now forget about it. Ghost Protocol handles the rest.

---

## 📊 The Monitor

```
┌──────────────────────────────────────────────────────────────┐
│  👻 Ghost Protocol v21.0.0 | Status: ACTIVE                  │
├─────────────────────────────┬────────────────────────────────┤
│  📊 Project Stats           │  🧠 The Brain                  │
│                             │                                │
│  Total Tokens    1,247,832  │  • Writer: IgnoreManager (DRY) │
│  Files Tracked        342   │  • Scanner: Auto-updating (30s)│
│  Est. Cost ($3/M)  $3.74    │  • Config: Cached & Valid      │
│                             │                                │
│                             │  Press Ctrl+C to exit.         │
└─────────────────────────────┴────────────────────────────────┘
```

---

## ⚙️ Configuration

Create `ghost_config.json` in your project root:

```json
{
  "limits": {
    "max_asset_size_mb": 1.0,
    "max_code_size_mb": 0.5,
    "debounce_seconds": 0.5
  },
  "skip_dirs": ["my_custom_folder", "secrets"],
  "extensions": {
    "garbage": [".custom", ".mybigfile"],
    "code": [".mycode"]
  }
}
```

### Default Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `max_asset_size_mb` | 1.0 | Auto-ignore assets larger than this |
| `max_code_size_mb` | 0.5 | Warn/block code files larger than this |
| `debounce_seconds` | 0.5 | Wait time before processing file changes |

### Pre-configured Skip Directories

```
venv, .venv, node_modules, __pycache__, .git, 
.idea, .vscode, dist, build, coverage, target...
```

### Pre-configured Garbage Extensions

```
.log, .sqlite, .db, .zip, .mp4, .mp3, .pdf, 
.png, .jpg, .gif, .exe, .dll, .bin...
```

---

## 🏗️ How It Works

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│  Watchdog   │────▶│   Queue     │────▶│  IgnoreManager  │
│  (Events)   │     │  (Debounce) │     │  (Atomic Write) │
└─────────────┘     └─────────────┘     └─────────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │ .gitignore  │
                                        │.cursorignore│
                                        └─────────────┘
```

**Key Design Decisions:**
- **Singleton Config** — Thread-safe, cached sets for O(1) lookups
- **File Locking** — Cross-platform advisory locks (fcntl/msvcrt)
- **Atomic Writes** — temp file → os.replace() for data integrity
- **Fail-Closed** — Git hook blocks commit on any error

---

## 🧑‍💻 For Developers

```bash
# Project structure
ghost-protocol/
├── main.py              # Entry point & CLI
├── requirements.txt     # Dependencies
└── src/
    ├── config.py        # Singleton configuration
    ├── core.py          # Logger & console
    ├── utils.py         # Atomic write, file locking
    ├── watcher.py       # File system events → queue
    ├── scanner.py       # Project stats & git integration
    ├── pruner.py        # Cleanup stale ignore entries
    ├── ignore_manager.py # DRY: single source for ignore logic
    └── monitor.py       # Rich TUI dashboard
```

---

## 🤝 Contributing

PRs are welcome! Please:

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## 📄 License

MIT © 2024 — Do whatever you want with it.

---

<div align="center">

**Made for vibe coders, by a vibe coder.**

*Because life's too short to manually edit .gitignore*

<br>

⭐ Star this repo if Ghost saved your tokens ⭐

</div>
