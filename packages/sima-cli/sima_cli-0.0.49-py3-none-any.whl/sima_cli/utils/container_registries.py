import click
import subprocess

from sima_cli.utils.config import get_auth_token
from sima_cli.auth.devportal import resolve_public_registry, ensure_docker_available, docker_login_with_token
from sima_cli.utils.docker import check_and_start_docker

def _pull_container_from_registry(registry_url: str, image_ref: str) -> str:
    """
    Pulls container image from given registry and returns its local reference.
    """
    if ensure_docker_available():
        full_image = f"{registry_url.rstrip('/')}/{image_ref}"
        subprocess.run(["docker", "pull", full_image], check=True)
        return full_image

def docker_logout_from_registry(registry: str = "artifacts.eng.sima.ai"):
    """
    Logout from the specified Docker registry.
    Removes stored credentials (even if managed by a credential helper).
    Safe to call multiple times — no error if already logged out.
    """
    if ensure_docker_available():
        click.echo(f"🐳 Logging out of Docker registry")

        try:
            proc = subprocess.run(
                ["docker", "logout", registry],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            if proc.returncode == 0:
                click.echo(proc.stdout.decode().strip() or f"✅ Logged out from {registry}")
            else:
                msg = proc.stderr.decode().strip() or proc.stdout.decode().strip()
                if "not logged in" in msg.lower():
                    click.echo(f"ℹ️  Already logged out from {registry}")
                else:
                    raise click.ClickException(f"Docker logout failed: {msg}")

        except Exception as e:
            raise click.ClickException(f"⚠️  Unexpected error during Docker logout: {e}")


def _select_artifactory_version(image_name: str) -> str:
    """
    Query available tags for an image from SiMa Artifactory and prompt user to select one.

    Args:
        image_name (str): The image name under sima-docker (e.g., 'modelsdk').

    Returns:
        str: The user-selected tag (e.g., 'latest_develop').

    Raises:
        click.ClickException: If no tags are found or query fails.
    """
    import requests
    from InquirerPy import inquirer

    click.echo(f"🔍 Querying available versions for {image_name} from Artifactory...")

    # Retrieve internal auth token, if available
    token = get_auth_token(internal=True)
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    if not token:
        click.secho("⚠️  Not authorized to access Artifactory; please run `sima-cli -i login` with your Identity Token.", fg='yellow')
        exit(-1)

    tags_url = (
        f"https://artifacts.eng.sima.ai/artifactory/api/docker/"
        f"sima-docker/v2/{image_name}/tags/list"
    )

    try:
        resp = requests.get(tags_url, headers=headers, timeout=10)
        if resp.status_code != 200:
            raise click.ClickException(
                f"❌ Failed to query tags for '{image_name}': {resp.status_code} {resp.text}"
            )

        tags = sorted(resp.json().get("tags", []))
        if not tags:
            raise click.ClickException(f"❌ No tags found for image '{image_name}'")

        # Interactive tag selection
        return inquirer.select(
            message=f"Select a version for {image_name}:",
            choices=tags,
            default="latest" if "latest" in tags else tags[0],
        ).execute()

    except requests.exceptions.RequestException as e:
        raise click.ClickException(f"❌ Network error while querying Artifactory: {e}")


def install_from_cr(resource_spec: str, internal: bool = False) -> str:
    """
    Install a component from a container registry resource.

    Args:
        resource_spec (str): Resource string in the form:
            cr:<image>[:tag] or cr:<image>@<digest>
        internal (bool): Whether to use SiMa internal Artifactory registry.

    Examples:
        install_from_cr("cr:modelsdk:latest_develop", internal=True)
        install_from_cr("cr:modelsdk@sha256:abcd1234", internal=False)
    """
    if not ensure_docker_available():
        click.echo("⚠️  Docker not available; skipping container installation.")
        return ""

    if not check_and_start_docker():
        click.echo("⚠️  Unable to start Docker on this platform.")
        return ""

    resource_spec = resource_spec[3:].strip()

    # Parse image and version/digest
    if "@" in resource_spec:
        image_name, version = resource_spec.split("@", 1)
        separator = "@"
    elif ":" in resource_spec:
        image_name, version = resource_spec.split(":", 1)
        separator = ":"
    else:
        image_name, version, separator = resource_spec, None, ":"

    # Resolve registry, default to Artifactory, if external resolve again.
    registry_url = "artifacts.eng.sima.ai/sima-docker"
          
    if not internal:
        try:
            token, registry_url = resolve_public_registry("ecr")
            if not token or not registry_url:
                click.secho("⚠️  Failed to resolve container registry or token is missing.", fg="yellow")
                return None

            success = docker_login_with_token("sima_cli", token, registry_url)
            if success:
                crtype = 'internal' if internal else 'SiMa.ai'
                click.secho(f"✅ Logged in to {crtype} container registry", fg="green")
            else:
                click.secho(f"❌ Docker login to container registry failed", fg="red")

        except Exception as e:
            click.secho(f"❌ Unexpected error during container login: {e}", fg="red")
            return None
        
    # If internal and version not specified, prompt for version
    if internal and version is None:
        version = _select_artifactory_version(image_name)

    # Compose final ref
    full_image_ref = f"{registry_url}/{image_name}{separator}{version or 'latest'}"

    # Auto-login if internal and not logged in
    if internal and not get_auth_token(internal=internal):
        click.echo(
            f"⚠️  No internal token found; please login as "
            + click.style("sima-cli -i login", fg="cyan", bold=True)
        )
        return

    # Pull image
    try:
        registry_url = registry_url.replace('https://', '')
        pulled_ref = _pull_container_from_registry(
            registry_url, f"{image_name}{separator}{version or 'latest'}"
        )

        if pulled_ref:
            click.echo(f"✅ Successfully pulled container: {pulled_ref}")
    
    except subprocess.CalledProcessError as e:
        raise click.ClickException(f"❌ Docker pull failed: {e}")

    return full_image_ref
