#!/usr/bin/env python3
"""
SiMa.ai SDK Management Commands
──────────────────────────────────────────────────────────
Manage local SDK containers and tools.

Usage:
    sima-cli sdk setup : setting up SDK & start
    sima-cli sdk start : start one or more SDK containers
    sima-cli sdk stop : stop one or more SDK containers
    sima-cli sdk remove : remove the container and its image to free up storage space
    sima-cli sdk mpk : go to mpk container
    sima-cli sdk model : go to model container
    sima-cli sdk yocto : go to Yocto container
    sima-cli sdk elxr : go to elxr container
"""

import click
from rich.console import Console
from sima_cli.sdk.install import setup_and_start
from sima_cli.sdk.cmdexec import exec_container_cmd
from sima_cli.sdk.uninstall import remove_containers, remove_unused_images
from sima_cli.sdk.stop import stop_containers
from sima_cli.sdk.utils import get_all_containers
from rich.table import Table
from sima_cli.utils.env import get_environment_type
from sima_cli.utils.docker import check_and_start_docker
from sima_cli.sdk.config import IMAGE_CONFIG

console = Console()

# ------------------------------------------------------------
# Group Definition
# ------------------------------------------------------------
@click.group(hidden=True, context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.option(
    "-v", "--version",
    "version_filter",
    help="Filter SDK containers by version tag (e.g. latest_master).",
    required=False
)
@click.pass_context
def sdk(ctx, version_filter):
    """
    Manage and launch SiMa SDK 2.0 container environments (Beta).

    This group provides access to the full SDK 2.0 toolchain, including
    setup, container orchestration, tool-specific shells (MPK, model,
    Yocto, eLxr), and hybrid `.sima` script execution. These commands are
    intended for SDK 2.0+ users only.

    \c Host platforms only.

    Typical Use Cases
    
        • Setting up a full SDK toolchain

        • Starting one or more SDK containers

        • Stopping or removing SDK containers and cached images

        • Launching MPK, model, Yocto, or eLxr shells

    """
    ctx.ensure_object(dict)
    ctx.obj["version_filter"] = version_filter
    check_and_start_docker()

# ------------------------------------------------------------
# Helper functions 
# ------------------------------------------------------------

def launch_sdk_tool(tool: str, cmd, ctx):
    """
    Launch a selected SDK tool container, optionally executing a command inside it.
    If no command is provided, defaults to an interactive bash login shell.
    """
    # Normalize click's tuple argument
    if not cmd:
        cmd_str = "bash -l"
    elif isinstance(cmd, (list, tuple)):
        cmd_str = " ".join(cmd)
    else:
        cmd_str = str(cmd)

    exec_container_cmd(ctx, tool, cmd_str)


# ------------------------------------------------------------
# Subcommands
# ------------------------------------------------------------

@sdk.command(name="setup")
@click.option(
    "--noninteractive", "-n",
    is_flag=True,
    help="Run in non-interactive mode (auto-select defaults)."
)
@click.option(
    "-y", "--yes",
    is_flag=True,
    help="Skip confirmation before starting the container."
)
@click.pass_context
def setup(ctx, yes, noninteractive):
    """Initialize SDK environment and select components to start."""
    setup_and_start(noninteractive=noninteractive, yes_to_all=yes)

@sdk.command(name="start")
@click.option(
    "--noninteractive", "-n",
    is_flag=True,
    help="Run in non-interactive mode (auto-select defaults)."
)
@click.option(
    "-y", "--yes",
    is_flag=True,
    help="Skip confirmation before starting the container."
)
@click.pass_context
def start(ctx, yes, noninteractive):
    """Select and start one or more SDK containers."""
    setup_and_start(noninteractive=noninteractive,start_only=True, yes_to_all=yes)

@sdk.command(
    name="stop",
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True}
)
@click.argument("sdk", required=False)
@click.option(
    "-y", "--yes",
    is_flag=True,
    help="Skip confirmation before stopping SDK containers."
)
@click.pass_context
def stop(ctx, sdk, yes):
    """
    Stop one or more running SDK containers.

    Examples:
        sima-cli sdk stop
        sima-cli sdk stop yocto
        sima-cli sdk -v latest_develop stop mpk -y
    """
    # Confirmation prompt unless -y provided
    if not yes:
        confirm = click.confirm(
            "⚠️  This will stop one or more running SDK containers. Continue?",
            default=False,
        )
        if not confirm:
            console.print("❌ Operation cancelled.", style="bold yellow")
            return

    stop_containers(ctx, sdk)

