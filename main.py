#!/usr/bin/env python3
"""news-image-20261121 v6 — 'ONE WORLD, ONE DAY'

A world-atlas front page summing up Saturday 21 November 2026's news:
a dot-matrix world map with 8 numbered pins marking WHERE each story
happened, plus a numbered legend (headline + big stat + fact line).

Pure Python standard library only. Deterministic: same bytes every run.
Renders 1024x1024 PNG to $MAKEFUN_OUTPUT_DIR/entry.png (default ./out).
"""
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (245, 239, 227)   # parchment
INK = (20, 32, 43)        # near-black navy (masthead band, headlines)
MAP_NAVY = (14, 42, 71)   # atlas field
MAP_DOT = (232, 220, 195) # parchment dots on the map
MAP_GRID = (27, 58, 92)   # graticule lines
MAP_GRID_EQ = (36, 72, 107)
OCEAN_LABEL = (74, 106, 138)
RED = (200, 16, 46)       # breaking red
GOLD = (201, 162, 39)
TEAL = (14, 124, 123)     # good-news stats
GREY = (91, 103, 112)     # fact text
RULE = (216, 205, 180)    # hairlines on paper
WHITE = (255, 255, 255)
CHIP_BG = (239, 231, 211) # pictogram disc

# ---------------------------------------------------------------- masthead
MASTHEAD_TITLE = "ONE WORLD, ONE DAY"
MASTHEAD_DATE = "SATURDAY 21 NOVEMBER 2026"

# ---------------------------------------------------------------- map field
MAP_X0, MAP_X1, MAP_Y0, MAP_Y1 = 24, 1000, 96, 500
LON_MIN, LON_MAX = -170.0, 190.0
LAT_MAX, LAT_MIN = 83.0, -58.0
DOT_STEP = 8
PIN_R = 14

# ---------------------------------------------------------------- legend
LEGEND_Y0 = 512
LEGEND_ROW_H = 116
LEGEND_COLS = [24, 524]          # left x of each column
LEGEND_COL_W = 476
LEGEND_TEXT_X = 84               # text starts this far into a cell
LEGEND_TEXT_W = 384              # max text width in a cell

# ---------------------------------------------------------------- stories
# headline <= 23 chars at scale 3; stat short + punchy; fact <= ~78 chars
# (wraps to at most 2 lines at scale 2). lon/lat = where it happened.
STORIES = [
    {"n": 1, "headline": "FBI DATABASE HACKED", "stat": "2ND BREACH",
     "stat_color": RED,
     "fact": "NCIC crime database probed; USDA payments hit; Trump confirms",
     "region": "USA", "lon": -77.0, "lat": 38.9, "dx": -36, "dy": -32},
    {"n": 2, "headline": "ICJ: GENOCIDE VERDICT", "stat": "FIRST EVER",
     "stat_color": INK,
     "fact": "9-6 ruling; 10,000 killed in 2017; reparations ordered",
     "region": "Netherlands", "lon": 4.3, "lat": 52.1, "dx": 14, "dy": -36},
    {"n": 3, "headline": "AI MARKET MELTDOWN", "stat": "-5.28%",
     "stat_color": RED,
     "fact": "Worst week since Mar 2020; S&P -3.7%, Dow -950, Nvidia -14%",
     "region": "USA", "lon": -74.0, "lat": 40.7, "dx": 34, "dy": 28},
    {"n": 4, "headline": "KYIV UNDER FIRE", "stat": "400+ DRONES",
     "stat_color": RED,
     "fact": "110+ missiles, 3 land in Poland; 8 killed; biggest of November",
     "region": "Ukraine", "lon": 30.5, "lat": 50.4, "dx": 26, "dy": -30},
    {"n": 5, "headline": "CANCER BREAKTHROUGH", "stat": "1 IN 12",
     "stat_color": TEAL,
     "fact": "Tumours undetectable in 8.2% on daraxonrasib; 90.2% stop growing",
     "region": "Spain", "lon": 2.2, "lat": 41.4, "dx": -34, "dy": 32},
    {"n": 6, "headline": "CHAPO ISIDRO CAUGHT", "stat": "$5M REWARD",
     "stat_color": TEAL,
     "fact": "FBI Top 10 fugitive seized in Sinaloa with US help",
     "region": "Mexico", "lon": -108.5, "lat": 25.6, "dx": -38, "dy": -30},
    {"n": 7, "headline": "KILLER-ROBOT RULES", "stat": "128 NATIONS",
     "stat_color": INK,
     "fact": "UN to draft rules by 2028; no treaty yet - Russia objects",
     "region": "Switzerland", "lon": 6.1, "lat": 46.2, "dx": 30, "dy": 32},
    {"n": 8, "headline": "ANTHROPIC IPO SOARS", "stat": "+17% DAY ONE",
     "stat_color": TEAL,
     "fact": "$81.3bn, the largest IPO ever; $1.75tn as AI stocks crashed",
     "region": "USA", "lon": -122.4, "lat": 37.8, "dx": -36, "dy": 26},
]

