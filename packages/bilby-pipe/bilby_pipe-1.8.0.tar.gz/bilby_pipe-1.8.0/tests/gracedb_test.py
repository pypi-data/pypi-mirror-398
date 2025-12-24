import glob
import json
import os
import shutil
import tempfile
import unittest
from itertools import product

import numpy as np
from parameterized import parameterized

from bilby.core.prior import DeltaFunction
from bilby.gw.prior import BBHPriorDict
from bilby_pipe import gracedb
from bilby_pipe.bilbyargparser import BilbyConfigFileParser
from bilby_pipe.utils import BilbyPipeError


class TestGraceDB(unittest.TestCase):
    def setUp(self):
        self.directory = os.path.abspath(os.path.dirname(__file__))
        self.outdir = "outdir"
        self.example_gracedb_uid = "G298936"
        self.example_gracedb_uid_outdir = f"outdir_{self.example_gracedb_uid}"
        self.cert_dummy_path = os.path.join(self.directory, "temp/certdir/")
        self.example_json_file = f"examples/gracedb/{self.example_gracedb_uid}.json"
        self.args = ["--json", self.example_json_file, "--channel-dict", "gwosc"]
        self.tearDown()  # make sure that temp files deleted from previous attempts
        os.makedirs(self.cert_dummy_path)
        os.makedirs(self.outdir)

    def tearDown(self):
        if os.path.isdir(self.outdir):
            shutil.rmtree(self.outdir)
        if os.path.isdir(self.example_gracedb_uid_outdir):
            shutil.rmtree(self.example_gracedb_uid_outdir)
        if os.path.isdir(self.cert_dummy_path):
            shutil.rmtree(self.cert_dummy_path)

    # def test_read_from_gracedb(self):
    #    uid = "G298936"
    #    gracedb_url = 'https://gracedb.ligo.org/api/'
    #    gracedb.read_from_gracedb(uid, gracedb_url, self.outdir)

    def test_read_from_json(self):
        out = gracedb.read_from_json(self.example_json_file)
        self.assertIsInstance(out, dict)

    def test_read_from_json_not_a_file(self):
        with self.assertRaises(FileNotFoundError):
            gracedb.read_from_json("not-a-file")

    # def test_create_config_file(self):
    #     example_json_data = "examples/gracedb/{}.json".format(self.example_gracedb_uid)
    #     candidate = gracedb.read_from_json(example_json_data)
    #     # Create ini file
    #     filename = gracedb.create_config_file(
    #         candidate, self.example_gracedb_uid, self.outdir
    #     )
    #     # Check it exists
    #     self.assertTrue(os.path.isfile(filename))
    #     # Read in using bilby_pipe
    #     parser = main.create_parser(top_level=True)
    #     args = parser.parse_args([filename])
    #     # Check it is set up correctly
    #     self.assertEqual(args.label, self.example_gracedb_uid)
    #     self.assertEqual(args.prior_file, "4s")

    # def test_create_config_file_roq(self):
    #     gracedb_uid = "G298936"
    #     example_json_data = "examples/gracedb/{}.json".format(gracedb_uid)
    #     candidate = gracedb.read_from_json(example_json_data)
    #     candidate["extra_attributes"]["CoincInspiral"]["mchirp"] = 2.1
    #     # Create ini file
    #     filename = gracedb.create_config_file(candidate, gracedb_uid, self.outdir)
    #     # Check it exists
    #     self.assertTrue(os.path.isfile(filename))
    #     # Read in using bilby_pipe
    #     parser = main.create_parser(top_level=True)
    #     args = parser.parse_args([filename])
    #     # Check it is set up correctly
    #     self.assertEqual(args.label, gracedb_uid)
    #     self.assertEqual(args.prior_file, "128s")
    #     self.assertEqual(args.likelihood_type, "ROQGravitationalWaveTransient")
    #     self.assertEqual(args.roq_folder, "/home/cbc/ROQ_data/IMRPhenomPv2/128s")

    def test_create_config_file_no_chirp_mass(self):
        gracedb_uid = "G298936"
        candidate = gracedb.read_from_json(self.example_json_file)
        channel_dict = dict(
            H1="GDS-CALIB_STRAIN_CLEAN",
            L1="GDS-CALIB_STRAIN_CLEAN",
            V1="Hrec_hoft_16384Hz",
        )
        webdir = "."
        sampler_kwargs = "{'a': 1, 'b': 2}"
        del candidate["extra_attributes"]["CoincInspiral"]["mchirp"]
        with self.assertRaises(BilbyPipeError):
            gracedb.create_config_file(
                candidate,
                gracedb_uid,
                channel_dict,
                self.outdir,
                sampler_kwargs,
                webdir,
            )

    def test_parse_args(self):
        parser = gracedb.create_parser()
        args = parser.parse_args(self.args)
        self.assertEqual(args.gracedb, None)
        self.assertEqual(args.json, self.example_json_file)
        self.assertEqual(args.output, "full")
        self.assertEqual(args.outdir, None)
        self.assertEqual(args.gracedb_url, "https://gracedb.ligo.org/api/")

    def test_main(self):
        parser = gracedb.create_parser()
        args = parser.parse_args(self.args + ["--cbc-likelihood-mode", "test"])
        gracedb.main(args)
        files = glob.glob(self.example_gracedb_uid_outdir + "/submit/*")
        print(files)
        # Check this creates all relevant jobs
        self.assertEqual(len(files), 9)

    @parameterized.expand([(True,), (False,)])
    def test_phase_marginalization(self, phase_marginalization):
        gracedb_uid = "G298936"
        likelihood_settings = {
            "likelihood_args": {
                "minimum_frequency": 20,
                "maximum_frequency": 1024,
                "duration": 4,
                "phase_marginalization": phase_marginalization,
            },
            "likelihood_parameter_bounds": {
                "chirp_mass_min": 30,
                "chirp_mass_max": 40,
                "mass_ratio_min": 0.125,
                "a_1_max": 0.99,
                "a_2_max": 0.99,
                "spin_template": "aligned",
            },
        }
        cbc_likelihood_mode = os.path.join(self.outdir, "test.json")
        with open(cbc_likelihood_mode, "w") as ff:
            json.dump(likelihood_settings, ff, indent=2)
        parser = gracedb.create_parser()
        args = parser.parse_args(
            self.args + ["--cbc-likelihood-mode", cbc_likelihood_mode]
        )
        gracedb.main(args)
        (config,) = glob.glob(
            os.path.join(
                self.example_gracedb_uid_outdir, f"{gracedb_uid}_config_complete.ini"
            )
        )
        config_parser = BilbyConfigFileParser()
        with open(config, "r") as f:
            config, _, _, _ = config_parser.parse(f)
        self.assertEqual(config["phase-marginalization"], str(phase_marginalization))
        if phase_marginalization:
            suffix = "_distance_marginalization_lookup_phase.npz"
        else:
            suffix = "_distance_marginalization_lookup.npz"
        self.assertTrue(
            config["distance-marginalization-lookup-table"].endswith(suffix)
        )


