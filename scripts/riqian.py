#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日运势日签 · 日签引擎
纯 Python 标准库实现，零第三方依赖。

设计原则：
  1. 日柱、月建、建除十二神全部由脚本确定性计算，不靠任何模型心算。
  2. 只给「今日一签」——宜、忌、一句提点、一个颜色，30 秒看完。
  3. 不联网、不写文件、不收集任何信息。

用法：
  python3 riqian.py                # 今天
  python3 riqian.py 2026-11-27     # 指定日期
  python3 riqian.py 2026-11-27 --long   # 展开版（多一段说明）
"""
import sys, math
from datetime import datetime, timedelta, timezone

# ─────────────────────────── 基础常量 ───────────────────────────
TIANGAN = "甲乙丙丁戊己庚辛壬癸"
DIZHI   = "子丑寅卯辰巳午未申酉戌亥"

GAN_WX = {"甲":"木","乙":"木","丙":"火","丁":"火","戊":"土",
          "己":"土","庚":"金","辛":"金","壬":"水","癸":"水"}
ZHI_WX = {"子":"水","丑":"土","寅":"木","卯":"木","辰":"土","巳":"火",
          "午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水"}

# 五行 → 今日宜色（传统五行配色）
WX_COLOR = {
    "木": ("青绿", "青、绿、翠"),
    "火": ("赤红", "红、橙、紫"),
    "土": ("黄褐", "黄、米、咖"),
    "金": ("白金", "白、银、金"),
    "水": ("玄蓝", "黑、深蓝、灰"),
}

# 建除十二神（以月建为「建」，顺行十二位）
JIANCHU = ["建", "除", "满", "平", "定", "执", "破", "危", "成", "收", "开", "闭"]

# 建除十二神传统宜忌（《协纪辨方书》所载通行说法，公开常识层）
JIANCHU_YIJI = {
    "建": (["出行", "上任", "见贵", "议事"], ["动土", "开仓", "掘井"]),
    "除": (["扫除", "除旧", "求医", "净宅"], ["远行", "嫁娶", "开业"]),
    "满": (["祭祀", "祈福", "开市", "结纳"], ["动土", "服药", "赴任"]),
    "平": (["修饰", "平治", "协调", "疏通"], ["开渠", "栽种", "动土"]),
    "定": (["嫁娶", "安床", "冠笄", "立约"], ["诉讼", "远行", "搬迁"]),
    "执": (["修造", "捕捉", "固守"], ["开市", "远行", "搬迁"]),
    "破": (["拆旧", "破土", "求医"], ["嫁娶", "开市", "签约"]),
    "危": (["祈福", "安床", "静养"], ["登高", "远行", "冒险"]),
    "成": (["嫁娶", "开市", "入学", "签约"], ["诉讼", "争竞"]),
    "收": (["纳财", "收账", "进人", "收藏"], ["开仓", "远行", "放贷"]),
    "开": (["开市", "出行", "求学", "求财"], ["安葬", "封仓"]),
    "闭": (["筑堤", "修补", "埋藏", "养息"], ["开市", "出行", "求医"]),
}

# 一句提点（现代语，不谈吉凶，只说「今天适合往哪个方向用力」）
JIANCHU_TIP = {
    "建": "地基日——把新的东西立起来，比修补旧的更划算。",
    "除": "清理日——该扔的扔、该断的断，清空比填满有用。",
    "满": "收拢日——把散着的人和事凑到一起，今天适合聚不适合散。",
    "平": "摆平日——不平的事今天摆平最省力，别硬碰。",
    "定": "落定日——口头的事今天写下来，悬着的事今天定下来。",
    "执": "守住日——今天不进攻，守住已有的就是赢。",
    "破": "拆旧日——拆掉比新建容易，先破后立，别在今天签新约。",
    "危": "收着日——话少说两句、步子放慢半拍，不出错就是顺。",
    "成": "成事日——今天去做那件拖了很久的正事，容易成。",
    "收": "收账日——该回来了的今天去要，别怕开口。",
    "开": "开门日——把想做的事推出去，今天门是开的。",
    "闭": "关门日——今天适合往里收，不适合往外跑。",
}

# ─────────────────────────── 天文：太阳视黄经 ───────────────────────────
def julian_day(y, m, d, hour=12.0):
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524.5 + hour / 24.0

def sun_longitude(jd):
    t = (jd - 2451545.0) / 36525.0
    l0 = 280.46646 + 36000.76983 * t + 0.0003032 * t * t
    m  = 357.52911 + 35999.05029 * t - 0.0001537 * t * t
    c  = ((1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(math.radians(m))
          + (0.019993 - 0.000101 * t) * math.sin(math.radians(2 * m))
          + 0.000289 * math.sin(math.radians(3 * m)))
    true_long = l0 + c
    omega = 125.04 - 1934.136 * t
    return (true_long - 0.00569 - 0.00478 * math.sin(math.radians(omega))) % 360.0

def find_solar_term(year, target_lon):
    base = julian_day(year, 3, 20, 12.0)
    offset = ((target_lon - 360.0) if target_lon >= 270 else target_lon) / 0.98565
    est = base + offset
    for _ in range(12):
        lon = sun_longitude(est)
        diff = ((lon - target_lon) + 180.0) % 360.0 - 180.0
        if abs(diff) < 1e-6:
            break
        est -= diff / 0.98565
    return est

def month_branch(jd_ut):
    """按太阳黄经判月令地支（等价于按节气分界）。"""
    lon = sun_longitude(jd_ut)
    idx = int(((lon - 315.0) % 360.0) // 30.0)
    return "寅卯辰巳午未申酉戌亥子丑"[idx], idx

# ─────────────────────────── 日签计算 ───────────────────────────
WEEKDAY_CN = ["一", "二", "三", "四", "五", "六", "日"]

def day_pillar(y, m, d):
    """日柱（以当地日期为准，不涉及时区）。1999-03-21 = 壬申 校准。"""
    jd = julian_day(y, m, d, 0.0)
    jdn = int(jd + 0.5)
    idx = (jdn + 49) % 60
    return TIANGAN[idx % 10] + DIZHI[idx % 12], idx

def year_pillar(y, m, d):
    """年柱（立春为界）。"""
    jd_ut = julian_day(y, m, d, 12.0) - 8.0 / 24.0
    lichun = find_solar_term(y, 315.0)
    yy = y - 1 if jd_ut < lichun else y
    idx = (yy - 1984) % 60
    return TIANGAN[idx % 10] + DIZHI[idx % 12]

def jianchu_shen(day_zhi, month_zhi):
    """建除十二神：以月建为该月「建」日，日支与月支同即建，顺行。"""
    d = DIZHI.index(day_zhi)
    m = DIZHI.index(month_zhi)
    return JIANCHU[(d - m) % 12]

def make_qian(date_str=None, long=False):
    if date_str:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        dt = datetime.now(timezone(timedelta(hours=8)))
    y, m, d = dt.year, dt.month, dt.day

    dgz, didx = day_pillar(y, m, d)
    ygz = year_pillar(y, m, d)
    jd_ut = julian_day(y, m, d, 12.0) - 8.0 / 24.0
    mzhi, midx = month_branch(jd_ut)
    # 月干：五虎遁（甲己丙寅、乙庚戊寅、丙辛庚寅、丁壬壬寅、戊癸甲寅）
    _start = {0: 2, 5: 2, 1: 4, 6: 4, 2: 6, 7: 6, 3: 8, 8: 8, 4: 0, 9: 0}[TIANGAN.index(ygz[0])]
    mgz = TIANGAN[(_start + midx) % 10] + mzhi
    jc = jianchu_shen(dgz[1], mzhi)

    d_gan, d_zhi = dgz[0], dgz[1]
    wx = GAN_WX[d_gan]
    color_name, color_list = WX_COLOR[wx]
    yi, ji = JIANCHU_YIJI[jc]
    tip = JIANCHU_TIP[jc]

    return {
        "date": dt.strftime("%Y-%m-%d"),
        "weekday": "星期" + WEEKDAY_CN[dt.weekday()],
        "year_gz": ygz, "month_gz": mgz, "month_zhi": mzhi, "day_gz": dgz,
        "jianchu": jc, "wx": wx, "color_name": color_name, "color_list": color_list,
        "yi": yi, "ji": ji, "tip": tip, "long": long,
    }

# ─────────────────────────── 渲染 ───────────────────────────
def render(q):
    L = []
    L.append("╔" + "═" * 34 + "╗")
    L.append(f"║　{q['date']}　{q['weekday']}　今日一签" + "　║")
    L.append("╚" + "═" * 34 + "╝")
    L.append("")
    L.append(f"　干支　{q['year_gz']}年　{q['month_gz']}月　{q['day_gz']}日")
    L.append(f"　建除　{q['jianchu']}日")
    L.append(f"　五行　{q['wx']}日　·　今日宜色：{q['color_name']}（{q['color_list']}）")
    L.append("")
    L.append(f"　宜　{'、'.join(q['yi'])}")
    L.append(f"　忌　{'、'.join(q['ji'])}")
    L.append("")
    L.append(f"　一句　{q['tip']}")
    L.append("")
    L.append("─" * 36)
    if q["long"]:
        L.append(f"　{q['jianchu']}日是怎么来的：")
        L.append(f"　本月月建为「{q['month_zhi']}」，以月建当日为「建」，依次顺行十二位；")
        L.append(f"　今天是{q['day_gz']}日，日支「{q['day_gz'][1]}」，落在第 {JIANCHU.index(q['jianchu'])} 位，故为「{q['jianchu']}」日。")
        L.append("")
        L.append(f"　宜色说明：今日日干「{q['day_gz'][0]}」属{q['wx']}，传统五行配色为{q['color_name']}系。")
        L.append("　穿衣、配饰取这一色系即可，不必刻意。")
        L.append("")
    L.append("　※ 建除与宜忌属传统历法常识，本结果为民俗文化参考，")
    L.append("　　不构成任何决策依据。今天怎么过，由你自己决定。")
    return "\n".join(L)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    long_mode = "--long" in sys.argv
    date_str = args[0] if args else None
    if date_str and len(args) > 1:
        print("用法：python3 riqian.py [YYYY-MM-DD] [--long]")
        sys.exit(1)
    print(render(make_qian(date_str, long_mode)))

if __name__ == "__main__":
    main()
