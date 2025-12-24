import sys
import click
import os
import subprocess
from pathlib import Path

from sima_cli.update.updater import download_image
from sima_cli.utils.env import is_pcie_host

def _check_driver_installation():
    """
    Checks whether the PCIe host driver (sima_mla_drv) and related components are correctly installed.

    Returns:
        dict: A dictionary with validation results for gstreamer, kernel module, and PCI device.
    """
    results = {}

    # 1. Check GStreamer plugin
    try:
        gst_output = subprocess.check_output(["gst-inspect-1.0", "pciehost"], stderr=subprocess.STDOUT, text=True)
        if "pciehost" in gst_output:
            results["gstreamer"] = {
                "success": True,
                "message": "✅ GStreamer plugin 'pciehost' is installed."
            }
        else:
            results["gstreamer"] = {
                "success": False,
                "message": "❌ GStreamer plugin 'pciehost' not found."
            }
    except subprocess.CalledProcessError as e:
        results["gstreamer"] = {
            "success": False,
            "message": f"❌ GStreamer check failed: {e.output.strip()}"
        }

    # 2. Check kernel module
    try:
        modinfo_output = subprocess.check_output(["modinfo", "sima_mla_drv"], stderr=subprocess.STDOUT, text=True)
        if "filename:" in modinfo_output and "sima_mla_drv" in modinfo_output:
            results["kernel_module"] = {
                "success": True,
                "message": "✅ Kernel module 'sima_mla_drv' is installed."
            }
        else:
            results["kernel_module"] = {
                "success": False,
                "message": "❌ Kernel module 'sima_mla_drv' not found."
            }
    except subprocess.CalledProcessError as e:
        results["kernel_module"] = {
            "success": False,
            "message": f"❌ Kernel module check failed: {e.output.strip()}"
        }

    # 3. Check PCI device presence
    try:
        lspci_output = subprocess.check_output(["lspci", "-vd", "1f06:abcd"], stderr=subprocess.STDOUT, text=True)
        if "sima_mla_drv" in lspci_output or "1f06:abcd" in lspci_output:
            results["pci_device"] = {
                "success": True,
                "message": "✅ PCIe device (1f06:abcd) detected and bound to 'sima_mla_drv'."
            }
        else:
            results["pci_device"] = {
                "success": False,
                "message": "❌ PCIe device not detected."
            }
    except subprocess.CalledProcessError as e:
        results["pci_device"] = {
            "success": False,
            "message": f"❌ PCIe device check failed: {e.output.strip()}"
        }

    return results

def _print_driver_validation_table(results: dict):
    """
    Prints the driver validation results in a table format with fixed-width columns.
    """
    print("\nDriver Installation Validation:\n")
    print(f"{'Component':<20} | {'Status':<10} | {'Details'}")
    print("-" * 60)

    for section, result in results.items():
        component = section.replace("_", " ").title()
        status = "PASS" if result["success"] else "FAIL"
        message = result["message"]
        print(f"{component:<20} | {status:<10} | {message}")

def install_hostdriver(version: str, internal: bool = False):
    """
    Install PCIe host driver on supported platforms.

    This function is only valid on PCIe host machines. It downloads the appropriate image
    package and installs the host driver script if present.

    Args:
        version (str): Firmware version string (e.g., "1.6.0").
        internal (bool): Whether to use internal sources for the download.

    Raises:
        RuntimeError: If the platform is not supported or the driver script is missing.
    """
    if not is_pcie_host():
        click.echo("❌ This command is only supported on PCIe host Linux machines.")
        sys.exit(1)

    try:
        # Step 1: Install system dependencies
        click.echo("🔧 Installing required system packages...")
        try:
            subprocess.run([
                "sudo", "apt-get", "update"
            ], check=True)
            subprocess.run([
                "sudo", "apt-get", "install", "-y",
                "make", "cmake", "gcc", "g++", "dkms", "doxygen",
                "libjson-c-dev", "libjsoncpp-dev", "build-essential", "linux-headers-generic"
            ], check=True)
            click.echo("✅ Dependencies installed successfully.")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"❌ Failed to install dependencies: {e}")

        # Step 2: Download driver package which is part of the firmware release.
        click.echo(f"⬇️  Downloading host driver package for version {version}...")
        extracted_files = download_image(version_or_url=version, board="davinci", swtype="yocto", internal=internal)

        # Find the host driver script in extracted files
        script_path = next((f for f in extracted_files if f.endswith("sima_pcie_host_pkg.sh")), None)

        if not script_path or not os.path.isfile(script_path):
            raise RuntimeError("sima_pcie_host_pkg.sh not found in the downloaded package.")

        click.echo(f"📦 Host driver script found: {script_path}")
        click.confirm("⚠️  This will install drivers on your system using sudo. Continue?", abort=True)

        # Make sure the script is executable
        os.chmod(script_path, 0o755)

        # Run the script with sudo
        subprocess.run(["sudo", script_path], check=True)

        click.echo("✅ Host driver installation completed.")

        results = _check_driver_installation()
        _print_driver_validation_table(results)

    except Exception as e:
        raise RuntimeError(f"❌ Failed to install host driver: {e}")