FOOTER_LINES = [
    "ALSO TODAY: Shenzhen peace declaration - COP31 deadlock past deadline - Bayer $7.25bn Roundup deal",
    "Houthi missiles at Riyadh intercepted - Gen Z protests in 25 countries - Peru 6.9 quake",
    "Sources: Reuters - AP - CNN - BBC - AFP - UN News - ICJ - ISW",
]

MAP_LABEL = "WHERE THE NEWS HAPPENED"
OCEAN_LABELS = [
    ("PACIFIC OCEAN", -150.0, -5.0),
    ("ATLANTIC OCEAN", -28.0, -22.0),
    ("INDIAN OCEAN", 60.0, -35.0),
]

ALL_COPY_LINES = (
    [MASTHEAD_TITLE, MASTHEAD_DATE, MAP_LABEL, "N"]
    + [t for t, _, _ in OCEAN_LABELS]
    + [s["headline"] for s in STORIES]
    + [s["stat"] for s in STORIES]
    + [s["fact"] for s in STORIES]
    + FOOTER_LINES
)

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 cells, '#' = ink. Written from scratch here.
def _g(*rows):
    return rows

FONT = {
    "A": _g("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": _g("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": _g("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": _g("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": _g("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": _g("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": _g("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": _g("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": _g("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": _g("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": _g("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": _g("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": _g("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": _g("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": _g("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": _g("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": _g("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": _g("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": _g("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": _g("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": _g("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": _g("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": _g("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": _g("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": _g("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": _g("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "a": _g("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    "b": _g("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    "c": _g("00000", "00000", "01110", "10000", "10000", "10001", "01110"),
    "d": _g("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    "e": _g("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    "f": _g("00110", "01000", "01000", "11110", "01000", "01000", "01000"),
    "g": _g("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    "h": _g("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    "i": _g("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    "j": _g("00010", "00000", "00110", "00010", "00010", "10010", "01100"),
    "k": _g("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    "l": _g("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "m": _g("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    "n": _g("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    "o": _g("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    "p": _g("00000", "11110", "10001", "10001", "11110", "10000", "10000"),
    "q": _g("00000", "00000", "01111", "10001", "10001", "01111", "00001"),
    "r": _g("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    "s": _g("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    "t": _g("00100", "00100", "01110", "00100", "00100", "00100", "00110"),
    "u": _g("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    "v": _g("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    "w": _g("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    "x": _g("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    "y": _g("00000", "10001", "10001", "10001", "01111", "00001", "01110"),
    "z": _g("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    "0": _g("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": _g("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": _g("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": _g("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": _g("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": _g("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": _g("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": _g("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": _g("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": _g("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": _g("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": _g("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": _g("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": _g("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": _g("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": _g("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": _g("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": _g("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': _g("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "-": _g("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "(": _g("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": _g("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": _g("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": _g("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": _g("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "+": _g("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": _g("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "&": _g("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "#": _g("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "*": _g("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
    "_": _g("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "@": _g("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    "[": _g("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    "]": _g("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    "<": _g("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": _g("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
}

# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg) * (w * h)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def fill_rect(self, x0, y0, x1, y1, c):
        x0 = max(0, x0); y0 = max(0, y0)
        x1 = min(self.w - 1, x1); y1 = min(self.h - 1, y1)
        for y in range(y0, y1 + 1):
            i = (y * self.w + x0) * 3
            self.px[i:(y * self.w + x1 + 1) * 3] = bytes(c) * (x1 - x0 + 1)

    def hline(self, x0, x1, y, c):
        if not (0 <= y < self.h):
            return
        x0 = max(0, x0); x1 = min(self.w - 1, x1)
        if x1 < x0:
            return
        i = (y * self.w + x0) * 3
        self.px[i:(y * self.w + x1 + 1) * 3] = bytes(c) * (x1 - x0 + 1)

    def vline(self, x, y0, y1, c):
        if not (0 <= x < self.w):
            return
        for y in range(max(0, y0), min(self.h - 1, y1) + 1):
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def line(self, x0, y0, x1, y1, c):
        dx = abs(x1 - x0); dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy; x0 += sx
            if e2 <= dx:
                err += dx; y0 += sy

    def circle(self, cx, cy, r, c, fill=True):
        if fill:
            for y in range(cy - r, cy + r + 1):
                dx = int((r * r - (y - cy) ** 2) ** 0.5) if abs(y - cy) <= r else 0
                self.hline(cx - dx, cx + dx, y, c)
        else:
            x, y, d = 0, r, 1 - r
            while x <= y:
                for px, py in ((cx + x, cy + y), (cx - x, cy + y), (cx + x, cy - y),
                               (cx - x, cy - y), (cx + y, cy + x), (cx - y, cy + x),
                               (cx + y, cy - x), (cx - y, cy - x)):
                    self.set(px, py, c)
                if d < 0:
                    d += 2 * x + 3
                else:
                    d += 2 * (x - y) + 5
                    y -= 1
                x += 1

    def polyline(self, pts, c, close=False):
        for a, b in zip(pts, pts[1:]):
            self.line(a[0], a[1], b[0], b[1], c)
        if close and len(pts) > 2:
            self.line(pts[-1][0], pts[-1][1], pts[0][0], pts[0][1], c)

    def polyfill(self, pts, c):
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h - 1, max(ys)) + 1):
            xs = []
            for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(int(x0 + (y - y0) * (x1 - x0) / (y1 - y0)))
            xs.sort()
            for a, b in zip(xs[::2], xs[1::2]):
                self.hline(a, b, y, c)


# ---------------------------------------------------------------- text
def text_width(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(cv, x, y, s, scale, color):
    cx = x
    for ch in s:
        glyph = FONT.get(ch)
        if glyph is None:
            raise KeyError(f"font missing char {ch!r}")
        for r, row in enumerate(glyph):
            for col, bit in enumerate(row):
                if bit == "1":
                    cv.fill_rect(cx + col * scale, y + r * scale,
                                 cx + col * scale + scale - 1,
                                 y + r * scale + scale - 1, color)
        cx += 6 * scale
    return cx


def draw_text_right(cv, x_right, y, s, scale, color):
    return draw_text(cv, x_right - text_width(s, scale), y, s, scale, color)


def wrap_text(s, scale, max_w):
    words = s.split(" ")
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- PNG
def _chunk(ctype, data):
    return (struct.pack(">I", len(data)) + ctype + data +
            struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF))


def encode_png(cv):
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * stride:(y + 1) * stride]
    idat = zlib.compress(bytes(raw), 9)
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) +
            _chunk(b"IDAT", idat) + _chunk(b"IEND", b""))


# ---------------------------------------------------------------- world map
# Coarse continent outlines (lon, lat), equirectangular. Stylised on purpose.
NORTH_AMERICA = [(-168, 66), (-165, 60), (-158, 58), (-152, 60), (-140, 60),
                 (-135, 58), (-130, 54), (-125, 49), (-124, 42), (-120, 34),
                 (-114, 29), (-110, 24), (-105, 20), (-97, 16), (-94, 17),
                 (-90, 14), (-86, 12), (-83, 9), (-79, 9), (-83, 11),
                 (-86, 15), (-88, 17), (-90, 21), (-97, 26), (-93, 30),
                 (-89, 30), (-84, 30), (-81, 25), (-80, 32), (-76, 35),
                 (-74, 40), (-70, 42), (-66, 45), (-60, 47), (-55, 47),
                 (-60, 52), (-65, 58), (-68, 58), (-75, 62), (-78, 62),
                 (-85, 66), (-92, 66), (-95, 69), (-110, 68), (-125, 70),
                 (-140, 70), (-155, 71), (-165, 68)]
GREENLAND = [(-58, 64), (-52, 60), (-43, 60), (-40, 64), (-32, 68),
             (-22, 70), (-20, 74), (-25, 78), (-35, 80), (-50, 80),
             (-58, 76), (-60, 70)]
SOUTH_AMERICA = [(-79, 9), (-77, 4), (-80, -3), (-81, -6), (-77, -12),
                 (-72, -18), (-70, -23), (-70, -30), (-73, -37), (-73, -44),
                 (-74, -50), (-70, -54), (-66, -55), (-65, -45), (-62, -40),
                 (-58, -35), (-52, -32), (-48, -28), (-41, -23), (-39, -17),
                 (-35, -9), (-35, -6), (-40, -3), (-44, -2), (-50, 0),
                 (-52, 4), (-55, 6), (-60, 8), (-68, 11), (-72, 12), (-77, 8)]
AFRICA = [(-17, 15), (-17, 21), (-15, 27), (-10, 31), (-5, 35), (0, 36),
          (10, 37), (11, 34), (20, 32), (30, 31), (32, 31), (35, 28),
          (37, 22), (39, 18), (43, 12), (48, 11), (51, 12), (46, 5),
          (41, 0), (40, -5), (40, -10), (36, -18), (35, -22), (33, -26),
          (28, -33), (20, -35), (17, -32), (15, -27), (13, -18), (12, -10),
          (9, -1), (9, 4), (6, 4), (-8, 5), (-13, 8), (-17, 12)]
EURASIA = [(-10, 36), (-9, 43), (-2, 44), (-1, 46), (-4, 48), (0, 50),
           (2, 51), (5, 53), (8, 57), (5, 60), (5, 62), (10, 64),
           (13, 66), (18, 69), (25, 71), (30, 70), (35, 68), (40, 68),
           (45, 68), (50, 69), (55, 68), (60, 69), (68, 73), (75, 74),
           (80, 73), (90, 75), (100, 76), (110, 74), (120, 73), (130, 72),
           (140, 72), (150, 70), (160, 70), (170, 67), (178, 65),
           (170, 60), (162, 60), (158, 53), (155, 59), (142, 50),
           (140, 45), (135, 43), (130, 42), (127, 40), (122, 38),
           (120, 34), (122, 30), (118, 25), (110, 20), (108, 18),
           (105, 10), (103, 8), (100, 7), (98, 10), (97, 15), (94, 17),
           (92, 21), (89, 22), (86, 20), (80, 15), (77, 8), (76, 10),
           (73, 16), (70, 20), (66, 25), (62, 25), (58, 25), (54, 26),
           (51, 28), (48, 29), (44, 29), (43, 26), (39, 21), (35, 18),
           (35, 15), (39, 12), (43, 12), (45, 14), (48, 16), (52, 16),
           (55, 17), (58, 20), (58, 23), (56, 26), (52, 26), (50, 28),
           (48, 30), (44, 30), (40, 31), (36, 36), (33, 36), (30, 36),
           (27, 37), (23, 37), (22, 39), (19, 42), (15, 44), (12, 45),
           (8, 44), (6, 43), (3, 43), (0, 40), (-2, 37), (-6, 36), (-9, 37)]
AUSTRALIA = [(113, -22), (114, -30), (115, -33), (118, -35), (124, -33),
             (129, -32), (132, -32), (135, -35), (138, -35), (140, -38),
             (145, -38), (150, -37), (153, -32), (153, -27), (150, -22),
             (146, -19), (142, -15), (142, -11), (137, -12), (135, -15),
             (132, -12), (130, -13), (126, -14), (122, -17), (118, -20)]
UK = [(-5, 50), (-3, 53), (-5, 56), (-2, 58), (0, 53), (1, 51)]
JAPAN = [(130, 31), (133, 34), (137, 35), (140, 38), (141, 41), (143, 43),
         (141, 45), (140, 40), (139, 37), (136, 34), (132, 33)]
SUMATRA = [(95, 5), (98, 2), (100, 0), (103, -2), (105, -4), (106, -6),
           (104, -5), (101, -1), (97, 3)]
BORNEO = [(109, 1), (111, 3), (114, 4), (117, 2), (118, -1), (117, -4),
          (114, -4), (111, -3), (109, -1)]
NEW_GUINEA = [(131, -1), (134, -2), (137, -2), (141, -3), (145, -5),
              (147, -7), (146, -9), (142, -8), (139, -6), (136, -4), (132, -2)]
MADAGASCAR = [(44, -16), (47, -15), (50, -16), (49, -20), (46, -24),
              (44, -25), (43, -21)]
NEW_ZEALAND = [(167, -45), (170, -42), (173, -40), (176, -38), (178, -38),
               (175, -41), (172, -43), (168, -46)]
SRI_LANKA = [(80, 6), (81, 8), (80, 9), (79, 8)]
TAIWAN = [(120, 22), (121, 24), (121, 25), (120, 23)]
PHILIPPINES = [(120, 14), (121, 16), (122, 18), (122, 14), (121, 11),
               (123, 10), (122, 13)]

LAND = [NORTH_AMERICA, GREENLAND, SOUTH_AMERICA, AFRICA, EURASIA,
        AUSTRALIA, UK, JAPAN, SUMATRA, BORNEO, NEW_GUINEA, MADAGASCAR,
        NEW_ZEALAND, SRI_LANKA, TAIWAN, PHILIPPINES]


def _point_in_poly(lon, lat, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > lat) != (y1 > lat):
            xin = x0 + (lat - y0) * (x1 - x0) / (y1 - y0)
            if lon < xin:
                inside = not inside
    return inside


def is_land(lon, lat):
    return any(_point_in_poly(lon, lat, p) for p in LAND)


def lonlat_to_xy(lon, lat):
    x = MAP_X0 + (lon - LON_MIN) / (LON_MAX - LON_MIN) * (MAP_X1 - MAP_X0)
    y = MAP_Y0 + (LAT_MAX - lat) / (LAT_MAX - LAT_MIN) * (MAP_Y1 - MAP_Y0)
    return int(round(x)), int(round(y))


def xy_to_lonlat(x, y):
    lon = LON_MIN + (x - MAP_X0) / (MAP_X1 - MAP_X0) * (LON_MAX - LON_MIN)
    lat = LAT_MAX - (y - MAP_Y0) / (MAP_Y1 - MAP_Y0) * (LAT_MAX - LAT_MIN)
    return lon, lat


def pin_chip_xy(story):
    px, py = lonlat_to_xy(story["lon"], story["lat"])
    return px + story["dx"], py + story["dy"]

# ---------------------------------------------------------------- pictograms
# Each draws a large icon centred on (cx, cy) inside a ~48px box.
def pic_lock(cv, cx, cy, c):
    cv.circle(cx, cy - 2, 10, c, fill=False)
    cv.fill_rect(cx - 16, cy - 4, cx + 16, cy + 20, c)
    cv.fill_rect(cx - 4, cy + 4, cx + 4, cy + 12, PAPER)


def pic_scales(cv, cx, cy, c):
    cv.vline(cx, cy - 22, cy + 20, c)
    cv.hline(cx - 20, cx + 20, cy - 18, c)
    cv.line(cx - 20, cy - 18, cx - 26, cy + 4, c)
    cv.line(cx - 20, cy - 18, cx - 14, cy + 4, c)
    cv.line(cx - 26, cy + 4, cx - 14, cy + 4, c)
    cv.line(cx + 20, cy - 18, cx + 14, cy + 4, c)
    cv.line(cx + 20, cy - 18, cx + 26, cy + 4, c)
    cv.line(cx + 14, cy + 4, cx + 26, cy + 4, c)
    cv.hline(cx - 12, cx + 12, cy + 20, c)


def pic_chart(cv, cx, cy, c):
    cv.polyline([(cx - 24, cy - 16), (cx - 8, cy - 4), (cx + 4, cy - 12),
                 (cx + 20, cy + 16)], c)
    cv.line(cx + 20, cy + 16, cx + 8, cy + 16, c)
    cv.line(cx + 20, cy + 16, cx + 20, cy + 4, c)
    cv.hline(cx - 26, cx + 26, cy + 22, c)


def pic_burst(cv, cx, cy, c):
    for dx, dy in ((0, -22), (16, -16), (22, 0), (16, 16), (0, 22),
                   (-16, 16), (-22, 0), (-16, -16), (8, -20), (-8, -20),
                   (20, 8), (-20, 8)):
        cv.line(cx, cy, cx + dx, cy + dy, c)
    cv.circle(cx, cy, 6, c)


def pic_plus(cv, cx, cy, c):
    cv.fill_rect(cx - 6, cy - 22, cx + 6, cy + 22, c)
    cv.fill_rect(cx - 22, cy - 6, cx + 22, cy + 6, c)


def pic_cuffs(cv, cx, cy, c):
    cv.circle(cx - 14, cy - 6, 10, c, fill=False)
    cv.circle(cx + 14, cy + 6, 10, c, fill=False)
    cv.line(cx - 6, cy - 2, cx + 6, cy + 2, c)
    cv.line(cx - 4, cy - 6, cx + 8, cy - 2, c)


def pic_robot(cv, cx, cy, c):
    cv.fill_rect(cx - 18, cy - 12, cx + 18, cy + 20, c)
    cv.vline(cx, cy - 24, cy - 12, c)
    cv.circle(cx, cy - 26, 4, c)
    cv.fill_rect(cx - 10, cy - 4, cx - 4, cy + 2, PAPER)
    cv.fill_rect(cx + 4, cy - 4, cx + 10, cy + 2, PAPER)
    cv.hline(cx - 8, cx + 8, cy + 12, PAPER)


def pic_rocket(cv, cx, cy, c):
    cv.polyfill([(cx, cy - 24), (cx + 10, cy + 4), (cx - 10, cy + 4)], c)
    cv.polyfill([(cx - 10, cy + 0), (cx - 20, cy + 18), (cx - 10, cy + 14)], c)
    cv.polyfill([(cx + 10, cy + 0), (cx + 20, cy + 18), (cx + 10, cy + 14)], c)
    cv.polyfill([(cx, cy + 12), (cx + 6, cy + 24), (cx - 6, cy + 24)], GOLD)


PICTOGRAMS = [pic_lock, pic_scales, pic_chart, pic_burst,
              pic_plus, pic_cuffs, pic_robot, pic_rocket]


# ---------------------------------------------------------------- render
def render():
    cv = Canvas(W, H, PAPER)

    # --- masthead band
    cv.fill_rect(0, 0, W - 1, 88, INK)
    cv.fill_rect(28, 38, 40, 50, RED)
    draw_text(cv, 52, 27, MASTHEAD_TITLE, 5, WHITE)
    draw_text_right(cv, 996, 16, "SATURDAY", 3, GOLD)
    draw_text_right(cv, 996, 46, "21 NOVEMBER 2026", 3, WHITE)
    cv.fill_rect(0, 88, W - 1, 91, GOLD)

    # --- map field
    cv.fill_rect(MAP_X0, MAP_Y0, MAP_X1, MAP_Y1, MAP_NAVY)
    for x in range(MAP_X0, MAP_X1 + 1):
        cv.set(x, MAP_Y0, GOLD)
        cv.set(x, MAP_Y1, GOLD)
    for y in range(MAP_Y0, MAP_Y1 + 1):
        cv.set(MAP_X0, y, GOLD)
        cv.set(MAP_X1, y, GOLD)
    # graticule every 30 degrees
    for lon in range(-150, 181, 30):
        x, _ = lonlat_to_xy(lon, 0)
        cv.vline(x, MAP_Y0 + 1, MAP_Y1 - 1, MAP_GRID)
    for lat in range(-30, 61, 30):
        _, y = lonlat_to_xy(0, lat)
        cv.hline(MAP_X0 + 1, MAP_X1 - 1, y, MAP_GRID)
    _, y_eq = lonlat_to_xy(0, 0)
    cv.hline(MAP_X0 + 1, MAP_X1 - 1, y_eq, MAP_GRID_EQ)
    # dot-matrix continents
    for gy in range(MAP_Y0 + 4, MAP_Y1 - 2, DOT_STEP):
        for gx in range(MAP_X0 + 4, MAP_X1 - 2, DOT_STEP):
            lon, lat = xy_to_lonlat(gx, gy)
            if is_land(lon, lat):
                cv.circle(gx, gy, 2, MAP_DOT)
    # ocean labels
    for label, lon, lat in OCEAN_LABELS:
        x, y = lonlat_to_xy(lon, lat)
        draw_text(cv, x, y, label, 2, OCEAN_LABEL)
    # map label + compass
    draw_text(cv, MAP_X0 + 12, MAP_Y0 + 10, MAP_LABEL, 2, GOLD)
    cv.circle(968, 132, 13, GOLD, fill=False)
    cv.line(968, 132, 968, 121, GOLD)
    cv.polyfill([(968, 120), (965, 128), (971, 128)], GOLD)
    draw_text(cv, 965, 102, "N", 2, GOLD)

    # pins: dot at true location, leader line, numbered chip
    for s in STORIES:
        px, py = lonlat_to_xy(s["lon"], s["lat"])
        cx, cy = pin_chip_xy(s)
        cv.line(px, py, cx, cy, GOLD)
        cv.circle(px, py, 4, WHITE)
        cv.circle(px, py, 4, RED, fill=False)
        cv.circle(cx, cy, PIN_R, RED)
        cv.circle(cx, cy, PIN_R, WHITE, fill=False)
        num = str(s["n"])
        draw_text(cv, cx - text_width(num, 2) // 2, cy - 7, num, 2, WHITE)

    # --- legend
    TINT = {RED: (246, 222, 221), TEAL: (216, 237, 234), INK: (226, 230, 233)}
    for i, s in enumerate(STORIES):
        col = LEGEND_COLS[i % 2]
        row_y = LEGEND_Y0 + (i // 2) * LEGEND_ROW_H
        # big picture field (tinted square + pictogram) at the cell's left
        cv.fill_rect(col + 8, row_y + 12, col + 72, row_y + 76, TINT[s["stat_color"]])
        PICTOGRAMS[s["n"] - 1](cv, col + 40, row_y + 44, s["stat_color"])
        # number chip badged on the picture field's corner
        cv.circle(col + 8, row_y + 12, 13, RED)
        num = str(s["n"])
        draw_text(cv, col + 8 - text_width(num, 2) // 2, row_y + 5, num, 2, WHITE)
        # headline
        draw_text(cv, col + LEGEND_TEXT_X, row_y + 12, s["headline"], 3, INK)
        # big stat
        draw_text(cv, col + LEGEND_TEXT_X, row_y + 42, s["stat"], 5, s["stat_color"])
        # fact lines (max 2)
        for k, line in enumerate(wrap_text(s["fact"], 2, LEGEND_TEXT_W)):
            draw_text(cv, col + LEGEND_TEXT_X, row_y + 84 + k * 16, line, 2, GREY)
    # separators
    cv.vline(512, LEGEND_Y0, LEGEND_Y0 + 4 * LEGEND_ROW_H - 1, RULE)
    for r in range(1, 4):
        y = LEGEND_Y0 + r * LEGEND_ROW_H
        cv.hline(LEGEND_COLS[0], LEGEND_COLS[1] + LEGEND_COL_W - 1, y, RULE)

    # --- footer
    cv.hline(24, 1000, 980, RULE)
    for k, line in enumerate(FOOTER_LINES):
        draw_text(cv, 24, 988 + k * 9, line, 1, GREY)

    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(outdir, exist_ok=True)
    data = encode_png(render())
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print(f"wrote {path} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
