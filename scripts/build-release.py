from __future__ import annotations

import argparse
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "terrarium-sim"


def project_version() -> str:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'(?m)^version\s*=\s*"([^"]+)"\s*$', pyproject)
    if not match:
        raise RuntimeError("could not find project version in pyproject.toml")
    return match.group(1)


def host_platform_label() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system.startswith("win"):
        os_name = "windows"
    elif system == "darwin":
        os_name = "macos"
    elif system == "linux":
        os_name = "linux"
    else:
        os_name = system or "unknown"

    if machine in {"amd64", "x86_64"}:
        arch = "x64"
    elif machine in {"arm64", "aarch64"}:
        arch = "arm64"
    else:
        arch = re.sub(r"[^a-z0-9]+", "-", machine).strip("-") or "unknown"
    return f"{os_name}-{arch}"


def safe_label(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    cleaned = cleaned.strip(".-_")
    return cleaned or "dev"


def run(command: list[str]) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def build_executable(dist_dir: Path, work_dir: Path, spec_dir: Path) -> Path:
    dist_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    spec_dir.mkdir(parents=True, exist_ok=True)

    run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--onefile",
            "--console",
            "--name",
            "terrarium",
            "--clean",
            "--distpath",
            str(dist_dir),
            "--workpath",
            str(work_dir),
            "--specpath",
            str(spec_dir),
            str(ROOT / "packaging" / "terrarium_launcher.py"),
        ]
    )

    executable = dist_dir / ("terrarium.exe" if os.name == "nt" else "terrarium")
    if not executable.exists():
        raise FileNotFoundError(f"expected PyInstaller output at {executable}")
    return executable


def copy_if_exists(source: Path, destination: Path) -> None:
    if source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def make_package(executable: Path, version: str, platform_label: str, release_dir: Path) -> Path:
    version_label = safe_label(version)
    platform_label = safe_label(platform_label)
    package_dir = release_dir / f"{PACKAGE_NAME}-{version_label}-{platform_label}"
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True)

    binary_name = "terrarium.exe" if executable.suffix == ".exe" else "terrarium"
    shutil.copy2(executable, package_dir / binary_name)
    copy_if_exists(ROOT / "README.md", package_dir / "README.md")
    copy_if_exists(ROOT / "docs" / "user-guide.zh-CN.md", package_dir / "docs" / "user-guide.zh-CN.md")
    copy_if_exists(ROOT / "docs" / "user-guide.en.md", package_dir / "docs" / "user-guide.en.md")
    copy_if_exists(ROOT / "docs" / "packaging.md", package_dir / "docs" / "packaging.md")
    copy_if_exists(ROOT / "LICENSE", package_dir / "LICENSE")

    archive_path = release_dir / f"{package_dir.name}.zip"
    if archive_path.exists():
        archive_path.unlink()
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(package_dir.rglob("*")):
            archive.write(path, path.relative_to(release_dir))
    return archive_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a release package for the current platform.")
    parser.add_argument("--version", default=project_version(), help="version or release tag used in the archive name")
    parser.add_argument("--platform-label", default=host_platform_label(), help="platform label, e.g. windows-x64")
    parser.add_argument("--dist-dir", type=Path, default=ROOT / "dist" / "pyinstaller")
    parser.add_argument("--work-dir", type=Path, default=ROOT / "build" / "pyinstaller")
    parser.add_argument("--spec-dir", type=Path, default=ROOT / "build" / "spec")
    parser.add_argument("--release-dir", type=Path, default=ROOT / "dist" / "release")
    args = parser.parse_args()

    executable = build_executable(args.dist_dir, args.work_dir, args.spec_dir)
    archive_path = make_package(executable, args.version, args.platform_label, args.release_dir)
    print("")
    print(f"Built executable: {executable}")
    print(f"Built release archive: {archive_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
