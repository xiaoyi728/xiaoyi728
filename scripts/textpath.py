"""把文字转成 SVG path —— 让 banner 在任何系统上都不依赖本地字体。

GitHub 用 <img> 加载 README 里的 SVG，此时外部字体、@font-face 全部失效，
中文还可能因系统缺字变豆腐块。把字符轮廓直接写进 path 是唯一稳的做法。
"""
from fontTools.ttLib import TTFont, TTCollection
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform

_CACHE = {}


def load(path, family_hint=None):
    key = (path, family_hint)
    if key in _CACHE:
        return _CACHE[key]
    if path.lower().endswith(".ttc"):
        coll = TTCollection(path)
        chosen = None
        for f in coll.fonts:
            names = " ".join(
                str(r) for r in f["name"].names if r.nameID in (1, 4, 6)
            )
            if family_hint and family_hint in names:
                chosen = f
                break
        font = chosen or coll.fonts[0]
    else:
        font = TTFont(path)
    font.upem = font["head"].unitsPerEm
    font.cmap = font.getBestCmap()
    font.gset = font.getGlyphSet()
    _CACHE[key] = font
    return font


def is_cjk(ch):
    o = ord(ch)
    return (
        0x3000 <= o <= 0x9FFF
        or 0xFF00 <= o <= 0xFFEF
        or 0x2018 <= o <= 0x201D
        or o in (0x00B7, 0x3001, 0x3002, 0x2014, 0x2026)
    )


def measure(text, font, size, tracking=0.0):
    w = 0.0
    for ch in text:
        gname = font.cmap.get(ord(ch))
        if gname and gname in font["hmtx"].metrics:
            w += font["hmtx"].metrics[gname][0] * size / font.upem
        else:
            w += size * 0.5
        w += tracking
    return w


def to_path(text, font, size, x, y, tracking=0.0, ntos=None):
    """返回 (path_d, 结束时的 x 坐标)。y 是基线。"""
    ntos = ntos or (lambda v: f"{v:.2f}")
    ds = []
    cx = x
    for ch in text:
        gname = font.cmap.get(ord(ch))
        if gname is None:
            cx += size * 0.5 + tracking
            continue
        g = font.gset[gname]
        pen = SVGPathPen(font.gset, ntos=ntos)
        tpen = TransformPen(pen, Transform(size / font.upem, 0, 0, -size / font.upem, cx, y))
        g.draw(tpen)
        d = pen.getCommands()
        if d:
            ds.append(d)
        cx += font["hmtx"].metrics[gname][0] * size / font.upem + tracking
    return " ".join(ds), cx
