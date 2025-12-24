# SATAID Data Reader

A robust Python package to read, parse, and visualize meteorological satellite data from the proprietary SATAID format, developed by the Japan Meteorological Agency (JMA).

This tool makes valuable satellite imagery from satellites like Himawari accessible for research, analysis, and visualization within the Python ecosystem.

## Key Features
- Parses SATAID file headers to retrieve critical metadata.
- Extracts and calibrates data into a NumPy array.
- Automatically converts infrared channel data from Kelvin to Celsius.
- Provides a powerful `SataidArray` object with methods for:
  - **Plotting**: Simple plots and professional-grade map visualizations with Cartopy.
  - **Data Selection**: Cropping by geographic area or extracting values at specific points with interpolation.
  - **Exporting**: Saving data to NetCDF, GeoTIFF, and image files (PNG).
  - **Integration**: Seamless conversion to `xarray.DataArray` for advanced scientific analysis.

## Installation

```bash
pip install sataid
```

## Usage Example

```python
import sataid

# Read a SATAID file
sat_data = sataid.read_sataid('path/to/your/IR_FILE.dat')

# Display data description
sat_data.description()

# Create a map-based plot using a custom colormap
sat_data.plot(cartopy=True, cmap='jet')
```