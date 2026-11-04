#!/usr/bin/env python3
"""Check output dimensions, opacity, provenance and seamless road connectors."""

import hashlib
import json

from PIL import Image

from build_tilesets import PACKS, ROOT


def validate() -> None:
    config = json.loads((ROOT / "tilesets.json").read_text(encoding="utf-8"))
    expected = set(config["tiles"])
    dimensions = (config["size"], config["size"])
    roads = {}
    for pack, transparent in PACKS.items():
        folder = ROOT / pack
        report = json.loads((folder / "build-manifest.json").read_text(encoding="utf-8"))
        actual = {path.name for path in (folder / "pixmaps").glob("*.png")}
        assert actual == expected, f"{pack}: missing or extra PNGs"
        for relative, digest in report["source_sha256"].items():
            assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest, relative
        for relative, digest in report["output_sha256"].items():
            path = folder / relative
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, str(path)
            with Image.open(path) as image:
                assert image.format == "PNG" and image.size == dimensions, str(path)
                if transparent:
                    assert image.mode == "RGBA", str(path)
                    alpha = image.getchannel("A")
                    if path.name == "terrain-field.png":
                        assert image.tobytes() == bytes(dimensions[0] * dimensions[1] * 4), str(path)
                    else:
                        low, high = alpha.getextrema()
                        assert low == 0 and high > 0, str(path)
                    if path.name.startswith("road-"):
                        roads[path.stem.removeprefix("road-")] = image.copy()
                else:
                    assert image.mode == "RGB", f"{path}: parchment pack must be opaque"
        assert (folder / "pixmaps/terrain-road.png").read_bytes() == (
            folder / "pixmaps/road-none.png"
        ).read_bytes(), f"{pack}: generic road alias differs"

    required = {"none", "n", "e", "s", "w", "ns", "ew", "ne", "es", "sw", "nw",
                "nes", "new", "esw", "nsw", "all"}
    assert set(roads) == required, "Expected all 16 road configurations"
    size = dimensions[0]
    edges = {
        "n": (0, 0, size, 1), "s": (0, size - 1, size, size),
        "w": (0, 0, 1, size), "e": (size - 1, 0, size, size),
    }
    profiles = {}
    connectors = 0
    for suffix, image in roads.items():
        directions = "nesw" if suffix == "all" else "" if suffix == "none" else suffix
        for direction, box in edges.items():
            edge = image.crop(box)
            if direction not in directions:
                assert edge.getchannel("A").getbbox() is None, f"road-{suffix}: unexpected {direction} exit"
                continue
            assert edge.getchannel("A").getbbox(), f"road-{suffix}: missing {direction} connection"
            axis = "vertical" if direction in "ns" else "horizontal"
            profile = edge.tobytes()
            if axis in profiles:
                assert profile == profiles[axis], f"road-{suffix}: {direction} border mismatch"
            else:
                profiles[axis] = profile
            connectors += 1
    print(f"Validated both {dimensions[0]} px packs and {connectors} matching road edge profiles.")


if __name__ == "__main__":
    validate()
