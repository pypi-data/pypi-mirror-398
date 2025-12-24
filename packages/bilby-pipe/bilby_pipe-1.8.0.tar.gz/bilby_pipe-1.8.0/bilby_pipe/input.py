#!/usr/bin/env python
"""
Module containing the main input class
"""
import glob
import inspect
import itertools
import json
import os
import shutil
import subprocess
from importlib import import_module

import numpy as np
import pandas as pd
from astropy.cosmology import cosmology_equal
from gwosc.datasets import event_gps

import bilby

from . import utils
from .utils import (
    CALIBRATION_CORRECTION_TYPE_LOOKUP,
    SAMPLER_SETTINGS,
    BilbyPipeError,
    BilbyPipeInternalError,
    check_if_psd_is_from_built_in,
    convert_string_to_dict,
    convert_string_to_list,
    convert_string_to_tuple,
    get_and_set_cosmology,
    get_colored_string,
    get_function_from_string_path,
    get_time_prior,
    logger,
    pretty_print_dictionary,
    resolve_filename_with_transfer_fallback,
)


class Input(object):
    """Superclass of input handlers"""

    _cosmology = None

    def __init__(self, args, unknown_args, print_msg=True):
        if print_msg:
            logger.info(f"Command line arguments: {args}")
            logger.info(f"Unknown command line arguments: {unknown_args}")
        self.known_args = args
        self.unknown_args = unknown_args

        self.container = getattr(self.known_args, "container", None)
        self.conda_env = getattr(self.known_args, "conda_env", None)

    @property
    def complete_ini_file(self):
        return f"{self.outdir}/{self.label}_config_complete.ini"

    @property
    def cosmology(self):
        if self._cosmology is None:
            self._cosmology = get_and_set_cosmology()
            logger.warning(f"No cosmology set, using default: {self._cosmology}")
        return self._cosmology

    @cosmology.setter
    def cosmology(self, cosmology):
        logger.debug(f"Setting cosmology to {cosmology}")
        self._cosmology = get_and_set_cosmology(cosmology)

    @property
    def idx(self):
        """The level A job index"""
        return self._idx

    @idx.setter
    def idx(self, idx):
        self._idx = idx

    @property
    def known_detectors(self):
        dirs = os.path.join(os.path.dirname(bilby.gw.detector.__file__), "detectors")
        known_files = glob.glob(os.path.join(dirs, "*"))
        return [os.path.basename(kf).split(".")[0] for kf in known_files]

    @property
    def detectors(self):
        """A list of the detectors to include, e.g., ['H1', 'L1']"""
        return self._detectors

    @detectors.setter
    def detectors(self, detectors):
        self._detectors = utils.convert_detectors_input(detectors)
        self._check_detectors_against_known_detectors()

    def _check_detectors_against_known_detectors(self):
        for element in self.detectors:
            if element not in self.known_detectors:
                msg = (
                    'Argument detectors contains "{}" not in the known '
                    "detectors list: {} ".format(element, self.known_detectors)
                    + ". This will likely fail at the data generation step"
                )
                logger.warning(get_colored_string(msg))

    @staticmethod
    def _split_string_by_space(string):
        """Converts "H1 L1" to ["H1", "L1"]"""
        return string.split(" ")

    @staticmethod
    def _convert_string_to_list(string):
        """Converts various strings to a list"""
        string = string.replace(",", " ")
        string = string.replace("[", "")
        string = string.replace("]", "")
        string = string.replace('"', "")
        string = string.replace("'", "")
        string_list = string.split()
        return string_list

    @property
    def outdir(self):
        """The path to the directory where output will be stored"""
        utils.check_directory_exists_and_if_not_mkdir(self._outdir)
        return self._outdir

    @outdir.setter
    def outdir(self, outdir):
        if outdir == ".":
            raise BilbyPipeError("Unable to use '.' as an outdir")
        self._outdir = os.path.relpath(outdir)

    @property
    def submit_directory(self):
        """The path to the directory where submit output will be stored"""
        path = os.path.join(self._outdir, "submit")
        utils.check_directory_exists_and_if_not_mkdir(path)
        return path

    @property
    def log_directory(self):
        """The top-level directory for the log directories"""
        utils.check_directory_exists_and_if_not_mkdir(self._log_directory)
        return self._log_directory

    @log_directory.setter
    def log_directory(self, log_directory):
        if log_directory is None:
            self._log_directory = self._outdir
        else:
            self._log_directory = log_directory

    @property
    def data_generation_log_directory(self):
        """The path to the directory where generation logs will be stored"""
        path = os.path.join(self.log_directory, "log_data_generation")
        utils.check_directory_exists_and_if_not_mkdir(path)
        return path

    @property
    def data_analysis_log_directory(self):
        """The path to the directory where analysis logs will be stored"""
        path = os.path.join(self.log_directory, "log_data_analysis")
        utils.check_directory_exists_and_if_not_mkdir(path)
        return path

    @property
    def summary_log_directory(self):
        """The path to the directory where pesummary logs will be stored"""
        path = os.path.join(self.log_directory, "log_results_page")
        utils.check_directory_exists_and_if_not_mkdir(path)
        return path

    @property
    def data_directory(self):
        """The path to the directory where data output will be stored"""
        path = os.path.join(self._outdir, "data")
        utils.check_directory_exists_and_if_not_mkdir(path)
        return path

    @property
    def result_directory(self):
        """The path to the directory where result output will be stored"""
        path = os.path.join(self._outdir, "result")
        utils.check_directory_exists_and_if_not_mkdir(path)
        return path

    @property
    def final_result_directory(self):
        """The path to the directory where final result output will be stored"""
        path = os.path.join(self._outdir, "final_result")
        utils.check_directory_exists_and_if_not_mkdir(path)
        return path

    @property
    def webdir(self):
        utils.check_directory_exists_and_if_not_mkdir(self._webdir)
        return self._webdir

    @webdir.setter
    def webdir(self, webdir):
        if webdir is None:
            self._webdir = os.path.join(self.outdir, "results_page")
        else:
            self._webdir = webdir

    @property
    def gps_file(self):
        """The gps file containing the list of gps times"""
        return self._gps_file

    @gps_file.setter
    def gps_file(self, gps_file):
        """Set and parse the gps_file"""
        if gps_file is None:
            self._gps_file = None
            return
        elif filename := resolve_filename_with_transfer_fallback(gps_file):
            self._gps_file = filename
        else:
            raise FileNotFoundError(f"Input file gps_file={gps_file} does not exist")

        self._parse_gps_file()

    def _parse_gps_file(self):
        gpstimes = self.read_gps_file(self.gps_file)
        n = len(gpstimes)
        logger.debug(f"{n} start times found in gps_file={self.gps_file}")
        self.gpstimes = gpstimes

    @staticmethod
    def read_gps_file(gps_file):
        gpstimes = np.loadtxt(gps_file, ndmin=2, delimiter=",")
        if gpstimes.ndim > 1:
            logger.debug(f"Reading column 0 from gps_file={gps_file}")
            gpstimes = gpstimes[:, 0]
        return gpstimes

    @property
    def gps_tuple(self):
        return self._gps_tuple

    @gps_tuple.setter
    def gps_tuple(self, gps_tuple):
        """Set and parse the gps_tuple"""
        if gps_tuple is None:
            self._gps_tuple = None
            return
        else:
            self._gps_tuple = gps_tuple
            self.gpstimes = self.parse_gps_tuple(gps_tuple)

    @staticmethod
    def parse_gps_tuple(gps_tuple):
        start, dt, N = convert_string_to_tuple(gps_tuple)
        start_times = np.linspace(start, start + (N - 1) * dt, N)
        return start_times

    @property
    def timeslide_file(self):
        """Timeslide file.

        Timeslide file containing the list of timeslides to apply to each
        detector's start time.
        """
        return self._timeslide_file

    @timeslide_file.setter
    def timeslide_file(self, timeslide_file):
        """Set the timeslide_file.

        At setting, will check the file exists, read the contents,
        save the timeslide value for each of the detectors.
        """
        if timeslide_file is None:
            self._timeslide_file = None
            return
        elif filename := resolve_filename_with_transfer_fallback(timeslide_file):
            self._timeslide_file = filename
        else:
            raise FileNotFoundError(
                f"Input file timeslide_file={timeslide_file} not understood"
            )

        if hasattr(self, "_timeslide_file"):
            self._parse_timeslide_file()
        else:
            logger.debug("No _parse_timeslide_file method present")

    def read_timeslide_file(self):
        """Read timeslide file.

        Each row of file is an array, hence ndmin = 2
        [ [timshift1,...], [], [] ...]
        """
        timeslides_list = np.loadtxt(self.timeslide_file, ndmin=2)
        return timeslides_list

    def _parse_timeslide_file(self):
        """Parse the timeslide file and check for correctness.

        Sets the attribute "timeslides" if timeslide file correctly formatted
        and passed to Inputs()
        """
        timeslides_list = self.read_timeslide_file()

        number_rows, number_columns = timeslides_list.shape
        if number_columns != len(self.detectors):
            raise BilbyPipeError(
                "The timeslide file must have one column for each of the detectors. "
                "Number Cols: {}, Number Detectors: {}".format(
                    number_columns, len(self.detectors)
                )
            )
        if number_rows != len(self.gpstimes):
            raise BilbyPipeError(
                "The timeslide file must have one row for each gps time. "
                "Number Rows: {}, Number Gps Times: {}".format(
                    number_rows, len(self.gpstimes)
                )
            )
        times = np.hsplit(timeslides_list, len(self.detectors))
        self.timeslides = {}
        for i in range(len(self.detectors)):
            self.timeslides.update({self.detectors[i]: times[i].flatten()})
        logger.debug(
            f"{number_rows} timeslides found in timeslide_file={self.timeslide_file}"
        )

    def get_timeslide_dict(self, idx):
        """Return a specific timeslide value from the timeslide file.

        Given an index, the dict of {detector: timeslide value} is created for
        the specific index and returned.
        """
        if not hasattr(self, "timeslides"):
            raise BilbyPipeError("Timeslide file must be provided.")
        if any(len(t) <= idx for t in self.timeslides.values()):
            raise BilbyPipeError(
                f"Timeslide index={idx} > number of timeslides available."
            )
        timeslide_val = {
            det: timeslide[idx] for det, timeslide in self.timeslides.items()
        }
        logger.debug(f"Timeslide value: {timeslide_val}")
        return timeslide_val

    @property
    def bilby_frequency_domain_source_model(self):
        """
        The bilby function to pass to the waveform_generator

        This can be a function defined in an external package.
        """
        return self.get_bilby_source_model_function(self.frequency_domain_source_model)

    def get_bilby_source_model_function(self, model_string):
        """
        Method to return a bilby frequency domain source model function
        given a string.
        """

        if model_string in bilby.gw.source.__dict__.keys():
            model = model_string
            logger.debug(f"Using the {model} source model")
            return bilby.gw.source.__dict__[model]
        elif "." in model_string:
            return get_function_from_string_path(model_string)
        else:
            raise BilbyPipeError(f"No source model {model_string} found.")

    @property
    def reference_frequency(self):
        return self._reference_frequency

    @reference_frequency.setter
    def reference_frequency(self, reference_frequency):
        self._reference_frequency = float(reference_frequency)

    @property
    def mode_array(self):
        return self._mode_array

    @mode_array.setter
    def mode_array(self, mode_array):
        # Pre sanitize the mode array
        if mode_array == [None]:
            mode_array = None

        if isinstance(mode_array, list):
            # Hack because configargparse splits the mode_array
            mode_array = ",".join(mode_array)

        if mode_array is not None:
            self._mode_array = convert_string_to_list(mode_array)
        else:
            logger.debug("mode_array not set")
            self._mode_array = None

        # Ensure it is a list of lists
        if np.array(self._mode_array).ndim == 1:
            self._mode_array = [self._mode_array]

        if np.array(self._mode_array).ndim == 2:
            for mode in self._mode_array:
                if len(mode) != 2:
                    raise BilbyPipeError(f"mode_array {self._mode_array} is invalid")
        if np.array(self._mode_array).ndim > 2:
            raise BilbyPipeError(f"mode_array {self._mode_array} is invalid")

    def get_default_waveform_generator_class_ctor_arguments(self):
        wf_cls_a = dict()

        if self.waveform_generator_class_ctor_args is not None:
            wf_cls_a.update(
                convert_string_to_dict(self.waveform_generator_class_ctor_args)
            )

        logger.debug(
            f"Default waveform_generator_constructor_dict: {pretty_print_dictionary(wf_cls_a)}"
        )
        return wf_cls_a

    def get_default_waveform_arguments(self):
        wfa = dict(
            reference_frequency=self.reference_frequency,
            waveform_approximant=self.waveform_approximant,
            minimum_frequency=self.minimum_frequency,
            maximum_frequency=self.maximum_frequency,
            catch_waveform_errors=self.catch_waveform_errors,
            pn_spin_order=self.pn_spin_order,
            pn_tidal_order=self.pn_tidal_order,
            pn_phase_order=self.pn_phase_order,
            pn_amplitude_order=self.pn_amplitude_order,
            mode_array=self.mode_array,
        )

        if self.waveform_arguments_dict is not None:
            wfa.update(convert_string_to_dict(self.waveform_arguments_dict))

        logger.debug(f"Default waveform_arguments: {pretty_print_dictionary(wfa)}")
        return wfa

    def get_default_injection_waveform_generator_class_ctor_arguments(self):
        wf_cls_a = dict()

        if self.injection_waveform_generator_class_ctor_args is not None:
            wf_cls_a.update(
                convert_string_to_dict(
                    self.injection_waveform_generator_class_ctor_args
                )
            )

        logger.debug(
            f"Default injection_waveform_generator_class_ctor_args: {pretty_print_dictionary(wf_cls_a)}"
        )
        return wf_cls_a

    def get_injection_waveform_arguments(self):
        """Get the dict of the waveform arguments needed for creating injections.

        Defaults the injection-waveform-approximant to waveform-approximant, if
        no injection-waveform-approximant provided. Note that the default
        waveform-approximant is `IMRPhenomPv2`.
        """
        if self.injection_waveform_approximant is None:
            self.injection_waveform_approximant = self.waveform_approximant
        waveform_arguments = self.get_default_waveform_arguments()

        if self.injection_waveform_arguments is not None:
            waveform_arguments.update(
                convert_string_to_dict(self.injection_waveform_arguments)
            )

        waveform_arguments["waveform_approximant"] = self.injection_waveform_approximant
        waveform_arguments["numerical_relativity_file"] = self.numerical_relativity_file
        return waveform_arguments

    @property
    def bilby_roq_frequency_domain_source_model(self):
        if self.frequency_domain_source_model == "lal_binary_neutron_star":
            logger.debug("Using the binary_neutron_star_roq source model")
            return bilby.gw.source.binary_neutron_star_roq
        elif self.frequency_domain_source_model == "lal_binary_black_hole":
            logger.debug("Using the binary_black_hole_roq source model")
            return bilby.gw.source.binary_black_hole_roq
        else:
            return self.bilby_frequency_domain_source_model

    @property
    def bilby_relative_binning_frequency_domain_source_model(self):
        if self.frequency_domain_source_model == "lal_binary_neutron_star":
            logger.debug("Using the binary_neutron_star_relative_binning source model")
            return bilby.gw.source.lal_binary_neutron_star_relative_binning
        elif self.frequency_domain_source_model == "lal_binary_black_hole":
            logger.debug("Using the binary_black_hole_relative_binning source model")
            return bilby.gw.source.lal_binary_black_hole_relative_binning
        else:
            return self.bilby_frequency_domain_source_model

    @property
    def bilby_multiband_frequency_domain_source_model(self):
        if self.frequency_domain_source_model == "lal_binary_neutron_star":
            logger.info("Using the binary_neutron_star_frequency_sequence source model")
            return bilby.gw.source.binary_neutron_star_frequency_sequence
        elif self.frequency_domain_source_model == "lal_binary_black_hole":
            logger.info("Using the binary_black_hole_frequency_sequence source model")
            return bilby.gw.source.binary_black_hole_frequency_sequence
        else:
            return self.bilby_frequency_domain_source_model

    @property
    def frequency_domain_source_model(self):
        """String of which frequency domain source model to use"""
        return self._frequency_domain_source_model

    @frequency_domain_source_model.setter
    def frequency_domain_source_model(self, frequency_domain_source_model):
        self._frequency_domain_source_model = frequency_domain_source_model

    @property
    def trigger_time(self):
        return self._trigger_time

    @trigger_time.setter
    def trigger_time(self, trigger_time):
        # Convert trigger time
        if trigger_time is None:
            logger.debug("No trigger time given")
        elif isinstance(trigger_time, str) and "GW" in trigger_time:
            logger.debug(f"Using gwosc to find trigger time for event {trigger_time}")
            trigger_time = event_gps(trigger_time)
        else:
            trigger_time = float(trigger_time)

        self._trigger_time = trigger_time
        if trigger_time is not None:
            logger.debug(f"Setting trigger time {trigger_time}")

    @property
    def start_time(self):
        if hasattr(self, "_start_time"):
            self._verify_start_time(self._start_time)
            return self._start_time
        try:
            self._start_time = (
                self.trigger_time + self.post_trigger_duration - self.duration
            )
            return self._start_time
        except AttributeError:
            logger.warning("Unable to calculate default segment start time")
            return None

    def _verify_start_time(self, start_time):
        try:
            inferred_start_time = (
                self.trigger_time + self.post_trigger_duration - self.duration
            )
        except AttributeError:
            logger.warning("Unable to verify start-time consistency")
            return

        if inferred_start_time != start_time:
            raise BilbyPipeError("Unexpected behaviour encountered with start time")

    @start_time.setter
    def start_time(self, start_time):
        self._verify_start_time(start_time)
        self._start_time = start_time
        if start_time is not None:
            logger.debug(f"Setting segment start time {start_time}")

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, duration):
        self._duration = duration
        if duration is not None:
            logger.debug(f"Setting segment duration {duration}s")

    @property
    def injection_numbers(self):
        if hasattr(self, "_injection_numbers"):
            return self._injection_numbers
        else:
            raise BilbyPipeInternalError("Injection numbers requested, but not yet set")

    @injection_numbers.setter
    def injection_numbers(self, injection_numbers):
        if (
            injection_numbers is None
            or len(injection_numbers) == 0
            or injection_numbers == "None"
            or injection_numbers[0] == "None"
            or injection_numbers[0] is None
        ):
            self._injection_numbers = None
        elif all(
            i is not None
            and not isinstance(i, float)
            and utils.check_if_represents_int(i)
            or ":" in str(i)
            for i in injection_numbers
        ):
            list_of_lists = []
            for i in injection_numbers:
                if utils.check_if_represents_int(i):
                    list_of_lists.append([int(i)])
                else:
                    list_of_lists.append(utils.convert_string_slice_syntax(i))
            self._injection_numbers = list(set(itertools.chain(*list_of_lists)))
        else:
            raise BilbyPipeError(f"Invalid injection numbers {injection_numbers}")

    @property
    def injection_df(self):
        return self._injection_df

    @injection_df.setter
    def injection_df(self, injection_df):
        if isinstance(injection_df, pd.DataFrame) is False:
            raise BilbyPipeError("Setting injection df with non-pandas DataFrame")
        elif self.injection_numbers is not None:
            logger.debug(
                f"Truncating injection injection df to rows {self.injection_numbers}"
            )
            try:
                self._injection_df = injection_df.iloc[self.injection_numbers]
            except IndexError:
                raise BilbyPipeError(
                    "Your injection_numbers are incompatible with the injection set"
                )
        else:
            self._injection_df = injection_df

    @property
    def injection_file(self):
        return self._injection_file

    @injection_file.setter
    def injection_file(self, injection_file):
        if injection_file is None:
            logger.debug("No injection file set")
            self._injection_file = None
        elif filename := resolve_filename_with_transfer_fallback(injection_file):
            self._injection_file = os.path.relpath(filename)
            self.injection_df = self.read_injection_file(filename)
            self.total_number_of_injections = len(self.injection_df)
            self.injection = True
        else:
            raise FileNotFoundError(f"Injection file {injection_file} not found")

    @property
    def injection_dict(self):
        return self._injection_dict

    @injection_dict.setter
    def injection_dict(self, injection_dict):
        if injection_dict is None:
            self._injection_dict = None
            return
        elif isinstance(injection_dict, str):
            self._injection_dict = convert_string_to_dict(injection_dict)
        elif isinstance(injection_dict, dict):
            self._injection_dict = injection_dict
        else:
            raise BilbyPipeError("injection-dict can not be coerced to a dict")

        self.injection_df = pd.DataFrame(self._injection_dict, index=[0])
        self.total_number_of_injections = 1
        self.injection = True

    @staticmethod
    def read_injection_file(injection_file):
        extension = os.path.splitext(injection_file)[-1]
        if extension == ".json":
            return Input.read_json_injection_file(injection_file)
        elif extension == ".dat":
            return Input.read_dat_injection_file(injection_file)

    @staticmethod
    def read_json_injection_file(injection_file):
        with open(injection_file, "r") as file:
            injection_dict = json.load(
                file, object_hook=bilby.core.utils.decode_bilby_json
            )
        injection_df = injection_dict["injections"]
        try:
            injection_df = pd.DataFrame(injection_df)
        except ValueError:
            # If injection_df is a dictionary of single elements, set the index-array in pandas
            injection_df = pd.DataFrame(injection_df, index=[0])
        return injection_df

    @staticmethod
    def read_dat_injection_file(injection_file):
        return pd.read_csv(injection_file, sep=r"\s+")

    @property
    def calibration_correction_type(self):
        return self._calibration_correction_type_dict

    @calibration_correction_type.setter
    def calibration_correction_type(self, calibration_correction_type):
        if calibration_correction_type is None:
            logger.warning(
                "calibration_correction_type=None is passed. Assuming "
                "calibration_correction_type='data' for H1, L1, K1, and 'template' for V1"
            )
            self._calibration_correction_type_dict = {
                det: CALIBRATION_CORRECTION_TYPE_LOOKUP[det] for det in self.detectors
            }
        elif (
            calibration_correction_type == "data"
            or calibration_correction_type == "template"
        ):
            logger.info(
                "Assuming the same calibration correction type "
                f"{calibration_correction_type} for all detectors"
            )
            self._calibration_correction_type_dict = {
                det: calibration_correction_type for det in self.detectors
            }
        elif calibration_correction_type is not None:
            try:
                self._calibration_correction_type_dict = convert_string_to_dict(
                    calibration_correction_type, "calibration-correction-type"
                )
            except Exception as e:
                raise BilbyPipeError(
                    f"{calibration_correction_type} not understood, failed with exception {e}"
                )

    @property
    def spline_calibration_envelope_dict(self):
        return self._spline_calibration_envelope_dict

    @spline_calibration_envelope_dict.setter
    def spline_calibration_envelope_dict(self, spline_calibration_envelope_dict):
        if spline_calibration_envelope_dict is not None:
            self._spline_calibration_envelope_dict = convert_string_to_dict(
                spline_calibration_envelope_dict, "spline-calibration-envelope-dict"
            )
        else:
            logger.debug("spline_calibration_envelope_dict")
            self._spline_calibration_envelope_dict = None

    @property
    def spline_calibration_amplitude_uncertainty_dict(self):
        return self._spline_calibration_amplitude_uncertainty_dict

    @spline_calibration_amplitude_uncertainty_dict.setter
    def spline_calibration_amplitude_uncertainty_dict(
        self, spline_calibration_amplitude_uncertainty_dict
    ):
        if spline_calibration_amplitude_uncertainty_dict is not None:
            self._spline_calibration_amplitude_uncertainty_dict = (
                convert_string_to_dict(
                    spline_calibration_amplitude_uncertainty_dict,
                    "spline-calibration-amplitude-uncertainty-dict",
                )
            )
        else:
            logger.debug("spline_calibration_amplitude_uncertainty_dict")
            self._spline_calibration_amplitude_uncertainty_dict = None

    @property
    def spline_calibration_phase_uncertainty_dict(self):
        return self._spline_calibration_phase_uncertainty_dict

    @spline_calibration_phase_uncertainty_dict.setter
    def spline_calibration_phase_uncertainty_dict(
        self, spline_calibration_phase_uncertainty_dict
    ):
        if spline_calibration_phase_uncertainty_dict is not None:
            self._spline_calibration_phase_uncertainty_dict = convert_string_to_dict(
                spline_calibration_phase_uncertainty_dict,
                "spline-calibration-phase-uncertainty-dict",
            )
        else:
            logger.debug("spline_calibration_phase_uncertainty_dict")
            self._spline_calibration_phase_uncertainty_dict = None

    @property
    def minimum_frequency(self):
        """The minimum frequency

        If a per-detector dictionary is given, this will return the minimum
        frequency value. To access the dictionary,
        see self.minimum_frequency_dict
        """
        return self._minimum_frequency

    @minimum_frequency.setter
    def minimum_frequency(self, minimum_frequency):
        if minimum_frequency is None:
            self._minimum_frequency = None
            self.minimum_frequency_dict = {det: None for det in self.detectors}
        else:
            try:
                self._minimum_frequency = float(minimum_frequency)
                self.minimum_frequency_dict = {
                    det: float(minimum_frequency) for det in self.detectors
                }
            except ValueError:
                self.minimum_frequency_dict = convert_string_to_dict(
                    minimum_frequency, "minimum-frequency"
                )
                self._minimum_frequency = np.min(
                    [xx for xx in self._minimum_frequency_dict.values()]
                ).item()

    @property
    def minimum_frequency_dict(self):
        return self._minimum_frequency_dict

    @minimum_frequency_dict.setter
    def minimum_frequency_dict(self, minimum_frequency_dict):
        self.test_frequency_dict(frequency_dict=minimum_frequency_dict, label="minimum")
        self._minimum_frequency_dict = minimum_frequency_dict

    @property
    def maximum_frequency(self):
        """The maximum frequency

        If a per-detector dictionary is given, this will return the maximum
        frequency value. To access the dictionary,
        see self.maximum_frequency_dict
        """

        return self._maximum_frequency

    @maximum_frequency.setter
    def maximum_frequency(self, maximum_frequency):
        if maximum_frequency is None:
            self._maximum_frequency = self.sampling_frequency / 2
            self.maximum_frequency_dict = {
                det: self._maximum_frequency for det in self.detectors
            }
            logger.debug(
                "No maximum frequency given. "
                "Setting to sampling frequency / 2 = {}".format(self._maximum_frequency)
            )
        else:
            try:
                self._maximum_frequency = float(maximum_frequency)
                self.maximum_frequency_dict = {
                    det: float(maximum_frequency) for det in self.detectors
                }
            except ValueError:
                self.maximum_frequency_dict = convert_string_to_dict(
                    maximum_frequency, "maximum-frequency"
                )
                self._maximum_frequency = np.max(
                    [xx for xx in self._maximum_frequency_dict.values()]
                ).item()

    @property
    def maximum_frequency_dict(self):
        return self._maximum_frequency_dict

    @maximum_frequency_dict.setter
    def maximum_frequency_dict(self, maximum_frequency_dict):
        self.test_frequency_dict(frequency_dict=maximum_frequency_dict, label="maximum")
        self._maximum_frequency_dict = maximum_frequency_dict

    def test_frequency_dict(self, frequency_dict, label=""):
        for det in self.detectors:
            if det not in frequency_dict.keys():
                raise BilbyPipeError(
                    f"Input {label} frequency required for detector {det}"
                )
        return frequency_dict

    @property
    def default_prior_files(self):
        return self.get_default_prior_files()

    @staticmethod
    def get_default_prior_files():
        """Returns a dictionary of the default priors"""
        prior_files_glob = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "data_files/*prior"
        )
        filenames = glob.glob(prior_files_glob)
        return {os.path.basename(ff).rstrip(".prior"): ff for ff in filenames}

    def get_distance_file_lookup_table(self, prior_file_str):
        lookup_file_source = self.get_source_distance_file_lookup_table(prior_file_str)
        fname = os.path.basename(lookup_file_source)
        lookup_file_dest = os.path.join(self.outdir, "." + fname)
        if os.path.isfile(lookup_file_source):
            shutil.copyfile(lookup_file_source, lookup_file_dest)
        return lookup_file_dest

    def get_source_distance_file_lookup_table(self, prior_file_str):
        direc = os.path.dirname(self.default_prior_files[prior_file_str])
        if self.phase_marginalization:
            fname = f"{prior_file_str}_distance_marginalization_lookup_phase.npz"
        else:
            fname = f"{prior_file_str}_distance_marginalization_lookup.npz"
        return os.path.join(direc, fname)

    @property
    def prior_file(self):
        return self._prior_file

    @prior_file.setter
    def prior_file(self, prior_file):
        if prior_file is None:
            self._prior_file = None
        elif filename := resolve_filename_with_transfer_fallback(prior_file):
            self._prior_file = filename
        elif prior_file in self.default_prior_files:
            self._prior_file = self.default_prior_files[prior_file]
            self.distance_marginalization_lookup_table = (
                self.get_distance_file_lookup_table(prior_file)
            )
        else:
            raise FileNotFoundError(f"No prior file {prior_file} available")

        logger.debug(f"Setting prior-file to {self._prior_file}")

    @property
    def prior_dict(self):
        """The input prior_dict from the ini (if given)

        Note, this is not the bilby prior (see self.priors for that), this is
        a key-val dictionary where the val's are strings which are converting
        into bilby priors in :func:`_get_priors`
        """
        return self._prior_dict

    @prior_dict.setter
    def prior_dict(self, prior_dict):
        if isinstance(prior_dict, dict):
            prior_dict = prior_dict
        elif isinstance(prior_dict, str):
            prior_dict = utils.convert_prior_string_input(prior_dict)
        elif prior_dict is None:
            self._prior_dict = None
            return
        else:
            raise BilbyPipeError(f"prior_dict={prior_dict} not understood")

        self._prior_dict = {
            self._convert_prior_dict_key(key): val for key, val in prior_dict.items()
        }

    @staticmethod
    def _convert_prior_dict_key(key):
        """Converts the prior dict key to standard form

        In the ini read, mass_1 -> mass-1, this corrects for that
        """
        if "-" in key:
            key_replaced = key.replace("-", "_")
            logger.debug(f"Converting prior-dict key {key} to {key_replaced}")
            key = key_replaced
        return key

    @property
    def distance_marginalization_lookup_table(self):
        return self._distance_marginalization_lookup_table

    @distance_marginalization_lookup_table.setter
    def distance_marginalization_lookup_table(
        self, distance_marginalization_lookup_table
    ):
        if distance_marginalization_lookup_table is None:
            if hasattr(self, "_distance_marginalization_lookup_table"):
                pass
            else:
                self._distance_marginalization_lookup_table = None
        else:
            if hasattr(self, "_distance_marginalization_lookup_table"):
                logger.debug("Overwriting distance_marginalization_lookup_table")
            self._distance_marginalization_lookup_table = (
                resolve_filename_with_transfer_fallback(
                    distance_marginalization_lookup_table
                )
            )

    @property
    def default_prior(self):
        return getattr(self, "_default_prior", None)

    @default_prior.setter
    def default_prior(self, default_prior):
        self._default_prior = default_prior

    @property
    def combined_default_prior_dicts(self):
        d = bilby.core.prior.__dict__.copy()
        d.update(bilby.gw.prior.__dict__)
        return d

    @property
    def time_parameter(self):
        return f"{self.time_reference}_time"

    def create_time_prior(self):
        cond_a = getattr(self, "trigger_time", None) is not None
        cond_b = getattr(self, "deltaT", None) is not None
        if cond_a and cond_b:
            logger.debug(
                "Setting geocent time prior using trigger-time={} and deltaT={}".format(
                    self.trigger_time, self.deltaT
                )
            )
            if self.time_reference == "geocent":
                latex_label = "$t_c$"
            else:
                latex_label = f"$t_{self.time_reference[0]}$"
            time_prior = get_time_prior(
                time=self.trigger_time,
                uncertainty=self.deltaT / 2.0,
                name=self.time_parameter,
                latex_label=latex_label,
            )
        else:
            raise BilbyPipeError("Unable to set geocent_time prior from trigger_time")

        return time_prior

    @property
    def priors(self):
        """Read in and compose the prior at run-time"""
        if getattr(self, "_priors", None) is None:
            self._priors = self._get_priors()
            error = self.enforce_signal_duration
            if error and hasattr(self._priors, "validate_prior"):
                self._priors.validate_prior(
                    duration=self.duration,
                    minimum_frequency=self.minimum_frequency,
                    error=True,
                    warning=False,
                )
            try:
                self._priors.check_valid_cosmology()
            except AttributeError:
                logger.warning("Could not check if prior uses a valid cosmology.")
            if hasattr(self._priors, "cosmology"):
                if self._priors.cosmology and not cosmology_equal(
                    self.cosmology, self._priors.cosmology, allow_equivalent=True
                ):
                    raise ValueError(
                        "Cosmology in prior does not match the global cosmology: \n"
                        f"Prior: {self._priors.cosmology}\n"
                        f"Global: {self.cosmology}"
                    )
            else:
                logger.warning(
                    "Prior does not have a cosmology. Could not check for consistency."
                )
        return self._priors

    @priors.setter
    def priors(self, priors):
        self._priors = priors

    def _get_priors(self, add_time=True):
        """Construct the priors

        Parameters
        ----------
        add_time: bool
            If True, the time prior is constructed from either the
            prior file or the trigger time. If False (used for the overview
            page where a single time-prior doesn't make sense), this isn't
            added to the prior

        Returns
        -------
        prior: bilby.core.prior.PriorDict
            The generated prior
        """
        if self.default_prior in self.combined_default_prior_dicts.keys():
            prior_class = self.combined_default_prior_dicts[self.default_prior]
        elif "." in self.default_prior:
            prior_class = get_function_from_string_path(self.default_prior)
        else:
            raise ValueError("Unable to set prior: default_prior unavailable")

        if self.prior_dict is not None:
            priors = prior_class(dictionary=self.prior_dict)
        else:
            priors = prior_class(filename=self.prior_file)

        priors = self._update_default_prior_to_sky_frame_parameters(priors)

        if self.time_parameter in priors:
            logger.debug(f"Using {self.time_parameter} prior from prior_file")
        elif add_time:
            priors[self.time_parameter] = self.create_time_prior()
        else:
            logger.debug("No time prior available or requested")

        if self.calibration_model is not None:
            priors.update(self.calibration_prior)
        return priors

    def _get_default_sky_priors(self):
        return bilby.core.prior.PriorDict(
            dict(
                dec=bilby.core.prior.Cosine(name="dec"),
                ra=bilby.core.prior.Uniform(
                    name="ra", minimum=0, maximum=2 * np.pi, boundary="periodic"
                ),
            )
        )

    def _priors_contains_default_sky_prior(self, priors):
        sky_priors = self._get_default_sky_priors()
        for key in sky_priors:
            if sky_priors[key] != priors.get(key, None):
                return False
        return True

    def _update_default_prior_to_sky_frame_parameters(self, priors):
        if (
            self._priors_contains_default_sky_prior(priors)
            and self.reference_frame != "sky"
        ):
            if "ra" in priors:
                del priors["ra"]
            if "dec" in priors:
                del priors["dec"]
            if "azimuth" not in priors:
                priors["azimuth"] = bilby.core.prior.Uniform(
                    minimum=0,
                    maximum=2 * np.pi,
                    latex_label="$\\epsilon$",
                    boundary="periodic",
                )
            if "zenith" not in priors:
                priors["zenith"] = bilby.core.prior.Sine(latex_label="$\\kappa$")
        return priors

    @property
    def calibration_prior(self):
        if self.calibration_model is None:
            return None
        if getattr(self, "_calibration_prior", None) is not None:
            return self._calibration_prior
        self._calibration_prior = bilby.core.prior.PriorDict()
        if self.calibration_model.lower() == "cubicspline":
            for det in self.detectors:
                if (
                    self.spline_calibration_envelope_dict is not None
                    and det in self.spline_calibration_envelope_dict
                ):
                    fname = resolve_filename_with_transfer_fallback(
                        self.spline_calibration_envelope_dict[det]
                    )
                    logger.info(f"Creating calibration prior for {det} from {fname}")
                    self._calibration_prior.update(
                        bilby.gw.prior.CalibrationPriorDict.from_envelope_file(
                            fname,
                            minimum_frequency=self.minimum_frequency_dict[det],
                            maximum_frequency=self.maximum_frequency_dict[det],
                            n_nodes=self.spline_calibration_nodes,
                            label=det,
                            boundary=self.calibration_prior_boundary,
                            correction_type=self.calibration_correction_type[det],
                        )
                    )
                elif (
                    det in self.spline_calibration_amplitude_uncertainty_dict
                    and det in self.spline_calibration_phase_uncertainty_dict
                ):
                    logger.debug(
                        "Creating calibration prior for {} from "
                        "provided constant uncertainty values.".format(det)
                    )
                    self._calibration_prior.update(
                        bilby.gw.prior.CalibrationPriorDict.constant_uncertainty_spline(
                            amplitude_sigma=self.spline_calibration_amplitude_uncertainty_dict[
                                det
                            ],
                            phase_sigma=self.spline_calibration_phase_uncertainty_dict[
                                det
                            ],
                            minimum_frequency=self.minimum_frequency_dict[det],
                            maximum_frequency=self.maximum_frequency_dict[det],
                            n_nodes=self.spline_calibration_nodes,
                            label=det,
                        )
                    )
                else:
                    logger.warning(f"No calibration information for {det}")
        elif self.calibration_model.lower() == "precomputed":
            for det in self.detectors:
                self._calibration_prior[
                    f"recalib_index_{det}"
                ] = bilby.core.prior.Categorical(1000)
        return self._calibration_prior

    @property
    def calibration_model(self):
        return getattr(self, "_calibration_model", None)

    @calibration_model.setter
    def calibration_model(self, calibration_model):
        if calibration_model is not None:
            logger.debug(f"Setting calibration_model={calibration_model}")
            self._calibration_model = calibration_model
        else:
            logger.debug(
                "No calibration_model model provided, calibration "
                "marginalization will not be used"
            )
            self._calibration_model = None

    @property
    def calibration_lookup_table(self):
        return getattr(self, "_calibration_lookup_table", None)

    @calibration_lookup_table.setter
    def calibration_lookup_table(self, lookup):
        if isinstance(lookup, str):
            lookup = convert_string_to_dict(lookup)
        self._calibration_lookup_table = lookup

    @property
    def likelihood(self):
        self.search_priors = self.priors.copy()

        likelihood_kwargs = dict(
            interferometers=self.interferometers,
            waveform_generator=self.waveform_generator,
            priors=self.search_priors,
            phase_marginalization=self.phase_marginalization,
            distance_marginalization=self.distance_marginalization,
            distance_marginalization_lookup_table=self.distance_marginalization_lookup_table,
            time_marginalization=self.time_marginalization,
            reference_frame=self.reference_frame,
            time_reference=self.time_reference,
            calibration_marginalization=self.calibration_marginalization,
            calibration_lookup_table=self.calibration_lookup_table,
            number_of_response_curves=self.number_of_response_curves,
        )
        relative_binning_kwargs = dict(
            fiducial_parameters=self.fiducial_parameters,
            update_fiducial_parameters=self.update_fiducial_parameters,
            epsilon=self.epsilon,
        )

        if getattr(self, "likelihood_lookup_table", None) is not None:
            logger.debug("Using internally loaded likelihood_lookup_table")
            likelihood_kwargs["distance_marginalization_lookup_table"] = getattr(
                self, "likelihood_lookup_table"
            )

        if self.likelihood_type in ["GravitationalWaveTransient", "zero"]:
            Likelihood = bilby.gw.likelihood.GravitationalWaveTransient
            likelihood_kwargs.update(jitter_time=self.jitter_time)

        elif self.likelihood_type == "ROQGravitationalWaveTransient":
            Likelihood = bilby.gw.likelihood.ROQGravitationalWaveTransient
            likelihood_kwargs.update(
                self.roq_likelihood_kwargs, jitter_time=self.jitter_time
            )
        elif self.likelihood_type == "RelativeBinningGravitationalWaveTransient":
            Likelihood = bilby.gw.likelihood.RelativeBinningGravitationalWaveTransient
            likelihood_kwargs.update(relative_binning_kwargs)
        elif self.likelihood_type == "MBGravitationalWaveTransient":
            Likelihood = bilby.gw.likelihood.MBGravitationalWaveTransient
            likelihood_kwargs.update(self.multiband_likelihood_kwargs)
            likelihood_kwargs.update(self.extra_likelihood_kwargs)
        elif "." in self.likelihood_type:
            split_path = self.likelihood_type.split(".")
            module = ".".join(split_path[:-1])
            likelihood_class = split_path[-1]
            Likelihood = getattr(import_module(module), likelihood_class)
            likelihood_kwargs.update(self.extra_likelihood_kwargs)
            if "roq" in self.likelihood_type.lower():
                likelihood_kwargs.update(self.roq_likelihood_kwargs)
            elif "relative" in self.likelihood_type.lower():
                likelihood_kwargs.update(relative_binning_kwargs)
            if "multiband" in self.likelihood_type.lower():
                likelihood_kwargs.update(self.multiband_likelihood_kwargs)
        else:
            raise ValueError(f"Unknown Likelihood class {self.likelihood_type}")

        likelihood_kwargs = {
            key: likelihood_kwargs[key]
            for key in likelihood_kwargs
            if key in inspect.getfullargspec(Likelihood.__init__).args
        }

        logger.debug(
            f"Initialise likelihood {Likelihood} with kwargs: \n{likelihood_kwargs}"
        )

        if likelihood_kwargs.get("update_fiducial_parameters", False):
            if self.calibration_prior is not None:
                for key in self.calibration_prior:
                    self.search_priors[key] = self.calibration_prior[key].rescale(0.5)

        likelihood = Likelihood(**likelihood_kwargs)

        if likelihood_kwargs.get("update_fiducial_parameters", False):
            if self.calibration_prior is not None:
                for key in self.calibration_prior:
                    self.search_priors[key] = self.calibration_prior[key]

        # If requested, use a zero likelihood: for testing purposes
        if self.likelihood_type == "zero":
            logger.debug("Using a ZeroLikelihood")
            likelihood = bilby.core.likelihood.ZeroLikelihood(likelihood)

        return likelihood

    @property
    def extra_likelihood_kwargs(self):
        return self._extra_likelihood_kwargs

    @extra_likelihood_kwargs.setter
    def extra_likelihood_kwargs(self, likelihood_kwargs):
        if isinstance(likelihood_kwargs, str):
            likelihood_kwargs = utils.convert_string_to_dict(likelihood_kwargs)
        elif likelihood_kwargs is None:
            likelihood_kwargs = dict()
        elif not isinstance(likelihood_kwargs, dict):
            raise TypeError(
                f"Type {type(likelihood_kwargs)} not understood for likelihood kwargs."
            )
        for key in list(likelihood_kwargs.keys()):
            likelihood_kwargs[key.replace("-", "_")] = likelihood_kwargs.pop(key)
        forbidden_keys = [
            "interferometers",
            "waveform_generator",
            "priors",
            "distance_marginalization",
            "time_marginalization",
            "phase_marginalization",
            "jitter_time",
            "distance_marginalization_lookup_table",
            "reference_frame",
            "time_reference",
        ]
        if "roq" in self.likelihood_type.lower():
            forbidden_keys += ["weights", "roq_params", "roq_scale_factor"]
        for key in forbidden_keys:
            if key in likelihood_kwargs:
                raise KeyError(
                    "{} should be passed through named argument not likelihood_kwargs".format(
                        key
                    )
                )
        self._extra_likelihood_kwargs = likelihood_kwargs

    @property
    def roq_likelihood_kwargs(self):
        kwargs = dict(roq_scale_factor=self.roq_scale_factor)
        if hasattr(self, "likelihood_roq_params"):
            kwargs["roq_params"] = self.likelihood_roq_params
        elif self.roq_folder is not None:
            kwargs["roq_params"] = np.genfromtxt(
                f"{self.roq_folder}/params.dat", names=True
            )

        if hasattr(self, "likelihood_roq_weights"):
            kwargs["weights"] = self.likelihood_roq_weights
        elif "weight_file" in self.meta_data:
            kwargs["weights"] = self.meta_data["weight_file"]
            logger.debug(f"Loading ROQ weights from {kwargs['weights']}")
        elif self.roq_folder is not None:
            kwargs["linear_matrix"] = np.load(f"{self.roq_folder}/B_linear.npy").T
            kwargs["quadratic_matrix"] = np.load(f"{self.roq_folder}/B_quadratic.npy").T
        else:
            kwargs["linear_matrix"] = self.roq_linear_matrix
            kwargs["quadratic_matrix"] = self.roq_quadratic_matrix
        return kwargs

    @property
    def multiband_likelihood_kwargs(self):
        if hasattr(self, "likelihood_multiband_weights"):
            weights = self.likelihood_multiband_weights
        elif "weight_file" in self.meta_data:
            weights = self.meta_data["weight_file"]
            logger.info(f"Loading multiband weights from {weights}")
        else:
            weights = None
            logger.info("No multiband weights found, these will be calculated now")
        return dict(weights=weights)

    @property
    def parameter_conversion(self):
        cf = self.conversion_function

        _lookups = dict(noconvert=bilby.gw.conversion.identity_map_conversion)

        if isinstance(cf, str) and cf.lower() in _lookups:
            logger.info(f"Using conversion function {cf} from lookups")
            return _lookups[cf.lower()]
        elif cf is not None:
            logger.info(f"Using user-specified conversion_function {cf}")
            return get_function_from_string_path(cf)
        elif "binary_neutron_star" in self._frequency_domain_source_model:
            logger.info(
                "Using conversion_function convert_to_lal_binary_neutron_star_parameters"
            )
            return bilby.gw.conversion.convert_to_lal_binary_neutron_star_parameters
        elif "binary_black_hole" in self._frequency_domain_source_model:
            logger.info(
                "Using conversion_function convert_to_lal_binary_black_hole_parameters"
            )
            return bilby.gw.conversion.convert_to_lal_binary_black_hole_parameters
        else:
            logger.info("No conversion function")
            return None

    @property
    def waveform_generator(self):
        waveform_generator_class_ctor_arguments = (
            self.get_default_waveform_generator_class_ctor_arguments()
        )
        waveform_arguments = self.get_default_waveform_arguments()

        if "ROQ" in self.likelihood_type:
            if self.roq_folder is not None:
                logger.info(
                    "Using {} likelihood with roq-folder={}".format(
                        self.likelihood_type, self.roq_folder
                    )
                )
                freq_nodes_linear = np.load(self.roq_folder + "/fnodes_linear.npy")
                freq_nodes_quadratic = np.load(
                    self.roq_folder + "/fnodes_quadratic.npy"
                )
                freq_nodes_linear *= self.roq_scale_factor
                freq_nodes_quadratic *= self.roq_scale_factor

                waveform_arguments["frequency_nodes_linear"] = freq_nodes_linear
                waveform_arguments["frequency_nodes_quadratic"] = freq_nodes_quadratic

            _ = waveform_arguments.pop("minimum_frequency", None)
            _ = waveform_arguments.pop("maximum_frequency", None)
            fdsm = self.bilby_roq_frequency_domain_source_model
        elif "relative" in self.likelihood_type.lower():
            fdsm = self.bilby_relative_binning_frequency_domain_source_model
        elif self.is_likelihood_multiband:
            _ = waveform_arguments.pop("minimum_frequency", None)
            _ = waveform_arguments.pop("maximum_frequency", None)
            fdsm = self.bilby_multiband_frequency_domain_source_model
        else:
            fdsm = self.bilby_frequency_domain_source_model

        waveform_generator = self.waveform_generator_class(
            **waveform_generator_class_ctor_arguments,
            frequency_domain_source_model=fdsm,
            sampling_frequency=self.interferometers.sampling_frequency,
            duration=self.interferometers.duration,
            parameter_conversion=self.parameter_conversion,
            start_time=self.interferometers.start_time,
            waveform_arguments=waveform_arguments,
        )

        return waveform_generator

    @property
    def waveform_generator_class(self):
        return self._waveform_generator_class

    @waveform_generator_class.setter
    def waveform_generator_class(self, class_name):
        if "." in class_name:
            module = ".".join(class_name.split(".")[:-1])
            class_name = class_name.split(".")[-1]
        else:
            module = "bilby.gw.waveform_generator"
        wfg_class = getattr(import_module(module), class_name, None)
        if wfg_class is not None:
            self._waveform_generator_class = wfg_class
        else:
            raise BilbyPipeError(
                f"Cannot import waveform generator class {module}.{class_name}"
            )

    @property
    def parameter_generation(self):
        gf = self.generation_function

        _lookups = dict(noconvert=bilby.gw.conversion.identity_map_generation)

        if isinstance(gf, str) and gf.lower() in _lookups:
            logger.info(f"Using generation function {gf} from lookups")
            return _lookups[gf.lower()]
        elif gf is not None:
            logger.info(f"Using user-specified generation {gf}")
            return get_function_from_string_path(self.generation_function)
        elif "binary_neutron_star" in self._frequency_domain_source_model:
            logger.info("Using generation_function generate_all_bns_parameters")
            return bilby.gw.conversion.generate_all_bns_parameters
        elif "binary_black_hole" in self._frequency_domain_source_model:
            logger.info("Using generation_function generate_all_bbh_parameters")
            return bilby.gw.conversion.generate_all_bbh_parameters
        else:
            logger.info("No conversion function")
            return None

    @property
    def summarypages_arguments(self):
        return self._summarypages_arguments

    @summarypages_arguments.setter
    def summarypages_arguments(self, summarypages_arguments):
        if summarypages_arguments is None:
            self._summarypages_arguments = None
            return
        string = summarypages_arguments
        if "{" in string and "}" in string:
            self._summarypages_arguments = convert_string_to_dict(string)
        else:
            self._summarypages_arguments = summarypages_arguments

    @property
    def postprocessing_arguments(self):
        return self._postprocessing_arguments

    @postprocessing_arguments.setter
    def postprocessing_arguments(self, postprocessing_arguments):
        if postprocessing_arguments in [None, "None"]:
            self._postprocessing_arguments = None
        elif postprocessing_arguments == [None]:
            self._postprocessing_arguments = None
        elif isinstance(postprocessing_arguments, str):
            self._postprocessing_arguments = postprocessing_arguments.split(" ")
        else:
            self._postprocessing_arguments = postprocessing_arguments

    @property
    def sampler(self):
        return self._sampler

    @sampler.setter
    def sampler(self, sampler):
        """Setter for the sampler"""

        if not isinstance(sampler, str):
            raise BilbyPipeError("Sampler must be a single string")
        elif sampler in bilby.core.sampler.IMPLEMENTED_SAMPLERS:
            self._sampler = sampler
        else:
            raise BilbyPipeError(f"Requested sampler {sampler} not implemented")

    @property
    def sampler_kwargs(self):
        return self._sampler_kwargs

    @sampler_kwargs.setter
    def sampler_kwargs(self, sampler_kwargs):
        # Set up the default choices
        if self.sampler == "dynesty":
            self._sampler_kwargs = SAMPLER_SETTINGS["DynestyDefault"]
        elif self.sampler == "bilby_mcmc":
            self._sampler_kwargs = SAMPLER_SETTINGS["BilbyMCMCDefault"]
        else:
            self._sampler_kwargs = dict()

        if sampler_kwargs is not None:
            if sampler_kwargs.lower() in ["default", "dynestydefault"]:
                self._sampler_kwargs.update(SAMPLER_SETTINGS["DynestyDefault"])
            elif sampler_kwargs.lower() == "bilbymcmcdefault":
                self._sampler_kwargs.update(SAMPLER_SETTINGS["BilbyMCMCDefault"])
            elif sampler_kwargs.lower() == "fasttest":
                self._sampler_kwargs.update(SAMPLER_SETTINGS["FastTest"])
            else:
                self._sampler_kwargs.update(
                    convert_string_to_dict(sampler_kwargs, "sampler-kwargs")
                )
        else:
            self._sampler_kwargs = dict()

        self.update_sampler_kwargs_conditional_on_request_cpus()

    def update_sampler_kwargs_conditional_on_request_cpus(self):
        """If the user adds request-cpu >1, update npool in the sampler kwargs"""
        # Only run if request_cpus > 1
        if self.request_cpus > 1:
            self._sampler_kwargs.update(npool=self.request_cpus)

    def pretty_print_prior(self):
        try:
            prior = self._get_priors(add_time=False)
        except Exception as e:
            raise BilbyPipeError(
                get_colored_string(f"Unable to parse prior, exception raised {e}")
            )
        pp = pretty_print_dictionary(prior)
        logger.info(f"Input prior = {pp}")

    @property
    def conda_env(self):
        return self._conda_env

    @conda_env.setter
    def conda_env(self, conda_env):
        if conda_env is None:
            self._conda_env = None
            self._conda_path = None
        elif os.path.isdir(conda_env):
            # conda_env is a path
            self._conda_path = conda_env
            self._conda_env = conda_env.rstrip("/").split("/")
        elif (
            _conda_path := self._determine_conda_path_from_env(conda_env)
        ) is not None:
            self._conda_env = conda_env
            self._conda_path = _conda_path
        elif self.container is not None:
            self._conda_env = conda_env
            self._conda_path = conda_env
        else:
            raise BilbyPipeError(
                f"conda_env={conda_env} not recognised as an environment"
            )

    @staticmethod
    def _determine_conda_path_from_env(conda_env):
        run_out = subprocess.run(["conda", "env", "list"], capture_output=True)
        elist = run_out.stdout.decode().split("\n")
        for line in elist:
            line_split = line.split()
            if (len(line_split) > 0) and (conda_env == line_split[0]):
                _conda_path = line_split[-1]
                if line_split[1] != "*":
                    logger.warning(
                        get_colored_string(
                            "You are running bilby_pipe from a different environment"
                            " than the run-time environment. This is not recommended"
                            " and could cause unexpected behaviour"
                        )
                    )
                return _conda_path

    @property
    def psd_dict(self):
        return self._psd_dict

    @psd_dict.setter
    def psd_dict(self, psd_dict):
        if psd_dict is not None:
            self._psd_dict = convert_string_to_dict(psd_dict, "psd-dict")
            self._validate_psd_dict()
        else:
            logger.debug("psd-dict set to None")
            self._psd_dict = None

    def _validate_psd_dict(self):
        """
        Verify that all detectors are listed in the PSD dict and that they
        correspond to resolvable PSDs. Note that `None` is a special case that
        indicates the default PSD should be used.
        """
        for det in self.detectors:
            if det not in self.psd_dict:
                raise BilbyPipeError(f"Detector {det} not listed in the psd-dict")

        for det, psd_file in self.psd_dict.items():
            if psd_file is None:
                continue
            elif psd_file == "None":
                self.psd_dict[det] = None
            elif filename := resolve_filename_with_transfer_fallback(psd_file):
                self.psd_dict[det] = filename
            elif check_if_psd_is_from_built_in(psd_file):
                continue
            else:
                raise BilbyPipeError(
                    f"PSD file {psd_file} for detector {det} does not exist"
                )

    @property
    def additional_transfer_paths(self):
        return self._additional_transfer_paths

    @additional_transfer_paths.setter
    def additional_transfer_paths(self, paths):
        if isinstance(paths, list):
            self._additional_transfer_paths = paths
        if paths is None or paths == [None]:
            self._additional_transfer_paths = list()

    @property
    def is_likelihood_multiband(self):
        return (
            self.likelihood_type == "MBGravitationalWaveTransient"
            or "multiband" in self.likelihood_type.lower()
        )

    @property
    def reweighting_configuration(self):
        return getattr(self, "_reweighting_configuration", None)

    @reweighting_configuration.setter
    def reweighting_configuration(self, conf):
        if isinstance(conf, str):
            if os.path.exists(conf):
                with open(conf, "r") as ff:
                    conf = json.load(ff)
            else:
                try:
                    conf = convert_string_to_dict(conf)
                except (ValueError, SyntaxError):
                    logger.error("Cannot parse reweighting configuration")
                    raise
        self._reweighting_configuration = conf

    @property
    def data_dict(self):
        return self._data_dict

    @data_dict.setter
    def data_dict(self, data_dict):
        """
        Identify the appropriate data files from the specified json
        formatted string.

        To support :code:`HTCondor` file transfer, we also look for any
        specified paths in the local directory.

        As a final fallback we look for any frame files in the local directory
        like, e.g., :code:`H*.gwf`, note that this means :code:`HDF5` files
        are likely not supported with file transfer.
        """
        if isinstance(data_dict, str):
            data_dict = convert_string_to_dict(data_dict, "data-dict")
        if getattr(self, "transfer_files", False):
            data = dict()
            if data_dict is not None:
                data.update(data_dict)
            for det in self.detectors:
                frames = list()
                if det in data:
                    source = data[det]
                    if isinstance(source, str) and "*" in source:
                        frames = glob.glob(source)
                    elif isinstance(source, str):
                        frames = [source]
                    elif isinstance(source, (list, tuple, set)):
                        frames = source
                    else:
                        raise TypeError(
                            "data-dict entries should be str of list of str"
                        )
                    frames = [
                        resolve_filename_with_transfer_fallback(frame)
                        for frame in frames
                    ]
                    frames = [frame for frame in frames if frame is not None]
                if len(frames) == 0:
                    frames = glob.glob(f"{det[0]}*.gwf")
                    if len(frames) > 0:
                        logger.warning(
                            f"Found local data files {frames} not specified in "
                            "the data dict, this behaviour is not recommended."
                        )
                if len(frames) > 0:
                    data[det] = frames
            self._data_dict = data
        elif data_dict is None:
            logger.debug("data-dict set to None")
            self._data_dict = None
        elif isinstance(data_dict, dict):
            self._data_dict = data_dict
        else:
            raise BilbyPipeError(f"Input data-dict={data_dict} not understood")

    @property
    def channel_dict(self):
        return self._channel_dict

    @channel_dict.setter
    def channel_dict(self, channel_dict):
        if channel_dict is not None:
            self._channel_dict = convert_string_to_dict(channel_dict, "channel-dict")
        else:
            logger.debug("channel-dict set to None")
            self._channel_dict = None

    @property
    def fetch_open_data_kwargs(self):
        return self._fetch_open_data_kwargs

    @fetch_open_data_kwargs.setter
    def fetch_open_data_kwargs(self, fetch_open_data_kwargs):
        if fetch_open_data_kwargs is not None:
            self._fetch_open_data_kwargs = convert_string_to_dict(
                fetch_open_data_kwargs, "fetch-open-data-kwargs"
            )
        else:
            logger.debug("fetch-open-data-kwargs set to None")
            self._fetch_open_data_kwargs = None

    @property
    def frame_type_dict(self):
        return self._frame_type_dict

    @frame_type_dict.setter
    def frame_type_dict(self, frame_type_dict):
        if frame_type_dict is not None:
            self._frame_type_dict = convert_string_to_dict(
                frame_type_dict, "frame-type-dict"
            )
        else:
            logger.debug("frame-type-dict set to None")
            self._frame_type_dict = None

    @property
    def psd_length(self):
        """Integer number of durations to use for generating the PSD"""
        return self._psd_length

    @psd_length.setter
    def psd_length(self, psd_length):
        if isinstance(psd_length, int):
            self._psd_length = psd_length
            self.psd_duration = psd_length * self.duration

        else:
            raise BilbyPipeError(f"Unable to set psd_length={psd_length}")

    @property
    def psd_duration(self):
        return self._psd_duration

    @psd_duration.setter
    def psd_duration(self, psd_duration):
        MAXIMUM = self.psd_maximum_duration
        if psd_duration <= MAXIMUM:
            self._psd_duration = psd_duration
            logger.debug(
                f"PSD duration set to {psd_duration}s, {self.psd_length}x the duration {self.duration}s"
            )
        else:
            self._psd_duration = MAXIMUM
            logger.info(
                f"Requested PSD duration {psd_duration}={self.psd_length}x{self.duration} exceeds "
                f"allowed maximum {MAXIMUM}. Setting psd_duration = {self.psd_duration}"
            )

    @property
    def psd_start_time(self):
        """The PSD start time relative to segment start time"""
        if self._psd_start_time is not None:
            return self._psd_start_time
        elif self.trigger_time is not None:
            psd_start_time = -self.psd_duration
            logger.info(
                f"Using default PSD start time {psd_start_time} relative to start time"
            )
            return psd_start_time
        else:
            raise BilbyPipeError("PSD start time not set")

    @psd_start_time.setter
    def psd_start_time(self, psd_start_time):
        if psd_start_time is None:
            self._psd_start_time = None
        else:
            self._psd_start_time = psd_start_time
            logger.info(
                f"PSD start-time set to {self._psd_start_time} relative to segment start time"
            )
