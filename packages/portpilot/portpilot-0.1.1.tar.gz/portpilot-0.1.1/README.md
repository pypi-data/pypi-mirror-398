# 🛫 PortPilot

**Interactive terminal port manager for developers**

Tired of running `lsof -i :3000` and then `kill -9 <pid>` every time? PortPilot gives you a beautiful TUI to see all listening ports and kill them with a keystroke.

![PortPilot Demo](https://raw.githubusercontent.com/emre/portpilot/main/demo.gif)

## ✨ Features

- 🖥️ **Interactive TUI** - Navigate with keyboard, search, and kill processes instantly
- 🔍 **Real-time filtering** - Filter by port, process name, or PID
- 🎨 **Syntax highlighting** - Common dev ports (3000, 8000, 5432, etc.) are color-coded
- ⚡ **Quick commands** - CLI mode for scripting and one-liners
- 📊 **Detailed info** - See memory usage, start time, command line, and more
- 👀 **Watch mode** - Monitor specific ports in real-time

## 📦 Installation

```bash
pip install portpilot
```

Or install from source:

```bash
git clone https://github.com/emre/portpilot.git
cd portpilot
pip install -e .
```

## 🚀 Usage

### Interactive TUI

Just run:

```bash
portpilot
# or use the short alias
pp
```

**Keyboard shortcuts:**

| Key | Action |
|-----|--------|
| `↑/↓` | Navigate |
| `k` | Kill selected process (SIGTERM) |
| `K` | Force kill (SIGKILL) |
| `r` | Refresh list |
| `f` or `/` | Focus filter |
| `Esc` | Clear filter |
| `q` | Quit |

### CLI Commands

```bash
# List all listening ports
portpilot list
pp list

# Filter by port
pp list -p 3000

# Filter by name
pp list -n python

# Output as JSON (great for scripting)
pp list --json

# Kill a specific port
pp kill 3000

# Force kill
pp kill 3000 -f

# Skip confirmation
pp kill 3000 -y

# Kill multiple ports
pp killall 3000 8000 5432

# Get detailed info about a port
pp info 3000

# Watch specific ports
pp watch 3000 8000

# Watch all ports
pp watch
```

## 🎨 Port Colors

PortPilot highlights common development ports:

| Color | Ports | Common Use |
|-------|-------|------------|
| 🟢 Green | 3000, 3001 | React, Next.js |
| 🟡 Yellow | 8000, 8080 | Django, General |
| 🔵 Cyan | 5000, 5001 | Flask |
| 🟣 Magenta | 5432 | PostgreSQL |
| 🔴 Red | 6379 | Redis |

## 🔧 Examples

### Quick port cleanup before starting dev server

```bash
pp kill 3000 -y && npm run dev
```

### Find what's using a port

```bash
pp info 8000
```

### Kill all common dev ports

```bash
pp killall 3000 3001 8000 8080 5000 -y
```

### Script integration

```bash
# Check if port is in use
if pp list -p 3000 --json | jq -e '.[0]' > /dev/null; then
    echo "Port 3000 is in use"
fi
```

## 🛠️ Development

```bash
# Clone the repo
git clone https://github.com/emre/portpilot.git
cd portpilot

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black portpilot/
ruff check portpilot/
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### How to contribute

1) Fork the repository and create a feature branch:
- `git checkout -b feature/my-change`

2) Set up a virtual environment and install dev dependencies:
- `python -m venv venv`
- Activate it (Windows: `venv\Scripts\activate`, macOS/Linux: `source venv/bin/activate`)
- `pip install -e ".[dev]"`

3) Run checks before opening a PR:
- `pytest`
- `ruff check portpilot/`
- `black portpilot/`

4) Open a Pull Request against `main` and describe:
- What changed and why
- How to test it locally

Maintainer: **Emre Çalışkan**

---

Made with ❤️ for developers who are tired of port conflicts
