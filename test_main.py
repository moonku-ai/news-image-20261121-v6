"""Tests for news-image-20261121 v6 — 'ONE WORLD, ONE DAY' world-atlas infographic.

Pure stdlib. Run: python3 -m pytest test_main.py -q  (or python3 test_main.py)
"""
import os
import struct
import subprocess
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import main


def _run_main(outdir):
    env = dict(os.environ)
    env["MAKEFUN_OUTPUT_DIR"] = outdir
    r = subprocess.run([sys.executable, "main.py"], cwd=os.path.dirname(os.path.abspath(__file__)),
                       env=env, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, f"main.py failed: {r.stdout}\n{r.stderr}"
    return os.path.join(outdir, "entry.png")


def test_png_valid_and_size(tmp_path):
    """PNG signature, IHDR 1024x1024, chunk CRCs valid, <= 1 MiB."""
    p = _run_main(str(tmp_path))
    data = open(p, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "bad PNG signature"
    assert len(data) <= 1048576, f"too big: {len(data)} bytes"
    pos = 8
    saw_ihdr = saw_idat = saw_iend = False
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        ctype = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        (crc,) = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])
        assert zlib.crc32(ctype + chunk) & 0xFFFFFFFF == crc, f"bad CRC on {ctype}"
        if ctype == b"IHDR":
            w, h, depth, ctype_b = struct.unpack(">IIBB", chunk[:10])
            assert (w, h) == (1024, 1024), f"size {w}x{h}"
            assert depth == 8 and ctype_b == 2, "expect 8-bit RGB"
            saw_ihdr = True
        if ctype == b"IDAT":
            saw_idat = True
        if ctype == b"IEND":
            saw_iend = True
        pos += 12 + length
    assert saw_ihdr and saw_idat and saw_iend


def test_deterministic(tmp_path):
    """Two runs produce byte-identical output."""
    a = _run_main(str(tmp_path / "a"))
    b = _run_main(str(tmp_path / "b"))
    assert open(a, "rb").read() == open(b, "rb").read()


def test_font_covers_copy():
    """Every character used in the visible copy exists in the font."""
    for line in main.ALL_COPY_LINES:
        for ch in line:
            assert ch in main.FONT, f"font missing char {ch!r} (line {line!r})"


def test_headlines_fit_cells():
    """Every legend headline fits its cell width at scale 3 (no overflow)."""
    for story in main.STORIES:
        w = main.text_width(story["headline"], 3)
        assert w <= main.LEGEND_TEXT_W, f"headline too wide: {story['headline']} ({w}px)"


def test_stats_fit_cells():
    """Every big stat fits its cell width at scale 5."""
    for story in main.STORIES:
        w = main.text_width(story["stat"], 5)
        assert w <= main.LEGEND_TEXT_W, f"stat too wide: {story['stat']} ({w}px)"


def test_facts_fit_two_lines():
    """Every fact wraps to at most 2 lines at scale 2 within cell width."""
    for story in main.STORIES:
        lines = main.wrap_text(story["fact"], 2, main.LEGEND_TEXT_W)
        assert len(lines) <= 2, f"fact wraps to {len(lines)} lines: {story['fact']}"


def test_map_land_sea():
    """Point-in-polygon sanity: known land points are land, ocean points are sea."""
    land = [(0, 51), (-100, 40), (-60, -15), (20, 5), (135, -25), (30, 55), (100, 60)]
    sea = [(0, 0), (-150, 0), (-30, -30), (90, -40), (-170, 70)]
    for lon, lat in land:
        assert main.is_land(lon, lat), f"expected land at {(lon, lat)}"
    for lon, lat in sea:
        assert not main.is_land(lon, lat), f"expected sea at {(lon, lat)}"


def test_pins_inside_map_field():
    """Every story pin projects inside the map field rectangle."""
    for story in main.STORIES:
        x, y = main.lonlat_to_xy(story["lon"], story["lat"])
        assert main.MAP_X0 <= x <= main.MAP_X1, f"pin x out of field: {story['headline']}"
        assert main.MAP_Y0 <= y <= main.MAP_Y1, f"pin y out of field: {story['headline']}"


def test_pin_chips_do_not_overlap():
    """Numbered pin chips (with offsets) must not overlap each other."""
    chips = [main.pin_chip_xy(s) for s in main.STORIES]
    for i in range(len(chips)):
        for j in range(i + 1, len(chips)):
            dx = chips[i][0] - chips[j][0]
            dy = chips[i][1] - chips[j][1]
            assert dx * dx + dy * dy >= (2 * main.PIN_R + 4) ** 2, \
                f"chips {i + 1} and {j + 1} overlap"


def test_eight_stories_eight_regions():
    """Breadth: 8 stories across distinct regions/fields."""
    assert len(main.STORIES) == 8
    regions = {s["region"] for s in main.STORIES}
    assert len(regions) >= 6, f"only {len(regions)} regions"


def test_date_present():
    """The image names the exact day it sums up."""
    assert "21 NOVEMBER 2026" in main.MASTHEAD_DATE
    assert "SATURDAY" in main.MASTHEAD_DATE


if __name__ == "__main__":
    import traceback
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    failed = 0
    import tempfile
    for t in tests:
        try:
            if "tmp_path" in t.__code__.co_varnames:
                with tempfile.TemporaryDirectory() as d:
                    class P:
                        def __truediv__(self, x):
                            return os.path.join(str(d), x)
                    t(P())
            else:
                t()
            print(f"PASS {t.__name__}")
        except Exception:
            failed += 1
            print(f"FAIL {t.__name__}")
            traceback.print_exc()
    print(f"{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
