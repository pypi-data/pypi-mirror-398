![cpf-utils for Python](https://br-utils.vercel.app/img/cover_cpf-utils.jpg)

[![PyPI Version](https://img.shields.io/pypi/v/cpf-utils)](https://pypi.org/project/cpf-utils)
[![PyPI Downloads](https://img.shields.io/pypi/dm/cpf-utils)](https://pypi.org/project/cpf-utils)
[![Python Version](https://img.shields.io/pypi/pyversions/cpf-utils)](https://www.python.org/)
[![Test Status](https://img.shields.io/github/actions/workflow/status/LacusSolutions/br-utils-py/ci.yml?label=ci/cd)](https://github.com/LacusSolutions/br-utils-py/actions)
[![Last Update Date](https://img.shields.io/github/last-commit/LacusSolutions/br-utils-py)](https://github.com/LacusSolutions/br-utils-py)
[![Project License](https://img.shields.io/github/license/LacusSolutions/br-utils-py)](https://github.com/LacusSolutions/br-utils-py/blob/main/LICENSE)

Toolkit to deal with CPF data (Brazilian personal ID): validation, formatting and generation of valid IDs.

## Python Support

| ![Python 3.10](https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white) | ![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white) | ![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white) | ![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white) | ![Python 3.14](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white) |
|--- | --- | --- | --- | --- |
| Passing ✔ | Passing ✔ | Passing ✔ | Passing ✔ | Passing ✔ |

## Installation

```bash
$ pip install cpf-utils
```

## Import

```python
# Using class-based resource
from cpf_utils import CpfUtils

# Or using function-based approach
from cpf_utils import cpf_fmt, cpf_gen, cpf_val

# Or using the default instance
from cpf_utils import cpf_utils
```

## Usage

### Object-Oriented Usage

The `CpfUtils` class provides a unified interface for all CPF operations:

```python
cpf_utils = CpfUtils()
cpf = '93247057062'

# Format CPF
print(cpf_utils.format(cpf))       # returns '932.470.570-62'

# Validate CPF
print(cpf_utils.is_valid(cpf))      # returns True

# Generate CPF
print(cpf_utils.generate())          # returns '65453043078'
```

#### With Configuration Options

You can configure the formatter and generator options in the constructor:

```python
from cpf_fmt import CpfFormatterOptions
from cpf_gen import CpfGeneratorOptions

cpf_utils = CpfUtils(
    formatter=CpfFormatterOptions(
        hidden=True,
        hidden_key='#',
        hidden_start=3,
        hidden_end=10
    ),
    generator=CpfGeneratorOptions(format=True)
)

cpf = '93247057062'
print(cpf_utils.format(cpf))       # returns '932.###.###-##'
print(cpf_utils.generate())          # returns '730.085.350-06'
```

The options can be provided to the constructor or the respective methods. If passed to the constructor, the options will be attached to the `CpfUtils` instance. When passed to the methods, it only applies the options to that specific call.

```python
cpf_utils = CpfUtils(
    formatter=CpfFormatterOptions(hidden=True)
)

cpf = '93247057062'
print(cpf_utils.format(cpf))                  # '932.***.***.***-**'
print(cpf_utils.format(cpf, hidden=False))    # '932.470.570-62' (overrides instance options)
print(cpf_utils.format(cpf))                  # '932.***.***.***-**' (uses instance options again)
```

### Functional Programming

The package also provides standalone functions for each operation:

```python
cpf = '93247057062'

# Format CPF
print(cpf_fmt(cpf))                 # returns '932.470.570-62'

# Validate CPF
print(cpf_val(cpf))                 # returns True

# Generate CPF
print(cpf_gen())                     # returns '65453043078'
```

Or use the default instance:

```python
from cpf_utils import cpf_utils

cpf = '93247057062'
print(cpf_utils.format(cpf))        # returns '932.470.570-62'
print(cpf_utils.is_valid(cpf))      # returns True
print(cpf_utils.generate())          # returns '65453043078'
```

## API Reference

### Formatting (`cpf_fmt` / `CpfUtils.format`)

Formats a CPF string with customizable delimiters and masking options.

```python
cpf_utils.format(
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

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `hidden` | `bool \| None` | `False` | Whether to hide digits with a mask |
| `hidden_key` | `str \| None` | `'*'` | Character to replace hidden digits |
| `hidden_start` | `int \| None` | `3` | Starting index for hidden range (0-10) |
| `hidden_end` | `int \| None` | `10` | Ending index for hidden range (0-10) |
| `dot_key` | `str \| None` | `'.'` | String to replace dot characters |
| `dash_key` | `str \| None` | `'-'` | String to replace dash character |
| `escape` | `bool \| None` | `False` | Whether to HTML escape the result |
| `on_fail` | `Callable \| None` | `lambda value, error=None: value` | Fallback function for invalid input |

**Examples:**

```python
cpf = '93247057062'

# Basic formatting
print(cpf_fmt(cpf))                 # '932.470.570-62'

# With hidden digits
print(cpf_fmt(cpf, hidden=True))    # '932.***.***.***-**'

# Custom delimiters
print(cpf_fmt(cpf, dot_key='', dash_key='_'))  # '932470570_62'

# Custom hidden range
print(cpf_fmt(cpf, hidden=True, hidden_start=0, hidden_end=5, hidden_key='#'))  # '###.##0.570-62'
```

### Generation (`cpf_gen` / `CpfUtils.generate`)

Generates valid CPF numbers with optional formatting and prefix completion.

```python
cpf_utils.generate(
    format: bool | None = None,
    prefix: str | None = None,
) -> str
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `format` | `bool \| None` | `False` | Whether to format the output |
| `prefix` | `str \| None` | `''` | Prefix to complete with valid digits (1-9 digits) |

**Examples:**

```python
# Generate random CPF
print(cpf_gen())                     # '65453043078'

# Generate formatted CPF
print(cpf_gen(format=True))          # '730.085.350-06'

# Complete a prefix
print(cpf_gen(prefix='456237'))      # '45623741038'

# Complete and format
print(cpf_gen(prefix='456237410', format=True))  # '456.237.410-38'
```

### Validation (`cpf_val` / `CpfUtils.is_valid`)

Validates CPF numbers using the official algorithm.

```python
cpf_utils.is_valid(cpf_string: str) -> bool
```

**Examples:**

```python
# Valid CPF
print(cpf_val('93247057062'))        # True
print(cpf_val('932.470.570-62'))     # True

# Invalid CPF
print(cpf_val('93247057063'))        # False
```

## Advanced Usage

### Accessing Individual Components

You can access the individual formatter, generator, and validator instances:

```python
cpf_utils = CpfUtils()

# Access individual components
formatter = cpf_utils.formatter
generator = cpf_utils.generator
validator = cpf_utils.validator

# Use them directly
formatter.format('93247057062', hidden=True)
generator.generate(format=True)
validator.is_valid('93247057062')
```

### Custom Error Handling

```python
cpf = '123'  # Invalid length

# Custom fallback
def custom_fail(value, error=None):
    return f"Invalid CPF: {value}"

print(cpf_fmt(cpf, on_fail=custom_fail))  # 'Invalid CPF: 123'

# Return original value (default behavior)
print(cpf_fmt(cpf))  # '123'
```

## Dependencies

This package is built on top of the following specialized packages:

- [`cpf-fmt`](https://pypi.org/project/cpf-fmt) - CPF formatting
- [`cpf-gen`](https://pypi.org/project/cpf-gen) - CPF generation
- [`cpf-val`](https://pypi.org/project/cpf-val) - CPF validation

## Contribution & Support

We welcome contributions! Please see our [Contributing Guidelines](https://github.com/LacusSolutions/br-utils-py/blob/main/CONTRIBUTING.md) for details. But if you find this project helpful, please consider:

- ⭐ Starring the repository
- 🤝 Contributing to the codebase
- 💡 [Suggesting new features](https://github.com/LacusSolutions/br-utils-py/issues)
- 🐛 [Reporting bugs](https://github.com/LacusSolutions/br-utils-py/issues)

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/LacusSolutions/br-utils-py/blob/main/LICENSE) file for details.

## Changelog

See [CHANGELOG](https://github.com/LacusSolutions/br-utils-py/blob/main/packages/cpf-utils/CHANGELOG.md) for a list of changes and version history.

---

Made with ❤️ by [Lacus Solutions](https://github.com/LacusSolutions)
