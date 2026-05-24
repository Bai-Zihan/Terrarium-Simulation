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

The script installs the bundle dependencies, builds the executable, and writes a
release zip. The output is:

```text
dist\release\terrarium-sim-0.1.0-windows-x64.zip
```

The zip contains `terrarium.exe`, the README, and the user guides. The launcher in
`packaging\terrarium_launcher.py` exists so PyInstaller can start the package
through the normal `terrarium.cli:main` entry point.

## Cross-platform release builds

GitHub Actions builds release packages on native runners for each target system.
This matters because PyInstaller packages should be built on the operating
system they will run on.

The workflow is:

```text
.github/workflows/build-release.yml
```

When a GitHub release is published, the workflow builds and attaches these
assets to the release:

```text
terrarium-sim-<tag>-windows-x64.zip
terrarium-sim-<tag>-macos-x64.zip
terrarium-sim-<tag>-macos-arm64.zip
terrarium-sim-<tag>-linux-x64.zip
```

The macOS x64 package is for Intel Macs. The macOS arm64 package is for Apple
Silicon Macs.

You can also run the workflow manually from the Actions tab. Manual runs upload
the zips as workflow artifacts. Release-published runs also attach the zips to
the GitHub release.

## Release asset contents

Each release zip contains:

```text
terrarium / terrarium.exe
README.md
docs/user-guide.zh-CN.md
docs/user-guide.en.md
docs/packaging.md
```

Do not attach local save files such as `game.json`, `test_bottle.json`, or other
personal bottle exports to public releases.

## Python package entry

`pyproject.toml` exposes:

```toml
[project.scripts]
terrarium = "terrarium.cli:main"
```

So wheel/editable installs and standalone builds both use the same game entry.
