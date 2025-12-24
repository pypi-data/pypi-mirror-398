# utils.py
from typing import Dict, List, Set
import os
import sys
import time
import getpass
import shutil
import socket
import subprocess
import json
import re
import platform
from collections import defaultdict

from sima_cli.sdk.config import (
    IMAGE_NAMES,
    IMAGE_CONFIG,
    BASELINE_IMAGE
)


FILTER_KEYWORDS = ["elxr", "yocto", "mpk", "modelsdk"]

def check_os() -> str:
    """Detect and return the current operating system."""
    if sys.platform.startswith("linux"):
        return "linux"
    if sys.platform == "darwin":
        return "macos"
    if sys.platform in ("win32", "cygwin"):
        return "windows"
    return "not_supported"

def check_and_start_docker(platform_os):
    """
    Check if Docker daemon is running and start it if necessary.

    - Linux: optionally uses `sudo systemctl restart docker.service`
    - macOS: uses `open -a Docker` (may require sudo if permission denied)
    - Windows: launches Docker Desktop executable
    """

    # Step 1: Check if Docker is already running
    if is_docker_running():
        print("✅ Docker daemon is running.")
        return

    # Step 2: Docker not running → ask user if they want to start it
    response = input("⚠️  Docker daemon is not running. Do you want to start it? [Y/n]: ").strip().lower()
    if response in {"n", "no"}:
        print("❌ Please start Docker manually and re-run the script.")
        print_manual_start_instructions(platform_os)
        sys.exit(1)

    # Step 3: Ask if sudo is allowed (for Linux/macOS)
    use_sudo = False
    if platform_os in {"linux", "macos"}:
        sudo_resp = input("🔒 Starting Docker may require sudo privileges. Grant sudo access? [Y/n]: ").strip().lower()
        use_sudo = sudo_resp not in {"n", "no"}  # Default is YES

    print("⏳ Attempting to start Docker...")

    # Step 4: Platform-specific handling
    if platform_os == "linux":
        docker_start_cmd = ["systemctl", "restart", "docker.service"]
        if use_sudo:
            docker_start_cmd.insert(0, "sudo")

        for attempt in range(1, 4):
            result = subprocess.run(docker_start_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if result.returncode == 0 and is_docker_running():
                print("✅ Docker daemon started successfully.")
                return
            print(f"Retrying Docker start... Attempt {attempt}/3")
            time.sleep(5)

        print("❌ Failed to start Docker service after 3 attempts.")
        print_manual_start_instructions(platform_os)
        sys.exit(1)

    elif platform_os == "windows":
        docker_exe = r"C:\Program Files\Docker\Docker\Docker Desktop.exe"
        if not os.path.exists(docker_exe):
            print(f"❌ Docker Desktop executable not found at:\n   {docker_exe}")
            print("Please install Docker Desktop and try again.")
            sys.exit(1)

        print("ℹ️ Launching Docker Desktop on Windows...")
        subprocess.Popen(["cmd.exe", "/c", "start", "", docker_exe])
        print("⏳ Waiting for Docker Desktop to initialize...")

        for i in range(6):
            time.sleep(10)
            if is_docker_running():
                print("✅ Docker daemon started successfully.")
                return
            print(f"⌛ Checking again ({i+1}/6)...")

        print("❌ Docker daemon did not start after waiting.")
        print_manual_start_instructions(platform_os)
        sys.exit(1)

    elif platform_os == "macos":
        docker_app_path = "/Applications/Docker.app"
        if not os.path.exists(docker_app_path):
            print(f"❌ Docker Desktop not found at {docker_app_path}")
            print("Please install Docker Desktop for macOS and try again.")
            sys.exit(1)

        start_cmd = ["open", "-a", "Docker"]
        if use_sudo:
            start_cmd.insert(0, "sudo")

        print("ℹ️ Starting Docker Desktop for macOS...")
        subprocess.Popen(start_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        for i in range(10):
            time.sleep(10)
            if is_docker_running():
                print("✅ Docker daemon started successfully.")
                return
            print(f"⌛ Checking again ({i+1}/10)...")

        print("❌ Docker daemon did not start after waiting.")
        print_manual_start_instructions(platform_os)
        sys.exit(1)

    else:
        print(f"❌ Unsupported platform: {platform_os}")
        sys.exit(1)


def print_manual_start_instructions(platform_os):
    """Print platform-specific manual instructions for starting Docker."""
    print("\n🧭 Manual Start Instructions:")
    if platform_os == "linux":
        print("   ➤ Run:  sudo systemctl start docker.service")
        print("   ➤ Verify: docker info")
    elif platform_os == "macos":
        print("   ➤ Open Docker Desktop manually from Applications folder.")
        print("   ➤ Or run:  open -a Docker")
    elif platform_os == "windows":
        print("   ➤ Launch Docker Desktop from the Start menu.")
    print("   Then re-run this installer once Docker is active.\n")
        
def docker_login_jfrog(host: str, user: str, password: str) -> None:
    print(f"\n🔑 Logging in to JFrog Docker registry: {host}")
    # Use --password-stdin to avoid exposing the password in the process list
    p = subprocess.Popen(
        ["docker", "login", host, "-u", user, "--password-stdin"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    out, err = p.communicate(input=password or "")
    if p.returncode != 0:
        print("❌ Docker login failed.")
        if err:
            print(err.strip())
        sys.exit(1)
    print("✅ Docker login successful")

def baseline_is_present(
    installed_refs: Set[str],
    version: str,
    images_user_will_remove: Set[str],
) -> bool:
    # True if mpk_cli_toolset:<version> exists AND the user did not choose to remove it
    installed = any(ref.endswith(f"{BASELINE_IMAGE}:{version}") for ref in installed_refs)
    not_removed = BASELINE_IMAGE not in images_user_will_remove
    return installed and not_removed

def prompt_multi_select(baseline_present: bool = False) -> List[str]:
    """
    Prompts the user to select one or more items by number or name (comma-separated).

    Rules:
      - If '0' or 'All' is selected, all items are included automatically.
      - Enforce baseline (mpk_cli_toolset) unless `baseline_present` is True.
      - Displays detailed information (name, description, sizes) for each container.
    """
    while True:
        print("\nSelect one or more options (numbers or names, comma-separated):\n")
        # Calculate total sizes for "All"
        total_size = sum(cfg.get("size", 0) for cfg in IMAGE_CONFIG.values())
        total_pull_space = sum(cfg.get("pull_space", 0) for cfg in IMAGE_CONFIG.values())

        print("0. All")
        print(
            f"    📦 Description      : Select all available components\n"
            f"    💾 Final image size : {total_size} GB (runtime requirement)\n"
            f"    📂 Pull space need  : {total_pull_space} GB (temporary during pull)\n"
        )

        # Display image information dynamically from IMAGE_CONFIG
        for idx, (img, cfg) in enumerate(IMAGE_CONFIG.items(), start=1):
            print(
                f"{idx}. {cfg['display']}\n"
                f"    📦 Description      : {cfg['description']}\n"
                f"    💾 Final image size : {cfg.get('size', 'N/A')} GB (runtime requirement)\n"
                f"    📂 Pull space need  : {cfg.get('pull_space', 'N/A')} GB (temporary during pull)\n"
            )

        raw = input(
            "\nYour selection (e.g., 1,3 or yocto,ModelSDK, or 0 for All):\n"
            "⚠️  **Important Note:**\n"
            "   1. If there are any existing containers associated with your selection, "
            "they will be stopped, removed, and relaunched automatically.\n"
            "   2. If you need to save any data from an existing container, "
            "please save it **now** and run this setup again.\n"
            "   3. If you need to exit the setup at any point, press **CTRL+C**.\n"
            "Enter your choice: "
        ).strip()

        if not raw:
            retry = input("⚠️  No selection provided. Try again? (Y/n): ").strip().lower()
            if retry in {"n", "no"}:
                print("Exiting without making any selections.")
                sys.exit(0)
            continue

        # ---- Handle "All" selection early ----
        if raw.lower() in {"0", "all"}:
            print("\nℹ️  'All' selected → All components will be included.")
            return list(IMAGE_CONFIG.keys())

        # ---- Process comma-separated custom selections ----
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        selected_images: List[str] = []
        invalid_entries = []

        # Build lookups
        display_to_internal = {cfg["display"].lower(): img for img, cfg in IMAGE_CONFIG.items()}
        name_lookup = {img.lower(): img for img in IMAGE_CONFIG.keys()}

        for part in parts:
            if part.isdigit():
                idx = int(part)
                if 1 <= idx <= len(IMAGE_CONFIG):
                    selected_images.append(list(IMAGE_CONFIG.keys())[idx - 1])
                else:
                    invalid_entries.append(part)
            else:
                # Try display name match
                disp_match = display_to_internal.get(part.lower())
                if disp_match:
                    selected_images.append(disp_match)
                else:
                    # Try internal name match
                    name_match = name_lookup.get(part.lower())
                    if name_match:
                        selected_images.append(name_match)
                    else:
                        invalid_entries.append(part)

        if invalid_entries:
            print(f"\n⚠️  Invalid selection(s): {', '.join(invalid_entries)}")
            retry = input("Do you want to retry? (Y/n): ").strip().lower()
            if retry in {"n", "no"}:
                print("Exiting due to invalid selections.")
                sys.exit(0)
            continue

        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for img in selected_images:
            if img not in seen:
                seen.add(img)
                deduped.append(img)

        # ---- Baseline enforcement ----
        baseline_image = next((k for k, v in IMAGE_CONFIG.items() if v.get("baseline")), None)
        if not baseline_present and baseline_image and baseline_image not in deduped:
            baseline_display = IMAGE_CONFIG[baseline_image]["display"]
            print(f"\n⚠️  You did not select the required baseline component: '{baseline_display}'.")
            add_baseline = input(f"Would you like to add '{baseline_display}' now? (Y/n): ").strip().lower()
            if add_baseline in {"y", "yes", ""}:
                deduped.insert(0, baseline_image)
            else:
                confirm_exit = input("Do you want to exit instead? (Y/n): ").strip().lower()
                if confirm_exit in {"y", "yes", ""}:
                    print("Exiting without making selections.")
                    sys.exit(0)
                else:
                    print("Let's try the selection again.")
                    continue

        return deduped

def run_command(cmd, capture_output=False):
    """Run a shell command and return output if requested."""
    try:
        if capture_output:
            return subprocess.check_output(cmd, text=True).strip()
        else:
            subprocess.run(cmd, check=True)
            return None
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {' '.join(cmd)}")
        if e.stderr:
            print(f"Error: {e.stderr.strip()}")
        sys.exit(1)


### Dynamic port allocation
def is_port_in_use(port):
    platform_os = check_os()
    if platform_os in ["linux", "macos"]:
        # Using lsof to check if the port is being used
        result = subprocess.run(
            ["lsof", "-i", f":{port}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        return result.returncode == 0  # If return code is 0, the port is in use
    elif platform_os == "windows":
        # Using netstat to check if the port is being used
        result = subprocess.run(
            ["netstat", "-ano", "-p", "TCP"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.stdout:
            lines = result.stdout.decode("utf-8").splitlines()
            for line in lines:
                if str(port) in line:
                    print(f"Port {port} is in use. Line: {line}")
                    return True
        return False
    else:
        print(f"Unsupported OS: {platform_os}")
        return False

def find_available_ports(count=1, start_port=49152, end_port=65535):
    """
    Find a given number of available ports within the specified range.

    Args:
        count (int): Number of free ports to return.
        start_port (int): Starting port number to check.
        end_port (int): Ending port number to check.

    Returns:
        list[int]: A list of free ports.

    Raises:
        SystemExit: If not enough free ports are found.
    """
    free_ports = []

    for port in range(start_port, end_port + 1):
        if not is_port_in_use(port):
            try:
                # Try to bind to confirm the port is truly free
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("", port))
                    free_ports.append(port)
                    if len(free_ports) == count:
                        return free_ports
            except OSError:
                continue

    print(f"❌ Could not find {count} free ports in the range {start_port}-{end_port}.")
    sys.exit(1)

def check_and_install_netstat():
    platform_os = check_os()
    
    # Check if netstat is available using shutil.which
    if shutil.which("netstat") is not None:
        print("netstat is already installed.")
        return True
    else:
        print("netstat is not installed. Attempting to install...")
        
        try:
            if platform_os == "linux":
                # For most Linux distributions, netstat is in the net-tools package
                print("Installing net-tools package...")
                subprocess.run(["sudo", "apt-get", "update"], check=True)
                subprocess.run(["sudo", "apt-get", "install", "-y", "net-tools"], check=True)
            elif platform_os == "macos":
                # For macOS, check if Homebrew is installed first
                try:
                    subprocess.run(["brew", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                except (subprocess.SubprocessError, FileNotFoundError):
                    print("Homebrew is not installed. Please install Homebrew first: https://brew.sh/")
                    return False
                
                print("Installing net-tools via Homebrew...")
                subprocess.run(["brew", "install", "net-tools"], check=True)
            elif platform_os == "windows":
                print("netstat should be pre-installed on Windows. Please check your Windows installation.")
                return False
            
            print("netstat has been installed successfully.")
            return True
        except subprocess.SubprocessError as e:
            print(f"Failed to install netstat: {e}")
            return False

def get_installed_images():
    """Get all SDK-related images installed locally."""
    output = run_command(["docker", "images", "--format", "{{.Repository}}"], capture_output=True)
    images = []
    for line in output.splitlines():
        for name in IMAGE_NAMES:
            if line.endswith(f"/{name}") or line.endswith(name):
                images.append(name)
    return sorted(set(images))

def get_container_status():
    """
    Return dict of container_name -> status, filtered by IMAGE_NAMES.
    Matches are partial (substring) matches instead of exact matches.
    """
    output = run_command(
        ["docker", "ps", "-a", "--format", "{{.Names}}:{{.Status}}"],
        capture_output=True
    )
    containers = {}
    for line in output.splitlines():
        parts = line.split(":", 1)
        if len(parts) == 2:
            name, status = parts
            # only include if the container name contains any IMAGE_NAMES entry
            if any(img in name for img in IMAGE_NAMES):
                containers[name] = status.lower()
    return containers


def get_running_containers():
    """
    Return list of currently running container names, reusing get_container_status().
    """
    all_containers = get_container_status()
    running = [
        cname for cname, status in all_containers.items()
        if "up" in status  # "up" substring covers "up x minutes/hours/days"
    ]
    return running


def get_workspace(yes_to_all=False):
    """
    Determine the workspace:
    - If at least one container is running, read from ~/.simaai/.mount
    - If a workspace is found, confirm with the user (unless yes_to_all=True)
    - Otherwise, prompt the user for a path
    """
    home = os.path.expanduser("~")
    simaai_dir = os.path.join(home, ".simaai")
    mount_file = os.path.join(simaai_dir, ".mount")

    running_containers = get_running_containers()

    # Case 1: At least one container running → read workspace
    if running_containers:
        if os.path.isfile(mount_file):
            with open(mount_file) as f:
                workspace = f.read().strip()

            if yes_to_all:
                print(f"\n📂 Detected running container. Using workspace: {workspace}")
                return workspace

            # Ask user for confirmation
            print(f"\n📂 Detected running container. Found workspace: {workspace}")
            confirm = input("Use this workspace? [Y/n]: ").strip().lower()
            if confirm in ("", "y", "yes"):
                print(f"✅ Using detected workspace: {workspace}")
                return workspace
            else:
                print("➡️  Skipping detected workspace. Proceeding to collect new path...")

        else:
            sys.exit("❌  Running containers detected but no mount file found.")
    
    # Case 2: No container running → ask user
    default_workspace = os.path.join(home, "workspace")
    if os.path.isfile(mount_file):
        with open(mount_file) as f:
            default_workspace = f.read().strip()

    while True:
        user_input = input(f"Enter workspace directory [{default_workspace}]: ").strip()
        workspace = user_input or default_workspace
        workspace = os.path.realpath(os.path.expanduser(workspace))

        if os.path.isdir(workspace):
            print(f"✅ Workspace set to: {workspace}")
            break
        else:
            print(f"❌ Directory '{workspace}' does not exist.")
            create_choice = input("Create it automatically? (Y/n): ").strip().lower()
            if create_choice in {"", "y", "yes"}:
                os.makedirs(workspace, exist_ok=True)
                print(f"📂 Created: {workspace}")
                break
            retry = input("Retry entering location? (Y/n): ").strip().lower()
            if retry in {"n", "no"}:
                sys.exit("❌ Exiting as per user request.")

    # Save the workspace for future use
    os.makedirs(simaai_dir, exist_ok=True)
    with open(mount_file, "w") as f:
        f.write(workspace)
    return workspace

def configure_container(sdk_container_name, port=None, configure_network=False):
    """
    Configure container user mappings and permissions:
      - Detects current host user (uid, gid, login_name)
      - Updates passwd, shadow, group, sudoers
      - Creates home directory inside container
      - Optionally saves port to container and updates rsyslog (if configure_network=True)
      - If configure_network=True, computes and stores .hash for /usr/local/simaai/plugins
    """
    platform_os = check_os()

    # Detect current host user
    if platform_os in ["linux", "macos"]:
        login_name, uid, gid = detect_current_user()
    else:
        login_name, uid, gid = "docker", 900, 900

    print(f"⚙️  Configuring container '{sdk_container_name}' for user '{login_name}' (UID={uid}, GID={gid})")

    # ---- Linux / MacOS User Setup ----
    if platform_os in ["linux", "macos"]:
        run_command(["docker", "cp", f"{sdk_container_name}:/etc/passwd", "./passwd.txt"])
        with open("./passwd.txt", "a") as f:
            f.write(f"{login_name}:x:{uid}:{gid}::/home/{login_name}:/bin/sh\n")
        run_command(["docker", "cp", "./passwd.txt", f"{sdk_container_name}:/etc/passwd"])
        os.remove("./passwd.txt")

        run_command(["docker", "cp", f"{sdk_container_name}:/etc/shadow", "./shadow.txt"])
        with open("./shadow.txt", "a") as f:
            f.write(f"{login_name}:$6$hash$placeholder:::::::\n")
        run_command(["docker", "cp", "./shadow.txt", f"{sdk_container_name}:/etc/shadow"])
        os.remove("./shadow.txt")

        run_command(["docker", "cp", f"{sdk_container_name}:/etc/group", "./group.txt"])
        with open("./group.txt", "a") as f:
            f.write(f"{login_name}:x:{gid}:\n")
        run_command(["docker", "cp", "./group.txt", f"{sdk_container_name}:/etc/group"])
        os.remove("./group.txt")

        run_command(["docker", "cp", f"{sdk_container_name}:/etc/sudoers", "./sudoers.txt"])
        os.chmod("./sudoers.txt", 0o755)
        with open("./sudoers.txt", "a") as f:
            f.write(f"{login_name} ALL=(ALL:ALL) NOPASSWD:ALL\n")
        run_command(["docker", "cp", "./sudoers.txt", f"{sdk_container_name}:/etc/sudoers"])
        run_command(["docker", "exec", "-u", "root", sdk_container_name, "chmod", "440", "/etc/sudoers"])
        run_command(["docker", "exec", "-u", "root", sdk_container_name, "chown", "root:root", "/etc/sudoers"])
        os.remove("./sudoers.txt")

        run_command(["docker", "exec", "-u", "root", sdk_container_name,
                     "usermod", "-a", "-G", "docker", login_name])

        home_directory = f"/home/{login_name}"
        run_command(["docker", "exec", "-u", "root", sdk_container_name, "mkdir", "-p", home_directory])
        run_command(["docker", "exec", "-u", "root", sdk_container_name, "chown", f"{uid}:{gid}", home_directory])
    else:
        command = f"echo '{login_name} ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers"
        run_command(["docker", "exec", "-u", "root", sdk_container_name, "sh", "-c", command])

    # ---- Optional Network & Syslog Configuration ----
    if configure_network:
        if port is None:
            raise ValueError("Port must be provided when configure_network=True")

        run_command(["docker", "cp", "./config.json", f"{sdk_container_name}:/home/docker/.simaai/config.json"])
        #os.remove("./config.json")

        run_command(["docker", "exec", "-u", "root", sdk_container_name,
                     "sed", "-i.bk", f"s@docker@{login_name}@g", "/etc/rsyslog.conf"])
        print(f"🌐 Network and syslog configuration applied (Port={port}).")

        run_command(["docker", "exec", "-u", "root", sdk_container_name,
                     "chown", "-R", f"{uid}:{gid}", "/usr/local/simaai/"])

        # ---- Compute plugin hash and store it ----
        plugin_dir = "/usr/local/simaai/plugin_zoo/a65-apps"
        print(f"🧮 Computing C++ source hash inside {plugin_dir} ...")

        hash_command = f"""
import hashlib, os
def get_cpp_plugins_source_code_hash(directory):
    hasher = hashlib.md5()
    cpp_extensions = {{'.cpp','.cc','.cxx','.hpp','.h','.c'}}
    excluded_dirs = {{'build'}}
    file_list = []
    for root, dirs, files in os.walk(directory, topdown=True):
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        dirs.sort(); files.sort()
        for f in files:
            if f == 'CMakeLists.txt' or any(f.endswith(ext) for ext in cpp_extensions):
                rel = os.path.relpath(os.path.join(root,f),directory).replace('\\\\','/').lower()
                file_list.append(rel)
    for f in sorted(file_list):
        hasher.update(f.encode('utf-8'))
        try:
            with open(os.path.join(directory,f),'rb') as fd:
                while chunk := fd.read(4096):
                    chunk = chunk.replace(b'\\r\\n',b'\\n')
                    hasher.update(chunk)
        except (FileNotFoundError,PermissionError): pass
    return hasher.hexdigest()

path='{plugin_dir}'
h = get_cpp_plugins_source_code_hash(path)
with open(os.path.join(path,'.hash'),'w') as f: f.write(h)
print(f'✅ Hash written to {{path}}/.hash → {{h}}')
"""
        run_command(["docker", "exec", sdk_container_name, "python3", "-c", hash_command])

    else:
        print("ℹ️  Skipping network and syslog configuration as requested.")

    print(f"✅ Container '{sdk_container_name}' configured successfully.")

def ensure_simasdkbridge_network():
    """
    Ensure that the 'simasdkbridge' Docker network exists.

    This method:
      - Lists all available Docker networks.
      - If the network 'simasdkbridge' exists, it prints a confirmation.
      - If not found, it creates the network silently.

    Raises:
        RuntimeError: If Docker command fails to run.
    """
    print("🔍 Checking SiMa SDK Bridge Network...")

    try:
        # List existing Docker networks
        result = subprocess.run(
            ["docker", "network", "ls", "--format", "{{.Name}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )

        networks = result.stdout.splitlines()

        # Check for simasdkbridge
        if "simasdkbridge" in networks:
            print("✅ SiMa SDK Bridge Network found.")
        else:
            print("⚙️ 'simasdkbridge' network not found. Creating it now...")
            subprocess.run(
                ["docker", "network", "create", "simasdkbridge"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            print("✅ 'simasdkbridge' network created successfully.")

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"❌ Failed to check or create Docker network: {e.stderr.strip() if e.stderr else str(e)}")


def start_docker_container(
    uid,
    gid,
    port,
    workspace,
    image,
    privileged=False,
    port_mapping_required=False,
):
    """
    Start a Docker container using an image pulled from either JFrog or AWS ECR.

    Automatically mounts log folders from the container's /var/log to
    the host workspace/<container_name>/logs/.
    """

    # ─────────────────────────────────────────────
    # Generate container name
    # ─────────────────────────────────────────────
    container_name = sanitize_container_name(image)
    print(f"🚀 Starting container '{container_name}' using image '{image}'")

    # Detect macOS with Apple Silicon
    system_name = platform.system()
    machine_arch = platform.machine().lower()
    is_macos_arm = (system_name == "Darwin" and "arm" in machine_arch)

    # Base Docker command
    docker_cmd = [
        "docker", "run", "-t", "-d",
        f"--user={uid}:{gid}",
        "--name", container_name,
        "--hostname", container_name,
        "--network", "simasdkbridge",
        "-v", f"{workspace}:/home/docker/sima-cli/",
    ]

    # ─────────────────────────────────────────────
    # Add --platform=linux/amd64 for macOS ARM
    # ─────────────────────────────────────────────
    if is_macos_arm and "modelsdk" in image.lower():
        print("💻 Detected macOS with Apple Silicon → forcing amd64 emulation for ModelSDK.")
        docker_cmd.extend(["--platform", "linux/amd64"])

    # ─────────────────────────────────────────────
    # Add privileged and port mappings
    # ─────────────────────────────────────────────
    if privileged:
        docker_cmd.extend(["--privileged", "--cap-add=NET_RAW", "--cap-add=NET_ADMIN"])

    if port_mapping_required:
        docker_cmd.extend(["-p", f"{port}:8084"])

    # ─────────────────────────────────────────────
    # Mount /var/log subfolders based on IMAGE_CONFIG
    # ─────────────────────────────────────────────
    short_name = None
    for key in IMAGE_CONFIG.keys():
        if key in image.lower():
            short_name = key
            break

    if short_name:
        var_log_folders = IMAGE_CONFIG[short_name].get("var-log-folders", [])
        if var_log_folders:
            for folder in var_log_folders:
                log_host_dir = os.path.join(workspace, '.' + container_name, "logs", folder.strip("/"))
                os.makedirs(log_host_dir, exist_ok=True)
                if folder == "/" or folder == "":
                    mount_target = "/var/log"
                else:
                    mount_target = f"/var/log/{folder.strip('/')}"
                docker_cmd.extend(["-v", f"{log_host_dir}:{mount_target}"])
            print(f"🪵 Mapped log folders: {', '.join(var_log_folders)} → host logs/")
        else:
            print("ℹ️  No /var/log mappings configured for this SDK.")
    else:
        print("⚠️ Could not determine SDK short name for log mapping.")

    # ─────────────────────────────────────────────
    # Launch container
    # ─────────────────────────────────────────────
    docker_cmd.append(image)
    run_command(docker_cmd)

    # ─────────────────────────────────────────────
    # Post-launch configuration
    # ─────────────────────────────────────────────
    if port_mapping_required:
        print(f"✅ Container '{container_name}' started successfully on port {port}.")
    else:
        print(f"✅ Container '{container_name}' started successfully (no external port mapping).")

    configure_container(container_name, port, port_mapping_required)

    return container_name


def print_section(title):
    print("\n" + "=" * 20 + f"[ {title} ]" + "=" * 20 + "\n")

def create_config_json(file_path="config.json", port=8084, selected_images=None):
    """
    Create a JSON configuration file containing port, selected SDK images,
    and their associated sanitized container names.

    The image keys come from IMAGE_CONFIG, not raw image URLs.

    Example output:
    {
        "port": 8084,
        "images": {
            "elxr": { "container_name": "ecr-sima-elxr-1.8" },
            "yocto": { "container_name": "jfrog-yocto-latest" },
            "modelsdk": { "container_name": "modelsdk-latest" }
        }
    }
    """

    if not selected_images:
        print("⚠️ No selected images provided; nothing to write.")
        return None

    try:
        images_data = {}

        # Iterate through known image keys
        for key, meta in IMAGE_CONFIG.items():
            # Try to find the matching image (partial name match)
            match = next((img for img in selected_images if key in img), None)
            if match:
                container_name = sanitize_container_name(match)
                images_data[key] = {"container_name": container_name}
            else:
                # Skip if that SDK component was not selected
                continue

        if not images_data:
            print("⚠️ No matching images found for IMAGE_CONFIG keys.")
            return None

        config_data = {
            "port": port,
            "images": images_data,
        }

        # Write JSON
        with open(file_path, "w") as f:
            json.dump(config_data, f, indent=4)

        abs_path = os.path.abspath(file_path)
        print(f"✅ Configuration file created successfully at: {abs_path}")
        return abs_path

    except Exception as e:
        print(f"❌ Failed to create configuration file: {e}")
        return None

def is_docker_running():
    """Check if the Docker daemon is running."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False

def yes_no_prompt(prompt: str, default_yes=True) -> bool:
    """
    Prompt user for a yes/no response.
    Defaults to YES if Enter is pressed.
    """
    default_choice = "Y/n" if default_yes else "y/N"
    while True:
        choice = input(f"{prompt} ({default_choice}): ").strip().lower()
        if choice == "" and default_yes:
            return True
        if choice in {"y", "yes"}:
            return True
        if choice in {"n", "no"}:
            return False
        print("❌ Invalid choice. Please enter Y or N.")


SDK_CONTAINER_PATTERNS = re.compile(r"(elxr|yocto|modelsdk|mpk_cli_toolset)", re.IGNORECASE)

def get_all_containers(running_containers_only: bool = False):
    """
    Return a filtered list of Docker containers whose names contain:
        - elxr
        - yocto
        - model
        - mpk

    Args:
        running_containers_only (bool): If True, return only running containers.

    Returns:
        list[dict]: Each entry is a parsed JSON object from docker ps output.
    """
    try:
        cmd = ["docker", "ps", "--format", "{{json .}}"]
        if not running_containers_only:
            cmd.insert(2, "-a")

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        containers = []
        for line in result.stdout.strip().splitlines():
            if not line:
                continue

            try:
                info = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Only keep SDK containers with name containing patterns
            name = info.get("Names", "")

            if SDK_CONTAINER_PATTERNS.search(name):
                containers.append(info)

        return containers

    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Failed to list containers: {e}[/red]")
        sys.exit(1)

def get_container_info(container_id):
    """Return container name, image, and status by container ID."""
    name = subprocess.check_output(
        ["docker", "inspect", "--format", "{{.Name}}", container_id],
        text=True
    ).strip().lstrip('/')

    image = subprocess.check_output(
        ["docker", "inspect", "--format", "{{.Config.Image}}", container_id],
        text=True
    ).strip()

    status = subprocess.check_output(
        ["docker", "inspect", "--format", "{{.State.Status}}", container_id],
        text=True
    ).strip()  # running, exited, etc.

    return name, image, status

def is_target_container(container_name, container_image):
    """Check if container name or image matches our list of IMAGE_NAMES."""
    return any(
        container_name.startswith(name)
        or container_image.endswith(name)
        or f"/{name}:" in container_image
        for name in IMAGE_NAMES
    )

def extract_tag_from_image(image_name):
    """Extract the tag/version from a Docker image string."""
    return image_name.split(":")[-1] if ":" in image_name else "unknown"

def stop_and_remove_container(container_id, container_name, container_status):
    """Stop and optionally remove a single container."""
    if container_status == "running":
        if yes_no_prompt(f"Do you want to stop '{container_name}'?"):
            subprocess.run(["docker", "stop", container_id], check=True)
            print(f"✅ Container '{container_name}' stopped.")
    else:
        print(f"ℹ️ Container '{container_name}' is already stopped.")

    if yes_no_prompt(f"Do you want to remove container '{container_name}'?"):
        subprocess.run(["docker", "rm", container_id], check=True)
        print(f"🗑️  Container '{container_name}' removed.")

def stop_and_remove_group(group_items, selected_tag):
    """Stop and remove all containers in a group with a single prompt."""
    container_names = [cname for _, cname, _, _ in group_items]
    print(f"\n⚠️ You have chosen to manage ALL containers in group '{selected_tag}'.")
    print(f"Containers: {', '.join(container_names)}")

    if yes_no_prompt("Do you want to stop ALL containers in this group?"):
        for cid, cname, cstatus, _ in group_items:
            if cstatus == "running":
                subprocess.run(["docker", "stop", cid], check=True)
                print(f"✅ Stopped: {cname}")
            else:
                print(f"ℹ️ Already stopped: {cname}")

    if yes_no_prompt("Do you want to remove ALL containers in this group?"):
        for cid, cname, _, _ in group_items:
            subprocess.run(["docker", "rm", cid], check=True)
            print(f"🗑️ Removed: {cname}")

def get_valid_input(prompt, valid_range, allow_a=False):
    """
    Prompt user for input and handle invalid choices.
    - valid_range: range of valid numbers
    - allow_a: allow 'a' as a valid option
    """
    while True:
        choice = input(prompt).strip().lower()
        if allow_a and choice == 'a':
            return 'a'
        if choice.isdigit():
            choice_num = int(choice)
            if choice_num in valid_range:
                return choice_num

        # Invalid input handling
        if yes_no_prompt("❌ Invalid input. Would you like to retry?"):
            continue
        else:
            print("Exiting as per user request.")
            sys.exit(0)

def group_images_by_tag(images):
    """Group images by their version tag."""
    grouped = defaultdict(list)
    for image in images:
        tag = extract_tag_from_image(image)
        grouped[tag].append(image)
    return grouped

def remove_image(image_name):
    """Remove a single Docker image."""
    try:
        run_command(["docker", "rmi", image_name])
        print(f"🗑️  Image '{image_name}' removed.")
    except subprocess.CalledProcessError:
        print(f"❌ Failed to remove image '{image_name}'.")

def remove_images_in_group(group_images, tag):
    """
    Provide user with options to remove all images or selected ones.
    Includes validation and retry logic.
    """
    while True:
        print(f"\n⚙️ Managing image group: Version {tag}")
        print("Images in this group:")
        for idx, img in enumerate(group_images, start=1):
            print(f"    {idx}. {extract_image_name(img)}")
        print("    a. Remove ALL images in this group")

        selection = input("\nEnter image numbers (comma-separated) or 'a' to remove ALL: ").strip().lower()

        if selection == 'a':
            for img in group_images:
                remove_image(img)
            return

        # Validate numeric input
        parts = [p.strip() for p in selection.split(",") if p.strip()]
        if not parts or not all(p.isdigit() for p in parts):
            if yes_no_prompt("❌ Invalid input. Do you want to retry?", default_yes=True):
                continue
            print("Exiting as per user request.")
            sys.exit(0)

        # Convert to set of indices
        selected_indices = {int(i) for i in parts}
        invalid_indices = [i for i in selected_indices if i < 1 or i > len(group_images)]
        if invalid_indices:
            print(f"❌ Invalid selection: {invalid_indices}")
            if yes_no_prompt("Do you want to retry?", default_yes=True):
                continue
            print("Exiting as per user request.")
            sys.exit(0)

        for idx, img in enumerate(group_images, start=1):
            if idx in selected_indices:
                remove_image(img)
        return

def get_all_images():
    """
    Return list of all docker images filtered by IMAGE_NAMES with full repository:tag format.
    """
    output = subprocess.check_output(
        ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
        text=True
    ).strip()

    if not output:
        return []

    images = []
    for line in output.splitlines():

        repo_part = line.rsplit(":", 1)[0]  # split once from the right
        base_name = repo_part.split("/")[-1]  # take the last part

        if base_name in IMAGE_NAMES:
            images.append(line.strip())

    return images

def extract_image_name(full_repo_path):
    """
    Extract just the image name (e.g., 'elxr') from a full repository string.
    Example:
        'artifacts.eng.sima.ai:443/sima-docker/elxr:latest_VP-10555'
        -> 'elxr'
    """
    # Split by '/' then take the last part (e.g., 'elxr:latest_VP-10555')
    last_part = full_repo_path.split("/")[-1]
    # Remove the tag
    return last_part.split(":")[0]

#--------------------------------------------
# Added when integrating into sima-cli
#--------------------------------------------

from rich.console import Console
from rich.panel import Panel
from InquirerPy import inquirer

console = Console()

def get_local_sima_images():
    """Return a list of local SDK images containing 'sima-docker' or 'vdp-cli'."""
    try:
        output = subprocess.check_output(
            ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
            text=True
        ).strip()
    except subprocess.CalledProcessError:
        return []

    keywords = ("sima-docker", "vdp-cli")

    images = [
        line for line in output.splitlines()
        if any(key in line for key in keywords)
    ]

    return sorted(set(images))

def _print_help_box():
    """Display a styled help box using Rich Panel."""
    message = (
        "[bold cyan]How to use this menu:[/bold cyan]\n\n"
        "• Use [green]↑[/green]/[green]↓[/green] arrows then [green]Space[/green] to select one or more images.\n"
        "• Press [bold]Enter[/bold] to confirm your selection.\n"
        "• These are local Docker images found containing 'sima-docker'.\n"
        "• Containers based on these images will be started automatically.\n"
        "• Press [yellow]CTRL+C[/yellow] to cancel anytime."
    )

    console.print(
        Panel(
            message,
            title="📘 SiMa.ai SDK Image Selection",
            border_style="green",
            expand=False,
        )
    )

def prompt_image_selection(images, noninteractive=False):
    """Prompt the user to select one or more SDK images to start, supporting multi-version."""
    if not images:
        console.print("[red]❌ No SiMa.ai SDK images found locally.[/red]")
        sys.exit(1)

    if not noninteractive:
        _print_help_box()

    # ─────────────────────────────────────────────
    # 1. Detect SDK versions by image tag
    # ─────────────────────────────────────────────
    version_map = defaultdict(list)
    for img in images:
        parts = img.split(":")
        version = parts[-1] if len(parts) > 1 else "unknown"
        version_map[version].append(img)

    versions = sorted(version_map.keys())

    # ─────────────────────────────────────────────
    # 2. Version selection
    # ─────────────────────────────────────────────
    if len(versions) > 1:
        if noninteractive:
            # Non-interactive mode: select all versions
            console.print(
                "[dim]Non-interactive mode: multiple SDK versions detected — selecting all.[/dim]"
            )
            images = [img for imgs in version_map.values() for img in imgs]
        else:
            version_choices = [{"name": v, "value": v} for v in versions]
            selected_version = (
                inquirer.select(
                    message="Multiple SDK versions detected — select one to start:",
                    choices=version_choices,
                    qmark="🔢",
                ).execute()
            )
            images = version_map[selected_version]
            console.print(
                f"[cyan]ℹ️  Showing images for version [bold]{selected_version}[/bold][/cyan]"
            )
    else:
        console.print(f"[dim]Single SDK version detected: {versions[0]}[/dim]")

    # ─────────────────────────────────────────────
    # 3. Image selection
    # ─────────────────────────────────────────────
    if noninteractive:
        console.print("[dim]Non-interactive mode: selecting all SDK images.[/dim]")
        return images

    choices = (
        [{"name": "✅ Select All", "value": "__all__", "enabled": True}]
        + [{"name": sanitize_container_name(img), "value": img} for img in images]
        + [{"name": "🚫 Cancel", "value": "__cancel__"}]
    )

    selected = (
        inquirer.checkbox(
            message="Select SDK images to start:",
            choices=choices,
            instruction="(Space to toggle, Enter to confirm)",
            qmark="📦",
            transformer=lambda res: (
                f"[bold green]{len(res)} selected[/bold green]"
                if res else "[dim]None selected[/dim]"
            ),
        ).execute()
    )

    # ─────────────────────────────────────────────
    # 4. Handle user actions
    # ─────────────────────────────────────────────
    if "__cancel__" in selected or not selected:
        console.print("[yellow]Exiting — no images selected.[/yellow]")
        sys.exit(-1)

    if "__all__" in selected:
        return images

    return [s for s in selected if s not in {"__all__", "__cancel__"}]

def confirm_to_remove_exiting_container(image, yes_to_all=False):
    """Start a container for the given SDK image."""
    container_name = image.split("/")[-1].replace(":", "_")

    # 🔍 Check if container already exists
    existing = subprocess.run(
        ["docker", "ps", "-a", "--format", "{{.Names}}"],
        text=True, capture_output=True
    ).stdout.splitlines()

    if container_name in existing:
        console.print(f"[yellow]⚠️  Container '{container_name}' already exists.[/yellow]")
        if yes_to_all:
            console.print(f"[cyan]Auto-removing '{container_name}' (yes_to_all=True).[/cyan]")
            subprocess.run(["docker", "rm", "-f", container_name], check=False)
            console.print(f"✅ Removed old container '{container_name}'.", style="green")
        else:
            resp = input("🗑️  Remove and recreate it? [Y/n]: ").strip().lower()
            if resp in {"", "y", "yes"}:
                subprocess.run(["docker", "rm", "-f", container_name], check=False)
                console.print(f"✅ Removed old container '{container_name}'.", style="green")
            else:
                console.print(f"⏩ Skipping existing '{container_name}'.", style="yellow")
                return container_name


def sanitize_container_name(image: str) -> str:
    """
    Convert an image name (e.g. 'sima-docker/abc:def.gpu') into a valid Docker container name.
    """
    name = image

    # Normalize known registry prefixes
    name = re.sub(r"\b(sima-docker)\b", "", name)
    name = re.sub(r"\bartifacts\.eng\.sima\.ai\b", "jfrog", name)
    # remove any AWS ECR registry domain like "123456789012.dkr.ecr.us-west-1.amazonaws.com"
    name = re.sub(r"\b\d+\.dkr\.ecr\.[a-z0-9-]+\.amazonaws\.com\b", "", name)

    # Replace separators and invalid characters
    name = name.replace("/", "-").replace(":", "-").lower()
    name = re.sub(r"[^a-z0-9_.-]", "_", name)

    # Clean up leading/trailing non-alphanumeric chars
    name = name.strip("._-")
    name = name.replace("--", '-')

    # Ensure it starts with an alphanumeric
    if not name or not name[0].isalnum():
        name = f"c_{name}"

    # Docker name limit: 128 chars
    return name[:128]

def extract_short_name(image: str) -> str:
    """
    Extracts the short SDK name from a full image string.
    Examples:
        sima-docker/modelsdk:1.8         → modelsdk
        artifacts.eng.sima.ai/elxr:1.9   → elxr
        512422982161.dkr.ecr.../yocto:v2 → yocto
    """
    # Extract the part before the tag (:)
    base = image.split(":")[0]
    # Take the last path segment
    short = os.path.basename(base)
    return short.lower().strip()

def detect_current_user():
    """
    Return (login_name, uid, gid) in a cross-platform way.

    On Windows, UID/GID are set to 0 since os.getuid/getgid are unavailable.
    """
    # ────────────────────────────────────────
    # 1. Determine username
    # ────────────────────────────────────────
    try:
        login_name = getpass.getuser()
    except Exception:
        # Fallbacks for rare environments
        login_name = (
            os.getenv("USERNAME")
            or os.getenv("USER")
            or os.getenv("LOGNAME")
            or "unknown"
        )

    # ────────────────────────────────────────
    # 2. Determine UID / GID
    # ────────────────────────────────────────
    if platform.system() == "Windows":
        uid, gid = 0, 0  # Not applicable on Windows
    else:
        try:
            uid = os.getuid()
            gid = os.getgid()
        except Exception:
            uid, gid = 0, 0

    return login_name, uid, gid

def select_containers(containers, single_select=False):
    """
    Prompt user to select one or more containers by name.
    Supports both single and multiple selection modes.

    Args:
        containers (list[dict|str]): List of Docker containers.
        single_select (bool): If True, use single-select (like radio buttons).
                              If False, allow multiple selection.
    Returns:
        list[str] | str: List of selected container names (or a single name if single_select=True).
    """
    if not containers:
        print("⚠️  No running containers found.")
        return [] if not single_select else None

    # Extract names from dicts or strings
    names = []
    for c in containers:
        if isinstance(c, dict):
            name = c.get("Names") or c.get("Name") or c.get("name")
            if name:
                names.append(name)
        elif isinstance(c, str):
            names.append(c)

    if not names:
        print("⚠️  No valid container names found.")
        return [] if not single_select else None

    # Build menu choices
    choices = [{"name": n, "value": n} for n in names]

    # Single select mode
    if single_select:
        selected = inquirer.select(
            message="Select a container:",
            choices=choices,
            qmark="🐳",
            instruction="Use ↑/↓ to navigate, Enter to confirm",
        ).execute()
        return selected  # returns a single name string

    # Multi-select mode
    selected = inquirer.checkbox(
        message="Select containers:",
        choices=choices,
        qmark="🐳",
        instruction="(Space to select, Enter to confirm)",
    ).execute()

    return selected  # returns a list of names