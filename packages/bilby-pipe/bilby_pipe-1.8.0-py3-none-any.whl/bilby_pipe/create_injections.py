#!/usr/bin/env python
"""
This a command line tool for the generation of injection files for consumption
by bilby_pipe. Injection files can be generated in a variety of formats, see
below, and are generated from a bilby-style prior_file.

Available formats: A dat file consists of a space-separated list of parameters
with a header; A json formatted file.

If a geocent_time prior is given in the file, this will be used to create the
time prior. Otherwise, the trigger-time & deltaT or gps-time and deltaT options
are used (see below).

As an example, this file
specifies a prior for precessing black hole binary systems

.. code-block:: python

   mass_1 = Uniform(name='mass_1', minimum=10, maximum=80)
   mass_2 = Uniform(name='mass_2', minimum=10, maximum=80)
   mass_ratio =  Constraint(name='mass_ratio', minimum=0.125, maximum=1)
   a_1 = Uniform(name='a_1', minimum=0, maximum=0.99)
   a_2 = Uniform(name='a_2', minimum=0, maximum=0.99)
   tilt_1 = Sine(name='tilt_1')
   tilt_2 = Sine(name='tilt_2')
   phi_12 = Uniform(name='phi_12', minimum=0, maximum=2 * np.pi)
   phi_jl = Uniform(name='phi_jl', minimum=0, maximum=2 * np.pi)
   luminosity_distance = PowerLaw(alpha=2, name='luminosity_distance', minimum=50, maximum=2000)
   dec = Cosine(name='dec')
   ra = Uniform(name='ra', minimum=0, maximum=2 * np.pi)
   theta_jn = Sine(name='theta_jn')
   psi =  Uniform(name='psi', minimum=0, maximum=np.pi)
   phase =  Uniform(name='phase', minimum=0, maximum=2 * np.pi)

Naming this file :code:`bbh.prior` and running

.. code-block:: console

   $ bilby_pipe_create_injection_file bbh.prior --n-injection 100 --generation-seed 1234 -f injections.json

Will produce a file :code:`injections.json` containing 100 random draws from the prior.
"""
import argparse
import json
import os
import sys

import pandas as pd

import bilby

from .input import Input
from .parser import StoreBoolean
from .utils import (
    BilbyPipeError,
    check_directory_exists_and_if_not_mkdir,
    get_geocent_time_with_uncertainty,
    logger,
    parse_args,
)


class BilbyPipeCreateInjectionsError(BilbyPipeError):
    def __init__(self, message):
        super().__init__(message)


