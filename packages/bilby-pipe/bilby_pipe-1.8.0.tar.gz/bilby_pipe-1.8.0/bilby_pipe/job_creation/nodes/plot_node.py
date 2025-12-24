import os

from ...utils import DataDump, logger
from ..node import Node


class PlotNode(Node):
    run_node_on_osg = True

    def __init__(self, inputs, merged_node, dag):
        super().__init__(inputs)
        self.dag = dag
        self.job_name = merged_node.job_name + "_plot"
        self.label = merged_node.job_name + "_plot"
        self.request_cpus = 1

        if self.inputs.transfer_files or self.inputs.osg:
            input_files_to_transfer = [
                self._relative_topdir(merged_node.result_file, self.inputs.initialdir),
                self._relative_topdir(self.data_dump_file, self.inputs.initialdir),
            ] + inputs.additional_transfer_paths
            if self.transfer_container:
                input_files_to_transfer.append(self.inputs.container)

            input_files_to_transfer, need_scitokens = self.job_needs_authentication(
                input_files_to_transfer
            )
            if need_scitokens:
                self.extra_lines.extend(self.scitoken_lines)

            self.extra_lines.extend(
                self._condor_file_transfer_lines(
                    input_files_to_transfer,
                    [self._relative_topdir(self.inputs.outdir, self.inputs.initialdir)],
                )
            )

        self.setup_arguments(
            add_ini=False, add_unknown_args=False, add_command_line_args=False
        )
        self.arguments.add("result", os.path.relpath(merged_node.result_file))
        self.arguments.add("outdir", os.path.relpath(self.inputs.result_directory))
        for plot_type in ["calibration", "corner", "marginal", "skymap", "waveform"]:
            if getattr(inputs, f"plot_{plot_type}", False):
                self.arguments.add_flag(plot_type)
        self.arguments.add("format", inputs.plot_format)

        self.process_node()
        self.job.add_parent(merged_node.job)

    @property
    def data_dump_file(self):
        label = self.label.split("analysis")[0] + "generation"
        return DataDump.get_filename(self.inputs.data_directory, label)

    @property
    def executable(self):
        return self._get_executable_path("bilby_pipe_plot")

    @property
    def request_memory(self):
        return "32 GB"

    @property
    def log_directory(self):
        return self.inputs.data_analysis_log_directory

    @property
    def universe(self):
        if self.inputs.local_plot:
            logger.debug(
                "Data plotting done locally: please do not use this when "
                "submitting a large number of jobs"
            )
            universe = "local"
        else:
            logger.debug(f"All data will be grabbed in the {self._universe} universe")
            universe = self._universe
        return universe
