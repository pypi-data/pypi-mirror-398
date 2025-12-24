#!/usr/bin/env python
"""
This module provides the code for the top-level interface for
:code:`bilby_pipe` executable.
"""

import importlib
import json
import os

import numpy as np
import pandas as pd

from .create_injections import create_injection_file
from .input import Input
from .job_creation import generate_dag
from .parser import create_parser
from .utils import (
    BilbyPipeError,
    convert_string_to_dict,
    get_colored_string,
    get_command_line_arguments,
    get_outdir_name,
    log_version_information,
    logger,
    parse_args,
    request_memory_generation_lookup,
)


class MainInput(Input):
    """An object to hold all the inputs to bilby_pipe"""

    def __init__(self, args, unknown_args, perform_checks=True):
        super().__init__(args, unknown_args, print_msg=False)

        self.known_args = args
        self.unknown_args = unknown_args
        self.ini = args.ini
        self.submit = args.submit
        self.condor_job_priority = args.condor_job_priority
        self.create_summary = args.create_summary
        self.scitoken_issuer = args.scitoken_issuer
        self.container = args.container

        self.cosmology = args.cosmology

        self.outdir = args.outdir
        self.label = args.label
        self.log_directory = args.log_directory
        self.accounting = args.accounting
        self.accounting_user = args.accounting_user
        self.sampler = args.sampler
        self.sampling_seed = args.sampling_seed
        self.detectors = args.detectors
        self.coherence_test = args.coherence_test
        self.data_dict = args.data_dict
        self.channel_dict = args.channel_dict
        self.frame_type_dict = args.frame_type_dict
        self.data_find_url = args.data_find_url
        self.data_find_urltype = args.data_find_urltype
        self.n_parallel = args.n_parallel
        self.transfer_files = args.transfer_files
        self.additional_transfer_paths = args.additional_transfer_paths
        self.osg = args.osg
        self.desired_sites = args.desired_sites
        self.analysis_executable = args.analysis_executable
        self.analysis_executable_parser = args.analysis_executable_parser
        self.result_format = args.result_format
        self.final_result = args.final_result
        self.final_result_nsamples = args.final_result_nsamples

        self.webdir = args.webdir
        self.email = args.email
        self.notification = args.notification
        self.queue = args.queue
        self.existing_dir = args.existing_dir

        self.scheduler = args.scheduler
        self.scheduler_args = args.scheduler_args
        self.scheduler_module = args.scheduler_module
        self.scheduler_env = args.scheduler_env
        self.scheduler_analysis_time = args.scheduler_analysis_time
        self.disable_hdf5_locking = args.disable_hdf5_locking
        self.environment_variables = args.environment_variables
        self.getenv = args.getenv

        self.waveform_approximant = args.waveform_approximant

        self.time_reference = args.time_reference
        self.reference_frame = args.reference_frame
        self.likelihood_type = args.likelihood_type
        self.duration = args.duration
        self.phase_marginalization = args.phase_marginalization
        self.prior_file = args.prior_file
        self.prior_dict = args.prior_dict
        self.default_prior = args.default_prior
        self.minimum_frequency = args.minimum_frequency
        self.enforce_signal_duration = args.enforce_signal_duration

        self.run_local = args.local
        self.generation_pool = args.generation_pool
        self.local_generation = args.local_generation
        self.local_plot = args.local_plot

        self.post_trigger_duration = args.post_trigger_duration

        self.ignore_gwpy_data_quality_check = args.ignore_gwpy_data_quality_check
        self.trigger_time = args.trigger_time
        self.deltaT = args.deltaT
        self.gps_tuple = args.gps_tuple
        self.gps_file = args.gps_file
        self.timeslide_file = args.timeslide_file
        self.gaussian_noise = args.gaussian_noise
        self.zero_noise = args.zero_noise
        self.n_simulation = args.n_simulation

        self.injection = args.injection
        self.injection_numbers = args.injection_numbers
        self.injection_file = args.injection_file
        self.injection_dict = args.injection_dict
        self.injection_waveform_arguments = args.injection_waveform_arguments
        self.injection_waveform_approximant = args.injection_waveform_approximant
        self.injection_frequency_domain_source_model = (
            args.injection_frequency_domain_source_model
        )
        self.injection_waveform_generator_class_ctor_args = (
            args.injection_waveform_generator_constructor_dict
        )
        self.generation_seed = args.generation_seed

        self.request_disk = args.request_disk
        self.request_memory = args.request_memory
        self.request_memory_generation = args.request_memory_generation
        self.request_cpus = args.request_cpus
        self.sampler_kwargs = args.sampler_kwargs
        self.mpi_samplers = ["pymultinest"]
        self.use_mpi = (self.sampler in self.mpi_samplers) and (self.request_cpus > 1)

        # Set plotting options when need the plot node
        self.plot_node_needed = False
        for plot_attr in [
            "calibration",
            "corner",
            "marginal",
            "skymap",
            "waveform",
        ]:
            attr = f"plot_{plot_attr}"
            setattr(self, attr, getattr(args, attr))
            if getattr(self, attr):
                self.plot_node_needed = True

        # Set all other plotting options
        for plot_attr in [
            "trace",
            "data",
            "injection",
            "spectrogram",
            "format",
        ]:
            attr = f"plot_{plot_attr}"
            setattr(self, attr, getattr(args, attr))

        self.postprocessing_executable = args.postprocessing_executable
        self.postprocessing_arguments = args.postprocessing_arguments
        self.single_postprocessing_executable = args.single_postprocessing_executable
        self.single_postprocessing_arguments = args.single_postprocessing_arguments

        self.summarypages_arguments = args.summarypages_arguments

        self.psd_dict = args.psd_dict
        self.psd_maximum_duration = args.psd_maximum_duration
        self.psd_length = args.psd_length
        self.psd_fractional_overlap = args.psd_fractional_overlap
        self.psd_start_time = args.psd_start_time
        self.spline_calibration_envelope_dict = args.spline_calibration_envelope_dict

        if perform_checks:
            self.check_source_model(args)
            self.check_calibration_prior_boundary(args)
            self.check_cpu_parallelisation()
            self.check_accounting()
            if self.injection:
                self.check_injection()

        self.extra_lines = []
        self.requirements = []

    @property
    def ini(self):
        return self._ini

    @ini.setter
    def ini(self, ini):
        if os.path.isfile(ini) is False:
            raise FileNotFoundError(f"No ini file {ini} found")
        self._ini = os.path.relpath(ini)

    @property
    def notification(self):
        return self._notification

    @notification.setter
    def notification(self, notification):
        valid_settings = ["Always", "Complete", "Error", "Never"]
        if notification in valid_settings:
            self._notification = notification
        else:
            raise BilbyPipeError(
                "'{}' is not a valid notification setting. "
                "Valid settings are {}.".format(notification, valid_settings)
            )

    @property
    def initialdir(self):
        return os.getcwd()

    @property
    def n_simulation(self):
        return self._n_simulation

    @n_simulation.setter
    def n_simulation(self, n_simulation):
        logger.debug(f"Setting n_simulation={n_simulation}")
        if isinstance(n_simulation, int) and n_simulation >= 0:
            self._n_simulation = n_simulation
        elif n_simulation is None:
            self._n_simulation = 0
        else:
            raise BilbyPipeError(f"Input n_simulation={n_simulation} not understood")

    @property
    def analysis_executable(self):
        return self._analysis_executable

    @analysis_executable.setter
    def analysis_executable(self, analysis_executable):
        if analysis_executable:
            self._analysis_executable = analysis_executable
        else:
            self._analysis_executable = "bilby_pipe_analysis"

    @property
    def request_disk(self):
        return self._request_disk

    @request_disk.setter
    def request_disk(self, request_disk):
        self._request_disk = f"{request_disk}GB"
        self._request_disk_in_GB = float(request_disk)
        logger.debug(f"Setting analysis request_disk={self._request_disk}")
        self._request_disk = f"{request_disk}GB"

    @property
    def request_memory(self):
        return self._request_memory

    @request_memory.setter
    def request_memory(self, request_memory):
        self._request_memory = f"{request_memory}GB"
        self._request_memory_in_GB = request_memory
        logger.debug(f"Setting analysis request_memory={self._request_memory}")

    @property
    def request_memory_generation(self):
        return self._request_memory_generation

    @request_memory_generation.setter
    def request_memory_generation(self, request_memory_generation):
        if request_memory_generation is None:
            roq = "roq" in self.likelihood_type.lower()
            request_memory_generation = request_memory_generation_lookup(
                self.duration, roq=roq
            )
        logger.debug(f"Setting request_memory_generation={request_memory_generation}GB")
        self._request_memory_generation = f"{request_memory_generation}GB"

    @property
    def request_cpus(self):
        return self._request_cpus

    @request_cpus.setter
    def request_cpus(self, request_cpus):
        logger.debug(f"Setting analysis request_cpus = {request_cpus}")
        self._request_cpus = request_cpus

    @property
    def use_mpi(self):
        return self._use_mpi

    @use_mpi.setter
    def use_mpi(self, use_mpi):
        if use_mpi:
            logger.debug(f"Turning on MPI for {self.sampler}")
        self._use_mpi = use_mpi

    @property
    def environment_variables(self):
        return self._environment_variables

    @environment_variables.setter
    def environment_variables(self, environment_variables):
        if environment_variables is None:
            self._environment_variables = dict()
        else:
            self._environment_variables = convert_string_to_dict(environment_variables)

    @property
    def getenv(self):
        return self._getenv

    @getenv.setter
    def getenv(self, getenv):
        if isinstance(getenv, list):
            self._getenv = getenv
        if getenv is None or getenv == [None]:
            self._getenv = list()

    @staticmethod
    def check_source_model(args):
        """Check the source model consistency with the approximant"""
        if "tidal" in args.waveform_approximant.lower():
            if "neutron_star" not in args.frequency_domain_source_model.lower():
                msg = [
                    "You appear to be using a tidal waveform with the",
                    f"{args.frequency_domain_source_model} source model.",
                    "You may want to use `frequency-domain-source-model=",
                    "lal_binary_neutron_star`.",
                ]
                logger.warning(get_colored_string("_".join(msg)))

    @staticmethod
    def check_calibration_prior_boundary(args):
        # List of recommendations: print warning if these are not adhered to
        recs = dict(bilby_mcmc=None, dynesty="reflective")
        suggested_boundary = recs.get(args.sampler, args.calibration_prior_boundary)
        if args.calibration_prior_boundary != suggested_boundary:
            msg = (
                "You have requested a calibration prior boundary "
                f"{args.calibration_prior_boundary}, but {suggested_boundary} "
                "is recommended."
            )
            logger.warning(get_colored_string(msg))

    def check_cpu_parallelisation(self):
        request_cpus = self.request_cpus
        npool = self.sampler_kwargs.get("npool", request_cpus)
        if request_cpus != npool:
            msg = (
                f"request-cpus={request_cpus}, but sampler_kwargs[npool]={npool}:"
                "this may cause inefficient performance"
            )
            logger.warning(get_colored_string(msg))

    def check_accounting(self):
        if self.accounting is None:
            logger.warning(
                "No accounting tag specified. If using IGWN computing resources"
                " please refer to https://computing.docs.ligo.org/guide/htcondor/accounting/"
            )
        else:
            try:
                purpose = self.accounting.split(".")[1]
                if purpose == "prod":
                    logger.info(
                        get_colored_string(
                            "Using a 'prod' accounting tag: please ensure this is intentional"
                        )
                    )
                pipeline = self.accounting.split(".")[-1]
                if pipeline != "bilby":
                    logger.info(
                        get_colored_string(
                            "Using a non-'bilby' accounting tag: please ensure this is intentional"
                        )
                    )
            except ValueError:
                logger.debug(
                    "Accounting tag does not follow the IGWN format. If you are using non-IGWN"
                    " resources this is fine, otherwise please refer to"
                    " https://computing.docs.ligo.org/guide/htcondor/accounting/"
                )
        logger.info(f"Using accounting tag: {self.accounting}")
        logger.info(f"Using accounting-user: {self.accounting_user}")

    def check_injection(self):
        """Check injection behaviour

        If injections are requested, either use the injection-dict,
        injection-file, or create an injection-file

        """
        default_injection_file_name = "{}/{}_injection_file.dat".format(
            self.data_directory, self.label
        )
        if self.injection_dict is not None:
            logger.debug(
                "Using injection dict from ini file {}".format(
                    json.dumps(self.injection_dict, indent=2)
                )
            )
        elif self.injection_file is not None:
            logger.debug(f"Using injection file {self.injection_file}")
        elif os.path.isfile(default_injection_file_name):
            # This is done to avoid overwriting the injection file
            logger.debug(f"Using injection file {default_injection_file_name}")
            self.injection_file = default_injection_file_name
        else:
            logger.debug("No injection file found, generating one now")

            if self.gps_file is not None or self.gps_tuple is not None:
                if self.n_simulation > 0 and self.n_simulation != len(self.gpstimes):
                    raise BilbyPipeError(
                        "gps_file/gps_tuple option and n_simulation are not matched"
                    )
                gpstimes = self.gpstimes
                n_injection = len(gpstimes)
            else:
                gpstimes = None
                n_injection = self.n_simulation

            if self.trigger_time is None:
                trigger_time_injections = 0
            else:
                trigger_time_injections = self.trigger_time

            create_injection_file(
                filename=default_injection_file_name,
                prior_file=self.prior_file,
                prior_dict=self.prior_dict,
                n_injection=n_injection,
                trigger_time=trigger_time_injections,
                deltaT=self.deltaT,
                gpstimes=gpstimes,
                duration=self.duration,
                post_trigger_duration=self.post_trigger_duration,
                generation_seed=self.generation_seed,
                extension="dat",
                default_prior=self.default_prior,
                cosmology=self.cosmology,
            )
            self.injection_file = default_injection_file_name

        # Check the gps_file has the sample length as number of simulation
        if self.gps_file is not None:
            if len(self.gpstimes) != len(self.injection_df):
                raise BilbyPipeError("Injection file length does not match gps_file")

        if self.n_simulation > 0:
            if self.n_simulation != len(self.injection_df):
                raise BilbyPipeError(
                    "n-simulation does not match the number of injections: "
                    "please check your ini file"
                )
        elif self.n_simulation == 0 and self.gps_file is None:
            self.n_simulation = len(self.injection_df)
            logger.debug(
                f"Setting n_simulation={self.n_simulation} to match injections"
            )

    @property
    def local_generation(self):
        return self.generation_pool == "local"

    @local_generation.setter
    def local_generation(self, local_generation):
        if local_generation:
            logger.warning(
                "The local-generation argument is deprecated. "
                "Use generation-pool=local instead."
            )
            self.generation_pool = "local"


