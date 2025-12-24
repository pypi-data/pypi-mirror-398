import os
import shutil
import unittest
from contextlib import contextmanager
from unittest.mock import MagicMock, PropertyMock, patch

import bilby
import bilby_pipe
from bilby.gw.detector.networks import get_empty_interferometer
from bilby_pipe.data_analysis import DataAnalysisInput, create_analysis_parser
from bilby_pipe.main import parse_args
from bilby_pipe.utils import BilbyPipeError


class TestDataAnalysisInput(unittest.TestCase):
    def setUp(self):
        self.outdir = "test_outdir"
        self.default_args_list = [
            "--ini",
            "tests/test_data_analysis.ini",
            "--outdir",
            self.outdir,
        ]
        self.parser = create_analysis_parser()
        self.inputs = DataAnalysisInput(
            *parse_args(self.default_args_list, self.parser), test=True
        )

    def tearDown(self):
        del self.default_args_list
        del self.parser
        del self.inputs
        if os.path.isdir(self.outdir):
            shutil.rmtree(self.outdir)

    def test_unset_sampling_seed(self):
        self.assertEqual(type(self.inputs.sampling_seed), int)

    def test_set_sampling_seed(self):
        args_list = self.default_args_list + ["--sampling-seed", "1"]
        inputs = DataAnalysisInput(*parse_args(args_list, self.parser), test=True)
        self.assertEqual(inputs.sampling_seed, 1)

    def test_set_sampler_ini(self):
        self.inputs = DataAnalysisInput(
            *parse_args(self.default_args_list, self.parser), test=True
        )
        self.assertEqual(self.inputs.sampler, "nestle")

    def test_set_sampler_command_line(self):
        args_list = self.default_args_list
        args_list.append("--sampler")
        args_list.append("emcee")
        self.inputs = DataAnalysisInput(*parse_args(args_list, self.parser), test=True)
        self.assertEqual(self.inputs.sampler, "emcee")

    def test_set_sampler_command_line_multiple_fail(self):
        args_list = self.default_args_list
        self.inputs = DataAnalysisInput(*parse_args(args_list, self.parser), test=True)
        with self.assertRaises(BilbyPipeError):
            self.inputs.sampler = ["dynesty", "nestle"]

    def test_direct_set_sampler(self):
        self.inputs.sampler = "dynesty"
        self.assertEqual(self.inputs.sampler, "dynesty")

    def test_set_sampling_kwargs_ini(self):
        self.assertEqual(
            self.inputs.sampler_kwargs, dict(a=1, b=2, sampling_seed=150914)
        )

    def test_set_sampling_kwargs_direct(self):
        self.inputs.sampler_kwargs = "{'a':5, 'b':5}"
        self.assertEqual(self.inputs.sampler_kwargs, dict(a=5, b=5))

    def test_unset_sampling_kwargs(self):
        args, unknown_args = parse_args(self.default_args_list, self.parser)
        args.sampler_kwargs = None
        args.sampling_seed = None
        # This tests the case where the sampling seed is not set
        with patch("numpy.random.randint", return_value=170817):
            inputs = DataAnalysisInput(args, unknown_args, test=True)
        self.assertEqual(inputs.sampler_kwargs, dict(sampling_seed=170817))

    def test_set_sampler_kwargs_fail(self):
        with self.assertRaises(BilbyPipeError):
            self.inputs.sampler_kwargs = "random_string"

    def test_set_frequency_domain_source_model(self):
        self.inputs.frequency_domain_source_model = "lal_binary_black_hole"
        self.assertEqual(
            self.inputs.frequency_domain_source_model, "lal_binary_black_hole"
        )

    def test_bilby_frequency_domain_source_model(self):
        self.inputs.frequency_domain_source_model = "lal_binary_black_hole"
        self.assertEqual(
            self.inputs.bilby_frequency_domain_source_model,
            bilby.gw.source.lal_binary_black_hole,
        )

    def test_unset_bilby_frequency_domain_source_model(self):
        self.inputs.frequency_domain_source_model = "not_a_source_model"
        with self.assertRaises(BilbyPipeError):
            print(self.inputs.bilby_frequency_domain_source_model)


