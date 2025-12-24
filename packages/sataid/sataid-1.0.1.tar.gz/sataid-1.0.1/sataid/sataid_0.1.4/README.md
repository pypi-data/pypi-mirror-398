# SATAID

SATAID is a Python package for reading and visualizing Himawari-8 SATAID binary data.

## Installation
```bash
pip install sataid
```

## Usage Example
```python
import sataid as sat

sat_data = sat.read_sataid("sample_file.Z0000")
sat_data.description()
sat_data.plot()
```

## License
MIT
