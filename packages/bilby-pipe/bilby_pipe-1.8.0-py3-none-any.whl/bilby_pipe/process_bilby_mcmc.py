"""

This executable will process an ongoing bilby_mcmc analyses to produce a
combined result. The executable is assumed to be run from the submit
directory (e.g., where the .ini file is) and on the submit machine.

.. note::
    If your analysis uses HTCondor file transfer (:code:`transfer-files=True`), the
    resume files required for processing will not exist on the submit machine until
    the job has completed. You will need to use :code:`bilby_pipe_htcondor_sync`
    to first sync the files to the submit machine, then run
    :code:`bilby_pipe_process_bilby_mcmc`.

"""

import argparse
import copy
import datetime
import glob
import logging
import os
import re
import sys

import dill
import matplotlib.colors as mcolors
import numpy as np

import bilby
from bilby.bilby_mcmc.sampler import Bilby_MCMC
from bilby.bilby_mcmc.utils import ConvergenceInputs
from bilby.core.utils import loaded_modules_dict
from bilby.core.utils import logger as bilby_logger
from bilby_pipe.data_analysis import (
    DataAnalysisInput,
    create_analysis_parser,
    parse_args,
)
from bilby_pipe.utils import logger as bilby_pipe_logger

bilby_pipe_logger.setLevel(logging.WARNING)
bilby_logger.setLevel(logging.WARNING)

RESULT_SUBDIR = "result"


class Dummy:
    pass


class RobustUnpickler(dill.Unpickler):
    def find_class(self, module, name):
        try:
            return super().find_class(module, name)
        except AttributeError as e:
            print(f"WARNING: AttributeError raised: {e}")
            return Dummy


def glob_and_filter_files(args, globpath):
    files = glob.glob(globpath)
    files = sorted(files)
    if args.filter_match is not None:
        files = [f for f in files if re.search(args.filter_match, f) is not None]
    if args.filter_antimatch is not None:
        files = [f for f in files if re.search(args.filter_antimatch, f) is None]
    return files


def get_resume_file_paths(args, label):
    # Identify existing resume files
    path = os.path.join(args.directory, RESULT_SUBDIR, f"{label}*resume.pickle")
    resume_files = glob_and_filter_files(args, path)
    if len(resume_files) > 0:
        print(f"Reading in {len(resume_files)} checkpoint files from {path}")
    else:
        print("No checkpoint files found, exiting")
        sys.exit()
    return resume_files


def extract_label_from_filename(filename):
    filename = os.path.basename(filename)
    return filename.replace("_resume.pickle", "")


def check_unique_file(files, ftype):
    if len(files) > 1:
        raise ValueError(f"Multiple {ftype} files found, aborting")
    elif len(files) == 0:
        raise ValueError(f"No {ftype} files found, aborting")


def find_data_dump_file(args):
    path = os.path.join(args.directory, "data", "*dump.pickle")
    dd_files = glob.glob(path)
    check_unique_file(dd_files, "data dump")
    fname = dd_files[0]
    print(f"Using data dump file {fname}")
    return fname


def find_config(args):
    path = os.path.join(args.directory, "*ini")
    config_files = glob.glob(path)
    check_unique_file(config_files, "config")
    fname = config_files[0]
    print(f"Using config file {fname}")
    return fname


def get_output_fname(
    outdir_result, resume_files, naming_method="datetime", extension="json"
):
    file_labels = [
        rf.split("/")[-1].replace("_resume.pickle", "") for rf in resume_files
    ]
    base_labels = {bl.split("_par")[0] for bl in file_labels}
    if len(base_labels) > 1:
        raise ValueError("Processing error: resume files mismatch")
    else:
        base_label = list(base_labels)[0]

    if naming_method == "datetime":
        now = datetime.datetime.now().strftime("%y%m%d-%H%M")
        fname = f"{outdir_result}/{base_label}_PRELIM_result{now}.{extension}"
    elif naming_method == "final":
        if len(resume_files) > 1:
            fname = f"{outdir_result}/{base_label}_merge_result.{extension}"
        else:
            # If a single file, name it appropriately
            fname = f"{outdir_result}/{file_labels[0]}_result.{extension}"
    else:
        fname = f"{outdir_result}/{base_label}_PRELIM_resultA.{extension}"
        index = "resultA"
        while os.path.isfile(fname):
            new_index = index[:-1] + chr(ord(index[-1]) + 1)
            fname = fname.replace(index, new_index)
            index = new_index
    return fname


