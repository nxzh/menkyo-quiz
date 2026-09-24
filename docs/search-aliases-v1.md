# 搜索别名表 v1（JA → ZH / EN / VI / PT）

学习者在搜索框里**实际会打**的词，术语表不收、也不该收的那些：口语说法、
简称、外来语写法、异体写法。只服务搜索，**永远不进题干、不进解说、不进任何
译文**。

## 使用规则

1. **本表不是术语表。** 每一行的键是术语表 `assets/术语表_v7_JA-ZH-EN-VI-PT.md`
   的日文词条，一字不差；键不在术语表里，生成器直接报错。译法的唯一依据仍是
   术语表，本表只回答「打什么能搜到它」。
2. **定译不写在这里。** 每种语言的第 0 位（定译）由生成器从术语表取，本表只
   写第 1 位以后的别名。把定译重复写进来没有用，只会造成两份会漂移的记录。
3. **官方资料里被弃用的写法不写在这里。** 术语表的「v7 官方核对结果」四节
   （改从官方译法的 v6 列、官方内部冲突的弃用列、有意不改从官方的官方列、
   官方译法与 ZH 列不一致的官方中文列）本身就是一份被记录下来的别名表，生成器
   自己去读。本表只补这四节之外的口语。
4. **规则 5 的固定区分在这里同样有效**，而且更要紧：搜索把两个词并到一组，就是
   在告诉读者它们是一回事。
   - 停车（停車）/ 驻车（駐車）/ 暂停（一時停止）/ 停留（停止禁止部分）四者
     的任何一个写法都不得做另一个的别名。EN 的 `stop` 只属于 一時停止。
   - 标识（標識）/ 标示（標示）同理。
   - 超车（追越し）/ 超过（追抜き）同理，EN 的 `passing` 只属于 追抜き。
5. **禁用词不做别名。** 「超越」被术语表规则 5 禁用，是因为教材里它同时指
   追越し 和 追抜き —— 把它接到其中任何一组，都会教错一半人。生成器把
   「禁用」一节里的词从所有组里删掉，打这个词的人得到的是字面搜索，不是一个
   看起来很确定的错答案。
6. 一个别名可以属于多个组（打「摩托车」会同时命中 二輪車 与 大型自動二輪車），
   这是对的：搜索给的是候选，不是断言。
7. 多个别名用 `；` 分隔。空单元格表示该语言没有补充，不是遗漏。

## 禁用

| 词 | 语言 | 依据 |
|---|---|---|
| 超越 | ZH | 术语表规则 5：教材中两义混用，NPA 官方中文版用它译 追越し，本表禁用 |

## 别名

