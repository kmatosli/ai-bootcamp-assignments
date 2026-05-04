# Development Environment Setup Guide
## Pre-Work Section B Portfolio Artifact
### Written for future Coding Temple students starting the AI Bootcamp

---

## 1. VS Code Extensions

### Python (Microsoft)
The core extension for Python development in VS Code. It provides syntax highlighting,
code navigation, and connects VS Code to your Python interpreter and virtual environment.
Without this, VS Code treats Python files as plain text.

### Pylance
Works alongside the Python extension to provide fast, intelligent type checking and
IntelliSense (autocomplete). It catches type errors before you run the code, which
saves significant debugging time on larger projects.

### GitLens
Extends VS Code's built-in Git support by showing who last changed each line of code
and when, directly in the editor. Essential for understanding the history of a file
and for collaborative work.

### Prettier
An automatic code formatter. When you save a file, Prettier reformats it to a
consistent style. Eliminates arguments about formatting and keeps code readable.

### GitHub Copilot
AI code completion that suggests entire lines or blocks of code as you type.
Useful for boilerplate and repetitive patterns. Treat suggestions as a starting
point — always read and understand what it generates.

---

## 2. VS Code Screenshot

[Screenshot: VS Code with file explorer showing ai-bootcamp-assignments,
integrated terminal open at the repo root, about_me.py open with Python
syntax highlighting visible]

To take this screenshot on Windows: Win + Shift + S to capture a region,
then paste into this document or save as PNG.

---

## 3. settings.json

Location: File > Preferences > Settings > Open Settings (JSON) icon (top right)

```json
{
  "editor.formatOnSave": true,
  "editor.tabSize": 4,
  "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
  "files.autoSave": "afterDelay",
  "editor.minimap.enabled": false,
  "terminal.integrated.defaultProfile.windows": "PowerShell"
}
```

**Settings explained:**
- `editor.formatOnSave` — automatically formats code when you save. Keeps style consistent without thinking about it.
- `editor.tabSize: 4` — Python convention is 4-space indentation. This enforces it.
- `python.defaultInterpreterPath` — points VS Code to the virtual environment Python, not the system Python. Critical for package isolation.
- `files.autoSave: afterDelay` — saves files automatically after a short pause. Prevents losing work.
- `terminal.integrated.defaultProfile.windows: PowerShell` — opens PowerShell by default in the integrated terminal.

---

## 4. Terminal Cheat Sheet (PowerShell)

| # | Command | Description | Example |
|---|---------|-------------|---------|
| 1 | `pwd` | Print working directory — shows where you are | `pwd` → C:\Users\kmato\Documents |
| 2 | `ls` | List files and folders in current directory | `ls` |
| 3 | `ls -Force` | List including hidden files (equivalent of ls -a) | `ls -Force` |
| 4 | `cd folder` | Change directory — navigate into a folder | `cd Documents` |
| 5 | `cd ..` | Go up one level to parent directory | `cd ..` |
| 6 | `mkdir name` | Create a new folder | `mkdir my-project` |
| 7 | `New-Item file.py` | Create a new empty file | `New-Item about_me.py` |
| 8 | `cat file` | Print file contents to terminal | `cat requirements.txt` |
| 9 | `Remove-Item -Recurse -Force folder\` | Delete a folder and all contents | `Remove-Item -Recurse -Force venv\` |
| 10 | `git add . && git commit -m "msg"` | Stage all changes and commit with message | `git commit -m "feat: add about_me.py"` |

**Virtual environment commands:**

| Command | Purpose |
|---|---|
| `python -m virtualenv venv` | Create virtual environment (use this on Python 3.14) |
| `.\venv\Scripts\Activate.ps1` | Activate virtual environment |
| `deactivate` | Exit virtual environment |
| `pip install package` | Install a package |
| `pip freeze > requirements.txt` | Save all installed packages |
| `pip install -r requirements.txt` | Restore packages from file |

---

## 5. Troubleshooting: Python 3.14 Virtual Environment Error

**The problem:**
When running `python -m venv venv` to create a virtual environment, the command
failed with this error:
Unable to copy 'C:\Users\kmato\AppData\Local\Python\pythoncore-3.14-64\Lib\venv
scripts\nt\venvlauncher.exe' to venv\Scripts\python.exe

The environment was created but unusable — activating it immediately failed.

**What I tried first:**
Tried running the command again assuming it was a one-time failure. Same error.
Then tried repairing the Python 3.14 installation through Windows Settings. Did
not resolve the issue.

**How I found the solution:**
Identified that Python 3.14 is a very recent release (2025) and some tooling has
not yet updated to support it fully. The built-in `venv` module has a known
compatibility issue with Python 3.14 on Windows.

The fix was to use `virtualenv` (a third-party package) instead of the built-in
`venv` module:

```powershell
python -m pip install virtualenv
python -m virtualenv venv
.\venv\Scripts\Activate.ps1
```

This worked immediately.

**What I learned:**
Being on the newest version of a language is not always an advantage. Production
code and tooling lag behind language releases by months or years. When you hit
a mysterious error on a brand new tool version, search for known compatibility
issues before spending time debugging your own setup. The error message itself
was not descriptive enough to point to the root cause — the diagnosis required
understanding the context (Python 3.14 just released, venv module changed).

---

## Reflection

[Your personal reflection goes here — 150-300 words]

Prompt: Before this week, describe how you thought about the files and programs
on your computer. How has your mental model changed? What surprised you most,
and why?

Write this in your own voice. The graders are looking for genuine reflection
on how your understanding shifted, not a polished answer.
