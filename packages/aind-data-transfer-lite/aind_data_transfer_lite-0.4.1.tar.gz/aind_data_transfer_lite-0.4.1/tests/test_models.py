"""Unit tests for models module."""

import os
import unittest
from pathlib import Path

from aind_data_transfer_lite.models import JobSettings

RESOURCES_DIR = Path(os.path.dirname(os.path.realpath(__file__))) / "resources"


class TestJobSettings(unittest.TestCase):
    """Tests for JobSettings class"""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up common JobSettings"""
        cls.job_settings = JobSettings(
            metadata_directory=RESOURCES_DIR / "metadata_dir",
            modality_directories={
                "ecephys": RESOURCES_DIR / "ecephys_data",
                "behavior": RESOURCES_DIR / "behavior_data",
            },
            dry_run=True,
        )

    def test_modality_directory_invalid_key(self):
        """Tests validate_modality_keys when an invalid modality is set."""
        with self.assertRaises(KeyError) as e:
            JobSettings(
                modality_directories={"NONESUCH_MODALITY": Path(".")},
            )
        self.assertIn(
            "['NONESUCH_MODALITY'] are not from set of", str(e.exception)
        )


if __name__ == "__main__":
    unittest.main()
