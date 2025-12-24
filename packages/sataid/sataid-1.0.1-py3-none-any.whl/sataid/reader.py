import io
import re
from struct import unpack
import numpy as np

from .core import SataidArray

# ============================================================
#  SZDD DECOMPRESS (MS COMPRESS/EXPAND)
# ============================================================

def _szdd_decompress_bytes(data: bytes) -> bytes:
    """
    Decompress SZDD (MS COMPRESS/EXPAND) data into raw bytes.

    Expected SZDD header layout:
      0x00: 'SZDD'
      0x08: mode
      0x09: missing_char
      0x0A-0x0D: uncompressed size (uint32 little-endian)
      0x0E-...: LZSS payload

    This is used for Himawari WIS files that are distributed with SZDD
    compression. The function returns the decompressed raw byte stream
    that can then be parsed as a normal SATAID binary file.
    """
    if len(data) < 14 or data[:4] != b"SZDD":
        raise ValueError("Not an SZDD file (signature 'SZDD' not found).")

    print("Detected SZDD-compressed file → decompressing...")

    out_len = unpack('I', data[10:14])[0]
    payload = data[14:]

    # LZSS sliding window (4096 bytes), initialized with spaces
    window = bytearray(4096)
    for i in range(4096):
        window[i] = 0x20  # space character

    pos = 4096 - 16
    out = bytearray()

    p = 0
    while p < len(payload):
        control = payload[p]
        p += 1

        bit = 1
        while bit <= 0x80 and p < len(payload):
            if control & bit:
                # Literal byte
                if p >= len(payload):
                    break
                ch = payload[p]
                p += 1
                out.append(ch)
                window[pos] = ch
                pos = (pos + 1) & 0xFFF
            else:
                # Sequence (offset, length)
                if p + 1 > len(payload):
                    break
                matchpos = payload[p]
                matchlen = payload[p + 1]
                p += 2

                matchpos |= (matchlen & 0xF0) << 4
                matchlen = (matchlen & 0x0F) + 3

                for _ in range(matchlen):
                    c = window[matchpos & 0xFFF]
                    matchpos = (matchpos + 1) & 0xFFF
                    out.append(c)
                    window[pos] = c
                    pos = (pos + 1) & 0xFFF

            bit <<= 1

    if out_len > 0 and len(out) >= out_len:
        out = out[:out_len]

    return bytes(out)


# ============================================================
#  SATAID READER (RAW / SZDD)
# ============================================================

