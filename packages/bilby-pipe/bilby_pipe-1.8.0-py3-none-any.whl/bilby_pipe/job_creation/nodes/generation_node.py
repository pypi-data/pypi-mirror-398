import os

from ...utils import (
    DEFAULT_GWDATAFIND_SERVER,
    BilbyPipeError,
    DataDump,
    log_function_call,
    logger,
)
from ..node import Node


class GenerationNode(Node):
    def __init__(self, inputs, trigger_time, idx, dag, parent=None):
        """
        Node for data generation jobs

        Parameters
        ----------
        inputs: bilby_pipe.main.MainInput
            The user-defined inputs
        trigger_time: float
            The trigger time to use in generating analysis data
        idx: int
            The index of the data-generation job, used to label data products
        dag: bilby_pipe.dag.Dag
            The dag structure
        parent: bilby_pipe.job_creation.node.Node (optional)
            Any job to set as the parent to this job - used to enforce
            dependencies
        """

        super().__init__(inputs, retry=3)
        if not inputs.osg and inputs.generation_pool == "igwn-pool":
            raise BilbyPipeError(
                "Generation job requested to use the igwn-pool "
                "(OSG, --generation-pool=igwn-pool), but --osg=False"
            )
        else:
            self.run_node_on_osg = inputs.generation_pool == "igwn-pool"
        self.inputs = inputs
        self.trigger_time = trigger_time
        self.inputs.trigger_time = trigger_time
        self.idx = idx
        self.dag = dag
        self.request_cpus = 1

        self.setup_arguments()
        self.arguments.add("label", self.label)
        self.arguments.add("idx", self.idx)
        self.arguments.add("trigger-time", self.trigger_time)
        if self.inputs.injection_file is not None:
            self.arguments.add("injection-file", self.inputs.injection_file)
        if self.inputs.timeslide_file is not None:
            self.arguments.add("timeslide-file", self.inputs.timeslide_file)

        frame_files, success = self.resolve_frame_files
        need_scitokens = not success

        if self.inputs.transfer_files or self.inputs.osg:
            input_files_to_transfer = list()
            for attr in [
                "complete_ini_file",
                "prior_file",
                "injection_file",
                "gps_file",
                "timeslide_file",
            ]:
                if (value := getattr(self.inputs, attr)) is not None:
                    # input_files_to_transfer.append(str(value))
                    input_files_to_transfer.append(os.path.abspath(str(value)))
            if self.transfer_container:
                input_files_to_transfer.append(self.inputs.container)
            for value in [
                self.inputs.psd_dict,
                self.inputs.spline_calibration_envelope_dict,
                frame_files,
            ]:
                input_files_to_transfer.extend(self.extract_paths_from_dict(value))
            input_files_to_transfer.extend(self.inputs.additional_transfer_paths)

            input_files_to_transfer, need_auth = self.job_needs_authentication(
                input_files_to_transfer
            )
            need_scitokens = need_scitokens or need_auth

            self.extra_lines.extend(
                self._condor_file_transfer_lines(
                    input_files_to_transfer,
                    [self._relative_topdir(self.inputs.outdir, self.inputs.initialdir)],
                )
            )
            self.arguments.add("outdir", os.path.relpath(self.inputs.outdir))

        elif new_frames := [
            fname
            for fname in self.extract_paths_from_dict(frame_files)
            if fname.startswith(self.inputs.data_find_urltype)
        ]:
            logger.warning(
                "The following frame files were identified by gwdatafind for this analysis. "
                "These frames may not be found by the data generation stage as file "
                "transfer is not being used. You should either set transfer-files=True or "
                "pass these frame files to the data-dict option. You may need to "
                f"remove a prefix, e.g., file://localhost.\n\t{new_frames}"
            )
        if need_scitokens:
            self.extra_lines.extend(self.scitoken_lines)

        self.process_node()
        if parent:
            self.job.add_parent(parent.job)

    @property
    def resolve_frame_files(self):
        """
        Resolve frame files from frame_type_dict and data_dict.
        For each detector, if the frame filepath(s) is given
        return the filepath(s), otherwise use gwdatafind to
        resolve the frame files using the provided frame type.

        Returns
        -------
        output: list
            list of frame filepaths
        success: bool
            True if frame files are resolved successfully for all detectors
        """
        from gwdatafind import find_urls
        from gwpy.io.datafind import find_best_frametype
        from requests.exceptions import HTTPError

        success = True
        if self.inputs.gaussian_noise or self.inputs.zero_noise:
            return list(), success
        elif self.inputs.channel_dict is None:
            raise BilbyPipeError(
                "channel-dict must be provided if not using gaussian-noise or zero-noise"
            )

        data = dict()
        if self.inputs.frame_type_dict is not None:
            data = self.inputs.frame_type_dict
        if self.inputs.data_dict is not None:
            data.update(self.inputs.data_dict)
        output = dict()
        for det in self.inputs.detectors:
            if (
                self.inputs.channel_dict is not None
                and self.inputs.channel_dict[det] == "GWOSC"
            ):
                logger.info(f"Skipping datafind for {det} as GWOSC data is used.")
            elif isinstance(data.get(det, None), list):
                output[det] = data[det]
            elif os.path.exists(data.get(det, "/not/a/real/file")):
                output[det] = [data[det]]
            else:
                start_time = self.inputs.start_time
                end_time = self.inputs.start_time + self.inputs.duration
                if (
                    self.inputs.psd_dict is None
                    or self.inputs.psd_dict.get(det, None) is None
                ):
                    start_time -= self.inputs.psd_duration

                # If data_find_url is not set, use the environment variable
                # GWDATAFIND_SERVER, otherwise use the default from bilby_pipe.utils
                if self.inputs.data_find_url is None:
                    datafind_server = os.environ.get("GWDATAFIND_SERVER")
                    if datafind_server is None:
                        logger.warning(
                            (
                                "GWDATAFIND_SERVER not set, using default "
                                f"gwdatafind server: {DEFAULT_GWDATAFIND_SERVER}"
                            )
                        )
                        datafind_server = DEFAULT_GWDATAFIND_SERVER
                else:
                    datafind_server = self.inputs.data_find_url
                if det not in data:
                    channel_name = self.inputs.channel_dict[det]
                    if not channel_name.startswith(f"{det}:"):
                        channel_name = f"{det}:{channel_name}"
                    frame_type = find_best_frametype(
                        channel_name,
                        start_time,
                        end_time,
                        host=datafind_server,
                    )
                else:
                    frame_type = data[det]
                kwargs = dict(
                    site=det[0],
                    gpsstart=start_time,
                    gpsend=end_time,
                    urltype=self.inputs.data_find_urltype,
                    host=datafind_server,
                    on_gaps="error",
                    frametype=frame_type,
                )
                log_function_call("gwdatafind.find_urls", kwargs)
                try:
                    output[det] = find_urls(**kwargs)
                    logger.info(f"Found frame files with {frame_type}")
                except (HTTPError, RuntimeError):
                    logger.warning(
                        f"Failed to resolve frame files for detector {det}, the generation "
                        "job will attempt with gwpy.get."
                    )
                    success = False
        return output, success

    @property
    def executable(self):
        return self._get_executable_path("bilby_pipe_generation")

    @property
    def request_memory(self):
        return self.inputs.request_memory_generation

    @property
    def log_directory(self):
        return self.inputs.data_generation_log_directory

    @property
    def universe(self):
        if self.inputs.local_generation:
            logger.debug(
                "Data generation done locally: please do not use this when "
                "submitting a large number of jobs"
            )
            universe = "local"
        else:
            logger.debug(f"All data will be grabbed in the {self._universe} universe")
            universe = self._universe
        return universe

    @property
    def job_name(self):
        job_name = "{}_data{}_{}_generation".format(
            self.inputs.label, str(self.idx), self.trigger_time
        )
        job_name = job_name.replace(".", "-")
        return job_name

    @property
    def label(self):
        return self.job_name

    @property
    def data_dump_file(self):
        return DataDump.get_filename(self.inputs.data_directory, self.label)
