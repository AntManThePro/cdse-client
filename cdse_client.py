#!/usr/bin/env python3
"""CDSE client: OAuth2 token, STAC search, OData download, S3 access."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any

import requests

IDENTITY = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
STAC_LEGACY = "https://stac.dataspace.copernicus.eu/v1"
STAC_SFEOS = "https://stac.opensearch.dataspace.copernicus.eu/v1"
ODATA = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
SH_CATALOG = "https://sh.dataspace.copernicus.eu/catalog/v1/search"
SH_PROCESS = "https://sh.dataspace.copernicus.eu/process/v1"
S3_ENDPOINT = "eodata.dataspace.copernicus.eu"
S3_OTC = "eodata.ams.dataspace.copernicus.eu"


@dataclass
class CDSEClient:
    username: str = field(default_factory=lambda: os.environ.get("CDSE_USERNAME", ""))
    password: str = field(default_factory=lambda: os.environ.get("CDSE_PASSWORD", ""))
    client_id: str = "cdse-public"
    token: str | None = None
    token_exp: float = 0.0
    session: requests.Session = field(default_factory=requests.Session, repr=False)

    def authenticate(self) -> str:
        """Password grant → bearer token. Refreshes when < 60s remain."""
        if self.token and time.time() < self.token_exp - 60:
            return self.token
        r = self.session.post(
            IDENTITY,
            data={
                "client_id": self.client_id,
                "username": self.username,
                "password": self.password,
                "grant_type": "password",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        r.raise_for_status()
        body = r.json()
        self.token = body["access_token"]
        self.token_exp = time.time() + body.get("expires_in", 300)
        return self.token

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.authenticate()}"}

    def stac_search(
        self,
        collections: list[str],
        bbox: list[float],
        datetime: str,
        cloud_cover_lte: float | None = None,
        limit: int = 10,
        base: str = STAC_SFEOS,
        sort_desc: bool = True,
    ) -> list[dict[str, Any]]:
        """POST STAC item search. cloud_cover_lte filters eo:cloud_cover."""
        payload: dict[str, Any] = {
            "collections": collections,
            "bbox": bbox,
            "datetime": datetime,
            "limit": limit,
        }
        if cloud_cover_lte is not None:
            payload["filter"] = {
                "op": "<=",
                "args": [{"property": "eo:cloud_cover"}, cloud_cover_lte],
            }
            payload["filter-lang"] = "cql2-json"
        if sort_desc:
            payload["sortby"] = [{"field": "properties.datetime", "direction": "desc"}]
        r = self.session.post(f"{base}/search", json=payload, headers=self._headers(), timeout=60)
        r.raise_for_status()
        return r.json().get("features", [])

    def odata_search(self, collection: str, top: int = 100, **filters: str) -> list[dict[str, Any]]:
        """OData $filter query. Pass extra filters as keyword args."""
        parts = [f"Collection/Name eq '{collection}'"]
        for k, v in filters.items():
            parts.append(f"{k} {v}")
        q = " and ".join(parts)
        r = self.session.get(
            ODATA,
            params={"$filter": q, "$top": top, "$orderby": "ContentDate/Start desc"},
            headers=self._headers(),
            timeout=60,
        )
        r.raise_for_status()
        return r.json().get("value", [])

    def download_product(self, product_id: str, dest: str) -> str:
        """Stream a product zip via OData $value."""
        url = f"{ODATA}({product_id})/$value"
        with self.session.get(url, headers=self._headers(), stream=True, timeout=600) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(1024 * 256):
                    f.write(chunk)
        return dest

    def sh_process_truecolor(
        self,
        bbox: list[float],
        start: str,
        end: str,
        width: int = 1024,
        height: int = 1024,
        collection: str = "S2L2A",
    ) -> bytes:
        """Sentinel Hub Process API: true-color PNG for bbox/time range."""
        body = {
            "input": {
                "bounds": {"bbox": bbox, "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"}},
                "data": [{
                    "type": collection,
                    "dataFilter": {
                        "timeRange": {"from": f"{start}T00:00:00Z", "to": f"{end}T23:59:59Z"},
                        "mosaickingOrder": "leastCC",
                    },
                }],
            },
            "output": {
                "width": width,
                "height": height,
                "responses": [{"identifier": "default", "format": {"type": "image/png"}}],
            },
            "evalscript": "function evaluatePixel(sample) { return [2.5*sample.B04, 2.5*sample.B03, 2.5*sample.B02]; }",
        }
        r = self.session.post(SH_PROCESS, headers=self._headers(), json=body, timeout=120)
        r.raise_for_status()
        return r.content


def bbox_from_city(name: str) -> list[float]:
    """Tiny geocoder fallback — extend with geopy for production."""
    table = {
        "buda, tx": [-98.05, 29.85, -97.65, 30.15],
        "austin, tx": [-98.05, 30.15, -97.55, 30.55],
        "houston, tx": [-95.85, 29.55, -95.05, 30.15],
        "dallas, tx": [-97.05, 32.65, -96.55, 33.15],
    }
    key = name.strip().lower()
    if key not in table:
        raise KeyError(f"unknown city '{name}' — add to table or pass a bbox directly")
    return table[key]
