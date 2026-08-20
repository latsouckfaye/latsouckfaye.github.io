"""Minimal pure-Python reader for the site's multi-band LZW-compressed GeoTIFF.

No GIS dependency (rasterio/GDAL/tifffile) is available in this environment,
so this module implements just enough of the TIFF 6.0 spec — IFD parsing and
TIFF-flavor LZW decompression (early-change, MSB-first) — to recover the raw
float32 bands. Validated against the file's own embedded GDAL statistics.
"""
import struct
import numpy as np

_TYPE_SIZE = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 11: 4, 12: 8}
NODATA = -3.4e38


def _read_ifd(data, offset, endian):
    n = struct.unpack(endian + "H", data[offset:offset + 2])[0]
    entries = {}
    p = offset + 2
    for _ in range(n):
        tag, typ, count = struct.unpack(endian + "HHI", data[p:p + 8])
        valoff = data[p + 8:p + 12]
        tsize = _TYPE_SIZE.get(typ, 1)
        total = tsize * count
        raw = valoff[:total] if total <= 4 else data[struct.unpack(endian + "I", valoff)[0]:][:total]
        if typ == 3:
            vals = struct.unpack(endian + "H" * count, raw[:2 * count])
        elif typ == 4:
            vals = struct.unpack(endian + "I" * count, raw[:4 * count])
        else:
            vals = raw
        entries[tag] = vals
        p += 12
    return entries


def _lzw_decode(buf, expected_len):
    """TIFF-flavor LZW (early change), MSB-first bit packing."""
    CLEAR, EOI = 256, 257
    out = bytearray()
    bitbuf = bitcnt = pos = 0
    codesize = 9

    def reset_table():
        return [bytes([i]) for i in range(256)] + [b"", b""]

    table = reset_table()
    prev = None
    while len(out) < expected_len:
        while bitcnt < codesize:
            if pos >= len(buf):
                return bytes(out[:expected_len])
            bitbuf = (bitbuf << 8) | buf[pos]
            pos += 1
            bitcnt += 8
        bitcnt -= codesize
        code = (bitbuf >> bitcnt) & ((1 << codesize) - 1)

        if code == EOI:
            break
        if code == CLEAR:
            table = reset_table()
            codesize = 9
            prev = None
            continue
        if code < len(table):
            entry = table[code]
        elif code == len(table) and prev is not None:
            entry = prev + prev[:1]
        else:
            raise ValueError(f"bad LZW code {code} (table size {len(table)})")
        out += entry
        if prev is not None:
            table.append(prev + entry[:1])
        prev = entry
        tlen = len(table)
        if tlen == 511:
            codesize = 10
        elif tlen == 1023:
            codesize = 11
        elif tlen == 2047:
            codesize = 12
    return bytes(out[:expected_len])


def read_tiff_bands(path):
    """Return a list of (H, W) float32 numpy arrays, one per band, NaN where nodata."""
    with open(path, "rb") as f:
        data = f.read()

    endian = "<" if data[0:2] == b"II" else ">"
    ifd_offset = struct.unpack(endian + "I", data[4:8])[0]
    e = _read_ifd(data, ifd_offset, endian)

    W, H = e[256][0], e[257][0]
    spp = e[277][0]
    rows_per_strip = e[278][0]
    strip_offsets, strip_byte_counts = e[273], e[279]
    n_strips_per_band = -(-H // rows_per_strip)

    bands = []
    strip_i = 0
    for _ in range(spp):
        band = np.zeros((H, W), dtype=np.float32)
        row = 0
        for _ in range(n_strips_per_band):
            off, bc = strip_offsets[strip_i], strip_byte_counts[strip_i]
            this_rows = min(rows_per_strip, H - row)
            decoded = _lzw_decode(data[off:off + bc], this_rows * W * 4)
            band[row:row + this_rows, :] = np.frombuffer(decoded, dtype=endian + "f4").reshape(this_rows, W)
            row += this_rows
            strip_i += 1
        band[band <= NODATA] = np.nan
        bands.append(band)
    return bands


def read_geotransform(path):
    """Return (scale_x, scale_y, tie_x, tie_y): the pixel size in meters and
    the projected (UTM) coordinate of the top-left pixel, read from the
    GeoTIFF's ModelPixelScaleTag (33550) / ModelTiepointTag (33922)."""
    with open(path, "rb") as f:
        data = f.read()
    endian = "<" if data[0:2] == b"II" else ">"
    ifd_offset = struct.unpack(endian + "I", data[4:8])[0]
    e = _read_ifd(data, ifd_offset, endian)
    scale_x, scale_y, _ = struct.unpack(endian + "3d", e[33550][:24])
    _, _, _, tie_x, tie_y, _ = struct.unpack(endian + "6d", e[33922][:48])
    return scale_x, scale_y, tie_x, tie_y


def utm_to_latlon(easting, northing, zone=38, southern=True):
    """Inverse UTM projection (WGS84 ellipsoid), pure numpy — no pyproj/GDAL.
    Standard Snyder (1987) closed-form formulas. Accepts scalars or arrays."""
    easting = np.asarray(easting, dtype=np.float64)
    northing = np.asarray(northing, dtype=np.float64)
    a = 6378137.0
    f = 1 / 298.257223563
    e2 = f * (2 - f)
    k0 = 0.9996
    e1 = (1 - np.sqrt(1 - e2)) / (1 + np.sqrt(1 - e2))
    x = easting - 500000.0
    y = northing - 10000000.0 if southern else northing
    lon0 = np.radians(-183 + 6 * zone)

    M = y / k0
    mu = M / (a * (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256))
    phi1 = (mu + (3 * e1 / 2 - 27 * e1**3 / 32) * np.sin(2 * mu)
            + (21 * e1**2 / 16 - 55 * e1**4 / 32) * np.sin(4 * mu)
            + (151 * e1**3 / 96) * np.sin(6 * mu)
            + (1097 * e1**4 / 512) * np.sin(8 * mu))

    N1 = a / np.sqrt(1 - e2 * np.sin(phi1)**2)
    T1 = np.tan(phi1)**2
    C1 = e2 * np.cos(phi1)**2 / (1 - e2)
    R1 = a * (1 - e2) / (1 - e2 * np.sin(phi1)**2)**1.5
    D = x / (N1 * k0)

    lat = phi1 - (N1 * np.tan(phi1) / R1) * (
        D**2 / 2
        - (5 + 3 * T1 + 10 * C1 - 4 * C1**2 - 9 * e2) * D**4 / 24
        + (61 + 90 * T1 + 298 * C1 + 45 * T1**2 - 252 * e2 - 3 * C1**2) * D**6 / 720)
    lon = lon0 + (D - (1 + 2 * T1 + C1) * D**3 / 6
                  + (5 - 2 * C1 + 28 * T1 - 3 * C1**2 + 8 * e2 + 24 * T1**2) * D**5 / 120) / np.cos(phi1)
    return np.degrees(lat), np.degrees(lon)
