import os
import shutil
import sys

import click
from loguru import logger

from gable.cli.helpers.jsonpickle import register_jsonpickle_handlers
from gable.cli.helpers.logging import configure_default_click_logging
from gable.cli.options import global_options
from gable.cli.version import print_version
from gable.openapi import CreateTelemetryRequest, TelemetryType

from .commands.auth import auth
from .commands.contract import contract
from .commands.data_asset import data_asset
from .commands.debug import debug
from .commands.lineage import lineage
from .commands.ping import ping
from .commands.ui import ui

# Configure default logging which uses click.echo(), this will be replaced if the --debug flag is passed
# to the CLI
configure_default_click_logging()
# Configure jsonpickle's custom serialization handlers
register_jsonpickle_handlers()


# Click normally wraps text at 80 characters, but this is too narrow and makes the help text difficult to read.
# This sets the max width to the width of the terminal, which is a better default.
@click.group(
    add_help_option=False,
    context_settings={"max_content_width": shutil.get_terminal_size().columns},
)
@global_options()
@click.option(
    "--version",
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
    help="Show the version and exit.",
)
def cli():
    pass


cli.add_command(auth)
cli.add_command(debug)
cli.add_command(lineage)
cli.add_command(contract)
cli.add_command(data_asset)
cli.add_command(ping)
cli.add_command(ui)


@cli.result_callback()
@click.pass_context
def process_result(ctx, result, **kwargs):
    """This function runs after the command has finished."""
    # Skip telemetry if the environment variable is set used for C1 testing
    # Since the API is not reachable at moment from the C1 test environment
    if os.getenv("GABLE_SKIP_TELEMETRY", "").lower() == "true":
        return

    try:
        argv_cleaned = sys.argv[1:]
        for forbidden_arg in ["--api-key", "--proxy-password"]:
            if forbidden_arg in argv_cleaned:
                key_index = argv_cleaned.index(forbidden_arg)
                argv_cleaned = argv_cleaned[1:key_index] + argv_cleaned[key_index + 2 :]

        ctx.obj.client.post_telemetry(
            CreateTelemetryRequest(
                id=None,
                data={"argv": argv_cleaned},
                type=TelemetryType.GABLE_CLIENT,
            )
        )
    except Exception as e:
        logger.debug(f"Error posting telemetry: {e}")


if __name__ == "__main__":
    cli()
