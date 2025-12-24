"""
A set of generic utilities used in bilby_pipe
"""
import ast
import json
import logging
import math
import os
import pickle
import re
import subprocess
import sys
import urllib
import urllib.request
from importlib import import_module

import bilby

CHECKPOINT_EXIT_CODE = 77

ENVIRONMENT_DEFAULTS = dict(
    HDF5_USE_FILE_LOCKING="FAlSE",
    OMP_NUM_THREADS=1,
    OMP_PROC_BIND="false",
)

DEFAULT_GWDATAFIND_SERVER = "https://datafind.igwn.org"


class tcolors:
    WARNING = "\u001b[31m"
    KEY = "\033[93m"
    VALUE = "\033[91m"
    HIGHLIGHT = "\033[95m"
    END = "\033[0m"


def get_colored_string(msg_list, color="HIGHLIGHT"):
    if isinstance(msg_list, str):
        msg_list = [msg_list]
    colstr = getattr(tcolors, color)
    msg = [colstr] + msg_list + [tcolors.END]
    return "".join(msg)


class BilbyPipeError(Exception):
    def __init__(self, message):
        super().__init__(message)


class BilbyPipeInternalError(Exception):
    def __init__(self, message):
        super().__init__(message)


class ArgumentsString(object):
    """A convenience object to aid in the creation of argument strings"""

    def __init__(self):
        self.argument_list = []

    def append(self, argument):
        self.argument_list.append(argument)

    def add_positional_argument(self, value):
        self.argument_list.append(f"{value}")

    def add_flag(self, flag):
        self.argument_list.append(f"--{flag}")

    def add(self, argument, value):
        self.argument_list.append(f"--{argument}")
        self.argument_list.append(f"{value}")

    def add_unknown_args(self, unknown_args):
        self.argument_list += unknown_args

    def add_command_line_arguments(self):
        """Adds command line arguments given in addition to the ini file"""
        command_line_args_list = get_command_line_arguments()
        # Remove the first positional ini-file argument
        command_line_args_list = command_line_args_list[1:]
        self.argument_list += command_line_args_list

    def print(self):
        return " ".join(self.argument_list)


class DataDump(object):
    def __init__(
        self,
        label,
        outdir,
        trigger_time,
        likelihood_lookup_table,
        likelihood_roq_weights,
        likelihood_roq_params,
        likelihood_multiband_weights,
        priors_dict,
        priors_class,
        interferometers,
        meta_data,
        idx,
    ):
        self.trigger_time = trigger_time
        self.label = label
        self.outdir = outdir
        self.interferometers = interferometers
        self.likelihood_lookup_table = likelihood_lookup_table
        self.likelihood_roq_weights = likelihood_roq_weights
        self.likelihood_roq_params = likelihood_roq_params
        self.likelihood_multiband_weights = likelihood_multiband_weights
        self.priors_dict = priors_dict
        self.priors_class = priors_class
        self.meta_data = meta_data
        self.idx = idx

    @staticmethod
    def get_filename(outdir, label):
        return os.path.join(outdir, "_".join([label, "data_dump.pickle"]))

    @property
    def filename(self):
        return self.get_filename(self.outdir, self.label)

    def to_pickle(self):
        with open(self.filename, "wb+") as file:
            pickle.dump(self, file)

    @classmethod
    def from_pickle(cls, filename=None):
        """Loads in a data dump

        Parameters
        ----------
        filename: str
            If given, try to load from this filename

        """
        with open(filename, "rb") as file:
            res = pickle.load(file)
        if res.__class__ != cls:
            raise TypeError("The loaded object is not a DataDump")
        return res


class NoneWrapper(object):
    """
    Wrapper around other types so that "None" always evaluates to None.

    This is needed to properly read None from ini files.

    Examples
    --------
    >>> nonestr = NoneWrapper(str)
    >>> nonestr("None")
    None
    >>> nonestr(None)
    None
    >>> nonestr("foo")
    "foo"

    >>> noneint = NoneWrapper(int)
    >>> noneint("None")
    None
    >>> noneint(None)
    None
    >>> noneint(0)
    0
    """

    def __init__(self, type):
        self.type = type

    def __call__(self, val):
        if val == "None" or val is None:
            return None
        else:
            return self.type(val)


nonestr = NoneWrapper(str)
noneint = NoneWrapper(int)
nonefloat = NoneWrapper(float)

