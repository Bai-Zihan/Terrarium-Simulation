# Terrarium Simulation 用户指南

Terrarium Simulation 是一个从命令行开始的生态瓶制作与模拟游戏。玩家先像真正制作生态瓶一样选择容器、铺基质、放纱网、润湿土壤、摆放石头或沉木、种植物、加入小型动物，最后封瓶。封瓶后，系统会按照游戏时间自动运行，观察水分、光照、温度、空气、营养、植物和动物之间的变化。

这个项目目前不是一个“只看数值”的计算器，而是一个偏制作、偏观察的 CLI 游戏原型。它的核心乐趣是：玩家可以很自由地做一个瓶子，但瓶子能否长期稳定，要由封瓶后的生态过程来回答。

## 运行方式

安装命令后，可以在任意目录输入：

```powershell
terrarium
```

进入交互式游戏。也可以在项目目录中使用：

```powershell
python -m terrarium shell
```

如果只想批量跑模拟，可以使用：

```powershell
terrarium run --ticks 168 --interval 12
```

这里的意思是：运行 168 个模拟小时，并且每隔 12 个模拟小时打印一次状态。

交互模式支持多行粘贴，也支持一行里用分号连接多个命令：

```text
moisten 30ml; spray 5; seal
```

## 玩家可以操控什么

玩家主要操控两件事：制作阶段的选择，以及封瓶后的管理。

制作阶段可以完全自由地跳过任何可选步骤。也就是说，玩家可以不放硬景、不放动物、不放灯、不放伞，甚至可以做一个很怪的瓶子。游戏不会在制作阶段强行判断“这能不能活”，只会检查一些基本限制，例如空间是否够、材料顺序是否合理、植物是否有最小种植面积。真正的好坏留到封瓶后的模拟中体现。

常用制作流程大致是：

```text
make my_bottle
container set wide_jar
placement window east
placement face 90
placement umbrella 125% center leaning_west
placement lamp 230 0.18 schedule 18-21
substrate add drainage 1.6cm leca=70,pumice=30
mesh
substrate add soil 4.0cm peat_moss=45,compost=20,sphagnum_moss=20,perlite=15
moisten 72ml
spray 5
hardscape place driftwood 10% center arch x=48 y=55 angle=35 tilt=14
plant add fittonia_mini 5% surface x=35 y=36
animal add springtail 32 soil x=48 y=52
seal
```

封瓶以后，已有生态瓶会继续运行。玩家可以查看、暂停、恢复、删除某个瓶子，也可以继续制作另一个瓶子：

```text
bottles
bottle status B01
bottle plants B01
bottle placement B01 status
bottle pause B01
bottle resume B01
bottle remove B01
make second_bottle
```

## 容器

容器决定总容量、底面积、高度和可用空间。当前有直立圆形瓶，也有横向或长条形容器。

| key | 名称 | 容量 | 高度 | 形状 |
| --- | --- | ---: | ---: | --- |
| `tiny_vial` | Tiny 150ml vial | 150ml | 9cm | 圆形 |
| `nano_jar` | Nano 300ml jar | 300ml | 8cm | 圆形 |
| `standard_1l` | Standard 1L upright jar | 1000ml | 16.7cm | 圆形 |
| `wide_jar` | Wide 1.5L jar | 1500ml | 14cm | 圆形 |
| `tall_2l` | Tall 2L display jar | 2000ml | 24cm | 圆形 |
| `horizontal_jar` | Horizontal 1.2L long jar | 1200ml | 8cm | 矩形 |
| `long_low_tank` | Long low 800ml tank | 800ml | 6cm | 矩形 |

容器空间是 3D 预算，不只看表面积。水、基质、土壤、硬景、根系、冠层、动物都会占用空间，剩余空间会成为空气体积。

## 基质和土壤

基质按层铺设，顺序不能颠倒，但每一层都可以不选。

推荐顺序是：

1. 排水与隔水层
2. 净化与缓冲层
3. 核心保湿与营养层，也就是中层土壤
4. 颗粒土与调节介质

玩家可以多次添加同一类层，也可以混合添加。混合比例使用百分制：

```text
substrate add drainage 2cm leca=70,pumice=30
substrate add soil 4cm peat_moss=50,compost=30,perlite=20
substrate add amendment 0.8cm akadama=45,kanuma=25,perlite=30
```

也可以设置坡度，让土层不是完全水平：

```text
substrate add soil 4cm peat_moss=60,perlite=40 slope=0.6,-0.2
```

当前材料：

