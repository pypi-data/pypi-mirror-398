import os
from pathlib import Path

from ...utils import check_directory_exists_and_if_not_mkdir
from ..node import Node


class AnalysisNode(Node):
    # If --osg, run analysis nodes on the OSG
    run_node_on_osg = True

    def __init__(self, inputs, generation_node, detectors, sampler, parallel_idx, dag):
        super().__init__(inputs, retry=3)
        self.dag = dag
        self.generation_node = generation_node
        self.detectors = detectors
        self.parallel_idx = parallel_idx
        self.request_cpus = inputs.request_cpus

        data_label = generation_node.job_name
        base_name = data_label.replace("generation", "analysis")
        self.base_job_name = f"{base_name}_{''.join(detectors)}"
        if parallel_idx != "":
            self.job_name = f"{self.base_job_name}_{parallel_idx}"
        else:
            self.job_name = self.base_job_name
        self.label = self.job_name

        if self.inputs.use_mpi:
            self.setup_arguments(
                parallel_program=self._get_executable_path(
                    self.inputs.analysis_executable
                )
            )

        else:
            self.setup_arguments()

        if self.inputs.transfer_files or self.inputs.osg:
            data_dump_file = generation_node.data_dump_file
            input_files_to_transfer = (
                [
                    str(data_dump_file),
                    str(self.inputs.complete_ini_file),
                ]
                + touch_checkpoint_files(
                    os.path.join(inputs.outdir, "result"),
                    self.job_name,
                    inputs.sampler,
                    inputs.result_format,
                )
                + inputs.additional_transfer_paths
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
            self.arguments.add("outdir", os.path.relpath(self.inputs.outdir))

        for det in detectors:
            self.arguments.add("detectors", det)
        self.arguments.add("label", self.label)
        self.arguments.add("data-dump-file", generation_node.data_dump_file)
        self.arguments.add("sampler", sampler)
        if self.parallel_idx and self.inputs.sampling_seed:
            self.arguments.add(
                "sampling-seed",
                str(int(self.inputs.sampling_seed) + int(self.parallel_idx[3:])),
            )

        self.extra_lines.extend(self._checkpoint_submit_lines())

        self.process_node()
        self.job.add_parent(generation_node.job)

    @property
    def executable(self):
        if self.inputs.use_mpi:
            return self._get_executable_path("mpiexec")
        elif self.inputs.analysis_executable:
            return self._get_executable_path(self.inputs.analysis_executable)
        else:
            return self._get_executable_path("bilby_pipe_analysis")

    @property
    def request_memory(self):
        return self.inputs.request_memory

    @property
    def log_directory(self):
        return self.inputs.data_analysis_log_directory

    @property
    def result_file(self):
        return f"{self.inputs.result_directory}/{self.job_name}_result.{self.inputs.result_format}"

    @property
    def slurm_walltime(self):
        """Default wall-time for base-name"""
        # Seven days
        return self.inputs.scheduler_analysis_time


def touch_checkpoint_files(directory, label, sampler, result_format="hdf5"):
    """
    Figure out the pathnames required to recover from a checkpoint.

    Uses the :code:`get_expected_outputs` method for the corresponding sampler
    class.
    """
    from bilby.core.sampler import get_sampler_class

    def touch_pickle_file(filename):
        import dill

        if not Path(filename).exists():
            with open(filename, "wb") as ff:
                dill.dump(dict(), ff)

    def touch_file(filename):
        open(filename, "a").close()

    check_directory_exists_and_if_not_mkdir(directory=directory)
    result_file = Path(directory) / f"{label}_result.{result_format}"
    result_file.touch()
    filenames = [str(result_file)]

    sampler_filenames, sampler_directories = get_sampler_class(
        sampler.lower()
    ).get_expected_outputs(
        outdir=directory,
        label=label,
    )

    for filename in sampler_filenames:
        if filename.endswith((".pkl", ".pickle")):
            touch_pickle_file(filename)
        else:
            touch_file(filename)
    filenames += sampler_filenames

    for dirname in sampler_directories:
        check_directory_exists_and_if_not_mkdir(directory=dirname)
    filenames += sampler_directories

    return filenames
