#!/usr/bin/env python3
"""openEO process graph on CDSE compute — no local raster crunching."""

from __future__ import annotations

import openeo

BASE = "https://openeo.dataspace.copernicus.eu/"


def connect() -> openeo.Connection:
    con = openeo.connect(BASE)
    con.authenticate_oidc()
    return con


def ndvi_composite(con: openeo.Connection, bbox: list[float], start: str, end: str, out: str = "ndvi.tif"):
    """Load Sentinel-2 L2A, compute NDVI, save as GeoTIFF on CDSE storage."""
    s2 = con.load_collection(
        "SENTINEL2_L2A",
        spatial_extent={"west": bbox[0], "south": bbox[1], "east": bbox[2], "north": bbox[3]},
        temporal_extent=[start, end],
        bands=["B04", "B08"],
        max_cloud_cover=20,
    )
    nir = s2.band("B08")
    red = s2.band("B04")
    ndvi = (nir - red) / (nir + red)
    ndvi.save_result(format="GTiff").execute_batch(out)
    return out


def truecolor_png(con: openeo.Connection, bbox: list[float], date: str, out: str = "tc.png"):
    s2 = con.load_collection(
        "SENTINEL2_L2A",
        spatial_extent={"west": bbox[0], "south": bbox[1], "east": bbox[2], "north": bbox[3]},
        temporal_extent=[date, date],
        bands=["B02", "B03", "B04"],
        max_cloud_cover=15,
    ).reduce_dimension(dimension="bands", reducer="sum")
    s2.save_result(format="PNG").execute_batch(out)
    return out


if __name__ == "__main__":
    c = connect()
    buda = [-98.05, 29.85, -97.65, 30.15]
    print(ndvi_composite(c, buda, "2026-09-01", "2026-10-16"))
