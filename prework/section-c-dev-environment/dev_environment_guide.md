# VS Code Setup Guide
# Pre-Work Section B — Development Environment Reference

## Extensions Installed

| Extension | Purpose |
|---|---|
| Python (Microsoft) | Python language support, linting, debugging |
| Pylance | Fast type checking and IntelliSense |
| GitLens | Enhanced Git history and blame annotations |
| Prettier | Code formatter |
| GitHub Copilot | AI code completion |

## Key Settings (settings.json)

```json
{
  "editor.formatOnSave": true,
  "editor.tabSize": 4,
  "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
  "files.autoSave": "afterDelay"
}
```

## Terminal Cheat Sheet

| Command | PowerShell | Purpose |
|---|---|---|
| Create venv | python -m virtualenv venv | Create virtual environment |
| Activate venv | .\venv\Scripts\Activate.ps1 | Activate environment |
| Deactivate | deactivate | Exit virtual environment |
| Install package | pip install package-name | Install a package |
| Save dependencies | pip freeze > requirements.txt | Export packages |
| Restore dependencies | pip install -r requirements.txt | Rebuild environment |

## Git Workflow
git add .
git commit -m "type: description — context"
git push origin main

## Commit Message Convention

| Type | Use for |
|---|---|
| feat: | New file or feature |
| fix: | Bug correction |
| docs: | README or comments |
| chore: | Config, gitignore, tooling |
| refactor: | Restructuring without behavior change |

## Troubleshooting

**Activation blocked:** Run once — Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

**Python 3.14 venv error:** Use python -m virtualenv venv instead of python -m venv venv

**KeyError on CSV read:** Use encoding="utf-8-sig" to strip PowerShell BOM character
