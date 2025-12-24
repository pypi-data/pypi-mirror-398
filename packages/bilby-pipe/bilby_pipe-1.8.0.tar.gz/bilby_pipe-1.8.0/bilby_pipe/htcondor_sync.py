"""
bilby_pipe_htcondor_sync can be used to sync jobs running under HTCondor where
transfer-files=True (i.e. they do not use a virtual file system). It will use
rsync to copy the results from remote worker nodes or spool back to the execute
node.  The executable is assumed to be run from the submit directory (i.e.,
where the .ini file is) and on the submit machine (i.e. where the job was
submitted from).
"""
import argparse
import glob
import os
import subprocess

from bilby_pipe.utils import logger


def get_cluster_id_list(outdir):
    """Get a list of cluster IDs for every running analysis job"""
    logfile_matches = glob.glob(f"{outdir}/log_data_analysis/*.log")
    ids = []
    for logfile in logfile_matches:
        ids.append(get_cluster_id(logfile))
    return ids


def get_cluster_id(logfile):
    """Read a log files to determine the latest cluster ID

    Extract the HTCondor cluster ID from the .log file. For example, if the log
    file reads

    ```
    001 (100503183.000.000) 2022-03-07 15:22:49 Job executing on host: <10.14.4.164...>
    ```
    Then this function return the cluster ID 100503183

    Parameters
    ----------
    logfile: str
        A path to a HTCondor log file

    Returns
    -------
    cluster_id: str
        The cluster ID. If not ID is found, None is returned and a log message
        is printed.
    """

    with open(logfile, "r") as f:
        ids = []
        for line in f:
            if "Job executing on" in line:
                elements = line.split()
                ids.append(int(elements[1].lstrip("(").rstrip(")").split(".")[0]))

    if len(ids) > 0:
        return ids[-1]
    else:
        logger.info("No cluster ID found in log file")


def rsync_via_ssh(cluster_id, outdir, verbose=False, timeout=30):
    """Attempt to rsync the local (submit) directory to current running worker nodes

    This method applies when the job is actively executing on a remote worker
    node and condor_ssh_to_job is possible. The method works by using
    condor_ssh_to_job and rsync as described in the HTCondor documentation:
    https://htcondor.readthedocs.io/en/latest/man-pages/condor_ssh_to_job.html.

    Parameters
    ----------
    cluster_id: int
        The HTCondor clusterId
    outdir: str
        The top-level outdir of the bilby_pipe job
    verbose: bool
        If true, print explicit error messages
    timeout: int
        The timeout interval

    Returns
    -------
    success: bool
        True if the method was successful.

    """
    sync_path = f"{outdir}/result/"
    target = f"{cluster_id}:{sync_path}"
    cmd = [
        "timeout",
        str(timeout),
        "rsync",
        "-v",
        "-r",
        "-e",
        '"condor_ssh_to_job"',
        target,
        sync_path,
    ]
    logger.info("Running " + " ".join(cmd))
    out = subprocess.run(cmd, capture_output=True)
    if verbose:
        logger.info(f"stdout: {out.stdout.decode('utf-8')}")
        logger.info(f"stderr: {out.stderr.decode('utf-8')}")
    if out.returncode == 0:
        return True
    else:
        return False


def rsync_via_spool(cluster_id, outdir, verbose=False):
    """Attempt to rsync the local (submit) directory to the spool

    This method applies when the job is not actively executing on a remote
    worker, but is idle.  In this instance, any files produced by the job will
    be stored in the spool (a local directory on the submit machine). This
    methods identifies the spool location, based on the cluster_id, and attempts
    to rsync the data.

    Parameters
    ----------
    cluster_id: int
        The HTCondor clusterId
    outdir: str
        The top-level outdir of the bilby_pipe job

    Returns
    -------
    success: bool
        True if the method was successful.

    """

    outdir = outdir.rstrip("/")
    subdir = cluster_id % 10000
    procid = 0
    spool_dir = (
        subprocess.check_output("condor_config_val SPOOL", shell=True)
        .decode("utf-8")
        .rstrip("\n")
    )
    # Definition of the spool location credit to James Clark
    src = f"{spool_dir}/{subdir}/{procid}/cluster{cluster_id}.proc{procid}.subproc0/{outdir}/"
    if os.path.isdir(src):
        cmd = ["rsync", "-r", src, outdir]
        logger.info("Running " + " ".join(cmd))
        out = subprocess.run(cmd, capture_output=True)
        if verbose:
            logger.info(f"stdout: {out.stdout.decode('utf-8')}")
            logger.info(f"stderr: {out.stderr.decode('utf-8')}")
        return True
    else:
        if verbose:
            logger.info(f"Spool directory {src} does not exist")
        return False


methods = [rsync_via_ssh, rsync_via_spool]


def create_parser():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("outdir", help="The bilby_pipe directory to sync")
    parser.add_argument(
        "--verbose", action="store_true", help="Print explicit error messages"
    )
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    args.outdir = args.outdir.rstrip("/")
    cluster_id_list = get_cluster_id_list(args.outdir)
    for cluster_id in cluster_id_list:
        if cluster_id is not None:
            logger.info(f"Trying to sync job {cluster_id}")
            success = False
            for method in methods:
                logger.info(f"Trying to sync using method {method.__name__}")
                success = method(cluster_id, args.outdir, args.verbose)
                if success:
                    logger.info(f"Successfully synced using method {method.__name__}")
                    break
                else:
                    logger.info(f"Failed to sync using method {method.__name__}")
            if success is False:
                logger.warning(f"All sync methods failed for job {cluster_id}")


if __name__ == "__main__":
    main()
