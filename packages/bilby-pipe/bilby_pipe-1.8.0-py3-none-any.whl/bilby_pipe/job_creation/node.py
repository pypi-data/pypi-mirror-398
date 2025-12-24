import os
import re
import shutil
import subprocess
from pathlib import Path

import pycondor

from ..utils import (
    CHECKPOINT_EXIT_CODE,
    ArgumentsString,
    BilbyPipeError,
    get_environment_variables_dictionary,
    logger,
)


class Node(object):
    """Base Node object, handles creation of arguments, executables, etc"""

    # Flag to not run on the OSG - overwritten in child nodes
    run_node_on_osg = False

    def __init__(self, inputs, retry=None):
        self.inputs = inputs
        self._universe = "vanilla"
        self.request_disk = self.inputs.request_disk
        self.notification = inputs.notification
        self.retry = retry
        self.verbose = 0
        self.condor_job_priority = inputs.condor_job_priority
        self.disable_hdf5_locking = inputs.disable_hdf5_locking
        self.extra_lines = list(self.inputs.extra_lines)
        self.requirements = (
            [self.inputs.requirements] if self.inputs.requirements else []
        )

    @property
    def universe(self):
        return self._universe

    def process_node(self):
        self.create_pycondor_job()

        if self.inputs.run_local:
            logger.info(
                "Running command: "
                + " ".join([self.executable] + self.arguments.argument_list)
            )
            subprocess.run([self.executable] + self.arguments.argument_list, check=True)

    def _get_executable_path(self, exe_name):
        if self.inputs._conda_path is not None:
            if self.inputs._conda_path not in exe_name:
                return os.path.join(
                    self.inputs._conda_path,
                    "bin",
                    exe_name,
                )
            else:
                return exe_name

        exe = shutil.which(exe_name)
        if self.inputs.container is not None:
            return exe_name
        elif exe is not None:
            return exe
        else:
            raise OSError(f"{exe_name} not installed on this system, unable to proceed")

    def setup_arguments(
        self,
        parallel_program=None,
        add_command_line_args=True,
        add_ini=True,
        add_unknown_args=True,
    ):
        self.arguments = ArgumentsString()
        if parallel_program is not None:
            self.arguments.add("np", self.inputs.request_cpus)
            self.arguments.add_positional_argument(parallel_program)
        if add_ini:
            self.arguments.add_positional_argument(self.inputs.complete_ini_file)
        if add_unknown_args:
            self.arguments.add_unknown_args(self.inputs.unknown_args)
        if add_command_line_args:
            self.arguments.add_command_line_arguments()

    @property
    def log_directory(self):
        raise NotImplementedError()

    def create_pycondor_job(self):
        job_name = self.job_name
        self.extra_lines.extend(
            _log_output_error_submit_lines(self.log_directory, job_name)
        )

        if self.inputs.scheduler.lower() == "condor" and not self.inputs.run_local:
            self.add_accounting()

        self.extra_lines.append(f"priority = {self.condor_job_priority}")
        env = self.environment
        self.extra_lines.append(
            f'environment = "{" ".join([f"{k}={v}" for k, v in env.items()])}"'
        )
        if self.inputs.email is not None:
            self.extra_lines.append(f"notify_user = {self.inputs.email}")

        if self.inputs.queue is not None:
            self.extra_lines.append(f"+{self.inputs.queue} = True")
            self.requirements.append(f"((TARGET.{self.inputs.queue} =?= True))")

        if self.universe != "local" and self.inputs.osg:
            sites = self.inputs.desired_sites
            if self.run_node_on_osg and sites != "nogrid":
                _osg_lines, _osg_reqs = self._osg_submit_options(
                    self.executable, has_ligo_frames=False
                )
                self.extra_lines.extend(_osg_lines)
                self.requirements.extend(_osg_reqs)
            else:
                sites = "nogrid"
            if sites == "nogrid":
                self.extra_lines.append("MY.flock_local = True")
                self.extra_lines.append('MY.DESIRED_Sites = "nogrid"')
            # FIXME: find a more permanent solution to allow desired sites to
            # be passed to merge jobs
            elif sites is not None and self.__class__.__name__ == "AnalysisNode":
                self.extra_lines.append(f'MY.DESIRED_Sites = "{sites}"')
                self.requirements.append("IS_GLIDEIN=?=True")
            else:
                self.extra_lines.append("MY.flock_local = True")
        elif not self.inputs.osg:
            # these lines ignore the OSG for jobs submitted from LDAS OSG
            # access points see
            # https://computing.docs.ligo.org/guide/htcondor/access/?h=flock#flock_local
            # for more details
            self.extra_lines.append("MY.flock_local = True")
            self.extra_lines.append('MY.DESIRED_Sites = "nogrid"')

        if self.inputs.container is not None:
            if self.universe == "local":
                raise BilbyPipeError(
                    "Cannot use containers with HTCondor local universe."
                )
            if self.transfer_container:
                container = f"./{os.path.basename(self.inputs.container)}"
            else:
                container = self.inputs.container
            self.extra_lines.append(f'MY.SingularityImage = "{container}"')
            self.extra_lines.append("transfer_executable = False")
            self.requirements.append("(HAS_SINGULARITY=?=True)")

        self.job = pycondor.Job(
            name=job_name,
            executable=self.executable,
            submit=self.inputs.submit_directory,
            request_memory=self.request_memory,
            request_disk=self.request_disk,
            request_cpus=self.request_cpus,
            universe=self.universe,
            initialdir=self.inputs.initialdir,
            notification=self.notification,
            requirements=" && ".join(self.requirements),
            extra_lines=self.extra_lines,
            dag=self.dag.pycondor_dag,
            arguments=self.arguments.print(),
            retry=self.retry,
            verbose=self.verbose,
        )

        # Hack to allow passing walltime down to slurm
        setattr(self.job, "slurm_walltime", self.slurm_walltime)

        logger.debug(f"Adding job: {job_name}")

    def add_accounting(self):
        """Add the accounting-group and accounting-group-user extra lines"""
        if self.inputs.accounting:
            self.extra_lines.append(f"accounting_group = {self.inputs.accounting}")
            # Check for accounting user
            if self.inputs.accounting_user:
                self.extra_lines.append(
                    f"accounting_group_user = {self.inputs.accounting_user}"
                )
        else:
            raise BilbyPipeError(
                "No accounting tag provided - this is required for condor submission"
            )

    @staticmethod
    def _checkpoint_submit_lines():
        return [
            f"checkpoint_exit_code = {CHECKPOINT_EXIT_CODE}",
        ]

    @staticmethod
    def _condor_file_transfer_lines(inputs, outputs):
        return [
            "should_transfer_files = YES",
            f"transfer_input_files = {','.join(inputs)}",
            f"transfer_output_files = {','.join(outputs)}",
            "when_to_transfer_output = ON_EXIT_OR_EVICT",
            "preserve_relative_paths = True",
            "stream_error = True",
            "stream_output = True",
        ]

    @staticmethod
    def _relative_topdir(path, reference):
        """Returns the top-level directory name of a path relative
        to a reference
        """
        try:
            return str(Path(path).resolve().relative_to(reference))
        except ValueError as exc:
            exc.args = (f"cannot format {path} relative to {reference}",)
            raise

    def _osg_submit_options(self, executable, has_ligo_frames=False):
        """Returns the extra submit lines and requirements to enable running
        a job on the Open Science Grid

        Returns
        -------
        lines : list
            the list of extra submit lines to include
        requirements : str
            the extra requirements line to include
        """
        # required for OSG submission
        lines = []
        requirements = []

        # if we need GWF data:
        if has_ligo_frames:
            requirements.append("(HAS_LIGO_FRAMES=?=True)")

        # if need a /cvmfs repo for the software:
        # NOTE: this should really be applied to _all_ workflows
        #       that need CVMFS, not just distributed ones, but
        #       not all local pools advertise the CVMFS repo flags
        if executable.startswith("/cvmfs"):
            repo = executable.split(os.path.sep, 3)[2]
            requirements.append(f"(HAS_CVMFS_{re.sub('[.-]', '_', repo)}=?=True)")

        return lines, requirements

    @property
    def slurm_walltime(self):
        """Default wall-time for base-name"""
        # One hour
        return "1:00:00"

    @property
    def environment(self):
        """Environment variables to set in jobs.

        See :code:`bilby_pipe.utils.get_environment_variables_dictionary`
        for more details on how the environment variables are determined.

        .. versionchanged:: 1.8.0
              The environment variables are now determined by the
              :code:`bilby_pipe.utils.get_environment_variables_dictionary`
              function.
        """
        return get_environment_variables_dictionary(self.inputs)

    @property
    def transfer_container(self):
        """
        Whether a singularity container should be transferred to the job
        """
        return (
            self.inputs.container is not None
            and (self.inputs.transfer_files or self.inputs.osg)
            and os.path.exists(self.inputs.container.replace("osdf://", "/osdf"))
            and not self.inputs.container.startswith(
                "/cvmfs/singularity.opensciencegrid.org"
            )
        )

    @staticmethod
    def extract_paths_from_dict(input):
        output = list()
        if isinstance(input, dict):
            for value in input.values():
                if isinstance(value, str):
                    output.append(value)
                elif isinstance(value, list):
                    output.extend(value)
        return output

    def job_needs_authentication(self, input_files):
        need_scitokens = False
        for ii, fname in enumerate(input_files):
            if fname.startswith("osdf://") and self._file_needs_authentication(fname):
                need_scitokens = True
                prefix = self.authenticated_file_prefix
                input_files[ii] = f"{prefix}{fname}"
        return input_files, need_scitokens

    @staticmethod
    def _file_needs_authentication(fname):
        """
        Check if a file needs authentication to be accessed, currently the only
        repositories that need authentication are :code:`ligo.osgstorage.org` and
        :code:`*.storage.igwn.org`.

        Parameters
        ----------
        fname: str
            The file name to check
        """
        proprietary_paths = ["igwn", "frames"]
        return any(path in fname for path in proprietary_paths)

    @property
    def scitoken_lines(self):
        """
        Additional lines needed for the submit file to enable access to
        proprietary files/services. Note that we do not support scoped tokens.
        This is determined by the method used to issue the scitokens. For more details
        see `here <https://computing.docs.ligo.org/guide/htcondor/credentials>`_.
        """
        issuer = self.scitoken_issuer
        if issuer is None:
            return []
        else:
            return [f"use_oauth_services = {issuer}"]

    @property
    def authenticated_file_prefix(self):
        """
        Return the prefix to add to files that need authentication. This is
        determined by the method used to issue the scitokens. For more details see
        `here <https://computing.docs.ligo.org/guide/htcondor/credentials>`.
        """
        if self.scitoken_issuer in [None, "scitokens"]:
            return ""
        else:
            return "igwn+"

    @property
    def scitoken_issuer(self):
        """
        Return the issuer to use for scitokens. This is determined by the :code:`--scitoken-issuer`
        argument or the version :code:`HTCondor` running on the current machine. For more details
        see `here <https://computing.docs.ligo.org/guide/htcondor/credentials>`_.
        """
        if self.inputs.scheduler.lower() != "condor":
            return None
        elif (
            self.inputs.scitoken_issuer == "local"
            or _is_htcondor_scitoken_local_issuer()
        ):
            return "scitokens"
        else:
            return "igwn"


def _is_htcondor_scitoken_local_issuer():
    """
    Test whether the machine being used is configured to use a local issuer
    or not. See `here <https://git.ligo.org/lscsoft/bilby_pipe/-/issues/304#note_1033251>`_
    for where this logic comes from.
    """
    try:
        from htcondor import param
    except ModuleNotFoundError:
        logger.warning(
            "HTCondor python bindings are not installed, assuming local "
            "issuer for scitokens if using HTCondor."
        )
        return True

    return param.get("LOCAL_CREDMON_ISSUER", None) is not None


def _log_output_error_submit_lines(logdir, prefix):
    """Returns the filepaths for condor log, output, and error options

    Parameters
    ----------
    logdir : str
        the target directory for the files
    prefix : str
        the prefix for the files

    Returns
    -------
    log, output, error : list of str
        the list of three file paths to be passed to pycondor.Job

    Examples
    --------
    >>> Dag._log_output_error_submit_lines("test", "job")
    ['log = test/job.log',
     'output = test/job.out',
     'error = test/job.err']
    """
    logpath = Path(logdir)
    filename = f"{prefix}.{{}}"
    return [
        f"{opt} = {str(logpath / filename.format(opt[:3]))}"
        for opt in ("log", "output", "error")
    ]
