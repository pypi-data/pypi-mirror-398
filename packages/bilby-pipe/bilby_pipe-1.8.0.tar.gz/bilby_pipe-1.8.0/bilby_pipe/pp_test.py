#!/usr/bin/env python
"""Analyse a set of runs for parameter-parameter plots

`Percent-percent (pp) <https://en.wikipedia.org/wiki/P%E2%80%93P_plot>`_
plots are commonly used to assess the performance of stochastic samplers.
This module provides utilities to make pp-plots from a set of
:code`bilby_pipe` results.
"""

import argparse
import glob
import json
import os
from datetime import timedelta

import corner
import numpy as np
import tqdm

from bilby.core.result import ResultList, ResultListError, make_pp_plot, read_in_result

from .utils import logger

# fmt: off
import matplotlib as mpl  # isort:skip
mpl.use("agg")
# fmt: on


mpl.rcParams.update(mpl.rcParamsDefault)


def create_parser():
    parser = argparse.ArgumentParser(
        prog="bilby_pipe_pp_test",
        description="Generates a pp plot from a directory containing a set of results",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("directory", help="Path to the result files")
    parser.add_argument(
        "--outdir", help="Path to output directory, defaults to input directory "
    )
    parser.add_argument("--label", help="Additional label to use for output")
    parser.add_argument(
        "--print", action="store_true", help="Print the list of filenames used"
    )
    parser.add_argument(
        "-n", type=int, help="Number of samples to truncate to", default=None
    )
    parser.add_argument(
        "--filter",
        type=str,
        help="A string to match and filtering results",
        default=None,
    )
    return parser


def get_results_filenames(args):
    results_files = []
    for extension in ["json", "h5", "hdf5", "pkl"]:
        glob_string = os.path.join(args.directory, "*result*" + extension)
        results_files += glob.glob(glob_string)
    results_files = [rf for rf in results_files if os.path.isfile(rf)]
    if len(results_files) == 0:
        raise FileNotFoundError(f"No results found in path {args.directory}")

    if args.filter is not None:
        logger.info(f"Filtering results to only '{args.filter}' results")
        results_files = [rf for rf in results_files if args.filter in rf]

    if any("merge" in item for item in results_files):
        logger.info("Filtering results to only 'merge' results")
        results_files = [rf for rf in results_files if "merge" in rf]

    if args.n is not None:
        logger.info(f"Truncating to first {args.n} results")
        results_files = results_files[: args.n]
    return results_files


def check_consistency(results):
    for check in ["sampler", "parameters", "priors"]:
        try:
            getattr(results, f"check_consistent_{check}")()
        except ResultListError as emsg:
            logger.warning(f"Results have inconsistent {check}: {emsg}")


def read_in_result_list(args, results_filenames):
    print("Reading in results ...")
    results = []
    for f in tqdm.tqdm(results_filenames):
        try:
            results.append(read_in_result(f))
        except json.decoder.JSONDecodeError:
            pass
    print(f"Read in {len(results)} results from directory {args.directory}")

    print("Checking if results are complete")
    results_u = []
    for r in results:
        if r._posterior is not None:
            results_u.append(r)
    if len(results_u) < len(results):
        print(f"Results incomplete, truncating to {len(results_u)}")
        results = results_u
    else:
        print("Results complete")

    if args.print:
        print(f"List of result-labels: {sorted([res.label for res in results])}")
    return ResultList(results)


def get_basename(args):
    if args.outdir is None:
        args.outdir = args.directory
    basename = f"{args.outdir}/"
    if args.label is not None:
        basename += f"{args.label}_"
    return basename


def make_meta_data_plot(results, basename):
    logger.info("Create meta data plot")

    TIME_SCALE = 3600

    stimes = []
    nsamples = []
    for result in results:
        if isinstance(result.sampling_time, timedelta):
            stimes.append(result.sampling_time.total_seconds() / TIME_SCALE)
        else:
            stimes.append(result.sampling_time / TIME_SCALE)

        nsamples.append(len(result.posterior) / 1000)

    snrs = []
    detectors = list(results[0].meta_data["likelihood"]["interferometers"].keys())
    for det in detectors:
        snrs.append(
            [
                r.meta_data["likelihood"]["interferometers"][det]["optimal_SNR"]
                for r in results
            ]
        )
    network_snr = np.sqrt(np.sum(np.array(snrs) ** 2, axis=0))

    fig = corner.corner(
        np.array([network_snr, stimes, nsamples]).T,
        bins=20,
        labels=["optimal SNR", "wall time [hr]", "nsamples [e3]"],
        plot_density=False,
        plot_contours=False,
        data_kwargs=dict(alpha=1),
        show_titles=True,
        range=[1, 1, 1],
    )
    fig.savefig(f"{basename}meta.png")


def main(args=None):
    if args is None:
        args = create_parser().parse_args()
    results_filenames = get_results_filenames(args)
    results = read_in_result_list(args, results_filenames)
    check_consistency(results)
    basename = get_basename(args)

    logger.info("Generating PP plot")
    keys = [
        name
        for name, p in results[0].priors.items()
        if isinstance(p, str) or p.is_fixed is False
    ]
    logger.info(f"Parameters = {keys}")
    make_pp_plot(results, filename=f"{basename}pp.png", keys=keys)
    make_meta_data_plot(results, basename)
