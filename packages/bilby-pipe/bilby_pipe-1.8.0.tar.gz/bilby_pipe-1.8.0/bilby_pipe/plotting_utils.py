"""Plotting helper functions."""
import os
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
from gwpy.signal import filter_design
from gwpy.timeseries import TimeSeries

import bilby.gw.detector
from bilby_pipe.utils import logger

# fmt: off
import matplotlib  # isort:skip
matplotlib.use("agg")
# fmt: on


def safe_run(func):
    """Try-catch gwpy_func_wrapper."""

    def gwpy_func_wrapper(*args, **kwargs):
        """Gwpy funct wrapper."""
        try:
            return func(*args, **kwargs)

        except UnboundLocalError:
            # Issue raised: https://github.com/gwpy/gwpy/issues/1144
            logger.warning(
                "Error with gwpy_plot of time and spectogram data. "
                "Skipping plotting. "
            )

    return gwpy_func_wrapper


@safe_run
def strain_spectrogram_plot(
    det: str,
    data: TimeSeries,
    data_directory: str,
    label: Optional[str] = "spectrogram",
    extra_label: Optional[str] = "",
    trigger_time: Optional[int] = None,
    duration: Optional[int] = None,
    post_trigger_duration: Optional[int] = None,
):
    """Save a timeseries and Q-transform spectrogram plot of the detector's data.

    Parameters
    ----------
    det: str
            The detector name corresponding to the key in data-dict
    data: gwpy.TimeSeries
        the timeseries strain data of a detector
    trigger_time: None or int
        The trigger time to where the plot is zoomed.
        If none, then will not zoom plot.
    duration: None or int
        The data duration to help zoom the plot to the trigger time
        If none, then will not zoom plot.
    post_trigger_duration: None or int
        The post_trigger_duration time to help zoom the plot to the trigger time.
        If none, then will not zoom plot.
    data_directory: str
            The data dir where the plot is stored.
    label: str
    extra_label: str
        A string identifier added to the name of the file

    Returns
    -------
    None

    File by the name `<outdir>/data/<Detector>_<Label>_<ExtraLabel>_data.png`
    is saved

    """
    # clean data
    filt_data = _filter_strain_data(data)

    # plot data
    det_color = {
        "H1": "gwpy:ligo-hanford",
        "L1": "gwpy:ligo-livingston",
        "V1": "gwpy:virgo",
        "K1": "gwpy:kagra",
    }
    plot, axes = plt.subplots(nrows=2, sharex=True, figsize=(8, 6))
    tax, qax = axes  # timeseries axis, q-transform spectogram axis
    tax.plot(filt_data, color=det_color[det])  # note: len(filt_data) < len(data)
    tax.set_xlabel("")
    tax.set_xscale("auto-gps")
    tax.set_ylabel("Whitened strain amplitude")
    specgram = filt_data.spectrogram2(fftlength=1 / 16, overlap=15 / 256) ** 0.5
    qax.imshow(specgram)
    qax.set_yscale("log")
    qax.set_ylabel("Frequency [Hz]")
    qax.colorbar(label="Normalised energy")
    tax.set_ylim(-5, 5)
    qax.set_ylim(20, 1024)

    # zoom into trigger and plot line if the data contains trigger
    if (trigger_time and duration and post_trigger_duration is not None) and (
        data.t0.value < trigger_time < (data.t0.value + data.duration.value)
    ):
        tax.axvline(x=trigger_time, linewidth=2, color="k", linestyle="--", alpha=0.3)
        qax.axvline(x=trigger_time, linewidth=2, color="w", linestyle="--", alpha=0.3)
        offset = duration - post_trigger_duration
        xmin = trigger_time - (offset * 0.2)
        xmax = trigger_time + (offset * 0.1)
        tax.set_xlim(xmin, xmax)

    plot.savefig(
        os.path.join(data_directory, "_".join([det, label, extra_label, "data.png"]))
    )