class TestPriorSettings(unittest.TestCase):
    @parameterized.expand([(1,), (3,), (5,), (10,)])
    def test_trigger_chirp_mass(self, trigger_chirp_mass):
        with tempfile.TemporaryDirectory() as outdir:
            gracedb.generate_cbc_prior_from_template(
                chirp_mass=trigger_chirp_mass,
                likelihood_parameter_bounds=dict(
                    chirp_mass_min=0.1,
                    chirp_mass_max=10,
                    mass_ratio_min=0.125,
                    comp_min=0.1,
                    a_1_max=0.99,
                    a_2_max=0.99,
                    spin_template="precessing",
                ),
                outdir=outdir,
            )
            priors = BBHPriorDict(f"{outdir}/online.prior")

        if trigger_chirp_mass < 2:
            self.assertEqual(priors["chirp_mass"].minimum, trigger_chirp_mass - 0.01)
            self.assertEqual(priors["chirp_mass"].maximum, trigger_chirp_mass + 0.01)
        elif trigger_chirp_mass < 4:
            self.assertEqual(priors["chirp_mass"].minimum, trigger_chirp_mass - 0.1)
            self.assertEqual(priors["chirp_mass"].maximum, trigger_chirp_mass + 0.1)
        elif trigger_chirp_mass < 8:
            self.assertEqual(priors["chirp_mass"].minimum, trigger_chirp_mass * 0.9)
            self.assertEqual(priors["chirp_mass"].maximum, trigger_chirp_mass * 1.1)
        else:
            self.assertEqual(priors["chirp_mass"].minimum, 0.1)
            self.assertEqual(priors["chirp_mass"].maximum, 10)
        self.assertEqual(priors["mass_ratio"].minimum, 0.125)
        self.assertEqual(priors["mass_2"].minimum, 0.1)
        self.assertEqual(priors["a_1"].maximum, 0.99)
        self.assertEqual(priors["a_2"].maximum, 0.99)

    def test_no_comp_min(self):
        with tempfile.TemporaryDirectory() as outdir:
            gracedb.generate_cbc_prior_from_template(
                chirp_mass=1,
                likelihood_parameter_bounds=dict(
                    chirp_mass_min=0.1,
                    chirp_mass_max=10,
                    mass_ratio_min=0.125,
                    a_1_max=0.99,
                    a_2_max=0.99,
                    spin_template="precessing",
                ),
                outdir=outdir,
            )
            priors = BBHPriorDict(f"{outdir}/online.prior")
        self.assertTrue("mass_1" not in priors)
        self.assertTrue("mass_2" not in priors)

    @parameterized.expand([("aligned",), ("precessing",)])
    def test_spin_template(self, spin_template):
        with tempfile.TemporaryDirectory() as outdir:
            gracedb.generate_cbc_prior_from_template(
                chirp_mass=1,
                likelihood_parameter_bounds=dict(
                    chirp_mass_min=0.1,
                    chirp_mass_max=10,
                    mass_ratio_min=0.125,
                    comp_min=0.1,
                    a_1_max=0.99,
                    a_2_max=0.99,
                    spin_template=spin_template,
                ),
                outdir=outdir,
            )
            priors = BBHPriorDict(f"{outdir}/online.prior")

        if spin_template == "aligned":
            self.assertTrue("chi_1" in priors)
            self.assertTrue("chi_2" in priors)
        else:
            self.assertTrue("a_1" in priors)
            self.assertTrue("a_2" in priors)
            self.assertTrue("tilt_1" in priors)
            self.assertTrue("tilt_2" in priors)
            self.assertTrue("phi_12" in priors)
            self.assertTrue("phi_jl" in priors)

    def test_unknown_spin_template(self):
        with tempfile.TemporaryDirectory() as outdir:
            with self.assertRaises(ValueError):
                gracedb.generate_cbc_prior_from_template(
                    chirp_mass=1,
                    likelihood_parameter_bounds=dict(
                        chirp_mass_min=0.1,
                        chirp_mass_max=10,
                        mass_ratio_min=0.125,
                        comp_min=0.1,
                        a_1_max=0.99,
                        a_2_max=0.99,
                        spin_template="unknown",
                    ),
                    outdir=outdir,
                )

    @parameterized.expand(product([True, False], [True, False]))
    def test_tides(self, tides_1, tides_2):
        likelihood_parameter_bounds = dict(
            chirp_mass_min=0.1,
            chirp_mass_max=10,
            mass_ratio_min=0.125,
            comp_min=0.1,
            a_1_max=0.99,
            a_2_max=0.99,
            spin_template="precessing",
        )
        if tides_1:
            likelihood_parameter_bounds["lambda_1_max"] = 5000
        if tides_2:
            likelihood_parameter_bounds["lambda_2_max"] = 5000
        with tempfile.TemporaryDirectory() as outdir:
            gracedb.generate_cbc_prior_from_template(
                chirp_mass=1,
                likelihood_parameter_bounds=likelihood_parameter_bounds,
                outdir=outdir,
            )
            priors = BBHPriorDict(f"{outdir}/online.prior")

        if tides_1:
            self.assertTrue("lambda_1" in priors)
        else:
            self.assertTrue("lambda_1" not in priors)
        if tides_2:
            self.assertTrue("lambda_2" in priors)
        else:
            self.assertTrue("lambda_2" not in priors)

    @parameterized.expand([True, False])
    def test_psi(self, half):
        likelihood_parameter_bounds = dict(
            chirp_mass_min=0.1,
            chirp_mass_max=10,
            mass_ratio_min=0.125,
            comp_min=0.1,
            a_1_max=0.99,
            a_2_max=0.99,
            spin_template="precessing",
        )
        if half:
            likelihood_parameter_bounds["psi_max"] = np.pi / 2
        with tempfile.TemporaryDirectory() as outdir:
            gracedb.generate_cbc_prior_from_template(
                chirp_mass=1,
                likelihood_parameter_bounds=likelihood_parameter_bounds,
                outdir=outdir,
            )
            priors = BBHPriorDict(f"{outdir}/online.prior")
        if half:
            self.assertEqual(priors["psi"].maximum, np.pi / 2)
        else:
            self.assertEqual(priors["psi"].maximum, np.pi)

    def test_fast_settings(self):
        with tempfile.TemporaryDirectory() as outdir:
            gracedb.generate_cbc_prior_from_template(
                chirp_mass=1,
                likelihood_parameter_bounds=dict(
                    chirp_mass_min=0.1,
                    chirp_mass_max=10,
                    mass_ratio_min=0.125,
                    comp_min=0.1,
                    a_1_max=0.99,
                    a_2_max=0.99,
                    spin_template="precessing",
                ),
                outdir=outdir,
                fast_test=True,
            )
            priors = BBHPriorDict(f"{outdir}/online.prior")

        for key in ["a_1", "a_2", "tilt_1", "tilt_2", "phi_jl", "phi_12", "psi"]:
            self.assertTrue(isinstance(priors[key], DeltaFunction))


