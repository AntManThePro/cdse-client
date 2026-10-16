# cdse-client

Python client for the **Copernicus Data Space Ecosystem (CDSE)** — Europe's free, open gateway to the Sentinel satellite constellation (91 PB online, 120M+ products, free full-archive access).

Built for field ops: hood inspections, roof condition, grease-trap site surveys, pre/post-clean documentation. Sentinel-2 gives 10 m multispectral every 5 days; Sentinel-1 SAR sees through Texas summer clouds; Copernicus DEM 30 m adds terrain context for drainage and runoff.

## What's inside

| Module | What it does |
|---|---|
| `cdse_client.py` | OAuth2 token (Keycloak), STAC search, OData download, S3 listing |
| `raster_extract.py` | Stream Sentinel-2 bands via `/vsis3/` into rasterio — no full download |
| `openeo_graph.py` | Build and run openEO process graphs on CDSE compute |
| `examples/` | Ready-to-run scripts: Buda TX true-color, cloud-filtered archive pull, SAR coherence |

## Quick start

```bash
pip install requests rasterio pystac-client openeo
```

```python
from cdse_client import CDSEClient

client = CDSEClient()                      # reads CDSE_USERNAME / CDSE_PASSWORD from env
client.authenticate()                      # Keycloak password grant, client_id=cdse-public

items = client.stac_search(
    collections=["sentinel-2-l2a"],
    bbox=[-98.05, 29.85, -97.65, 30.15],   # Buda, TX
    datetime="2026-09-16/2026-10-16",
    cloud_cover_lte=20,
    limit=5,
)
for it in items:
    print(it["id"], it["properties"]["eo:cloud_cover"])
```

## Auth

One Keycloak realm covers everything: `identity.dataspace.copernicus.eu/auth/realms/CDSE`.

- **API token:** password grant → bearer token for OData, Sentinel Hub, openEO, STAC.
- **S3 keys:** generate in your CDSE profile. Free quota: 12 TB/month, 20 MB/s. Endpoint: `eodata.dataspace.copernicus.eu` (GSLB routes to CloudFerro or OpenTelekom; pin OTC with the `.ams.` subdomain).

```bash
export CDSE_USERNAME=you@example.com
export CDSE_PASSWORD=yourpassword
```

## Catalogue endpoints (4 doors, same archive)

| Protocol | URL |
|---|---|
| STAC (legacy) | `https://stac.dataspace.copernicus.eu/v1` |
| STAC (new SFEOS/OpenSearch, migration target) | `https://stac.opensearch.dataspace.copernicus.eu/v1` |
| OData | `https://catalogue.dataspace.copernicus.eu/odata/v1/Products` |
| Sentinel Hub Catalog | `https://sh.dataspace.copernicus.eu/catalog/v1/search` |

> New SFEOS endpoint went live 2026-10-16. Old STAC dies **2027-01-12**. Migrate.

## Sentinel-2 band cheat sheet (L2A)

| Band | Name | Res | Use |
|---|---|---|---|
| B02 | Blue | 10 m | True color |
| B03 | Green | 10 m | True color |
| B04 | Red | 10 m | True color, NDVI |
| B08 | NIR | 10 m | NDVI, vegetation |
| B11 | SWIR | 20 m | Built-up / roof materials |
| B12 | SWIR | 20 m | Moisture, bare soil |

NDVI = (B08 - B04) / (B08 + B04). Healthy vegetation ~0.6–0.9. Bare roof / gravel ~0.0–0.2.

## Sentinel-1 for the cloudy days

- Collection: `sentinel-1-grd` (IW GRDH, VV+VH).
- C-band SAR, day/night, through cloud. Revisit ~6 days (A+B).
- Coherence between two passes flags surface change — useful for post-storm roof damage checks.

## openEO

Service base: `https://openeo.dataspace.copernicus.eu/` (API 1.2).

```python
import openeo
con = openeo.connect("https://openeo.dataspace.copernicus.eu/")
con.authenticate_oidc()
# build process graph → con.create_process().execute() or save_result
```

## Sentinel Hub Process API

`POST https://sh.dataspace.copernicus.eu/process/v1` with an evalscript + bbox → rendered PNG or raw bands, up to 2500×2500 px. One HTTP call from "I want a true-color tile of Buda" to image.

## Quotas & gotchas

- STAC burst: 10 req/s; 60 rpm unauthenticated / 240 rpm authenticated (per IP).
- S3 secret key shown once — store it.
- Legacy STAC `catalogue.dataspace.copernicus.eu/stac` deprecated since 2025-11-17.
- Sentinel Hub API paths migrated Mar 2026: `/api/v1/process` → `/process/v1`.

## License

MIT. Data itself is free, full and open (EU free-data policy since 2013).