| 材料 | 层级 | 主要作用 | 保水 | 透气 | 土壤 pH/营养 |
| --- | --- | --- | ---: | ---: | --- |
| `leca` | 排水层 | 轻质陶粒，制造底部排水空间 | 2 | 10 | 无 |
| `pumice` | 排水层 | 轻石，保留少量水分并保持孔隙 | 4 | 8 | 无 |
| `volcanic_rock` | 排水层 | 火山岩，结构稳定 | 2 | 8 | 无 |
| `activated_charcoal` | 净化层 | 活性炭，吸附异味和部分污染 | 3 | 7 | 无 |
| `peat_moss` | 土壤层 | 泥炭土，强保水、偏酸、有营养 | 9 | 3 | pH 4.2，营养 6 |
| `sphagnum_moss` | 土壤层 | 水苔，强保水、透气较好、营养低 | 10 | 6 | pH 4.8，营养 1 |
| `compost` | 土壤层 | 腐叶土，营养高但更容易带来腐败风险 | 7 | 4 | pH 6.5，营养 10 |
| `akadama` | 调节介质 | 赤玉土，保水和透气较均衡 | 6 | 7 | 无 |
| `kanuma` | 调节介质 | 鹿沼土，轻质偏酸，适合喜酸植物 | 5 | 8 | 无 |
| `perlite` | 调节介质 | 珍珠岩，几乎不供养分，主要增加透气 | 1 | 9 | 无 |
| `vermiculite` | 调节介质 | 蛭石，提高保水和缓冲肥分流失 | 8 | 5 | 无 |

注意：不是所有基质都有酸碱度和营养。当前只有真正的土壤材料参与土壤 pH 和营养计算，陶粒、浮石、珍珠岩这类结构介质主要影响水、空气和空间。

## 纱网、湿润和喷水

纱网是可选层，用来隔开排水层和上方土壤，减少细土下漏：

```text
mesh
```

种植前可以湿润土壤，单位是毫升：

```text
moisten 60ml
```

也可以喷水，单位是“下”。当前假设每喷一下约等于 0.8ml：

```text
spray 5
```

## 光照和摆放

玩家可以决定生态瓶靠近哪个方向的窗户，以及瓶身朝向窗户的角度。

```text
placement window east
placement face 90
```

角度规则是：

| 角度 | 方向 |
| ---: | --- |
| 0 | 北 |
| 90 | 东 |
| 180 | 南 |
| 270 | 西 |

玩家还可以放置苔藓灯。灯有方向、强度和时间表：

```text
placement lamp 230 0.18 schedule 18-21
```

遮阳伞不是瓶内装饰，而是外部调光媒介。它的面积按瓶子投影面积计算，范围是 105% 到 180%，默认 120%。它会削弱直射光、轻微影响散射光，并降低直射导致的升温。

```text
placement umbrella 125% center leaning_west
placement umbrella 135% x=55 y=70 angle=180 tilt=20
placement umbrella off
```

季节和天气不是玩家直接指定的内容。游戏会根据日期和随机天气影响日照长度、直射强度、散射光和热量。

## 硬景和装饰物

硬景会影响可种植面积、局部遮阴、潮湿边缘、附着面、动物藏身处和空间占用。玩家可以指定覆盖面积、位置、朝向、角度和倾斜：

```text
hardscape place driftwood 12% west leaning_east x=35 y=55 angle=25
hardscape place slate 14% center flat tilt=22 angle=120
hardscape pick H01
```

当前硬景：

| key | 类型 | 形状 | 可附着面 |
| --- | --- | --- | --- |
| `pebble` | 石 | 小卵石簇 | 顶部 |
| `river_stone` | 石 | 光滑椭圆石 | 顶部、侧面、裂缝 |
| `slate` | 石 | 扁平石片 | 顶部、侧面、裂缝、下侧 |
| `lava_rock` | 石 | 多孔火山岩 | 顶部、侧面、裂缝 |
| `pumice_stone` | 石 | 轻质多孔石 | 顶部、侧面、裂缝 |
| `gravel_patch` | 表面材料 | 颗粒铺面 | 顶部 |
| `bark_chip` | 木 | 树皮片 | 顶部、侧面、凹槽 |
| `driftwood` | 木 | 沉木或拱枝 | 顶部、侧面、凹槽、下侧 |
| `cork_bark` | 木 | 软木皮 | 顶部、侧面、凹槽、下侧 |
| `ceramic_figure` | 装饰 | 陶瓷摆件 | 顶部 |

在实现上，石头和沉木不是简单圆形。长条沉木、椭圆石、倾斜石片都有方向和碰撞影响；植物可以贴附在顶部、侧面、裂缝、凹槽或下侧等不同表面。

