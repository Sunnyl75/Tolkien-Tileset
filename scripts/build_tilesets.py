#!/usr/bin/env python3
"""Build the four background-only MMapper packs from approved master PNGs."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re

import PIL
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PACKS = {
    "Tolkien": False,
    "Tolkien (transparent)": True,
    "Tolkien - colour": False,
    "Tolkien - colour - transparent": True,
}
COLOUR_PACKS = {"Tolkien - colour", "Tolkien - colour - transparent"}
PNG_NAME = re.compile(r"(?:terrain|road)-[a-z]+\.png\Z")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def png_bytes(image: Image.Image) -> bytes:
    # Do not copy source metadata, timestamps or machine-specific paths.
    image = Image.frombytes(image.mode, image.size, image.tobytes())
    output = io.BytesIO()
    image.save(output, format="PNG", compress_level=9)
    return output.getvalue()


def render_tile(
    foreground: Image.Image,
    parchment: Image.Image,
    size: int,
    transparent: bool,
    field: bool = False,
) -> Image.Image:
    dimensions = (size, size)
    if transparent:
        if field:
            return Image.new("RGBA", dimensions, (0, 0, 0, 0))
        # Filter associated colours and alpha together, avoiding dark halos.
        return foreground.convert("RGBa").resize(
            dimensions, Image.Resampling.LANCZOS
        ).convert("RGBA")
    # Compose at master resolution before reducing, as requested.
    composed = parchment if field else Image.alpha_composite(parchment, foreground)
    return composed.convert("RGB").resize(dimensions, Image.Resampling.LANCZOS)


def prepare(root: Path) -> tuple[dict[str, dict[str, bytes]], dict]:
    config = json.loads((root / "tilesets.json").read_text(encoding="utf-8"))
    size = config["size"]
    if not isinstance(size, int) or size <= 0:
        raise ValueError("size must be a positive number of pixels")
    tiles = config["tiles"]
    field = config["field"]
    if tiles.get("terrain-field.png") != field:
        raise ValueError("The Field output must use the approved parchment")
    if not all(PNG_NAME.fullmatch(name) for name in [*tiles, *tiles.values()]):
        raise ValueError("Tile filenames must be simple terrain-*.png or road-*.png names")
    source_dir = (root / config["source_directory"]).resolve()
    if not source_dir.is_relative_to(root.resolve()):
        raise ValueError("Master directory must be inside the repository")
    def load_sources(directory: Path) -> tuple[dict, dict]:
        if not directory.is_relative_to(root.resolve()):
            raise ValueError("Master directory must be inside the repository")
        images, sources = {}, {}
        for name in sorted(set(tiles.values())):
            # All packs share the exact approved original Field parchment.
            path = (source_dir if name == field else directory) / name
            data = path.read_bytes()
            with Image.open(io.BytesIO(data)) as source:
                if source.format != "PNG" or source.width != source.height or source.width < size:
                    raise ValueError(f"{path}: expected square PNG at least {size} pixels wide")
                if name != field and "A" not in source.getbands():
                    raise ValueError(f"{path}: foreground master must have an alpha channel")
                images[name] = source.convert("RGBA")
            sources[path.relative_to(root).as_posix()] = sha256(data)
        parchment = images[field]
        if parchment.getchannel("A").getextrema() != (255, 255):
            raise ValueError("Field parchment must be fully opaque")
        for name, image in images.items():
            if image.size != parchment.size:
                raise ValueError(f"{name}: master canvas must match Field {parchment.size}")
            if name != field and image.getchannel("A").getextrema()[0] != 0:
                raise ValueError(f"{name}: foreground must have a transparent background")
        return images, sources

    original = load_sources(source_dir)
    colour_dir = (root / config.get("colour_source_directory", config["source_directory"])).resolve()
    colour = original if colour_dir == source_dir else load_sources(colour_dir)
    result = {}
    for pack, transparent in PACKS.items():
        images, sources = colour if pack in COLOUR_PACKS else original
        parchment = images[field]
        cached = {}
        outputs = {}
        for target, source in sorted(tiles.items()):
            if source not in cached:
                cached[source] = png_bytes(render_tile(
                    images[source], parchment, size, transparent, source == field
                ))
            outputs[f"pixmaps/{target}"] = cached[source]
        report = {
            "pack": pack,
            "size": [size, size],
            "background": "transparent" if transparent else "approved Field parchment",
            "master_size": list(parchment.size),
            "pillow_version": PIL.__version__,
            "source_sha256": sources,
            "output_sha256": {name: sha256(data) for name, data in outputs.items()},
        }
        outputs["build-manifest.json"] = (
            json.dumps(report, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        result[pack] = outputs
    return result, config


def build(root: Path = ROOT, check: bool = False) -> bool:
    root = root.resolve()
    packs, config = prepare(root)
    differences = []
    for pack, outputs in packs.items():
        directory = root / pack
        expected = {Path(name).name for name in outputs if name.startswith("pixmaps/")}
        for stale in sorted((directory / "pixmaps").glob("*.png")):
            if stale.name not in expected:
                differences.append(str(stale.relative_to(root)))
                if not check:
                    stale.unlink()
        for name, data in outputs.items():
            path = directory / name
            if path.is_file() and path.read_bytes() == data:
                continue
            differences.append(str(path.relative_to(root)))
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                temporary = path.with_suffix(path.suffix + ".tmp")
                temporary.write_bytes(data)
                temporary.replace(path)
    if check and differences:
        print("Generated files need rebuilding:\n" + "\n".join(differences))
        return False
    verb = "Checked" if check else "Built"
    print(f"{verb} {len(packs)} packs, {len(config['tiles'])} PNGs each, "
          f"{config['size']} x {config['size']} pixels; {len(differences)} files differed.")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify without changing any file")
    arguments = parser.parse_args()
    raise SystemExit(0 if build(check=arguments.check) else 1)
