import os

from ..node import Node


class PostProcessSingleResultsNode(Node):
    def __init__(self, inputs, merged_node, dag):
        super().__init__(inputs)
        self.dag = dag
        self.request_cpus = 1
        self.job_name = f"{merged_node.label}_postprocess_single"

        self.setup_arguments(
            add_ini=False, add_unknown_args=False, add_command_line_args=False
        )

        alist = self.inputs.single_postprocessing_arguments.split()
        alist = [arg.replace("$RESULT", merged_node.result_file) for arg in alist]

        if self.inputs.transfer_files or self.inputs.osg:
            input_files_to_transfer = inputs.additional_transfer_paths.copy()
            for arg in alist:
                if os.path.isfile(arg):
                    input_files_to_transfer.append(
                        self._relative_topdir(arg, self.inputs.initialdir)
                    )
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

        self.arguments.argument_list = alist
        self.process_node()
        self.job.add_parent(merged_node.job)

    @property
    def executable(self):
        return self._get_executable_path(self.inputs.single_postprocessing_executable)

    @property
    def request_memory(self):
        return "4 GB"

    @property
    def log_directory(self):
        return self.inputs.data_analysis_log_directory


class PostProcessAllResultsNode(Node):
    def __init__(self, inputs, merged_node_list, dag):
        super().__init__(inputs)
        self.dag = dag
        self.request_cpus = 1
        self.job_name = f"{self.inputs.label}_postprocess_all"
        self.setup_arguments(
            add_ini=False, add_unknown_args=False, add_command_line_args=False
        )
        self.arguments.argument_list = self.inputs.postprocessing_arguments

        if self.inputs.transfer_files or self.inputs.osg:
            input_files_to_transfer = inputs.additional_transfer_paths.copy()
            for arg in self.arguments.argument_list:
                if os.path.isfile(arg):
                    input_files_to_transfer.append(
                        self._relative_topdir(arg, self.inputs.initialdir)
                    )
            self.extra_lines.extend(
                self._condor_file_transfer_lines(
                    input_files_to_transfer,
                    [self._relative_topdir(self.inputs.outdir, self.inputs.initialdir)],
                )
            )
            if self.transfer_container:
                input_files_to_transfer.append(self.inputs.container)

        self.process_node()
        for node in merged_node_list:
            self.job.add_parent(node.job)

    @property
    def executable(self):
        return self._get_executable_path(self.inputs.postprocessing_executable)

    @property
    def request_memory(self):
        return "32 GB"

    @property
    def log_directory(self):
        return self.inputs.data_analysis_log_directory
