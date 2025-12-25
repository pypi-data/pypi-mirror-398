import copy
import os
import random
import string
import tempfile
from typing import Dict, List, Optional, Tuple

import typer
import yaml

from avatars.manager import Manager
from avatars.models import JobKind


def random_string(length):
    """Generate a random string of fixed length."""

    letters = string.ascii_letters
    return "".join(random.choice(letters) for i in range(length))  # noqa: S311


app = typer.Typer(help="Run avatarization with a YAML config file.")


def extract_file_references_from_yaml(yaml_path: str) -> List[Tuple[str, str, str]]:
    """
    Extract all file references from the YAML configuration.

    Returns:
        List of tuples containing (table_name, volume_name, file_name)
    """
    with open(yaml_path, "r") as f:
        yaml_content = list(yaml.safe_load_all(f))

    file_references = []

    for doc in yaml_content:
        if doc.get("kind") == "AvatarSchema" and "spec" in doc and "tables" in doc["spec"]:
            for table in doc["spec"]["tables"]:
                if "data" in table and "file" in table["data"]:
                    table_name = table["name"]
                    volume_name = table["data"].get("volume", "")
                    file_name = table["data"]["file"]
                    file_references.append((table_name, volume_name, file_name))

    return file_references


def modify_yaml_with_new_paths(yaml_path: str, file_mapping: Dict[str, str]) -> str:
    """
    Create a copy of the YAML file with updated file paths.

    Args:
        yaml_path: Path to the original YAML file
        file_mapping: Dictionary mapping original filenames to new paths

    Returns:
        Path to the modified YAML file
    """
    with open(yaml_path, "r") as f:
        yaml_content = list(yaml.safe_load_all(f))

    # Create modified YAML content
    modified_content = copy.deepcopy(yaml_content)

    for doc in modified_content:
        if doc.get("kind") == "AvatarSchema" and "spec" in doc and "tables" in doc["spec"]:
            for table in doc["spec"]["tables"]:
                if "data" in table and "file" in table["data"]:
                    original_filename = table["data"]["file"]
                    if original_filename in file_mapping:
                        # Extract just the filename from the path,
                        # as the API expects just a filename
                        table["data"]["file"] = os.path.basename(file_mapping[original_filename])

    # Create a temporary file for the modified YAML
    fd, temp_path = tempfile.mkstemp(suffix=".yaml")
    os.close(fd)

    # Write the modified YAML to the temporary file
    with open(temp_path, "w") as f:
        yaml.dump_all(modified_content, f, default_flow_style=False)

    return temp_path


def prompt_for_file_paths(file_references: List[Tuple[str, str, str]]) -> Dict[str, str]:
    """
    Prompt the user to provide paths for each referenced file.

    Args:
        file_references: List of tuples containing (table_name, volume_name, file_name)

    Returns:
        Dictionary mapping original filenames to user-provided paths
    """
    file_mapping = {}

    typer.echo("\nThe YAML configuration refers to the following input files:")

    for table_name, _, file_name in file_references:
        typer.echo(f"  • Table '{table_name}' requires file '{file_name}'")

    typer.echo("\nPlease provide the paths to these files:")

    for table_name, _, file_name in file_references:
        while True:
            user_input = input(
                f"Please input the path to the file named '{file_name}' for table '{table_name}': "
            )
            if user_input and os.path.isfile(user_input):
                file_mapping[file_name] = user_input
                break
            else:
                typer.echo(f"Error: '{user_input}' is not a valid file path. Please try again.")

    return file_mapping


