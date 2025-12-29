# Kaizo

Kaizo is a **declarative YAML-based configuration parser** for Python.
It allows you to dynamically load, resolve, and execute Python objects, functions, and plugins from YAML configuration files.

Key features:

- Cross-file imports
- Lazy execution
- Result caching
- Plugin dispatch
- Variable references
- Local Python module support

---

## Installation

Install Kaizo via pip:

```bash
pip install kaizo
```

Or install from source:

```bash
git clone https://github.com/NaughtFound/kaizo.git
cd kaizo
pip install -e .
```

Requirements:

- Python 3.10+
- PyYAML

---

## Quick Start

Create a simple configuration file `hello.yaml`:

```yaml
hello:
  module: builtins
  source: print
  args:
    - "Hello Kaizo"
```

Load and execute it:

```python
from kaizo import ConfigParser

parser = ConfigParser("hello.yaml")
config = parser.parse()

# Accessing the entry automatically resolves and executes it
config["hello"]  # Outputs: Hello Kaizo
```

---

## Documentation

Full documentation, including configuration, parser architecture, plugins, and utilities, is available in the docs:

[Kaizo Documentation](https://naughtfound.github.io/kaizo/)

---

## Contributing

Contributions are welcome! Please submit issues or pull requests via GitHub.

---

## License

[Apache License](LICENSE)