DEFAULT_DISTANCE_LOOKUPS = {
    "high_mass": (1e2, 5e3),
    "4s": (1e1, 1e4),
    "8s": (1e1, 5e3),
    "16s": (1e1, 4e3),
    "32s": (1e1, 3e3),
    "64s": (5, 2e3),
    "128s": (1, 5e2),
    "128s_tidal": (1, 5e2),
    "128s_tidal_lowspin": (1, 5e2),
}

DURATION_LOOKUPS = {
    "high_mass": 4,
    "4s": 4,
    "8s": 8,
    "16s": 16,
    "32s": 32,
    "64s": 64,
    "128s": 128,
    "128s_tidal": 128,
    "128s_tidal_lowspin": 128,
}

MAXIMUM_FREQUENCY_LOOKUPS = {
    "high_mass": 1024,
    "4s": 1024,
    "8s": 2048,
    "16s": 2048,
    "32s": 2048,
    "64s": 2048,
    "128s": 4096,
    "128s_tidal": 2048,
    "128s_tidal_lowspin": 2048,
}

SAMPLER_SETTINGS = {
    "DynestyDefault": {
        "nlive": 1000,
        "naccept": 60,
        "check_point_plot": True,
        "check_point_delta_t": 1800,
        "print_method": "interval-60",
        "sample": "acceptance-walk",
    },
    "FastTest": {
        "nlive": 50,
        "naccept": 5,
        "dlogz": 1,
        "check_point_plot": True,
        "check_point_delta_t": 1800,
        "print_method": "interval-10",
        "sample": "acceptance-walk",
    },
    "BilbyMCMCDefault": {
        "nsamples": 5000,
        "thin_by_nact": 0.1,
        "ntemps": 8,
        "Tmax_from_SNR": 15,
        "adapt": True,
        "proposal_cycle": "gwA",
        "L1steps": 100,
        "L2steps": 3,
        "check_point_plot": True,
        "check_point_delta_t": 1800,
        "print_update": 60,
    },
}

CALIBRATION_CORRECTION_TYPE_LOOKUP = {
    "H1": "data",
    "L1": "data",
    "V1": "template",
    "K1": "data",
}


def get_command_line_arguments():
    """Helper function to return the list of command line arguments"""
    return sys.argv[1:]


def run_command_line(arguments, directory=None):
    if directory:
        pwd = os.path.abspath(".")
        os.chdir(directory)
    else:
        pwd = None
    print(f"\nRunning command $ {' '.join(arguments)}\n")
    subprocess.call(arguments)
    if pwd:
        os.chdir(pwd)


def parse_args(input_args, parser, allow_unknown=True):
    """Parse an argument list using parser generated by create_parser()

    Parameters
    ----------
    input_args: list
        A list of arguments

    Returns
    -------
    args: argparse.Namespace
        A simple object storing the input arguments
    unknown_args: list
        A list of any arguments in `input_args` unknown by the parser

    """

    if len(input_args) == 0:
        raise BilbyPipeError("No command line arguments provided")

    ini_file = input_args[0]
    if os.path.isfile(ini_file) is False:
        if os.path.isfile(os.path.basename(ini_file)):
            input_args[0] = os.path.basename(ini_file)

    args, unknown_args = parser.parse_known_args(input_args)
    return args, unknown_args


