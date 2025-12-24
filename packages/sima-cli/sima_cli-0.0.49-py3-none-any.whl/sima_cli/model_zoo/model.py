# model_zoo/models.py

import requests
import click
import os
import yaml
from InquirerPy import inquirer
from urllib.parse import urlparse
from rich import print
from rich.table import Table
from rich.panel import Panel
from sima_cli.utils.config import get_auth_token
from sima_cli.utils.config_loader import artifactory_url
from sima_cli.download import download_file_from_url

ARTIFACTORY_BASE_URL = artifactory_url() + '/artifactory'

def _is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def _describe_model_internal(ver: str, model_name: str):
    repo = "sima-qa-releases"
    base_path = f"SiMaCLI-SDK-Releases/{ver}-Release/modelzoo_edgematic/{model_name}"
    aql_query = f"""
                items.find({{
                    "repo": "{repo}",
                    "path": "{base_path}",
                    "$or": [
                        {{ "name": {{ "$match": "*.yaml" }} }},
                        {{ "name": {{ "$match": "*.yml" }} }}
                    ],
                    "type": "file"
                }}).include("name", "path", "repo")
                """.strip()

    headers = {
        "Content-Type": "text/plain",
        "Authorization": f"Bearer {get_auth_token(internal=True)}"
    }

    aql_url = f"{ARTIFACTORY_BASE_URL}/api/search/aql"
    response = requests.post(aql_url, data=aql_query, headers=headers)
    if response.status_code != 200:
        click.echo(f"❌ Failed to list model files. Status: {response.status_code}")
        click.echo(response.text)
        return

    files = response.json().get("results", [])
    yaml_file = next((f for f in files if f["name"].endswith((".yaml", ".yml"))), None)

    if not yaml_file:
        click.echo(f"⚠️ No .yaml or .yml file found under: {base_path}")
        return

    # Download the YAML file
    yaml_url = f"{ARTIFACTORY_BASE_URL}/{repo}/{yaml_file['path']}/{yaml_file['name']}"
    response = requests.get(yaml_url, headers={"Authorization": f"Bearer {get_auth_token(internal=True)}"})

    if response.status_code != 200:
        click.echo(f"❌ Failed to fetch YAML: {response.status_code}")
        return

    try:
        data = yaml.safe_load(response.text)
    except yaml.YAMLError as e:
        click.echo(f"❌ Failed to parse YAML: {e}")
        return

    model = data.get("model", {})
    pipeline = data.get("pipeline", {})

    print(Panel.fit(f"[bold green]{model.get('name', 'Unknown')}[/bold green] - {model.get('task', 'Unknown Task')}",
                    subtitle=f"Status: [yellow]{model.get('status', 'n/a')}[/yellow]"))

    desc_table = Table(title="Description", show_header=False)
    for k, v in (model.get("description") or {}).items():
        desc_table.add_row(k.capitalize(), v or "-")
    print(desc_table)

    dataset = model.get("dataset", {})
    dataset_table = Table(title="Dataset", header_style="bold magenta")
    dataset_table.add_column("Key")
    dataset_table.add_column("Value")
    dataset_table.add_row("Name", dataset.get("name", "-"))
    for k, v in (dataset.get("params") or {}).items():
        dataset_table.add_row(k, str(v))
    dataset_table.add_row("Accuracy", dataset.get("accuracy", "-"))
    dataset_table.add_row("Calibration", dataset.get("calibration", "-"))
    print(dataset_table)

    if qm := model.get("quality_metric"):
        print(Panel.fit(f"Quality Metric: [cyan]{qm.get('name')}[/cyan]"))

    q = model.get("quantization_settings", {})
    q_table = Table(title="Quantization Settings", header_style="bold blue")
    q_table.add_column("Setting")
    q_table.add_column("Value")

    q_table.add_row("Calibration Samples", str(q.get("calibration_num_samples", "-")))
    q_table.add_row("Calibration Method", q.get("calibration_method", "-"))
    q_table.add_row("Requantization Mode", q.get("requantization_mode", "-"))
    q_table.add_row("Bias Correction", str(q.get("bias_correction", "-")))

    aq = q.get("activation_quantization_scheme", {})
    wq = q.get("weight_quantization_scheme", {})

    q_table.add_row("Activation Quant", f"Asym: {aq.get('asymmetric')}, PerCh: {aq.get('per_channel')}, Bits: {aq.get('bits')}")
    q_table.add_row("Weight Quant", f"Asym: {wq.get('asymmetric')}, PerCh: {wq.get('per_channel')}, Bits: {wq.get('bits')}")
    print(q_table)

    transforms = pipeline.get("transforms", [])
    t_table = Table(title="Pipeline Transforms", header_style="bold green")
    t_table.add_column("Name")
    t_table.add_column("Params")

    for step in transforms:
        name = step.get("name")
        params = step.get("params", {})
        param_str = ", ".join(f"{k}={v}" for k, v in params.items()) if params else "-"
        t_table.add_row(name, param_str)

    print(t_table)

