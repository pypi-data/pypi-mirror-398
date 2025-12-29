from typing import Optional

from .openapi import CrossServiceDataStore, SourceType, StaticAnalysisPathsUploadRequest

ALL_SOURCE_TYPES = list(SourceType)

DATABASE_SOURCE_TYPES = [
    SourceType.mysql,
    SourceType.mssql,
    SourceType.postgres,
]

FILE_SOURCE_TYPES = [SourceType.protobuf, SourceType.avro]

STATIC_CODE_ANALYSIS_SOURCE_TYPES = [
    SourceType.python,
    SourceType.typescript,
    SourceType.pyspark,
    SourceType.s3,
]

SCHEMA_SOURCE_TYPES = DATABASE_SOURCE_TYPES + FILE_SOURCE_TYPES


class LineageDataFile(StaticAnalysisPathsUploadRequest):
    run_id: Optional[str] = (
        None  # make optional for upload direct file, we will add this before upload
    )


class LineageDataStore(CrossServiceDataStore):
    run_id: Optional[str] = (
        None  # make optional for upload direct file, we will add this before upload
    )
