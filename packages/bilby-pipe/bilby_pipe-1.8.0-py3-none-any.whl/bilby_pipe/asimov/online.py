"""
Bilby Pipeline Specifications
"""

import importlib.resources
import pathlib
import re
import subprocess

from asimov import config
from asimov.pipeline import PipelineException, PipelineLogger
from asimov.pipelines import Bilby
from gwpy.frequencyseries import FrequencySeries
from ligo.gracedb.exceptions import HTTPError
from ligo.gracedb.rest import GraceDb

from ..bilbyargparser import BilbyConfigFileParser
from ..gracedb import read_from_gracedb
from ..utils import convert_string_to_dict


class BilbyOnline(Bilby):
    """
    Bilby Pipeline---Online Replication Configuration.

    Parameters
    ----------
    production : :class:`asimov.Production`
        The production object.
    category : str, optional, default="C01_offline"
        The category of the job.

    Raises
    ------
    PipelineException
        Should a non BilbyOnline production be used to initiate the run
    """

    name = "bilbyonline"
    STATUS = {"wait", "stuck", "stopped", "running", "finished"}
    config_template = str(
        importlib.resources.files(__package__).joinpath("online_config.ini")
    )

    def __init__(self, production, category=None):
        super(Bilby, self).__init__(production, category)
        self.logger.info("Using the bilby pipeline in online replication configuration")
        self.event_id = None

        if not production.pipeline.lower() == "bilbyonline":
            raise PipelineException("Pipeline does not match")

    def build_dag(self, dryrun=False):
        """
        Construct a DAG file in order to submit a production to the condor
        scheduler using `bilby_pipe_gracedb`.

        Parameters
        ----------
        dryrun : bool, optional, default=False
            If true commands will not be run and will instead be printed to
            standard out.

        Raises
        ------
        PipelineException
            Raised if the construction of the DAG fails.
        """

        self.logger.info(f"Working in {pathlib.Path.cwd()}")

        if not self.production.rundir:
            self.production.rundir = pathlib.Path.expanduser("~").joinpath(
                self.production.event.name,
                self.production.name,
            )

        if not pathlib.Path(self.production.rundir).is_dir():
            pathlib.Path(self.production.rundir).mkdir(parents=True)

        self.event_id = self.resolve_grace_id()
        json_data = read_from_gracedb(
            self.event_id, config.get("gracedb", "url"), self.production.rundir
        )
        json_file = str(
            pathlib.Path(self.production.rundir).joinpath(f"{self.event_id}.json")
        )
        psd_file = self.psd_file(json_data)

        settings_fp, likelihood_mode = self.mass_settings(json_data)

        webdir = str(
            pathlib.Path(config.get("general", "webroot")).joinpath(
                f"{self.production.event.name}", f"{self.production.name}"
            )
        )

        if "channels" in self.production.meta:
            channel_dict = self.production.meta["channels"]
        else:
            channel_dict = "online"

        command = [
            str(
                pathlib.Path(config.get("pipelines", "environment")).joinpath(
                    "bin", "bilby_pipe_gracedb"
                )
            ),
            "--settings",
            settings_fp,
            "--cbc-likelihood-mode",
            likelihood_mode,
            "--webdir",
            webdir,
            "--outdir",
            self.production.rundir,
            "--json",
            json_file,
            "--psd-file",
            psd_file,
            "--channel-dict",
            channel_dict,
        ]

        if dryrun:
            print(" ".join(command))
        else:
            self.logger.info(" ".join(command))
            pipe = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
            )
            out, err = pipe.communicate()
            self.logger.info(out)

            if err or "DAG generation complete" not in str(out):
                self.production.status = "stuck"
                self.logger.error(err)
                raise PipelineException(
                    f"DAG file could not be created.\n{command}\n{out}\n{err}",
                    production=self.production.name,
                )
            return PipelineLogger(message=out, production=self.production.name)
        return None

    def resolve_grace_id(self) -> str:
        """
        Establish the correct GID for the selected event

        Returns
        --------
        grace_id : str
            GraceDB Event ID (Gname)

        Raises
        ------
        ValueError
            Raised when GraceID cannot be identified from metadata or cannot be
            found on GraceDB
        """

        grace_id = None
        if "ligo" in self.production.meta:
            ligo_dict = self.production.meta["ligo"]
            if "gname" in ligo_dict:
                grace_id = ligo_dict["gname"]
            elif "preferred event" in ligo_dict:
                grace_id = ligo_dict["preferred event"]
            elif "sname" in ligo_dict:
                grace_id = self.get_gname_from_sname(grace_id)

        if grace_id is None:
            if self.production.event.name.startswith("G"):
                grace_id = self.production.event.name
            elif self.production.event.name.startswith("S"):
                grace_id = self.get_gname_from_sname(self.production.event.name)
            else:
                raise ValueError(
                    "Unable to resolve GraceDB ID from provided information"
                )

        return grace_id

    def get_gname_from_sname(self, sname) -> str:
        """
        Gets the preferred event Gname from the given Sname. Will retrieve the
        preferred event.

        Parameters
        ----------
        sname : str
            GraceDB ID for the Superevent (Sname).

        Returns
        -------
        gname : str
            GraceDB ID for the preferred Event (Gname).

        Raises
        ------
        ValueError
            If Sname does not recover an associated Gname
        """

        gracedb_server = config.get("gracedb", "url")
        gracedb = GraceDb(service_url=gracedb_server)

        try:
            superevent_data = gracedb.superevent(sname).json()
            gname = superevent_data["preferred_event_data"]["graceid"]
        except HTTPError as exc:
            raise HTTPError(f"Unable to retrieve {sname} from gracedb") from exc

        return gname

    def mass_settings(self, json_data) -> tuple[str, str]:
        """
        Determines settings for run based on best fitting template chirp mass.

        Parameters
        ----------
        json_data : dict
            GraceDB meta data.

        Returns
        -------
        settings_fp : str
            Path to settings for binary type.
        likelihood_mode : str
            Contains the ROQ type to use.

        Raises
        ------
        ValueError
            If settings cannot be found or the chirp mass is incompatible with
            setting types
        """

        mchirp = float(json_data["extra_attributes"]["CoincInspiral"]["mchirp"])

        mass_settings = None
        if "mass settings" in self.production.meta:
            mass_settings = self.production.meta["mass settings"]
        elif "pipelines" in self.production.meta:
            pipelines = self.production.meta["pipelines"]
            if "bilbyonline" in self.production.meta["pipelines"]:
                if "mass settings" in pipelines["bilbyonline"]:
                    mass_settings = pipelines["bilbyonline"]["mass settings"]
        if mass_settings is None:
            raise ValueError("No mass settings available")

        defaults = mass_settings.pop("defaults", None)
        if defaults:
            settings_fp = defaults["settings file"]
            likelihood_mode = defaults["likelihood mode"]

        for key, settings in mass_settings.items():
            lower = float(settings["low mass bound"])
            higher = float(settings["high mass bound"])
            if lower <= mchirp < higher:
                settings_fp = settings["settings file"]
                likelihood_mode = settings["likelihood mode"]
                break
        else:
            if not defaults:
                raise ValueError(
                    f"{mchirp} did not have associated settings nor were defaults"
                    "available"
                )

        return settings_fp, likelihood_mode

    def psd_file(self, json_data) -> str:
        """
        Establishes which file contains the PSD information

        Parameters
        ----------
        json_data : dict
            Contains the metadata retrieved from GraceDB

        Returns
        -------
        psd_file : str
            Path to XML file containing PSD information

        Raises
        ------
        ValueError
            If unable to retrieve a PSD XML from GraceDB
        """

        psd_file = None
        if "coinc_file" in json_data:
            coinc = json_data["coinc_file"]
            ifos = json_data["instruments"].split(",")

            psds_present = 0
            for ifo in ifos:
                try:
                    _ = FrequencySeries.read(coinc, instrument=ifo)
                    psds_present += 1
                    break
                except ValueError:
                    continue

            if bool(psds_present):
                psd_file = coinc

        if psd_file is None:
            gracedb_server = config.get("gracedb", "url")
            gracedb = GraceDb(service_url=gracedb_server)

            try:
                data = gracedb.files(self.event_id, "psd.xml.gz")
            except HTTPError as exc:
                raise ValueError(
                    f"Unable to retrieve PSDs for {self.event_id}"
                ) from exc

            psd_file = pathlib.Path(self.production.rundir).joinpath(
                f"{self.production.event.name}_psd.xml.gz"
            )
            with open(psd_file, "wb") as fb:
                fb.write(data.read())

        return str(psd_file)

    def submit_dag(self, dryrun=False):
        """
        Submit a DAG file to the condor cluster

        Parameters
        ----------
        dryrun : bool, optional, default=False
            If true, the DAG will not be submitted but all commands will be
            printed to standard out.

        Returns
        -------
        int
            The cluster ID assigned to the running DAG file.
        PipelineLogger
            The pipeline logger message.

        Raises
        ------
        PipelineException
            Raised if the pipeline fails to submit the job.
        """

        self.logger.info(f"Working in {pathlib.Path.cwd()}")
        self.before_submit()

        try:
            dag_filename = f"dag_{self.event_id}.submit"
            command = [
                "condor_submit_dag",
                "-batch-name",
                f"bilby_online/{self.production.event.name}/{self.production.name}",
                str(
                    pathlib.Path(self.production.rundir).joinpath(
                        "submit", dag_filename
                    )
                ),
            ]

            if dryrun:
                print(" ".join(command))
            else:
                self.logger.info(" ".join(command))
                dagman = subprocess.Popen(
                    command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                )
                out, err = dagman.communicate()

                if "submitted to cluster" in str(out):
                    cluster = re.search(
                        r"submitted to cluster ([\d]+)", str(out)
                    ).groups()[0]
                    self.logger.info(
                        "Submitted successfully." f"Running with job ID {int(cluster)}"
                    )
                    self.production.status = "running"
                    self.production.job_id = int(cluster)
                    return cluster, PipelineLogger(out)
                self.logger.error("Could not submit the job to the cluster")
                self.logger.info(out)
                self.logger.error(err)

                raise PipelineException(
                    "The DAG file could not be submitted.",
                )

        except FileNotFoundError as error:
            self.logger.exception(error)
            raise PipelineException(
                "It looks like condor isn't installed on this system\n"
                f"I wanted to run {' '.join(command)}"
            ) from error

    def after_completion(self):
        if "postprocessing" not in self.production.meta:
            self.production.status = "uploaded"
            self.production.event.update_data()
            return

        ini_file = pathlib.Path(self.production.rundir).joinpath(
            f"{self.production.event.name}_config_complete.ini"
        )

        config_parser = BilbyConfigFileParser()
        with open(ini_file, "r", encoding="utf-8") as f:
            config_content, _, _, _ = config_parser.parse(f)

        if "waveform" not in self.production.meta:
            self.production.meta["waveform"] = {}

        self.production.meta["waveform"]["approximant"] = config_content[
            "waveform-approximant"
        ]
        self.production.meta["waveform"]["reference frequency"] = float(
            config_content["reference-frequency"]
        )

        if "quality" not in self.production.meta:
            self.production.meta["quality"] = {}

        detectors = config_content["detectors"]

        self.production.meta["quality"]["minimum frequency"] = {
            key.strip("'"): float(config_content["minimum-frequency"])
            for key in detectors
        }
        self.production.meta["quality"]["maximum frequency"] = {
            key.strip("'"): float(config_content["maximum-frequency"])
            for key in detectors
        }

        self.production.psds = convert_string_to_dict(config_content["psd-dict"])

        self.production.event.update_data()

        super().after_completion()
