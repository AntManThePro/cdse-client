#!/usr/bin/env python3
"""STAC search: Sentinel-2 L2A over Buda, last 30 days, cloud <= 20%, sorted newest first."""

from cdse_client import CDSEClient, bbox_from_city


def main() -> None:
    client = CDSEClient()
    items = client.stac_search(
        collections=["sentinel-2-l2a"],
        bbox=bbox_from_city("Buda, TX"),
        datetime="2026-09-16/2026-10-16",
        cloud_cover_lte=20,
        limit=10,
    )
    print(f"{len(items)} scenes")
    for it in items:
        p = it["properties"]
        print(
            f"{it['id'][:40]:40s} {p['datetime'][:10]}  cloud={p.get('eo:cloud_cover'):5.1f}%  "
            f"assets={len(it.get('assets', {}))}"
        )


if __name__ == "__main__":
    main()
