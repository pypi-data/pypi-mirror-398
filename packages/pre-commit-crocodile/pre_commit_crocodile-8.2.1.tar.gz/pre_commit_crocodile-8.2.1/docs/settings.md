# pre-commit-crocodile

<!-- documentation no-toc -->
<!-- markdownlint-disable no-inline-html -->

[![Release](https://img.shields.io/pypi/v/pre-commit-crocodile?color=blue)](https://pypi.org/project/pre-commit-crocodile)
[![Python](https://img.shields.io/pypi/pyversions/pre-commit-crocodile?color=blue)](https://pypi.org/project/pre-commit-crocodile)
[![Downloads](https://img.shields.io/pypi/dm/pre-commit-crocodile?color=blue)](https://pypi.org/project/pre-commit-crocodile)
[![License](https://img.shields.io/gitlab/license/RadianDevCore/tools/pre-commit-crocodile?color=blue)](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/-/blob/main/LICENSE)
<br />
[![Build](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/badges/main/pipeline.svg)](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/-/commits/main/)
[![Bugs](https://sonarcloud.io/api/project_badges/measure?project=RadianDevCore_pre-commit-crocodile&metric=bugs)](https://sonarcloud.io/dashboard?id=RadianDevCore_pre-commit-crocodile)
[![Code Smells](https://sonarcloud.io/api/project_badges/measure?project=RadianDevCore_pre-commit-crocodile&metric=code_smells)](https://sonarcloud.io/dashboard?id=RadianDevCore_pre-commit-crocodile)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=RadianDevCore_pre-commit-crocodile&metric=coverage)](https://sonarcloud.io/dashboard?id=RadianDevCore_pre-commit-crocodile)
[![Lines of Code](https://sonarcloud.io/api/project_badges/measure?project=RadianDevCore_pre-commit-crocodile&metric=ncloc)](https://sonarcloud.io/dashboard?id=RadianDevCore_pre-commit-crocodile)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=RadianDevCore_pre-commit-crocodile&metric=alert_status)](https://sonarcloud.io/dashboard?id=RadianDevCore_pre-commit-crocodile)
<br />
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Commitizen friendly](https://img.shields.io/badge/commitizen-friendly-brightgreen.svg)](https://commitizen-tools.github.io/commitizen/)
[![gcil](https://img.shields.io/badge/gcil-enabled-brightgreen?logo=gitlab)](https://radiandevcore.gitlab.io/tools/gcil)
[![pre-commit-crocodile](https://img.shields.io/badge/pre--commit--crocodile-enabled-brightgreen?logo=gitlab)](https://radiandevcore.gitlab.io/tools/pre-commit-crocodile)

Git hooks manager intended for developers using [pre-commit](https://pre-commit.com/), [prek](https://github.com/j178/prek) and [commitizen](https://commitizen-tools.github.io/commitizen/).

---

## Userspace available settings

`pre-commit-crocodile` creates a `settings.ini` configuration file in a userspace folder.

For example, it allows to disable the automated updates daily check (`[updates] > enabled`)

The `settings.ini` file location and contents can be shown with the following command:

```bash
pre-commit-crocodile --settings
```

---

## Environment available configurations

`pre-commit-crocodile` uses `colored` for colors outputs and `questionary` for interactive menus.

If colors of both outputs types do not match the terminal's theme,  
an environment variable `NO_COLOR=1` can be defined to disable colors.