| 日文 | ZH | EN | VI | PT |
| --- | --- | --- | --- | --- |
| 信号機 | 红绿灯；交通灯；信号灯杆 | traffic signal；traffic lights；stoplight |  |  |
| 警察官 | 警察 | policeman；cop |  |  |
| 停止線 | 白线 | stop bar |  |  |
| 標識 | 路牌；交通标志 | traffic sign；signboard |  |  |
| 標示 | 路面标线；地面标线 | pavement marking；lane marking |  |  |
| 最高速度 | 限速；速度上限 | speed limit；top speed |  |  |
| 駐停車禁止 | 禁停 | no stopping at all |  |  |
| 車両通行帯 | 车道 | traffic lane；driving lane |  |  |
| 中央線 | 中线；中央分隔线 | centre line；middle line |  |  |
| 交差点 | 十字路口；路口 | junction；crossroads |  |  |
| 環状交差点 | 环岛；转盘 | traffic circle；rotary |  |  |
| 横断歩道 | 斑马线 | zebra crossing |  |  |
| 踏切 | 道口；铁道口 | grade crossing |  |  |
| 歩道 | 便道 | pavement；footpath；walkway |  |  |
| 路肩 | 应急车道 | hard shoulder |  |  |
| トンネル | 涵洞 | underpass |  |  |
| 高速自動車国道 | 高速公路；高速 | expressway；highway；motorway |  |  |
| 自動車専用道路 | 汽车专用路 | motorway-only road |  |  |
| 自転車 | 单车；脚踏车 | pedal bike |  |  |
| 二輪車 | 摩托；机车 | motorbike；two-wheeler |  |  |
| 一般原動機付自転車 | 助力车；小绵羊 | scooter |  |  |
| 特定小型原動機付自転車 | 电动滑板车 | e-scooter；electric kick scooter |  |  |
| 路面電車 | 有轨电车；电车 | tramcar；trolley |  |  |
| 緊急自動車 | 急救车；警车；消防车 | ambulance；fire engine；police car |  |  |
| オートマチック車 | 自动挡；自动波 | automatic car |  |  |
| 徐行 | 慢行 | drive slowly；go slowly |  |  |
| 追越し | 变道超车 | overtake |  |  |
| 追抜き（追い抜く） | 不变道超过 | pass without changing lanes |  |  |
| 進路変更 | 变道；变更车道 | lane change；changing lane |  |  |
| 転回 | 调头；掉转方向 | U turn；turning around |  |  |
| 後退 | 倒车；倒退 | backing up；reverse |  |  |
| 合図 | 打灯；示意 | signalling |  |  |
| 方向指示器 | 转向灯；转弯灯 | turn signal；blinker；indicator |  |  |
| 非常点滅表示灯 | 双闪；危险灯 | hazard lamps；four-way flashers |  |  |
| 警音器 | 鸣笛；按喇叭 | hooter |  |  |
| 追突 | 追尾事故 | rear-ending |  |  |
| エンジンブレーキ | 引擎制动 | engine braking |  |  |
| ハンドブレーキ | 驻车制动；拉手刹 | parking brake；handbrake |  |  |
| ブレーキペダル | 刹车板；制动踏板 | brake |  |  |
| アクセルペダル | 油门 | accelerator；gas pedal |  |  |
| ハンドル | 方向盘；车把 | steering |  |  |
| シートベルト | 保险带 | seatbelt |  |  |
| チャイルドシート | 安全座椅 | child restraint |  |  |
| 二人乗り | 带人；载人 | riding double；pillion |  |  |
| 携帯電話 | 打电话；玩手机 | cellphone；cell phone |  |  |
| 空走距離 | 反应距离 | thinking distance；perception distance |  |  |
| 制動距離 | 刹车距离 | brake distance |  |  |
| 停止距離 | 总停车距离 | total stopping distance |  |  |
| 死角 | 视野盲区 | blind area |  |  |
| 運転免許 | 驾驶证；驾驶执照 | driving licence；driver licence |  |  |
| 仮運転免許（仮免許） | 临时驾驶证 | provisional licence |  |  |
| 免許の停止 | 暂扣驾照 | licence suspension |  |  |
| 免許の取消し | 注销驾照 | licence cancellation |  |  |
| 初心運転者 | 新手；新司机 | novice driver |  |  |
| 初心者マーク | 新手贴 | beginner mark |  |  |
| 高齢者マーク | 老年人标志 | senior mark |  |  |
| 停止表示器材 | 三角牌；警示三角 | warning triangle |  |  |
| 歩行者 | 行人 | people on foot |  |  |
| 児童・幼児 | 小孩 | kids；young children |  |  |
| 運転者 | 司机 | motorist |  |  |
| 同乗者 | 乘客 | rider；occupant |  |  |
| 積載 | 载货；拉货 | cargo；load |  |  |
| 車両総重量 | 总重 | total weight |  |  |
| ナンバープレート | 牌照 | number plate |  |  |
| ブレーキ灯 | 刹车灯 | stop lamp |  |  |

### 日文别名

题库的题干是日文的，读日文的人也会用别的说法搜。

| 日文 | 日文别名 |
| --- | --- |
| 交差点 | 十字路 |
| 環状交差点 | ラウンドアバウト |
| 高速自動車国道 | 高速道路 |
| 警音器 | クラクション；ホーン |
| 方向指示器 | ウインカー；ウィンカー |
| 非常点滅表示灯 | ハザード；ハザードランプ |
| ハンドブレーキ | サイドブレーキ；パーキングブレーキ |
| オートマチック車 | AT車；オートマ |
| 一般原動機付自転車 | 原付 |
| 路面電車 | 市電；チンチン電車 |
| 転回 | Uターン |
| 進路変更 | 車線変更 |
| 仮運転免許（仮免許） | 仮免 |
| 初心者マーク | 若葉マーク |
| 高齢者マーク | もみじマーク；四つ葉マーク |
| 停止表示器材 | 三角表示板；停止表示板 |
| 死角 | ブラインドスポット |

## 待确认

1. **VI / PT 两列是空的，这是有意的。** 术语表的「待确认」第 1 条已经说明：
   官方资料只覆盖约 70 条，VI / PT 的其余译法本身还等着母语者复核。在那之前，
   本表不替这两种语言编造口语 —— 它们靠术语表「v7 官方核对结果」里**已经被
   记录下来的**官方写法（giao lộ、đi chậm、xe đạp gắn động cơ、parada
   momentânea、ciclomotor、passagem de nível 等）就已经能搜到东西，
   这些是生成器自动读出来的，不是猜的。VI / PT 的口语别名，随母语者复核一起补。
2. ZH 的 停车 / 驻车 一组是最容易出事的：中文里「停车」日常兼指两者，而术语表
   规则 5 要求四分。本表因此不给 駐車 任何 ZH 别名。是否该给 駐車 加
   「停放」「长时间停车」这类不会与 停車 混淆的说法，等第一批用户的搜索反馈。
3. 「摩托车」既是 二輪車 的口语，也出现在 大型自動二輪車 / 普通自動二輪車 的
   定译里。搜索给的是候选，多命中几组是对的；如果实际用起来噪声太大，改为
   限制一个查询最多展开的组数，而不是删掉这个别名。
