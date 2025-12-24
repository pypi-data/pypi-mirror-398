#!/usr/bin/env python3
"""
exec.py — interactive launcher for running commands inside SiMa SDK containers.
"""

import subprocess
import sys
from typing import Optional
from rich.console import Console
from sima_cli.sdk.utils import select_containers, get_all_containers

console = Console()

# ─────────────────────────────────────────────
# Core executer
# ─────────────────────────────────────────────
def exec_container_cmd(ctx, keyword: str, cmd: Optional[str] = None):
    """
    Find a running container matching the given SDK keyword (e.g. mpk, yocto),
    optionally filtering by version (from ctx.obj['version_filter']),
    and execute the command or open a shell inside it.
    """
    version_filter = None
    if ctx and getattr(ctx, "obj", None):
        version_filter = ctx.obj.get("version_filter")

    containers = get_all_containers(running_containers_only=True)
    if not containers:
        console.print("[yellow]⚠️  No running containers found.[/yellow]")
        sys.exit(0)

    # ──────────────────────────────────────────────
    # Step 1: Filter by SDK keyword (tool name)
    # ──────────────────────────────────────────────
    matches = []
    for c in containers:
        name = c.get("Names") or c.get("Name") or c.get("name") or ""
        image = c.get("Image") or c.get("image") or ""
        if keyword.lower() in name.lower() or keyword.lower() in image.lower():
            matches.append(c)

    # ──────────────────────────────────────────────
    # Step 2: Filter by version if provided
    # ──────────────────────────────────────────────
    if version_filter:
        filtered = []
        for c in matches:
            name = c.get("Names") or c.get("Name") or ""
            image = c.get("Image") or ""
            if version_filter.lower() in name.lower() or version_filter.lower() in image.lower():
                filtered.append(c)
        matches = filtered

        console.print(
            f"[dim]🔍 Version filter applied:[/dim] [bold cyan]{version_filter}[/bold cyan]"
        )

    if not matches:
        console.print(
            f"[red]❌ No running containers found for '{keyword}'"
            + (f" with version '{version_filter}'" if version_filter else "")
            + ".[/red]"
        )
        sys.exit(1)

    # ──────────────────────────────────────────────
    # Step 3: Prompt user if multiple matches
    # ──────────────────────────────────────────────
    if len(matches) > 1:
        selected_name = select_containers(matches, single_select=True)
    else:
        selected_name = matches[0].get("Names") or matches[0].get("Name") or matches[0].get("name")

    # ──────────────────────────────────────────────
    # Step 4: Execute command or attach shell
    # ──────────────────────────────────────────────
    if cmd:
        console.print(
            f"[cyan]▶ Executing command in container:[/cyan] [bold]{selected_name}[/bold]"
        )
        exec_cmd = ["docker", "exec", "-it", selected_name, "bash", "-c", cmd]
    else:
        console.print(
            f"[cyan]▶ Attaching to container:[/cyan] [bold]{selected_name}[/bold]"
        )
        exec_cmd = ["docker", "exec", "-it", selected_name, "bash", "-l"]

    try:
        subprocess.run(exec_cmd)
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Interrupted by user.[/yellow]")

        console.print("\n[yellow]⚠️ Interrupted by user.[/yellow]")