class TestDataAnalysisInputWaveformGeneratorOptions(unittest.TestCase):
    def setUp(self):
        self.outdir = "test_outdir"
        self.default_args_list = [
            "--ini",
            "tests/test_data_analysis.ini",
            "--outdir",
            self.outdir,
            "--data-label",
            "TEST",
            "--trigger-time",
            "2",
            "--post-trigger-duration=2.0",
        ]
        self.data_dir = "tests/DATA/"
        self.parser = create_analysis_parser()

    def tearDown(self):
        del self.default_args_list
        if os.path.isdir(self.outdir):
            shutil.rmtree(self.outdir)

    class MyException(Exception):
        pass

    class WaveformInterface:
        def __init__(self, argument1, *args, **kwargs):  # noqa
            # argument1 is mandatory
            self.argument1 = argument1
            self.args = args
            self.kwargs = kwargs

        @property
        def duration(self):
            return 10

        @duration.setter
        def duration(self, value):
            return

        @property
        def sampling_frequency(self):
            return 10

        @sampling_frequency.setter
        def sampling_frequency(self, value):
            return

        @property
        def start_time(self):
            return 10

        @start_time.setter
        def start_time(self, value):
            return

        def frequency_domain_strain(self, *args, **kwargs):
            raise TestDataAnalysisInputWaveformGeneratorOptions.MyException

        def time_domain_strain(self, *args, **kwargs):
            raise TestDataAnalysisInputWaveformGeneratorOptions.MyException

    @contextmanager
    def _helper_mock(self):
        original_function = (
            DataAnalysisInput.get_default_waveform_generator_class_ctor_arguments
        )

        with patch.object(
            bilby_pipe.main.Input,
            "get_default_waveform_generator_class_ctor_arguments",
            autospec=True,
        ) as p_get_waveform_generator_class_ctor_arguments, patch.object(
            bilby_pipe.main.Input, "waveform_generator_class", new_callable=PropertyMock
        ) as p_waveform_generator_class, patch(
            "bilby_pipe.data_analysis.DataAnalysisInput.data_dump",
            # autospec=True,
            new_callable=PropertyMock,
        ) as p_data_dump, patch(
            "bilby_pipe.data_analysis.DataAnalysisInput._load_data_dump",
            autospec=True,
        ) as p_load_data_dump:
            p_waveform_generator_class.return_value = (
                TestDataAnalysisInputWaveformGeneratorOptions.WaveformInterface
            )
            p_get_waveform_generator_class_ctor_arguments.side_effect = (
                original_function
            )

            # mocking the interferometers property
            p_data_dump.return_value.interferometers = [
                get_empty_interferometer("L1"),
                get_empty_interferometer("H1"),
            ]

            yield (
                p_get_waveform_generator_class_ctor_arguments,
                p_waveform_generator_class,
                p_data_dump,
                p_load_data_dump,
            )

    def test_waveform_class_construction_no_data_creation(self):
        args_list = self.default_args_list + [
            "--waveform-generator",
            "some.dummy.class",  # intercepted by the mock
            "--waveform-generator-constructor-dict",
            "{'argument1': 10, 'arg2': 20, 'arg3': 'dummy'}",
        ]
        with self._helper_mock():
            # checks the type of the waveform generator class
            inputs = DataAnalysisInput(*parse_args(args_list, self.parser), test=True)
            self.assertIs(
                inputs.waveform_generator_class,
                self.WaveformInterface,
            )
            self.assertTrue(hasattr(inputs, "waveform_generator_class_ctor_args"))

    def test_waveform_class_construction_instance_type_passed_to_likelihood(self):
        """Checks that the correct instance of the WG is given"""
        args_list = self.default_args_list + [
            "--likelihood-type",
            "zero",
            "--waveform-generator",
            "some.dummy.class",  # intercepted by the mock
            "--injection-waveform-generator-constructor-dict",
            "{'argument1': 30, 'arg2': 20, 'arg3': 'dummy'}",
            "--waveform-generator-constructor-dict",
            "{'argument1': 10, 'arg2': 20, 'arg3': 'dummy'}",
        ]

        with self._helper_mock() as (
            p_get_waveform_generator_class_ctor_arguments,
            p_waveform_generator_class,
            p_data_dump,
            p_load_data_dump,
        ):
            args, unknown_args = parse_args(args_list, self.parser)

            # disable marginalization to make the test faster
            args.time_marginalization = False
            args.distance_marginalization = False

            inputs = DataAnalysisInput(args, unknown_args, test=False)

            # one setter
            p_waveform_generator_class.assert_called_once()
            self.assertEqual(
                # first [0] is the setter, it should be the right hand side of "=" which is the class name
                # last [0] is "args", it should be a tuple of arguments for the setter
                p_waveform_generator_class.call_args_list[0][0],
                ("some.dummy.class",),
            )

            # no instance created
            p_get_waveform_generator_class_ctor_arguments.assert_not_called()

            # we now check what is being instantiated on the waveform generator side
            p_waveform_generator_class.reset_mock()
            likelihood, priors = inputs.get_likelihood_and_priors()

            # one instance created
            p_get_waveform_generator_class_ctor_arguments.assert_called_once()
            p_waveform_generator_class.assert_called_once()
            # getter, empty args
            self.assertEqual(p_waveform_generator_class.call_args_list[0][0], tuple())

            # correct instance in the likelihood. If incorrect, we would have a TypeError
            self.assertIs(type(likelihood.waveform_generator), self.WaveformInterface)

    def test_waveform_class_construction_instance_arguments(self):
        """Checks the arguments passed to the WF generator"""
        args_list = self.default_args_list + [
            "--likelihood-type",
            "zero",
            "--waveform-generator",
            "some.dummy.class",  # intercepted by the mock
            "--injection-waveform-generator-constructor-dict",
            "{'argument1': 30, 'dummy_arg2': 20, 'dummy_arg3': 'dummy'}",
            "--waveform-generator-constructor-dict",
            "{'argument1': 10, 'arg2': 20, 'arg3': 'dummy'}",
        ]

        with self._helper_mock() as (
            p_get_waveform_generator_class_ctor_arguments,
            p_waveform_generator_class,
            p_data_dump,
            p_load_data_dump,
        ):
            args, unknown_args = parse_args(args_list, self.parser)

            # disable marginalization to make the test faster
            args.time_marginalization = False
            args.distance_marginalization = False

            inputs = DataAnalysisInput(args, unknown_args, test=False)

            # one setter (previous test)
            p_waveform_generator_class.assert_called_once()

            # we now check what is being instantiated on the waveform generator side
            p_waveform_generator_class.reset_mock()
            likelihood, priors = inputs.get_likelihood_and_priors()

            # one instance created
            p_get_waveform_generator_class_ctor_arguments.assert_called_once()
            p_waveform_generator_class.assert_called_once()
            # getter, empty args
            self.assertEqual(p_waveform_generator_class.call_args_list[0][0], tuple())

            # correct instance in the likelihood. If incorrect, we would have a TypeError
            self.assertIs(type(likelihood.waveform_generator), self.WaveformInterface)

            # correct parameters passed to the instance constructor
            waveform_generator = likelihood.waveform_generator

            # no confusion with the injection ctor dict
            self.assertEqual(waveform_generator.argument1, 10)

            # no unnamed arguments
            self.assertEqual(waveform_generator.args, tuple())

            # type of the argument is conserved
            self.assertIn("arg2", waveform_generator.kwargs)
            self.assertEqual(waveform_generator.kwargs["arg2"], 20)
            self.assertIn("arg3", waveform_generator.kwargs)
            self.assertEqual(waveform_generator.kwargs["arg3"], "dummy")

    def test_get_waveform_generator_class_ctor_arguments(self):
        """Checks the method get_waveform_generator_class_ctor_arguments"""
        args_list = self.default_args_list + [
            "--likelihood-type",
            "zero",
            "--waveform-generator",
            "some.dummy.class",  # intercepted by the mock
            "--injection-waveform-generator-constructor-dict",
            "{'argument1': 30, 'arg2': 20, 'dummy_arg3': 'dummy'}",
            "--waveform-generator-constructor-dict",
            "{'argument1': 10, 'arg2': 20, 'arg3': 'dummy'}",
        ]

        with self._helper_mock() as (
            p_get_waveform_generator_class_ctor_arguments,
            p_waveform_generator_class,
            p_data_dump,
            p_load_data_dump,
        ):
            inputs = DataAnalysisInput(*parse_args(args_list, self.parser), test=False)

            # one setter (previous test)
            p_waveform_generator_class.assert_called_once()
            p_get_waveform_generator_class_ctor_arguments.assert_not_called()

            dict_ctor = inputs.get_default_waveform_generator_class_ctor_arguments()
            p_get_waveform_generator_class_ctor_arguments.assert_called_once()

            self.assertIn("argument1", dict_ctor)
            self.assertEqual(
                dict_ctor["argument1"],
                10,  # int
            )
            self.assertIn(
                "arg2",
                dict_ctor,
            )
            self.assertEqual(
                dict_ctor["arg2"],
                20,  # int
            )
            self.assertIn("arg3", dict_ctor)
            self.assertEqual(
                dict_ctor["arg3"],
                "dummy",
            )

    def test_correct_arguments_passed_to_ctor(self):
        """Checks arguments passed to the constructor"""
        args_list = self.default_args_list + [
            "--injection-dict",
            "{'mass_1':10, 'mass_2':20, 'a_1':0.5, 'a_2':0.5, 'tilt_1':0, 'tilt_2':0}",
            "--zero-noise",
            "--waveform-generator",
            "some.dummy.class",  # intercepted by the mock
            "--injection-waveform-generator-constructor-dict",
            "{'a': 30, 'b': 20, 'c': 'dummy'}",
            "--waveform-generator-constructor-dict",
            "{'argument1': 10, 'arg2': 20, 'arg3': 'dummy'}",
        ]

        with self._helper_mock() as (
            p_get_injection_waveform_generator_class_ctor_arguments,
            p_waveform_generator_class,
            p_get_data,
            p_inject_signal_into_gwpy_timeseries,
        ):
            mock_class = MagicMock(side_effect=self.MyException)
            p_waveform_generator_class.return_value = mock_class
            inputs = DataAnalysisInput(*parse_args(args_list, self.parser), test=False)
            with self.assertRaises(self.MyException):
                _ = inputs.waveform_generator

            mock_class.assert_called_once()
            self.assertEqual(mock_class.call_args[0], tuple())
            self.assertLessEqual(
                {"argument1", "arg2", "arg3"}, mock_class.call_args[1].keys()
            )
            self.assertDictEqual(
                {_: mock_class.call_args[1][_] for _ in {"argument1", "arg2", "arg3"}},
                {"argument1": 10, "arg2": 20, "arg3": "dummy"},
            )


if __name__ == "__main__":
    unittest.main()