def write_complete_config_file(parser, args, inputs, input_cls=MainInput):
    args_dict = vars(args).copy()
    for key, val in args_dict.items():
        if key == "label":
            continue
        if isinstance(val, str):
            if os.path.isfile(val) or os.path.isdir(val):
                setattr(args, key, os.path.abspath(val))
        if isinstance(val, list):
            if len(val) == 0:
                setattr(args, key, "[]")
            elif isinstance(val[0], str):
                setattr(args, key, f"[{', '.join(val)}]")
    args.sampler_kwargs = str(inputs.sampler_kwargs)
    args.submit = False
    parser.write_to_file(
        filename=inputs.complete_ini_file,
        args=args,
        overwrite=False,
        include_description=False,
    )

    # Verify that the written complete config is identical to the source config
    complete_args = parser.parse([inputs.complete_ini_file])
    complete_inputs = input_cls(complete_args, "", perform_checks=False)
    ignore_keys = ["scheduler_module", "submit"]
    differences = []
    for key, val in inputs.__dict__.items():
        if key in ignore_keys:
            continue
        if key not in complete_args:
            continue
        if isinstance(val, pd.DataFrame) and all(val == complete_inputs.__dict__[key]):
            continue
        if isinstance(val, np.ndarray) and all(
            np.array(val) == np.array(complete_inputs.__dict__[key])
        ):
            continue
        if isinstance(val, str) and os.path.isfile(val):
            # Check if it is relpath vs abspath
            if os.path.abspath(val) == os.path.abspath(complete_inputs.__dict__[key]):
                continue
        if val == complete_inputs.__dict__[key]:
            continue

        differences.append(key)

    if len(differences) > 0:
        for key in differences:
            print(key, f"{inputs.__dict__[key]} -> {complete_inputs.__dict__[key]}")
        raise BilbyPipeError(
            "The written config file {} differs from the source {} in {}".format(
                inputs.ini, inputs.complete_ini_file, differences
            )
        )
    else:
        logger.info(f"To see full configuration, check {inputs.complete_ini_file}")