def update_convergence_inputs(args, ptsampler):
    # Read in convergence inputs from sampler
    inputs = dict()
    s0 = ptsampler.sampler_list[0]
    for field in ConvergenceInputs._fields:
        if hasattr(s0.chain, field):
            inputs[field] = getattr(s0.chain, field)
        elif hasattr(s0, field):
            inputs[field] = getattr(s0, field)
        elif hasattr(ptsampler, field):
            inputs[field] = getattr(ptsampler, field)
        else:
            raise ValueError(f"Unable to handle {field}")

    # Overwrite convergence inputs
    if args.thin_by_nact:
        inputs["thin_by_nact"] = args.thin_by_nact

    ci = ConvergenceInputs(**inputs)

    ptsampler.set_convergence_inputs(ci)

    return ptsampler


def create_parser():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "directory",
        type=str,
        help=(
            'Directory to process: this should be the "outdir" specified in '
            " the configuration file"
        ),
    )
    parser.add_argument(
        "-o",
        "--output-directory",
        type=str,
        help="Directory to write outputs, if not given `directory` is used.",
    )
    parser.add_argument("--npool", type=int, default=1, help="Multiprocess using npool")
    parser.add_argument(
        "--thin-by-nact",
        type=float,
        default=None,
        help="Overwrite the thin-by nact used.",
    )
    parser.add_argument(
        "--plot", action="store_true", help="Create plots for each individual sampler."
    )
    parser.add_argument(
        "--convergence-check",
        action="store_true",
        help="Create convergence check plots.",
    )
    parser.add_argument(
        "--pt-rejection-sample",
        type=bool,
        default=False,
        help="If True, use pt_rejection_sampling.",
    )
    parser.add_argument(
        "-n",
        "--naming-method",
        type=str,
        default="datetime",
        help=(
            "Naming method for output. If 'datetime', name the file by the"
            "time it was written. If 'final' name it as if it was final."
        ),
    )
    parser.add_argument(
        "--filter-match",
        type=str,
        default=None,
        help=(
            "Filter globbed files against this: anything not containing "
            "filter-match is discarded. Can use regex for matching."
        ),
    )
    parser.add_argument(
        "--filter-antimatch",
        type=str,
        default=None,
        help=(
            "Filter globbed files against this: anything containing "
            "filter-antimatch is discarded. Can use regex for matching."
        ),
    )
    parser.add_argument(
        "--no-conversion-function",
        action="store_true",
        help=("If given, ignore the conversion_function"),
    )
    parser.add_argument(
        "--minimum-independent-samples",
        default=50,
        type=int,
        help=("The minimum number of independent samples per chain."),
    )
    return parser


def get_args():
    parser = create_parser()
    return parser.parse_args()


