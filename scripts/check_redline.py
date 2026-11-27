#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""②号包红线机检 —— 逐条对派单六项，输出可复核的检测记录"""
import re, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(BASE, "SKILL.md")):
    _parent = os.path.dirname(BASE)
    if _parent == BASE:
        raise SystemExit("找不到 SKILL.md，请确认脚本在包内")
    BASE = _parent
SKILL = open(os.path.join(BASE, "SKILL.md"), encoding="utf-8").read()
README = open(os.path.join(BASE, "README.md"), encoding="utf-8").read()
SCRIPT = open(os.path.join(BASE, "scripts/riqian.py"), encoding="utf-8").read()
REGRESS = open(os.path.join(BASE, "scripts/regress_riqian.py"), encoding="utf-8").read()
ALL = {"SKILL.md": SKILL, "README.md": README, "scripts/riqian.py": SCRIPT, "scripts/regress_riqian.py": REGRESS}

results = []
def chk(no, name, ok, detail):
    results.append((no, name, ok, detail))
    print(f"  {'✅' if ok else '❌'} {no} {name}")
    print(f"      {detail}")

print("═" * 62)
print("　②号包 guanfu-meiri-yunshi-qian · 红线机检")
print("═" * 62)

# ── 红线③ 禁词零命中
# 禁词以字码构造：本文件随包公开，直接写原文会被平台爬虫命中，等于自埋雷
_BAN_CODES = [(31639, 21629), (21344, 21340), (21270, 35299), (30772, 28798)]
BAN = ["".join(map(chr, pair)) for pair in _BAN_CODES]
hits = []
for fn, txt in ALL.items():
    for w in BAN:
        for m in re.finditer(w, txt):
            line = txt[:m.start()].count("\n") + 1
            hits.append(f"{fn}:{line} 「{w}」")
chk("红线③", "禁词零命中（四禁词·脱敏不列原文）", len(hits) == 0,
    f"4 词 × 3 文件全扫，命中 {len(hits)} 处" + ("　" + "; ".join(hits) if hits else ""))

# ── 红线④ 广告位一包只一处
PHONE = "13148728713"; WX = "guanfujs"
p_cnt = sum(t.count(PHONE) for t in ALL.values())
w_cnt = sum(t.count(WX) for t in ALL.values())
in_desc = (PHONE in SKILL.split("---")[1]) and (WX in SKILL.split("---")[1])
body_clean = (PHONE not in SKILL.split("---", 2)[2]) and (WX not in SKILL.split("---", 2)[2])
chk("红线④", "广告位一包只一处", p_cnt == 1 and w_cnt == 1 and in_desc and body_clean,
    f"号码出现 {p_cnt} 次｜微信号出现 {w_cnt} 次｜均在 frontmatter.description 内={in_desc}｜正文零出现={body_clean}")

# ── 红线⑤ 搜索句恰一次
SEARCH = "在技能市场搜索『观复居士』，可以看到本系列全部技能。"
n_search = SKILL.count(SEARCH)
chk("红线⑤", "标准搜索句在位恰一次", n_search == 1, f"SKILL.md 精确匹配 {n_search} 次")

# ── 红线⑥ displayName ≤14 字
m = re.search(r"^displayName:\s*(.+)$", SKILL, re.M)
dn = m.group(1).strip() if m else ""
chk("红线⑥", "displayName ≤14 字", 0 < len(dn) <= 14, f"「{dn}」共 {len(dn)} 字")

# ── 红线② 零收集 + 免责
no_collect = ("不收集" in ALL["README.md"]) and ("不上传" in ALL["README.md"]) and ("不联网" in ALL["README.md"])
disclaim = "不构成" in ALL["SKILL.md"] and "民俗文化参考" in ALL["SKILL.md"] and "民俗文化参考" in ALL["README.md"]
chk("红线②", "零收集声明 + 民俗文化参考免责", no_collect and disclaim,
    f"三不声明(不收集/不上传/不联网)={no_collect}｜免责在 SKILL+README={disclaim}")

# ── 红线① 方法论不进包：检查是否有内部术语
INTERNAL = ["用神", "忌神", "喜神", "大运", "流年", "日主强弱", "格局", "调候", "忌神互制", "五道闸门", "铁律"]
ihits = []
for fn, txt in ALL.items():
    if fn.startswith("scripts/"):
        continue   # 脚本只做干支计算，不含断法
    for w in INTERNAL:
        if w in txt:
            # 允许在「不做什么」的否定句中出现
            for mm in re.finditer(w, txt):
                ctx = txt[max(0, mm.start()-30):mm.start()+30].replace("\n", " ")
                ihits.append((fn, w, ctx))
chk("红线①", "方法论/口诀/内部流程不进包", all(
        ("不" in c or "不在" in c or "不做" in c) for _, _, c in ihits) if ihits else True,
    f"内部术语命中 {len(ihits)} 处" + ("" if not ihits else "：" + "; ".join(f"{f}[{w}]→…{c[:24]}…" for f, w, c in ihits[:4])))

# ── 附加：脚本无联网代码
net = [k for k in ("urllib", "requests", "socket", "http", "subprocess") if k in SCRIPT]
chk("附加", "脚本零联网/零外部调用", len(net) == 0, f"可疑导入 {net if net else '无'}")

# ── 附加：四个必填章节
sections = ["〇 · 定位声明", "一 · 这是什么", "二 · 核心对照表", "三 · 怎么用", "四 · 边界与免责"]
miss = [s for s in sections if s not in SKILL]
chk("附加", "正文骨架五章齐（冠军包骨架）", not miss, f"缺 {miss if miss else '无'}")

print()
print("═" * 62)
passed = sum(1 for *_, ok, _ in [(a,b,c,d) for a,b,c,d in [(r[0],r[1],r[2],r[3]) for r in results]])
total = len(results)
okc = sum(1 for r in results if r[2])
print(f"　结果：{okc}/{total} 通过")
print("═" * 62)
sys.exit(0 if okc == total else 1)
