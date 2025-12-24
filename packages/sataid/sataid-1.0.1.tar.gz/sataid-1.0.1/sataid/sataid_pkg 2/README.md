
# SATAID

A Python package to read and handle SATAID meteorological satellite data.

## Installation

```bash
pip install sataid
```

For TestPyPI:

```bash
pip install --index-url https://test.pypi.org/simple/ --no-deps sataid
```

## Usage

```python
import sataid as sat

data = sat.read_sataid("path/to/file.Z0000")
sat.description(data)
sat.plot(data)
sat.savefig(data)
```
