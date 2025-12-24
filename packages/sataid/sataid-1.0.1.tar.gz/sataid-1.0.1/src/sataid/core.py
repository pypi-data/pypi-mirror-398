import os
import re
from struct import pack
from typing import Optional

import numpy as np
from matplotlib import pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable

from .utils import etim_to_datetime
from .colormaps import get_custom_colormap

class SataidArray:
    """
    Lightweight container providing xarray-like access to SATAID data.

    Attributes
    ----------
    lat : numpy.ndarray
        1D latitude array (north → south).
    lon : numpy.ndarray
        1D longitude array (west → east).
    data : numpy.ndarray
        2D calibrated data (Reflectance or Brightness Temperature in °C).
    units : str
        Data units ('Reflectance', '°C', or 'unknown').

    Methods
    -------
    description()
        Print a formatted summary of the dataset.
    plot(...)
        Quick visualization with or without Cartopy.
    savefig(...)
        Save plots to disk.
    sel(...)
        Select by point or lat/lon bounding box (returns scalar or subset).
    to_netcdf(...)
        Export to NetCDF4.
    to_geotiff(...)
        Export to GeoTIFF (rasterio required).
    to_sataid(...)
        Write back to SATAID binary format (including subsets).
    to_xarray(...)
        Convert to xarray.DataArray (xarray required).
    to_array()
        Return (lat, lon, data).
    """

    ShortName = ['V1', 'V2', 'VS', 'N1', 'N2', 'N3', 'I4',
                 'WV', 'W2', 'W3', 'MI', 'O3', 'IR', 'L2', 'I2', 'CO']

    def __init__(self,
                 lats: np.ndarray,
                 lons: np.ndarray,
                 data: np.ndarray,
                 sate: tuple,
                 chan: tuple,
                 etim: tuple,
                 fint: Optional[tuple] = None,
                 asat: Optional[tuple] = None,
                 vers: Optional[tuple] = None,
                 eint: Optional[tuple] = None,
                 cord: Optional[tuple] = None,
                 eres: Optional[tuple] = None,
                 fname: Optional[str] = None,
                 units: Optional[str] = None,
                 ftim: Optional[tuple] = None):
        self.lat = lats
        self.lon = lons
        self.data = data

        self.sate = sate
        self.chan = chan
        self.etim = etim
        self.ftim = ftim
        self.fint = fint
        self.asat = asat
        self.vers = vers
        self.eint = eint
        self.cord = cord
        self.eres = eres
        self.fname = fname
        self.units = units

        # Internal metadata for round-trip SATAID writing
        self._digital_data: Optional[np.ndarray] = None  # digital counts
        self._cal_table: Optional[np.ndarray] = None
        self._nrec: Optional[tuple] = None
        self._ncal: Optional[tuple] = None
        self._calb: Optional[tuple] = None
        self._recl: Optional[int] = None

    # ------------------ helper properties ------------------

    @property
    def satellite_name(self) -> str:
        """Return cleaned satellite name (e.g., 'Himawari-8', 'Himawari-9')."""
        if not self.sate:
            return ""
        name = b"".join(self.sate).decode(errors='replace').strip()
        return 'Himawari-9' if name == 'Himawa-9' else name

    @property
    def channel_name(self) -> str:
        """
        Return the base channel name (alphabetic prefix), e.g.:
        'IR' from 'IR1', 'WV' from 'WV_', etc.
        """
        if not self.chan:
            return ""
        raw_name = b"".join(self.chan).decode(errors='ignore')
        match = re.match(r'^[A-Za-z0-9]+', raw_name)
        return match.group(0) if match else ''

    # ------------------ description ------------------

    def _get_description_string(self):
        """Build a formatted multi-line description string."""
        nadir_coord = f"{self.asat[3]:.6f}, {self.asat[4]:.6f}" if self.asat is not None else ""
        altitude = f"{self.asat[5]:.2f} km" if self.asat is not None else ""
        time_str = etim_to_datetime(self.etim).strftime("%Y-%m-%d %H:%M UTC") if self.etim is not None else ""
        dimension = f"{self.data.shape[1]}x{self.data.shape[0]}"
        resolution = f"{self.eres[0]}" if self.eres is not None else ""
        version = b"".join(self.vers).decode(errors='replace') if self.vers is not None else ""
        lats = self.lat
        lons = self.lon
        coord_range = (
            f"lat : {lats.min():.6f} - {lats.max():.6f}\n"
            f"lon : {lons.min():.6f} - {lons.max():.6f}"
        )
        desc = (
            "=== Data Description ===\n"
            f"Time: {time_str}\n"
            f"Channel: {self.channel_name}\n"
            f"Dimension: {dimension}\n"
            f"Resolution: {resolution}\n"
            f"Units: {self.units}\n"
            f"SATAID Version: {version}\n"
            f"Coordinate Range:\n{coord_range}\n\n"
            "=== Satellite Description ===\n"
            f"Satellite: {self.satellite_name}\n"
            f"Nadir Coordinate: {nadir_coord}\n"
            f"Altitude: {altitude}\n\n"
        )
        return desc

    def description(self):
        """Print a formatted description of the dataset."""
        print(self._get_description_string())

    def to_array(self):
        """
        Return a tuple (lat, lon, data).

        This is equivalent to calling read_sataid_array on a file, but
        for an already-instantiated SataidArray.
        """
        return self.lat, self.lon, self.data

    # ------------------ plotting ------------------

    def _create_plot(self, cartopy=True, coastline_resolution=None,
                     coastline_color=None, coastline_width=None, cmap=None):
        """
        Create a Matplotlib figure for quick visualization.
        """
        plot_data = self.data.copy()

        # ----- default settings based on units -----
        plot_cmap = cmap
        norm = None
        cbar_kwargs = {}

        if self.units == 'Reflectance':
            colorbar_label = 'Reflectance'
            default_cmap = 'gray'
            vmin, vmax = 0, 1.1
        elif self.units == '°C':
            colorbar_label = 'Brightness Temperature (°C)'
            default_cmap = 'gray_r'
            vmin, vmax = -80, 60
        else:
            colorbar_label = f'Value ({self.units})' if self.units else 'Value'
            default_cmap = 'gray'
            vmin, vmax = None, None

        # ----- custom colormap (EH, RAINBOW_IR, etc.) -----
        custom = None
        if isinstance(plot_cmap, str):
            custom = get_custom_colormap(plot_cmap, self.channel_name, self.units)

        if custom is not None:
            plot_cmap, norm, label_from_custom, custom_cbar_kwargs = custom
            
            # If custom map returned None (e.g. invalid channel), fallback
            if plot_cmap is None:
                plot_cmap = default_cmap
                # Reset others just in case
                norm = None
                label_from_custom = None
                custom_cbar_kwargs = {}

            if label_from_custom:
                colorbar_label = label_from_custom
            if custom_cbar_kwargs:
                cbar_kwargs.update(custom_cbar_kwargs)
            # When using a norm, vmin/vmax are handled by the norm
            vmin = vmax = None
        else:
            if plot_cmap is None:
                plot_cmap = default_cmap

        # ----- titles -----
        time_str = etim_to_datetime(self.etim).strftime('%Y-%m-%d %H:%M UTC') \
                   if self.etim is not None else ""
        channel_label = self.channel_name
        if isinstance(cmap, str):
             c_upper = cmap.upper()
             if c_upper in ('EH', 'EH_IR', 'SW', 'WE', 'RAINBOW_IR', 'IR_GOES'):
                 channel_label = c_upper

        left_title = f"{self.satellite_name} {channel_label}"
        right_title = time_str

        # ----- Cartopy plot -----
        if cartopy:
            try:
                import cartopy.crs as ccrs
                import cartopy.feature as cfeature
            except ImportError:
                print("\nError: 'cartopy' is required for mapped plots.")
                print("Install via: pip install cartopy matplotlib")
                return

            # Determine coastline color default based on colormap
            if coastline_color is None:
                if isinstance(cmap, str) and cmap.upper() in ('EH', 'EH_IR'):
                    coastline_color = 'white'
                else:
                    coastline_color = 'blue'

            # Determine coastline width and resolution dynamically if not provided
            max_extent = 0
            if self.lat.size > 0 and self.lon.size > 0:
                 max_extent = max(self.lat.max() - self.lat.min(), self.lon.max() - self.lon.min())

            if coastline_width is None:
                if self.lat.size == 0 or self.lon.size == 0:
                    print("Warning: Data is empty (0 size), nothing to plot.")
                    return None
                 
                if max_extent > 40:
                    coastline_width = 0.5
                elif max_extent > 20:
                    coastline_width = 0.7
                elif max_extent > 10:
                    coastline_width = 0.9
                else:
                    coastline_width = 1.2
            
            # Dynamic resolution
            # > 80 deg: 110m (Global)
            # > 20 deg: 50m (Regional)
            # <= 20 deg: 10m (Local/High Res)
            if coastline_resolution is None:
                if max_extent > 80:
                    coastline_resolution = '110m'
                elif max_extent > 20:
                    coastline_resolution = '50m'
                else:
                    coastline_resolution = '10m'

            fig, ax = plt.subplots(
                figsize=(10, 8),
                subplot_kw={'projection': ccrs.PlateCarree()}
            )

            imshow_kwargs = dict(
                extent=(self.lon.min(), self.lon.max(),
                        self.lat.min(), self.lat.max()),
                origin='upper',
                cmap=plot_cmap,
                interpolation='none',
                transform=ccrs.PlateCarree()
            )
            if norm is not None:
                imshow_kwargs["norm"] = norm
            else:
                if vmin is not None:
                    imshow_kwargs["vmin"] = vmin
                if vmax is not None:
                    imshow_kwargs["vmax"] = vmax

            img = ax.imshow(plot_data, **imshow_kwargs)

            ax.coastlines(resolution=coastline_resolution,
                          color=coastline_color, linewidth=coastline_width)
            ax.add_feature(cfeature.BORDERS, linewidth=coastline_width * 0.5,
                           edgecolor=coastline_color)
            gl = ax.gridlines(draw_labels=True, linewidth=0.5,
                              color='gray', alpha=0.5, linestyle='--')
            gl.top_labels = False
            gl.right_labels = False
            gl.xlabel_style = {'size': 9}
            gl.ylabel_style = {'size': 9}

            ax.set_title(left_title, loc='left',
                         fontsize=10, fontweight='bold')
            ax.set_title(right_title, loc='right',
                         fontsize=10, fontweight='bold')

            # Colorbar with a dedicated Axes (non-GeoAxes)
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="3%", pad=0.04,
                                      axes_class=plt.Axes)

            cbar = fig.colorbar(img, cax=cax, orientation='vertical',
                                **cbar_kwargs)
            cbar.set_label(colorbar_label, size=9)
            cbar.ax.tick_params(labelsize=8)
            if self.units == '°C':
                cbar.ax.invert_yaxis()

        # ----- Plain imshow plot (no Cartopy) -----
        else:
            fig, ax = plt.subplots(figsize=(10, 6))

            imshow_kwargs = dict(
                extent=(self.lon.min(), self.lon.max(),
                        self.lat.min(), self.lat.max()),
                aspect='auto',
                cmap=plot_cmap,
            )
            if norm is not None:
                imshow_kwargs["norm"] = norm
            else:
                if vmin is not None:
                    imshow_kwargs["vmin"] = vmin
                if vmax is not None:
                    imshow_kwargs["vmax"] = vmax

            img = ax.imshow(plot_data, **imshow_kwargs)

            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="3%", pad=0.04)

            cbar = fig.colorbar(img, cax=cax, **cbar_kwargs)
            cbar.set_label(colorbar_label, size=9)
            cbar.ax.tick_params(labelsize=8)
            if self.units == '°C':
                cbar.ax.invert_yaxis()

            ax.set_title(right_title, loc='right',
                         fontsize=10, fontweight='bold')
            ax.set_title(left_title, loc='left',
                         fontsize=10, fontweight='bold')
            ax.set_xlabel('Longitude', fontsize=9)
            ax.set_ylabel('Latitude', fontsize=9)

        return fig

    def plot(self, cartopy=True, coastline_resolution=None,
             coastline_color=None, coastline_width=None, cmap=None):
        """
        Display the data interactively.

        Thin wrapper around _create_plot() that calls plt.show().

        See _create_plot() for parameter details.
        """
        fig = self._create_plot(cartopy=cartopy,
                                coastline_resolution=coastline_resolution,
                                coastline_color=coastline_color,
                                coastline_width=coastline_width,
                                cmap=cmap)
        if fig:
            plt.show()

    def savefig(self, output_file=None, cartopy=True,
                coastline_resolution=None, coastline_color=None, 
                coastline_width=None, cmap=None):
        """
        Save a visualization of the data to an image file.

        Parameters
        ----------
        output_file : str, optional
            Output filename. If None and `fname` is known, the script
            will append `.png` to the original input filename.
        cartopy, coastline_resolution, coastline_color, cmap :
            Passed directly to _create_plot().
        """
        fig = self._create_plot(cartopy=cartopy,
                                coastline_resolution=coastline_resolution,
                                coastline_color=coastline_color,
                                coastline_width=coastline_width,
                                cmap=cmap)
        if not fig:
            return

        filename_to_save = output_file
        if filename_to_save is None and self.fname:
            filename_to_save = os.path.basename(self.fname) + '.png'

        if filename_to_save:
            print(f"Saving plot to: {filename_to_save}")
            fig.savefig(filename_to_save, bbox_inches='tight', dpi=300)
            plt.close(fig)

    # ------------------ selection (.sel) ------------------

    def sel(self, latitude=None, longitude=None, method=None):
        """
        Select data by coordinates.

        Two modes are supported:

        1. Point extraction
           latitude : float
           longitude: float
           method   : 'nearest' (default), 'linear', or 'cubic'
              - 'nearest' uses simple nearest-neighbor lookup.
              - 'linear' / 'cubic' use RectBivariateSpline (requires SciPy).

           Examples
           --------
           sat.sel(latitude=-7.0, longitude=110.0)
           sat.sel(latitude=-7.0, longitude=110.0, method='linear')

        2. Region (bounding-box) extraction
           latitude : slice(start_lat, end_lat)
           longitude: slice(start_lon, end_lon)

           Examples
           --------
           sat.sel(latitude=slice(-10, 0), longitude=slice(100, 120))

           Returns a new SataidArray for the subset, preserving metadata
           and enabling round-trip writing via .to_sataid().
        """
        # ----- point extraction -----
        if isinstance(latitude, (int, float)) and isinstance(longitude, (int, float)):
            if method is None:
                method = 'nearest'

            if method == 'nearest':
                lat_idx = np.abs(self.lat - latitude).argmin()
                lon_idx = np.abs(self.lon - longitude).argmin()
                return self.data[lat_idx, lon_idx]

            elif method in ['linear', 'cubic']:
                try:
                    from scipy.interpolate import RectBivariateSpline
                except ImportError:
                    print(f"\nError: 'scipy' is required for method='{method}'.")
                    print("Install via: pip install scipy")
                    return None

                lats_interp, data_interp = (self.lat, self.data)
                # RectBivariateSpline expects monotonically increasing latitudes
                if lats_interp[0] > lats_interp[-1]:
                    lats_interp = lats_interp[::-1]
                    data_interp = data_interp[::-1, :]

                k = 3 if method == 'cubic' else 1
                interpolator = RectBivariateSpline(
                    lats_interp, self.lon, data_interp, kx=k, ky=k)
                return interpolator(latitude, longitude)[0, 0]
            else:
                raise NotImplementedError(
                    f"Method '{method}' is not supported for point extraction."
                )

        # ----- region (crop) extraction -----
        lat_idx = slice(None)
        lon_idx = slice(None)
        if latitude is not None:
            if not isinstance(latitude, slice):
                raise TypeError("For region extraction, 'latitude' must be a slice.")
            lat_min, lat_max = latitude.start, latitude.stop
            lat_idx = (self.lat >= min(lat_min, lat_max)) & (self.lat <= max(lat_min, lat_max))
        if longitude is not None:
            if not isinstance(longitude, slice):
                raise TypeError("For region extraction, 'longitude' must be a slice.")
            lon_min, lon_max = longitude.start, longitude.stop
            lon_idx = (self.lon >= min(lon_min, lon_max)) & (self.lon <= max(lon_min, lon_max))

        data_subset = self.data[np.ix_(lat_idx, lon_idx)]
        lats_subset = self.lat[lat_idx]
        lons_subset = self.lon[lon_idx]

        subset_obj = SataidArray(
            lats_subset, lons_subset, data_subset,
            sate=self.sate, chan=self.chan, etim=self.etim,
            fint=self.fint, asat=self.asat, vers=self.vers,
            eint=self.eint, cord=self.cord, eres=self.eres,
            fname=self.fname, units=self.units, ftim=self.ftim
        )

        # Also crop the underlying digital data, so .to_sataid()
        # can write a consistent subset.
        if self._digital_data is not None:
            subset_obj._digital_data = self._digital_data[np.ix_(lat_idx, lon_idx)]
        subset_obj._cal_table = self._cal_table
        subset_obj._nrec = self._nrec
        subset_obj._ncal = self._ncal
        subset_obj._calb = self._calb
        subset_obj._recl = self._recl
        return subset_obj

    # ------------------ NetCDF & GeoTIFF ------------------

    def to_netcdf(self, output_filename=None):
        """
        Export the dataset to a NetCDF4 file.

        Parameters
        ----------
        output_filename : str, optional
            Output NetCDF filename. If None and the original file name
            is known, '.nc' is appended to `fname`.
        """
        try:
            import netCDF4 as nc
        except ImportError:
            print("\nError: 'netCDF4' is required for NetCDF export.")
            print("Install via: pip install netCDF4")
            return
            
        if output_filename is None and self.fname:
            output_filename = os.path.basename(self.fname) + '.nc'

        print(f"Saving data to NetCDF: {output_filename}")
        with nc.Dataset(output_filename, 'w', format='NETCDF4') as ds:
            ds.description = self._get_description_string()
            ds.author = "Sepriando"

            ds.createDimension('lat', self.data.shape[0])
            ds.createDimension('lon', self.data.shape[1])

            latitudes = ds.createVariable('lat', 'f4', ('lat',))
            longitudes = ds.createVariable('lon', 'f4', ('lon',))
            latitudes.units = "degrees_north"
            longitudes.units = "degrees_east"
            latitudes[:] = self.lat
            longitudes[:] = self.lon

            data_var = ds.createVariable(self.channel_name, 'f4', ('lat', 'lon',))
            data_var.long_name = f"Data from SATAID channel {self.channel_name}"
            if self.units:
                data_var.units = self.units
            data_var[:, :] = self.data

    def to_geotiff(self, output_filename=None):
        """
        Export the dataset to a GeoTIFF file (requires rasterio).

        Parameters
        ----------
        output_filename : str, optional
            Output GeoTIFF filename. If None and the original file name
            is known, '.tif' is appended to `fname`.
        """
        try:
            import rasterio
            from rasterio.transform import from_bounds
        except ImportError:
            print("\nError: 'rasterio' is required for GeoTIFF export.")
            print("Install via: pip install rasterio")
            return

        if output_filename is None and self.fname:
            output_filename = os.path.basename(self.fname) + '.tif'

        print(f"Saving data to GeoTIFF: {output_filename}")

        left, right = self.lon.min(), self.lon.max()
        bottom, top = self.lat.min(), self.lat.max()
        height, width = self.data.shape
        transform = from_bounds(left, bottom, right, top, width, height)

        with rasterio.open(
            output_filename,
            'w',
            driver='GTiff',
            height=height,
            width=width,
            count=1,
            dtype=str(self.data.dtype),
            crs='EPSG:4326',
            transform=transform
        ) as dst:
            dst.write(self.data, 1)

    # ------------------ to_sataid (USING DIGITAL_DATA) ------------------

    def to_sataid(self, output_filename: Optional[str] = None):
        """
        Write the current SataidArray to SATAID binary format.

        This supports both full scenes and cropped subsets. No inverse
        calibration is performed; instead the original digital counts
        (`_digital_data`) are subset and written together with the
        original calibration table. This ensures a lossless round-trip
        as long as the object originated from `read_sataid()`.

        Parameters
        ----------
        output_filename : str, optional
            Output SATAID filename. If None and the original filename
            is known, '<original>_out.sataid' is used.
        """
        if output_filename is None:
            if self.fname:
                output_filename = os.path.basename(self.fname) + '.sataid'

            else:
                raise ValueError("output_filename was not provided and original file name is unknown.")

        if self._digital_data is None:
            raise ValueError("Digital data (_digital_data) not available. Make sure the object comes from read_sataid().")
        if self._cal_table is None or self._nrec is None or self._ncal is None or self._calb is None:
            raise ValueError("Internal metadata incomplete for to_sataid().")

        print(f"Saving data to SATAID binary file: {output_filename}")

        digital_data = self._digital_data.astype(np.uint16)

        ny, nx = digital_data.shape
        new_eint = (nx, ny)

        # Build new cord based on subset extents:
        lat_min = float(self.lat.min())
        lat_max = float(self.lat.max())
        lon_min = float(self.lon.min())
        lon_max = float(self.lon.max())
        # UL(lat1,lon1), UR(lat2,lon2), LL(lat3,lon3), LR(lat4,lon4)
        new_cord = [
            lat_max, lon_min,   # UL
            lat_max, lon_max,   # UR
            lat_min, lon_min,   # LL
            lat_min, lon_max    # LR
        ]

        recl = self._recl if self._recl is not None else 288

        with open(output_filename, 'wb') as fo:
            fo.write(pack('I', recl))
            fo.write(pack('c' * 8, *self.chan))
            fo.write(pack('c' * 8, *self.sate))
            fo.write(pack('I', 0))

            ftim_to_write = self.ftim if self.ftim is not None else self.etim
            fo.write(pack('I' * 8, *ftim_to_write))
            fo.write(pack('I' * 8, *self.etim))
            fo.write(pack('I', self._calb[0]))
            fo.write(pack('I' * 2, *self.fint))
            fo.write(pack('f' * 2, *self.eres))
            fo.write(pack('I' * 2, *new_eint))
            fo.write(pack('I' * 2, *self._nrec))
            fo.write(pack('f' * 8, *new_cord))
            fo.write(pack('I' * 3, *self._ncal))
            fo.write(b'\x00' * 24)
            fo.write(pack('f' * 6, *self.asat))
            fo.write(b'\x00' * 32)
            fo.write(pack('c' * 4, *self.vers))
            fo.write(pack('I', recl))

            # Calibration table: write as-is
            cal_nbyt = (len(self._cal_table) + 2) * 4
            fo.write(pack('I', cal_nbyt))
            fo.write(self._cal_table.astype('f4').tobytes())
            fo.write(pack('I', cal_nbyt))

            if self._nrec[1] != 2:
                raise NotImplementedError("Writing for 1-byte data (nrec[1] == 1) not implemented yet.")

            # Image data, line by line (same orientation as read_sataid)
            line_data_len = new_eint[0] * 2
            base_len = line_data_len + 8
            padding_len = (4 - (base_len % 4)) % 4
            line_nbyt = base_len + padding_len

            for i in range(new_eint[1]):
                fo.write(pack('I', line_nbyt))
                line_data = digital_data[i, :].astype('uint16')
                fo.write(line_data.tobytes())
                if padding_len > 0:
                    fo.write(b'\x00' * padding_len)
                fo.write(pack('I', line_nbyt))

        print("SATAID binary file successfully written.")

    # ------------------ to_xarray ------------------

    def to_xarray(self):
        """
        Convert the SataidArray into an xarray.DataArray.

        Requires the `xarray` package.

        Returns
        -------
        xarray.DataArray or None
            DataArray with 'lat' and 'lon' coordinates, or None if
            xarray is not installed.
        """
        try:
            import xarray as xr
        except ImportError:
            print("\nError: 'xarray' is required for this conversion.")
            print("Install via: pip install xarray")
            return None

        lats_xr, data_xr = (self.lat, self.data)
        # xarray prefers latitudes increasing from south → north
        if lats_xr[0] > lats_xr[-1]:
            lats_xr = lats_xr[::-1]
            data_xr = data_xr[::-1, :]

        coords = {'lat': ('lat', lats_xr), 'lon': ('lon', self.lon)}
        attrs = {
            'satellite': self.satellite_name,
            'channel': self.channel_name,
            'units': self.units,
            'long_name': f'Data from SATAID channel {self.channel_name}'
        }

        return xr.DataArray(
            data=data_xr, dims=('lat', 'lon'),
            coords=coords, name=self.channel_name, attrs=attrs
        )
