# step-exec-lib

[![build](https://github.com/giantswarm/step-exec-lib/actions/workflows/main.yml/badge.svg)](https://github.com/giantswarm/step-exec-lib/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/giantswarm/step-exec-lib/branch/master/graph/badge.svg)](https://codecov.io/gh/giantswarm/step-exec-lib)
[![PyPI Version](https://img.shields.io/pypi/v/step-exec-lib.svg)](https://pypi.org/project/step-exec-lib/)
[![Python Versions](https://img.shields.io/pypi/pyversions/step-exec-lib.svg)](https://pypi.org/project/step-exec-lib/)
[![Apache License](https://img.shields.io/badge/license-apache-blue.svg)](https://pypi.org/project/step-exec-lib/)

A simple library to easily orchestrate a set of Steps into a filtrable pipeline.

**Disclaimer**: docs are still work-in-progress!

Each step provides a defined set of actions. When a pipeline is execute first all `pre` actions
of all Steps are executed, then `run` actions and so on. Steps can provide labels, so
you can easily disable/enable a subset of steps.

A ready to use python app template. Based on `pipenv`.

## How to use the library

### BuildStep

The most important basic class is [BuildStep](step_exec_lib/steps.py). The class is abstract
and you have to inherit from it to provide any actual functionality.  The most important methods and properties of
this class are:

* Each `BuildStep` provides a set of step names it is associated with in the `steps_provided` property.
  These steps are used for filtering with `--steps`/`--skip-steps` command line options.
* `initialize_config` provides additional config options a specific class delivered from `BuildStep`
  wants to provide.
* `pre_run` is optional and should be used for validation and assertions. `pre_runs` of all `BuildSteps` are executed
  before any `run` method is executed. Its purpose is to allow the `abs`
  to quit with error even before any actual build or tests are done. The method can't be blocking and should run
  fast. If `pre_step` of any `BuildStep` fails, `run` methods of all `BuildSteps` are skipped.
* `run` is the method where actual long-running actions of the `BuildStep` are executed.
* `cleanup` is an optional method used to clean up resources that might have been needed by `run` but can't be cleaned
  up until all `runs` have executed. `cleanups` are called after any `run` failed or all of them are done.

### BuildStepsFilteringPipeline

`BuildStep` class provides the `steps_provided` property, but is not in control of whether it should be executed or not
and when. `BuildSteps` have to be assembled into `pipelines`. The basic pipeline in `BuildStepsFilteringPipeline`, which
allows you to make a sequential pipeline out of your steps and filter and skip them according to `steps_provided` they
return and command line options `--steps`/`--skip-steps`. Each major part of `abs` execution is combined into a
pipeline, like `HelmBuildFilteringPipeline` used to execute build pipeline with Helm 3 or `PytestTestFilteringPipeline`
which is used to execute tests using `pytest` once the build pipeline is done.