def create_main_parser():
    _bilby_pipe_doc = """
    bilby_pipe is a command line tools for taking user input (as command line
    arguments or an ini file) and creating DAG files for submitting bilby parameter
    estimation jobs. To get started, write an ini file `config.ini` and run

    .. code-block:: console

        $ bilby_pipe config.ini

    Instruction for how to submit the job are printed in a log message. You can
    also specify extra arguments from the command line, e.g.

    .. code-block:: console

        $ bilby_pipe config.ini --submit

    will build and submit the job.
    """
    return create_parser(top_level=True, usage=_bilby_pipe_doc)


def main():
    """Top-level interface for bilby_pipe"""
    parser = create_main_parser()
    args, unknown_args = parse_args(get_command_line_arguments(), parser)

    if args.analysis_executable_parser is not None:
        # Alternative parser requested, reload args
        module = ".".join(args.analysis_executable_parser.split(".")[:-1])
        function = args.analysis_executable_parser.split(".")[-1]
        parser = getattr(importlib.import_module(module), function)()
        args, unknown_args = parse_args(get_command_line_arguments(), parser)

    # Check and sort outdir
    args.outdir = args.outdir.replace("'", "").replace('"', "")
    if args.overwrite_outdir is False:
        args.outdir = get_outdir_name(args.outdir)

    log_version_information()
    inputs = MainInput(args, unknown_args)
    write_complete_config_file(parser, args, inputs)
    generate_dag(inputs)

    if len(unknown_args) > 0:
        msg = get_colored_string(f"Unrecognized arguments {unknown_args}")
        logger.warning(msg)