def process_sampler(ptsampler, analysis, outdir, args):
    # Obtain likelihood and priors
    likelihood, search_priors = analysis.get_likelihood_and_priors()
    priors = analysis.priors

    search_priors.convert_floats_to_delta_functions()

    ind_label = ptsampler.label

    result_kwargs = dict(
        label=ind_label,
        outdir=outdir,
        sampler=analysis.sampler,
        search_parameter_keys=search_priors.non_fixed_keys,
        fixed_parameter_keys=search_priors.fixed_keys,
        constraint_parameter_keys=search_priors.constraint_keys,
        priors=search_priors,
        meta_data=analysis.meta_data,
        injection_parameters=analysis.meta_data["injection_parameters"],
        sampler_kwargs=analysis.sampler_kwargs,
        use_ratio=True,
    )

    if analysis.result_class is None:
        result = bilby.gw.result.CompactBinaryCoalescenceResult(**result_kwargs)
    else:
        result = analysis.result_class(**result_kwargs)

    result = Bilby_MCMC.add_data_to_result(
        result=result,
        ptsampler=ptsampler,
        outdir=outdir,
        label=ind_label,
        make_plots=args.plot,
    )

    result.outdir = outdir
    prior_class = analysis.priors.__class__
    search_priors_copy = copy.deepcopy(prior_class(search_priors))
    likelihood_copy = copy.deepcopy(likelihood)

    # Convert sampling time into seconds
    result.sampling_time = result.sampling_time.total_seconds()

    if ptsampler.use_ratio:
        result.log_noise_evidence = likelihood.noise_log_likelihood()
        result.log_bayes_factor = result.log_evidence
        result.log_evidence = result.log_bayes_factor + result.log_noise_evidence
    else:
        result.log_noise_evidence = likelihood.noise_log_likelihood()
        result.log_bayes_factor = result.log_evidence - result.log_noise_evidence

    if args.no_conversion_function:
        conversion_function = None
    else:
        conversion_function = analysis.parameter_generation

    if None not in [result.injection_parameters, conversion_function]:
        result.injection_parameters = conversion_function(result.injection_parameters)

    result.samples_to_posterior(
        likelihood=likelihood_copy,
        priors=search_priors_copy,
        conversion_function=conversion_function,
        npool=args.npool,
    )

    # Overwrite the priors: search_priors_copy is updated in place
    result.priors = search_priors_copy
    result.meta_data["likelihood"] = likelihood_copy.meta_data
    result.meta_data["loaded_modules"] = loaded_modules_dict()
    result.posterior["log_likelihood"] = result.log_likelihood_evaluations

    if args.plot:
        Bilby_MCMC.plot_progress(
            ptsampler,
            result.label,
            outdir,
            priors,
            diagnostic=True,
        )

    return result


def main():
    # Setup
    args = get_args()
    config = find_config(args)

    # Get arguments from the config
    config_args, _ = parse_args([config], create_analysis_parser())
    config_args.data_dump_file = find_data_dump_file(args)

    if config_args.sampler != "bilby_mcmc":
        raise ValueError(f"Unable to process samples for sampler {config_args.sampler}")

    # Recreate bilby_pipe analysis object
    analysis = DataAnalysisInput(config_args, [])

    # Use the outdir given at the command line, not the stored outdir
    outdir_result = os.path.join(args.directory, RESULT_SUBDIR)

    label = config_args.label

    resume_files = get_resume_file_paths(args, label)

    results = []
    chain_data = {}
    min_ind_samples = args.minimum_independent_samples
    for ii, resume_file in enumerate(resume_files):
        print(f"Processing sampler {ii+1}/{len(resume_files)}: {resume_file}")
        with open(resume_file, "rb") as f:
            ptsampler = RobustUnpickler(f).load()

        if ptsampler == {}:
            print(f"Resume file {resume_file} is empty: ignoring")
            continue
        elif len(ptsampler.samples) == 0:
            print(f"Resume file {resume_file} contains no samples: ignoring")
            continue
        elif (
            ptsampler.nsamples * ptsampler.convergence_inputs.thin_by_nact
            < min_ind_samples
        ):
            print(
                f"Resume file {resume_file} contains less than {min_ind_samples}"
                " independent samples: this chain will not be included."
            )
            continue

        # Add the individual label
        ptsampler.label = extract_label_from_filename(resume_file)
        ptsampler = update_convergence_inputs(args, ptsampler)

        result = process_sampler(ptsampler, analysis, outdir_result, args)
        results.append(result)

        # Add to the convergence plot
        chain_data[ii] = extract_chain_data(ptsampler)

    if args.output_directory is not None:
        outdir = args.output_directory
    else:
        outdir = outdir_result

    result_fname = get_output_fname(
        outdir,
        resume_files,
        args.naming_method,
        extension=analysis.result_format,
    )
    if len(results) > 0:
        combined_result = bilby.core.result.ResultList(results).combine()
        combined_result.save_to_file(result_fname, extension=analysis.result_format)
        print(
            f"Saving results with {len(combined_result.posterior)} samples to {result_fname}"
        )
    else:
        print("No samples yet available")

    if args.convergence_check:
        create_convergence_plot(chain_data, result_fname)


