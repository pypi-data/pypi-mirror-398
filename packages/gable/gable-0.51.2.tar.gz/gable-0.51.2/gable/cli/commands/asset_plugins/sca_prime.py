import functools
import importlib
import json
import os
import re
import subprocess
import sys
import traceback
from typing import Any, Callable, List, Mapping, TypedDict

import click
from loguru import logger

from gable.api.client import GableAPIClient
from gable.cli.commands.asset_plugins.baseclass import (
    AssetPluginAbstract,
    ExtractedAsset,
)
from gable.cli.helpers.data_asset import (
    get_git_repo,
    get_relative_project_path,
    merge_rules_file_with_backend_config,
)
from gable.cli.helpers.emoji import EMOJI
from gable.cli.helpers.exclude_options import resolve_excludes_from_flag_and_rules
from gable.cli.helpers.npm import (
    get_sca_prime_results,
    prepare_npm_environment,
    run_sca_npx_help,
    start_sca_prime,
)
from gable.openapi import SourceType, StructuredDataAssetResourceName


def create_extracted_asset_from_finding(
    finding: dict[str, Any], source_type: SourceType, data_source: str
) -> ExtractedAsset | None:
    """
    Create an ExtractedAsset from a SCA Prime finding.

    Args:
        finding: A finding dictionary containing name, type, fields, etc.
        source_type: The source type for the DARN
        data_source: The data source for the DARN

    Returns:
        ExtractedAsset if the finding has required fields, None otherwise
    """
    finding_name = finding.get("name", f"Unresolved-name")
    finding_fields = finding.get("fields", [])

    # Use the static build_darn method to properly handle detection method logic
    darn = ScaPrimePlugin.build_darn(finding_name, finding, data_source, source_type)

    extracted_asset = ExtractedAsset(
        darn=darn,
        fields=[
            field
            for field in map(ExtractedAsset.safe_parse_field, finding_fields)
            if field is not None
        ],
        dataProfileMapping=None,
    )

    # Do not attempt to send assets without fields
    if extracted_asset.fields:
        return extracted_asset
    else:
        logger.debug(
            f"{EMOJI.RED_X.value} Skipping asset '{finding_name}' with no fields data"
        )
        return None


ScaPrimeConfig = TypedDict(
    "ScaPrimeConfig",
    {
        "project_root": click.Path,
        "annotation": str,
        "exclude_pattern": str,
        "debug": click.Option,
        "rules_file": click.Path,
        "prime_findings_file": click.Path,
    },
)


