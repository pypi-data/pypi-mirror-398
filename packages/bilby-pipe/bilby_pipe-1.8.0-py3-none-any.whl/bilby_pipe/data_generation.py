#!/usr/bin/env python
"""Script to perform data generation steps"""
import glob
import os
import sys

import gwpy
import lal
import numpy as np

import bilby
from bilby.gw.detector import PowerSpectralDensity, calibration
from bilby_pipe.input import Input
from bilby_pipe.main import parse_args
from bilby_pipe.parser import create_parser
from bilby_pipe.plotting_utils import plot_whitened_data, strain_spectrogram_plot
from bilby_pipe.utils import (
    BilbyPipeError,
    DataDump,
    convert_string_to_dict,
    get_geocent_time_with_uncertainty,
    get_version_information,
    is_a_power_of_2,
    log_function_call,
    log_version_information,
    logger,
    resolve_filename_with_transfer_fallback,
)

# fmt: off
import matplotlib  # isort:skip
matplotlib.use("agg")
# fmt: on


try:
    import nds2  # noqa
except ImportError:
    logger.warning(
        "You do not have nds2 (python-nds2-client) installed. You may "
        " experience problems accessing interferometer data."
    )

try:
    import LDAStools.frameCPP  # noqa
except ImportError:
    logger.warning(
        "You do not have LDAStools.frameCPP (python-ldas-tools-framecpp) "
        "installed. You may experience problems accessing interferometer data."
    )