def read_sataid(fname):
    """
    Read a SATAID binary file (either raw or SZDD-compressed) and return
    a SataidArray object.

    The returned object contains:
    - lat / lon 1D coordinate arrays
    - calibrated data (reflectance or brightness temperature in °C)
    - full metadata (header fields)
    - original digital counts & calibration table for lossless round-trip

    Parameters
    ----------
    fname : str
        Path to a SATAID raw file (e.g. *.Z0000) or SZDD-compressed WIS
        file (e.g. *.wis).

    Returns
    -------
    SataidArray
        High-level container for SATAID data and metadata.
    """

    def _calibration(data, cord, eint, cal):
        """
        Apply calibration and compute geographic coordinates.

        Notes
        -----
        - Data row 0 corresponds to the northern edge of the domain.
        - The last data row corresponds to the southern edge.
        Therefore:
        - lat[0]  = upper/northern latitude
        - lat[-1] = lower/southern latitude

        SATAID 'cord' layout:
          cord = (lat1, lon1, lat2, lon2, lat3, lon3, lat4, lon4)
          UL(lat1, lon1), UR(lat2, lon2), LL(lat3, lon3), LR(lat4, lon4)

        `eint` is (nx, ny).
        """
        # UL(lat1,lon1), UR(lat2,lon2), LL(lat3,lon3), LR(lat4,lon4)
        lat_ul = float(cord[0])  # top (north)
        lon_ul = float(cord[1])  # left (west)
        lat_ll = float(cord[4])  # bottom (south)
        lon_ur = float(cord[3])  # right (east)

        nx, ny = eint  # eint = (nx, ny)

        # Latitude from north → south (matches data row order)
        lats = np.linspace(lat_ul, lat_ll, ny, dtype=np.float64)
        # Longitude from west → east
        lons = np.linspace(lon_ul, lon_ur, nx, dtype=np.float64)

        idx = data.astype(np.int64) - 1
        idx = np.clip(idx, 0, len(cal) - 1)
        calibrated_data = cal[idx]
        return lats, lons, calibrated_data

    # --- Read file and detect SZDD compression ---
    with open(fname, 'rb') as f:
        first4 = f.read(4)
        f.seek(0)
        if first4 == b"SZDD":
            raw_bytes = _szdd_decompress_bytes(f.read())
        else:
            raw_bytes = f.read()

    fi = io.BytesIO(raw_bytes)

    # --- Parse SATAID header ---
    recl = unpack('I', fi.read(4))[0]
    chan = unpack('c' * 8, fi.read(8))
    sate = unpack('c' * 8, fi.read(8))
    fi.read(4)  # skip
    ftim = unpack('I' * 8, fi.read(4 * 8))
    etim = unpack('I' * 8, fi.read(4 * 8))
    calb = unpack('I', fi.read(4))
    fint = unpack('I' * 2, fi.read(4 * 2))
    eres = unpack('f' * 2, fi.read(4 * 2))
    eint = unpack('I' * 2, fi.read(4 * 2))  # (nx, ny)
    nrec = unpack('I' * 2, fi.read(4 * 2))
    cord = unpack('f' * 8, fi.read(4 * 8))
    ncal = unpack('I' * 3, fi.read(4 * 3))
    fi.read(24)  # skip
    asat = unpack('f' * 6, fi.read(4 * 6))
    fi.read(32)  # skip
    vers = unpack('c' * 4, fi.read(4))
    fi.read(4)   # closing recl

    # --- Calibration table ---
    nbyt = unpack('I', fi.read(4))[0]
    cal_len = int(nbyt / 4 - 2)
    if cal_len <= 0 or cal_len > 100000:
        raise ValueError(f"Unreasonable cal_len: {cal_len} (nbyt={nbyt})")

    cal = np.array(unpack('f' * cal_len, fi.read(4 * cal_len)))
    fi.read(4)  # closing nbyt

    # --- Digital image data ---
    data_raw = []
    nx, ny = eint
    if nrec[1] == 2:  # 2 bytes per pixel (uint16)
        for _ in range(ny):
            line_nbyt = unpack('I', fi.read(4))[0]
            line = unpack('H' * nx, fi.read(nx * 2))
            data_raw.append(line[0:nx])
            pad_len = line_nbyt - (nx * 2 + 8)
            if pad_len > 0:
                fi.read(pad_len)
            fi.read(4)  # trailing nbyt
    elif nrec[1] == 1:  # 1 byte per pixel (uint8)
        for _ in range(ny):
            line_nbyt = unpack('I', fi.read(4))[0]
            line = unpack('B' * (line_nbyt - 8), fi.read(line_nbyt - 8))
            data_raw.append(line[0:nx])
            fi.read(4)  # trailing nbyt
    else:
        raise NotImplementedError("Only 1-byte and 2-byte record formats are supported (nrec[1] == 1 or 2).")

    data_raw = np.asarray(data_raw, dtype=np.uint16)
    lats, lons, data = _calibration(data_raw, cord, eint, cal)

    # --- Convert to Celsius and assign units based on channel name ---
    channel_name_raw = b"".join(chan).decode(errors='ignore')
    m = re.match(r'^[A-Za-z0-9]+', channel_name_raw)
    channel_name = m.group(0) if m else ''

    units = 'unknown'
    if channel_name in SataidArray.ShortName:
        idx = SataidArray.ShortName.index(channel_name)
        if 0 <= idx <= 6:
            units = 'Reflectance'
        elif 7 <= idx <= 15:
            data = data - 273.15  # Kelvin → Celsius
            units = '°C'

    sataid_obj = SataidArray(
        lats=lats, lons=lons, data=data, sate=sate, chan=chan, etim=etim,
        fint=fint, asat=asat, vers=vers, eint=eint, cord=cord, eres=eres,
        fname=fname, units=units, ftim=ftim
    )

    # Store additional internal metadata for round-trip writing
    sataid_obj._digital_data = data_raw        # original digital counts
    sataid_obj._cal_table = cal               # calibration table
    sataid_obj._nrec = nrec
    sataid_obj._ncal = ncal
    sataid_obj._calb = calb
    sataid_obj._recl = recl

    return sataid_obj


def read_sataid_array(fname):
    """
    Convenience reader returning only (lat, lon, data).

    This is useful for machine learning or generic numerical processing
    where full SATAID metadata is not required.

    Parameters
    ----------
    fname : str
        Path to a SATAID raw or SZDD-compressed file.

    Returns
    -------
    (numpy.ndarray, numpy.ndarray, numpy.ndarray)
        Tuple of (latitudes, longitudes, calibrated_data).
    """
    sat = read_sataid(fname)
    return sat.lat, sat.lon, sat.data
