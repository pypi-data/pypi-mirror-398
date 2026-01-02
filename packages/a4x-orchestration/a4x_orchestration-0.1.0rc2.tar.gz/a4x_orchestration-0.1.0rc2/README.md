<h1 align="center">
A4X-Orchestration
</h1>

<a href="https://codecov.io/gh/Analytics4MD/a4x-orchestration"><img src="https://codecov.io/gh/Analytics4MD/a4x-orchestration/graph/badge.svg?token=FJP980TF2E"/></a>

## About

A4X-Orchestration is a Python library that abstracts the process of configuring a workflow to be
agnostic of the workflow management system (WMS) used. When using A4X-Orchestration, users can configure their
workflow for any supported WMS by performing the following steps:
1. Define workflow tasks using A4X-Orchestration
2. Combine workflow tasks into a workflow represented as a DAG using A4X-Orchestration
3. Call A4X-Orchestration's `Workflow.convert` method to get a WMS-specific representation of the workflow
4. If desired, perform additional, WMS-specific configuration using the output of `Workflow.convert`

Support for different WMSes is (for the most part) not built directly into A4X-Orchestration. Instead, A4X-Orchestration
uses entry point-based plugins to support different WMSes. So, to use A4X-Orchestration with a specific
WMS, users must install the plugin for that WMS. Below is an unofficial list of all supported
WMSes and how to install them:

<table>
    <tr>
        <th>Plugin Name</th>
        <th>Workflow Management System or<br>Resource Manager</th>
        <th>Install Command</th>
    </tr>
    <tr>
        <td>A4X Pegasus WMS</td>
        <td><a href="https://pegasus.isi.edu/">Pegasus</a></td>
        <td><code>pip install a4x-pegasus-wms</code></td>
    </tr>
    <tr>
        <td>Flux Plugin</th>
        <td><a href="https://flux-framework.org/">Flux</a></th>
        <td>N.A. (builtin)</td>
    </tr>
</table>

## Dependencies

A4X-Orchestration has the following dependencies:
* Python 3.7 or newer
* [networkx](https://networkx.org/)
* [ruamel.yaml](https://pypi.org/project/ruamel.yaml/)
* [Jinja2](https://jinja.palletsprojects.com/en/stable/)
* [importlib-metadata](https://pypi.org/project/importlib-metadata/) (only for Python versions less than 3.10)

Note that most users should not have to install these manually. Most Python package managers (e.g., `pip`)
will automatically install all these dependencies (except Python itself) when you install A4X-Orchestration.

## Installation

There are two ways to install A4X-Orchestration: (1) with `pip` and (2) with Spack.

### (1) Pip

A4X-Orchestration can be installed like most other Python packages by simply running:
```bash
$ python3 -m pip install a4x-orchestration
```

Additionally, users can install A4X-Orchestration from source by cloning the repository and running:
```bash
$ python3 -m pip install [-e] .
```

### (2) Spack

Support for building with Spack is not yet implemented.

## Using in Other Projects

A4X-Orchestration can be used by other projects once installed by simply importing it with:
```python
from a4x.orchestration import ...
```

To make A4X-Orchestration a dependency of your project, simply add the following to `pyproject.toml`
for a `pip`-installable project:
```toml
[project]
dependencies = [
    "a4x-orchestration"
]
```

Or add the following to `package.py` for a Spack-installable project:
```python
depends_on("a4x-orchestration")
```

<!-- ## Related Publications -->

## Contact Us

A4X-Orchestration is part of the Analytics4X project from the [Global Computing Lab](https://globalcomputing.group/).
For more information, please contact Michela Taufer (email: taufer@acm.org).

## Copyright and License

Copyright 2025 Global Computing Lab.

A4X-Core is distributed under the terms of the [Apache License, Version 2.0](https://spdx.org/licenses/Apache-2.0.html)
with [LLVM Exceptions](https://spdx.org/licenses/LLVM-exception.html).

See [LICENSE](./LICENSE) and [COPYRIGHT](./COPYRIGHT) for more details.

SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception

## Acknowledgements

This material is based upon work supported
by the US National Science Foundation under Grant No. 
2530461, 2513101, 2331152, 2223704, 2138811, and 2103845.

This work was performed under the auspices of the U.S. Department of Energy by Lawrence Livermore
National Laboratory under Contract DE-AC52-07NA27344 and was supported by the LLNL-LDRD Program
under Project No. 24-SI-005. 
