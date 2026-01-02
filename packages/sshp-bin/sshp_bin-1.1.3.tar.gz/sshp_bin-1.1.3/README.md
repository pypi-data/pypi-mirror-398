# sshp-bin

[![PyPI - Version](https://img.shields.io/pypi/v/sshp-bin.svg)](https://pypi.org/project/sshp-bin)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/sshp-bin.svg)](https://pypi.org/project/sshp-bin)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/FlavioAmurrioCS/sshp-bin/main.svg)](https://results.pre-commit.ci/latest/github/FlavioAmurrioCS/sshp-bin/main)

Parallel SSH Executor.

This project provides pre-compiled binary wheels for the `sshp` tool, which allows you to execute SSH commands in parallel across multiple hosts.

Original project: [sshp](https://github.com/bahamas10/sshp)

-----

## Table of Contents

- [sshp-bin](#sshp-bin)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Usage](#usage)
  - [License](#license)

## Installation

With pipx:

```bash
pipx install sshp-bin
```

With uv:

```bash
uv tool install sshp-bin
```

## Usage
After installation, you can use the `sshp` command in your terminal. For example, to see the help message:

```bash
sshp --help
```

## License

`sshp-bin` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
