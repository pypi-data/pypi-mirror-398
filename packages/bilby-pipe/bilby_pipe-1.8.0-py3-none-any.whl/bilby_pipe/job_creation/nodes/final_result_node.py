import os

from ..node import Node


class FinalResultNode(Node):
    run_node_on_osg = True

    def __init__(self, inputs, parent_node, dag):
        super().__init__(inputs)
        self.dag = dag
        self.request_cpus = 1
        self.job_name = f"{parent_node.label}_final_result"

        if self.inputs.transfer_files or self.inputs.osg:
            input_files_to_transfer = [
                self._relative_topdir(parent_node.result_file, self.inputs.initialdir)
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
                    [
                        self._relative_topdir(
                            self.inputs.final_result_directory, self.inputs.initialdir
                        )
                    ],
                )
            )

        self.setup_arguments(
            add_ini=False, add_unknown_args=False, add_command_line_args=False
        )

        self.arguments.add("result", os.path.relpath(parent_node.result_file))
        self.arguments.add("outdir", os.path.relpath(inputs.final_result_directory))
        self.arguments.add("extension", self.inputs.result_format)
        self.arguments.add("max-samples", self.inputs.final_result_nsamples)
        self.arguments.add_flag("lightweight")
        self.arguments.add_flag("save")

        self.process_node()
        self.job.add_parent(parent_node.job)

    @property
    def executable(self):
        return self._get_executable_path("bilby_result")

    @property
    def request_memory(self):
        return "4 GB"

    @property
    def log_directory(self):
        return self.inputs.data_analysis_log_directory