@app.command()
def main(
    yaml_path: str = typer.Option(..., "--yaml", "-y", help="Path to the YAML configuration file"),
    set_name: str = typer.Option(None, "--set-name", "-n", help="Name of the set to create"),
    url: str = typer.Option(
        os.environ.get("AVATAR_BASE_URL", "https://www.octopize.app/api"),
        "--url",
        "-u",
        help="Base URL for the Avatarization API (default: $AVATAR_BASE_URL or https://www.octopize.app/api)",
    ),
    username: Optional[str] = typer.Option(
        os.environ.get("AVATAR_USERNAME"),
        "--username",
        help="Username for authentication (default: $AVATAR_USERNAME)",
    ),
    password: Optional[str] = typer.Option(
        os.environ.get("AVATAR_PASSWORD"),
        "--password",
        help="Password for authentication (default: $AVATAR_PASSWORD)",
    ),
    no_report: bool = typer.Option(False, "--no-report", help="Skip generating the report"),
    report_path: Optional[str] = typer.Option(
        None, "--report-path", help="Path where to save the report"
    ),
    non_interactive: bool = typer.Option(
        False,
        "--non-interactive",
        help="Non-interactive mode, use file paths as specified in the YAML without prompting",
    ),
) -> None:
    """Run avatarization with a YAML config file."""
    # Apply the default random string for set_name if not provided
    if set_name is None:
        set_name = random_string(10)

    # Validate required arguments
    if not os.path.isfile(yaml_path):
        typer.echo(f"Error: YAML file '{yaml_path}' not found", err=True)
        raise typer.Exit(code=1)

    if not username or not password:
        typer.echo(
            "Error: Username and password are required. "
            "Provide them as arguments or environment variables.",
            err=True,
        )
        raise typer.Exit(code=1)

    # Extract file references from the YAML
    file_references = extract_file_references_from_yaml(yaml_path)

    if not file_references:
        typer.echo("Warning: No data file references found in the YAML configuration.")

    # Initialize the manager and authenticate
    typer.echo(f"Connecting to {url}...")
    manager = Manager(base_url=url)

    try:
        manager.authenticate(username, password)
        typer.echo("Authentication successful")
    except Exception as e:  # noqa: BLE001
        typer.echo(f"Authentication failed: {e}", err=True)
        raise typer.Exit(code=1)

    # If interactive mode, prompt for file paths
    file_mapping = {}
    effective_yaml_path = yaml_path
    if file_references and not non_interactive:
        file_mapping = prompt_for_file_paths(file_references)
        effective_yaml_path = modify_yaml_with_new_paths(yaml_path, file_mapping)
        typer.echo(f"Created modified YAML with updated file paths: {effective_yaml_path}")

    # Upload the files first before creating the runner
    if file_mapping:
        typer.echo("\nUploading input files...")
        for original_name, file_path in file_mapping.items():
            try:
                typer.echo(f"Uploading {file_path}...")
                # Fix: Use the file path directly instead of opening the file ourselves
                # The upload_file method will handle opening the file
                manager.auth_client.upload_file(file_path, os.path.basename(file_path))
                typer.echo(f"Successfully uploaded {os.path.basename(file_path)}")
            except Exception as e:  # noqa: BLE001
                typer.echo(f"Failed to upload file {os.path.basename(file_path)}: {e}", err=True)
                raise typer.Exit(code=1)

    # Create a runner from the YAML file
    typer.echo(f"\nCreating runner from YAML file: {effective_yaml_path}")
    try:
        runner = manager.create_runner_from_yaml(yaml_path=effective_yaml_path, set_name=set_name)
        typer.echo(f"Runner created successfully for set: {set_name}")
    except Exception as e:  # noqa: BLE001
        typer.echo(f"Failed to create runner: {e}", err=True)
        raise typer.Exit(code=1)

    # Clean up temporary YAML file if it was created
    if effective_yaml_path != yaml_path:
        try:
            # os.remove(effective_yaml_path)
            typer.echo(f"Cleaned up temporary YAML file: {effective_yaml_path}")
        except Exception as e:  # noqa: BLE001
            typer.echo(f"Warning: Failed to clean up temporary YAML file: {e}")

    # Determine which jobs to run
    jobs_to_run = [JobKind.standard, JobKind.signal_metrics, JobKind.privacy_metrics]
    if not no_report:
        jobs_to_run.append(JobKind.report)

    # Run the avatarization
    typer.echo("\nStarting avatarization process...")
    try:
        jobs = runner.run(jobs_to_run=jobs_to_run)
        typer.echo("Avatarization jobs submitted successfully")

        # Get results
        typer.echo("Gathering results...")
        runner.get_all_results()
        typer.echo("Results collected successfully")

        # Download report if requested
        if JobKind.report in jobs and report_path:
            typer.echo(f"Downloading report to {report_path}")
            runner.download_report(report_path)
            typer.echo(f"Report saved to {report_path}")

    except Exception as e:  # noqa: BLE001
        typer.echo(f"Error during avatarization: {e}", err=True)
        raise typer.Exit(code=1)

    typer.echo("\nAvatarization process completed successfully!")


if __name__ == "__main__":
    app()