class ScaPrimePlugin(AssetPluginAbstract):
    def __init__(self, language: SourceType):
        self.language = language

    def source_type(self) -> SourceType:
        return self.language

    def click_options_decorator(self) -> Callable:
        def decorator(func):
            @click.option(
                "--project-root",
                help="The directory location of the project that will be analyzed.",
                type=click.Path(exists=True),
                required=True,
            )
            @click.option(
                "--annotation",
                help="Annotation name that will be used for asset detection, can include multiple entries (e.g. --annotation <a> --annotation <b>)",
                type=str,
                multiple=True,
                required=False,
            )
            @click.option(
                "--exclude-pattern",
                help="Glob pattern to exclude files or directories from the analysis, can include multiple entries (e.g., --exclude-pattern 'tests/**'  --exclude-pattern '**/node_modules').",
                type=str,
                multiple=True,
                required=False,
            )
            @click.option(
                "--rules-file",
                help="Rules file to be used for asset detection",
                type=click.Path(exists=True),
                required=False,
            )
            # This option is used for internal testing purposes only.
            # It allows to use a pre-existing findings.json file instead of running SCA Prime.
            @click.option(
                "--prime-findings-file",
                help="JSON file containing SCA Prime findings for asset extraction (bypasses actual SCA Prime execution)",
                type=click.Path(exists=True),
                required=False,
                hidden=True,
            )
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                exclude = kwargs.get("exclude")
                rules_file = kwargs.get("rules_file")
                if exclude and rules_file:
                    kwargs["exclude"] = resolve_excludes_from_flag_and_rules(
                        exclude,
                        rules_file,
                    )
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def click_options_keys(self) -> set[str]:
        return set(ScaPrimeConfig.__annotations__.keys())

    def pre_validation(self, config: Mapping) -> None:
        typed_config = ScaPrimeConfig(**config)

        if not typed_config.get("project_root"):
            raise click.MissingParameter(
                f"{EMOJI.RED_X.value} Missing required options for project registration. --project-root is required. You can use the --help option for more details.",
                param_type="option",
            )
        if typed_config.get("prime_findings_file"):
            if typed_config.get("annotation") or typed_config.get("rules_file"):
                raise click.MissingParameter(
                    f"{EMOJI.RED_X.value} --annotation and --rules-file are not supported when using --prime-findings-file",
                    param_type="option",
                )

    def extract_assets(
        self, client: GableAPIClient, config: Mapping
    ) -> List[ExtractedAsset]:
        try:
            typed_config = ScaPrimeConfig(**config)

            # required
            project_root = str(typed_config["project_root"])

            if findings_file := typed_config.get("prime_findings_file"):
                logger.info(
                    f"Internal feature - not supported for customer usage.\n Using pre-existing findings from: {findings_file}"
                )
                findings = self.extract_from_json_file(str(findings_file))
            else:
                # optional args
                rules_file = (
                    str(rules_path)
                    if (rules_path := typed_config.get("rules_file"))
                    else None
                )
                annotations = list(typed_config.get("annotation", []))
                exclude_patterns = config.get("exclude_pattern", [])

                # Here, read the rules file, get the backend rules config, merge them, save to a new temp file, and then call sca prime with it
                updated_rules_file = merge_rules_file_with_backend_config(
                    rules_file, client, self.language, project_root
                )

                prepare_npm_environment(client)
                run_sca_npx_help(client.endpoint)
                semgrep_bin_path = self.install_semgrep()

                sca_prime_future = start_sca_prime(
                    client=client,
                    project_root=project_root,
                    annotations=annotations,
                    exclude_patterns=exclude_patterns,
                    lang=self.source_type(),
                    sca_debug=("debug" in config),
                    semgrep_bin_path=semgrep_bin_path,
                    rules_file=updated_rules_file,
                )
                findings = get_sca_prime_results(
                    sca_prime_future, client, project_root, post_metrics=False
                )

            git_ssh_repo = get_git_repo(str(typed_config.get("project_root")))
            _, relative_project_root = get_relative_project_path(
                str(typed_config.get("project_root"))
            )

            data_source = f"git@{git_ssh_repo}:{relative_project_root}"

            self.log_findings(findings)

            return self.extract_assets_from_findings(
                self.source_type(), data_source, findings
            )

        except Exception as e:
            traceback.print_exc()
            raise click.ClickException(
                f"{EMOJI.RED_X.value} FAILURE: {e}",
            )

    @staticmethod
    def extract_assets_from_findings(
        default_source_type: SourceType,
        data_source: str,
        findings: list[dict[str, Any]],
    ) -> list[ExtractedAsset]:
        assets = []
        for finding in findings:
            asset = create_extracted_asset_from_finding(
                finding, default_source_type, data_source
            )
            if asset:
                assets.append(asset)
        return assets

    @staticmethod
    def extract_from_json_file(json_file_path: str) -> list[dict[str, Any]]:
        """Extract schema and location results from a JSON file containing SCA Prime findings."""

        try:
            with open(json_file_path, "r") as f:
                findings_data = json.load(f)

            if isinstance(findings_data, dict) and "findings" in findings_data:
                all_findings = findings_data["findings"]
            else:
                raise ValueError(
                    f"{EMOJI.RED_X.value} JSON file must contain a 'findings' array"
                )

            findings = [
                {
                    **finding["recap"],
                    "metadata": finding.get("metadata", {}),
                    "source_location": finding["source_location"],
                }
                for finding in all_findings
                if "recap" in finding and "source_location" in finding
            ]

            logger.debug(
                f"Extracted {len(findings)} assets from JSON file: {json_file_path}"
            )
            return findings

        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            raise click.ClickException(
                f"{EMOJI.RED_X.value} Error reading JSON file {json_file_path}: {e}"
            )

    @staticmethod
    def build_darn(
        asset_name: str,
        asset_info: dict,
        git_uri: str,
        default_source_type: SourceType,  # value of self.source_type(), passed in from extract_assets_from_findings
    ) -> StructuredDataAssetResourceName:
        metadata = asset_info.get("metadata", {})
        detection_method = metadata.get("detection_method", "Unknown-detection-method")

        language = metadata.get("language")
        source_type = SourceType(language) if language else default_source_type
        data_source = f"{git_uri}:[{detection_method}]"

        match detection_method:
            case "Annotation":
                return StructuredDataAssetResourceName(
                    source_type=source_type,
                    data_source=data_source,
                    path=asset_name,
                )
            case "CandidateDetection":
                return StructuredDataAssetResourceName(
                    source_type=source_type,
                    data_source=data_source,
                    path=asset_name,
                )
            case "CallSiteMatch":
                enclosing_function_name = metadata.get("enclosing_function_name")
                if not enclosing_function_name:
                    enclosing_function_name = "Unknown-enclosing"
                if (
                    enclosing_function_name
                    and "__FunctionDefinition" in enclosing_function_name
                ):
                    enclosing_function_name = re.sub(
                        r"__FunctionDefinition.*$",
                        "LAMBDA",
                        enclosing_function_name,
                    )

                egress_function_name = (
                    metadata.get("egress_function_name") or "Unknown-egress"
                )
                path = f"{enclosing_function_name}:{egress_function_name}:{asset_name}"

                return StructuredDataAssetResourceName(
                    source_type=source_type,
                    data_source=data_source,
                    path=path,
                )
            case _:
                return StructuredDataAssetResourceName(
                    source_type=source_type,
                    data_source=f"{git_uri}:[Unknown]",
                    path=asset_name,
                )

    def checked_when_registered(self) -> bool:
        return False

    def log_findings(self, findings: list[dict[str, Any]]) -> None:
        for finding in findings:
            asset_name = finding["name"]
            self.log_finding(asset_name, finding)

    def log_finding(self, asset_name: str, finding: dict[str, Any]) -> None:
        try:
            asset_type = finding["type"]
            asset_fields = finding.get("fields", [])
            source_location = finding["source_location"]

            if not asset_fields:
                logger.debug(
                    f"{EMOJI.RED_X.value} Asset '{asset_name}' has no fields data for logging"
                )
                return

            log_message = "Detected asset: \n" + asset_type + " " + asset_name + " {\n"
            for field in asset_fields:
                log_message += f"  {field['name']}: {field['type']}"
                if field["type"] == "union":
                    log_message += (
                        "[" + ", ".join([x["type"] for x in field["types"]]) + "]"
                    )
                elif field["type"] == "list":
                    log_message += f"[{field['values']['type']}]"
                elif field["type"] == "map":
                    log_message += (
                        f"[{field['keys']['type']}: {field['values']['type']}]"
                    )
                log_message += "\n"
            log_message += "}\n"
            location = (
                source_location["file_path"]
                + ":"
                + str(source_location["start"]["line"])
            )
            log_message += f"Location: {location}\n"
            logger.debug(log_message)

        except KeyError as e:
            logger.warning(
                f"{EMOJI.RED_X.value} Malformed findings data for asset: {asset_name} - {e}"
            )
            # try to show as much as possible, even if there are some failures

        except Exception as e:
            raise click.ClickException(
                f"{EMOJI.RED_X.value} Failed to render asset: {asset_name} - {e}",
            )

    def install_semgrep(self) -> str:
        return "".join(self._pip_install("semgrep", "1.90.0"))

    def _pip_install(self, package, exact_version, import_name=None) -> str:
        """
        Install a package using pip if it's not already installed
        """
        try:
            bin_path = os.path.join(
                importlib.import_module(import_name or package).__path__[0],
                "bin",
                "semgrep-core",
            )
            return bin_path
        except ImportError:
            try:
                subprocess.run(
                    [
                        # sys.executable is the path to the current python interpreter so we know
                        # we're installing the package in the same environment
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        f"{package}=={exact_version}",
                        "-qqq",
                    ],
                    check=True,
                )
                bin_path = os.path.join(
                    importlib.import_module(import_name or package).__path__[0],
                    "bin",
                    "semgrep-core",
                )
                return bin_path

            except Exception as e:
                raise click.ClickException(
                    f"Error installing {package}: {e}",
                )
