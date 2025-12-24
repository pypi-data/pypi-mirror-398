# qbraid-core

[![Documentation](https://img.shields.io/badge/Documentation-DF0982)](https://qbraid.github.io/qbraid-core/)
[![codecov](https://codecov.io/gh/qBraid/qbraid-core/graph/badge.svg?token=vnZxySTsW2)](https://codecov.io/gh/qBraid/qbraid-core)
[![PyPI version](https://img.shields.io/pypi/v/qbraid-core.svg?color=blue)](https://pypi.org/project/qbraid-core/)
[![Python verions](https://img.shields.io/pypi/pyversions/qbraid-core.svg?color=blue)](https://pypi.org/project/qbraid-core/)
[![GitHub](https://img.shields.io/badge/issue_tracking-github-blue?logo=github)](https://github.com/qBraid/community/issues)

Python library providing core abstractions for software development within the qBraid ecosystem, and a low-level interface to a growing array of qBraid cloud services. The qbraid-core package forms the foundational base for the [qBraid CLI](https://pypi.org/project/qbraid-cli/), the [qBraid SDK](https://pypi.org/project/qbraid/), and the
[jupyter-environment-manager](https://pypi.org/project/jupyter-environment-manager/).

You can find the latest, most up to date, documentation [here](https://qbraid.github.io/qbraid-core/), including a list of services that are supported.

*See also*: [`qbraid-core-js`](https://qbraid.github.io/qbraid-core-js/)

## Getting Started

You can install qbraid-core from PyPI with:

```bash
python -m pip install qbraid-core
```

### Local configuration

After installing qbraid-core, you must configure your account credentials:

1. Create a qBraid account or log in to your existing account by visiting
   [account.qbraid.com](https://account.qbraid.com/)
2. Copy your [API Key](https://docs.qbraid.com/home/account#api-keys) from the left side of
    your [account page](https://account.qbraid.com/):
3. Save your API key from step 2 in local [configuration file](https://docs.qbraid.com/cli/user-guide/config-files). On Linux and macOS, this file is located at `~/.qbraid/qbraidrc`, where `~` corresponds to your home (`$HOME`) directory. On Windows, the equivalent default location is `%USERPROFILE%\.qbraid\qbraidrc`.

```ini
[default]
api-key = YOUR_KEY
url = https://api.qbraid.com/api
```

Or generate your `~/.qbraid/qbraidrc` file via the qbraid-core Python interface:

```python
>>> from qbraid_core import QbraidSession
>>> session = QbraidSession(api_key='API_KEY')
>>> session.save_config()
>>> session.get_available_services()
['chat', 'environments', 'quantum', 'storage']
```

Other credential configuration methods are available using the [qBraid-CLI](https://docs.qbraid.com/cli/api-reference/qbraid_configure).

### Verify setup

After configuring your qBraid credentials, verify your setup by running the following from a Python interpreter:

```python
>>> import qbraid_core
>>> quantum_client = qbraid_core.client('quantum')
>>> device_data = quantum_client.search_devices()
>>> for item in device_data:
...     print(item['qbraid_id'])
```

## Community

- For feature requests and bug reports: [Submit an issue](https://github.com/qBraid/community/issues)
- For discussions and/or specific questions about qBraid services, [join our discord community](https://discord.gg/KugF6Cnncm)
- For questions that are more suited for a forum, post to [Stack Overflow](https://stackoverflow.com/) with the [`qbraid`](https://stackoverflow.com/questions/tagged/qbraid) tag.

## Launch on qBraid

The "Launch on qBraid" button (below) can be added to any public GitHub
repository. Clicking on it automaically opens qBraid Lab, and performs a
`git clone` of the project repo into your account's home directory. Copy the
code below, and replace `YOUR-USERNAME` and `YOUR-REPOSITORY` with your GitHub
info.

[<img src="https://qbraid-static.s3.amazonaws.com/logos/Launch_on_qBraid_white.png" width="150">](https://account.qbraid.com?gitHubUrl=https://github.com/qBraid/qBraid.git)

Use the badge in your project's `README.md`:

```markdown
[<img src="https://qbraid-static.s3.amazonaws.com/logos/Launch_on_qBraid_white.png" width="150">](https://account.qbraid.com?gitHubUrl=https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git)
```

Use the badge in your project's `README.rst`:

```rst
.. image:: https://qbraid-static.s3.amazonaws.com/logos/Launch_on_qBraid_white.png
    :target: https://account.qbraid.com?gitHubUrl=https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
    :width: 150px
```
