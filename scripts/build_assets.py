#!/usr/bin/env python3
"""生成 GitHub profile 用的自绘 SVG（无外部服务、无字体依赖）。

  python3 scripts/build_assets.py                # 默认配色，写入 assets/
  python3 scripts/build_assets.py --all-preview   # 三种配色全部渲染到 previews/
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import textpath as tp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 字体路径可用环境变量覆盖（CI 与本机路径不同）
MONO = os.environ.get("FONT_MONO", "/home/incam/.local/share/fonts/JetBrainsMono-Regular.ttf")
MONO_B = os.environ.get("FONT_MONO_BOLD", "/home/incam/.local/share/fonts/JetBrainsMono-Bold.ttf")
SERIF_TTC = os.environ.get("FONT_SERIF_CJK", "/usr/share/fonts/google-noto-cjk/NotoSerifCJK-Regular.ttc")
SERIF_FAMILY = os.environ.get("FONT_SERIF_HINT", "Noto Serif CJK SC")

PALETTES = {
    # 纸墨 / 琥珀：编辑部＋工程铭牌，最不容易撞
    "amber": dict(
        light=dict(bg="#F7F4ED", ink="#17181B", muted="#6E6A62", line="#DED7C8", accent="#B45309", accent2="#17181B"),
        dark=dict(bg="#0E1013", ink="#EDE9E1", muted="#8B8F96", line="#242A31", accent="#E9A73C", accent2="#EDE9E1"),
    ),
    # 石墨 / 薄荷：最"开发者工具"，偏冷
    "mint": dict(
        light=dict(bg="#F3F6F5", ink="#0F1413", muted="#5F6B67", line="#D5DEDA", accent="#0F766E", accent2="#0F1413"),
        dark=dict(bg="#0A0F0E", ink="#E6F0EC", muted="#7E8C87", line="#1C2624", accent="#4FD1B5", accent2="#E6F0EC"),
    ),
    # 宣纸 / 朱砂：最有中文编辑气，也最大胆
    "vermilion": dict(
        light=dict(bg="#FAF6F0", ink="#1A1614", muted="#7A6E66", line="#E4D9CC", accent="#B3261E", accent2="#1A1614"),
        dark=dict(bg="#120F0E", ink="#F2EAE2", muted="#93857B", line="#2A2320", accent="#E0604F", accent2="#F2EAE2"),
    ),
}

SNAPSHOT = dict(
    login="xiaoyi728",
    name="xiaoyi233",
    followers=3,
    following=3,
    publicRepos=8,
    stars=5,
    contributions=33,
    years=5,
    languages={"Go": 3796724, "TypeScript": 3643163, "JavaScript": 240205, "CSS": 149792, "Other": 80000},
    weeks=[0, 0, 0, 1, 0, 0, 2, 0, 0, 0, 0, 0, 1, 0, 0, 0, 3, 0, 0, 1, 0, 0, 0, 2, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 2, 0, 0, 1, 0, 0, 0, 0, 0, 0, 3, 0, 0, 1, 0, 0, 0, 0, 0],
)


def load_snapshot():
    p = os.path.join(ROOT, "snapshot.json")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        SNAPSHOT.update({k: v for k, v in data.items() if v is not None})
    return SNAPSHOT


def fonts():
    return (
        tp.load(MONO),
        tp.load(MONO_B),
        tp.load(SERIF_TTC, SERIF_FAMILY),
    )


F = None


def seg(x, y, text, size, color, kind="mono", tracking=0.0, bold=False):
    """一段文字（自动按字符选字体：CJK -> 衬线，其余 -> 等宽）。返回 (svg, 结束 x)。"""
    mono_r, mono_b, serif = F
    font = (mono_b if bold else mono_r) if kind == "mono" else serif
    d, endx = tp.to_path(text, font, size, x, y, tracking)
    if not d:
        return "", endx
    return f'<path d="{d}" fill="{color}"/>', endx


def rich(x, y, parts, tracking=0.0):
    """parts: [(text, size, color, kind, bold)] —— 逐段渲染并返回 (svg, 结束 x)"""
    out, cx = [], x
    for text, size, color, kind, bold in parts:
        s, cx = seg(cx, y, text, size, color, kind, tracking, bold)
        out.append(s)
    return "".join(out), cx


def chars(text, size, color, kind="mono", tracking=0.0):
    """宽度计算，用于右对齐。"""
    mono_r, mono_b, serif = F
    font = serif if kind == "serif" else mono_r
    return tp.measure(text, font, size, tracking)


def svg_open(w, h, extra=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img"{extra}>'
    )


def grid(w, h, c, step=50, op=0.5):
    lines = []
    x = step
    while x < w:
        lines.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{h}"/>')
        x += step
    y = step
    while y < h:
        lines.append(f'<line x1="0" y1="{y}" x2="{w}" y2="{y}"/>')
        y += step
    return (
        f'<g stroke="{c["line"]}" stroke-width="1" opacity="{op}">'
        + "".join(lines)
        + "</g>"
    )


# ---------------------------------------------------------------- hero
def hero(c, who, meta):
    W, H = 1000, 300
    p = [svg_open(W, H, ' aria-label="xiaoyi728 profile banner"')]
    p.append(f'<rect width="{W}" height="{H}" fill="{c["bg"]}"/>')
    p.append(grid(W, H, c, 50, 0.45))

    # 左侧：身份
    p.append(f'<rect x="56" y="72" width="8" height="8" fill="{c["accent"]}"/>')
    s, _ = seg(74, 81, "PROFILE  /  2026", 11, c["muted"], tracking=2.4)
    p.append(s)

    name = who["login"]
    s, _ = seg(54, 158, name, 52, c["ink"], tracking=-1.2, bold=True)
    p.append(s)

    # 中文定位：书名号用强调色，正文用墨色
    parts = [
        ("「", 24, c["accent"], "serif", False),
        ("最小侵入式工具匠", 24, c["ink"], "serif", False),
        ("」", 24, c["accent"], "serif", False),
    ]
    s, endx = rich(56, 204, parts)
    p.append(s)
    s2, ex2 = seg(endx + 14, 204, "minimal intrusion by default", 11, c["muted"], tracking=0.6)
    p.append(s2)

    s, _ = seg(57, 233, "now", 12, c["accent"], tracking=0.6)
    p.append(s)
    nx = 57 + chars("now", 12, "", tracking=0.6) + 12
    s, _ = seg(nx, 233, "wild-work  /  aihot  /  dsh-rule-proxy", 12, c["ink"], tracking=0.3)
    p.append(s)

    # 光标
    cx = nx + chars("wild-work  /  aihot  /  dsh-rule-proxy", 12, "", tracking=0.3) + 7
    p.append(
        '<style>@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}'
        '.cur{animation:blink 1.2s steps(1) infinite}</style>'
    )
    p.append(f'<rect class="cur" x="{cx:.1f}" y="222" width="8" height="14" fill="{c["accent"]}"/>')

    s, _ = seg(57, 268, "GO   ·   TYPESCRIPT   ·   DSH PLUGINS", 10, c["muted"], tracking=2.0)
    p.append(s)

    # 分隔线
    p.append(f'<line x1="636" y1="64" x2="636" y2="252" stroke="{c["line"]}" stroke-width="1"/>')

    # 右侧：三条铁律（来自他自己项目里的设计口径）
    s, _ = seg(668, 84, "PRINCIPLES", 10, c["muted"], tracking=2.4)
    p.append(s)
    s, _ = seg(668 + chars("PRINCIPLES", 10, "", tracking=2.4) + 12, 84, "三条铁律", 11, c["muted"], kind="serif")
    p.append(s)

    rows = [
        ("01", "不改包", "no patch · no asar edit · survive auto-update"),
        ("02", "不越界", "rule-scoped routing, never a global takeover"),
        ("03", "可还原", "one click back to stock, zero residue"),
    ]
    for i, (num, title_cn, desc) in enumerate(rows):
        y = 130 + i * 48
        s, _ = seg(668, y, num, 11, c["accent"], tracking=1.0)
        p.append(s)
        s, _ = seg(700, y, title_cn, 19, c["ink"], kind="serif")
        p.append(s)
        s, _ = seg(700, y + 19, desc, 10, c["muted"], tracking=0.3)
        p.append(s)

    # 右下角 handle
    handle = f'github.com/{who["login"]}'
    s, _ = seg(944 - chars(handle, 10, "", tracking=1.0), 268, handle, 10, c["muted"], tracking=1.0)
    p.append(s)

    p.append("</svg>")
    return "".join(p)



# ---------------------------------------------------------------- mobile hero
def hero_mobile(c, who, meta):
    """手机端专用版：480 宽，字号放大，纵向堆叠。GitHub 手机网页会把 1000 宽的图缩到 ~360，字就没法看了。"""
    W, H = 480, 412
    p = [svg_open(W, H, ' aria-label="xiaoyi728 profile banner (mobile)"')]
    p.append(f'<rect width="{W}" height="{H}" fill="{c["bg"]}"/>')
    p.append(grid(W, H, c, 40, 0.4))

    p.append(f'<rect x="28" y="40" width="7" height="7" fill="{c["accent"]}"/>')
    s, _ = seg(43, 48, "PROFILE  /  2026", 10, c["muted"], tracking=2.2)
    p.append(s)

    s, _ = seg(26, 104, who["login"], 38, c["ink"], tracking=-1.0, bold=True)
    p.append(s)

    parts = [
        ("「", 20, c["accent"], "serif", False),
        ("最小侵入式工具匠", 20, c["ink"], "serif", False),
        ("」", 20, c["accent"], "serif", False),
    ]
    s, _ = rich(28, 142, parts)
    p.append(s)

    s, _ = seg(28, 168, "minimal intrusion by default", 10.5, c["muted"], tracking=0.5)
    p.append(s)

    s, _ = seg(28, 200, "now", 11, c["accent"], tracking=0.5)
    p.append(s)
    nx = 28 + chars("now", 11, "", tracking=0.5) + 10
    s, _ = seg(nx, 200, "wild-work / aihot / dsh-rule-proxy", 11, c["ink"], tracking=0.2)
    p.append(s)

    p.append(f'<line x1="28" y1="224" x2="452" y2="224" stroke="{c["line"]}"/>')

    rows = [
        ("01", "不改包", "no patch · survive auto-update"),
        ("02", "不越界", "rule-scoped, never global"),
        ("03", "可还原", "one click back to stock"),
    ]
    for i, (num, cn, desc) in enumerate(rows):
        y = 260 + i * 46
        s, _ = seg(28, y, num, 10, c["accent"], tracking=1.0)
        p.append(s)
        s, _ = seg(56, y, cn, 17, c["ink"], kind="serif")
        p.append(s)
        s, _ = seg(56, y + 17, desc, 9.5, c["muted"], tracking=0.3)
        p.append(s)

    s, _ = seg(28, 394, "GO   ·   TYPESCRIPT   ·   DSH PLUGINS", 9, c["muted"], tracking=1.8)
    p.append(s)
    p.append("</svg>")
    return "".join(p)


# ---------------------------------------------------------------- mobile stats
def stats_mobile(c, who, meta):
    W, H = 480, 330
    p = [svg_open(W, H, ' aria-label="xiaoyi728 stats (mobile)"')]
    p.append(f'<rect width="{W}" height="{H}" fill="{c["bg"]}"/>')
    p.append(grid(W, H, c, 40, 0.35))

    s, _ = seg(28, 46, "CONTRIBUTIONS  ·  12M", 9.5, c["muted"], tracking=1.8)
    p.append(s)
    s, _ = seg(26, 96, str(who["contributions"]), 40, c["ink"], tracking=-1.0, bold=True)
    p.append(s)
    s, _ = seg(26 + chars(str(who["contributions"]), 40, "", tracking=-1.0) + 8, 96, "contributions", 9, c["muted"])
    p.append(s)
    s, _ = seg(28, 118, f'across {who["years"]} years · public only', 9.5, c["muted"], tracking=0.4)
    p.append(s)

    p.append(f'<line x1="28" y1="142" x2="452" y2="142" stroke="{c["line"]}"/>')

    s, _ = seg(28, 170, "LANGUAGES", 9.5, c["muted"], tracking=1.8)
    p.append(s)
    s, _ = seg(28 + chars("LANGUAGES", 9.5, "", tracking=1.8) + 10, 170, "自有仓库", 9.5, c["muted"], kind="serif")
    p.append(s)

    langs = who["languages"]
    total = sum(langs.values()) or 1
    order = sorted(langs.items(), key=lambda kv: -kv[1])
    top = order[:3]
    rest = sum(v for _, v in order[3:])
    if rest:
        top = top + [("Other", rest)]
    colors = [c["accent"], c["ink"], c["muted"], c["line"]]
    x0, bw = 28, 424
    x = x0
    for i, (_, v) in enumerate(top):
        w = bw * v / total
        p.append(f'<rect x="{x:.1f}" y="186" width="{max(w - 2, 1):.1f}" height="11" fill="{colors[i]}" opacity="{1 if i < 2 else .38}"/>')
        x += w

    lx = x0
    for i, (name, v) in enumerate(top):
        label = f"{name} {v / total * 100:.0f}%"
        s, _ = seg(lx, 216, label, 9.5, c["ink"] if i == 0 else c["muted"], tracking=0.3)
        p.append(s)
        lx += chars(label, 9.5, "", tracking=0.3) + 14

    p.append(f'<line x1="28" y1="240" x2="452" y2="240" stroke="{c["line"]}"/>')

    s, _ = seg(28, 268, "ACTIVITY", 9.5, c["muted"], tracking=1.8)
    p.append(s)
    s, _ = seg(28 + chars("ACTIVITY", 9.5, "", tracking=1.8) + 10, 268, "近 53 周", 9.5, c["muted"], kind="serif")
    p.append(s)

    weeks = who["weeks"][-53:]
    mx = max(weeks) or 1
    n = len(weeks)
    gap = 1.3
    bwid = (424 - gap * (n - 1)) / n
    for i, v in enumerate(weeks):
        h = 1.5 + (26 * v / mx)
        op = 0.18 + 0.82 * (v / mx)
        p.append(
            f'<rect x="{28 + i * (bwid + gap):.1f}" y="{306 - h:.1f}" width="{bwid:.1f}" '
            f'height="{h:.1f}" fill="{c["accent"]}" opacity="{op:.2f}"/>'
        )

    s, _ = seg(28, 322, f'{who["publicRepos"]} REPOS · {who["stars"]} STARS · {who["followers"]} FOLLOWERS', 8.5, c["muted"], tracking=1.0)
    p.append(s)
    p.append("</svg>")
    return "".join(p)


# ---------------------------------------------------------------- stats
def stats(c, who, meta):
    W, H = 1000, 210
    p = [svg_open(W, H, ' aria-label="xiaoyi728 stats"')]
    p.append(f'<rect width="{W}" height="{H}" fill="{c["bg"]}"/>')
    p.append(grid(W, H, c, 50, 0.35))

    # A. 贡献
    s, _ = seg(56, 52, "CONTRIBUTIONS  ·  LAST 12M", 10, c["muted"], tracking=2.0)
    p.append(s)
    s, _ = seg(54, 112, str(who["contributions"]), 52, c["ink"], tracking=-1.0, bold=True)
    p.append(s)
    w_num = chars(str(who["contributions"]), 52, "", tracking=-1.0)
    s, _ = seg(56 + w_num + 10, 112, "contributions", 11, c["muted"], tracking=0.4)
    p.append(s)
    s, _ = seg(56, 140, f'across {who["years"]} years · public only', 10, c["muted"], tracking=0.5)
    p.append(s)

    p.append(f'<line x1="312" y1="40" x2="312" y2="170" stroke="{c["line"]}"/>')

    # B. 语言占比（只统计自有仓库）
    s, _ = seg(344, 52, "LANGUAGES", 10, c["muted"], tracking=2.0)
    p.append(s)
    s, _ = seg(344 + chars("LANGUAGES", 10, "", tracking=2.0) + 12, 52, "自有仓库", 10, c["muted"], kind="serif")
    p.append(s)

    langs = who["languages"]
    total = sum(langs.values()) or 1
    order = sorted(langs.items(), key=lambda kv: -kv[1])
    top = order[:3]
    rest = sum(v for _, v in order[3:])
    if rest:
        top = top + [("其它", rest)] if False else top + [("Other", rest)]
    colors = [c["accent"], c["ink"], c["muted"], c["line"]]
    x0, bw = 344, 316
    x = x0
    for i, (_, v) in enumerate(top):
        w = bw * v / total
        p.append(f'<rect x="{x:.1f}" y="72" width="{max(w - 2, 1):.1f}" height="12" fill="{colors[i]}" opacity="{1 if i < 2 else .38}"/>')
        x += w
    p.append(f'<line x1="{x0}" y1="90" x2="{x0 + bw}" y2="90" stroke="{c["line"]}"/>')

    lx = x0
    for i, (name, v) in enumerate(top):
        pct = v / total * 100
        s, _ = seg(lx, 112, f"{name} {pct:.0f}%", 10.5, c["ink"] if i == 0 else c["muted"], tracking=0.4)
        p.append(s)
        lx += chars(f"{name} {pct:.0f}%", 10.5, "", tracking=0.4) + 18

    s, _ = seg(344, 140, "measured by bytes in repos I own (forks excluded)", 9.5, c["muted"], tracking=0.3)
    p.append(s)

    p.append(f'<line x1="672" y1="40" x2="672" y2="170" stroke="{c["line"]}"/>')

    # C. 53 周活动条
    s, _ = seg(704, 52, "ACTIVITY", 10, c["muted"], tracking=2.0)
    p.append(s)
    s, _ = seg(704 + chars("ACTIVITY", 10, "", tracking=2.0) + 12, 52, "近 53 周", 10, c["muted"], kind="serif")
    p.append(s)

    weeks = who["weeks"][-53:]
    mx = max(weeks) or 1
    n = len(weeks)
    gap = 1.6
    bwid = (240 - gap * (n - 1)) / n
    for i, v in enumerate(weeks):
        h = 2 + (38 * v / mx)
        op = 0.18 + 0.82 * (v / mx)
        p.append(
            f'<rect x="{704 + i * (bwid + gap):.1f}" y="{150 - h:.1f}" width="{bwid:.1f}" '
            f'height="{h:.1f}" fill="{c["accent"]}" opacity="{op:.2f}"/>'
        )
    s, _ = seg(704, 174, "each bar = 1 week", 9.5, c["muted"], tracking=0.3)
    p.append(s)

    # 页脚
    foot = f'{who["publicRepos"]} PUBLIC REPOS   ·   {who["stars"]} STARS   ·   {who["followers"]} FOLLOWERS'
    s, _ = seg(56, 196, foot, 9.5, c["muted"], tracking=1.6)
    p.append(s)
    gen = "generated daily by github actions · no third-party service"
    s, _ = seg(944 - chars(gen, 9.5, "", tracking=0.8), 196, gen, 9.5, c["muted"], tracking=0.8)
    p.append(s)

    p.append("</svg>")
    return "".join(p)


def main():
    global F
    ap = argparse.ArgumentParser()
    ap.add_argument("--palette", default="amber", choices=list(PALETTES))
    ap.add_argument("--all-preview", action="store_true")
    args = ap.parse_args()

    who = load_snapshot()
    F = fonts()

    outdir = os.path.join(ROOT, "assets")
    os.makedirs(outdir, exist_ok=True)

    for mode in ("light", "dark"):
        c = PALETTES[args.palette][mode]
        with open(os.path.join(outdir, f"hero-{mode}.svg"), "w", encoding="utf-8") as f:
            f.write(hero(c, who, None))
        with open(os.path.join(outdir, f"stats-{mode}.svg"), "w", encoding="utf-8") as f:
            f.write(stats(c, who, None))
        with open(os.path.join(outdir, f"hero-mobile-{mode}.svg"), "w", encoding="utf-8") as f:
            f.write(hero_mobile(c, who, None))
        with open(os.path.join(outdir, f"stats-mobile-{mode}.svg"), "w", encoding="utf-8") as f:
            f.write(stats_mobile(c, who, None))

    if args.all_preview:
        pdir = os.path.join(ROOT, "previews")
        os.makedirs(pdir, exist_ok=True)
        for pname, pal in PALETTES.items():
            for mode in ("light", "dark"):
                c = pal[mode]
                with open(os.path.join(pdir, f"{pname}-hero-{mode}.svg"), "w", encoding="utf-8") as f:
                    f.write(hero(c, who, None))
                with open(os.path.join(pdir, f"{pname}-stats-{mode}.svg"), "w", encoding="utf-8") as f:
                    f.write(stats(c, who, None))
                with open(os.path.join(pdir, f"{pname}-hero-mobile-{mode}.svg"), "w", encoding="utf-8") as f:
                    f.write(hero_mobile(c, who, None))

    print("ok ->", outdir)


if __name__ == "__main__":
    main()
