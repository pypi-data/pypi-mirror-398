import json

import click
from click.core import Context as ClickContext

from gable.api.client import GableAPIClient
from gable.cli.options import global_options


@click.command(
    add_help_option=False,
    name="export",
    epilog="""Example:
    gable lineage export""",
)
@global_options(add_endpoint_options=False)
@click.pass_context
def lineage_export(
    ctx: ClickContext,
):
    """
    Export lineage data from Gable.
    """
    client: GableAPIClient = ctx.obj.client
    cross_service_components = client.get_cross_service_components()
    json_string = json.dumps(cross_service_components, indent=2)
    print(json_string)
