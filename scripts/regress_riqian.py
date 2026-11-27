#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""日签三柱回归：riqian.py vs 观复引擎 v5.5"""
import sys, os, re, subprocess
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE) if os.path.basename(_HERE) == "scripts" else _HERE
sys.path.insert(0, os.path.join(_ROOT, "scripts"))
from riqian import day_pillar, year_pillar, month_branch, TIANGAN

CASES = [
    "2026-11-27", "1999-03-21", "1984-02-05", "2000-02-04", "2026-05-27",
    "1990-05-12", "1992-09-03", "2024-02-04", "2024-02-10", "2000-01-01",
    "2008-08-08", "1968-11-11", "2020-02-29", "2015-07-07", "2030-07-01",
]

def engine(y, m, d):
    out = subprocess.run(
        ["bash", "/Users/mac/.hermes/skills/guanfu-paipan/scripts/paipan.sh",
         f"{y}-{m:02d}-{d:02d} 12:00", "女"],
        capture_output=True, text=True, timeout=120).stdout
    p = {}
    for k in ("年柱", "月柱", "日柱"):
        mm = re.search(rf"{k}:\s*(\S{{2}})", out)
        p[k] = mm.group(1) if mm else "??"
    return p

ok = 0; bad = []
for s in CASES:
    y, m, d = map(int, s.split("-"))
    dgz, _ = day_pillar(y, m, d)
    ygz = year_pillar(y, m, d)
    jd_ut = __import__("riqian").julian_day(y, m, d, 12.0) - 8.0 / 24.0
    mzhi, midx = month_branch(jd_ut)
    _start = {0:2,5:2,1:4,6:4,2:6,7:6,3:8,8:8,4:0,9:0}[TIANGAN.index(ygz[0])]
    mgz = TIANGAN[(_start + midx) % 10] + mzhi

    mine = {"年柱": ygz, "月柱": mgz, "日柱": dgz}
    exp = engine(y, m, d)
    if all(mine[k] == exp[k] for k in mine):
        ok += 1
    else:
        bad.append((s, {k: (mine[k], exp[k]) for k in mine if mine[k] != exp[k]}))

print("═" * 54)
print(f"　日签三柱回归：{ok}/{len(CASES)} 全中")
print("═" * 54)
for s, diff in bad:
    print(f"  · {s}")
    for k, (a, b) in diff.items():
        print(f"      {k}：日签 {a} ≠ 引擎 {b}")
if not bad:
    print("\n　✅ 15 例年/月/日三柱全中，含立春边界与闰日。")
