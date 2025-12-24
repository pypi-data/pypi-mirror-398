# All notable changes will be documented in this file

## v1.8.0

See full MR log [here](https://git.ligo.org/lscsoft/bilby_pipe/-/merge_requests?scope=all&state=all&milestone_title=1.8.0)

This version includes a few small new features and a significant bugfix to enable support for Python 3.12.

### Added

- Set environment variables with SLURM in the same was as for HTCondor (!648)

### Fixed

- Fix to parsing command-line arguments (!651)
- Make parser compatible with Python 3.12 (!660)
- Only call `validate_priors` if the prior class has that method.

### Changed

- Update to how asimov parses distance priors (!647)
- Allow more arguments to be passed to `fetch_open_data` (!657)
- Demote various log messages to debug (!659)
- PESummary is no longer a hard dependency (!662)

## v1.7.0

See full MR log [here](https://git.ligo.org/lscsoft/bilby_pipe/-/merge_requests?scope=all&state=all&milestone_title=1.7.0)

This is a feature release that improves support for `gwsignal` waveform generators, and fixes an issue that prevented the use of non-CBC priors.

### Added

- Add support for custom waveform generators (!640)

### Fixed

- Fix bug preventing the use of priors that do not inherit from `CBCPriorDict` (!653)
- Fix parsing for multi-lined dictionaries (!532)

## v1.6.0

See full MR log [here](https://git.ligo.org/lscsoft/bilby_pipe/-/merge_requests?scope=all&state=all&milestone_title=1.6.0)

This is a feature release that includes specifying cosmology and calibration, and improved asimov integration.

### Added

- Make cosmology specifyable via the configuration file (!623)
- Updates to the asimov config (!635, !638, !639)

### Changed

- Make calibration type a dictionary (!529)
- Make the data find URL behaviour more sensible. (!637)

### Fixed

- Fixes when using containers (!632, !641)
- Avoid warnings about extra waveform kwargs (!630)

## v1.5.0

See full MR log [here](https://git.ligo.org/lscsoft/bilby_pipe/-/merge_requests?scope=all&state=all&milestone_title=1.5.0)

This is a feature release that includes a new features, improvements to existing functionality and minor bug fixes.

### Added

- Add calibration type argument
- Add `asimov` plugin (previously implemented in `asimov` directly)
- Add support for online-style runs using `bilby_pipe_gracedb` via `asimov`
- Add SciToken authentication for non-generation jobs
- Add support for Singularity containers

### Changed

- Use `get_expected_outputs` for getting sampler outputs
- Improve handing of `slurm` arguments

### Fixed

- Remove preference for `lalframe` when loading frames

## v1.4.0 2024-06-28
See full MR log [here](https://git.ligo.org/lscsoft/bilby_pipe/-/merge_requests?scope=all&state=merged&milestone_title=1.4.0)

This release addresses new authentication methods for accessing proprietary LVK data (!607).
See the [LVK computing docs](https://computing.docs.ligo.org/guide/htcondor/credentials/) for details.

### Added
- Specify whether to run data generation jobs via the IGWN pool or the local cluster

### Changes
- Use the `GWDATAFIND_SERVER` environment variable when set.
- Support the local and IGWN scitoken issuer models with HTCondor.

### Deprecated
- The `local-generation` argument is deprecated in favour of `generation-pool=local`.

## v1.3.2 2024-05-31
See full MR log [here](https://git.ligo.org/lscsoft/bilby_pipe/-/merge_requests?scope=all&state=merged&milestone_title=1.3.2)

This is a bugfix release primarily to address an issue with resolving calibration envelopes for online PE.

### Changes
- Make sure the sampling seed is set to a different value for each parallel analysis (this doesn't directly impact default running conditions) (!587)
- Address a pandas deprecation warning (!601)
- Fix the logic for finding calibration files (!602) 

## v1.3.1 2024-03-15
See full MR log [here](https://git.ligo.org/lscsoft/bilby_pipe/-/merge_requests?scope=all&state=merged&milestone_title=1.3.1)

This is a release with minor updates to the online running configuration for the ongoing observing run.

### Changes
- Merge the 4s and 8s chirp mass bins to reduce prior railing (!590).
- Automatically set the distance prior bounds using Bayestar skymaps when available (!588).
- Update the logic for choosing calibration envelopes (!568).
- Make sure the start and end times for online frames consistent across methods (!595).

## v1.3.0 2023-11-13
See full MR log [here](https://git.ligo.org/lscsoft/bilby_pipe/-/merge_requests?scope=all&state=merged&milestone_title=1.3.0)

This release makes some significant changes to the internals of how data generation happens.
More details can be found in the [online docs](https://docs.ligo.org/lscsoft/bilby_pipe/master).
In general, when analyzing publicly available data, specifying, e.g., `channel-dict={H1: GWOSC}` will find the relevant data.

### Added
- Pass `HTGETTOKENOPTS` in dag file to enable robot/reduced scope credentials.
- Allow `bilby_pipe_gracedb` to query open data from `GWOSC`.

### Changes
- Don't require scitokens when they aren't needed by the job.
- `bilby_pipe_gracedb` will now grab enough data to create a PSD when not available from `GraceDb`.
- Fix passing environment variables through the config file.

### Removed
- No longer explicitly pass x509 credentials to gracedb. Users should make sure relevant scitoken authentication is set up.
- Remove function to find th default frame type and use gwpy version instead.

## v1.2.1 2023-09-10
See full MR log [here](https://git.ligo.org/lscsoft/bilby_pipe/-/merge_requests?scope=all&state=merged&milestone_title=1.2.1)

This MR contains changes required to support HTCondor >= 10.7.1 and the scitokens authentication system.
Most significantly, environment variables can now be generically and explicitly defined.

### Added
- Switch to scitokens authentication and explicitly use gwdatafind rather than relying on gwpy (!569)
- Change how environment variables are specified, defaults should be preserved, but users should be careful (!570)

## v1.2.0 2023-28-07
See full MR log [here](https://git.ligo.org/lscsoft/bilby_pipe/-/merge_requests?scope=all&state=merged&milestone_title=1.2.0)

This release drops support for Python 3.8.

### Changed
- Don't create unnecessary ROQ weight file to reduce memory/storage usage (!552)
- Fix a typo in the online MDC frame finding (!563)
- Allow custom waveform models to be used with accelerated likelihoods (!564)
- Use the new random number generation method in `Bilby` 2.1.2 (!565)

### Removed
- Drop support for Python 3.8 (!566)

## v1.1.2 2023-25-05
See full MR log [here](https://git.ligo.org/lscsoft/bilby_pipe/-/merge_requests?scope=all&state=merged&milestone_title=1.1.2)

### Changed
- Fix a typo in the online MDC frame finding (!557)
- Update distance prior minima to avoid railing seen in online PE (!560)
- Unpin the XHM version used for online PE (!561)
- Raise the minimum mass ratio bound for the Pv2 prior for online PE (!562)

## v1.1.1 2023-25-05
See full MR log [here](https://git.ligo.org/lscsoft/bilby_pipe/-/merge_requests?scope=all&state=merged&milestone_title=1.1.1)

### Added
- Read low-latency frame files when possible/requested for `bilby_pipe_gracedb` (!554)

### Changed
- Revert the previous switch to use `forkserver` start method (!555)
- Set `KMP_AFFINITY='reset'` environment variable to fix parallelisation issue (!553)

## v1.1.0 2023-28-04
See full MR log [here](https://git.ligo.org/lscsoft/bilby_pipe/-/merge_requests?scope=all&state=merged&milestone_title=1.1.0)

### Added
- Adding a reweighting executable (!536)
- Add command line flags to the bash script (!538)
- Default sampler settings for O4 (!539)

### Changed
- Bug fix to multiprocessing start method (!551)
- Improvements to gracedb exe (!550, !547, !548, !546)
- Set default sampler settings for O4 (!539)
- Bug fixes for nested sampling reweighting (!540)
- Fix edge case of naming (!537)
- Improve the bilby-mcmc processing tool (!541)
- Add generation node retries (!542)

## v1.0.10 2023-13-04
See full MR log [here](https://git.ligo.org/lscsoft/bilby_pipe/-/merge_requests?scope=all&state=merged&milestone_title=1.0.10)

### Changes
- Hotfix a breaking issue with HDF5 file locking (!534)

## v1.0.9 2023-12-04
See full MR log [here](https://git.ligo.org/lscsoft/bilby_pipe/-/merge_requests?scope=all&state=merged&milestone_title=1.0.9)

### Additions
- Add option to disable HDF5 locking, on by default (!529)
- Allow inline reweighting config (!523)

### Changes
- Enable increment of outdir naming past `_Z` (!531)
- Updates to online PE gracedb (!530, !526, !521)
- Introduce psd_cut in gracedb (!526)
- Bugfixes to reweighting outdir (!528)
- Fixes to time calibration (!522)

## v1.0.8 2023-03-02

See full MR log [here](https://git.ligo.org/lscsoft/bilby_pipe/-/merge_requests?scope=all&state=merged&milestone_title=1.0.8)

### Changes
- Fixed calibration bugs with latest bilby release (!519, !508)
- Improvements to online mode (!518, !499))
- Improve the bilby_pipe processing methods (!514)
- Improvemenst to enable nessai features (!512, !509)
- Use relative paths for file transfer (!501)
- No restart time on local jobs (!492)

### Added
- Set automatic retries for analysis jobs (!520)
- Relative binning likelihood (!506)
- Warnings for npool and ncpu mismatch (!505)
- Warnings for calibration boundary (!503)
- Quality of life improvements (reduce verbosity of outputs) (!504)
- Add stub files for transfer (!498)
- Support for calibration marginalized likelihood (!497)
- Implement multiband likelihood (!492)

## v1.0.7 2022-11-07

See full MR log [here](https://git.ligo.org/lscsoft/bilby_pipe/-/merge_requests?scope=all&state=merged&milestone_title=1.0.7)

### Changes
- Update keys stored in result for ligo skymap (!482)
- Improve npool behavior (!477)
- Improve htcondor sync method (!475, !464, !470)
- Updates for online PE (!478, !471, !467)
- Default to using the LALCBCWaveformGenerator (!462)
- Improvements to versioning and CI infrastructure (see logs)

### Added
- Enable specifying job queue (!485)
- ROQ time marginalization (!461)
- Python 3.10 testing

### Removed
- online-pe flag removed in favour of job queueu (!485)


## v1.0.6: 2022-04-25

See MR log [here](https://git.ligo.org/lscsoft/bilby_pipe/-/merge_requests?scope=all&state=merged&milestone_title=1.0.6)

### Changes
- Updates for O3 replay (!448)
- Improve plotting (!449, !438)
- Minor bug fixes

### Added
- Command line tool to online-process bilby_mcmc runs (!402)
- Option to specify job sides on IGWN network (!437)
- Option to specify alternative parser (!442)

## v1.0.5: 2022-01-31
### Changes
- Enable PP tests to handle real-data injections (!429)
- Update dependencies (!428, !431)
- Enable setting a range of injection values (!425)
- Use print rather than tqdm by default (!423)
- Bug fixed (https://git.ligo.org/lscsoft/bilby_pipe/-/merge_requests?scope=all&state=all&milestone_title=1.0.5)

### Added
- Add noconversion option (!420)

## v1.0.4: 2021-05-14
### Changes
- Allow different result file formats (!395)
- Address minor bugs (!394, !399)
- Add dtype kwarg to TimeSeries.get call (!401)
- Fixes to dependencies (!398, !404)

### Added
- Add parallelisation of bilby_mcmc (!397)
- Added zero likelihood option (!396)

## v1.0.3: 2021-02-17
### Changes
- Clean up the submit scripts, fixing bugs in the OSG (!380, !389, !387, !386)
- Force the use of outdirs to prevent complications (!382)
- Regenerate look-up tables based on new distance priors (!381)

### Added
- Allow data from tape (!385)
- Enable extra detectors (!383)
- Behaviour to prevent overwriting of directories (!375)
- Checking of duplicate entries (!372)
- Option to pass through the conversion functions (!373)

## v1.0.1: 2020-26-08
### Changed
- Updated bilby dependency to v1.0.2
- Enable support for the OSG and documentation (!364)
- PESummary now pointed to the "complete" config files (!366)
- Fixed bug related to nested outdir (!365)
- Add support for numerical relativity injection file (!361)
- Add support for generic waveform-arguments (!361)
- Improve behaviour for specifying single mode (!362)
- Improve slurm documentation and version information (!363, !362)
- Improve suppory for multi-line prior-dicts (!369)

## v1.0.1: 2020-26-08
### Added
- Priority setting for condor
- Email notofications

### Changed
- Python 3.6+ requirement
- Review files to use reference frequency of 100Hz
- Improved parent-child relation to avoid recreating cached files
- Job creation modularised
- Overhaul and improvements to the slurm backend


## v1.0.00: 2020-27-07
### Added
- Trigger-time now able to use event names (!333)
- Add option to pass in ROQ weight file directly (!340)
- Prior check and print-out and run time and sampler check (!337, !338)

### Changes
- Modularation of the main module (!336)
- Documentation bug fixes and versioning (!341 !343)

## v0.3.12: 2020-15-04
### Added
- Add support for the sky-frame in bilby 0.6.8
- Add support for post processing individual results

### Changes
- Fixed a bug in the periodic restart time

## v0.3.11: 2020-15-04

### Changes
-   Put periodic restart into job submission parser (!306)
-   Injection number fix (!281)
-   Changes to data read-in logic (!305)
-   Update lookup tables following changes in bilby (!307)
-   Remove hardcoded checkpoint from review runs (!309)
-   Fix issues with checkpointing (!308)
-   Remove future imports (!310)
-   Fix bug where request-cpu value was not passed through (!311)
-   Allow lal resampling (!312)

## v0.3.10 : 2020-30-03

### Added
-   Waveform arguments (!296)
-   prior-dict option (!288)
-   Variable waveform generator class (!283)
-   Calibration in injections (!282)
-   Likelihood kwargs (!285)

### Changes
-   Improved --help message (!298)
-   Update to date calibration files for online runs
-   Improvements to the review tests script (!286)
-   Documentation on injections (!275)

## v0.3.9 : 2020-30-03

### Changes
-   Update documentation for using CVMFS
-   Allow other samplers in the review script
-   Fix the timeslide check
-   Tweak the generation: add read methods for gwp, txt and hdf5 and improve PSD data handling
-   Use the generated complete config file at run time
-   Add an XML conversion method

## v0.3.8 : 2020-01-03
-   Minor release updating to bilby v0.6.3

## v0.3.7 : 2019-12-20
-   Minor release updating to bilby v0.6.2

### Changes
-   Fixes ROQ scaling issues
-   Modifies Default and FastTest sampler settings
-   Edits template priors to allow component mass scaling

## v0.3.6 : 2019-12-10
-   Minor release fixing bugs with the ROQ

## v0.3.5 : 2019-12-06
-   Minor release following small fixes

### Added
-   PESummary CI test
-   Mass 1 constraint to prior files

### Changes
-   Fix --convert-to-flat-in-component-mass flag
-   Pass the ROQ scale factor to the likelihood
-   Fix ROQ waveform plotting
-   Set max skymaps points to 5000

## v0.3.4 : 2019-12-02
-   Minor version release updating to bilby v0.6.1
-   Remove reflective boundaries from defaults priors
-   Resolve issue with ROQ times steps and the PSD roll off (!230)
-   Update the minimum pesummary version

## v0.3.3 : 2019-11-26
-   Minor release following small fixes

### Changes
-   All gracedb jobs default to "vanilla" universe
-   Fixes dict conversion error of reading negative numbers
-   Minor fix to gwdata paths

## v0.3.2 : 2019-11-13

### Added
-   GWpy data quality check
-   GWpy spectrogram plotting method
-   Method to apply timeshifts with example
-   Option to generate injection with different waveform to PE

### Changes
-   Fix to prior limits for actual spin maximum
-   Updated calls to pesummary
-   Minor improvements to gracedb script

## v0.3.1 : 2019-10-29

### Added
-   Flag for use of online PE dedicated nodes

### Changes
-   Fixed trigger time to zero for simulations
-   Writes review.ini to top level

## v0.3.0 : 2019-10-25
Major release with overhaul of main interface

### Added
-   Support for using n-parallel with other tools
-   Support for running on gps_time with injections
-   Default to file_transfer=True
-   Testing running ini files in biby-test-mode
-   Default and fast-PE sampler-kwarg settings

### Changes
-   Expanded default prior limits
-   PSD defaults updated to max at 1024 (user override available)
-   Data dump process changes

## v0.2.7 : 2019-10-02
Minor release following small fixes

## v0.2.6 : 2019-09-23
### Added
-   Testing of min/max frequencies
-   A warning message for cases when "tidal" waveforms are used without the appropriate frequency domain source model

### Changes
-   Improvements to the gracedb parsing in preparation for online running
-   Improvements to the logging output

## v0.2.5 : 2019-08-22
### Changes
-   Fixed bug in time-jitter option (default was None, now True)

## v0.2.4 : 2019-08-22
### Added
-   Support for use on a slurm filesystem
-   Limited support for a user-defined likelihood

### Changes
-   Improvements to the gracedb script (changes to the filenames and channels)

## v0.2.3 : 2019-08-15

### Changed
-   Removed testing against python3.5: it was found that the
    python-ldas-tools-framecpp package was no longer compatible with python3.5.
    As such, this breaks the C.I. testing environment. While basic running is
    still expected to work with python3.5, it is strongly recommended people
    update to a modern python installation.
-   Update to the review defaults and online running settings
-   Fixed bug when sampler_kwargs is None
-   Allow users to specific external source functions
-   Fix standard priors to have hign-spin (0.8) upper boundaries
-   Add time jittering option
-   Add shell script

## v0.2.2 : 2019-06-19
Release coinciding with bilby 0.5.2. Minor changes fixing bugs in 0.5.2 only

### Changed
-   Fix issues in ROQ rescaling
-   Remove print os environ statement
-   Add summary pages to fiducial runs
-   Fix minor bugs in the pp tests
-   Increase default periodic restart time to 12hrs 
-   Tweak plotting script
-   Remove double escape from priors
-   Review ini files not written to outdir
-   Compatibility issues with bilby 0.5.2


## v0.2.1 : 2019-06-18
Release coinciding with bilby 0.5.2

### Added
-   Automated rescaling
-   Automated calibration
-   pesummary as a dependency

## v0.2.0 : 2019-06-05
Release coinciding with bilby 0.5.1, planned for initial review

### Added
-   Gaussian noise flag
-   Review script
-   Gracedb module and CLI
-   Plotting module and CLI
-   PP-test module and CLI

### Changed
-   examples_ini_file -> examples 
-   Many bug fixes

## v0.1.0 : 2019-04-29

### Added
-   Calibration, ROQ, PSD estimation, data-setting methods, etc

## v0.0.4 : 2019-03-05

### Added
-   Flag for running the data generation step on the local head node
-   Flag for setting random seeds

### Changes
-   Moved all command line argument logic to a single module with switches
-   Moved data generation to use gwpy only
-   Moved PSD generation t use gwpy only

## v0.0.3 : 2019-01-14

### Added
-   Support for pesummary module to produce summary files

### Changed
-   Minor bug fixes for argument passing and result file naming

## v0.0.2 : 2019-01-10

### Added
-   Added singularity containers
-   Add testing in python 3.5, 3.6, and 3.7
-   Add a `--local` flag for testing/debug (runs the code on the host rather than submitting to a queue)
-   Add a `--query_types` flag to specify list of LDRDataFind query types to use when building the `gw_data_find` command line

## [0.0.1] 2018-12-31

-   First working version release with basic functionality
