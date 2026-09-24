# Verify log

Every question carrying `"verify": true`, what could not be confirmed, and where it
would be confirmed. A question stays on this list until the source is in hand; the
build ships it, flagged, rather than guessing a number.

Two sources the project does not hold locally account for most of this list: the
**道路交通法施行令** and the **道路交通法施行規則**. Several figures that a learner
thinks of as coming from the 教則 are in fact delegated to those, and the 教則 does
not restate them.

| question | fingerprint | what is unconfirmed | where it would be confirmed |
|---|---|---|---|
| `K5-4-416` | `QF-5-4-A-N-19` | Stopping distance ≈44 m at 60 km/h. The 教則 has no stopping-distance table; 第5章第4節2 gives only the definitions and the wet-and-worn doubling. The only numeric figures anywhere are the expressway following distances in 第7章第2節2(4). | A 警察庁 or 県警 stopping-distance table, or the 教則's own 参考 figures in an edition that carries them |
| `K5-4-417` | `QF-5-4-D-NU-03` | Same table — the question is the number-substituted mirror of the above. | ditto |
| `K5-4-418` | `QF-5-4-A-N-26` | Stopping distance ≈20 m at 40 km/h. Not in the 教則 or the 道交法. | ditto |
| `K5-4-425` | `QF-5-4-A-N-08` | That the 法定最高速度 is the same for passenger and goods vehicles. 道交法第22条 delegates the figure to 政令. | 施行令第11条 |
| `K5-4-426` | `QF-5-4-A-N-15` | 一般原動機付自転車 30 km/h. The figure *is* stated in 教則第5章第4節1(2) and 付表3（1）25(2), but the 教則 PDF held here is the 令和6年9月4日 edition and cannot reflect the 2026-09-01 施行令 revision. | 施行令第11条 as amended 2026-09-01 |
| `KS-403` | `QF-付3-D-EX-01` | Same 30 km/h figure, which is what makes the statement false. | ditto |
| `K4-2-621` | `QF-4-2-A-N-06` | What the AT-only condition on a 大型二輪免許 actually covers. 道交法第91条 authorises conditions but does not define them. | 施行規則第24条 |
| `K4-2-637` | `QF-4-2-A-N-12` | The 10-passenger ceiling for a 普通自動車. 道交法第3条 delegates the vehicle classes to 内閣府令; the 教則 nowhere states the number. | 施行規則第2条 |
| `K4-2-646` | `QF-4-2-D-NU-02` | The same 10 / 11 boundary, from the other side. | ditto |
| `K5-1-506` | `QF-5-5-A-N-09` | That the signal for moving off is the same as the right-turn signal. 教則第5章第1節5(2) says only 「方向指示器などによって」; the method table is delegated. | 施行令別表第4 |
| `K5-1-706` | `QF-5-1-A-N-09` | That a child seat goes in the rear when the front passenger seat has an airbag. The 教則 mentions エアバッグ once, at 第5章第1節3(1), and only about seat belts; 第5章第1節4 requires a seat matched to the child and fitted per the maker's instructions, and says nothing about position. | 道交法第71条の3 guidance, or the 警察庁 child-seat material |
| `KM-204` | `QF-付3-D-EI-04` | That a 通学通園バス falls inside 「路線バス等」. 道交法第20条の2第1項 says 「その他の政令で定める自動車」. | 施行令第27条の2 |
| `KL-649` | `QF-教則外-A-N-01` | The civil-liability limb of the three responsibilities. Criminal and administrative liability are in the 道交法; civil liability rests on 自賠法第3条 / 民法第709条, which are outside the sources this bank may use. | 自賠法第3条 / 民法第709条 |