## 植物

种植时，游戏只检查最小种植面积和剩余空间，不会提前禁止“可能不适合”的组合。植物是否适应，会在封瓶后的模拟中体现。

植物可以种在土面，也可以种在硬景表面：

```text
plant add fittonia_mini 5% surface x=35 y=36
plant add cushion_moss 4% hardscape:H01:groove
plant add rabbit_foot_fern 5% hardscape:H01:side
```

也可以剪根：

```text
plant prune P01 roots 20%
```

剪根会影响根系恢复、生长压力和后续状态，但不是一个单纯的好坏开关。

当前植物类型包括：

| 类别 | 代表植物 |
| --- | --- |
| 地生蕨类 | `lemon_button_fern`, `maidenhair_fern`, `heart_fern`, `silver_pteris`, `dwarf_boston_fern` |
| 附生蕨类 | `rabbit_foot_fern`, `mini_bird_nest_fern`, `creeping_microsorum`, `pyrrosia`, `button_epiphyte_fern` |
| 苔藓 | `cushion_moss`, `sheet_moss`, `mood_moss`, `fern_moss`, `sphagnum_live` |
| 地衣 | `reindeer_lichen`, `cup_lichen`, `crust_lichen`, `foliose_lichen` |
| 网纹草 | `fittonia_white`, `fittonia_pink`, `fittonia_red`, `fittonia_mini`, `fittonia_josanii` |
| 小型食虫植物 | `drosera_spatulata`, `drosera_capensis`, `pinguicula_esseriana`, `pinguicula_moranensis`, `utricularia_sandersonii` |
| 小型凤梨 | `neoregelia_fireball`, `neoregelia_liliputiana`, `cryptanthus_dwarf`, `tillandsia_ionantha`, `tillandsia_bulbosa`, `tillandsia_fuchsii` |
| 小型兰花 | `masdevallia_mini`, `pleurothallis`, `restrepia`, `jewel_orchid_mini`, `bulbophyllum_mini` |
| 匍匐植物 | `peperomia_prostrata`, `pilea_glauca`, `ficus_pumila_minima`, `selaginella`, `marcgravia_mini` |

每种植物都有自己的最小面积、成熟面积、高度、根长、湿度偏好、温度偏好、光照偏好、水分偏好、营养偏好、透气偏好、生长速率、繁殖方式和资源消耗特征。

## 动物

动物是可选的。它们主要承担分解、清理、消费或扰动的角色。加入动物需要考虑数量、空间、食物和环境。当前暂时没有捕食者，捕食者和更复杂的食物网被放进后续计划。

添加动物示例：

```text
animal add springtail 30 soil
animal add dwarf_white_isopod 8 leaf_litter
animal add micro_snail 3 moss x=45 y=60
animal remove A01
```

当前动物：

| key | 类型 | 数量范围 | 主要食物 |
| --- | --- | ---: | --- |
| `springtail` | 分解者 | 5-350 | 霉菌和软腐殖质 |
| `dwarf_white_isopod` | 分解者 | 2-80 | 落叶和腐木 |
| `tropical_isopod` | 分解者 | 2-45 | 落叶和树皮 |
| `soil_mite` | 分解者 | 10-400 | 真菌和细碎腐殖质 |
| `enchytraeid_worm` | 分解者 | 3-120 | 潮湿有机质 |
| `nematode_mix` | 微型消费者 | 20-900 | 微生物和溶解有机质 |
| `micro_snail` | 小型消费者 | 1-24 | 生物膜和嫩藻 |
| `tiny_slug` | 小型消费者 | 1-10 | 生物膜和柔软植物组织 |
| `aquatic_ostracod` | 小型消费者 | 5-180 | 湿润生物膜和悬浮碎屑 |
| `fungus_gnat_larva` | 小型消费者 | 1-40 | 真菌、腐殖质和细根 |

动物也有生存状态、生长趋势和繁殖进度，但繁殖被刻意做得比较慎重。空间不足、食物不足、氧气差、过湿或过干都会限制繁殖。

## 模拟逻辑

每个 tick 代表 1 个模拟小时。封瓶后，游戏会按时间倍率自动推进。默认情况下，模拟不是 1:1 真实时间，也不会快到瞬间跳过所有变化。目标是让玩家能看到关键事件，而不是一直盯着数字。

### 光照、昼夜、季节和天气

光照由几个部分组成：

- 窗户方向带来的直射光和散射光
- 瓶子面向窗户的角度
- 白天和夜晚的周期
- 自动季节变化
- 随机天气，如晴天、多云、阴天、雨天
- 苔藓灯补光
- 外部遮阳伞削弱直射并柔化光线