def extract_chain_data(ptsampler):
    keys = ptsampler.sampler_dictionary[1][0].parameters
    keys = [key for key in keys if "recalib" not in key]

    if len(ptsampler.sampler_dictionary[1]) > 1:
        raise ValueError("This method is not implemented for ensemble sampling")
    else:
        sampler = ptsampler.sampler_dictionary[1][0]

    nburn = sampler.chain.minimum_index
    end = sampler.chain.position
    thin = max([1, int(sampler.chain.thin_by_nact * sampler.chain.tau_last)])
    nsamples = sampler.nsamples
    n_independent_samples = int(nsamples * sampler.chain.thin_by_nact)

    data = {}
    data["iterations"] = np.arange(nburn, end)
    data["keys"] = keys
    for key in keys:
        data[key] = sampler.chain.get_1d_array(key)[nburn:end:thin]
    data["label"] = ptsampler.label.split("_")[-1]
    data[
        "label"
    ] += f": tau={sampler.chain.tau_last} | N_samp={nsamples} | N_ind_samp={n_independent_samples}"
    return data


def create_convergence_plot(chain_data, result_fname):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    keys = chain_data[0]["keys"]
    ndim = len(keys)

    # Calculate Gelman Rubin statistics
    mchains = len(chain_data)
    lengths = [len(chain_data[i][chain_data[i]["keys"][0]]) for i in range(mchains)]
    nlength = min(lengths)
    if mchains > 1:
        PSRF_dict = {}
        for key in keys:
            arr = np.zeros((mchains, nlength))
            for ii, data in chain_data.items():
                arr[ii] = data[key][:nlength]
            theta_hat = np.mean(arr)
            theta_hat_m = np.mean(arr, axis=1)
            sigma2_hat_m = np.var(arr, axis=1)
            B = nlength / (mchains - 1) * np.sum((theta_hat_m - theta_hat) ** 2)
            W = 1 / (mchains) * np.sum(sigma2_hat_m)
            Vhat = (nlength - 1) * W / nlength + (mchains + 1) / (nlength * mchains) * B
            PSRF = Vhat / W
            PSRF_dict[key] = f"{PSRF:.2f}"
    else:
        PSRF_dict = {key: "N/A" for key in keys}

    subplot_titles = []
    for key in keys:
        subplot_titles.append(f"PSRF={PSRF_dict[key]}")
        subplot_titles.append("")

    fig = make_subplots(
        rows=ndim, cols=2, shared_xaxes=False, subplot_titles=subplot_titles
    )

    # Set axes titles and link axes
    for ii, key in enumerate(keys):
        left = 2 * ii + 1
        right = 2 * ii + 2
        fig["layout"][f"xaxis{left}"]["title"] = "Sample index"
        fig["layout"][f"yaxis{left}"]["title"] = key
        fig["layout"][f"xaxis{right}"]["title"] = key
        fig["layout"][f"yaxis{right}"]["title"] = "%"

        fig.update_xaxes(row=(ii + 1), col=1, matches=f"x{2 * ii + 3}")
        fig.update_xaxes(row=(ii + 1), col=2, matches=f"y{2 * ii + 1}")

    # Set of standard colours
    colors = list(mcolors.TABLEAU_COLORS.values()) + list(mcolors.XKCD_COLORS.values())

    # Iterate over chain data and plot
    for ii, data in chain_data.items():
        label = data["label"]
        for jj, key in enumerate(keys):
            xx = data["iterations"]
            yy = data[key]

            if jj == 0:
                showlegend = True
            else:
                showlegend = False

            fig.add_trace(
                go.Scattergl(
                    x=xx,
                    y=yy,
                    name=label,
                    line=dict(color=colors[ii], width=0.8),
                    showlegend=showlegend,
                    hovertemplate=" ",
                    text=label,
                ),
                row=(jj + 1),
                col=1,
            )

            fig.add_trace(
                go.Histogram(
                    x=yy,
                    name=label,
                    nbinsx=50,
                    opacity=0.5,
                    showlegend=False,
                    histnorm="percent",
                    hovertemplate=" ",
                    marker=dict(
                        color=colors[ii],
                    ),
                ),
                row=(jj + 1),
                col=2,
            )

    fig.update_layout(
        autosize=False,
        width=1200,
        height=4000,
        barmode="overlay",
        margin=dict(l=10, r=10, b=10, t=10, pad=1),
    )
    fname_split = result_fname.split(".")
    fname_split[-1] = "html"
    fname = ".".join(fname_split)
    print(f"Saving convergence plot to {fname}")
    fig.write_html(fname)


if __name__ == "__main__":
    main()
