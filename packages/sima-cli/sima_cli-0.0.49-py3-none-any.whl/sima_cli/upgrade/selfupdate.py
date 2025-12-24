#!/usr/bin/env python3
"""
sima-cli Self-Update
====================

Manual self-update mechanism for sima-cli.

Supports:
  • Default → latest release from PyPI
  • -v <version> → specific version from PyPI
  • -m <url>     → manual wheel URL
Respects the global `--internal` flag for authenticated internal updates.
"""
import os
import sys
import tempfile
import subprocess
import click
from rich.console import Console

from sima_cli.download.downloader import download_file_from_url

console = Console()


@click.command("selfupdate")
@click.option(
    "-v", "--version",
    help="Version to update to (cannot be combined with --manual-url)."
)
@click.option(
    "-m", "--manual-url",
    help="Manual wheel URL (cannot be combined with --version)."
)
@click.pass_context
def selfupdate(ctx, version, manual_url):
    """
    Update sima-cli manually from PyPI or a direct wheel URL.

    This command downloads and installs a new version of sima-cli.
    You may update to the latest PyPI release, update to a specific
    version, or install from a manually supplied wheel URL.

    \b
    Update modes:
      - No options: update to the latest PyPI release
      - --version: update to the specified PyPI version
      - --manual-url: install from a direct wheel link
    
    \b
    Rules:
      - --version and --manual-url cannot be used together
      - Manual URLs must point to a valid .whl file
      - Internal builds may be installed using the global -i flag

    \b
    Examples:

      sima-cli selfupdate

      sima-cli selfupdate -v 0.0.45

      sima-cli selfupdate -m https://.../sima_cli-0.0.46.whl

    """
    if version and manual_url:
        console.print("[red]❌ Error:[/red] Cannot use -v and -m together.")
        sys.exit(1)

    # Retrieve global --internal flag from the parent CLI
    internal = ctx.obj.get("internal", False)
    python_exec = sys.executable

    try:
        # Case 1: Manual URL (direct .whl)
        if manual_url:
            _update_from_url(python_exec, manual_url, internal)

        # Case 2: Version + internal → build internal Artifactory URL
        elif version and internal:
            url = (
                f"https://artifacts.eng.sima.ai:443/artifactory/sima-pypi/"
                f"sima-cli/sima_cli-{version}-py3-none-any.whl"
            )
            console.print(
                f"[cyan]📦 Detected internal mode — fetching version {version} from Artifactory[/cyan]"
            )
            _update_from_url(python_exec, url, internal)

        # Case 3: Version only → PyPI
        elif version:
            _update_from_pypi(python_exec, version)

        # Case 4: Default → latest PyPI
        else:
            _update_from_pypi(python_exec)

    except Exception as e:
        console.print(f"[red]❌ Update failed:[/red] {e}")
        sys.exit(1)


def _update_from_pypi(python_exec, version=None):
    """Force reinstall sima-cli from PyPI."""
    package = "sima-cli"
    target = f"{package}=={version}" if version else package

    console.print(f"[cyan]⬇️  Updating {package} from PyPI...[/cyan]")
    if version:
        console.print(f"[dim]Requested version:[/dim] [white]{version}[/white]")

    cmd = [python_exec, "-m", "pip", "install", "--upgrade", "--force-reinstall", target]
    subprocess.run(cmd, check=True)
    console.print(f"[green]✅ sima-cli successfully updated from PyPI in {python_exec}.[/green]")

def _update_from_url(python_exec, url, internal=False):
    """
    Download a wheel from a URL (authenticated if internal) and install it.

    If the provided URL is actually a local path to an existing .whl file,
    the download step is skipped and installation proceeds directly.
    """
    # Check if it's a local file path (absolute or relative)
    if os.path.exists(url) and url.endswith(".whl"):
        wheel_path = os.path.abspath(url)
        console.print(f"[green]📦 Local wheel detected:[/green] {wheel_path}")
    else:
        console.print(f"[cyan]⬇️  Fetching wheel from:[/cyan] {url}")
        tmpdir = tempfile.mkdtemp(prefix="sima_selfupdate_")

        # ✅ Use built-in downloader (auth, resume, tqdm)
        wheel_path = download_file_from_url(url, dest_folder=tmpdir, internal=internal)
        console.print(f"[green]✅ Download complete:[/green] {wheel_path}")

    console.print("[cyan]📦 Installing wheel...[/cyan]")

    # Add --no-deps to avoid breaking shared environments
    cmd = [python_exec, "-m", "pip", "install", "--force-reinstall", wheel_path]
    subprocess.run(cmd, check=True)

    console.print(f"[green]✅ sima-cli successfully updated from wheel in {python_exec}.[/green]")

def register_selfupdate_command(main):
    """Attach the 'selfupdate' command to the main Click CLI."""
    main.add_command(selfupdate)