def create_parser():
    """Generate a parser for the create_injections.py script

    Additional options can be added to the returned parser before calling
    `parser.parse_args` to generate the arguments`

    Returns
    -------
    parser: BilbyArgParser
        A parser with all the default options already added

    """
    parser = argparse.ArgumentParser(
        prog="bilby_pipe_create_injection_file",
        description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_arg(
        "prior_file",
        type=str,
        default=None,
        help="The prior file from which to generate injections",
    )
    parser.add("-f", "--filename", type=str, default="injection")
    parser.add_arg(
        "-e",
        "--extension",
        type=str,
        default="dat",
        choices=["json", "dat"],
        help="Prior file format",
    )
    parser.add_arg(
        "-n",
        "--n-injection",
        type=int,
        default=None,
        help="The number of injections to generate: not required if --gps-file is also given",
        required=False,
    )
    parser.add_arg(
        "-t",
        "--trigger-time",
        type=int,
        default=0,
        help=(
            "The trigger time to use for setting a geocent_time prior "
            "(default=0). Ignored if a geocent_time prior exists in the "
            "prior_file or --gps-file is given."
        ),
    )

    time_parser = parser.add_mutually_exclusive_group()
    time_parser.add_arg(
        "-g",
        "--gps-file",
        type=str,
        default=None,
        help=(
            "File containing segment GPS start times. This can be a multi-"
            "column file if (a) it is comma-separated and (b) the zeroth "
            "column contains the gps-times to use"
        ),
    )
    time_parser.add_arg(
        "--gps-tuple",
        type=str,
        default=None,
        help=(
            "Tuple of the (start, step, number) of GPS start times. For"
            " example, (10, 1, 3) produces the gps start times [10, 11, 12]."
            " If given, gps-file is ignored."
        ),
    )
    parser.add(
        "--deltaT",
        type=float,
        default=0.2,
        help=(
            "The symmetric width (in s) around the trigger time to"
            " search over the coalescence time. Ignored if a geocent_time prior"
            " exists in the prior_file"
        ),
    )
    parser.add_arg(
        "--post-trigger-duration",
        type=float,
        default=2,
        help=(
            "The post trigger duration (default=2s), used only in conjunction "
            "with --gps-file"
        ),
    )
    parser.add_arg(
        "--duration",
        type=float,
        default=4,
        help=(
            "The segment duration (default=4s), used only in conjunction with "
            "--gps-file"
        ),
    )
    parser.add_argument(
        "--minimum-frequency",
        type=float,
        default=None,
        help=(
            "The minimum frequency, this is needed when "
            "enforce-signal-duration is true."
        ),
    )
    parser.add(
        "-s",
        "--generation-seed",
        default=None,
        type=int,
        help="Random seed used during data generation",
    )
    parser.add(
        "--default-prior",
        default="BBHPriorDict",
        type=str,
        help="The name of the prior set to base the prior on. Can be one of"
        "[PriorDict, BBHPriorDict, BNSPriorDict, CalibrationPriorDict]",
    )
    parser.add(
        "--enforce-signal-duration",
        action=StoreBoolean,
        default=False,
        help=(
            "Whether to require that all signals fit within the segment duration. "
            "The signal duration is calculated using a post-Newtonian approximation."
        ),
    )
    return parser


class InjectionCreator(Input):
    """An object to hold inputs to create_injection for consistency"""

    def __init__(
        self,
        prior_file,
        prior_dict,
        default_prior,
        trigger_time,
        gpstimes,
        n_injection,
        generation_seed,
        deltaT=0.2,
        duration=4,
        post_trigger_duration=2,
        enforce_signal_duration=False,
        minimum_frequency=None,
        cosmology=None,
    ):
        self.prior_file = prior_file
        self.prior_dict = prior_dict
        self.check_prior()
        self.default_prior = default_prior
        self.trigger_time = trigger_time
        self.gpstimes = gpstimes
        self.deltaT = deltaT
        self.duration = duration
        self.post_trigger_duration = post_trigger_duration
        self.n_injection = n_injection
        self.generation_seed = generation_seed
        self.time_reference = "geocent"
        self.reference_frame = "sky"
        self.detectors = self.known_detectors
        self.minimum_frequency = minimum_frequency
        self.enforce_signal_duration = enforce_signal_duration
        self.cosmology = cosmology

        if self.gpstimes is not None and self.trigger_time not in [0, None]:
            raise BilbyPipeCreateInjectionsError(
                "Cannot parse both gpstimes and trigger_time"
            )

    def check_prior(self):
        """Ensures at least prior/prior_dict set"""
        if self.prior_file is None and self.prior_dict is None:
            raise BilbyPipeCreateInjectionsError("No prior_file or prior_dict given")

    @property
    def n_injection(self):
        """The number of injections parameters to be stored."""
        return self._n_injection

    @n_injection.setter
    def n_injection(self, n_injection):
        if self.gpstimes is not None:
            gps_n_injection = len(self.gpstimes)
            if n_injection is not None:
                logger.warning(
                    f"n-injection={gps_n_injection} given but gps_file/gps_tuple is also given,"
                    f" ignoring n-injection={n_injection}"
                )
            n_injection = gps_n_injection

        if isinstance(n_injection, int) is False or n_injection < 1:
            raise BilbyPipeCreateInjectionsError(
                f"n_injection={n_injection}, but must be a positive integer"
            )
        self._n_injection = n_injection

    def get_injection_dataframe(self):
        """Samples parameters from the prior into a dataframe"""
        inj_df = pd.DataFrame.from_dict(self.priors.sample(self.n_injection))
        if self.gpstimes is not None:
            geocent_times = []
            for start_time in self.gpstimes:
                geocent_time = get_geocent_time_with_uncertainty(
                    geocent_time=start_time
                    + self.duration
                    - self.post_trigger_duration,
                    uncertainty=self.deltaT / 2.0,
                )
                geocent_times.append(geocent_time)
            inj_df["geocent_time"] = geocent_times
        return inj_df

    @staticmethod
    def write_injection_dataframe(dataframe, filename, extension):
        """Writes dataframe into a file with a dat/json extension"""
        path, extension = get_full_path(filename, extension)
        if extension == "json":
            injections = dict(injections=dataframe)
            with open(path, "w") as file:
                json.dump(
                    injections, file, indent=2, cls=bilby.core.result.BilbyJsonEncoder
                )
        elif extension == "dat":
            dataframe.to_csv(path, index=False, header=True, sep=" ")
        else:
            raise BilbyPipeCreateInjectionsError(
                f"Extension {extension} not implemented"
            )
        logger.info(f"Created injection file {path}")

    def generate_injection_file(self, filepath, extension):
        """Sets the generation seed and randomly generates parameters to create inj"""
        bilby.core.utils.random.seed(self.generation_seed)
        logger.info(
            f"Generating injection file {filepath} from "
            f"prior={self.prior_file}, "
            f"n_injection={self.n_injection}, "
            f"generation_seed={self.generation_seed}"
        )
        injection_dataframe = self.get_injection_dataframe()
        self.write_injection_dataframe(injection_dataframe, filepath, extension)


def get_full_path(filename, extension):
    """Makes filename and ext consistent amongst user input"""
    ext_in_filename = os.path.splitext(filename)[1].lstrip(".")
    if ext_in_filename == "":
        path = f"{filename}.{extension}"
    elif ext_in_filename == extension:
        path = filename
    else:
        logger.debug("Overwriting given extension name")
        path = filename
        extension = ext_in_filename
    outdir = os.path.dirname(path)
    if outdir != "":
        check_directory_exists_and_if_not_mkdir(outdir)
    return path, extension


def create_injection_file(
    filename,
    n_injection,
    prior_file=None,
    prior_dict=None,
    trigger_time=None,
    deltaT=0.2,
    gpstimes=None,
    duration=4,
    post_trigger_duration=2,
    generation_seed=None,
    extension="dat",
    default_prior="BBHPriorDict",
    enforce_signal_duration=False,
    cosmology=None,
):
    """Makes injection file using arguments from the namespace args parameter"""
    injection_creator = InjectionCreator(
        prior_file=prior_file,
        prior_dict=prior_dict,
        n_injection=n_injection,
        default_prior=default_prior,
        trigger_time=trigger_time,
        deltaT=deltaT,
        gpstimes=gpstimes,
        duration=duration,
        post_trigger_duration=post_trigger_duration,
        generation_seed=generation_seed,
        enforce_signal_duration=enforce_signal_duration,
        cosmology=cosmology,
    )
    injection_creator.generate_injection_file(filename, extension)


def main():
    """Driver to create an injection file"""
    args, unknown_args = parse_args(sys.argv[1:], create_parser())

    if args.gps_tuple is not None:
        gpstimes = Input.parse_gps_tuple(args.gps_tuple)
    elif args.gps_file is not None:
        gpstimes = Input.read_gps_file(args.gps_file)
    else:
        gpstimes = None

    create_injection_file(
        args.filename,
        prior_file=args.prior_file,
        prior_dict=None,
        n_injection=args.n_injection,
        trigger_time=args.trigger_time,
        deltaT=args.deltaT,
        gpstimes=gpstimes,
        duration=args.duration,
        post_trigger_duration=args.post_trigger_duration,
        generation_seed=args.generation_seed,
        enforce_signal_duration=args.enforce_signal_duration,
    )