class TestLikelihoodSettings(unittest.TestCase):
    @parameterized.expand(product([1.5, 2.5], [0.2, 0.7]))
    def test_from_json(self, chirp_mass, mass_ratio):
        trigger_values = {"chirp_mass": chirp_mass, "mass_ratio": mass_ratio}
        settings = {
            "likelihood_args": {
                "likelihood_type": "ROQGravitationalWaveTransient",
                "waveform_approximant": "IMRPhenomPv2",
                "minimum_frequency": 20,
                "maximum_frequency": 2048,
            },
        }
        settings["trigger_dependent"] = {
            "range": {
                "chirp_mass": [[1, 2], [1, 2], [2, 3], [2, 3]],
                "mass_ratio": [[0.5, 1], [0.1, 0.5], [0.5, 1], [0.1, 0.5]],
            },
            "likelihood_args": [
                {"roq_folder": "lowmass_lowQ", "duration": 256},
                {"roq_folder": "lowmass_highQ", "duration": 256},
                {"roq_folder": "highmass_lowQ", "duration": 128},
                {"roq_folder": "highmass_highQ", "duration": 128},
            ],
            "likelihood_parameter_bounds": [
                {"chirp_mass_min": 1, "chirp_mass_max": 2, "mass_ratio_min": 0.5},
                {"chirp_mass_min": 1, "chirp_mass_max": 2, "mass_ratio_min": 0.1},
                {"chirp_mass_min": 2, "chirp_mass_max": 3, "mass_ratio_min": 0.5},
                {"chirp_mass_min": 2, "chirp_mass_max": 3, "mass_ratio_min": 0.1},
            ],
        }

        with tempfile.TemporaryDirectory() as d:
            filename = os.path.join(d, "test_likelihood.json")
            with open(filename, "w") as ff:
                json.dump(settings, ff, indent=2)
            (
                likelihood_args,
                likelihood_parameter_bounds,
                minimum_frequency,
                maximum_frequency,
                duration,
            ) = gracedb._get_cbc_likelihood_args(filename, trigger_values)

        self.assertEqual(
            likelihood_args["likelihood_type"], "ROQGravitationalWaveTransient"
        )
        self.assertEqual(likelihood_args["waveform_approximant"], "IMRPhenomPv2")
        self.assertEqual(minimum_frequency, 20)
        self.assertEqual(maximum_frequency, 2048)
        if chirp_mass < 2 and mass_ratio > 0.5:
            self.assertEqual(likelihood_args["roq_folder"], "lowmass_lowQ")
            self.assertEqual(likelihood_parameter_bounds["chirp_mass_min"], 1)
            self.assertEqual(likelihood_parameter_bounds["chirp_mass_max"], 2)
            self.assertEqual(likelihood_parameter_bounds["mass_ratio_min"], 0.5)
            self.assertEqual(duration, 256)
        elif chirp_mass < 2 and mass_ratio < 0.5:
            self.assertEqual(likelihood_args["roq_folder"], "lowmass_highQ")
            self.assertEqual(likelihood_parameter_bounds["chirp_mass_min"], 1)
            self.assertEqual(likelihood_parameter_bounds["chirp_mass_max"], 2)
            self.assertEqual(likelihood_parameter_bounds["mass_ratio_min"], 0.1)
            self.assertEqual(duration, 256)
        elif chirp_mass > 2 and mass_ratio > 0.5:
            self.assertEqual(likelihood_args["roq_folder"], "highmass_lowQ")
            self.assertEqual(likelihood_parameter_bounds["chirp_mass_min"], 2)
            self.assertEqual(likelihood_parameter_bounds["chirp_mass_max"], 3)
            self.assertEqual(likelihood_parameter_bounds["mass_ratio_min"], 0.5)
            self.assertEqual(duration, 128)
        elif chirp_mass > 2 and mass_ratio < 0.5:
            self.assertEqual(likelihood_args["roq_folder"], "highmass_highQ")
            self.assertEqual(likelihood_parameter_bounds["chirp_mass_min"], 2)
            self.assertEqual(likelihood_parameter_bounds["chirp_mass_max"], 3)
            self.assertEqual(likelihood_parameter_bounds["mass_ratio_min"], 0.1)
            self.assertEqual(duration, 128)
        else:
            raise

    def assertEqualParameterBounds(self, x, y):
        keys_x = list(x.keys())
        keys_y = list(y.keys())
        self.assertEqual(set(keys_x), set(keys_y))
        self.assertEqual(x["spin_template"], y["spin_template"])
        keys_x.remove("spin_template")
        np.testing.assert_array_almost_equal(
            [x[k] for k in keys_x], [y[k] for k in keys_x]
        )

    @parameterized.expand([50, 20, 10, 7, 5, 3, 2, 1.2, 0.7])
    def test_phenompv2_bbh_roq(self, chirp_mass):
        (
            likelihood_args,
            likelihood_parameter_bounds,
            minimum_frequency,
            maximum_frequency,
            duration,
        ) = gracedb._choose_phenompv2_bbh_roq(chirp_mass, ignore_no_params=True)

        self.assertEqual(likelihood_args["waveform_approximant"], "IMRPhenomPv2")

        if chirp_mass > 35:
            self.assertEqual(
                likelihood_args["likelihood_type"], "GravitationalWaveTransient"
            )
        else:
            self.assertEqual(
                likelihood_args["likelihood_type"], "ROQGravitationalWaveTransient"
            )

        if chirp_mass <= 0.9:
            self.assertEqual(likelihood_args["roq_scale_factor"], 2)
        elif chirp_mass <= 1.43:
            self.assertEqual(likelihood_args["roq_scale_factor"], 1.6)
        elif chirp_mass <= 35:
            self.assertEqual(likelihood_args["roq_scale_factor"], 1)
        else:
            self.assertTrue("roq_scale_factor" not in likelihood_args)

    @parameterized.expand(
        product(
            [
                "lowspin_phenomd_narrowmc_roq",
                "lowspin_phenomd_broadmc_roq",
                "phenompv2_bns_roq",
                "phenompv2nrtidalv2_roq",
            ],
            [3, 2, 1.2, 0.7],
        )
    )
    def test_bns_roq(self, mode, chirp_mass):
        trigger_values = {"chirp_mass": chirp_mass}
        (
            likelihood_args,
            likelihood_parameter_bounds,
            minimum_frequency,
            maximum_frequency,
            duration,
        ) = gracedb._get_cbc_likelihood_args(mode, trigger_values)

        args_answer = {
            "enforce_signal_duration": False,
            "likelihood_type": "ROQGravitationalWaveTransient",
            "roq_scale_factor": 1,
        }
        bounds_answer = {
            "mass_ratio_min": 0.125,
            "psi_max": np.pi / 2,
        }
        minimum_frequency_answer = 20
        maximum_frequency_answer = 4096
        if mode == "lowspin_phenomd_narrowmc_roq":
            args_answer["waveform_approximant"] = "IMRPhenomD"
            bounds_answer["a_1_max"] = 0.05
            bounds_answer["a_2_max"] = 0.05
            bounds_answer["spin_template"] = "aligned"
            roq_dir = "/home/roq/IMRPhenomD/lowspin_narrowmc_bns"
        elif mode == "lowspin_phenomd_broadmc_roq":
            args_answer["waveform_approximant"] = "IMRPhenomD"
            bounds_answer["a_1_max"] = 0.05
            bounds_answer["a_2_max"] = 0.05
            bounds_answer["spin_template"] = "aligned"
            roq_dir = "/home/roq/IMRPhenomD/lowspin_broadmc_bns"
        elif mode == "phenompv2_bns_roq":
            args_answer["waveform_approximant"] = "IMRPhenomPv2"
            bounds_answer["a_1_max"] = 0.99
            bounds_answer["a_2_max"] = 0.99
            bounds_answer["spin_template"] = "precessing"
            roq_dir = "/home/roq/IMRPhenomPv2/bns"
        elif mode == "phenompv2nrtidalv2_roq":
            args_answer["waveform_approximant"] = "IMRPhenomPv2_NRTidalv2"
            bounds_answer["a_1_max"] = 0.4
            bounds_answer["a_2_max"] = 0.4
            bounds_answer["spin_template"] = "precessing"
            bounds_answer["lambda_1_max"] = 5000
            bounds_answer["lambda_2_max"] = 5000
            roq_dir = "/home/roq/IMRPhenomPv2_NRTidalv2/bns"

        if 4.0 > chirp_mass > 2.31:
            basis = os.path.join(roq_dir, "basis_64s.hdf5")
            bounds_answer["chirp_mass_min"] = 2.1
            bounds_answer["chirp_mass_max"] = 4.0
            maximum_frequency_answer = 2048
            duration_answer = 64
        elif chirp_mass > 1.54:
            basis = os.path.join(roq_dir, "basis_128s.hdf5")
            bounds_answer["chirp_mass_min"] = 1.4
            bounds_answer["chirp_mass_max"] = 2.6
            maximum_frequency_answer = 4096
            duration_answer = 128
        elif chirp_mass > 1.012:
            basis = os.path.join(roq_dir, "basis_256s.hdf5")
            bounds_answer["chirp_mass_min"] = 0.92
            bounds_answer["chirp_mass_max"] = 1.7
            maximum_frequency_answer = 4096
            duration_answer = 256
        elif chirp_mass > 0.6:
            basis = os.path.join(roq_dir, "basis_512s.hdf5")
            bounds_answer["chirp_mass_min"] = 0.6
            bounds_answer["chirp_mass_max"] = 1.1
            maximum_frequency_answer = 4096
            duration_answer = 512
        args_answer["roq_linear_matrix"] = basis
        args_answer["roq_quadratic_matrix"] = basis

        self.assertEqual(likelihood_args, args_answer)
        self.assertEqualParameterBounds(likelihood_parameter_bounds, bounds_answer)
        self.assertEqual(minimum_frequency, minimum_frequency_answer)
        self.assertEqual(maximum_frequency, maximum_frequency_answer)
        self.assertEqual(duration, duration_answer)

    @parameterized.expand([15, 7, 4.5, 3, 2])
    def test_low_q_phenompv2_roq(self, chirp_mass):
        (
            likelihood_args,
            likelihood_parameter_bounds,
            minimum_frequency,
            maximum_frequency,
            duration,
        ) = gracedb._get_cbc_likelihood_args(
            "low_q_phenompv2_roq", {"chirp_mass": chirp_mass}
        )

        self.assertEqual(likelihood_args["waveform_approximant"], "IMRPhenomPv2")

        if 21.0 > chirp_mass > 9.57:
            duration_ans = 8
        elif chirp_mass > 5.72:
            duration_ans = 16
        elif chirp_mass > 3.63:
            duration_ans = 32
        elif chirp_mass > 2.31:
            duration_ans = 64
        elif chirp_mass > 1.4:
            duration_ans = 128
        self.assertEqual(duration, duration_ans)
        self.assertEqual(
            os.path.basename(likelihood_args["roq_linear_matrix"]),
            f"basis_{duration_ans}s.hdf5",
        )
        self.assertEqual(
            os.path.basename(likelihood_args["roq_quadratic_matrix"]),
            f"basis_{duration_ans}s.hdf5",
        )

    @parameterized.expand([100, 35, 20, 13])
    def test_xphm_roq(self, chirp_mass):
        (
            likelihood_args,
            likelihood_parameter_bounds,
            minimum_frequency,
            maximum_frequency,
            duration,
        ) = gracedb._get_cbc_likelihood_args(
            "phenomxphm_roq", {"chirp_mass": chirp_mass}
        )

        self.assertEqual(likelihood_args["waveform_approximant"], "IMRPhenomXPHM")

        if chirp_mass > 25:
            self.assertEqual(duration, 8)
        else:
            if chirp_mass > 16:
                duration_ans = 16
            elif chirp_mass > 10.03:
                duration_ans = 32
            self.assertEqual(
                os.path.basename(likelihood_args["roq_linear_matrix"]),
                f"basis_{duration_ans}s.hdf5",
            )
            self.assertEqual(
                os.path.basename(likelihood_args["roq_quadratic_matrix"]),
                f"basis_{duration_ans}s.hdf5",
            )
            self.assertEqual(duration, duration_ans)


if __name__ == "__main__":
    unittest.main()
