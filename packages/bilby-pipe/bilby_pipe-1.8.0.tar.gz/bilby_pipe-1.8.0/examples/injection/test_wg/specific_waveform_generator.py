import logging

from bilby.gw.waveform_generator import GWSignalWaveformGenerator

logger = logging.getLogger(__name__)
formatter = logging.Formatter(
    "BILBY_PIPE_WG_HANDLING TEST **************** %(name)s - %(levelname)s - %(asctime)s - %(message)s"
)
ch = logging.StreamHandler()
ch.setFormatter(formatter)
if logger.hasHandlers():
    logger.removeHandler(logger.handlers[0])
logger.propagate = False
logger.setLevel(logging.DEBUG)
logger.addHandler(ch)


class SpecificWaveformGenerator(GWSignalWaveformGenerator):
    def __init__(self, configuration, log_level: str = "DEBUG", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log_level = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "ERROR": logging.ERROR,
            "WARNING": logging.WARNING,
        }.get(log_level.upper(), logging.DEBUG)
        self.configuration = configuration

    def time_domain_strain(self, parameters):
        logger.log(self.log_level, "calling time_domain_strain %s", self.configuration)

        return super().time_domain_strain(parameters=parameters)

    def frequency_domain_strain(self, parameters):
        logger.log(
            self.log_level, "calling frequency_domain_strain %s", self.configuration
        )
        return super().frequency_domain_strain(parameters=parameters)