光照会影响光合作用，也会影响温度。直射越强，瓶内靠窗侧越容易升温和变干；散射光更温和，但效率不同。

### 水循环

水不只是一个单一数值。模型会区分：

- 已加入的水
- 土壤和基质孔隙里的水
- 游离水
- 空气中的水汽
- 玻璃上的凝结水
- 表面湿润程度

排水层、土壤保水性、孔隙率、硬景遮挡、坡度和温度都会影响水在系统里的位置。比如低洼处可能更湿，高处更容易先干。

### 空气和碳循环

植物和藻类在有光时进行光合作用：消耗二氧化碳，释放氧气，并增加生物量。夜晚和低光时，植物、动物、藻类和微生物都会呼吸：消耗氧气，释放二氧化碳。

腐殖质分解也会消耗氧气、释放二氧化碳和营养。封闭瓶中空气体积有限，所以过多动物、过多腐殖质、积水或腐败都可能造成氧气下降或二氧化碳累积。

### 营养、腐殖质和微生物

土壤和腐叶土会提供营养，但营养不是越多越好。营养高、潮湿、通气差时，更容易出现霉菌、腐败和毒性压力。

分解者会处理霉菌、落叶和腐殖质，把一部分有机物重新转化为可用营养。但它们自己也会呼吸、排泄、占空间，并且需要食物和合适环境。

### 植物状态

每株植物会记录：

- 健康状态
- 生长阶段
- 生长速率
- 根系状态
- 叶片、茎、根尖等可见状态
- 是否有可分株或蔓延趋势
- 是否受到霉菌、啃食、拥挤、干旱、缺氧等压力

不同植物的资源使用不同。例如网纹草、苔藓、地衣、兰花、食虫植物对光、水、营养和透气性的偏好不同，因此同一个瓶子里它们的表现不会完全一样。

### 动物状态

动物群会记录：

- 存活数量
- 生存状态
- 种群趋势
- 活动区域
- 移动距离
- 食物摄取、同化、废物和呼吸
- 繁殖进度

动物会根据局部环境移动，比如寻找更湿的边缘、更多腐殖质、硬景下方或有生物膜的位置。它们也会受到空间拥挤、食物不足和空气质量的限制。

### 局部环境和空间

游戏使用 x/y 坐标来表示种植和摆放位置，范围通常是 0 到 100。对于圆形容器，坐标必须落在圆形底面里。

局部环境会考虑：

- 土层高度和坡度
- 当前位置是否低洼
- 附近硬景的阴影
- 硬景表面的顶部、侧面、裂缝、凹槽或下侧
- 植物之间的冠层和根系重叠
- 动物活动区域是否重叠
- 局部湿度、通气、遮蔽、生物膜和霉菌

因此，两个植物即使用同一种材料和同一个容器，只要位置不同，也可能出现不同的状态。

## 自动报告

封瓶后，游戏会在出现标志性变化时自动打印信息。报告尽量偏向“玩家能看到的证据”，而不是直接告诉玩家内部公式。

例如：

```text
[B01] survival day 4 10:00 - INCIDENT: a sharper sun patch crosses the planting surface
[B01] survival day 6 12:00 - FLORA: Mini fittonia has a paler new tip near the window side
[B01] survival day 8 00:00 - DAILY: plants look steady; springtails are still active under the litter
```

玩家仍然可以用 `status` 或 `bottle status B01` 查看完整仪表盘，但自动日志更像观察记录。

## 死亡和停止

一个封闭生态瓶的死亡定义是：所有明确加入的植物和动物都死亡。生态瓶死亡后，自动模拟会停止。

这意味着游戏不是简单地让某个数值低于阈值就结束，而是等实际生命对象全部失败后才判定死亡。

## 当前边界和后续方向

当前版本已经能走通从制作到封瓶、自动模拟、多瓶管理、暂停恢复和删除的流程。它也已经有 3D 空间预算、局部环境、硬景附着面、植物和动物状态、自动日志、季节天气和调光系统。

仍然可以继续扩展的方向包括：

- 图形界面或伪 3D 像素风视图
- 更丰富的植物视觉状态
- 捕食者和更完整的食物网
- 更复杂的长期演替
- 更真实的病虫害、菌群和藻类竞争
- 更细的玩家观察工具，而不是直接显示诊断答案

项目当前的重点不是追求现实生态的完全复刻，而是做一个“足够可信、可观察、可调试、好玩的封闭生态瓶模拟器”。
