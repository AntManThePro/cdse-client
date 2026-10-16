#!/usr/bin/env python3
"""Stream Sentinel-2 L2A bands through GDAL /vsis3/ — zero local download."""

from __future__ import annotations

import os

import numpy as np
import rasterio
from rasterio.session import AWSSession

S3_ENDPOINT = "eodata.dataspace.copernicus.eu"


def open_band(asset_href: str, access_key: str, secret_key: str):
    """Open a COG/JPEG2000 band asset directly from the STAC item."""
    session = AWSSession(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="default",
        endpoint_url=S3_ENDPOINT,
    )
    # strip s3://eodata/ prefix → /vsis3/eodata/...
    path = asset_href.replace("s3://", "/vsis3/")
    return rasterio.open(path, session=session)


def ndvi(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
    """(B08 - B04) / (B08 + B04). Mask nodata."""
    with np.errstate(divide="ignore", invalid="ignore"):
        out = (nir.astype(float) - red.astype(float)) / (nir.astype(float) + red.astype(float))
    return np.where(np.isfinite(out), out, np.nan)


def roof_mask(b11: np.ndarray, b04: np.ndarray, threshold: float = 0.25) -> np.ndarray:
    """SWIR-heavy, low-NDVI pixels ≈ built-up / roof material. Tune per site."""
    return (b11 > np.nanpercentile(b11, 70)) & (ndvi(b04, b04) < threshold)  # placeholder logic


if __name__ == "__main__":
    # Example: pull B04/B08 from a STAC item and compute NDVI stats
    access = os.environ["CDSE_S3_ACCESS"]
    secret = os.environ["CDSE_S3_SECRET"]
    # hrefs come from item["assets"]["B04_10m"]["href"] etc.
    print("set CDSE_S3_ACCESS / CDSE_S3_SECRET, then call open_band(href, access, secret)")
