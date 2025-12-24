import os
import unittest
from shutil import copyfile, rmtree
from unittest.mock import MagicMock, PropertyMock, create_autospec, patch

import pandas as pd

import bilby
import bilby_pipe
from bilby_pipe.utils import BilbyPipeError, BilbyPipeInternalError


class TestInput(unittest.TestCase):
    def setUp(self):
        self.test_gps_file = "tests/gps_file.txt"
        self.test_injection_file_json = (
            "tests/lalinference_test_injection_standard.json"
        )
        self.test_injection_file_dat = "tests/lalinference_test_injection_standard.dat"
        self.test_outdir = "test_outdir"

    def tearDown(self):
        if os.path.exists(self.test_outdir):
            rmtree(self.test_outdir)
        # Reset bilby cosmology to unset state
        bilby.gw.cosmology.DEFAULT_COSMOLOGY = None
        bilby.gw.cosmology.COSMOLOGY = [None, str(None)]

    def test_idx(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.idx = 1
        self.assertEqual(inputs.idx, 1)

    def test_split_by_space(self):
        inputs = bilby_pipe.main.Input(None, None)
        out = inputs._split_string_by_space("H1 L1")
        self.assertEqual(out, ["H1", "L1"])

    def test_detectors(self):
        inputs = bilby_pipe.main.Input(None, None)
        with self.assertRaises(AttributeError):
            print(inputs.detectors)

    def test_set_detectors_list(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.detectors = ["H1"]
        self.assertEqual(inputs.detectors, ["H1"])

    def test_set_detectors_string(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.detectors = "H1 L1"
        self.assertEqual(inputs.detectors, ["H1", "L1"])

    def test_set_detectors_ordering(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.detectors = "L1 H1"
        self.assertEqual(inputs.detectors, ["H1", "L1"])

    def test_convert_string_to_list(self):
        for string in [
            "H1 L1",
            "[H1, L1]",
            "H1, L1",
            '["H1", "L1"]',
            "'H1' 'L1'",
            '"H1", "L1"',
        ]:
            self.assertEqual(
                bilby_pipe.main.Input._convert_string_to_list(string), ["H1", "L1"]
            )

    def test_gps_file_unset(self):
        inputs = bilby_pipe.main.Input(None, None)
        with self.assertRaises(AttributeError):
            self.assertEqual(inputs.gps_file, None)

    def test_gps_file_set_none(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.gps_file = None
        self.assertEqual(inputs.gps_file, None)

    def test_gps_file_set(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.gps_file = self.test_gps_file
        self.assertEqual(inputs.gps_file, os.path.relpath(self.test_gps_file))
        self.assertEqual(len(inputs.read_gps_file(inputs.gps_file)), 2)

    def test_gps_file_set_fail(self):
        inputs = bilby_pipe.main.Input(None, None)
        gps_file = "tests/nonexistant_file.txt"
        with self.assertRaises(FileNotFoundError):
            inputs.gps_file = gps_file

    def test_frequency_domain_source_model(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.frequency_domain_source_model = "lal_binary_black_hole"
        self.assertEqual(inputs.frequency_domain_source_model, "lal_binary_black_hole")

    def test_frequency_domain_source_model_to_bilby(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.frequency_domain_source_model = "lal_binary_black_hole"
        self.assertEqual(
            inputs.bilby_frequency_domain_source_model,
            bilby.gw.source.lal_binary_black_hole,
        )

    def test_frequency_domain_source_model_to_bilby_fail(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.frequency_domain_source_model = "not_a_source_model"
        with self.assertRaises(BilbyPipeError):
            print(inputs.bilby_frequency_domain_source_model)

    def test_minimum_frequency_int(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.detectors = "H1 L1"
        inputs.minimum_frequency = 10
        self.assertEqual(inputs.minimum_frequency, 10)
        self.assertEqual(inputs.minimum_frequency_dict, dict(H1=10, L1=10))

    def test_minimum_frequency_float(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.detectors = "H1 L1"
        inputs.minimum_frequency = 10.1
        self.assertEqual(inputs.minimum_frequency, 10.1)
        self.assertEqual(inputs.minimum_frequency_dict, dict(H1=10.1, L1=10.1))

    def test_minimum_frequency_int_dict(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.detectors = "H1 L1"
        inputs.minimum_frequency = "{H1: 10, L1: 20}"
        self.assertIsInstance(inputs.minimum_frequency, int)
        self.assertEqual(inputs.minimum_frequency, 10)
        self.assertEqual(inputs.minimum_frequency_dict, dict(H1=10, L1=20))

    def test_minimum_frequency_float_dict(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.detectors = "H1 L1"
        inputs.minimum_frequency = "{H1: 10.1, L1: 20.1}"
        self.assertIsInstance(inputs.minimum_frequency, float)
        self.assertEqual(inputs.minimum_frequency, 10.1)
        self.assertEqual(inputs.minimum_frequency_dict, dict(H1=10.1, L1=20.1))

    def test_maximum_frequency_int(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.detectors = "H1 L1"
        inputs.maximum_frequency = 10
        self.assertEqual(inputs.maximum_frequency, 10)
        self.assertEqual(inputs.maximum_frequency_dict, dict(H1=10, L1=10))

    def test_maximum_frequency_str(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.detectors = "H1 L1"
        inputs.maximum_frequency = "10"
        self.assertEqual(inputs.maximum_frequency, 10)
        self.assertEqual(inputs.maximum_frequency_dict, dict(H1=10, L1=10))

    def test_maximum_frequency_float(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.detectors = "H1 L1"
        inputs.maximum_frequency = 10.1
        self.assertEqual(inputs.maximum_frequency, 10.1)
        self.assertEqual(inputs.maximum_frequency_dict, dict(H1=10.1, L1=10.1))

    def test_maximum_frequency_int_dict(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.detectors = "H1 L1"
        inputs.maximum_frequency = "{H1: 100, L1: 200}"
        self.assertIsInstance(inputs.maximum_frequency, int)
        self.assertEqual(inputs.maximum_frequency, 200)
        self.assertEqual(inputs.maximum_frequency_dict, dict(H1=100, L1=200))

    def test_maximum_frequency_float_dict(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.detectors = "H1 L1"
        inputs.maximum_frequency = "{H1: 100.1, L1: 200.1}"
        self.assertIsInstance(inputs.maximum_frequency, float)
        self.assertEqual(inputs.maximum_frequency, 200.1)
        self.assertEqual(inputs.maximum_frequency_dict, dict(H1=100.1, L1=200.1))

    def test_default_webdir(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.outdir = self.test_outdir
        inputs.webdir = None
        self.assertEqual(inputs.webdir, f"{self.test_outdir}/results_page")

    def test_default_start_time(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.trigger_time = 2
        inputs.post_trigger_duration = 2
        inputs.duration = 4
        self.assertEqual(inputs.start_time, 0)

    def test_set_start_time(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.start_time = 2
        self.assertEqual(inputs.start_time, 2)

    def test_set_start_time_fail(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.trigger_time = 2
        inputs.duration = 4
        inputs.post_trigger_duration = 2
        with self.assertRaises(BilbyPipeError):
            inputs.start_time = 2

    def test_default_waveform_arguments(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.detectors = ["H1"]
        inputs.reference_frequency = 20
        inputs.minimum_frequency = 20
        inputs.maximum_frequency = 1024
        inputs.waveform_approximant = "IMRPhenomPv2"
        inputs.pn_spin_order = -1
        inputs.pn_tidal_order = -1
        inputs.pn_phase_order = -1
        inputs.pn_amplitude_order = 0
        inputs.mode_array = None
        inputs.waveform_arguments_dict = None
        inputs.catch_waveform_errors = False
        wfa = inputs.get_default_waveform_arguments()
        self.assertEqual(wfa["reference_frequency"], 20)
        self.assertEqual(wfa["minimum_frequency"], 20)
        self.assertEqual(wfa["maximum_frequency"], 1024)
        self.assertEqual(wfa["waveform_approximant"], "IMRPhenomPv2")
        self.assertEqual(wfa["pn_spin_order"], -1)
        self.assertEqual(wfa["pn_tidal_order"], -1)
        self.assertEqual(wfa["pn_phase_order"], -1)
        self.assertEqual(wfa["pn_amplitude_order"], 0)
        self.assertIsNone(wfa["mode_array"])
        self.assertFalse(wfa["catch_waveform_errors"])
        self.assertEqual(len(wfa), 10)

    def test_added_waveform_arguments(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.detectors = ["H1"]
        inputs.reference_frequency = 20
        inputs.minimum_frequency = 20
        inputs.maximum_frequency = 1024
        inputs.waveform_approximant = "IMRPhenomPv2"
        inputs.pn_spin_order = -1
        inputs.pn_tidal_order = -1
        inputs.pn_phase_order = -1
        inputs.pn_amplitude_order = 0
        inputs.mode_array = None
        inputs.waveform_arguments_dict = "{a: 10, b=test, c=[1, 2]}"
        inputs.catch_waveform_errors = False
        wfa = inputs.get_default_waveform_arguments()
        self.assertEqual(wfa["reference_frequency"], 20)
        self.assertEqual(wfa["minimum_frequency"], 20)
        self.assertEqual(wfa["maximum_frequency"], 1024)
        self.assertEqual(wfa["waveform_approximant"], "IMRPhenomPv2")
        self.assertEqual(wfa["pn_spin_order"], -1)
        self.assertEqual(wfa["pn_tidal_order"], -1)
        self.assertEqual(wfa["pn_phase_order"], -1)
        self.assertEqual(wfa["pn_amplitude_order"], 0)
        self.assertIsNone(wfa["mode_array"])
        self.assertFalse(wfa["catch_waveform_errors"])

        # Check of added arguments
        self.assertEqual(wfa["a"], 10)
        self.assertEqual(wfa["b"], "test")
        self.assertEqual(wfa["c"], ["1", "2"])

        self.assertEqual(len(wfa), 13)

    def test_mode_array(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.detectors = ["H1"]
        inputs.catch_waveform_errors = False
        inputs.reference_frequency = 20
        inputs.minimum_frequency = 20
        inputs.maximum_frequency = 1024
        inputs.waveform_approximant = "IMRPhenomPv2"
        inputs.pn_spin_order = -1
        inputs.pn_tidal_order = -1
        inputs.pn_phase_order = -1
        inputs.pn_amplitude_order = 0
        inputs.phenomXPHMTwistPhenomHM = None
        inputs.phenomXPFinalSpinMod = None
        inputs.phenomXPConvention = None
        inputs.phenomXPrecVersion = None
        inputs.phenomXPHMMband = None
        inputs.phenomXHMMband = None
        inputs.numerical_relativity_file = None
        inputs.waveform_arguments_dict = None

        inputs.mode_array = "[[2, 2], [2, -2]]"
        wfa = inputs.get_default_waveform_arguments()
        self.assertEqual(wfa["mode_array"], [[2, 2], [2, -2]])

        inputs.mode_array = "[2, 4]"
        wfa = inputs.get_default_waveform_arguments()
        self.assertEqual(wfa["mode_array"], [[2, 4]])

        with self.assertRaises(BilbyPipeError):
            inputs.mode_array = "[2]"
            wfa = inputs.get_default_waveform_arguments()
        with self.assertRaises(BilbyPipeError):
            inputs.mode_array = "[[[2, 3], [2, 3]]]"
            wfa = inputs.get_default_waveform_arguments()

    def test_injection_waveform_arguments(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.detectors = ["H1"]
        inputs.reference_frequency = 20
        inputs.minimum_frequency = 20
        inputs.maximum_frequency = 1024
        inputs.pn_spin_order = -1
        inputs.pn_tidal_order = -1
        inputs.pn_phase_order = -1
        inputs.pn_amplitude_order = 0
        inputs.numerical_relativity_file = None
        inputs.catch_waveform_errors = False
        inputs.mode_array = None
        inputs.waveform_arguments_dict = None
        inputs.injection_waveform_arguments = None

        # injection-waveform-approx not provided
        inputs.waveform_approximant = "IMRPhenomPv2"
        inputs.injection_waveform_approximant = None
        wfa = inputs.get_injection_waveform_arguments()
        self.assertEqual(wfa["reference_frequency"], 20)
        self.assertEqual(wfa["minimum_frequency"], 20)
        self.assertEqual(wfa["maximum_frequency"], 1024)
        self.assertEqual(wfa["waveform_approximant"], "IMRPhenomPv2")
        self.assertEqual(wfa["pn_spin_order"], -1)
        self.assertEqual(wfa["pn_tidal_order"], -1)
        self.assertEqual(wfa["pn_phase_order"], -1)
        self.assertEqual(wfa["pn_amplitude_order"], 0)
        self.assertIsNone(wfa["mode_array"])
        self.assertIsNone(wfa["numerical_relativity_file"])
        self.assertEqual(len(wfa), 11)

        # injection-waveform-approx provided
        inputs.waveform_approximant = "IMRPhenomPv2"
        inputs.injection_waveform_approximant = "SEOBNRv4"
        wfa = inputs.get_injection_waveform_arguments()
        self.assertEqual(wfa["reference_frequency"], 20)
        self.assertEqual(wfa["minimum_frequency"], 20)
        self.assertEqual(wfa["waveform_approximant"], "SEOBNRv4")
        self.assertEqual(len(wfa), 11)

    def test_numerical_relativity_file(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.detectors = ["H1"]
        inputs.reference_frequency = 20
        inputs.minimum_frequency = 20
        inputs.maximum_frequency = 1024
        inputs.pn_spin_order = -1
        inputs.pn_tidal_order = -1
        inputs.pn_phase_order = -1
        inputs.pn_amplitude_order = 0
        inputs.phenomXPHMTwistPhenomHM = None
        inputs.phenomXPFinalSpinMod = None
        inputs.phenomXPConvention = None
        inputs.phenomXPrecVersion = None
        inputs.phenomXPHMMband = None
        inputs.phenomXHMMband = None
        inputs.catch_waveform_errors = False
        inputs.mode_array = None
        inputs.waveform_approximant = "IMRPhenomPv2"
        inputs.injection_waveform_approximant = None
        inputs.injection_waveform_arguments = None
        inputs.waveform_arguments_dict = None

        # numerical-relativity-file given
        filename = "somedir/file.h5"
        inputs.numerical_relativity_file = filename
        wfa = inputs.get_injection_waveform_arguments()
        self.assertEqual(wfa["numerical_relativity_file"], filename)

    def test_injection_number(self):
        inputs = bilby_pipe.main.Input(None, None)

        inputs.injection_numbers = [0]
        self.assertEqual(inputs.injection_numbers, [0])

        inputs.injection_numbers = ["0"]
        self.assertEqual(inputs.injection_numbers, [0])

        inputs.injection_numbers = ["1", "2"]
        self.assertEqual(inputs.injection_numbers, [1, 2])

        with self.assertRaises(BilbyPipeError):
            inputs.injection_numbers = ["abba"]

        inputs.injection_numbers = ["1:3"]
        self.assertEqual(inputs.injection_numbers, [1, 2])

        inputs.injection_numbers = [0, "1", "1:3", "4:6"]
        self.assertEqual(inputs.injection_numbers, [0, 1, 2, 4, 5])

    def test_bilby_roq_frequency_domain_source_model(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.frequency_domain_source_model = "lal_binary_black_hole"
        self.assertEqual(
            inputs.bilby_roq_frequency_domain_source_model,
            bilby.gw.source.binary_black_hole_roq,
        )

        inputs.frequency_domain_source_model = "lal_binary_neutron_star"
        self.assertEqual(
            inputs.bilby_roq_frequency_domain_source_model,
            bilby.gw.source.binary_neutron_star_roq,
        )

        with self.assertRaises(BilbyPipeError):
            inputs.frequency_domain_source_model = "unknown"
            inputs.bilby_roq_frequency_domain_source_model

    def test_bilby_multiband_frequency_domain_source_model(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.frequency_domain_source_model = "lal_binary_black_hole"
        self.assertEqual(
            inputs.bilby_multiband_frequency_domain_source_model,
            bilby.gw.source.binary_black_hole_frequency_sequence,
        )

        inputs.frequency_domain_source_model = "lal_binary_neutron_star"
        self.assertEqual(
            inputs.bilby_multiband_frequency_domain_source_model,
            bilby.gw.source.binary_neutron_star_frequency_sequence,
        )

        with self.assertRaises(BilbyPipeError):
            inputs.frequency_domain_source_model = "unknown"
            inputs.bilby_multiband_frequency_domain_source_model

    def test_default_prior_files(self):
        inputs = bilby_pipe.main.Input(None, None)
        self.assertEqual(inputs.get_default_prior_files(), inputs.default_prior_files)
        self.assertTrue(isinstance(inputs.default_prior_files, dict))
        self.assertTrue("4s" in inputs.default_prior_files)
        self.assertTrue("128s" in inputs.default_prior_files)

    def test_default_prior_files_lookups(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.outdir = self.test_outdir
        for phase_marginalization in [True, False]:
            inputs.phase_marginalization = phase_marginalization
            for prior in inputs.default_prior_files:
                self.assertTrue(
                    os.path.isfile(inputs.get_distance_file_lookup_table(prior))
                )

    def test_prior_file_set_None(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.prior_file = None
        self.assertEqual(inputs.prior_file, None)

    def test_prior_file_set(self):
        inputs = bilby_pipe.main.Input(None, None)
        prior_name = "4s"
        inputs.prior_file = inputs.default_prior_files[prior_name]
        self.assertEqual(inputs.prior_file, inputs.default_prior_files[prior_name])

    def test_prior_file_set_local(self):
        inputs = bilby_pipe.main.Input(None, None)
        filename = inputs.default_prior_files["4s"]
        temp_filename = "4s-copy"
        copyfile(filename, temp_filename)
        inputs.prior_file = f"not-a-directory/{temp_filename}"
        self.assertEqual(inputs.prior_file, temp_filename)
        os.remove(temp_filename)

    def test_prior_file_set_from_default(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.outdir = self.test_outdir
        filename = inputs.default_prior_files["4s"]
        inputs.phase_marginalization = False
        inputs.prior_file = "4s"
        self.assertEqual(inputs.prior_file, filename)

    def test_prior_file_set_fail(self):
        inputs = bilby_pipe.main.Input(None, None)
        with self.assertRaises(FileNotFoundError):
            inputs.prior_file = "not-a-file"

    def test_prior_dict_set_None(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.prior_dict = None
        self.assertEqual(inputs.prior_dict, None)

    def test_prior_dict_set_from_dict(self):
        inputs = bilby_pipe.main.Input(None, None)
        val = dict(a=bilby.core.prior.Uniform(-1, 1, "a"), b=2)
        inputs.prior_dict = val
        self.assertTrue(isinstance(inputs.prior_dict, dict))
        self.assertEqual(inputs.prior_dict, val)

    def test_prior_dict_set_from_str(self):
        inputs = bilby_pipe.main.Input(None, None)
        val = "{a=bilby.core.prior.Uniform(-1, 1, 'a'), b=2}"
        out = {"a": "bilby.core.prior.Uniform(-1,1,'a')", "b": "2"}
        inputs.prior_dict = val
        self.assertTrue(isinstance(inputs.prior_dict, dict))
        self.assertEqual(inputs.prior_dict, out)

    def test_prior_dict_set_from_str_nested(self):
        inputs = bilby_pipe.main.Input(None, None)
        val = "{a=bilby.core.prior.Uniform(-1, 1, 'a', a_prior=test(-1, 1)), b=2}"
        out = {"a": "bilby.core.prior.Uniform(-1,1,'a',a_prior=test(-1,1))", "b": "2"}
        inputs.prior_dict = val
        self.assertTrue(isinstance(inputs.prior_dict, dict))
        self.assertEqual(inputs.prior_dict, out)

    def test_prior_dict_set_from_str_nested_and_eval(self):
        inputs = bilby_pipe.main.Input(None, None)
        val = (
            "{chi_1=bilby.gw.prior.AlignedSpin(name='chi_1',"
            "a_prior=bilby.core.prior.Uniform(minimum=0,maximum=0.8)), b=2}"
        )
        inputs.prior_dict = val

        inputs.default_prior = "BBHPriorDict"
        inputs.trigger_time = 0
        inputs.deltaT = 2
        inputs.time_reference = "geocent"
        inputs.enforce_signal_duration = False
        self.assertTrue(isinstance(inputs.priors["chi_1"], bilby.gw.prior.AlignedSpin))

    def test_injection_numbers_unset(self):
        inputs = bilby_pipe.main.Input(None, None)
        with self.assertRaises(BilbyPipeInternalError):
            inputs.injection_numbers

    def test_injection_numbers_None(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.injection_numbers = None
        self.assertEqual(inputs.injection_numbers, None)

    def test_injection_numbers_list(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.injection_numbers = [1, 2, 3]
        self.assertEqual(inputs.injection_numbers, [1, 2, 3])

    def test_injection_numbers_None_list(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.injection_numbers = [None]
        self.assertEqual(inputs.injection_numbers, None)

    def test_injection_numbers_None_str_list(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.injection_numbers = ["None"]
        self.assertEqual(inputs.injection_numbers, None)

    def test_injection_numbers_invalid_str(self):
        inputs = bilby_pipe.main.Input(None, None)
        with self.assertRaises(BilbyPipeError):
            inputs.injection_numbers = ["a"]

    def test_injection_df_nonpandas(self):
        inputs = bilby_pipe.main.Input(None, None)
        with self.assertRaises(BilbyPipeError):
            inputs.injection_df = dict(a=1)

    def test_injection_df(self):
        inputs = bilby_pipe.main.Input(None, None)
        df = pd.DataFrame(dict(a=[1, 2, 3]))
        inputs.injection_numbers = None
        inputs.injection_df = df
        self.assertTrue(all(inputs.injection_df == df))

    def test_injection_df_injection_numbers(self):
        inputs = bilby_pipe.main.Input(None, None)
        df = pd.DataFrame(dict(a=[1, 2, 3]))
        df_trunc = pd.DataFrame(dict(a=[1, 2]))
        inputs.injection_numbers = [0, 1]
        inputs.injection_df = df
        self.assertTrue(all(inputs.injection_df == df_trunc))

    def test_injection_df_injection_numbers_fail(self):
        inputs = bilby_pipe.main.Input(None, None)
        df = pd.DataFrame(dict(a=[1, 2, 3]))
        inputs.injection_numbers = [0, 1, 10]
        with self.assertRaises(BilbyPipeError):
            inputs.injection_df = df

    def test_injection_numbers_invalid_float(self):
        inputs = bilby_pipe.main.Input(None, None)
        with self.assertRaises(BilbyPipeError):
            inputs.injection_numbers = [1.5]
        with self.assertRaises(BilbyPipeError):
            inputs.injection_numbers = ["1.5"]

    def test_injection_file_set_none(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.injection_file = None
        self.assertTrue(inputs.injection_file is None)

    def test_injection_file_set_no_file(self):
        inputs = bilby_pipe.main.Input(None, None)
        with self.assertRaises(FileNotFoundError):
            inputs.injection_file = "this/is/not/a/file"

    def test_injection_file_json_set(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.injection_numbers = None
        inputs.injection_file = self.test_injection_file_json
        self.assertTrue(len(inputs.injection_df) == 1)
        self.assertTrue(inputs.injection_df["mass_1"].values[0] == 30)
        self.assertTrue(inputs.injection_file == self.test_injection_file_json)

    def test_injection_file_dat_set(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.injection_numbers = None
        inputs.injection_file = self.test_injection_file_dat
        self.assertTrue(len(inputs.injection_df) == 1)
        self.assertTrue(inputs.injection_df["mass_1"].values[0] == 30)
        self.assertTrue(inputs.injection_file == self.test_injection_file_dat)

    def test_injection_file_json_dat_equiv(self):
        inputs_dat = bilby_pipe.main.Input(None, None)
        inputs_dat.injection_numbers = None
        inputs_dat.injection_file = self.test_injection_file_dat

        inputs_json = bilby_pipe.main.Input(None, None)
        inputs_json.injection_numbers = None
        inputs_json.injection_file = self.test_injection_file_json

        self.assertTrue(all(inputs_dat.injection_df == inputs_json.injection_df))

    def test_injection_file_set_with_numbers(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.injection_numbers = [0]
        inputs.injection_file = self.test_injection_file_json
        self.assertTrue(len(inputs.injection_df) == 1)
        self.assertTrue(inputs.injection_df["mass_1"].values[0] == 30)

    def test_injection_file_set_with_invalid_numbers(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.injection_numbers = [1]
        with self.assertRaises(BilbyPipeError):
            inputs.injection_file = self.test_injection_file_json

    def test_injection_dict_set_None(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.injection_dict = None
        self.assertEqual(inputs.injection_dict, None)

    def test_injection_dict_set_dict(self):
        inputs = bilby_pipe.main.Input(None, None)
        dict_test = dict(a=1, b=2)
        inputs.injection_numbers = None
        inputs.injection_dict = dict_test
        self.assertEqual(dict_test, inputs.injection_dict)

    def test_injection_dict_set_str(self):
        inputs = bilby_pipe.main.Input(None, None)
        dict_str = "{a=1, b=2}"
        dict_test = dict(a=1, b=2)
        inputs.injection_numbers = None
        inputs.injection_dict = dict_str
        self.assertEqual(dict_test, inputs.injection_dict)

    def test_injection_dict_set_fail(self):
        inputs = bilby_pipe.main.Input(None, None)
        with self.assertRaises(BilbyPipeError):
            inputs.injection_dict = "fail"

    def test_injection_dict_set_fail_int(self):
        inputs = bilby_pipe.main.Input(None, None)
        with self.assertRaises(BilbyPipeError):
            inputs.injection_dict = 1

    def test_psd_setting_from_built_in(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.detectors = ["H1"]
        inputs.gaussian_noise = True
        inputs.psd_dict = "{H1:aLIGO_ZERO_DET_high_P_psd.txt}"
        inputs._validate_psd_dict()

    def test_custom_default_prior(self):
        inputs = bilby_pipe.main.Input(None, None)
        val = dict(lambda_1=bilby.core.prior.Uniform(0, 1000, "lambda_1"))
        inputs.default_prior = "bilby.gw.prior.BNSPriorDict"
        inputs.prior_dict = val
        inputs.time_reference = "geocent"
        inputs.trigger_time = 0
        inputs.deltaT = 2
        p1 = inputs._get_priors()
        p2 = bilby.gw.prior.BNSPriorDict(val)
        self.assertEqual(p1["lambda_1"], p2["lambda_1"])

    def test_update_sampler_kwargs_conditional_on_request_cpus(self):
        mock_input = create_autospec(bilby_pipe.main.Input)
        mock_input.request_cpus = 2
        mock_input._sampler_kwargs = dict(npoints=100)
        bilby_pipe.main.Input.update_sampler_kwargs_conditional_on_request_cpus(
            mock_input
        )
        self.assertEqual(mock_input._sampler_kwargs, dict(npoints=100, npool=2))

    def test_default_cosmology(self):
        inputs = bilby_pipe.main.Input(None, None)
        self.assertEqual(inputs.cosmology, bilby.gw.cosmology.get_cosmology("Planck15"))

    def test_cosmology(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.cosmology = "Planck15_LAL"
        self.assertEqual(
            inputs.cosmology, bilby.gw.cosmology.get_cosmology("Planck15_LAL")
        )

    def test_consistent_cosmology(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.cosmology = "Planck15_LAL"
        inputs.default_prior = "BBHPriorDict"
        inputs.trigger_time = 0
        inputs.deltaT = 2
        inputs.time_reference = "geocent"
        inputs.enforce_signal_duration = False
        inputs.prior_dict = bilby.gw.prior.BBHPriorDict(
            {
                "luminosity_distance": bilby.gw.prior.UniformSourceFrame(
                    minimum=10,
                    maximum=1000,
                    name="luminosity_distance",
                    cosmology="Planck15_LAL",
                )
            }
        )

        assert inputs.priors is not None
        assert "luminosity_distance" in inputs.priors

    def test_inconsistent_cosmology(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.cosmology = "Planck15_LAL"
        inputs.default_prior = "BBHPriorDict"
        inputs.trigger_time = 0
        inputs.deltaT = 2
        inputs.time_reference = "geocent"
        inputs.enforce_signal_duration = False
        inputs.prior_dict = bilby.gw.prior.BBHPriorDict(
            {
                "luminosity_distance": bilby.gw.prior.UniformSourceFrame(
                    minimum=10,
                    maximum=1000,
                    name="luminosity_distance",
                    cosmology="Planck15",
                )
            }
        )

        with self.assertRaises(
            ValueError, msg="Cosmology in prior does not match the global cosmology"
        ):
            inputs.priors


@patch.object(
    bilby_pipe.main.Input,
    "get_bilby_source_model_function",
    autospec=True,
)
@patch.object(
    bilby_pipe.main.Input, "waveform_generator_class", new_callable=PropertyMock
)
class TestInputWaveformGenerator(unittest.TestCase):
    def setUp(self):
        inputs = bilby_pipe.main.Input(None, None)
        inputs.detectors = ["H1"]
        inputs.reference_frequency = 20
        inputs.minimum_frequency = 20
        inputs.maximum_frequency = 1024
        inputs.waveform_approximant = "IMRPhenomPv2"
        inputs.pn_spin_order = -1
        inputs.pn_tidal_order = -1
        inputs.pn_phase_order = -1
        inputs.pn_amplitude_order = 0
        inputs.mode_array = None

        p_interferometers = MagicMock()
        p_interferometers.sampling_frequency = 10
        p_interferometers.duration = 20
        p_interferometers.start_time = 30
        inputs.interferometers = p_interferometers

        inputs.conversion_function = "noconvert"
        inputs.catch_waveform_errors = False
        inputs.likelihood_type = "GravitationalWaveTransient"

        inputs.frequency_domain_source_model = "dummy"
        inputs.waveform_arguments_dict = "{a: 10, b=test, c=[1, 2]}"

        inputs.waveform_generator_class_ctor_args = None

        self.inputs = inputs

    def _helper_install_mocks(
        self, *, p_waveform_generator_class, p_bilby_frequency_domain_source_model
    ):
        p_bilby_frequency_domain_source_model.side_effect = (
            self.prop_bilby_freq_domain_source_model
        )

        p_waveform_generator_class.return_value = (
            TestInputWaveformGenerator.WaveformInterface
        )

    class WaveformInterface:
        def __init__(self, argument1, *args, **kwargs):
            self.argument1 = argument1
            self.args = args
            self.kwargs = kwargs

    @staticmethod
    def freq_source_model_function(*args, **kwargs):
        # should not be called
        assert False

    @staticmethod
    def prop_bilby_freq_domain_source_model(self, model_string):
        return TestInputWaveformGenerator.freq_source_model_function

    def test_waveform_generator_class_is_correct_instance(
        self, p_waveform_generator_class, p_bilby_frequency_domain_source_model
    ):
        """waveform-generator is of correct type"""
        self._helper_install_mocks(
            p_waveform_generator_class=p_waveform_generator_class,
            p_bilby_frequency_domain_source_model=p_bilby_frequency_domain_source_model,
        )

        self.inputs.waveform_generator_class_ctor_args = (
            "{'argument1': 1, 'some_other': 'dummy_string'}"
        )

        generator_cls = self.inputs.waveform_generator_class
        p_waveform_generator_class.assert_called_once()
        self.assertIs(generator_cls, TestInputWaveformGenerator.WaveformInterface)

    def test_missing_argument_raises_an_error(
        self, p_waveform_generator_class, p_bilby_frequency_domain_source_model
    ):
        """Missing mandatory arguments to the waveform-generator class raise an exception"""
        self._helper_install_mocks(
            p_waveform_generator_class=p_waveform_generator_class,
            p_bilby_frequency_domain_source_model=p_bilby_frequency_domain_source_model,
        )

        with self.assertRaises(TypeError) as e:
            _ = self.inputs.waveform_generator

        self.assertIn(
            "missing 1 required positional argument: 'argument1'", str(e.exception)
        )

        # no error now
        self.inputs.waveform_generator_class_ctor_args = (
            "{'argument1': 1, 'some_other': 'dummy_string'}"
        )
        self.assertIsNotNone(self.inputs.waveform_generator)

    def test_injection_waveform_generator_class_only_from_data_generation(
        self, p_waveform_generator_class, p_bilby_frequency_domain_source_model
    ):
        """Checks that Input instance has no injection ctor parameter by default"""
        # injection parameters cannot be tested directly on the input class as they
        # are instantiated differently (see eg. DataGenerationInput)
        self._helper_install_mocks(
            p_waveform_generator_class=p_waveform_generator_class,
            p_bilby_frequency_domain_source_model=p_bilby_frequency_domain_source_model,
        )

        self.assertFalse(
            hasattr(self.inputs, "injection_waveform_generator_class_ctor_args")
        )

        with self.assertRaises(AttributeError):
            _ = (
                self.inputs.get_default_injection_waveform_generator_class_ctor_arguments()
            )

        self.inputs.injection_waveform_generator_class_ctor_args = (
            "{'argument1': 1, 'some_other': 'dummy_string2'}"
        )

        self.assertDictEqual(
            self.inputs.get_default_injection_waveform_generator_class_ctor_arguments(),
            {"argument1": 1, "some_other": "dummy_string2"},
        )

    def test_waveform_generator_class_arguments(
        self, p_waveform_generator_class, p_bilby_frequency_domain_source_model
    ):
        """Argument passed to ctor of waveform-generator are correct"""
        self._helper_install_mocks(
            p_waveform_generator_class=p_waveform_generator_class,
            p_bilby_frequency_domain_source_model=p_bilby_frequency_domain_source_model,
        )

        self.inputs.waveform_generator_class_ctor_args = (
            "{'argument1': 1, 'some_other': 'dummy_string'}"
        )

        wg = self.inputs.waveform_generator

        p_bilby_frequency_domain_source_model.assert_called_once()
        p_waveform_generator_class.assert_called_once()

        # checking how elements passed to the WaveformGenerator instance
        # have been constructed
        # this is self
        self.assertEqual(
            p_bilby_frequency_domain_source_model.call_args[0][0], self.inputs
        )
        # this is the frequency_domain_source_model
        self.assertEqual(p_bilby_frequency_domain_source_model.call_args[0][1], "dummy")

        # checking the argument passed to the constructor of the WaveformGenerator class
        self.assertIsInstance(wg, TestInputWaveformGenerator.WaveformInterface)
        self.assertEqual(wg.argument1, 1)
        self.assertIn("some_other", wg.kwargs)
        self.assertEqual(wg.kwargs["some_other"], "dummy_string")

        self.assertIn("frequency_domain_source_model", wg.kwargs)
        self.assertIs(
            wg.kwargs["frequency_domain_source_model"],
            TestInputWaveformGenerator.freq_source_model_function,
        )

        self.assertIn("sampling_frequency", wg.kwargs)
        self.assertIs(wg.kwargs["sampling_frequency"], 10)

        self.assertIn("duration", wg.kwargs)
        self.assertIs(wg.kwargs["duration"], 20)

        self.assertIn("start_time", wg.kwargs)
        self.assertIs(wg.kwargs["start_time"], 30)

        self.assertIn("parameter_conversion", wg.kwargs)
        self.assertIs(
            wg.kwargs["parameter_conversion"],
            bilby.gw.conversion.identity_map_conversion,
        )


if __name__ == "__main__":
    unittest.main()
