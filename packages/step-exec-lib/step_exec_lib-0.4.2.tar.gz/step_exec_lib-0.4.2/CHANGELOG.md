# Changelog

Based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), following
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## 0.4.2 2024-12-22

- add testing for python 3.14
- switch project management tool from poetry to uv

## 0.4.1 2024-12-03

- remove `utils/git.py` as unrelated to this project

## 0.3.1 2024-10-23

- drop support for python 3.9, add support for python 3.13

## [0.2.4] 2024-10-08

- bug fix: wrong discovery of the commit hash

## [0.2.3] 2024-10-08

### Changed

- git tag discovery uses now both annotated and unannotated tags

## [0.2.2] 2024-10-07

- fix: the previous change didn't correctly handle the case when there are no tags at all

## [0.2.1] 2024-10-07

- fix: git tag detection in `utils/git` now checks only the last tag reachable on the current branch

## [0.2.0] 2024-05-28

- dependency updates
- changed supported python versions to 3.9, 3.10, 3.11 and 3.12

## [0.1.5] 2021-10-22

- fixed:
  - output capture in `run_and_handle_error`

## [0.1.4] 2021-10-20

- fixed
  - use sys.stdout in `run_and_handle_error` to get feedback from tests.

## [0.1.3] 2021-10-11

- fixed
  - fix error handling in `utils.processes.run_and_handle_error()`

## [0.1.2] 2021-10-11

- fixed
  - fix error handling in `utils.processes.run_and_handle_error()`

## [0.1.1] 2021-10-06

- added
  - `utils.processes.run_and_handle_error()`
- changed
  - upgraded dependencies
  - python 3.10 included in test platforms

## [0.1.0] 2021-06-02

- added
  - Initial commit
