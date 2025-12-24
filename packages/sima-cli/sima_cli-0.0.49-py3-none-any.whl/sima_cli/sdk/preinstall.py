#!/usr/bin/env python3
r"""
Palette SDK Preinstallation Check
───────────────────────────────────────────────────────────────
Performs essential environment checks before SDK installation:
1. Python version
2. Docker version
3. CPU and RAM
4. Rosetta (macOS)
5. Firewall
"""

import sys
import json
import subprocess
import platform
from rich.console import Console
from rich.table import Table
from rich import box
from sima_cli.sdk.utils import run_command
import importlib.resources as pkg_resources
from typing import Any

console = Console()

# ---------------------------------------------------------------------
# Load system requirements from JSON
# ---------------------------------------------------------------------
def load_requirements() -> Any:
    try:
        # Python 3.9+ supports importlib.resources.files()
        if hasattr(pkg_resources, "files"):
            with pkg_resources.files("sima_cli").joinpath("sdk/requirements.json").open("r", encoding="utf-8") as f:
                return json.load(f)
        else:
            # ✅ Fallback for Python 3.8 and older
            with pkg_resources.open_text("sima_cli.sdk", "requirements.json", encoding="utf-8") as f:
                return json.load(f)

    except Exception as e:
        print(f"Encountered error while loading requirements: {e}")
        sys.exit(1)


def version_gte(v1: str, v2: str) -> bool:
    try:
        t1, t2 = tuple(map(int, v1.split(".")[:3])), tuple(map(int, v2.split(".")[:3]))
        return t1 >= t2
    except Exception:
        return False

# ---------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------
def check_python(min_version):
    version = platform.python_version()
    passed = version_gte(version, min_version)
    console.print(
        f"{'✅' if passed else '❌'} Python {version} "
        f"(Required ≥ {min_version})",
        style="green" if passed else "red",
    )
    return not passed, ["Python", f"≥ {min_version}", version, "✅ PASS" if passed else "❌ FAIL"]


def get_docker_version():
    try:
        out = subprocess.check_output(["docker", "--version"], text=True)
        return out.split()[2].replace(",", "")
    except Exception:
        return None


def check_docker(min_version):
    ver = get_docker_version()
    passed = ver is not None and version_gte(ver, min_version)
    console.print(
        f"{'✅' if passed else '❌'} Docker {ver or 'Not Found'} "
        f"(Required ≥ {min_version})",
        style="green" if passed else "red",
    )
    return not passed, ["Docker", f"≥ {min_version}", ver or "N/A", "✅ PASS" if passed else "❌ FAIL"]


def check_cpu_ram(min_cores, min_ram_gb):
    import psutil
    cores = psutil.cpu_count(logical=False)
    ram_gb = psutil.virtual_memory().total / (1024 ** 3)
    passed = cores >= min_cores and ram_gb >= min_ram_gb
    console.print(
        f"{'✅' if passed else '❌'} {cores} cores / {ram_gb:.1f} GB RAM "
        f"(Required ≥ {min_cores} cores / {min_ram_gb} GB)",
        style="green" if passed else "red",
    )
    return not passed, ["CPU/RAM", f"≥{min_cores} cores / ≥{min_ram_gb} GB", f"{cores} / {ram_gb:.1f} GB", "✅ PASS" if passed else "❌ FAIL"]


