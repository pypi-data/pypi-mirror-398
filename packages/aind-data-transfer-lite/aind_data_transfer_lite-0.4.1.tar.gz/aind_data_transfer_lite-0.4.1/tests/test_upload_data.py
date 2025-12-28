"""Unit tests for upload_data module."""

import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, patch

from aind_data_transfer_lite.models import JobSettings
from aind_data_transfer_lite.upload_data import UploadDataJob

RESOURCES_DIR = Path(os.path.dirname(os.path.realpath(__file__))) / "resources"


class TestUploadDataJob(unittest.TestCase):
    """Tests for UploadDataJob class"""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up common JobSettings"""
        job_settings = JobSettings(
            metadata_directory=RESOURCES_DIR / "metadata_dir",
            modality_directories={
                "ecephys": RESOURCES_DIR / "ecephys_data",
                "behavior": RESOURCES_DIR / "behavior_data",
            },
            dry_run=True,
            s3_bucket="aind-private-data-dev-u5u0i5",
        )
        job = UploadDataJob(job_settings=job_settings)
        # This will cache the s3_prefix to avoid reading the
        # data_description multiple times
        _ = job.s3_prefix
        cls.job = job

    def test_s3_prefix(self):
        """Tests s3_prefix is properly set from data_description."""
        self.assertEqual("12345_2022-02-21_16-30-01", self.job.s3_prefix)

    def test_s3_root_location(self):
        """Tests s3_root_location is properly set from data_description."""
        self.assertEqual(
            "s3://aind-private-data-dev-u5u0i5/12345_2022-02-21_16-30-01",
            self.job.s3_root_location,
        )

    @patch("boto3.client")
    def test_check_s3_location(self, mock_boto: MagicMock):
        """Tests _check_s3_location when s3_location is clear."""
        mock_list_objects_v2 = MagicMock()
        mock_list_objects_v2.return_value = {"KeyCount": 0}
        mock_client = MagicMock()
        mock_client.list_objects_v2 = mock_list_objects_v2
        mock_boto.return_value = mock_client
        with self.assertLogs(level="INFO") as captured:
            self.job._check_s3_location()
        mock_list_objects_v2.assert_called_once_with(
            Bucket="aind-private-data-dev-u5u0i5",
            Prefix="12345_2022-02-21_16-30-01",
            MaxKeys=1,
        )
        self.assertEqual(["INFO:root:Checking S3 Location"], captured.output)

    @patch("boto3.client")
    def test_check_s3_location_exists(self, mock_boto: MagicMock):
        """Tests _check_s3_location when s3_location already exists."""
        mock_list_objects_v2 = MagicMock()
        mock_list_objects_v2.return_value = {"KeyCount": 1}
        mock_client = MagicMock()
        mock_client.list_objects_v2 = mock_list_objects_v2
        mock_boto.return_value = mock_client
        with self.assertLogs(level="INFO") as captured:
            with self.assertRaises(FileExistsError) as e:
                self.job._check_s3_location()
        self.assertIn(
            (
                "s3://aind-private-data-dev-u5u0i5/12345_2022-02-21_16-30-01"
                " already exists! Please contact a data admin for help."
            ),
            str(e.exception),
        )
        mock_list_objects_v2.assert_called_once_with(
            Bucket="aind-private-data-dev-u5u0i5",
            Prefix="12345_2022-02-21_16-30-01",
            MaxKeys=1,
        )
        self.assertEqual(["INFO:root:Checking S3 Location"], captured.output)

    def test_check_metadata_files(self):
        """Tests _check_metadata_files when all files present."""
        with self.assertLogs(level="INFO") as captured:
            self.job._check_metadata_files()
        self.assertEqual(
            ["INFO:root:Checking metadata directory"], captured.output
        )

    @patch("os.listdir")
    def test_check_metadata_missing_file(self, mock_listdir: MagicMock):
        """Tests _check_metadata_files when file is missing."""
        # Mock so subject.json is missing.
        mock_listdir.return_value = [
            "acquisition.json",
            "data_description.json",
            "procedures.json",
            "instrument.json",
        ]
        with self.assertLogs(level="INFO") as captured:
            with self.assertRaises(Exception) as e:
                self.job._check_metadata_files()
        self.assertEqual(
            ["INFO:root:Checking metadata directory"], captured.output
        )
        self.assertIn(
            (
                "Required metadata files not found in metadata directory!"
                " {'subject'}"
            ),
            str(e.exception),
        )

    @patch("os.listdir")
    def test_check_metadata_extra_file(self, mock_listdir: MagicMock):
        """Tests _check_metadata_files when extra file present."""
        # Mock so subject.json is missing.
        mock_listdir.return_value = [
            "acquisition.json",
            "data_description.json",
            "procedures.json",
            "instrument.json",
            "subject.json",
            "extra_stuff.json",
        ]
        with self.assertLogs(level="INFO") as captured:
            with self.assertRaises(Exception) as e:
                self.job._check_metadata_files()
        self.assertEqual(
            ["INFO:root:Checking metadata directory"], captured.output
        )
        self.assertIn(
            (
                "Unexpected files found in metadata directory!"
                " {'extra_stuff'}"
            ),
            str(e.exception),
        )

    @patch("platform.system")
    @patch("subprocess.run")
    def test_run_s3_sync_command(
        self, mock_subprocess_run: MagicMock, mock_platform: MagicMock
    ):
        """Tests _run_s3_sync_command."""
        mock_platform.return_value = "Linux"
        self.job._run_s3_sync_command(
            src_folder="local_folder",
            s3_location="s3://bucket/prefix",
            dry_run=True,
        )
        mock_subprocess_run.assert_called_once_with(
            [
                "aws",
                "s3",
                "sync",
                "local_folder",
                "s3://bucket/prefix",
                "--dryrun",
            ],
            check=True,
            shell=False,
        )

    @patch("platform.system")
    @patch("subprocess.run")
    def test_run_s3_sync_command_windows(
        self, mock_subprocess_run: MagicMock, mock_platform: MagicMock
    ):
        """Tests _run_s3_sync_command on Windows."""
        mock_platform.return_value = "Windows"
        self.job._run_s3_sync_command(
            src_folder="local_folder",
            s3_location="s3://bucket/prefix",
            dry_run=True,
        )
        mock_subprocess_run.assert_called_once_with(
            [
                "aws",
                "s3",
                "sync",
                "local_folder",
                "s3://bucket/prefix",
                "--dryrun",
            ],
            check=True,
            shell=True,
        )

    @patch(
        "aind_data_transfer_lite.upload_data.UploadDataJob"
        "._run_s3_sync_command"
    )
    def test_upload_data(self, mock_run_s3_command: MagicMock):
        """Tests _upload_data."""
        with self.assertLogs(level="INFO") as captured:
            self.job._upload_directory_data()
        expected_s3_location = (
            "s3://aind-private-data-dev-u5u0i5/12345_2022-02-21_16-30-01"
        )
        expected_subprocess_calls = [
            call(
                src_folder=str(RESOURCES_DIR / "ecephys_data"),
                s3_location=f"{expected_s3_location}/ecephys",
                dry_run=True,
            ),
            call(
                src_folder=str(RESOURCES_DIR / "behavior_data"),
                s3_location=f"{expected_s3_location}/behavior",
                dry_run=True,
            ),
            call(
                src_folder=str(RESOURCES_DIR / "metadata_dir"),
                s3_location=f"{expected_s3_location}",
                dry_run=True,
            ),
        ]
        self.assertEqual(
            [
                "INFO:root:Uploading Modality Data",
                "INFO:root:Uploading metadata files",
            ],
            captured.output,
        )
        self.assertEqual(
            expected_subprocess_calls, mock_run_s3_command.mock_calls
        )

    @patch("aind_data_transfer_lite.upload_data.MetadataDbClient")
    def test_register_asset_dry_run(self, mock_docdb_client: MagicMock):
        """Tests _register_asset with dry_run True."""
        with self.assertLogs(level="INFO") as captured:
            self.job._register_asset()
        mock_docdb_client.assert_not_called()
        self.assertEqual(
            [
                (
                    "INFO:root:(dryrun) Would register asset at:"
                    f" {self.job.s3_root_location}"
                )
            ],
            captured.output,
        )

    @patch("aind_data_transfer_lite.upload_data.MetadataDbClient")
    def test_register_asset_no_dry_run(self, mock_docdb_client: MagicMock):
        """Tests _register_asset with dry_run False."""
        job_settings_run = self.job.job_settings.model_copy(
            update={"dry_run": False}, deep=True
        )
        job_run = UploadDataJob(job_settings=job_settings_run)
        mock_instance = MagicMock()
        mock_instance.register_asset.return_value = {"status": "ok"}
        mock_docdb_client.return_value = mock_instance
        with self.assertLogs(level="INFO") as captured:
            job_run._register_asset()
        mock_docdb_client.assert_called_once_with(
            host=job_settings_run.metadata_docdb_host,
            version=job_settings_run.metadata_docdb_version,
        )
        mock_instance.register_asset.assert_called_once_with(
            s3_location=job_run.s3_root_location
        )
        self.assertEqual(
            [
                f"INFO:root:Registering asset for: {job_run.s3_root_location}",
                "INFO:root:Register asset response: {'status': 'ok'}",
            ],
            captured.output,
        )

    @patch("aind_data_transfer_lite.upload_data.UploadDataJob._register_asset")
    @patch(
        "aind_data_transfer_lite.upload_data.UploadDataJob"
        "._upload_directory_data"
    )
    @patch(
        "aind_data_transfer_lite.upload_data.UploadDataJob"
        "._check_metadata_files"
    )
    @patch(
        "aind_data_transfer_lite.upload_data.UploadDataJob._check_s3_location"
    )
    @patch("aind_data_transfer_lite.upload_data.time")
    def test_run_job(
        self,
        mock_time: MagicMock,
        mock_check_s3_location: MagicMock,
        mock_check_metadata_files: MagicMock,
        mock_upload_directory_data: MagicMock,
        mock_register_asset: MagicMock,
    ):
        """Tests run_job."""
        mock_time.side_effect = [1750017362.7353837, 1750018371.6479027]
        with self.assertLogs(level="INFO") as captured:
            self.job.run_job()
        mock_check_s3_location.assert_called_once()
        mock_check_metadata_files.assert_called_once()
        mock_upload_directory_data.assert_called_once()
        mock_register_asset.assert_called_once()
        self.assertEqual(
            ["INFO:root:Job finished in 0:16:48."], captured.output
        )


if __name__ == "__main__":
    unittest.main()
