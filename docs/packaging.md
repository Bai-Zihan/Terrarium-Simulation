# Packaging and command entry

The player-facing command is `terrarium`.

## Local command install

From the project root:

```powershell
.\scripts\install-command.ps1
```

This installs the package in editable mode for the current Windows user and
creates a `terrarium` command on the user's Python scripts path. The installer
also adds that scripts directory to the user's `PATH`, so the command works
from any folder after opening a new terminal.

If you want to install the command without editing `PATH`:

```powershell
.\scripts\install-command.ps1 -NoPath
```

Common starts:

```powershell
terrarium
terrarium --seed 42
terrarium --container horizontal_jar
terrarium run --ticks 168 --interval 12
terrarium shell --load test_bottle.json
```

`terrarium` with no subcommand starts the interactive shell.

## Standalone Windows executable

From the project root:

```powershell
.\scripts\build-windows-exe.ps1
```

The output is:

```text
dist\terrarium.exe
```

That executable can be distributed as the terminal game. The launcher in
`packaging\terrarium_launcher.py` exists so PyInstaller can start the package
through the normal `terrarium.cli:main` entry point.

## Python package entry

`pyproject.toml` exposes:

```toml
[project.scripts]
terrarium = "terrarium.cli:main"
```

So wheel/editable installs and standalone builds both use the same game entry.
