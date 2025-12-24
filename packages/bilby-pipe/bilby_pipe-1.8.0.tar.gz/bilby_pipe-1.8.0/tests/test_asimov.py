"""
Tests for Bilby-Asimov interfaces.
"""

import contextlib
import io
import json
import os
import pathlib
import shutil
import unittest
from unittest.mock import MagicMock, patch

from asimov.cli import project
from asimov.cli.application import apply_page
from asimov.ledger import YAMLLedger
from click.testing import CliRunner

import bilby_pipe.asimov.online


class BilbyOnlineTests(unittest.TestCase):
    """
    Test BilbyOnline interface
    """

    @classmethod
    def setUpClass(cls):
        cls.cwd = pathlib.Path.cwd()

    def setUp(self):
        self.test_dir = self.cwd.joinpath("tests", "tmp", "project")
        self.test_dir.mkdir(parents=True)
        os.chdir(str(self.test_dir))

        runner = CliRunner()
        result = runner.invoke(
            project.init, ["Test Project", "--root", f"{self.test_dir}"]
        )

        assert result.exit_code == 0
        assert result.output == "● New project created successfully!\n"

        self.ledger = YAMLLedger(".asimov/ledger.yml")

    def tearDown(self):
        os.chdir(str(self.cwd))
        shutil.rmtree(self.test_dir)

    def mock_json(self) -> dict:
        """
        Loads in the static mock json data for testing
        """
        json_fp = self.cwd.joinpath("examples", "gracedb", "G298936.json")
        if not json_fp.is_file():
            raise FileNotFoundError(
                f"{json_fp} not a valid file. Cannot complete testing"
            )
        with open(json_fp, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        return json_data

    def test_build_api(self):
        """
        Check that build_dag will successfully produce a command to be run to
        generate the DAG.
        """

        apply_page(
            file=f"{self.cwd.joinpath('tests', 'ASIMOV', 'online_event.yaml')}",
            event=None,
            ledger=self.ledger,
        )

        apply_page(
            file=f"{self.cwd.joinpath('tests','ASIMOV','online_defaults.yaml')}",
            event=None,
            ledger=self.ledger,
        )

        apply_page(
            file=f"{self.cwd.joinpath('tests','ASIMOV','online_analysis.yaml')}",
            event="G298936",
            ledger=self.ledger,
        )

        mock_gracedb_result = self.mock_json()
        mock_psd_result = str(self.cwd.joinpath("tests", "ASIMOV", "psd.xml.gz"))

        test_object = self.ledger.get_event("G298936")[0].productions[0].pipeline

        with patch.object(
            bilby_pipe.asimov.online,
            "read_from_gracedb",
            MagicMock(return_value=mock_gracedb_result),
        ):
            with patch.object(
                test_object,
                "psd_file",
                return_value=mock_psd_result,
            ):
                f = io.StringIO()
                with contextlib.redirect_stdout(f):
                    test_object.build_dag(dryrun=True)
                    print(f)
                    self.assertTrue("online-test" in f.getvalue())
                print(f.getvalue())
