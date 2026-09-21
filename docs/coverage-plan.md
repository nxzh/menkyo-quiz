# 仮免 1000 — coverage plan

1000 questions across the first-stage (仮免) knowledge range, in 50 batches of 20.
Allocation is weighted by how much of the 教則 each area occupies and by the gaps
found in the reference-bank analysis (three independent source sets, ≈371 deduplicated
question fingerprints).

| 教則 | area | group | questions | batches |
|---|---|---|---|---|
| 1-1 | 基本心得 | U | 20 | 04 |
| 1-2 ＋付表1・2 | 信号灯・标示牌 | A | 60 | 11–13 |
| 1-2 | 标志标示总论 | C | 25 | 14 |
| 1-3 ＋付表1(3) | 手势信号 | B | 25 | 15 |
| 1-4 | 禁止行为 | U | 20 | 04 |
| 2・3章 | 行人、自行车、特定小型原付 | J | 45 | 03, 16 |
| 4-1 | 驾驶前注意 | E | 40 | 17–18 |
| 4-2 | 驾照制度 | F | 55 | 19–21 |
| 5-1 | 安全出发、安全带 | G | 40 | 22–23 |
| 5-2 | 通行场所、通行带 | H, I | 80 | 24–27 |
| 5-3 | 行人等保护 | K | 65 | 03, 28–30 |
| 5-4 | 速度、徐行、停止距离、车距 | L, M | 70 | 02, 31–33 |
| 5-5 | 示意、变道、横穿掉头 | N, O | 55 | 34–36 |
| 5-6 | 超车、让行 | P | 50 | 37–39 |
| 5-7-1〜3 | 交叉路口 | Q | 65 | 40–42 |
| 5-7-4 | 环状交叉路口 | Q | 25 | 01, 43 |
| 5-9 | AT车等 | R | 30 | 44 |
| 6-1 | 铁路道口 | S | 30 | 45 |
| 6-2 | 坡道、弯道 | U | 20 | 04 |
| 8章 | 二轮车 | T | 35 | 46–47 |
| 付表3 | 个别标志、路面标示（图片题） | D | 120 | 05–10, 48–49 |
| 教則外 | 道交法（责任、点数、年龄） | U | 25 | 50 |
| | | | **1000** | |

Image questions are 120 of 1000 = 12%, the low end of the 12–20% the reference banks
show. Hand-signal and traffic-light images are capped at 8 (0.8%).

## Batch order

The reference-bank analysis found areas that all three source sets miss entirely.
Those run first, because they are where an original bank adds the most and where no
existing material can be leaned on.

1. **batch-01** 5-7-4 环状交叉路口 — 0 of 550 reference questions, but the 教則 gives
   it a full section and it is the rule foreign licence holders most often break.
2. **batch-02** 5-4 速度 — every reference question predates the 2026-09-01 施行令
   revision. The only knowledge point all three sources get wrong.
3. **batch-03** 2・3章 行人・自行车・特定小型原付 ＋ 5-3-7 自行车保护 (2026-04 rules) —
   too new to appear in any reference bank.
4. **batch-04** 1-1 基本心得 ＋ 1-4 禁止行为 ＋ 6-2 坡道弯道 — thin everywhere.
5. **batch-05** 付表3 標識 image questions — 規制標識, 警戒標識 and 指示標識, with the
   similar-sign confusion (SS) trap that only image questions can carry.

From batch-06 on, the well-covered areas in the order of the table above.

## Delivered so far

| batch | 教則 | questions | ○ / × | notes |
|---|---|---|---|---|
| 01 | 5-7-4 環状交差点, 5-5-1 合図, 5-7-1 | 20 | 10 / 10 | 道交法 35条の2・37条の2・53条 |
| 02 | 5-4 速度・車間距離・ブレーキ・徐行 | 20 | 10 / 10 | 2 carry `verify: true` on the 施行令第11条 speeds |
| 03 | 5-3 歩行者等の保護, 3-1, 3-3 特定小型原付・自転車 | 20 | 10 / 10 | includes 5-3-7, empty in all three source sets |
| 04 | 1-1 心構え, 1-4 禁止行為, 6-2 坂道・カーブ | 20 | 10 / 10 | |
| 05 | 付表3（1） 標識 | 20 | 10 / 10 | 20 SVGs under `signs/`, all `question_type: sign` |

## Statutory state this plan assumes

| item | state |
|---|---|
| 教則 | 令和6年9月4日告示第37号 |
| 生活道路の法定速度 30km/h | in force 2026-09-01 (施行令第11条). Any question quoting a 法定速度 figure carries `verify: true` until 施行令 is checked directly. |
| 2026-04-01 | 仮免 minimum age 17 years 6 months; passing a bicycle on its right; 自転車青切符 |
| 2025-10-01 | 外免切替 knowledge test became 50 text questions, 45 to pass. No image questions in 外免 scope. |
