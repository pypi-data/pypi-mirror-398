#!/usr/bin/env python

import os
import sys

from setuptools import setup

# check that python version is 3.9 or above
python_version = sys.version_info
print("Running Python version %s.%s.%s" % python_version[:3])
minimum_py_major = 3
minimum_py_minor = 9
if python_version < (minimum_py_major, minimum_py_minor):
    sys.exit(
        f"Python < {minimum_py_major}.{minimum_py_minor} "
        "is not supported, aborting setup"
    )
print(f"Confirmed Python version {minimum_py_major}.minimum_py_minor.0 or above")


def get_long_description():
    """Finds the README and reads in the description"""
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, "README.rst")) as f:
        long_description = f.read()
    return long_description


long_description = get_long_description()

MAIN = "bilby_pipe"
JOB_CREATION = f"{MAIN}.job_creation"
NODES = f"{JOB_CREATION}.nodes"
ASIMOV = f"{MAIN}.asimov"

setup(
    name="bilby_pipe",
    description="Automating the running of bilby for gravitational wave signals",
    long_description=long_description,
    url="https://git.ligo.org/lscsoft/bilby_pipe",
    project_urls={
        "Documentation": "https://lscsoft.docs.ligo.org/bilby_pipe/master/index.html",
    },
    author="Gregory Ashton, Isobel Romero-Shaw, Colm Talbot, Charlie Hoy, Shanika Galaudage",
    author_email="gregory.ashton@ligo.org",
    license="MIT",
    package_data={"bilby_pipe": ["data_files/*", "asimov/*.ini"]},
    packages=[MAIN, JOB_CREATION, NODES, ASIMOV],
    install_requires=[
        "future",
        "pycondor>=0.6",
        "configargparse",
        "ligo-gracedb",
        "bilby[gw]>=2.4.0",
        "scipy>=1.2.0",
        "gwpy>=3.0.4",
        "gwosc",
        "matplotlib",
        "numpy",
        "tqdm",
        "corner",
        "dynesty>=1.0.0",
        "seaborn",
        "jinja2",
        "astropy",
        "plotly",
        "python-ligo-lw>=1.8.0",
    ],
    extras_require={"asimov": ["asimov<0.6", "pesummary>=1.3.1"]},
    python_requires=f">={minimum_py_major}.{minimum_py_minor}",
    entry_points={
        "console_scripts": [
            "bilby_pipe=bilby_pipe.main:main",
            "bilby_pipe_generation=bilby_pipe.data_generation:main",
            "bilby_pipe_analysis=bilby_pipe.data_analysis:main",
            "bilby_pipe_create_injection_file=bilby_pipe.create_injections:main",
            "bilby_pipe_xml_converter=bilby_pipe.xml_converter:main",
            "bilby_pipe_pp_test=bilby_pipe.pp_test:main",
            "bilby_pipe_review=bilby_pipe.review:main",
            "bilby_pipe_plot=bilby_pipe.plot:main",
            "bilby_pipe_plot_calibration=bilby_pipe.plot:plot_calibration",
            "bilby_pipe_plot_corner=bilby_pipe.plot:plot_corner",
            "bilby_pipe_plot_marginal=bilby_pipe.plot:plot_marginal",
            "bilby_pipe_plot_skymap=bilby_pipe.plot:plot_skymap",
            "bilby_pipe_plot_waveform=bilby_pipe.plot:plot_waveform",
            "bilby_pipe_gracedb=bilby_pipe.gracedb:main",
            "bilby_pipe_write_default_ini=bilby_pipe.parser:main",
            "bilby_pipe_process_mcmc=bilby_pipe.process_bilby_mcmc:main",
            "bilby_pipe_htcondor_sync=bilby_pipe.htcondor_sync:main",
            "bilby_pipe_to_ligo_skymap_samples=bilby_pipe.ligo_skymap:main",
            "bilby_pipe_reweight_result=bilby_pipe.data_analysis:reweight",
        ],
        "asimov.pipelines": [
            "bilby_native=bilby_pipe.asimov.asimov:Bilby",
            "bilbyonline=bilby_pipe.asimov.online:BilbyOnline",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
    ],
)
