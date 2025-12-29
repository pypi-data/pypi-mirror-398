from urllib.parse import quote

import click
from click.core import Context as ClickContext

from gable.api.client import GableAPIClient
from gable.cli.helpers.data_asset import merge_dataflow_config_file_with_backend_config
from gable.cli.helpers.emoji import EMOJI
from gable.cli.helpers.lineage import (
    build_sca_args,
    ensure_npm_and_maybe_start_run,
    handle_darn_to_string,
    resolve_results_dir,
    run_sca_and_capture,
    upload_results_and_poll,
)
from gable.cli.helpers.npm import get_sca_cmd
from gable.cli.helpers.shell_output import shell_linkify_if_not_in_ci
from gable.cli.options import global_options


@click.command(
    add_help_option=False,
    name="register",
    epilog="""Example:
    gable lineage register --project-root ./path/to/project --language java --build-command "mvn clean install" --java-version 17""",
)
@global_options(add_endpoint_options=False)
@click.option(
    "--project-root",
    help="The root directory of the project that will be analyzed.",
    type=click.Path(exists=True),
    required=True,
)
@click.option(
    "--language",
    help="The programming language of the project.",
    type=click.Choice(["java"]),
    default="java",
)
@click.option(
    "--build-command",
    help="The build command used to build the project (e.g. mvn clean install).",
    type=str,
    required=False,
)
@click.option(
    "--java-version",
    help="The version of Java used to build the project.",
    type=str,
    default="17",
    required=False,
)
@click.option(
    "--dataflow-config-file",
    type=click.Path(exists=True),
    help="The path to the dataflow config JSON file.",
    required=False,
)
@click.option(
    "--dataflow-config-files",
    help="Multi option for dataflow config files. Overridden by --dataflow-config-file.",
    multiple=True,
    required=False,
)
@click.option(
    "--schema-depth",
    help="The max depth of the schemas to be extracted.",
    type=int,
    required=False,
)
@click.pass_context
def register_lineage(
    ctx: ClickContext,
    project_root: str,
    language: str,  # pylint: disable=unused-argument
    build_command: str,
    java_version: str,
    dataflow_config_file: str,
    dataflow_config_files: list[str],
    schema_depth: int,
):
    """
    Run static code analysis (SCA) to extract and register data lineage.
    """
    run_id, presigned_url, backend_config = ensure_npm_and_maybe_start_run(
        ctx, project_root, action="register", output=None, include_unchanged_assets=None
    )
    results_dir = resolve_results_dir(run_id)

    updated_dataflow_config_file = merge_dataflow_config_file_with_backend_config(
        dataflow_config_file, backend_config
    )

    sca_cmd = get_sca_cmd(
        None,
        build_sca_args(
            project_root,
            java_version,
            build_command,
            updated_dataflow_config_file,
            dataflow_config_files,
            schema_depth,
            results_dir,
        ),
    )
    final_stdout = run_sca_and_capture(sca_cmd)

    if presigned_url:
        client: GableAPIClient = ctx.obj.client
        sca_outcomes = upload_results_and_poll(
            client, run_id, presigned_url, results_dir
        )

        registered_assets = 0
        for outcome in sca_outcomes.get("asset_registration_outcomes", []):
            if outcome.get("error"):
                click.echo(
                    f"{EMOJI.RED_X.value} Error registering data asset: {outcome['error']}"
                )
                continue

            darn_string = handle_darn_to_string(
                outcome.get("data_asset_resource_name", {})
            )
            maybe_linkified_darn = shell_linkify_if_not_in_ci(
                f"{client.ui_endpoint}/assets/{quote(darn_string, safe='')}",
                darn_string,
            )
            registered_assets += 1
            click.echo(
                f"{EMOJI.GREEN_CHECK.value} Data asset {maybe_linkified_darn} registered successfully"
            )
        if registered_assets > 0:
            click.echo(f"{registered_assets} assets registered successfully")
