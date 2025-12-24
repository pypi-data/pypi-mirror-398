# model_zoo/models.py

import os
import json
import yaml
import zipfile
import tempfile
import requests
import click
from urllib.parse import urlparse
from rich import print
from rich.text import Text
from rich.table import Table
from rich.panel import Panel
from rich.console import Console
from InquirerPy import inquirer
from sima_cli.utils.config import get_auth_token
from sima_cli.utils.config_loader import artifactory_url
from sima_cli.download import download_file_from_url

ARTIFACTORY_BASE_URL = artifactory_url() + "/artifactory"


# ─────────────────────────────────────────────
# Shared helper utilities
# ─────────────────────────────────────────────

def _is_valid_url(url: str) -> bool:
    """Return True if a string is a valid URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def _fetch_yaml_data(yaml_url: str, internal: bool = False):
    """Download and parse a YAML file from a given URL."""
    try:
        local_path = download_file_from_url(yaml_url, dest_folder=".", internal=internal)
        with open(local_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        click.echo(f"❌ Failed to fetch or parse YAML: {e}")
        return None


def _prompt_user_action(app_name):
    """Display the action menu after describing an app."""
    return inquirer.select(
        message=f"What would you like to do with {app_name}?",
        choices=["Download", "Back", "Exit"],
        default="Back"
    ).execute()


# ─────────────────────────────────────────────
# Common YAML description logic
# ─────────────────────────────────────────────

def _describe_yaml_content(data: dict, app_name: str):
    """Pretty-print a YAML pipeline description."""
    console = Console()

    # ---- PIPELINE ----
    if "pipeline" in data:
        pipeline = data.get("pipeline", {})
        header = f"[bold green]{pipeline.get('name', app_name)}[/bold green] - {pipeline.get('category', 'Unknown')}"
        desc = pipeline.get("short_description", "")

        console.print(Panel(Text(desc, style="yellow", no_wrap=False), title=header, expand=False, width=min(console.width, 100)))

        p_table = Table(title="Pipeline", header_style="bold magenta")
        p_table.add_column("Field")
        p_table.add_column("Value")
        p_table.add_row("Input Format", pipeline.get("in_format", "-"))
        p_table.add_row("Output Format", pipeline.get("out_format", "-"))

        perf = pipeline.get("performance", {})
        p_table.add_row("Davinci FPS", str(perf.get("davinci_fps", "-")))
        p_table.add_row("Modalix FPS", str(perf.get("modalix_fps", "-")))
        console.print(p_table)

    # ---- MODELS ----
    if "model" in data:
        models = data["model"]
        if isinstance(models, dict):
            models = [models]
        elif not isinstance(models, list):
            models = []

        for idx, model in enumerate(models, start=1):
            title = f"Model #{idx}" if len(models) > 1 else "Model"
            m_table = Table(title=title, header_style="bold cyan")
            m_table.add_column("Field")
            m_table.add_column("Value")

            m_table.add_row("Name", model.get("name", "-"))

            if inp := model.get("input_description"):
                m_table.add_row("Resolution", str(inp.get("resolution", "-")))
                m_table.add_row("Format", inp.get("format", "-"))

            if resize := model.get("resize_configuration"):
                m_table.add_row("Resize Format", resize.get("input_image_format", "-"))
                m_table.add_row("Input Shape", str(resize.get("input_shape", "-")))
                m_table.add_row("Scaling Type", resize.get("scaling_type", "-"))
                m_table.add_row("Padding Type", resize.get("padding_type", "-"))
                m_table.add_row("Aspect Ratio", str(resize.get("aspect_ratio", "-")))

            if norm := model.get("normalization_configuration"):
                m_table.add_row("Channel Mean", str(norm.get("channel_mean", "-")))
                m_table.add_row("Channel Stddev", str(norm.get("channel_stddev", "-")))

            if "dataset" in model:
                ds = model["dataset"]
                m_table.add_row("Dataset", ds.get("name", "-"))
                for k, v in (ds.get("params") or {}).items():
                    m_table.add_row(k, str(v))
                m_table.add_row("Accuracy", ds.get("accuracy", "-"))
                m_table.add_row("Calibration", ds.get("calibration", "-"))

            if "quantization_settings" in model:
                q = model["quantization_settings"]
                m_table.add_row("Calibration Samples", str(q.get("calibration_num_samples", "-")))
                m_table.add_row("Calibration Method", q.get("calibration_method", "-"))
                m_table.add_row("Requantization Mode", q.get("requantization_mode", "-"))
                m_table.add_row("Bias Correction", str(q.get("bias_correction", "-")))

            console.print(m_table)

    # ---- TRANSFORMS ----
    if "pipeline" in data and "transforms" in data["pipeline"]:
        transforms = data["pipeline"]["transforms"]
        if isinstance(transforms, list):
            t_table = Table(title="Pipeline Transforms", header_style="bold green")
            t_table.add_column("Name")
            t_table.add_column("Params")

            for step in transforms:
                name = step.get("name")
                params = step.get("params", {})
                param_str = ", ".join(f"{k}={v}" for k, v in params.items()) if params else "-"
                t_table.add_row(name, param_str)

            console.print(t_table)

    if not any(k in data for k in ("pipeline", "model")):
        click.echo("⚠️ YAML parsed, but no recognizable `pipeline` or `model` sections found.")


# ─────────────────────────────────────────────
# Internal App Zoo (AQL logic preserved)
# ─────────────────────────────────────────────

def _list_available_app_versions_internal(match_keyword: str = None):
    """List all available App Zoo versions from Artifactory."""
    repo = "vdp"
    base_path = "vdp-app-config-default"
    aql_query = f"""
        items.find({{
            "repo": "{repo}",
            "path": {{"$match": "{base_path}/*"}},
            "type": "folder"
        }}).include("repo","path","name")
    """.strip()

    aql_url = f"{ARTIFACTORY_BASE_URL}/api/search/aql"
    headers = {
        "Content-Type": "text/plain",
        "Authorization": f"Bearer {get_auth_token(internal=True)}"
    }

    response = requests.post(aql_url, data=aql_query, headers=headers)
    if response.status_code == 401:
        print('❌ Unauthorized. Run `sima-cli -i login` first.')
        return []
    if response.status_code != 200:
        print(f"❌ Failed to list app versions ({response.status_code})")
        return []

    results = response.json().get("results", [])
    versions = sorted({
        item["path"].replace(base_path + "/", "").split("/")[0]
        for item in results
        if item["path"].startswith(base_path + "/")
    })

    if match_keyword:
        mk = match_keyword.lower()
        versions = [v for v in versions if mk in v.lower()]

    return versions


def _list_internal_apps(ver):
    """List apps from internal Artifactory source (with version selection)."""
    click.echo("App Zoo Source : SiMa Artifactory...")

    versions = _list_available_app_versions_internal(ver)
    if not versions:
        click.echo(f"❌ No version match found in Artifactory for [{ver}]")
        return []

    if len(versions) == 1:
        # Single match → list apps directly
        return _list_available_apps_internal(versions[0])

    # Multiple matches → prompt user to choose
    click.echo("Multiple App Zoo versions found matching your input:")
    selected_version = inquirer.fuzzy(
        message="Select a version:",
        choices=versions,
        max_height="70%",
        instruction="(Use ↑↓ to navigate, / to search, Enter to select)"
    ).execute()

    if not selected_version:
        click.echo("No selection made. Exiting.", err=True)
        raise SystemExit(1)

    return _list_available_apps_internal(selected_version)


def _list_available_apps_internal(version: str):
    """Original interactive internal app listing and description."""
    repo = "vdp"
    base_prefix = f"vdp-app-config-default/{version}"
    aql_query = f"""
        items.find({{
            "repo": "{repo}",
            "path": {{"$match": "{base_prefix}/*"}}
        }}).include("repo","path","name")
    """.strip()

    aql_url = f"{ARTIFACTORY_BASE_URL}/api/search/aql"
    headers = {
        "Content-Type": "text/plain",
        "Authorization": f"Bearer {get_auth_token(internal=True)}"
    }

    response = requests.post(aql_url, data=aql_query, headers=headers)
    if response.status_code != 200:
        click.echo(f"❌ Failed to retrieve app list (status {response.status_code})")
        return None

    results = response.json().get("results", [])
    app_names = sorted({
        item["path"].replace(base_prefix + "/", "").split("/")[0]
        for item in results
        if item["path"].startswith(base_prefix + "/")
    })

    if not app_names:
        click.echo("⚠️ No apps found.")
        return None

    while True:
        selected_app = inquirer.fuzzy(
            message=f"Select an app from version {version}:",
            choices=app_names + ["Exit"],
            max_height="70%",
        ).execute()

        if not selected_app or selected_app == "Exit":
            click.echo("👋 Exiting.")
            break

        _describe_app_internal(version, selected_app)

        action = _prompt_user_action(selected_app)
        if action == "Download":
            _download_app_internal(version, selected_app)
        elif action == "Exit":
            break


def _describe_app_internal(ver: str, app_name: str):
    """Fetch and display app YAML from Artifactory."""
    repo = "vdp"
    base_path = f"vdp-app-config-default/{ver}/{app_name}"
    aql_query = f"""
        items.find({{
            "repo": "{repo}",
            "path": "{base_path}",
            "$or": [
                {{ "name": {{ "$match": "*.yaml" }} }},
                {{ "name": {{ "$match": "*.yml" }} }}
            ],
            "type": "file"
        }}).include("repo","path","name")
    """.strip()

    headers = {
        "Content-Type": "text/plain",
        "Authorization": f"Bearer {get_auth_token(internal=True)}"
    }

    aql_url = f"{ARTIFACTORY_BASE_URL}/api/search/aql"
    response = requests.post(aql_url, data=aql_query, headers=headers)
    if response.status_code != 200:
        click.echo(f"❌ Failed to list YAML files ({response.status_code})")
        return

    results = response.json().get("results", [])
    yaml_file = next((f for f in results if f["name"].endswith((".yaml", ".yml"))), None)
    if not yaml_file:
        click.echo(f"⚠️ No .yaml file found under: {base_path}")
        return

    yaml_url = f"{ARTIFACTORY_BASE_URL}/{repo}/{yaml_file['path']}/{yaml_file['name']}"
    response = requests.get(yaml_url, headers={"Authorization": f"Bearer {get_auth_token(internal=True)}"})
    if response.status_code != 200:
        click.echo(f"❌ Failed to fetch YAML: {response.status_code}")
        return

    try:
        data = yaml.safe_load(response.text)
        _describe_yaml_content(data, app_name)
    except yaml.YAMLError as e:
        click.echo(f"❌ Failed to parse YAML: {e}")


def _download_app_internal(ver: str, app_name: str):
    """Download internal .zip app package."""
    repo = "vdp"
    base_path = f"vdp-app-config-default/{ver}/{app_name}"
    aql_query = f"""
        items.find({{
            "repo": "{repo}",
            "path": "{base_path}",
            "name": {{"$match": "*.zip"}},
            "type": "file"
        }}).include("repo","path","name")
    """.strip()

    aql_url = f"{ARTIFACTORY_BASE_URL}/api/search/aql"
    headers = {
        "Content-Type": "text/plain",
        "Authorization": f"Bearer {get_auth_token(internal=True)}"
    }

    response = requests.post(aql_url, data=aql_query, headers=headers)
    if response.status_code != 200:
        click.echo(f"❌ Failed to list app files ({response.status_code})")
        return None

    results = response.json().get("results", [])
    if not results:
        click.echo(f"⚠️ No .zip found for app: {app_name}")
        return None

    file_info = results[0]
    zip_url = f"{ARTIFACTORY_BASE_URL}/{repo}/{file_info['path']}/{file_info['name']}"
    dest_dir = os.path.join(os.getcwd(), app_name)
    os.makedirs(dest_dir, exist_ok=True)

    local_zip = download_file_from_url(zip_url, dest_folder=dest_dir, internal=True)
    with zipfile.ZipFile(local_zip, "r") as zf:
        zf.extractall(dest_dir)
    os.remove(local_zip)
    click.echo(f"✅ App '{app_name}' ready at {dest_dir}")
    return dest_dir


# ─────────────────────────────────────────────
# External App Zoo (JSON-index flow)
# ─────────────────────────────────────────────

def _fetch_app_index(index_url):
    """Download and parse external app index (cross-platform, temp-safe)."""
    try:
        # Create a platform-specific temporary folder (auto-cleaned by OS)
        with tempfile.TemporaryDirectory(prefix="sima_appzoo_") as tmpdir:
            local_json = download_file_from_url(index_url, dest_folder=tmpdir, internal=False)
            json_path = os.path.join(tmpdir, os.path.basename(local_json))

            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)

    except Exception as e:
        click.echo(f"❌ Failed to retrieve or parse app list: {e}")
        return None

def _fetch_current_version(metadata_url):
    """Download and parse metadata_url (cross-platform, temp-safe)."""
    try:
        # Create a platform-specific temporary folder (auto-cleaned by OS)
        with tempfile.TemporaryDirectory(prefix="sima_appzoo_") as tmpdir:
            local_json = download_file_from_url(metadata_url, dest_folder=tmpdir, internal=False)
            json_path = os.path.join(tmpdir, os.path.basename(local_json))

            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)[0].get('current_version')

    except Exception as e:
        click.echo(f"❌ Failed to retrieve or parse app list: {e}")
        return None


def _list_external_apps(ver):
    """External flow behaves like internal list → describe → menu."""
    base_url = f"https://docs.sima.ai/pkg_downloads/SDK{ver}/app_zoo"
    index_url = f"{base_url}/pipelines_list.json"
    metadata_url = f"{base_url}/metadata.json"
    click.echo(f"🌐 Fetching App Zoo index from: {index_url}")

    current_version = _fetch_current_version(metadata_url)
    app_list = _fetch_app_index(index_url)
    if not app_list:
        click.echo("❌ No apps found in App Zoo index.")
        return []

    if not current_version:
        click.echo("❌ No current version found in App Zoo.")
        return []

    print(current_version)
    app_names = [app["name"] for app in app_list]

    while True:
        selected_app = inquirer.fuzzy(
            message=f"Select an App from SDK {ver}:",
            choices=app_names + ["Exit"],
            max_height="70%",
        ).execute()

        if not selected_app or selected_app == "Exit":
            click.echo("👋 Exiting.")
            break

        entry = next((a for a in app_list if a["name"] == selected_app), None)
        if not entry:
            click.echo(f"❌ Could not find metadata for {selected_app}.")
            continue

        assets = entry.get('assets')

        # Temporarily disable the yaml file download and presentation because we are not yet publishing it.
        yaml_url = f"{base_url}/{current_version}/{entry['yaml_file']}"
        data = _fetch_yaml_data(yaml_url, internal=False)
        if data:
            _describe_yaml_content(data, selected_app)

        action = _prompt_user_action(selected_app)
        if action == "Download":
            click.echo(f"⬇️  Downloading assets for '{selected_app}' ...")
            for a in assets:
                asset_url = f"{base_url}/{current_version}/{a}"
                download_file_from_url(asset_url, dest_folder=selected_app, internal=False)
        elif action == "Exit":
            break

# ─────────────────────────────────────────────
# Unified command entry points
# ─────────────────────────────────────────────

def list_apps(internal, ver):
    if internal:
        return _list_internal_apps(ver)
    else:
        return _list_external_apps(ver)


def describe_app(internal, ver, model_name):
    if internal:
        return _describe_app_internal(ver, model_name)
    else:
        click.echo("❌ Direct describe not supported for developer portal. Use list subcommand instead.")


def download_app(internal, ver, model_name):
    if internal:
        return _download_app_internal(ver, model_name)
    else:
        click.echo("❌ External ZIP download not supported for developer portal. Use list subcommand instead.")
