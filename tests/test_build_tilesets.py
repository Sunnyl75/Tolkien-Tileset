import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/build_tilesets.py"
SPEC = importlib.util.spec_from_file_location("build_tilesets", SCRIPT)
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class CompositingTests(unittest.TestCase):
    def test_half_transparent_ink_composes_over_parchment(self):
        paper = Image.new("RGBA", (8, 8), (200, 160, 100, 255))
        ink = Image.new("RGBA", (8, 8), (40, 20, 0, 128))
        result = builder.render_tile(ink, paper, 4, False)
        self.assertEqual(result.mode, "RGB")
        self.assertEqual(result.getpixel((2, 2)), (120, 90, 50))

    def test_transparent_field_is_completely_blank(self):
        paper = Image.new("RGBA", (8, 8), (200, 160, 100, 255))
        result = builder.render_tile(paper, paper, 4, True, field=True)
        self.assertEqual(result.tobytes(), bytes(4 * 4 * 4))

    def test_transparent_edges_do_not_gain_black_halos(self):
        ink = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        ink.paste((255, 0, 0, 255), (4, 4, 12, 12))
        paper = Image.new("RGBA", ink.size, (200, 160, 100, 255))
        result = builder.render_tile(ink, paper, 7, True)
        pixels = list(result.get_flattened_data())
        self.assertTrue(any(0 < a < 255 for _, _, _, a in pixels))
        self.assertTrue(all((r, g, b) == (255, 0, 0) for r, g, b, a in pixels if a > 0))


class RepositoryBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.assets = self.root / "working folder/Assets"
        self.assets.mkdir(parents=True)
        Image.new("RGB", (8, 8), (200, 160, 100)).save(self.assets / "terrain-field.png")
        ink = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
        ink.putpixel((4, 4), (40, 20, 0, 255))
        ink.save(self.assets / "terrain-forest.png")
        config = {"size": 4, "source_directory": "working folder/Assets", "field": "terrain-field.png",
                  "tiles": {"terrain-field.png": "terrain-field.png",
                            "terrain-forest.png": "terrain-forest.png"}}
        (self.root / "tilesets.json").write_text(json.dumps(config), encoding="utf-8")

    def test_rebuild_is_deterministic_and_never_changes_masters(self):
        before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in self.assets.glob("*.png")}
        self.assertTrue(builder.build(self.root))
        outputs = {path.relative_to(self.root): path.read_bytes()
                   for pack in builder.PACKS for path in (self.root / pack).rglob("*") if path.is_file()}
        self.assertTrue(builder.build(self.root))
        self.assertTrue(builder.build(self.root, check=True))
        self.assertTrue(all((self.root / name).read_bytes() == data for name, data in outputs.items()))
        after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in self.assets.glob("*.png")}
        self.assertEqual(before, after)

    def test_mismatched_master_canvas_fails_before_writing_outputs(self):
        Image.new("RGBA", (6, 6), (0, 0, 0, 0)).save(self.assets / "terrain-forest.png")
        with self.assertRaisesRegex(ValueError, "master canvas must match Field"):
            builder.build(self.root)
        self.assertFalse((self.root / "Tolkien").exists())

    def test_check_detects_a_modified_output_without_overwriting_it(self):
        builder.build(self.root)
        path = self.root / "Tolkien/pixmaps/terrain-forest.png"
        path.write_bytes(b"edited output")
        self.assertFalse(builder.build(self.root, check=True))
        self.assertEqual(path.read_bytes(), b"edited output")


if __name__ == "__main__":
    unittest.main()
