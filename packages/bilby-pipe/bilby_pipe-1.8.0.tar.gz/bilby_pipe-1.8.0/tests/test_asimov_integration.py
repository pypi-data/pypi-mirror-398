"""Tests for the Bilby interface."""

import contextlib
import io
import os
import shutil
import unittest

from asimov.cli import project
from asimov.cli.application import apply_page
from asimov.ledger import YAMLLedger
from click.testing import CliRunner


class BilbyTests(unittest.TestCase):
    """Test bilby interface"""

    @classmethod
    def setUpClass(cls):
        cls.cwd = os.getcwd()

    def setUp(self):
        os.makedirs(f"{self.cwd}/tests/tmp/project")
        os.chdir(f"{self.cwd}/tests/tmp/project")
        runner = CliRunner()
        result = runner.invoke(
            project.init, ["Test Project", "--root", f"{self.cwd}/tests/tmp/project"]
        )
        assert result.exit_code == 0
        assert result.output == "● New project created successfully!\n"
        self.ledger = YAMLLedger(".asimov/ledger.yml")
        apply_page(
            file=f"{self.cwd}/tests/ASIMOV/GW150914.yaml",
            event=None,
            ledger=self.ledger,
        )

        apply_page(
            file=f"{self.cwd}/tests/ASIMOV/bilby_defaults.yaml",
            event=None,
            ledger=self.ledger,
        )

        apply_page(
            file=f"{self.cwd}/tests/ASIMOV/bilby_priors.yaml",
            event=None,
            ledger=self.ledger,
        )

        apply_page(
            file=f"{self.cwd}/tests/ASIMOV/bilby_analysis.yaml",
            event="GW150914",
            ledger=self.ledger,
        )

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(f"{self.cwd}/tests/tmp/project/")

    def test_build_api(self):
        """Check that a bilby config file can be built."""

        prod = self.ledger.get_event("GW150914")[0].productions[1]

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            prod.pipeline.build_dag(dryrun=True)
            print(f.getvalue())
            self.assertTrue("bilby_pipe" in f.getvalue())

    def test_build_config(self):
        """
        Test the built config file matches a preprepared reference, the reference file
        may have to be updated whenever the implementation or settings changes
        """
        prod = self.ledger.get_event("GW150914")[0].productions[1]

        config_file = f"{self.cwd}/tests/tmp/project/Prod1.ini"
        reference_file = f"{self.cwd}/tests/ASIMOV/expected.ini"
        prod.make_config(config_file)
        with open(config_file, "r") as f1, open(reference_file, "r") as f2:
            config = {ll.strip("\n") for ll in f1.readlines()}
            expected = {ll.strip("\n") for ll in f2.readlines()}
        assert len(expected.difference(config)) == 0
