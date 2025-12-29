"""Helper functions for uploading lineage data via API."""

from typing import Optional, Union

import click
from loguru import logger

from gable.api.client import GableAPIClient
from gable.common_types import LineageDataFile
from gable.openapi import (
    CrossServiceDataStore,
    CrossServiceDataStoreApiRequest,
    CrossServiceEdge,
    CrossServiceEdgeApiRequest,
    Destination,
    ErrorResponse,
    Metadata1,
    Metadata3,
    ScaResultsUploadRequest,
    Source,
    StaticAnalysisPathsApiRequest,
)

# Maximum chunk size in bytes (approximately 9MB)
MAX_CHUNK_SIZE_BYTES = 9 * 1024 * 1024


def _convert_metadata3_to_metadata1(
    metadata: Optional[Metadata3],
) -> Optional[Metadata1]:
    """Convert Metadata3 to Metadata1 (they have the same structure)."""
    if metadata is None:
        return None
    return Metadata1(extras=metadata.extras)


def _upload_api_request(
    client: GableAPIClient,
    api_request: Union[
        StaticAnalysisPathsApiRequest,
        CrossServiceDataStoreApiRequest,
        CrossServiceEdgeApiRequest,
    ],
    request_type: str,
) -> None:
    """Helper function to upload an API request and handle errors.

    Args:
        client: The Gable API client
        api_request: The API request object to upload
        request_type: A string describing the request type (for error messages)
    """
    upload_request = ScaResultsUploadRequest(root=api_request)
    response, success, status_code = client.post_sca_results(upload_request)

    if not success:
        error_msg = (
            f"API upload failed for {request_type}: "
            f"{response.message if isinstance(response, ErrorResponse) else response}"
        )
        raise click.ClickException(error_msg)

    logger.debug(f"Successfully uploaded {request_type} via API")


def upload_sca_results_via_api(
    client: GableAPIClient,
    run_id: str,
    lineage_data_file: Union[CrossServiceDataStore, CrossServiceEdge, LineageDataFile],
) -> None:
    """Upload SCA results via the API endpoint with chunking support.

    For CODE type (LineageDataFile), chunks the paths array to keep each chunk under 9MB.
    For DATA_STORE and EDGE types, sends the data as-is since they are single objects.

    Args:
        client: The Gable API client
        run_id: The ID of the run
        lineage_data_file: The lineage object to serialize and upload
    """
    if isinstance(lineage_data_file, LineageDataFile):
        # Chunk the paths array for CODE type
        paths = lineage_data_file.paths
        total_paths = len(paths)
        logger.debug(f"Uploading {total_paths} paths via API with chunking")

        chunk_start = 0
        chunk_index = 0

        while chunk_start < total_paths:
            # Find the right chunk size by incrementally building and checking size
            chunk_end = chunk_start
            test_paths = []

            # Build chunk incrementally, checking size after each addition
            while chunk_end < total_paths:
                test_paths.append(paths[chunk_end])
                # Estimate size of current chunk
                test_request = StaticAnalysisPathsApiRequest(
                    paths=test_paths,
                    run_id=run_id,
                    external_component_id=lineage_data_file.external_component_id,
                    type="CODE",
                    metadata=Metadata1(
                        extras=(
                            lineage_data_file.metadata.extras
                            if lineage_data_file.metadata
                            else None
                        )
                    ),
                    name=lineage_data_file.name,
                )
                test_json = test_request.json(by_alias=True, exclude_none=True)
                test_size = len(test_json.encode("utf-8"))

                if test_size > MAX_CHUNK_SIZE_BYTES:
                    # This chunk would be too large, remove the last path
                    if len(test_paths) > 1:
                        test_paths.pop()
                        chunk_end -= 1
                    break

                chunk_end += 1

            # Ensure we have at least one path in the chunk
            if not test_paths:
                # If even a single path exceeds the limit, we still need to send it
                test_paths = [paths[chunk_start]]
                chunk_end = chunk_start + 1

            # Create the chunk request
            chunk_request = StaticAnalysisPathsApiRequest(
                paths=test_paths,
                run_id=run_id,
                external_component_id=lineage_data_file.external_component_id,
                type="CODE",
                metadata=_convert_metadata3_to_metadata1(lineage_data_file.metadata),
                name=lineage_data_file.name,
            )

            # Upload this chunk
            _upload_api_request(client, chunk_request, f"chunk {chunk_index + 1}")

            logger.debug(
                f"Uploaded chunk {chunk_index + 1} with {len(test_paths)} paths "
                f"({chunk_start + 1}-{chunk_end} of {total_paths})"
            )

            chunk_start = chunk_end
            chunk_index += 1

        logger.debug(f"Successfully uploaded {chunk_index} chunk(s) via API")

    elif isinstance(lineage_data_file, CrossServiceDataStore):
        # DATA_STORE type - send as single request
        payload = lineage_data_file.model_dump(by_alias=True, exclude_none=True)
        payload["run_id"] = run_id  # ensure we use the run_id from the SCA run
        api_request = CrossServiceDataStoreApiRequest.model_validate(payload)
        _upload_api_request(client, api_request, "DATA_STORE")

    elif isinstance(lineage_data_file, CrossServiceEdge):
        # EDGE type - send as single request
        api_request = CrossServiceEdgeApiRequest(
            run_id=run_id,
            source_component_id=lineage_data_file.source_component_id,
            destination_component_id=lineage_data_file.destination_component_id,
            external_edge_id=lineage_data_file.external_edge_id,
            type=lineage_data_file.type,
            field_mappings=lineage_data_file.field_mappings,
            source=Source(
                component_id=lineage_data_file.source.component_id,
                egress_id=lineage_data_file.source.egress_id,
                type=lineage_data_file.source.type,
                payload_name=lineage_data_file.source.payload_name,
            ),
            destination=Destination(
                component_id=lineage_data_file.destination.component_id,
                ingress_id=lineage_data_file.destination.ingress_id,
                type=lineage_data_file.destination.type,
                payload_name=lineage_data_file.destination.payload_name,
            ),
        )
        _upload_api_request(client, api_request, "EDGE")

    else:
        raise ValueError(
            f"Unsupported lineage_data_file type: {type(lineage_data_file)}"
        )