def check_rosetta_and_firewall(use_sudo=False):
    """Check Rosetta (macOS) and Firewall (cross-platform, sudo-aware)."""
    results = []
    rosetta_failed, fw_failed = False, False
    sysname = platform.system()

    # ───────────────────────────────────────────────
    # 🧩 Rosetta 2 (macOS)
    # ───────────────────────────────────────────────
    if sysname == "Darwin":
        arch = platform.machine()
        if arch == "arm64":
            try:
                subprocess.check_output(["/usr/bin/pgrep", "oahd"], stderr=subprocess.DEVNULL)
                console.print("✅ Rosetta 2 Installed", style="green")
                results.append(["Rosetta 2", "Installed", "Installed", "✅ PASS"])
            except subprocess.CalledProcessError:
                console.print("⚠️ Rosetta 2 missing (Apple Silicon)", style="yellow")
                results.append(["Rosetta 2", "Installed", "Missing", "⚠️ WARNING"])
                rosetta_failed = True

    # ───────────────────────────────────────────────
    # 🔥 Firewall
    # ───────────────────────────────────────────────
    note, result = "Unknown", "⚠️ WARNING"

    try:
        if sysname == "Windows":
            out = subprocess.check_output(["netsh", "advfirewall", "show", "allprofiles"], text=True)
            note, result = ("Active", "⚠️ WARNING") if "ON" in out else ("Disabled", "✅ PASS")

        elif sysname == "Linux":
            # Try without sudo first
            out = run_command(["ufw", "status"], use_sudo=False).stdout
            if "permission denied" in out.lower() or not out.strip():
                if use_sudo:
                    out = run_command(["ufw", "status"], use_sudo=True).stdout
                else:
                    note, result = "Unverified (sudo required)", "⚠️ WARNING"
                    raise PermissionError
            note, result = ("Active", "⚠️ WARNING") if "active" in out.lower() else ("Disabled", "✅ PASS")

        elif sysname == "Darwin":
            # pfctl typically requires sudo
            try:
                out = run_command(["pfctl", "-s", "info"], use_sudo=False).stdout
                if "Permission denied" in out or not out.strip():
                    if use_sudo:
                        out = run_command(["pfctl", "-s", "info"], use_sudo=True).stdout
                    else:
                        note, result = "Unverified (sudo required)", "⚠️ WARNING"
                        raise PermissionError
                note, result = ("Active", "⚠️ WARNING") if "Status: Enabled" in out else ("Disabled", "✅ PASS")
            except subprocess.CalledProcessError:
                note, result = "Error running pfctl", "⚠️ WARNING"

    except PermissionError:
        console.print("[yellow]⚠️ Firewall check skipped — sudo required for accurate status.[/yellow]")
    except Exception:
        note, result = "Unverified", "⚠️ WARNING"

    fw_failed = "⚠️" in result
    results.append(["Firewall", "Disabled", note, result])

    if result == "⚠️ WARNING":
        console.print("⚠️  Firewall may restrict Docker or SDK communication.", style="yellow")
    else:
        console.print("✅ Firewall Disabled or Inactive", style="green")

    return rosetta_failed, fw_failed, results


# ---------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------
def print_system_report(all_data):
    table = Table(
        title="System Requirements Report",
        title_style="bold grey",
        header_style="bold cyan",
        border_style="cyan",
        box=box.SQUARE,
        show_lines=True,
    )
    table.add_column("Component", style="bold cyan")
    table.add_column("Required", style="white")
    table.add_column("Found", style="white")
    table.add_column("Result", justify="left")

    for comp, req, found, res in all_data:
        color = "green" if "✅" in res else "yellow" if "⚠️" in res else "red"
        table.add_row(comp, req, found, f"[{color}]{res}[/{color}]")

    console.print("\n")
    console.print(table)
    console.print()


# ---------------------------------------------------------------------
# syscheck
# ---------------------------------------------------------------------
def syscheck(force_install: bool):
    req = load_requirements()
    py_failed, py_info = check_python(req["python"])
    dock_failed, dock_info = check_docker(req["docker"])
    cpu_failed, cpu_info = check_cpu_ram(req["min_cores"], req["min_ram_gb"])
    rosetta_failed, fw_failed, rf_info = check_rosetta_and_firewall(use_sudo=True)
    all_data = [py_info, dock_info, cpu_info] + rf_info
    print_system_report(all_data)

    if any([py_failed, dock_failed, cpu_failed, fw_failed, rosetta_failed]):
        if force_install:
            console.print("[yellow]⚠️  Force install enabled — continuing despite warnings.[/yellow]")
            return 1
        else:
            console.print("[red]❌ Some system checks failed.[/red]")
            choice = input("Do you want to continue anyway? [y/N]: ").strip().lower()
            if choice in ("y", "yes"):
                console.print("[yellow]⚠️  Proceeding despite warnings.[/yellow]")
                return 0
            else:
                console.print("[cyan]🛑 Installation aborted by user.[/cyan]")
                exit(-1)

    console.print("[bold green]✅ All system requirements met. Ready for installation![/bold green]")
    return 0


if __name__ == "__main__":
    sys.exit(syscheck())
