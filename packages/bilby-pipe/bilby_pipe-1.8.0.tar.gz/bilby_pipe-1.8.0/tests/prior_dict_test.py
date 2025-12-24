import os
import shutil
import unittest

import bilby_pipe


class TestPriorDict(unittest.TestCase):
    def setUp(self):
        self.directory = os.path.abspath(os.path.dirname(__file__))
        self.outdir = "outdir"
        self.parser = bilby_pipe.main.create_parser()
        self.inifile = "tests/test_prior_dict.ini"

    def tearDown(self):
        if os.path.exists(self.outdir):
            shutil.rmtree(self.outdir)

    def test_read_in(self):
        args_list = [self.inifile, "--outdir", self.outdir]

        args, unknown_args = self.parser.parse_known_args(args_list)
        bilby_pipe.main.MainInput(args, unknown_args)


if __name__ == "__main__":
    unittest.main()
