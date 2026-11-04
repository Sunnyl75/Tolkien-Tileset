# Tolkien-Tileset
Tolkien-inspired terrain tiles for MUME and MMapper background maps.

## Ready-to-use background tile sets

| Folder | Contents |
| --- | --- |
| [Tolkien/pixmaps](Tolkien/pixmaps) | 512 × 512 opaque PNGs. Each foreground is laid over the approved Field parchment at full master resolution, then reduced. Field is the parchment itself. |
| [Tolkien (transparent)/pixmaps](<Tolkien (transparent)/pixmaps>) | 512 × 512 RGBA PNGs containing foreground ink only. Field is completely transparent, ready for a separate large parchment layer underneath the map. |

In MMapper's **Preferences → Background Map**, select **Separate custom tile pack**
and choose either tile-set folder, or its `pixmaps` subfolder. The transparent
pack supplies alpha artwork; a large parchment underlay is a separate rendering
feature, not an image included in this pack.

Each pack has 27 PNGs: ten approved terrain tiles, all sixteen road configurations,
and a generic `terrain-road.png` alias of `road-none.png`. Exports use MMapper's
plural filenames `terrain-hills.png` and `terrain-mountains.png`. The original
master filenames remain unchanged.

These packs target the current **surface background map**. Underwater, Tunnel,
Cavern and Undefined artwork has not been created. Approved Indoors artwork is
included, although the current bundled background dataset excludes interiors.
Trail masters remain available in Assets; the background renderer does not draw
trail overlays, so they are not included in these background-only exports.

## Approved masters and automatic regeneration

The original, full-resolution approved files remain in
[`working folder/Assets`](<working folder/Assets>). They are never resized,
rewritten or composited in place. [`tilesets.json`](tilesets.json) explicitly maps
approved masters to export filenames; unlisted files do not enter either pack.

The [Build Tolkien tile sets workflow](https://github.com/Sunnyl75/Tolkien-Tileset/actions/workflows/build-tilesets.yml)
automatically runs when masters, the mapping or build code change on `main`.
It can also be started with **Actions → Build Tolkien tile sets → Run workflow**.
It tests the builder, rebuilds both packs and commits changed exports back to
`main`. Generated-only commits do not trigger another build. Builds are
serialized, and a non-fast-forward push fails rather than overwriting newer work.

To replace approved artwork, update its existing master PNG on `main`. To add a
new approved tile, add its master and an entry in `tilesets.json`. The size is
set once in that file, currently **512 pixels square**. Future exports can be
regenerated at another size without altering the masters.

For a local rebuild with Python 3.12:

```sh
python3 -m pip install -r scripts/requirements.txt
python3 -m unittest discover -s tests -v
python3 scripts/build_tilesets.py
python3 scripts/build_tilesets.py --check
python3 scripts/validate_tilesets.py
```

Each tile-set folder contains a deterministic `build-manifest.json` recording
the source and output SHA-256 hashes, master and output sizes, and Pillow version.
The builder composites before reducing and filters transparent exports with
premultiplied alpha to avoid dark edge halos. Validation checks dimensions,
opacity, source hashes and all sixteen transparent road variants' border
connections. Edit the approved masters, not the generated PNGs.
