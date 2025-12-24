#!/usr/bin/env python3

import os
import subprocess
from rich.console import Console
from rich.panel import Panel

from sima_cli.sdk.preinstall import syscheck
from sima_cli.sdk.config import IMAGE_CONFIG

from sima_cli.sdk.utils import (
    create_config_json,
    find_available_ports,
    get_container_status,
    get_workspace,
    get_local_sima_images,
    prompt_image_selection,
    confirm_to_remove_exiting_container,
    sanitize_container_name,
    ensure_simasdkbridge_network,
    start_docker_container,
    print_section,
    extract_short_name
)

# ─────────────────────────────────────────────
# Entrypoint for setup/start
# ─────────────────────────────────────────────
def is_container_running(name: str) -> bool:
    """Return True if the container is running."""
    try:
        status = subprocess.check_output(
            ["docker", "inspect", "-f", "{{.State.Running}}", name],
            text=True
        ).strip()
        return status == "true"
    except subprocess.CalledProcessError:
        return False

def setup_and_start(noninteractive: bool = False, start_only: bool = False, yes_to_all: bool = False):
    """Main entry for SDK setup and container start."""

    console = Console()

    if not start_only:
        console.print(Panel("🔧 SiMa.ai SDK Setup", border_style="cyan", expand=False))
        ensure_simasdkbridge_network()
        syscheck(force_install=yes_to_all)

    images = get_local_sima_images()
    selected_images = prompt_image_selection(images, noninteractive)


    # Step 2: Check running containers
    print("\n🔍 Checking for running SDK containers...")
    container_statuses = get_container_status()

    if container_statuses:
        count = len(container_statuses)
        print(f"✅ Found {count} SDK container{'s' if count > 1 else ''}:")
        for cname, status in container_statuses.items():
            print(f"   • {cname:<30} | {status}")
    else:
        print("ℹ️  No Running SDK containers found.")

    # ──────────────────────────────────────────────
    # Start containers
    # ──────────────────────────────────────────────
    workspace = get_workspace(yes_to_all)
    uid = os.getuid() if hasattr(os, "getuid") else 900
    gid = os.getgid() if hasattr(os, "getgid") else 900
    
    for img in selected_images:
        container_name = sanitize_container_name(img)
        print_section(f"🔄 CONTAINER START SEQUENCE for {container_name}")
        existing_container = confirm_to_remove_exiting_container(container_name, yes_to_all)

        if existing_container == None:
            # Get image configuration
            config = IMAGE_CONFIG.get(extract_short_name(img), {"privileged": False, "port_mapping_required": False})

            # Dynamically allocate a free port if required
            port = find_available_ports(1)[0] if config["port_mapping_required"] else 0

            create_config_json(file_path="config.json", selected_images=selected_images, port=port)

            start_docker_container(
                uid=uid,
                gid=gid,
                port=port,
                workspace=workspace,
                image=img,
                privileged=config["privileged"],
                port_mapping_required=config["port_mapping_required"],
            )
        else:
            if not is_container_running(existing_container):
                subprocess.run(["docker", "start", existing_container], check=True)

            if len(selected_images) == 1:
                exec_cmd = ["docker", "exec", "-it", existing_container, "bash", "-l"]
                subprocess.run(exec_cmd)

    console.print("\n[bold green]✅ All selected containers started successfully![/bold green]")

if __name__ == "__main__":
    setup_and_start()
