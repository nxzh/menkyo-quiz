#!/usr/bin/env python3
"""Coverage and distribution report over the question bank.

    python3 tools/stats.py            # whole bank
    python3 tools/stats.py karimen    # one exam scope directory
"""
import json
import pathlib
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent

GROUP_NAMES = {
    "A": "信号灯", "B": "手势信号", "C": "标志标示总论", "D": "个别标志标示",
    "E": "驾驶前心得", "F": "驾照制度", "G": "上车·安全带", "H": "通行区分",
    "I": "紧急车·公交优先", "J": "行人道路", "K": "行人等保护", "L": "停止距离",
    "M": "徐行", "N": "示意·喇叭", "O": "变道·横穿掉头", "P": "超车·让行",
    "Q": "交叉路口", "R": "AT车", "S": "道口", "T": "二轮车", "U": "其他",
}
TRAP_NAMES = {
    "N": "无陷阱", "SW": "条件互换", "EI": "例外捏造", "EO": "例外省略",
    "SS": "相似标志混淆", "AB": "绝对化措辞", "EX": "条件扩大",
    "NU": "数字替换", "OR": "顺序互换", "SC": "情景判断", "NR": "要素缺漏",
}


def table(title, counter, total, names=None):
    print(f"\n## {title}")
    width = max((len(k) for k in counter), default=4)
    for key, n in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])):
        label = f" {names[key]}" if names and key in names else ""
        bar = "█" * round(n / max(total, 1) * 40)
        print(f"  {key:<{width}}{label:<16} {n:>4}  {n / total:>5.1%} {bar}")


def main(argv):
    sub = argv[1] if len(argv) > 1 else ""
    base = ROOT / "questions" / sub if sub else ROOT / "questions"
    items = []
    for p in sorted(base.rglob("batch-*.json")):
        items += json.loads(p.read_text(encoding="utf-8"))
    if not items:
        print(f"no questions under {base}")
        return 0

    n = len(items)
    wrong = [q for q in items if q["answer"] is False]
    print(f"# {n} questions")
    print(f"  ○ {sum(1 for q in items if q['answer'])}  "
          f"× {len(wrong)}")
    print(f"  image questions {sum(1 for q in items if q['question_type'] != 'text')} "
          f"({sum(1 for q in items if q['question_type'] != 'text') / n:.0%}) "
          "— what the fingerprint set gives; no quota — spec v8 §9.3")
    print(f"  verify:true {sum(1 for q in items if q.get('verify'))}")

    table("知识点组", Counter(q["group"] for q in items), n, GROUP_NAMES)
    table("教則 KP", Counter(q["kp"] for q in items), n)
    table("陷阱（×题内）", Counter(q["trap_type"] for q in wrong), max(len(wrong), 1), TRAP_NAMES)
    table("题型", Counter(q["question_type"] for q in items), n)
    table("难度", Counter(str(q["difficulty"]) for q in items), n)

    # 规范 v8 §9.3：陷阱分布不设配额，按指纹集合的实测分布出题。
    # 下表把实测值与 §4.3 在 507 个指纹上量到的比例并列，作为对照，不作合格判定。
    print("\n## 陷阱配比 vs 规范 §4.3 实测")
    measured = {"EI": 0.30, "SW": 0.18, "SS": 0.15, "NU": 0.03}
    for code, ref in measured.items():
        got = sum(1 for q in wrong if q["trap_type"] == code) / max(len(wrong), 1)
        print(f"  {code} {got:.1%} (§4.3 实测 {ref:.0%})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
