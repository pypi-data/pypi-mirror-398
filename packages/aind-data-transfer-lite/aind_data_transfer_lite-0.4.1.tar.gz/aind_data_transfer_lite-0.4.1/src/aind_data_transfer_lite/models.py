"""Module for package models."""

from typing import ClassVar, Dict, List

from aind_data_schema_models.modalities import Modality
from pydantic import DirectoryPath, Field, field_validator
from pydantic_settings import BaseSettings


class JobSettings(
    BaseSettings, cli_parse_args=True, cli_ignore_unknown_args=True
):
    """Settings for uploading data."""

    _modality_map: ClassVar[dict] = Modality.abbreviation_map
    _modality_abbreviations: ClassVar[List[str]] = list(_modality_map.keys())

    # Required Fields
    metadata_directory: DirectoryPath = Field(
        ...,
        description=(
            "Directory where aind-data-schema compliant metadata files are"
            " located"
        ),
        title="Metadata Directory",
    )
    modality_directories: Dict[str, DirectoryPath] = Field(
        ...,
        description=(
            f"Directories for data associated with each modality; must be"
            f" keyed by {_modality_abbreviations}"
        ),
        title="Modality Directories",
    )

    # Optional Fields
    metadata_docdb_host: str = Field(
        default="api.allenneuraldynamics.org",
        description=(
            "Host for the MetadataDBClient to interface with DocumentDB"
        ),
        title="Metadata DocDB Host",
    )
    metadata_docdb_version: str = Field(
        default="v2",
        description=(
            "API version for the MetadataDBClient to interface "
            "with DocumentDB"
        ),
        title="Metadata API Version",
    )
    s3_bucket: str = Field(
        default="aind-open-data",
        description="S3 bucket to upload data to",
        title="S3 Bucket",
    )
    dry_run: bool = Field(
        default=True,
        description=(
            "Perform a dry run of the upload without uploading any data."
        ),
        title="Dry Run",
    )

    # noinspection PyNestedDecorators
    @field_validator("modality_directories", mode="before")
    @classmethod
    def validate_modality_keys(cls, value: dict) -> dict:
        """
        Verifies dictionary keys are unique and are valid modalities.
        Parameters
        ----------
        value : dict

        Returns
        -------
        dict

        Raises
        ______
        KeyError

        """
        keys = list(value.keys())
        invalid_keys = [
            k for k in keys if k not in cls._modality_abbreviations
        ]
        if invalid_keys:
            raise KeyError(
                f"{invalid_keys} are not from set of "
                f"{cls._modality_abbreviations}."
            )
        return value
