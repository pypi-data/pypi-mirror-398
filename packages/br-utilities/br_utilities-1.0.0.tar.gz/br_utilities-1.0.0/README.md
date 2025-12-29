![br-utils for Python](https://br-utils.vercel.app/img/cover_br-utils.jpg)

[![PyPI Version](https://img.shields.io/pypi/v/br-utilities)](https://pypi.org/project/br-utilities)
[![PyPI Downloads](https://img.shields.io/pypi/dm/br-utilities)](https://pypi.org/project/br-utilities)
[![Python Version](https://img.shields.io/pypi/pyversions/br-utilities)](https://www.python.org/)
[![Test Status](https://img.shields.io/github/actions/workflow/status/LacusSolutions/br-utils-py/ci.yml?label=ci/cd)](https://github.com/LacusSolutions/br-utils-py/actions)
[![Last Update Date](https://img.shields.io/github/last-commit/LacusSolutions/br-utils-py)](https://github.com/LacusSolutions/br-utils-py)
[![Project License](https://img.shields.io/github/license/LacusSolutions/br-utils-py)](https://github.com/LacusSolutions/br-utils-py/blob/main/LICENSE)

Unified toolkit to deal with Brazilian documents (CPF and CNPJ): validation, formatting, and generation of valid IDs.

## Python Support

| ![Python 3.10](https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white) | ![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white) | ![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white) | ![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white) | ![Python 3.14](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white) |
|--- | --- | --- | --- | --- |
| Passing ✔ | Passing ✔ | Passing ✔ | Passing ✔ | Passing ✔ |

## Installation

```bash
$ pip install br-utilities
```

## Import

```python
# Using class-based resource
from br_utils import BrUtils

# Or import CPF/CNPJ utilities directly
from br_utils import CpfUtils, CnpjUtils

# Or using function-based approach
from br_utils import cpf_fmt, cpf_gen, cpf_val, cnpj_fmt, cnpj_gen, cnpj_val

# Or using the default instance
from br_utils import br_utils
```

## Usage

### Object-Oriented Usage

The `BrUtils` class provides a unified interface for all CPF and CNPJ operations:

```python
br_utils = BrUtils()

# CPF Operations
cpf = '93247057062'
print(br_utils.cpf.format(cpf))       # returns '932.470.570-62'
print(br_utils.cpf.is_valid(cpf))     # returns True
print(br_utils.cpf.generate())        # returns '65453043078'

# CNPJ Operations
cnpj = '11222333000181'
print(br_utils.cnpj.format(cnpj))     # returns '11.222.333/0001-81'
print(br_utils.cnpj.is_valid(cnpj))   # returns True
print(br_utils.cnpj.generate())       # returns '12345678000195'
```

#### With Configuration Options

You can configure the formatter and generator options for both CPF and CNPJ in the constructor:

```python
from br_utils import BrUtils
from br_utils.cpf import CpfFormatterOptions, CpfGeneratorOptions
from br_utils.cnpj import CnpjFormatterOptions, CnpjGeneratorOptions

br_utils = BrUtils(
    cpf_formatter=CpfFormatterOptions(hidden=True, hidden_key='#'),
    cpf_generator=CpfGeneratorOptions(format=True),
    cnpj_formatter=CnpjFormatterOptions(hidden=True, hidden_key='X'),
    cnpj_generator=CnpjGeneratorOptions(format=True),
)

# CPF with hidden digits
cpf = '93247057062'
print(br_utils.cpf.format(cpf))       # returns '932.###.###-##'
print(br_utils.cpf.generate())        # returns '730.085.350-06'

# CNPJ with hidden digits
cnpj = '11222333000181'
print(br_utils.cnpj.format(cnpj))     # returns '11.222.XXX/XXXX-XX'
print(br_utils.cnpj.generate())       # returns '12.345.678/0001-95'
```

### Using Individual Utilities

You can also use the individual `CpfUtils` and `CnpjUtils` classes directly:

```python
from br_utils import CpfUtils, CnpjUtils

cpf_utils = CpfUtils()
cnpj_utils = CnpjUtils()

# CPF operations
print(cpf_utils.format('93247057062'))     # '932.470.570-62'
print(cpf_utils.is_valid('93247057062'))   # True
print(cpf_utils.generate())                # '65453043078'

# CNPJ operations
print(cnpj_utils.format('11222333000181')) # '11.222.333/0001-81'
print(cnpj_utils.is_valid('11222333000181')) # True
print(cnpj_utils.generate())               # '12345678000195'
```

### Functional Programming

The package also provides standalone functions for each operation:

```python
from br_utils import cpf_fmt, cpf_gen, cpf_val, cnpj_fmt, cnpj_gen, cnpj_val

# CPF Functions
cpf = '93247057062'
print(cpf_fmt(cpf))                 # '932.470.570-62'
print(cpf_val(cpf))                 # True
print(cpf_gen())                    # '65453043078'

# CNPJ Functions
cnpj = '11222333000181'
print(cnpj_fmt(cnpj))               # '11.222.333/0001-81'
print(cnpj_val(cnpj))               # True
print(cnpj_gen())                   # '12345678000195'
```

Or use the default instance:

```python
from br_utils import br_utils

# CPF
print(br_utils.cpf.format('93247057062'))     # '932.470.570-62'
print(br_utils.cpf.is_valid('93247057062'))   # True
print(br_utils.cpf.generate())                # '65453043078'

# CNPJ
print(br_utils.cnpj.format('11222333000181')) # '11.222.333/0001-81'
print(br_utils.cnpj.is_valid('11222333000181')) # True
print(br_utils.cnpj.generate())               # '12345678000195'
```

## API Reference

### BrUtils Class

The `BrUtils` class consolidates CPF and CNPJ utilities in a single class.

```python
BrUtils(
    cpf_formatter: CpfFormatterOptions | None = None,
    cpf_generator: CpfGeneratorOptions | None = None,
    cnpj_formatter: CnpjFormatterOptions | None = None,
    cnpj_generator: CnpjGeneratorOptions | None = None,
)
```

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `cpf` | `CpfUtils` | Instance of `CpfUtils` for CPF operations |
| `cnpj` | `CnpjUtils` | Instance of `CnpjUtils` for CNPJ operations |

### CPF Operations

#### Formatting (`cpf_fmt` / `br_utils.cpf.format`)

Formats a CPF string with customizable delimiters and masking options.

```python
br_utils.cpf.format(
    cpf_string: str,
    hidden: bool | None = None,
    hidden_key: str | None = None,
    hidden_start: int | None = None,
    hidden_end: int | None = None,
    dot_key: str | None = None,
    dash_key: str | None = None,
    escape: bool | None = None,
    on_fail: Callable | None = None,
) -> str
```

**Examples:**

```python
cpf = '93247057062'

# Basic formatting
print(cpf_fmt(cpf))                 # '932.470.570-62'

# With hidden digits
print(cpf_fmt(cpf, hidden=True))    # '932.***.***.***-**'

# Custom delimiters
print(cpf_fmt(cpf, dot_key='', dash_key='_'))  # '932470570_62'
```

#### Generation (`cpf_gen` / `br_utils.cpf.generate`)

Generates valid CPF numbers with optional formatting and prefix completion.

```python
br_utils.cpf.generate(
    format: bool | None = None,
    prefix: str | None = None,
) -> str
```

**Examples:**

```python
# Generate random CPF
print(cpf_gen())                     # '65453043078'

# Generate formatted CPF
print(cpf_gen(format=True))          # '730.085.350-06'

# Complete a prefix
print(cpf_gen(prefix='456237'))      # '45623741038'
```

#### Validation (`cpf_val` / `br_utils.cpf.is_valid`)

Validates CPF numbers using the official algorithm.

```python
br_utils.cpf.is_valid(cpf_string: str) -> bool
```

**Examples:**

```python
print(cpf_val('93247057062'))        # True
print(cpf_val('932.470.570-62'))     # True
print(cpf_val('93247057063'))        # False
```

### CNPJ Operations

#### Formatting (`cnpj_fmt` / `br_utils.cnpj.format`)

Formats a CNPJ string with customizable delimiters and masking options.

```python
br_utils.cnpj.format(
    cnpj_string: str,
    hidden: bool | None = None,
    hidden_key: str | None = None,
    hidden_start: int | None = None,
    hidden_end: int | None = None,
    dot_key: str | None = None,
    slash_key: str | None = None,
    dash_key: str | None = None,
    escape: bool | None = None,
    on_fail: Callable | None = None,
) -> str
```

**Examples:**

```python
cnpj = '11222333000181'

# Basic formatting
print(cnpj_fmt(cnpj))                 # '11.222.333/0001-81'

# With hidden digits
print(cnpj_fmt(cnpj, hidden=True))    # '11.222.XXX/XXXX-XX'

# Custom delimiters
print(cnpj_fmt(cnpj, dot_key='', slash_key='-', dash_key=''))  # '11222333-000181'
```

#### Generation (`cnpj_gen` / `br_utils.cnpj.generate`)

Generates valid CNPJ numbers with optional formatting and prefix completion.

```python
br_utils.cnpj.generate(
    format: bool | None = None,
    prefix: str | None = None,
) -> str
```

**Examples:**

```python
# Generate random CNPJ
print(cnpj_gen())                     # '12345678000195'

# Generate formatted CNPJ
print(cnpj_gen(format=True))          # '12.345.678/0001-95'

# Complete a prefix
print(cnpj_gen(prefix='11222333'))    # '11222333000181'
```

#### Validation (`cnpj_val` / `br_utils.cnpj.is_valid`)

Validates CNPJ numbers using the official algorithm.

```python
br_utils.cnpj.is_valid(cnpj_string: str) -> bool
```

**Examples:**

```python
print(cnpj_val('11222333000181'))     # True
print(cnpj_val('11.222.333/0001-81')) # True
print(cnpj_val('11111111111111'))     # False
```

## Advanced Usage

### Accessing Individual Components

You can access the individual formatter, generator, and validator instances for both CPF and CNPJ:

```python
br_utils = BrUtils()

# Access CPF components
cpf_formatter = br_utils.cpf.formatter
cpf_generator = br_utils.cpf.generator
cpf_validator = br_utils.cpf.validator

# Access CNPJ components
cnpj_formatter = br_utils.cnpj.formatter
cnpj_generator = br_utils.cnpj.generator
cnpj_validator = br_utils.cnpj.validator

# Use them directly
cpf_formatter.format('93247057062', hidden=True)
cnpj_generator.generate(format=True)
```

### Importing from Submodules

You can also import directly from the `cpf` and `cnpj` submodules:

```python
# Import CPF resources
from br_utils.cpf import (
    CpfUtils,
    CpfFormatter,
    CpfFormatterOptions,
    CpfGenerator,
    CpfGeneratorOptions,
    CpfValidator,
    cpf_fmt,
    cpf_gen,
    cpf_val,
)

# Import CNPJ resources
from br_utils.cnpj import (
    CnpjUtils,
    CnpjFormatter,
    CnpjFormatterOptions,
    CnpjGenerator,
    CnpjGeneratorOptions,
    CnpjValidator,
    cnpj_fmt,
    cnpj_gen,
    cnpj_val,
)
```

## Dependencies

This package is built on top of the following specialized packages:

- [`cpf-utils`](https://pypi.org/project/cpf-utils) - CPF utilities (formatting, generation, validation)
- [`cnpj-utils`](https://pypi.org/project/cnpj-utils) - CNPJ utilities (formatting, generation, validation)

## Contribution & Support

We welcome contributions! Please see our [Contributing Guidelines](https://github.com/LacusSolutions/br-utils-py/blob/main/CONTRIBUTING.md) for details. But if you find this project helpful, please consider:

- ⭐ Starring the repository
- 🤝 Contributing to the codebase
- 💡 [Suggesting new features](https://github.com/LacusSolutions/br-utils-py/issues)
- 🐛 [Reporting bugs](https://github.com/LacusSolutions/br-utils-py/issues)

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/LacusSolutions/br-utils-py/blob/main/LICENSE) file for details.

## Changelog

See [CHANGELOG](https://github.com/LacusSolutions/br-utils-py/blob/main/packages/br-utilities/CHANGELOG.md) for a list of changes and version history.

---

Made with ❤️ by [Lacus Solutions](https://github.com/LacusSolutions)
