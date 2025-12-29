import os
import subprocess
from importlib import metadata

import click

from gable.cli.client import GableAPIClient, GableCliClient
from gable.cli.helpers.npm import (
    prepare_npm_environment,
    should_use_docker_node_cmd,
    should_use_local_sca,
)


def get_openapi_version():
    """Get the OpenAPI schema version"""
    try:
        from gable.openapi import OPENAPI_SCHEMA_VERSION

        return OPENAPI_SCHEMA_VERSION
    except (ImportError, AttributeError):
        return "unknown"


def get_api_version(client: GableCliClient):
    """Get the API version"""
    if os.getenv("GABLE_CLI_ISOLATION", "") == "true":
        raise Exception("API version: unable to reach API due to isolation mode")

    response, success, status_code = client.internal_client.get_version()
    if isinstance(response, dict):
        return response["hash"]
    else:
        raise Exception("API version response is not a dict")


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    cli_version = metadata.version("gable")
    openapi_version = get_openapi_version()
    click.echo(f"CLI version: {cli_version}")
    click.echo(f"OpenAPI Schema version: {openapi_version}")
    try:
        client = GableCliClient()
        api_version = get_api_version(client)
        click.echo(f"API version: {api_version}")
    except ValueError as e:
        click.echo(
            f"API version: unable to reach API due to lack of API key or endpoint"
        )
    except Exception as e:
        click.echo(f"API version: unable to reach")

    sca_version = None
    if should_use_docker_node_cmd():
        sca_version = "docker"
    elif should_use_local_sca(None):
        sca_version = "local"
    else:
        try:
            prepare_npm_environment(GableCliClient())  # type: ignore
            env_version = os.environ.get("GABLE_SCA_VERSION")
            if env_version:
                # Check if the specified version exists
                result = subprocess.run(
                    ["npm", "view", f"@gable-eng/sca@{env_version}", "version"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                if result.returncode == 0 and result.stdout.strip():
                    sca_version = result.stdout.strip()
                else:
                    sca_version = f"{env_version} (not found in registry)"
            else:
                # Get latest version
                result = subprocess.run(
                    ["npm", "show", "@gable-eng/sca", "version"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                sca_version = result.stdout.strip()
        except Exception:
            env_version = os.environ.get("GABLE_SCA_VERSION")
            if env_version:
                sca_version = f"{env_version} (validation failed)"
    if sca_version:
        click.echo(f"SCA version: {sca_version}")
    ctx.exit()
