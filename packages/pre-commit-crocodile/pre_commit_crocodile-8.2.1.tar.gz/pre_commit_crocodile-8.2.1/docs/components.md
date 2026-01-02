# pre-commit-crocodile

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

## CI/CD components

**GitLab CI/CD Catalog:** <https://gitlab.com/explore/catalog/RadianDevCore/tools/pre-commit-crocodile>

---

### `commits` - GitLab CI job to validate newly pushed commits

**Validate commits added on a branch or for a merge request :**

- **Show commits specifications** and syntax examples
- **Check commits automatically** with `commitizen` configurations
- **Run pre-commit checks** on all files
- **Deny `WIP` commits** on GitLab branches

```yaml title="Sources / .gitlab-ci.yml"
include:
  - component: gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commits@X.Y.Z # Adapt to latest release tag
    # remote: https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/-/raw/X.Y.Z/templates/commits.yml # Use on self-managed GitLab instances
    inputs:
      stage: prepare

stages:
  - prepare
  - ...
```