class DataGenerationInput(Input):
    """Handles user-input for the data generation script

    Parameters
    ----------
    parser: configargparse.ArgParser, optional
        The parser containing the command line / ini file inputs
    args_list: list, optional
        A list of the arguments to parse. Defaults to `sys.argv[1:]`
    create_data: bool
        If false, no data is generated (used for testing)

    """

    def __init__(self, args, unknown_args, create_data=True):
        super().__init__(args, unknown_args)

        # Generic initialisation
        self.meta_data = dict(
            command_line_args=args.__dict__,
            unknown_command_line_args=unknown_args,
            injection_parameters=None,
            bilby_version=bilby.__version__,
            bilby_pipe_version=get_version_information(),
        )
        self.injection_parameters = None

        # Admin arguments
        self.ini = args.ini
        self.transfer_files = args.transfer_files

        # Global settings
        self.cosmology = args.cosmology

        # Run index arguments
        self.idx = args.idx
        self.generation_seed = args.generation_seed
        self.trigger_time = args.trigger_time

        # Naming arguments
        self.outdir = args.outdir
        self.label = args.label

        # Prior arguments
        self.reference_frame = args.reference_frame
        self.time_reference = args.time_reference
        self.phase_marginalization = args.phase_marginalization
        self.prior_file = args.prior_file
        self.prior_dict = args.prior_dict
        self.deltaT = args.deltaT
        self.default_prior = args.default_prior

        # Data arguments
        self.ignore_gwpy_data_quality_check = args.ignore_gwpy_data_quality_check
        self.detectors = args.detectors
        self.channel_dict = args.channel_dict
        self.fetch_open_data_kwargs = args.fetch_open_data_kwargs
        self.data_dict = args.data_dict
        self.data_format = args.data_format
        self.allow_tape = args.allow_tape
        self.tukey_roll_off = args.tukey_roll_off
        self.gaussian_noise = args.gaussian_noise
        self.zero_noise = args.zero_noise
        self.resampling_method = args.resampling_method

        if args.timeslide_dict is not None:
            self.timeslide_dict = convert_string_to_dict(args.timeslide_dict)
            logger.info(f"Read-in timeslide dict directly: {self.timeslide_dict}")
        elif args.timeslide_file is not None:
            self.gps_file = args.gps_file
            self.timeslide_file = args.timeslide_file
            self.timeslide_dict = self.get_timeslide_dict(self.idx)

        # Data duration arguments
        self.duration = args.duration
        self.post_trigger_duration = args.post_trigger_duration

        # Frequencies
        self.sampling_frequency = args.sampling_frequency
        self.minimum_frequency = args.minimum_frequency
        self.maximum_frequency = args.maximum_frequency
        self.reference_frequency = args.reference_frequency

        # Waveform, source model and likelihood
        self.waveform_generator_class = args.waveform_generator
        self.waveform_generator_class_ctor_args = (
            args.waveform_generator_constructor_dict
        )
        self.waveform_approximant = args.waveform_approximant
        self.catch_waveform_errors = args.catch_waveform_errors
        self.pn_spin_order = args.pn_spin_order
        self.pn_tidal_order = args.pn_tidal_order
        self.pn_phase_order = args.pn_phase_order
        self.pn_amplitude_order = args.pn_amplitude_order
        self.mode_array = args.mode_array
        self.waveform_arguments_dict = args.waveform_arguments_dict
        self.numerical_relativity_file = args.numerical_relativity_file
        self.injection_waveform_approximant = args.injection_waveform_approximant
        self.frequency_domain_source_model = args.frequency_domain_source_model
        self.conversion_function = args.conversion_function
        self.generation_function = args.generation_function
        self.likelihood_type = args.likelihood_type
        self.extra_likelihood_kwargs = args.extra_likelihood_kwargs
        self.enforce_signal_duration = args.enforce_signal_duration

        # PSD
        self.psd_maximum_duration = args.psd_maximum_duration
        self.psd_dict = args.psd_dict
        self.psd_length = args.psd_length
        self.psd_fractional_overlap = args.psd_fractional_overlap
        self.psd_start_time = args.psd_start_time
        self.psd_method = args.psd_method

        # Calibration
        self.calibration_model = args.calibration_model
        self.calibration_correction_type = args.calibration_correction_type
        self.spline_calibration_envelope_dict = args.spline_calibration_envelope_dict
        self.spline_calibration_amplitude_uncertainty_dict = (
            args.spline_calibration_amplitude_uncertainty_dict
        )
        self.spline_calibration_phase_uncertainty_dict = (
            args.spline_calibration_phase_uncertainty_dict
        )
        self.spline_calibration_nodes = args.spline_calibration_nodes
        self.calibration_prior_boundary = args.calibration_prior_boundary

        # ROQ
        self.roq_folder = args.roq_folder
        self.roq_linear_matrix = args.roq_linear_matrix
        self.roq_quadratic_matrix = args.roq_quadratic_matrix
        self.roq_weights = args.roq_weights
        self.roq_weight_format = args.roq_weight_format
        self.roq_scale_factor = args.roq_scale_factor

        # Heterodyning
        if args.fiducial_parameters is not None:
            self.fiducial_parameters = convert_string_to_dict(args.fiducial_parameters)
        else:
            self.fiducial_parameters = args.fiducial_parameters
        self.update_fiducial_parameters = args.update_fiducial_parameters
        if self.fiducial_parameters is None:
            self.update_fiducial_parameters = True
        self.epsilon = args.epsilon

        # Marginalization
        self.distance_marginalization = args.distance_marginalization
        self.distance_marginalization_lookup_table = (
            args.distance_marginalization_lookup_table
        )
        self.phase_marginalization = args.phase_marginalization
        self.time_marginalization = args.time_marginalization
        self.calibration_marginalization = args.calibration_marginalization
        self.calibration_lookup_table = args.calibration_lookup_table
        self.number_of_response_curves = args.number_of_response_curves
        self.jitter_time = args.jitter_time

        # Plotting
        self.plot_data = args.plot_data
        self.plot_spectrogram = args.plot_spectrogram
        self.plot_injection = args.plot_injection

        # Reweighting
        self.reweighting_configuration = args.reweighting_configuration

        if create_data:
            self.create_data(args)

    def create_data(self, args):
        """Function to iterate through data generation method

        Note, the data methods are mutually exclusive and only one can be given to
        the parser.

        Parameters
        ----------
        args: Namespace
            Input arguments

        Raises
        ------
        BilbyPipeError:
            If no data is generated

        """

        self.data_set = False
        self.injection = args.injection
        self.injection_numbers = args.injection_numbers
        self.injection_file = args.injection_file
        self.injection_dict = args.injection_dict
        self.injection_waveform_generator_class_ctor_args = (
            args.injection_waveform_generator_constructor_dict
        )
        self.injection_waveform_arguments = args.injection_waveform_arguments
        self.injection_frequency_domain_source_model = (
            args.injection_frequency_domain_source_model
        )
        # The following are all mutually exclusive methods to set the data
        if self.gaussian_noise or self.zero_noise:
            if args.injection_file is not None:
                logger.debug("Using provided injection file")
                self._set_interferometers_from_injection_in_gaussian_noise()
            elif args.injection_dict is not None:
                logger.debug("Using provided injection dict")
                self._set_interferometers_from_injection_in_gaussian_noise()
            elif args.injection is False:
                self._set_interferometers_from_gaussian_noise()
            else:
                raise BilbyPipeError("Unable to set data: no injection file")
        else:
            self._set_interferometers_from_data()

        if self.data_set is False:
            raise BilbyPipeError("Unable to set data")

    @property
    def generation_seed(self):
        return self._generation_seed

    @generation_seed.setter
    def generation_seed(self, generation_seed):
        """Sets the generation seed.

        If no generation seed has been provided, a random seed between 1 and 1e6 is
        selected.

        If a seed is provided, it is used as the base seed and all generation jobs will
        have their seeds set as {generation_seed = base_seed + job_idx}.

        NOTE: self.idx must not be None

        Parameters
        ----------
        generation_seed: int or None

        """
        if generation_seed is None:
            generation_seed = np.random.randint(1, 1e6)
        else:
            assert self.idx is not None
            generation_seed = generation_seed + self.idx
        self._generation_seed = generation_seed
        bilby.core.utils.random.seed(generation_seed)
        logger.info(f"Generation seed set to {generation_seed}")

    @property
    def injection_parameters(self):
        return self._injection_parameters

    @injection_parameters.setter
    def injection_parameters(self, injection_parameters):
        self._injection_parameters = injection_parameters
        if self.calibration_prior is not None:
            for key in self.calibration_prior:
                if key not in injection_parameters:
                    if "frequency" in key:
                        injection_parameters[key] = self.calibration_prior[key].peak
                    else:
                        injection_parameters[key] = 0
        self.meta_data["injection_parameters"] = injection_parameters

    @property
    def parameter_conversion(self):
        if "binary_neutron_star" in self.frequency_domain_source_model:
            return bilby.gw.conversion.convert_to_lal_binary_neutron_star_parameters
        elif "binary_black_hole" in self.frequency_domain_source_model:
            return bilby.gw.conversion.convert_to_lal_binary_black_hole_parameters
        else:
            return None

    def get_channel_type(self, det):
        """Help method to read the channel_dict and print useful messages"""
        if self.channel_dict is None:
            raise BilbyPipeError("No channel-dict argument provided")
        if det in self.channel_dict:
            return self.channel_dict[det]
        else:
            raise BilbyPipeError(f"Detector {det} not given in the channel-dict")

    @property
    def sampling_frequency(self):
        return self._sampling_frequency

    @sampling_frequency.setter
    def sampling_frequency(self, sampling_frequency):
        if is_a_power_of_2(sampling_frequency) is False:
            logger.warning(
                "Sampling frequency {} not a power of 2, this can cause problems".format(
                    sampling_frequency
                )
            )
        self._sampling_frequency = sampling_frequency

    def _set_interferometers_from_gaussian_noise(self):
        """Method to generate the interferometers data from Gaussian noise"""

        ifos = bilby.gw.detector.InterferometerList(self.detectors)

        if self.psd_dict is not None:
            for ifo in ifos:
                if ifo.name in self.psd_dict.keys():
                    self._set_psd_from_file(ifo)

        if self.zero_noise:
            logger.info("Setting strain data from zero noise")
            ifos.set_strain_data_from_zero_noise(
                sampling_frequency=self.sampling_frequency,
                duration=self.duration,
                start_time=self.start_time,
            )
        else:
            logger.info("Simulating strain data from psd-colored noise")
            ifos.set_strain_data_from_power_spectral_densities(
                sampling_frequency=self.sampling_frequency,
                duration=self.duration,
                start_time=self.start_time,
            )

        self.interferometers = ifos

    def _set_interferometers_from_injection_in_gaussian_noise(self):
        """Method to generate the interferometers data from an injection in Gaussian noise"""

        self.injection_parameters = self.injection_df.iloc[self.idx].to_dict()
        logger.info("Injecting waveform with ")
        for prop in [
            "minimum_frequency",
            "maximum_frequency",
            "trigger_time",
            "start_time",
            "duration",
        ]:
            logger.info(f"{prop} = {getattr(self, prop)}")

        self._set_interferometers_from_gaussian_noise()

        waveform_arguments = self.get_injection_waveform_arguments()
        logger.info(f"Using waveform arguments: {waveform_arguments}")

        injection_waveform_generator_class_ctor_arguments = (
            self.get_default_injection_waveform_generator_class_ctor_arguments()
        )
        waveform_generator = self.waveform_generator_class(
            **injection_waveform_generator_class_ctor_arguments,
            duration=self.duration,
            start_time=self.start_time,
            sampling_frequency=self.sampling_frequency,
            frequency_domain_source_model=self.injection_bilby_frequency_domain_source_model,
            parameter_conversion=self.parameter_conversion,
            waveform_arguments=waveform_arguments,
        )

        self.interferometers.inject_signal(
            waveform_generator=waveform_generator,
            parameters=self.injection_parameters,
            raise_error=self.enforce_signal_duration,
        )

    def inject_signal_into_time_domain_data(self, data, ifo):
        """Method to inject a signal into time-domain interferometer data

        Parameters of the injection are obtained from the `injection_parameters` or
        the injection file (if injection_parameters has not been set).

        The geocent_time of the injection is set to be trigger_time +/- deltaT/2 if
        the geocent_time is not provided in the injection parameters.

        Parameters
        ----------
        data: gwpy.timeseries.TimeSeries
            The data into which to inject the signal
        ifo: bilby.gw.detector.Interferometer
            The interferometer for which the data relates to

        Returns
        -------
        data_and_signal: gwpy.timeseries.TimeSeries
            The data with the signal added

        """

        # Get the injection parameters
        if self.injection_parameters is not None:
            parameters = self.injection_parameters
        else:
            parameters = self.injection_df.iloc[self.idx].to_dict()
            self.injection_parameters = parameters

        # Set the geocent time if none is provided
        if "geocent_time" not in parameters:
            parameters["geocent_time"] = get_geocent_time_with_uncertainty(
                geocent_time=self.trigger_time, uncertainty=self.deltaT / 2.0
            )

        injection_waveform_generator_class_ctor_arguments = (
            self.get_default_injection_waveform_generator_class_ctor_arguments()
        )

        waveform_arguments = self.get_injection_waveform_arguments()

        waveform_generator = self.waveform_generator_class(
            **injection_waveform_generator_class_ctor_arguments,
            duration=self.duration,
            sampling_frequency=self.sampling_frequency,
            frequency_domain_source_model=self.injection_bilby_frequency_domain_source_model,
            parameter_conversion=self.parameter_conversion,
            waveform_arguments=waveform_arguments,
        )

        if self.plot_injection:
            outdir = self.data_directory
            label = self.label
        else:
            outdir = None
            label = None

        logger.info(f"Injecting with {self.injection_waveform_approximant}")
        (
            signal_and_data,
            meta_data,
        ) = bilby.gw.detector.inject_signal_into_gwpy_timeseries(
            data=data,
            waveform_generator=waveform_generator,
            parameters=parameters,
            det=ifo.name,
            power_spectral_density=ifo.power_spectral_density,
            outdir=outdir,
            label=label,
        )
        ifo.meta_data = meta_data

        if self.plot_spectrogram:
            # Plots of before and after injection saved
            plot_kwargs = dict(
                det=ifo.name,
                data_directory=self.data_directory,
                trigger_time=self.trigger_time,
                duration=self.duration,
                post_trigger_duration=self.post_trigger_duration,
                label=self.label,
            )

            strain_spectrogram_plot(
                data=data, extra_label="before_injection", **plot_kwargs
            )
            strain_spectrogram_plot(
                data=signal_and_data, extra_label="with_injection", **plot_kwargs
            )

        return signal_and_data

    def _set_psd_from_file(self, ifo):
        """
        Set the PSD if specified in the `psd_dict`. If the value is `None` leave the
        PSD as is.
        """
        psd_file = self.psd_dict[ifo.name]
        if psd_file is None:
            logger.debug(f"Using default PSD for {ifo.name}")
            return
        logger.info(f"Setting {ifo.name} PSD from file {psd_file}")
        ifo.power_spectral_density = (
            PowerSpectralDensity.from_power_spectral_density_file(psd_file=psd_file)
        )

    def _set_interferometers_from_data(self):
        """
        Method to generate the interferometers data from data

        This sets the PSD before the analysis data so that the SNR of injected
        signals is correct.
        """
        end_time = self.start_time + self.duration
        roll_off = self.tukey_roll_off
        if 2 * roll_off > self.duration:
            raise ValueError("2 * tukey-roll-off is longer than segment duration.")
        ifo_list = []
        for det in self.detectors:
            ifo = bilby.gw.detector.get_empty_interferometer(det)
            ifo.strain_data.roll_off = roll_off

            if self.psd_dict is not None and self.psd_dict.get(det, None) is not None:
                psd_data = None
                self._set_psd_from_file(ifo)
            else:
                logger.info(f"Setting PSD for {det} from data")
                psd_data = self.__get_psd_data(det)
                psd = self.__generate_psd(psd_data, roll_off)
                ifo.power_spectral_density = PowerSpectralDensity(
                    frequency_array=psd.frequencies.value, psd_array=psd.value
                )

            logger.info(f"Getting analysis-segment data for {det}")
            data = self._get_data(
                det, self.get_channel_type(det), self.start_time, end_time
            )
            if self.injection:
                data = self.inject_signal_into_time_domain_data(data, ifo)
            ifo.strain_data.set_from_gwpy_timeseries(data)

            if self.plot_spectrogram:
                self.__plot_ifo_spectrogram(
                    det, strain_data=data, psd_strain_data=psd_data
                )

            ifo_list.append(ifo)

        self.interferometers = bilby.gw.detector.InterferometerList(ifo_list)

    def __get_psd_data(self, det):
        # psd_start_time is given relative to the segment start time
        # so here we calculate the actual start time
        actual_psd_start_time = self.start_time + self.psd_start_time
        actual_psd_end_time = actual_psd_start_time + self.psd_duration
        logger.info(f"Getting psd-segment data for {det}")
        psd_data = self._get_data(
            det, self.get_channel_type(det), actual_psd_start_time, actual_psd_end_time
        )
        return psd_data

    def __generate_psd(self, psd_data, roll_off):
        """Create the psd from strain data."""
        psd_alpha = 2 * roll_off / self.duration
        overlap = self.psd_fractional_overlap * self.duration
        logger.info(
            "PSD settings: window=Tukey, Tukey-alpha={} roll-off={},"
            " overlap={}, method={}".format(
                psd_alpha, roll_off, overlap, self.psd_method
            )
        )
        psd = psd_data.psd(
            fftlength=self.duration,
            overlap=overlap,
            window=("tukey", psd_alpha),
            method=self.psd_method,
        )
        return psd

    def __plot_ifo_spectrogram(self, det, strain_data, psd_strain_data=None):
        """Method to plot an IFO's data.

        Parameters
        ----------
        det: str
            The detector name corresponding to the key in data-dict
        strain_data, psd_strain_data: gwpy.TimeSeries
            The timeseries strain data of a detector.

        Returns
        -------
        None

        File by the name `<outdir>/data/<det>_<Label>_D{duration}_data.png`
        is saved
        """
        if psd_strain_data is None:
            logger.info("Unable to plot the IFO data without the PSD data")
            return
        else:
            plot_psd = True

        plot_kwargs = dict(
            det=det,
            data_directory=self.data_directory,
            trigger_time=self.trigger_time,
            duration=self.duration,
            post_trigger_duration=self.post_trigger_duration,
            label=self.label,
        )

        time = [strain_data.t0.value, strain_data.t0.value + strain_data.duration.value]
        psd_time = [
            psd_strain_data.t0.value,
            psd_strain_data.t0.value + psd_strain_data.duration.value,
        ]

        # plot PSD
        if plot_psd:
            strain_spectrogram_plot(
                data=psd_strain_data,
                extra_label=f"D{int(psd_time[1] - psd_time[0])}",
                **plot_kwargs,
            )

        # plot psd_strain_data+strain_data  and zoom into strain_data segment
        data_with_psd = psd_strain_data.append(strain_data, inplace=False)
        strain_spectrogram_plot(
            data=data_with_psd, extra_label=f"D{int(time[1] - time[0])}", **plot_kwargs
        )

    def _get_data(self, det, channel_type, start_time, end_time, resample=True):
        """Read in data using gwpy

        If the channel_type is "GWOSC", open data is obtained. Otherwise, we
        try to read in the data first using "read" if a data_dict exists and
        then using "get".

        Parameters
        ----------
        channel_type: str
            The full channel name is formed from <det>:<channel_type>, see
            bilby_pipe --help for more information.

        start_time, end_time: float
            GPS start and end time of segment

        Returns
        -------
        data: gwpy.timeseries.TimeSeries
            The loaded data

        Raises
        ------
        BilbyPipeError:
            If there is an issue obtaining the data or with the data itself
        """
        timeslide_val = None
        if hasattr(self, "timeslide_dict"):
            timeslide_val = self.timeslide_dict[det]
            start_time = start_time + timeslide_val
            end_time = end_time + timeslide_val
            logger.info(
                "Applying timeshift of {}. Time range {} - {} => {} - {}".format(
                    timeslide_val,
                    start_time - timeslide_val,
                    end_time - timeslide_val,
                    start_time,
                    end_time,
                )
            )

        if self.ignore_gwpy_data_quality_check is False:
            data_is_good = self._is_gwpy_data_good(start_time, end_time, det)
            if not data_is_good:
                raise BilbyPipeError("Data quality is not good.")

        data = None

        if data is None and channel_type == "GWOSC":
            data = self._gwpy_fetch_open_data(
                det, start_time, end_time, self.fetch_open_data_kwargs
            )

        channel = f"{det}:{channel_type}"
        if data is not None:
            pass
        elif self.data_dict is not None and det in self.data_dict:
            data = self._gwpy_read(det, channel, start_time, end_time)
        else:
            data = self._gwpy_get(channel, start_time, end_time)

        if data is None:
            raise BilbyPipeError("Failed to obtain data")
        if np.all(data.value == 0):
            raise BilbyPipeError("Obtained data is all zeros")

        if data.unit.to_string() != "":
            from astropy.units import dimensionless_unscaled

            logger.warning(
                f"Loaded {det} data has unit '{data.unit.to_string()}', "
                "overwriting to dimensionless"
            )
            data.override_unit(dimensionless_unscaled)

        if resample and data.sample_rate.value == self.sampling_frequency:
            logger.info("Sample rate matches data no resampling")
        elif resample:
            message = "Resampling data to sampling_frequency {} using {}"
            if self.resampling_method == "gwpy":
                logger.info(
                    message.format(self.sampling_frequency, self.resampling_method)
                )
                data = data.resample(self.sampling_frequency)
            elif self.resampling_method == "lal":
                logger.info(
                    message.format(self.sampling_frequency, self.resampling_method)
                )
                try:
                    lal_timeseries = data.to_lal()
                    lal.ResampleREAL8TimeSeries(
                        lal_timeseries, float(1 / self.sampling_frequency)
                    )
                except Exception as e:
                    raise BilbyPipeError(
                        "The lal resampling method has failed with exception {} "
                        "You may wish to try a different resampling method".format(e)
                    )
                data = gwpy.timeseries.TimeSeries(
                    lal_timeseries.data.data,
                    epoch=lal_timeseries.epoch,
                    dt=lal_timeseries.deltaT,
                )
            else:
                logger.warning(
                    "Resampling method {} not understood, should be "
                    "'gwpy' or 'lal'.".format(self.resampling_method)
                )
        else:
            logger.info("No data resampling requested")

        if timeslide_val:
            # to match up the time axis for the interferometer network
            data.shift(-timeslide_val)

        return data

    @staticmethod
    def _is_gwpy_data_good(start_time, end_time, det):
        """Check if start-end time is a period when the IFO has quality data.

        Check passes if the IFO has quality data during the time period provided.

        Note: we are using the ITF_SCIENCE channel to check the quality for V1, and DMT-SCIENCE for other detectors.
        https://labcit.ligo.caltech.edu/~jzweizig/talks/LSC-2009-06-03/DMT-DQ_Stat-2009-06-03.pdf

        This method is slow as it queries GWpy.

        Parameters
        ----------
        start_time, end_time: float
            GPS start and end time of required data.
        det: str
            The string key that represents the detector ("H1", "L1", etc)

        Returns
        -------

        True: if data is good (IFO has quality data during entire duration).
        False: if data is bad (IFO does not have quality data during entire duration).
        None: if the data quality check failed

        """
        # Create data quality flag
        channel_num = 1
        quality_flag = (
            f"{det}:ITF_SCIENCE:{channel_num}"
            if det == "V1"
            else f"{det}:DMT-SCIENCE:{channel_num}"
        )
        logger.info(f"Checking data quality {quality_flag} {start_time}-{end_time}")
        try:
            flag = gwpy.segments.DataQualityFlag.query(
                quality_flag, gwpy.time.to_gps(start_time), gwpy.time.to_gps(end_time)
            )

            # compare active duration from quality flag and total duration
            total_duration = end_time - start_time
            active_duration = float(flag.livetime)
            inactive_duration = total_duration - active_duration

            # data is not good if there is any period when the IFO is inactive
            if inactive_duration > 0:
                data_is_good = False
                logger.warning(
                    "Data quality check: FAILED. \n"
                    "{det} does not have quality data for "
                    "{inactive_duration}s out of {total_duration}s".format(
                        det=det,
                        inactive_duration=inactive_duration,
                        total_duration=total_duration,
                    )
                )
            else:
                data_is_good = True
                logger.info("Data quality check: PASSED.")
        except Exception as e:
            logger.warning(f"Error in Data Quality Check: {e}.")
            data_is_good = None

        return data_is_good

    def _gwpy_read(self, det, channel, start_time, end_time, dtype="float64"):
        """Wrapper function to gwpy.timeseries.TimeSeries.read()

        Parameters
        ----------
        det: str
            The detector name corresponding to the key in data-dict
        channel: str
            The name of the channel to read, e.g. 'L1:GDS-CALIB_STRAIN'
        start_time, end_time: float
            GPS start and end time of required data
        dtype: str or np.dtype
            Data type requested

        Returns
        -------
        data: TimeSeries
            If successful, the data, otherwise None is returned

        """

        logger.debug("data-dict provided, attempt read of data")

        if det not in self.data_dict:
            logger.info(f"Detector {det} not found in data-dict")
            return None
        else:
            source = self.data_dict[det]
            if isinstance(source, str):
                format_ext = os.path.splitext(source)[1]
            elif isinstance(source, list):
                format_ext = os.path.splitext(source[0])[1]
            else:
                raise TypeError(
                    f"Frames should be either string or list, not {type(source)}"
                )

        # If the source contains a glob-path, e.g. *gwf, glob it first
        if "*" in source:
            logger.info(f"Globbing {source}")
            source = glob.glob(source)
            logger.info(f"Setting source={source}")

        if "gwf" in format_ext:
            kwargs = dict(source=source, channel=channel)
            type_kwargs = dict(dtype=dtype, subok=True, copy=False)
        elif "hdf5" in format_ext:
            kwargs = dict(source=source, start=start_time, end=end_time, format="hdf5")
        elif "txt" in format_ext:
            data = kwargs = dict(source=source)
        else:
            # Generic best try
            kwargs = dict(
                source=source, channel=channel, start=start_time, end=end_time
            )

        if self.data_format is not None:
            kwargs["format"] = self.data_format

        try:
            if "gwf" in format_ext:
                _call = log_function_call(
                    "gwpy.timeseries.TimeSeries.read", kwargs, log=False
                )
                log_function_call(f"{_call}.astype", type_kwargs)
                data = gwpy.timeseries.TimeSeries.read(**kwargs).astype(**type_kwargs)

            else:
                log_function_call("gwpy.timeseries.TimeSeries.read", kwargs)
                data = gwpy.timeseries.TimeSeries.read(**kwargs)

            data = data.crop(start=start_time, end=end_time)

            if data.duration.value < end_time - start_time:
                logger.warning(
                    "Unable to read in requested {}s duration of data from {}"
                    " only {}s available: returning None".format(
                        end_time - start_time, source, data.duration.value
                    )
                )
                data = None
            elif data.duration.value > end_time - start_time:
                logger.info(
                    "Read in {}s of data from {}, but {}s requested, truncating".format(
                        data.duration.value, source, end_time - start_time
                    )
                )
                data = data[data.times.value >= start_time]
                data = data[data.times.value < end_time]

            return data
        except ValueError as e:
            logger.info(f"Reading of data failed with error {e}")
            return None

    def _gwpy_get(self, channel, start_time, end_time, dtype="float64"):
        """Wrapper function to gwpy.timeseries.TimeSeries.get()

        Parameters
        ----------
        channel: str
            The name of the channel to read, e.g. 'L1:GDS-CALIB_STRAIN'
        start_time, end_time: float
            GPS start and end time of required data
        dtype: str or np.dtype
            Data type requested

        Returns
        -------
        data: TimeSeries
            If successful, the data, otherwise None is returned

        """
        logger.debug("Attempt to locate data")

        kwargs = dict(
            channel=channel,
            start=start_time,
            end=end_time,
            verbose=False,
            allow_tape=self.allow_tape,
        )

        type_kwargs = dict(
            dtype=dtype,
            subok=True,
            copy=False,
        )

        if self.data_format:
            kwargs["format"] = self.data_format

        _call = log_function_call("gwpy.timeseries.TimeSeries.get", kwargs, log=False)
        log_function_call(f"{_call}.astype", type_kwargs)

        try:
            data = gwpy.timeseries.TimeSeries.get(**kwargs).astype(**type_kwargs)
            return data
        except RuntimeError as e:
            logger.info(
                f"Unable to read data for channel {channel}. "
                "You may need to set the GWDATAFIND_SERVER environment variable."
            )
            logger.debug(f"Error message {e}")
        except ImportError:
            logger.info("Unable to read data as NDS2 is not installed")
        except TypeError:
            logger.debug("Problem reading data try again without kwargs")
            kwargs = dict(
                channel=channel,
                start=start_time,
                end=end_time,
                verbose=False,
            )
            _call = log_function_call(
                "gwpy.timeseries.TimeSeries.get", kwargs, log=False
            )
            log_function_call(f"{_call}.astype", type_kwargs)
            data = gwpy.timeseries.TimeSeries.get(**kwargs).astype(**type_kwargs)
            return data

    def _gwpy_fetch_open_data(
        self, det, start_time, end_time, fetch_open_data_kwargs=None
    ):
        """Wrapper function to gwpy.timeseries.TimeSeries.fetch_open_data()

        By default, this requests data at a sampling frequency of 16384 Hz. If instead
        you prefer to use the 4096 Hz data, specify `sample_rate=4096` in the
        `fetch-open-data-kwargs`.

        Parameters
        ----------
        det: str
            The detector name, e.g 'H1'
        start_time, end_time: float
            GPS start and end time of required data
        fetch_open_data_kwargs: dict
            Any optional keyword arguments to pass to `fetch_open_data`

        Returns
        -------
        data: TimeSeries
            If successful, the data, otherwise None is returned

        """

        logger.info("Attempting to download data from GWOSC")
        kwargs = dict(ifo=det, start=start_time, end=end_time, sample_rate=16384)
        if fetch_open_data_kwargs is not None:
            kwargs.update(fetch_open_data_kwargs)
        log_function_call("gwpy.timeseries.TimeSeries.fetch_open_data", kwargs)
        data = gwpy.timeseries.TimeSeries.fetch_open_data(**kwargs)
        return data

    @property
    def interferometers(self):
        """A bilby.gw.detector.InterferometerList"""
        try:
            return self._interferometers
        except AttributeError:
            raise ValueError(
                "interferometers unset, did you provide a set-data method?"
            )

    def add_calibration_model_to_interferometers(self, ifo):
        if self.calibration_model in [None, "Recalibrate"]:
            ifo.calibration_model = bilby.gw.calibration.Recalibrate()
        elif self.calibration_model == "CubicSpline":
            ifo.calibration_model = bilby.gw.calibration.CubicSpline(
                prefix=f"recalib_{ifo.name}_",
                minimum_frequency=ifo.minimum_frequency,
                maximum_frequency=ifo.maximum_frequency,
                n_points=self.spline_calibration_nodes,
            )
        elif self.calibration_model == "Precomputed":
            model = bilby.gw.calibration.Precomputed
            det = ifo.name
            if (
                self.spline_calibration_envelope_dict is not None
                and det in self.spline_calibration_envelope_dict
            ):
                original = self.spline_calibration_envelope_dict[det]
                fname = resolve_filename_with_transfer_fallback(original)
                if fname is None:
                    raise ValueError(f"Failed to find calibration file {original}.")

                ifo.calibration_model = model.from_envelope_file(
                    fname,
                    frequency_array=ifo.frequency_array[ifo.frequency_mask],
                    n_nodes=self.spline_calibration_nodes,
                    label=det,
                    n_curves=1000,
                    correction_type=self.calibration_correction_type[det],
                )
            elif (
                det in self.spline_calibration_amplitude_uncertainty_dict
                and det in self.spline_calibration_phase_uncertainty_dict
            ):
                ifo.calibration_model = model.constant_uncertainty_spline(
                    amplitude_sigma=self.spline_calibration_amplitude_uncertainty_dict[
                        det
                    ],
                    phase_sigma=self.spline_calibration_phase_uncertainty_dict[det],
                    frequency_array=ifo.frequency_array[ifo.frequency_mask],
                    n_nodes=self.spline_calibration_nodes,
                    label=det,
                    n_curves=1000,
                )
        else:
            raise BilbyPipeError(
                f"calibration model {self.calibration_model} not implemented"
            )

    @interferometers.setter
    def interferometers(self, interferometers):
        for ifo in interferometers:
            if isinstance(ifo, bilby.gw.detector.Interferometer) is False:
                raise BilbyPipeError(f"ifo={ifo} is not a bilby Interferometer")
            if self.minimum_frequency is not None:
                ifo.minimum_frequency = self.minimum_frequency_dict[ifo.name]
            if self.maximum_frequency is not None:
                ifo.maximum_frequency = self.maximum_frequency_dict[ifo.name]
            if self.calibration_model is not None:
                self.add_calibration_model_to_interferometers(ifo)

        self._interferometers = interferometers
        self.data_set = True
        if self.plot_data:
            interferometers.plot_data(outdir=self.data_directory, label=self.label)
            plot_whitened_data(
                interferometers=interferometers,
                data_directory=self.data_directory,
                label=self.label,
            )

    def build_calibration_lookups_if_needed(self):
        """
        Build lookup files that are needed for incorporating calibration uncertainty.
        These are needed if:

          - :code:`calibration_marginalization` is used either during sampling or
            post-processing
          - the calibration model is :code:`Precomputed`
        """
        sampling_calibration = self.calibration_model
        sampling_marginalization = self.calibration_marginalization
        calibration_lookup = self.calibration_lookup_table
        n_response = self.number_of_response_curves
        if self.reweighting_configuration is not None:
            data = self.reweighting_configuration
            if "calibration-model" in data:
                self.calibration_model = data["calibration-model"]
                for ifo in self.interferometers:
                    self.add_calibration_model_to_interferometers(ifo)
            if "calibration-marginalization" in data:
                self.calibration_marginalization = data["calibration-marginalization"]
            if "calibration-lookup-table" in data:
                self.calibration_lookup_table = data["calibration-lookup-table"]
            if "number-of-response-curves" in data:
                self.number_of_response_curves = data["number-of-response-curves"]

        if (
            self.calibration_marginalization
            or self.calibration_model == "Precomputed"
            or self.calibration_lookup_table
        ):
            calibration.build_calibration_lookup(
                interferometers=self.interferometers,
                lookup_files=self.calibration_lookup_table,
                priors=self.calibration_prior,
                number_of_response_curves=self.number_of_response_curves,
            )
        self.calibration_model = sampling_calibration
        for ifo in self.interferometers:
            self.add_calibration_model_to_interferometers(ifo)
        self.calibration_marginalization = sampling_marginalization
        self.calibration_lookup_table = calibration_lookup
        self.number_of_response_curves = n_response

    def save_data_dump(self):
        """Method to dump the saved data to disk for later analysis"""
        self.build_calibration_lookups_if_needed()

        likelihood = self.likelihood
        if self.distance_marginalization:
            likelihood_lookup_table = dict(
                np.load(likelihood.cached_lookup_table_filename)
            )
        else:
            likelihood_lookup_table = None
        if hasattr(likelihood, "fiducial_parameters"):
            self.meta_data["fiducial_parameters"] = likelihood.fiducial_parameters
        if self.is_likelihood_multiband:
            likelihood_roq_weights = None
            likelihood_multiband_weights = likelihood.weights
        else:
            likelihood_roq_weights = getattr(likelihood, "weights", None)
            likelihood_multiband_weights = None
        self.meta_data["reweighting_configuration"] = self.reweighting_configuration
        data_dump = DataDump(
            outdir=self.data_directory,
            label=self.label,
            idx=self.idx,
            trigger_time=self.trigger_time,
            interferometers=self.interferometers,
            meta_data=self.meta_data,
            likelihood_lookup_table=likelihood_lookup_table,
            likelihood_roq_weights=likelihood_roq_weights,
            likelihood_roq_params=getattr(likelihood, "roq_params", None),
            likelihood_multiband_weights=likelihood_multiband_weights,
            priors_dict=dict(self.priors),
            priors_class=self.priors.__class__,
        )
        data_dump.to_pickle()

    def save_roq_weights(self):
        if self.likelihood_type != "ROQGravitationalWaveTransient":
            raise ValueError(
                "ROQ weights can only be saved for ROQGravitationalWaveTransient"
            )
        if getattr(self, "likelihood_roq_weights", None) is not None:
            self.setup_roq_weights()
        weight_file = os.path.join(
            self.data_directory, f"{self.label}_roq_weights.{self.roq_weight_format}"
        )
        self.meta_data["weight_file"] = weight_file
        self.likelihood.save_weights(weight_file, format=self.roq_weight_format)

    def save_multiband_weights(self):
        if not self.is_likelihood_multiband:
            raise ValueError(
                "Multiband weights can only be saved for "
                "MultibandGravitationalWaveTransient"
            )
        weight_file = os.path.join(
            self.data_directory, f"{self.label}_multiband_weights.hdf5"
        )
        self.meta_data["weight_file"] = weight_file
        self.likelihood.save_weights(weight_file)

    @property
    def injection_frequency_domain_source_model(self):
        """String of which frequency domain source model to use for injection"""
        return self._injection_frequency_domain_source_model

    @injection_frequency_domain_source_model.setter
    def injection_frequency_domain_source_model(
        self, injection_frequency_domain_source_model
    ):
        if injection_frequency_domain_source_model is None:
            self._injection_frequency_domain_source_model = (
                self.frequency_domain_source_model
            )
        else:
            self._injection_frequency_domain_source_model = (
                injection_frequency_domain_source_model
            )

    @property
    def injection_bilby_frequency_domain_source_model(self):
        """Frequency domain source model function to use for injecting waveform"""
        return self.get_bilby_source_model_function(
            self.injection_frequency_domain_source_model
        )


def create_generation_parser():
    """Data generation parser creation"""
    return create_parser(top_level=False)


def main():
    """Data generation main logic"""
    args, unknown_args = parse_args(sys.argv[1:], create_generation_parser())
    log_version_information()
    data = DataGenerationInput(args, unknown_args)
    data.save_data_dump()
    logger.info("Completed data generation")
