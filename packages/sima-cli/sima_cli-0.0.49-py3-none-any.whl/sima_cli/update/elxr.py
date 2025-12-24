import subprocess
import click
from typing import Optional, List
import re

from sima_cli.utils.env import is_devkit_running_elxr


def _get_available_palette_versions() -> List[str]:
    """Parse apt policy output and return available simaai-palette-modalix versions."""
    try:
        result = subprocess.run(
            ["apt", "policy", "simaai-palette-modalix"],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        click.echo("❌ Failed to run: apt policy simaai-palette-modalix")
        return []

    versions: List[str] = []
    capture = False

    # Matches lines like:
    #   "     2.0.0~git202511281205.97d3129-755 950"
    #   "*** 2.0.0~git202511271206.97d3129-751 950"
    pattern = re.compile(r"^\s*(\*{3}\s+)?([0-9A-Za-z.~+-]+)\s+")

    for line in result.stdout.splitlines():
        line = line.rstrip()

        if "Version table:" in line:
            capture = True
            continue

        if not capture:
            continue

        m = pattern.match(line)
        if not m:
            continue

        ver = m.group(2)

        # Skip pure numeric entries (950, 100, etc.)
        if ver.isdigit():
            continue

        versions.append(ver)

    # Remove duplicates, preserve order
    return list(dict.fromkeys(versions))


def print_current_versions():
    p1 = subprocess.Popen(
        ["dpkg", "-l"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    p2 = subprocess.Popen(
        ["grep", "simaai"],
        stdin=p1.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    p1.stdout.close()
    out, err = p2.communicate()

    click.secho('Current SiMa component versions:', fg='green')
    click.secho(out)

def update_elxr(version_or_url: Optional[str]):
    """
    Update packages on an ELXR-based devkit using simaai-ota.
    Enhanced:
    - "Update to a specific version" shows available versions from apt policy.
    - Adds Back and Cancel options.
    """
    if not is_devkit_running_elxr():
        click.echo("ℹ️  Not an ELXR devkit, skipping update")
        return

    print_current_versions()

    from InquirerPy import inquirer

    # Check connectivity
    if subprocess.call(["ping", "-c", "1", "deb.debian.org"],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL) != 0:
        click.echo("⚠️  ELXR devkit not connected to the network, skipping update")
        return

    # -----------------------------
    # Main interaction loop
    # -----------------------------
    while True:

        # If user did not pass a version, show the update type menu
        if version_or_url is None:
            choice = inquirer.select(
                message="How would you like to update this ELXR devkit?",
                choices=[
                    {"name": "Update all packages (no reinstall if up-to-date)", "value": "normal"},
                    {"name": "Update all packages (force reinstall)", "value": "force"},
                    {"name": "Update to a specific simaai-palette version", "value": "version"},
                    {"name": "Fix u-boot environment (force reinstall + overwrite)", "value": "fix-uboot"},
                    {"name": "Cancel", "value": "cancel"},
                ],
                default="normal"
            ).execute()

            if choice == "cancel":
                click.echo("❌ Update cancelled")
                return

            if choice == "normal":
                cmd = ["simaai-ota"]
                desc = "Update all packages (no reinstall)"
                break

            elif choice == "force":
                cmd = ["simaai-ota", "-f"]
                desc = "Update all packages (force reinstall)"
                break

            elif choice == "fix-uboot":
                cmd = ["simaai-ota", "-f", "-o"]
                desc = "Fix u-boot env (force reinstall + overwrite)"
                break

            elif choice == "version":
                # -----------------------------
                # Fetch and display version list
                # -----------------------------
                versions = _get_available_palette_versions()

                if not versions:
                    click.echo("❌ No versions found in APT policy, aborting.")
                    return

                # Add back and cancel
                version_choices = (
                    [{"name": "⬅️  Back to previous menu", "value": "back"}] +
                    [{"name": v, "value": v} for v in versions] +
                    [{"name": "❌ Cancel", "value": "cancel"}]
                )

                selected = inquirer.select(
                    message="Available simaai-palette-modalix versions:",
                    choices=version_choices,
                ).execute()

                if selected == "back":
                    # Return to main menu loop
                    continue

                if selected == "cancel":
                    click.echo("❌ Update cancelled")
                    return

                # A version was selected
                cmd = ["simaai-ota", "-v", selected]
                desc = f"Update to specific version {selected}"
                break

        else:
            # version_or_url specified by user (non-interactive)
            cmd = ["simaai-ota", "-v", version_or_url]
            desc = f"Update to specific version {version_or_url}"
            break

    # -----------------------------
    # Execute update
    # -----------------------------
    cmd = ["sudo"] + cmd
    click.echo(f"➡️  {desc}\n   " + click.style(f"Running: {' '.join(cmd)}", fg="cyan"))

    if subprocess.call(["sudo", "-n", "true"],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL) != 0:
        click.echo("ℹ️  sudo may prompt you for a password...")

    subprocess.check_call(cmd)
    click.echo("✅ ELXR update completed successfully")