@sdk.command(
    name="remove",
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True}
)
@click.argument("sdk", required=False)
@click.option(
    "-y", "--yes",
    is_flag=True,
    help="Skip confirmation before removing SDK containers/images."
)
@click.pass_context
def remove(ctx, sdk, yes):
    """
    Remove SDK containers and images.
    Example:
        sima-cli sdk remove yocto
        sima-cli sdk -v latest_develop remove mpk -y
    """
    # Confirm unless -y is provided
    if not yes:
        confirm = click.confirm(
            "⚠️  This will remove matching SDK containers and cached images. Continue?",
            default=False,
        )
        if not confirm:
            console.print("❌ Operation cancelled.", style="bold yellow")
            return

    # Call version-aware remover
    remove_containers(ctx, sdk)
    remove_unused_images()


@sdk.command(
    name="mpk",
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True}
)
@click.argument("cmd", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def mpk(ctx, cmd):
    """Access MPK CLI toolset container for managing and building pipelines along with the device manager.
    It also includes the plugins zoo and the Performance Estimator tool.
    """
    launch_sdk_tool("mpk", cmd, ctx)


@sdk.command(
    name="model",
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True}
)
@click.argument("cmd", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def model(ctx, cmd):
    """Launch the Model SDK tool environment."""
    launch_sdk_tool("model", cmd, ctx)


@sdk.command(
    name="yocto",
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True}
)
@click.argument("cmd", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def yocto(ctx, cmd):
    """Launch the Yocto SDK tool environment."""
    launch_sdk_tool("yocto", cmd, ctx)


@sdk.command(
    name="elxr",
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True}
)
@click.argument("cmd", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def elxr(ctx, cmd):
    """Launch the eLxr SDK tool environment."""
    launch_sdk_tool("elxr", cmd, ctx)


@sdk.command(name="run")
@click.argument("script_path", type=click.Path(exists=True))
@click.pass_context
def run(ctx, script_path):
    """Run a .sima hybrid script with local + container commands."""
    from sima_cli.sdk.script import execute_script
    execute_script(ctx, script_path)

@sdk.command(name="ls")
@click.pass_context
def list_sdk(ctx):
    """
    List installed and running SiMa SDK containers.
    Shows SDK name, version, and running status.
    """
    containers = get_all_containers(running_containers_only=False)
    if not containers:
        console.print("[yellow]⚠️ No SDK containers found.[/yellow]")
        return

    table = Table(title="📦 Installed SDK Containers", show_lines=False, header_style="bold cyan")
    table.add_column("SDK", style="white", no_wrap=True)
    table.add_column("Version", style="magenta")
    table.add_column("Running", style="green", justify="center")

    for c in containers:
        name = c.get("Names") or c.get("Name") or c.get("name", "")
        image = c.get("Image", "")
        state_field = (c.get("State") or "").lower().strip()
        status_field = (c.get("Status") or "").lower().strip()

        # ──────────────────────────────────────────────
        # 1. Identify SDK name + version
        # ──────────────────────────────────────────────
        sdk_name = image.split("/")[-1].split(":")[0].replace("sima-docker-", "")
        version = image.split(":")[1] if ":" in image else "unknown"

        # ──────────────────────────────────────────────
        # 2. Determine running state robustly
        # ──────────────────────────────────────────────
        if any(word in status_field for word in ("up", "running")) or state_field == "running":
            running = "✅"
        else:
            running = "❌"

        # ──────────────────────────────────────────────
        # 3. Skip non-SDK containers
        # ──────────────────────────────────────────────
        if not sdk_name or sdk_name not in IMAGE_CONFIG:
            continue

        table.add_row(sdk_name, version, running)

    console.print()
    console.print(table)

# ------------------------------------------------------------------------------------------------------------
# Register the group to main CLI entrypoint, skip this group if it's running inside the SDK container already
# ------------------------------------------------------------------------------------------------------------
def register_sdk_commands(main):
    """Attach the SDK command group to the main Click CLI on the host platforms."""
    env, _ = get_environment_type()

    if env == 'host':
        main.add_command(sdk)
