#!/usr/bin/env python3
"""Pull a true-color Sentinel-2 PNG of Buda, TX via Sentinel Hub Process API."""

import os
from pathlib import Path

from cdse_client import CDSEClient, bbox_from_city

OUT = Path("buda_truecolor.png")


def main() -> None:
    client = CDSEClient()
    png = client.sh_process_truecolor(
        bbox=bbox_from_city("Buda, TX"),
        start="2026-10-01",
        end="2026-10-16",
        width=1024,
        height=1024,
    )
    OUT.write_bytes(png)
    print(f"wrote {OUT} ({len(png):,} bytes)")


if __name__ == "__main__":
    main()