def check_directory_exists_and_if_not_mkdir(directory):
    """Checks if the given directory exists and creates it if it does not exist

    Parameters
    ----------
    directory: str
        Name of the directory

    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.debug(f"Making directory {directory}")
    else:
        logger.debug(f"Directory {directory} exists")


def setup_logger(outdir=None, label=None, log_level="INFO"):
    """Setup logging output: call at the start of the script to use

    Parameters
    ----------
    outdir, label: str
        If supplied, write the logging output to outdir/label.log
    log_level: str, optional
        ['debug', 'info', 'warning']
        Either a string from the list above, or an integer as specified
        in https://docs.python.org/2/library/logging.html#logging-levels
    """

    if "-v" in sys.argv or "--verbose" in sys.argv:
        log_level = "DEBUG"

    if isinstance(log_level, str):
        try:
            level = getattr(logging, log_level.upper())
        except AttributeError:
            raise ValueError(f"log_level {log_level} not understood")
    else:
        level = int(log_level)

    logger = logging.getLogger("bilby_pipe")
    logger.propagate = False
    logger.setLevel(level)

    streams = [isinstance(h, logging.StreamHandler) for h in logger.handlers]
    if len(streams) == 0 or not all(streams):
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s", datefmt="%y%m%d_%H%M%S"
            )
        )
        stream_handler.setLevel(level)
        logger.addHandler(stream_handler)

    if any([isinstance(h, logging.FileHandler) for h in logger.handlers]) is False:
        if label:
            if outdir:
                check_directory_exists_and_if_not_mkdir(outdir)
            else:
                outdir = "."
            log_file = f"{outdir}/{label}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s %(levelname)-8s: %(message)s", datefmt="%H:%M"
                )
            )

            file_handler.setLevel(level)
            logger.addHandler(file_handler)

    for handler in logger.handlers:
        handler.setLevel(level)


def get_outdir_name(outdir, fail_on_match=False, base_increment="A"):
    # Check if the directory exists
    if os.path.exists(outdir) is False:
        return outdir
    else:
        msg = "Outdir exists,"
        if fail_on_match:
            raise BilbyPipeError(msg)

        while os.path.exists(outdir):
            outdir = generate_new_outdir_name(outdir)

        msg += f" incrementing outdir to {outdir}"
        logger.warning(get_colored_string(msg))
        return outdir


def generate_new_outdir_name(outdir):
    """Generate a new outdir name to avoid naming conflicts

    The incrementing name format is "_A", "_B", etc. Once "_Z" is reached, we then move to "_AA" etc.

    """
    tokens = outdir.split("_")
    # Check if at least one _ and non-empty
    if (
        len(tokens) <= 1
        or len(tokens[-1]) == 0
        or re.match("[A-Z]{1,2}$", tokens[-1]) is None
    ):
        new_outdir = outdir + "_A"
        return new_outdir

    # Check if target matches standard form
    matches = re.findall("^[A-Z]+", tokens[-1])
    if len(matches) == 1 and matches[0] != tokens[-1]:
        new_outdir = outdir + "_A"
        return new_outdir

    new_chars = []
    suffix = tokens[-1]
    n_chars = len(suffix)
    stop_idx = -1
    for idx in range(n_chars - 1, -1, -1):
        if ord(suffix[idx]) == ord("Z"):
            new_chars.append("A")
            continue
        else:
            new_chars.append(chr(ord(suffix[idx]) + 1))
            stop_idx = idx
            break
    if len(new_chars) > 0:
        new_chars.reverse()
    if stop_idx == -1:
        new_suffix = ""
        for idx in range(n_chars):
            new_suffix = new_suffix + new_chars[idx]
        new_suffix = new_suffix + "A"  # increase one character
    else:
        new_suffix = ""
        for idx in range(stop_idx):
            new_suffix = new_suffix + suffix[idx]
        for idx in range(len(new_chars)):
            new_suffix = new_suffix + new_chars[idx]
    roots = tokens[:-1]
    new_outdir = "_".join(roots) + "_" + new_suffix
    return new_outdir


def log_version_information():
    import bilby
    import bilby_pipe

    logger.info(f"Running bilby_pipe version: {bilby_pipe.__version__}")
    logger.info(f"Running bilby version: {bilby.__version__}")


def get_version_information():
    from bilby_pipe import __version__

    return __version__


def convert_string_to_tuple(string, key=None, n=None):
    """Convert a string to a tuple

    Parameters
    ----------
    string: str
        The string to convert
    key: str
        Name used for printing useful debug messages
    n: int
        The length of the string to check against, if None no check performed.

    Returns
    -------
    tup: tuple
        A tuple
    """
    try:
        tup = ast.literal_eval(string)
    except ValueError as e:
        if key is not None:
            raise BilbyPipeError(f"Error {e}: unable to convert {key}: {string}")
        else:
            raise BilbyPipeError(f"Error {e}: unable to {string}")
    if n is not None:
        if len(tup) != n:
            raise BilbyPipeError(
                f"Passed string {string} should be a tuple of length {n}"
            )

    return tup


def convert_string_to_dict(string, key=None):
    """Convert a string repr of a string to a python dictionary

    Parameters
    ----------
    string: str
        The string to convert
    key: str (None)
        A key, used for debugging
    """
    if string == "None":
        return None
    string = strip_quotes(string)
    # Convert equals to colons
    string = string.replace("=", ":")
    string = string.replace(" ", "")

    string = re.sub(r'([A-Za-z/\.0-9\-\+][^\[\],:"}]*)', r'"\g<1>"', string)

    # Force double quotes around everything
    string = string.replace('""', '"')

    # Evaluate as a dictionary of str: str
    try:
        dic = ast.literal_eval(string)
        if isinstance(dic, str):
            raise BilbyPipeError(f"Unable to format {string} into a dictionary")
    except (ValueError, SyntaxError) as e:
        if key is not None:
            raise BilbyPipeError(f"Error {e}. Unable to parse {key}: {string}")
        else:
            raise BilbyPipeError(f"Error {e}. Unable to parse {string}")

    # Convert values to bool/floats/ints where possible
    dic = convert_dict_values_if_possible(dic)

    return dic


def convert_string_to_list(string):
    """Converts a string to a list, e.g. the mode_array waveform argument

    See tests/utils_test for tested behaviour.

    Parameters
    ----------
    string: str
        The input string to convert

    Returns
    -------
    new_list: list
        A list (or lists)

    """

    if type(string) not in [str, list]:
        return string

    if (string.count("[") == 1) and (string.count("]") == 1):
        string = str(sanitize_string_for_list(string))

    try:
        new_list = ast.literal_eval(str(string))
    except ValueError:
        return string

    if not isinstance(new_list, list):
        return new_list

    for ii, ell in enumerate(new_list):
        new_list[ii] = convert_string_to_list(ell)

    return new_list


def sanitize_string_for_list(string):
    string = string.replace(",", " ")
    string = string.replace("[", "")
    string = string.replace("]", "")
    string = string.replace('"', "")
    string = string.replace("'", "")
    string_list = string.split()
    return string_list


def convert_dict_values_if_possible(dic):
    for key in dic:
        if isinstance(dic[key], str) and dic[key].lower() == "true":
            dic[key] = True
        elif isinstance(dic[key], str) and dic[key].lower() == "false":
            dic[key] = False
        elif isinstance(dic[key], str):
            dic[key] = string_to_int_float(dic[key])
        elif isinstance(dic[key], dict):
            dic[key] = convert_dict_values_if_possible(dic[key])
    return dic


def write_config_file(config_dict, filename, comment=None, remove_none=False):
    """Writes ini file

    Parameters
    ----------
    config_dict: dict
        Dictionary of parameters for ini file
    filename: str
        Filename to write the config file to
    comment: str
        Additional information on ini file generation
    remove_none: bool
        If true, remove None's from the config_dict before writing otherwise
        a ValueError is raised
    """
    logger.warning(
        "write_config_file has been deprecated, it will be removed in a future version"
    )

    if remove_none:
        config_dict = {key: val for key, val in config_dict.items() if val is not None}
    if None in config_dict.values():
        raise ValueError("config-dict is not complete")
    with open(filename, "w+") as file:
        if comment is not None:
            print(f"{comment}", file=file)
        for key, val in config_dict.items():
            print(f"{key}={val}", file=file)


def test_connection():
    """A generic test to see if the network is reachable"""
    try:
        urllib.request.urlopen("https://google.com", timeout=1.0)
    except urllib.error.URLError:
        raise BilbyPipeError(
            "It appears you are not connected to a network and so won't be "
            "able to interface with GraceDB. You may wish to specify the "
            " local-generation argument either in the configuration file "
            "or by passing the --local-generation command line argument"
        )


def strip_quotes(string):
    try:
        return string.replace('"', "").replace("'", "")
    except AttributeError:
        return string


def string_to_int_float(s):
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s


def is_a_power_of_2(num):
    num = int(num)
    return num != 0 and ((num & (num - 1)) == 0)


def next_power_of_2(x):
    return 1 if x == 0 else 2 ** math.ceil(math.log2(x))


def request_memory_generation_lookup(duration, roq=False):
    """Function to determine memory required at the data generation step"""
    if roq:
        return int(max([8, min([60, duration])]))
    else:
        return 8


def get_time_prior(time, uncertainty, name="geocent_time", latex_label="$t_c$"):
    """Generate a time prior given some uncertainty.

    Parameters
    ----------
    time: float
        The GPS geocent_time (time of coalescence at the center of the Earth)
    uncertainty: float
        The +/- uncertainty based around the geocenter time.
    name: str
        The name of the time parameter
    latex_label: str
        The latex label for the time parameter

    Returns
    -------
    A bilby.core.prior.Uniform for the time parameter.

    """
    return bilby.core.prior.Uniform(
        minimum=time - uncertainty,
        maximum=time + uncertainty,
        name=name,
        latex_label=latex_label,
        unit="$s$",
    )


def get_geocent_time_with_uncertainty(geocent_time, uncertainty):
    """Get a new geocent time within some uncertainty from the original geocent time.

    Parameters
    ----------
    geocent_time: float
        The GPS geocent_time (time of coalescence at the center of the Earth)
    uncertainty: float
        The +/- uncertainty based around the geocenter time.

    Returns
    -------
    A geocent GPS time (float) inside the range of geocent time - uncertainty and
    geocent time + uncertainty.

    """
    geocent_time_prior = get_time_prior(geocent_time, uncertainty)
    return geocent_time_prior.sample()


def convert_detectors_input(string):
    """Convert string inputs into a standard form for the detectors

    Parameters
    ----------
    string: str
        A string representation to be converted

    Returns
    -------
    detectors: list
        A sorted list of detectors

    """
    if string is None:
        raise BilbyPipeError("No detector input")
    if isinstance(string, list):
        string = ",".join(string)
    if isinstance(string, str) is False:
        raise BilbyPipeError(f"Detector input {string} not understood")
    # Remove square brackets
    string = string.replace("[", "").replace("]", "")
    # Remove added quotes
    string = strip_quotes(string)
    # Replace multiple spaces with a single space
    string = " ".join(string.split())
    # Spaces can be either space or comma in input, convert to comma
    string = string.replace(" ,", ",").replace(", ", ",").replace(" ", ",")

    detectors = string.split(",")

    detectors.sort()
    detectors = [det.upper() for det in detectors]
    return detectors


def convert_prior_string_input(string):
    string = string.replace(" ", "")
    string = string.replace(":", "=")
    prior_dict_of_strings = {}
    for part in comma_partition(string):
        if len(part) > 0:
            prior_dict_of_strings.update(kv_parser(part))
    return prior_dict_of_strings


def comma_partition(s):
    """Partitions `s` at top-level commas"""
    s = s.strip("{").strip("}")
    in_parens = 0
    ixs = []
    for i, c in enumerate(s):
        if c == "(":
            in_parens += 1
        if c == ")":
            in_parens -= 1
        if not in_parens and c == ",":
            ixs.append(i)
    return [s[sc] for sc in make_partition_slices(ixs)]


def make_partition_slices(ixs):
    """Yields partitioning slices, skipping each index of `ixs`"""
    ix_x = [None] + ixs
    ix_y = ixs + [None]
    for x, y in zip(ix_x, ix_y):
        yield slice(x + 1 if x else x, y)


def kv_parser(kv_str, remove_leading_namespace=False):
    """Takes a string in 'K=V' format and returns dictionary."""
    try:
        k, v = kv_str.split("=", 1)
        return {k: v}
    except ValueError:
        raise BilbyPipeInternalError(f"Error in ini-dict reader when reading {kv_str}")


def check_if_represents_int(s):
    """Checks if the string/bytes-like object/number s represents an int"""
    try:
        int(s)
        return True
    except ValueError:
        return False


def pretty_print_dictionary(dictionary):
    """Convert an input dictionary to a pretty-printed string

    Parameters
    ----------
    dictionary: dict
        Input dictionary

    Returns
    -------
    pp: str
        The dictionary pretty-printed as a string

    """
    dict_as_str = {key: str(val) for key, val in dictionary.items()}
    return json.dumps(dict_as_str, indent=2)


class DuplicateErrorDict(dict):
    """An dictionary with immutable key-value pairs

    Once a key-value pair is initialized, any attempt to update the value for
    an existing key will raise a BilbyPipeError.

    Raises
    ------
    BilbyPipeError:
        When a user attempts to update an existing key.

    """

    def __init__(self, color=True, *args):
        dict.__init__(self, args)
        self.color = color

    def __setitem__(self, key, val):
        if key in self:
            msg = f"Your ini file contains duplicate '{key}' keys"
            if self.color:
                msg = get_colored_string(msg)
            raise BilbyPipeError(msg)
        dict.__setitem__(self, key, val)


def get_function_from_string_path(python_path):
    split = python_path.split(".")
    module_str = ".".join(split[:-1])
    func_str = split[-1]
    try:
        return getattr(import_module(module_str), func_str)
    except ImportError as e:
        raise BilbyPipeError(
            f"Failed to load function {python_path}, full message: {e}"
        )


def convert_string_slice_syntax(string):
    if ":" in string:
        return list(range(*(int(i) if i else None for i in string.strip().split(":"))))
    else:
        return [int(string.strip())]


def check_if_psd_is_from_built_in(psd_file):
    """Check if the psd_file can be found in the bilby built-in directory"""
    psd_file_built_in = os.path.join(
        os.path.dirname(bilby.gw.detector.psd.__file__), "noise_curves", psd_file
    )
    return os.path.isfile(psd_file_built_in)


def resolve_filename_with_transfer_fallback(filename):
    """
    When absolute paths are transferred using HTCondor, the absolute path is
    replaced with the basename of the file. This function checks if the file
    exists, if not, checks if the basename exists. If the basename exists,
    returns the basename, otherwise returns None.

    Parameters
    ----------
    filename: str
        The filename to check

    Returns
    -------
    filename: str
        The filename, or basename, if it exists, otherwise None
    """
    if os.path.isfile(filename):
        return filename
    elif os.path.isfile(os.path.basename(filename)):
        return os.path.basename(filename)
    return None


def log_function_call(function, kwargs, log=True):
    kwargs_string = ""
    for key, val in kwargs.items():
        if isinstance(val, str):
            val = f"'{val}'"
        kwargs_string += f"{key}={val}, "
    call_str = f"{function}({kwargs_string})"
    if log:
        logger.info(f"Running: {call_str}")
    else:
        return call_str


def get_and_set_cosmology(cosmology=None):
    """Get the cosmology and set the global bilby cosmology.

    If a cosmology is None, then the default bilby cosmology is used.

    This function is used to ensure that the bilby_pipe and bilby cosmologies
    are always consistent.
    """
    cosmology = bilby.gw.cosmology.get_cosmology(cosmology)
    logger.debug(f"Setting global bilby cosmology to {cosmology}")
    bilby.gw.cosmology.set_cosmology(cosmology)
    return cosmology


def get_environment_variables_dictionary(inputs):
    f"""Get the environment variables dictionary from the inputs.

    This starts from {ENVIRONMENT_DEFAULTS} and adds values from the
    :code:`--environment-variables` and :code:`--getenv` arguments.

    ..versionadded:: 1.8.0

    Parameters
    ----------
    inputs: bilby_pipe.inputs.Inputs
        The inputs object containing the environment variables and getenv
        arguments.

    Returns
    -------
    env: dict
        A dictionary of environment variables names and values.
    """
    env = ENVIRONMENT_DEFAULTS.copy()
    for key in inputs.getenv:
        value = os.environ.get(key, None)
        if value is not None:
            env[key] = sanitize_string_for_list(str(value))[0]
        else:
            logger.warning(
                f"Variable {key} requested from getenv, "
                "but not found in environment."
            )
    env.update(inputs.environment_variables)
    if inputs.disable_hdf5_locking:
        logger.warning(
            "The --disable-hdf5-locking variable is deprecated use, "
            "--environment-variables instead."
        )
        env["HDF5_USE_FILE_LOCKING"] = "FALSE"

    # Set the GWDATAFIND_SERVER environment variable for use in jobs.
    # If data_find_url is not set, use the environment variable
    # GWDATAFIND_SERVER if it is included in `environment-variables`
    # otherwise use the default from bilby_pipe.utils
    if inputs.data_find_url is None:
        if "GWDATAFIND_SERVER" not in env:
            logger.debug(
                (
                    "`data-find-url` is not specified and `environment-variables` "
                    "does not include GWDATAFIND_SERVER. "
                    f"Using the default value: {DEFAULT_GWDATAFIND_SERVER}"
                )
            )
            env["GWDATAFIND_SERVER"] = DEFAULT_GWDATAFIND_SERVER
    else:
        if "GWDATAFIND_SERVER" in env:
            logger.warning(
                "GWDATAFIND_SERVER is specified in `environment-variables` "
                "and via the `data-find-url` argument. The latter will be used."
            )
        env["GWDATAFIND_SERVER"] = inputs.data_find_url
    return env


setup_logger()
logger = logging.getLogger("bilby_pipe")
