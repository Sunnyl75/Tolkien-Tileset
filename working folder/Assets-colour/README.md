# Colour overlay masters

- `terrain-water.png`: approved muted indigo-blue water overlay, with the first blue version's soft transitions and more purposeful ink-density variation.
- `terrain-rapids.png`: approved matching blue water, current strokes and spray, with all eight boulders retained in dark brown.
- `terrain-shallow.png`: approved muted green upright reeds with indigo-blue horizontal water strokes, dots and dashes.
- `terrain-forest.png`: approved muted green foliage outlines with the original dark brown trunks and transparent crown interiors.
- `terrain-brush.png`: approved dark brown brush branches with enlarged, hollow muted-green foliage circles.
- `terrain-hill.png`, `terrain-mountain.png`, `terrain-city.png`, `terrain-indoors.png`: unchanged copies of the approved brown-ink overlays in `../Assets/`.
- `road-*.png`: all 16 approved road overlays, copied unchanged from `../Assets/`.
- `trail-*.png`: all 16 approved track/trail overlays, copied unchanged from `../Assets/`.

All 41 PNGs are full-resolution 1254 × 1254 transparent foreground masters. Shared artwork retains exactly the original colours and PNG bytes. The copies reference the same Git blob objects as their originals.

This folder supplies the masters for `Tolkien - colour` and `Tolkien - colour - transparent`. The build mapping in `../../tilesets.json` exports them at 512 pixels square. All packs share the original Field parchment from `../Assets/`; the transparent pack has a blank Field. Trail masters remain here for future use; the background-only exports contain terrain and road files.