def _download_model_internal(ver: str, model_name: str):
    repo = "sima-qa-releases"
    base_path = f"SiMaCLI-SDK-Releases/{ver}-Release/modelzoo_edgematic/{model_name}"
    aql_query = f"""
                items.find({{
                "repo": "{repo}",
                "path": {{
                    "$match": "{base_path}*"
                }},
                "type": "file"
                }}).include("repo", "path", "name")
                """.strip()

    aql_url = f"{ARTIFACTORY_BASE_URL}/api/search/aql"
    headers = {
        "Content-Type": "text/plain",
        "Authorization": f"Bearer {get_auth_token(internal=True)}"
    }

    response = requests.post(aql_url, data=aql_query, headers=headers)
    if response.status_code != 200:
        click.echo(f"Failed to list model files. Status: {response.status_code}, path: {aql_url}")
        click.echo(response.text)
        return

    results = response.json().get("results", [])
    if not results:
        click.echo(f"No files found for model: {model_name}")
        return

    dest_dir = os.path.join(os.getcwd(), model_name)
    os.makedirs(dest_dir, exist_ok=True)

    click.echo(f"Downloading files for model '{model_name}' to '{dest_dir}'...")

    for item in results:
        file_path = item["path"]
        file_name = item["name"]
        download_url = f"{ARTIFACTORY_BASE_URL}/{repo}/{file_path}/{file_name}"

        try:
            local_path = download_file_from_url(download_url, dest_folder=dest_dir, internal=True)
            click.echo(f"✅ {file_name} -> {local_path}")
        except Exception as e:
            click.echo(f"❌ Failed to download {file_name}: {e}")

    # Check for model_path.txt and optionally download external ONNX model
    model_path_file = os.path.join(dest_dir, "model_path.txt")
    if os.path.exists(model_path_file):
        with open(model_path_file, "r") as f:
            first_line = f.readline().strip()
            if _is_valid_url(first_line):
                click.echo(f"\n🔍 model_path.txt contains external model link:\n{first_line}")
                if click.confirm("Do you want to download the FP32 ONNX model from this link?", default=True):
                    try:
                        external_model_path = download_file_from_url(first_line, dest_folder=dest_dir, internal=True)
                        click.echo(f"✅ External model downloaded to: {external_model_path}")
                    except Exception as e:
                        click.echo(f"❌ Failed to download external model: {e}")
            else:
                click.echo("⚠️ model_path.txt exists but does not contain a valid URL.")

def _list_available_models_internal(version: str, boardtype: str):
    """
    Query Artifactory for available models for the given SDK version.
    Display them in an interactive menu with an 'Exit' option.
    Apply boardtype filtering:
      - gen1_target* → only shown for mlsoc
      - gen2_target* → only shown for modalix
      - others → always shown
    """
    repo_path = f"SiMaCLI-SDK-Releases/{version}-Release/modelzoo_edgematic"
    aql_query = f"""
        items.find({{
            "repo": "sima-qa-releases",
            "path": {{"$match": "{repo_path}/*"}},
            "type": "folder"
        }}).include("repo","path","name")
    """.strip()

    aql_url = f"{ARTIFACTORY_BASE_URL}/api/search/aql"
    headers = {
        "Content-Type": "text/plain",
        "Authorization": f"Bearer {get_auth_token(internal=True)}"
    }

    response = requests.post(aql_url, data=aql_query, headers=headers)
    if response.status_code != 200:
        click.echo(f"❌ Failed to retrieve model list (status {response.status_code})")
        click.echo(response.text)
        return None

    results = response.json().get("results", [])
    base_prefix = f"{repo_path}/"
    model_paths = sorted({
        item["path"].replace(base_prefix, "").rstrip("/") + "/" + item["name"]
        for item in results
    })

    if not model_paths:
        click.echo("No models found.")
        return None

    # Apply boardtype filtering
    filtered_models = []
    for model in model_paths:
        if model.startswith("gen1_target") and boardtype != "mlsoc":
            continue
        if model.startswith("gen2_target") and boardtype != "modalix":
            continue
        filtered_models.append(model)

    if not filtered_models:
        click.echo(f"No models found for board type '{boardtype}'.")
        return None

    while True:
        # Add Exit option
        choices = filtered_models + ["Exit"]

        # Interactive selection with InquirerPy
        selected_model = inquirer.fuzzy(
            message=f"Select a model from version {version}:",
            choices=choices,
            max_height="70%",
            instruction="(Use ↑↓ to navigate, / to search, Enter to select)"
        ).execute()

        if selected_model == "Exit":
            click.echo("👋 Exiting without selecting a model.")
            return None

        click.echo(f"✅ Selected model: {selected_model}")

        # Auto-describe
        _describe_model_internal(version, selected_model)

        # Action menu loop
        while True:
            action = inquirer.select(
                message=f"What do you want to do with {selected_model}?",
                choices=["Download model", "Back", "Exit"],
                default="Download model",
                qmark="👉",
            ).execute()

            if action == "Download model":
                _download_model_internal(version, selected_model)
            elif action == "Back":
                break  # back to model list
            else:  # Exit
                click.echo("👋 Exiting.")
                return None

def list_models(internal, ver, boardtype):
    if internal:
        click.echo("Model Zoo Source : SiMa Artifactory...")
        return _list_available_models_internal(ver, boardtype)
    else:
        print('External model zoo not supported yet')

def download_model(internal, ver, model_name):
    if internal:
        click.echo("Model Zoo Source : SiMa Artifactory...")
        return _download_model_internal(ver, model_name)
    else:
        print('External model zoo not supported yet')

def describe_model(internal, ver, model_name):
    if internal:
        click.echo("Model Zoo Source : SiMa Artifactory...")
        return _describe_model_internal(ver, model_name)
    else:
        print('External model zoo not supported yet')

# Module CLI tests
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python models.py <version>")
    else:
        version_arg = sys.argv[1]
        boardtype = sys.argv[2]
        _list_available_models_internal(version_arg, boardtype)
