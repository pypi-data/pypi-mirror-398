<div align="center">

# pushikoo-getter-gh

GitHub getter adapter for Pushikoo. Monitors GitHub repository commits.

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/Pushikoo/pushikoo-getter-gh/package.yml)](https://github.com/Pushikoo/pushikoo-getter-gh/actions)
[![Python](https://img.shields.io/pypi/pyversions/pushikoo-getter-gh)](https://pypi.org/project/pushikoo-getter-gh)
[![PyPI version](https://badge.fury.io/py/pushikoo-getter-gh.svg)](https://pypi.org/project/pushikoo-getter-gh)
[![License](https://img.shields.io/github/license/Pushikoo/pushikoo-getter-gh.svg)](https://pypi.org/project/pushikoo-getter-gh/)

</div>

## Configuration

### Adapter Config

| Field  | Type             | Default           | Description                                                   |
| ------ | ---------------- | ----------------- | ------------------------------------------------------------- |
| `auth` | `dict[str, str]` | `{"default": ""}` | GitHub API tokens. Key is the token name, value is the token. |

### Instance Config

| Field    | Type   | Default     | Description                                         |
| -------- | ------ | ----------- | --------------------------------------------------- |
| `repo`   | `str`  | Required    | Repository path, e.g. `Pushikoo/pushikoo-getter-gh` |
| `commit` | `bool` | `true`      | Enable commit monitoring                            |
| `auth`   | `str`  | `"default"` | Token name to use from adapter config               |
