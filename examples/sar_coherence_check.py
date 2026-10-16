#!/usr/bin/env python3
"""Sentinel-1 GRD search for a date window — the through-cloud option."""

from cdse_client import CDSEClient, bbox_from_city


def main() -> None:
    client = CDSEClient()
    items = client.stac_search(
        collections=["sentinel-1-grd"],
        bbox=bbox_from_city("Buda, TX"),
        datetime="2026-10-01/2026-10-16",
        limit=10,
    )
    print(f"{len(items)} SAR scenes")
    for it in items:
        p = it["properties"]
        print(f"{it['id'][:48]:48s} {p['datetime'][:16]}  pol={p.get('sar:polarizations')}")


if __name__ == "__main__":
    main()
