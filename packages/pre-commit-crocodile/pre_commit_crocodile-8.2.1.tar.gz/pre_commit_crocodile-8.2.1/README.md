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
[![guidelines](https://img.shields.io/badge/radiandevcore-guidelines-brightgreen?logo=gitlab)](https://radiandevcore.gitlab.io/wiki/guidelines)

Git hooks manager intended for developers using [pre-commit](https://pre-commit.com/), [prek](https://github.com/j178/prek) and [commitizen](https://commitizen-tools.github.io/commitizen/).

**Documentation:** <https://radiandevcore.gitlab.io/tools/pre-commit-crocodile>  
**Package:** <https://pypi.org/project/pre-commit-crocodile/>

---

## Features

**`pre-commit-crocodile` uses the following features:**

- **CLI - [pre-commit](https://pre-commit.com/):** Automated Git hooks before commits and upon pushes
- **CLI - [prek](https://github.com/j178/prek):** Better `pre-commit`, re-engineered in Rust
- **CLI - [commitizen](https://commitizen-tools.github.io/commitizen/):** Commits tools and validation based upon [conventional commits](https://www.conventionalcommits.org/en/)
- **Hooks - [pre-commit-hooks](https://github.com/pre-commit/pre-commit-hooks):** Common `pre-commit` hooks useful for developers

**`pre-commit-crocodile` provides the following features:**

- **CLI - [pre-commit-crocodile](.):** Management tool for `pre-commit` Git hooks
- **CLI - [pre-commit-crocodile](.):** Easy Git hooks activation for development teams
- **CLI - [pre-commit-crocodile](.):** Dependencies preparation for [pre-commit](https://pre-commit.com/) or [prek](https://github.com/j178/prek).
- **CLI - [pre-commit-crocodile](https://radiandevcore.gitlab.io/tools/pre-commit-crocodile/pre-commit/):** Automated customized configurations for maintainers
- **Hooks - [prepare-commit-msg](https://radiandevcore.gitlab.io/tools/pre-commit-crocodile/hooks/):** Prepare commit message automatically based on changes

---

## Preview

![preview.svg](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/raw/8.2.1/docs/preview.svg)

---

<span class="page-break"></span>

## Usage

<!-- prettier-ignore-start -->
<!-- readme-help-start -->

```yaml
usage: pre-commit-crocodile [-h] [--version] [--no-color] [--update-check] [--settings] [--set GROUP KEY VAL]
                            [-l | -i | -c | -b | -e | -d | -a | -C | -r] [--config FOLDER | -D] [--commit]
                            [--components | --remotes | --no-components] [--offline] [--stage STAGE]
                            [--set-engine [ENGINE]] [--]

pre-commit-crocodile: Git hooks manager intended for developers using pre-commit, prek and commitizen

internal arguments:
  -h, --help             # Show this help message
  --version              # Show the current version
  --no-color             # Disable colors outputs with 'NO_COLOR=1'
                         # (or default settings: [themes] > no_color)
  --update-check         # Check for newer package updates
  --settings             # Show the current settings path and contents
  --set GROUP KEY VAL    # Set settings specific 'VAL' value to [GROUP] > KEY
                         # or unset by using 'UNSET' as 'VAL'

modes arguments:
  -l, --list             # List Git hooks installed in sources
  -i, --install          # Install dependencies for pre-commit hooks
  -c, --configure        # Update sources with hooks configurations
  -b, --badges           # Update documentation with badges configurations
  -e, --enable           # Enable pre-commit hooks
  -d, --disable          # Disable pre-commit hooks
  -a, --autoupdate       # Autoupdate pre-commit hooks
  -C, --clean            # Clean pre-commit cached hooks
  -r, --run              # Run pre-commit hooks

configurations arguments:
  --config FOLDER        # Use configurations from a specific folder
  -D, --default          # Use global default configurations instead of sources
  --commit               # Commit configurations changes automatically (implies --configure)
  --components           # Import components from GitLab with 'include: component:'
  --remotes              # Import components from GitLab with 'include: remote:'
  --no-components        # Import components templates locally instead of 'include: component:'
  --offline              # Use offline mode to disable configurations autoupdate
  --stage STAGE          # Run a specific pre-commit stage with --run
                         # (use 'list' to list supported stages)

settings arguments:
  --set-engine [ENGINE]  # Set pre-commit engine to use (pre-commit, prek, default: pre-commit)

positional arguments:
  --                     # Positional arguments separator (recommended)
```

<!-- readme-help-stop -->
<!-- prettier-ignore-end -->

---

<span class="page-break"></span>

## Installation

```bash
{
  # Option 1: If using pipx
  if type pipx >/dev/null 2>&1; then
    pipx ensurepath
    pipx install pre-commit-crocodile
    pipx upgrade pre-commit-crocodile

  # Option 2: If using pip
  else
    sudo pip3 install pre-commit-crocodile
  fi
}
```

---

## Compatibility

Projects compatible with `pre-commit-crocodile` can use this badge to ease things for developers, both as an indicator and a documentation shortcut button :

> [![pre-commit-crocodile](https://img.shields.io/badge/pre--commit--crocodile-enabled-brightgreen?logo=gitlab)](https://radiandevcore.gitlab.io/tools/pre-commit-crocodile)

```markdown title="Badge in Markdown"
[![pre-commit-crocodile](https://img.shields.io/badge/pre--commit--crocodile-enabled-brightgreen?logo=gitlab)](https://radiandevcore.gitlab.io/tools/pre-commit-crocodile)
```

```html title="Badge in HTML"
<a href="https://radiandevcore.gitlab.io/tools/pre-commit-crocodile"><img src="https://img.shields.io/badge/pre--commit--crocodile-enabled-brightgreen?logo=gitlab" alt="pre-commit-crocodile" style="max-width:100%;"></a>
```

---

<span class="page-break"></span>

## Projects with configurations | [![pre-commit-crocodile](https://img.shields.io/badge/pre--commit--crocodile-enabled-brightgreen?logo=gitlab)](https://radiandevcore.gitlab.io/tools/pre-commit-crocodile)

### Configure engine to use (once per user)

- **[prek](https://github.com/j178/prek):** Recent Rust re-implementation, in development and faster (default, recommended)
- **[pre-commit](https://pre-commit.com/):** Original Python implementation, stable but slower (legacy)

```bash
pre-commit-crocodile --set-engine [pre-commit,prek]
```

### Install dependencies (once per user)

```bash
pre-commit-crocodile --install
```

### Enable hooks for a project

```bash
pre-commit-crocodile --enable
```

### Manually run hooks of a project

```bash
pre-commit-crocodile --run
```

### Disable hooks for a project

```bash
pre-commit-crocodile --disable
```

---

## Projects without configurations | [![pre-commit](https://img.shields.io/badge/pre--commit-missing-gold)](https://github.com/pre-commit/pre-commit)

### Import or refresh configurations

```bash
pre-commit-crocodile --configure
```

---

## Projects maintenance | [![pre-commit-crocodile](https://img.shields.io/badge/pre--commit--crocodile-enabled-brightgreen?logo=gitlab)](https://radiandevcore.gitlab.io/tools/pre-commit-crocodile)

### Update hooks automatically

```bash
pre-commit-crocodile --autoupdate
```

### Cleanup hooks cache

```bash
pre-commit-crocodile --clean
```

---

<span class="page-break"></span>

## Dependencies

- [colored](https://pypi.org/project/colored/): Terminal colors and styles
- [commitizen](https://pypi.org/project/commitizen/): Simple commit conventions for internet citizens
- [pre-commit](https://pre-commit.com/): A framework for managing and maintaining pre-commit hooks
- [pre-commit-crocodile](https://radiandevcore.gitlab.io/tools/pre-commit-crocodile): Git hooks manager intended for developers using pre-commit, prek and commitizen
- [prek](https://github.com/j178/prek): Better `pre-commit`, re-engineered in Rust
- [setuptools](https://pypi.org/project/setuptools/): Build and manage Python packages
- [update-checker](https://pypi.org/project/update-checker/): Check for package updates on PyPI
- [uv](https://github.com/astral-sh/uv): An extremely fast Python package and project manager, written in Rust.

---

## References

- [.gitlab-ci.yml](https://docs.gitlab.com/ee/ci/yaml/): GitLab CI/CD Pipeline Configuration Reference
- [conventionalcommits](https://www.conventionalcommits.org/en/v1.0.0/): Conventional Commits specification for commit messages
- [gcil](https://radiandevcore.gitlab.io/tools/gcil): Launch .gitlab-ci.yml jobs locally
- [git-cliff](https://github.com/orhun/git-cliff): CHANGELOG generator
- [gitlab-release](https://pypi.org/project/gitlab-release/): Utility for publishing on GitLab
- [mkdocs](https://www.mkdocs.org/): Project documentation with Markdown
- [mkdocs-coverage](https://pawamoy.github.io/mkdocs-coverage/): Coverage plugin for mkdocs documentation
- [mkdocs-exporter](https://adrienbrignon.github.io/mkdocs-exporter/): Exporter plugin for mkdocs documentation
- [mkdocs-material](https://squidfunk.github.io/mkdocs-material/): Material theme for mkdocs documentation
- [mypy](https://pypi.org/project/mypy/): Optional static typing for Python
- [pexpect-executor](https://radiandevcore.gitlab.io/tools/pexpect-executor): Automate interactive CLI tools actions
- [PyPI](https://pypi.org/): The Python Package Index
- [termtosvg](https://pypi.org/project/termtosvg/): Record terminal sessions as SVG animations
- [twine](https://pypi.org/project/twine/): Utility for publishing on PyPI
