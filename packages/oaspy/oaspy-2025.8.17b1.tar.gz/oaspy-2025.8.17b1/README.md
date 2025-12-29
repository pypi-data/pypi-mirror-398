# oaspy

[![Python: 3.10](https://img.shields.io/badge/python-3.10-blue?logo=python)](https://docs.python.org/3.10/)
[![Python: 3.11](https://img.shields.io/badge/python-3.11-blue?logo=python)](https://docs.python.org/3.11/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/oaspy.svg)](https://pypi.org/project/oaspy/)
---

**oaspy** is a quick-and-dirty tool to generate an [OpenApi 3.x](https://www.openapis.org) specification from an [insomnia V4](https://insomnia.rest/products/insomnia)/[Yaak](https://yaak.app/) collections.


## Getting Started

For more, see the [documentation](./docs/README.md).

### Installation

**oaspy** is available on [PyPI](https://pypi.org/project/oaspy/):

```shell
pip install oaspy
```

## Usage

To run **oaspy**, try any of the following:

```sh
oaspy --help
```


## Commands

### **gen**

Generate an OpenApi 3.x file from an Insomnia/Yaak collections v4.

```sh
oaspy gen --help
```

- with the default options.

```sh
# using Insomnia v4
oaspy gen --file Insomnia_file_v4.json

# using Yaak v4
oaspy gen --file Yaak_file_v4.json
```

- defining the version of openapi to generate.

```sh
# using Insomnia v4
oaspy gen --file Insomnia_file_v4.json --schema v30

# using Yaak v4
oaspy gen --file Yaak_file_v4.json --schema v30
```
> argument `v30` refers to openapi version 3.0.x

- defining the version of openapi to generate and the output file name.

```sh
# using Insomnia v4
oaspy gen --file Insomnia_file_v4.json --output my_oa3_export.json

# using Yaak v4
oaspy gen --file Yaak_file_v4.json --output my_oa3_export.json
```

- order folders

```sh
# using Insomnia v4
oaspy gen --file Insomnia_file_v4.json -o_f

# using Yaak v4
oaspy gen --file Yaak_file_v4.json -o_f
```

- order request

```sh
# using Insomnia v4
oaspy gen --file Insomnia_file_v4.json -o_r

# using Yaak v4
oaspy gen --file Yaak_file_v4.json -o_r
```

- a complete version of the above.

```sh
# using Insomnia v4
oaspy gen --file Insomnia_file_v4.json --schema v30 --output my_oa3_export.json -o_f -o_r

# using Yaak v4
oaspy gen --file Yaak_file_v4.json --schema v30 --output my_oa3_export.json -o_f -o_r
```


### **check**

Validates the structure of an OpenApi file.

```sh
oaspy check --help
```

```sh
oaspy check --file my_oa3_export.json
```

### **info**

Shows information from an Insomnia/Yaak v4 file.

```sh
oaspy info --help
```

```sh
oaspy info --file Insomnia_file_v4.json
```

```sh
oaspy info --file Yaak_file_v4.json
```


## License

This project is licensed under the terms of the [MIT.](https://opensource.org/license/mit/) license.

The full text of this license can be found in the [LICENSE.](./LICENSE) file.


## How to Contribute

For any questions, comments, suggestions or contributions, go to the [issues.](https://gitlab.com/HomeInside/oaspy/-/issues) section.
Before opening a new issue, check the existing ones to find a solution (possibly already existing) to the problem you are facing.
