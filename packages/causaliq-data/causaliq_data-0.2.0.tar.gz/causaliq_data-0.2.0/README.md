# causaliq-data

[![Python Support](https://img.shields.io/pypi/pyversions/causaliq-core.svg)](https://pypi.org/project/causaliq-core/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This package provides data handling, statistical testing, and scoring infrastructure for causal discovery and Bayesian network operations.

## Installation

Install from PyPI:

```bash
pip install causaliq-data
```

## Status

🚧 **Active Development** - This repository is currently in active development, which involves:

- migrating functionality from the legacy monolithic [discovery repo](https://github.com/causaliq/discovery) 
- restructuring classes to reduce module size and improve maintainability and improve usability
- ensure CausalIQ development standards are met



## Features

Currently implemented:

- **Release v0.1.0 - Foundation Data**: CausalIQ compliant Data provider interface and concrete implementations with data store internally as pandas Dataframes or Numpy 2D arrays.
- **Release v0.2.0 - Score Functions**: Comprehensive scoring framework for Bayesian networks and DAGs with entropy-based (BIC, AIC, log-likelihood), Bayesian (BDE, K2, BDJ, BDS), and Gaussian (BGE, BIC-g, loglik-g) score types.

Planned releases (supporting legacy functionality):

- **Release v0.3.0 - CI Tests**: Conditional Independence

## Upcoming Key Innovations

### 🧩 Plugin Architecture
- **use by third-party software** - ability to use these data capabilities in third party structure learning algorithms so that comparisons are based on a common scoring or conditional independence framework, and performance optimisations speed up third-party algorithms.

### 🏛️ Stability Integration
- **Stable scores** - stable resolution of equal-score situations for unstable algorithms e.g. Tabu

### 🧠 LLM-assisted Causal Discovery
- **Data values** - Data values and variable names may provide part of the context for
LLM-assisted causal discovery
- **Knowledge integration** - incorporation of LLM and human expertise in scores and priors via the CausalIQ Knowledge package. 
- **Relationship explanations**: Natural language descriptions of relationships in data

### ⚡Optimised Performance
- **GPU Data provider** - support for optimised data handling on GPU hardware
- **Intelligent data scanning** - reduce number of full-row data scans

### 🎲 Enhanced Distribution Support
- **Mixed Types**: scores and independence tests that support mixtures of continuous and categorical variables


## Integration with CausalIQ Ecosystem

- 🔍 **CausalIQ Discovery** makes use of this package to provide objective functions and conditional independence
tests for structure learning algorithms.
- 🧪 **CausalIQ Analysis** uses score functions as part of the evaluation of learnt graphs.
- 💎 **CausalIQ Core** makes use of the BNFit interface to estimate parameters based on data.
- 🤖 **CausalIQ Workflow** uses the in-memory randomisation of this package for stability experiments.

## LLM Support

The following provides project-specific context for this repo which should be provided after the [personal and ecosystem context](https://github.com/causaliq/causaliq/blob/main/LLM_DEVELOPMENT_GUIDE.md):

```text
I wish to migrate the code in legacy/code/data following all CausalIQ development guidelines
so that the legacy repo can use the migrated code instead. I also want my legacy Bayesian Network
code to be able to use the BNFit interface (see bnfit_interface_spec.md). I would start by migrating
the Data abstract class and pandas.py. Please do this a little at a time and advise me what you intend
to do before making any changes.
```

## Quick Start

```python
# To be completed - example will score a known graph
```

## Getting started

### Prerequisites

- Git 
- Latest stable versions of Python 3.9, 3.10. 3.11 and 3.12


### Clone the new repo locally and check that it works

Clone the causaliq-core repo locally as normal

```bash
git clone https://github.com/causaliq/causaliq-data.git
```

Set up the Python virtual environments and activate the default Python virtual environment. You may see
messages from VSCode (if you are using it as your IDE) that new Python environments are being created
as the scripts/setup-env runs - these messages can be safely ignored at this stage.

```text
scripts/setup-env -Install
scripts/activate
```

Check that the causaliq-core CLI is working, check that all CI tests pass, and start up the local mkdocs webserver. There should be no errors  reported in any of these.

```text
causaliq-data --help
scripts/check_ci
mkdocs serve
```

Enter **http://127.0.0.1:8000/** in a browser and check that the 
causaliq-data documentation is visible.

If all of the above works, this confirms that the code is working successfully on your system.


## Documentation

Full API documentation is available at: **http://127.0.0.1:8000/** (when running `mkdocs serve`)

## Contributing

This repository is part of the CausalIQ ecosystem. For development setup:

1. Clone the repository
2. Run `scripts/setup-env -Install` to set up environments  
3. Run `scripts/check_ci` to verify all tests pass
4. Start documentation server with `mkdocs serve`

---

**Supported Python Versions**: 3.9, 3.10, 3.11, 3.12  
**Default Python Version**: 3.11  
**License**: MIT