def strain_spectogram_plot(
    det: str,
    data: TimeSeries,
    data_directory: str,
    label: Optional[str] = "spectrogram",
    extra_label: Optional[str] = "",
    trigger_time: Optional[int] = None,
    duration: Optional[int] = None,
    post_trigger_duration: Optional[int] = None,
):
    """Deprecated due to typo in name."""
    logger.warning(
        "strain_spectogram_plot is deprecated use strain_spectrogram_plot instead."
    )
    return strain_spectrogram_plot(
        det,
        data,
        data_directory,
        label,
        extra_label,
        trigger_time,
        duration,
        post_trigger_duration,
    )


def _filter_strain_data(data):
    """Apply general filtering and whitening techniques to clean strain data.

    Methods adapted from
    https://gwpy.github.io/docs/stable/examples/signal/gw150914.html and
    https://gwpy.github.io/docs/stable/examples/spectrogram/spectrogram2/

    Parameters
    ----------
    data: gwpy.timeseries.TimeSeries
        Strain data to be filtered

    Returns
    -------
    filtered_data: gwpy.timeseries.TimeSeries
        The whitened filtered strain data.

    """
    sample_rate = data.sample_rate

    # remove low and high freq
    bp = filter_design.bandpass(20, 1024, sample_rate)

    # notches for harmonics of the 60 Hz AC mains power
    notches = [filter_design.notch(line, sample_rate) for line in (60, 120, 180)]
    # combine filters
    zpk = filter_design.concatenate_zpks(bp, *notches)

    # apply filters
    filtered_data = data.filter(zpk, filtfilt=True)
    filtered_data = filtered_data.whiten()

    # crop corrupted data from filtering
    filtered_data = filtered_data.crop(*filtered_data.span.contract(1))

    return filtered_data


@safe_run
def plot_whitened_data(
    interferometers: bilby.gw.detector.InterferometerList,
    data_directory: str,
    label: str,
):
    """Save a plot of the whitened time and frequency domain strain data.

    Parameters
    ----------
    interferometers: bilby.gw.detector.InterferometerList
        Interferometers to make the plot for
    data_directory: str
            The data dir where the plot is stored.
    label: str
        A string identifier added to the name of the file

    Returns
    -------
    None

    File by the name `<outdir>/data/<Detector>_<label>_whitened_data.png`
    is saved

    """
    for ifo in interferometers:
        whitened_strain = ifo.whitened_frequency_domain_strain
        frequency_window_factor = np.sum(ifo.frequency_mask) / len(ifo.frequency_mask)
        normalization = np.sqrt(np.sum(ifo.frequency_mask)) / frequency_window_factor
        td_strain = np.fft.irfft(whitened_strain) * normalization
        whitened_strain = whitened_strain[ifo.frequency_mask]
        fig, axes = plt.subplots(
            figsize=(12, 8),
            nrows=3,
            ncols=1,
            gridspec_kw=dict(height_ratios=[2, 1, 1]),
        )
        xvalues = ifo.frequency_array[ifo.frequency_mask]
        for ii, strain in enumerate([whitened_strain.real, whitened_strain.imag]):
            kind = ["Frequency domain real", "Frequency domain imaginary"][ii]
            axes[0].hist(
                strain,
                bins=40,
                histtype="step",
                density=True,
                label=kind,
                color=f"C{ii}",
            )
            axes[0].legend(loc="upper right")
            axes[1].plot(xvalues, strain, color=f"C{ii}")
        axes[2].plot(ifo.time_array - ifo.start_time, td_strain, color="C2")
        axes[0].set_xlabel("Whitened strain")
        axes[1].set_xlabel("Frequency [Hz]")
        axes[2].set_xlabel(f"Time - {ifo.start_time} [s]")
        axes[1].set_ylabel("Whitened strain")
        axes[2].set_ylabel("Whitened strain")
        plt.tight_layout()
        plt.savefig(f"{data_directory}/{ifo.name}_{label}_whitened_data.png")
        plt.close(fig)
