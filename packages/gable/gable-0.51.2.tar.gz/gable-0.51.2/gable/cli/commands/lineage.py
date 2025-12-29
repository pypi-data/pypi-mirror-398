import click

from gable.cli.commands.lineage_check import check_lineage
from gable.cli.commands.lineage_enrich import lineage_enrich
from gable.cli.commands.lineage_export import lineage_export
from gable.cli.commands.lineage_register import register_lineage
from gable.cli.commands.lineage_scan import lineage_scan
from gable.cli.commands.lineage_upload import lineage_upload
from gable.cli.options import global_options


@click.group(name="lineage")
@global_options(add_endpoint_options=False)
def lineage():
    """Commands for data lineage analysis using static code analysis (SCA)"""


lineage.add_command(register_lineage)
lineage.add_command(check_lineage)
lineage.add_command(lineage_scan)
lineage.add_command(lineage_enrich)
lineage.add_command(lineage_upload)
lineage.add_command(lineage_export)
