import json
import os
import subprocess
import sys

import click
from click.core import Context as ClickContext
from loguru import logger

from gable.cli.options import global_options


@click.command(
    add_help_option=False,
    name="enrich",
)
@global_options(add_endpoint_options=False)
@click.option(
    "--model",
    type=str,
    default="gpt-4o",
    help="The model to use for the enrichment.",
)
@click.option(
    "--project-root",
    help="The root directory of the project that will be analyzed.",
    type=click.Path(exists=True),
    required=True,
)
@click.option(
    "--results-file",
    type=click.Path(exists=True),
    help="The path to the SCA results file.",
    required=True,
    default=os.path.join(os.getcwd(), "gable_lineage_scan_results.json"),
)
@click.option(
    "--output",
    type=click.Path(exists=False, file_okay=True, dir_okay=False),
    help="File path to output results.",
    required=False,
    default=os.path.join(os.getcwd(), "gable_lineage_scan_results_enriched.json"),
)
@click.option(
    "--field-mapping",
    is_flag=True,
    help="Whether to use field mapping.",
    default=False,
)
@click.pass_context
def lineage_enrich(
    ctx: ClickContext,
    project_root: str,
    model: str,
    results_file: str,
    output: str,
    field_mapping: bool,
):
    """Enrich lineage with AI"""
    debug = ctx.obj.debug
    try:
        run_ai_enrichment(
            project_root,
            model,
            results_file,
            "transform_summaries.json",
            field_mapping,
            debug,
        )
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    result_file = os.path.join(os.getcwd(), "transform_summaries.json")
    results = json.loads(open(result_file).read())["results"]
    paths = json.loads(open(results_file).read())["paths"]
    if len(paths) != len(results):
        raise ValueError("Number of paths and results do not match")

    for path, summary in zip(paths, results):
        path["transformation_summary"] = summary["code_flow_summary"]
        path["transformation_summary_detailed"] = summary["transform_summary"]
        path["ingress"]["description"] = summary["ingress_point"]["description"]
        path["egress"]["description"] = summary["egress_point"]["description"]
        field_mappings = (summary.get("field_mapping", {}) or {}).get(
            "field_transformations", None
        )
        if field_mappings and len(field_mappings) > 0:
            # corresponds to field_mappings: https://github.com/gabledata/product/blob/912e96bacf02546cc55919c910be766dd77b9dd2/openapi/gable/components/schemas/sca-ingestion/StaticAnalysisDataFlowPath.yaml#L17
            path["field_mappings"] = [
                {
                    "ingress_field": mapping["source_field"],
                    "egress_field": mapping["target_field"],
                    "notes": mapping["description"],
                    # "field_data_flow_path" -- we don't current produce these field level code anchors
                }
                for mapping in field_mappings
            ]

    final_result = {"paths": paths}
    logger.info(f"Writing results to {os.path.abspath(output)}")
    open(output, "w").write(json.dumps(final_result, indent=4))


def run_ai_enrichment(
    project_root: str,
    model: str,
    sca_results_file: str,
    output: str,
    field_mapping: bool,
    debug: bool,
):
    if os.environ.get("GABLE_LOCAL") == "true":
        venv_bin_dir = os.path.join(os.getcwd(), ".venv", "bin")
        gable_ai_executable = os.path.join(venv_bin_dir, "gable-ai")
        if not os.path.exists(gable_ai_executable):
            click.echo(
                f"Error: gable-ai executable not found at {gable_ai_executable}",
                err=True,
            )
            sys.exit(1)
    else:
        gable_ai_executable = "gable-ai"

    cmd = [gable_ai_executable, "transform-summaries"]
    cmd.extend(["--model", model])
    cmd.extend(["--project-root", project_root])
    cmd.extend(["--input", sca_results_file])
    cmd.extend(["--output", output])

    if field_mapping:
        cmd.append("--field-mapping")

    if debug:
        cmd.append("--debug")

    subprocess.run(cmd, check=True)
