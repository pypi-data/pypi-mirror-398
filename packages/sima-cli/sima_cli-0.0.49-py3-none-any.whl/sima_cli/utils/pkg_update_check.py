import importlib.metadata
import urllib.request
import subprocess
import json
import socket
import click
import sys
import shlex
import shutil
import glob
import os

def cleanup_pip_leftovers():
    """Remove ~-prefixed leftover dirs in site-packages."""
    for path in sys.path:
        if path.endswith("site-packages") and os.path.isdir(path):
            junk_dirs = glob.glob(os.path.join(path, "~*"))
            for d in junk_dirs:
                try:
                    shutil.rmtree(d, ignore_errors=True)
                except Exception as e:
                    click.secho(f"⚠️ Failed to remove {d}: {e}", fg="yellow")

def update_package(package_name: str):
    """Suggest manual update on Windows; auto-update elsewhere."""
    pip_cmd = f"{shlex.quote(sys.executable)} -m pip install --upgrade {package_name}"

    if sys.platform.startswith("win"):
        click.secho("⚠️  Automatic self-update is not supported on Windows while the CLI is running.", fg="yellow", bold=True)
        safe_cmd = pip_cmd.replace("'", "")
        click.echo(f"Please run the following command in a new terminal:\n\n    {safe_cmd}\n")
        return

    try:
        subprocess.run(shlex.split(pip_cmd), check=True)
        cleanup_pip_leftovers()
        click.secho(f"✅ {package_name} updated successfully.", fg="green", bold=True)
    except subprocess.CalledProcessError as e:
        click.secho(f"❌ Failed to update {package_name}: {e}", fg="red", bold=True)

def has_internet(timeout: float = 1.0) -> bool:
    """
    Quick check for internet connectivity by connecting to a known DNS server.
    First tries Cloudflare (1.1.1.1), falls back to Google (8.8.8.8).
    Uses IP to avoid DNS lookup delays.
    """
    def try_connect(ip: str, port: int = 53) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                sock.connect((ip, port))
            return True
        except OSError:
            return False

    return try_connect("1.1.1.1") or try_connect("8.8.8.8")

def check_for_update(package_name: str, timeout: float = 2.0):

    if os.environ.get("SIMA_CLI_CHECK_FOR_UPDATE", "1") != "1":
        print(f'⚠️  You have disabled update check with SIMA_CLI_CHECK_FOR_UPDATE environment variable, skipping sima-cli update check..')
        return
    
    try:
        current_version = importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        print(f'❌ package not found {package_name}')
        return

    if not has_internet(timeout=0.2):
        print(f'⚠️  Offline mode, skipping sima-cli update check..')
        return

    try:
        with urllib.request.urlopen(f"https://pypi.org/pypi/{package_name}/json", timeout=timeout) as resp:
            latest_version = json.load(resp)["info"]["version"]
    except Exception:
        return  # PyPI unreachable or network error; skip

    if current_version != latest_version:
        click.secho(f"🔔 Update available: {current_version} → {latest_version}", fg="green", bold=True)
        click.secho(f"🔔 If you don't want to automatically check for updates, set SIMA_CLI_CHECK_FOR_UPDATE environment variable to 0")
        if click.confirm(f"🔔 Do you want to update {package_name} now?", default=True):
            update_package(package_name)
            exit(0)
    else:
        print('✅ sima-cli is up-to-date')
