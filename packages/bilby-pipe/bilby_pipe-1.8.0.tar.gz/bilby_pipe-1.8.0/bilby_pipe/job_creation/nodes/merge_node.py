import os

from ..node import Node


class MergeNode(Node):
    run_node_on_osg = True

    def __init__(self, inputs, parallel_node_list, detectors, dag):
        super().__init__(inputs)
        self.dag = dag

        self.job_name = f"{parallel_node_list[0].base_job_name}_merge"
        self.label = f"{parallel_node_list[0].base_job_name}_merge"
        self.request_cpus = 1

        if self.inputs.transfer_files or self.inputs.osg:
            input_files_to_transfer = [
                self._relative_topdir(pn.result_file, self.inputs.initialdir)
                for pn in parallel_node_list
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
        self.arguments.append("--result")
        for pn in parallel_node_list:
            self.arguments.append(os.path.relpath(pn.result_file))
        self.arguments.add("outdir", os.path.relpath(self.inputs.result_directory))
        self.arguments.add("label", self.label)
        self.arguments.add("extension", self.inputs.result_format)
        self.arguments.add_flag("merge")

        self.process_node()
        for pn in parallel_node_list:
            self.job.add_parent(pn.job)

    @property
    def executable(self):
        return self._get_executable_path("bilby_result")

    @property
    def request_memory(self):
        return "16 GB"

    @property
    def log_directory(self):
        return self.inputs.data_analysis_log_directory

    @property
    def result_file(self):
        return f"{self.inputs.result_directory}/{self.label}_result.{self.inputs.result_format}"
