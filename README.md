# Terrarium Simulation

[中文](#中文) | [English](#english)

## 中文

Terrarium Simulation 是一个终端优先的封闭生态瓶制作与模拟游戏。玩家先像真实制作生态瓶一样选择容器、铺基质、放纱网、润湿土壤、摆放石头或沉木、种植物、加入小型动物，最后封瓶。封瓶后，系统会按照游戏时间自动运行，并输出可观察到的生态变化。

这个项目的核心不是提前告诉玩家“这瓶一定会活”或者“这瓶一定会死”，而是让玩家自由制作，再通过封瓶后的模拟去观察水分、光照、温度、空气、营养、植物、动物和分解过程之间的反馈。

### 当前状态

目前已经可以体验从制作到模拟的完整 CLI 流程：

- 选择不同容器，包括小瓶、1L 直立瓶、大瓶、横放瓶和长条低矮容器
- 按层铺设基质和土壤，并支持混合比例、坡度和挖出
- 可选放入纱网、湿润土壤、喷水
- 设置窗户方向、瓶子朝向、苔藓灯和外部遮阳伞
- 摆放石头、沉木、树皮、颗粒铺面等硬景
- 在土面、硬景顶部、侧面、裂缝、凹槽或下侧种植植物
- 加入跳虫、鼠妇、螨、线虫、微型蜗牛等小型动物
- 封瓶后自动模拟，多个瓶子可以同时存在
- 查看、暂停、恢复、删除已经封瓶的生态瓶
- 出现可见事件时自动打印观察日志

项目现在仍然是原型阶段，但模拟核心已经比较完整。后续更适合继续扩展图形界面、伪 3D 像素风视图、更多生物和更细的观察工具。

### 安装与运行

在项目目录中可以直接运行：

```powershell
python -m terrarium shell
```

如果想把 `terrarium` 安装成系统命令：

```powershell
.\scripts\install-command.ps1
```

安装后打开一个新的终端，就可以在任意目录运行：

```powershell
terrarium
```

批量模拟仍然可用：

```powershell
terrarium run --ticks 168 --interval 12
```

这表示运行 168 个模拟小时，并每隔 12 个模拟小时输出一次状态。

也可以打包成 Windows 可执行文件：

```powershell
.\scripts\build-windows-exe.ps1
```

生成结果会放在 `dist\terrarium.exe`。

### 基本玩法

进入 shell 后，可以直接输入命令。支持多行粘贴，也支持用分号在一行里连接多个命令：

```text
moisten 30ml; spray 5; seal
```

一个典型的稳定生态瓶配方：

```text
make stable_umbrella_test
container set wide_jar
placement window east
placement face 90
placement umbrella 125% center leaning_west
placement lamp 230 0.18 schedule 18-21
substrate add drainage 1.6cm leca=70,pumice=30 slope_x=0.2 slope_y=-0.1
mesh
substrate add soil 4.0cm peat_moss=45,compost=20,sphagnum_moss=20,perlite=15 slope_x=0.5 slope_y=-0.2
substrate add amendment 0.5cm akadama=50,perlite=30,kanuma=20 slope_x=0.3 slope_y=-0.1
moisten 72ml
spray 5
hardscape place driftwood 10% center arch x=48 y=55 angle=35 tilt=14
plant add cushion_moss 7% surface x=45 y=68
plant add sheet_moss 5% hardscape:H01:groove
plant add fittonia_mini 5% surface x=35 y=36
plant add fittonia_white 5% surface x=58 y=38
animal add springtail 32 soil x=48 y=52
animal add dwarf_white_isopod 6 leaf_litter x=56 y=56
seal
```

封瓶后可以观察：

```text
bottles
bottle status B01
bottle plants B01
bottle placement B01 status
```

### 玩家可以控制的内容

制作阶段尽量保持自由。玩家可以跳过大多数步骤，也可以做一个不太合理的瓶子。游戏不会在种植时就强行判断“是否能活”，通常只检查基本限制，例如：

- 容器空间是否足够
- 基质层顺序是否合理
- 植物是否满足最小种植面积
- 坐标是否落在容器范围内
- 硬景、植物和动物是否发生明显冲突

真正的成败留到封瓶后的模拟中体现。

封瓶后，玩家可以：

```text
bottles
bottle status B01
bottle plants B01
bottle pause B01
bottle resume B01
bottle remove B01
make second_bottle
```

已经封瓶的生态瓶会在后台继续模拟。为了避免过多瓶子同时运行，也可以手动暂停某个瓶子。

### 容器

容器决定容量、底面积、高度和空间形状。当前有：

| key | 容器 | 容量 | 高度 | 形状 |
| --- | --- | ---: | ---: | --- |
| `tiny_vial` | Tiny 150ml vial | 150ml | 9cm | 圆形 |
| `nano_jar` | Nano 300ml jar | 300ml | 8cm | 圆形 |
| `standard_1l` | Standard 1L upright jar | 1000ml | 16.7cm | 圆形 |
| `wide_jar` | Wide 1.5L jar | 1500ml | 14cm | 圆形 |
| `tall_2l` | Tall 2L display jar | 2000ml | 24cm | 圆形 |
| `horizontal_jar` | Horizontal 1.2L long jar | 1200ml | 8cm | 矩形 |
| `long_low_tank` | Long low 800ml tank | 800ml | 6cm | 矩形 |

容器空间按 3D 预算计算。水、基质、土壤、硬景、植物根系、植物冠层和动物都会占空间，剩余部分才是空气体积。

### 基质、土壤和铺设顺序

基质层顺序不能颠倒，但每层都可以不选。推荐顺序是：

1. 排水与隔水层
2. 净化与缓冲层
3. 核心保湿与营养层，也就是中层土壤
4. 颗粒土与调节介质

命令示例：

```text
substrate add drainage 2cm leca=70,pumice=30
substrate add purification 5% activated_charcoal=100
substrate add soil 4cm peat_moss=50,compost=30,perlite=20 slope=0.6,-0.2
substrate add amendment 0.8cm akadama=45,kanuma=25,perlite=30
substrate dig 1cm
```

当前材料：

| 材料 | 层级 | 主要作用 |
| --- | --- | --- |
| `leca` | 排水层 | 陶粒，轻质、多孔、透气，主要制造底部排水空间 |
| `pumice` | 排水层 | 浮石，保留少量水分并维持孔隙 |
| `volcanic_rock` | 排水层 | 火山岩，结构稳定，也可作为铺面石 |
| `activated_charcoal` | 净化层 | 活性炭，吸附异味和部分污染 |
| `peat_moss` | 土壤层 | 泥炭土，强保水、偏酸、有营养 |
| `sphagnum_moss` | 土壤层 | 水苔，强保水、透气较好、营养低 |
| `compost` | 土壤层 | 腐叶土，营养高，但腐败和虫害风险也更高 |
| `akadama` | 调节介质 | 赤玉土，保水和透气较均衡 |
| `kanuma` | 调节介质 | 鹿沼土，轻质偏酸，适合部分喜酸植物 |
| `perlite` | 调节介质 | 珍珠岩，几乎不供养分，主要提升透气 |
| `vermiculite` | 调节介质 | 蛭石，提高保水并缓冲肥分流失 |

注意：结构介质本身不一定有酸碱度和营养。当前只有真正的土壤材料参与土壤 pH 和营养计算。

### 纱网、湿润和喷水

纱网是可选层，用于隔开排水层和上方土壤：

```text
mesh
```

种植前可以湿润土壤，单位是毫升：

```text
moisten 60ml
```

喷水按“下”计算。当前假设每喷一下约为 0.8ml：

```text
spray 5
```

### 光照和摆放

玩家可以选择窗户方向，也可以指定瓶子朝向窗户的角度：

```text
placement window east
placement face 90
```

角度规则：

| 角度 | 方向 |
| ---: | --- |
| 0 | 北 |
| 90 | 东 |
| 180 | 南 |
| 270 | 西 |

还可以加入苔藓灯：

```text
placement lamp 230 0.18 schedule 18-21
```

外部遮阳伞用于调节直射和散射光。它不是瓶内装饰，不占容器空间，也不减少种植面积。遮阳伞面积按瓶子投影面积计算，范围是 105% 到 180%，默认 120%：

```text
placement umbrella 125% center leaning_west
placement umbrella 135% x=55 y=70 angle=180 tilt=20
placement umbrella off
```

季节和天气不是玩家直接指定的内容。游戏会根据日期和随机天气影响白天长度、直射光、散射光和热量。

### 硬景和装饰物

硬景会影响可种植面积、局部遮阴、潮湿边缘、动物藏身处、附着面和空间占用：

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

硬景不是简单圆形。长条沉木、椭圆石、倾斜石片都有方向和碰撞影响。植物可以根据种类贴附在顶部、侧面、裂缝、凹槽或下侧。

### 植物

种植时，游戏只检查最小面积和可用空间，不提前判断长期适应性。长期生存由模拟决定。

```text
plant add fittonia_mini 5% surface x=35 y=36
plant add cushion_moss 4% hardscape:H01:groove
plant add rabbit_foot_fern 5% hardscape:H01:side
plant prune P01 roots 20%
```

当前植物类别包括：

- 地生蕨类：`lemon_button_fern`, `maidenhair_fern`, `heart_fern`, `silver_pteris`, `dwarf_boston_fern`
- 附生蕨类：`rabbit_foot_fern`, `mini_bird_nest_fern`, `creeping_microsorum`, `pyrrosia`, `button_epiphyte_fern`
- 苔藓：`cushion_moss`, `sheet_moss`, `mood_moss`, `fern_moss`, `sphagnum_live`
- 地衣：`reindeer_lichen`, `cup_lichen`, `crust_lichen`, `foliose_lichen`
- 网纹草：`fittonia_white`, `fittonia_pink`, `fittonia_red`, `fittonia_mini`, `fittonia_josanii`
- 小型食虫植物：`drosera_spatulata`, `drosera_capensis`, `pinguicula_esseriana`, `pinguicula_moranensis`, `utricularia_sandersonii`
- 小型凤梨：`neoregelia_fireball`, `neoregelia_liliputiana`, `cryptanthus_dwarf`, `tillandsia_ionantha`, `tillandsia_bulbosa`, `tillandsia_fuchsii`
- 小型兰花：`masdevallia_mini`, `pleurothallis`, `restrepia`, `jewel_orchid_mini`, `bulbophyllum_mini`
- 匍匐植物：`peperomia_prostrata`, `pilea_glauca`, `ficus_pumila_minima`, `selaginella`, `marcgravia_mini`

每种植物都有自己的最小面积、成熟面积、高度、根长、湿度偏好、温度偏好、光照偏好、水分偏好、营养偏好、透气偏好、生长速率、繁殖方式和资源消耗。

### 动物

动物是可选的。它们主要承担分解、清理、消费或扰动的角色。当前暂时没有捕食者，捕食者和更复杂的食物网放在后续计划中。

```text
animal add springtail 30 soil
animal add dwarf_white_isopod 8 leaf_litter
animal add micro_snail 3 moss x=45 y=60
animal remove A01
```

当前动物：

| key | 类型 | 主要作用 |
| --- | --- | --- |
| `springtail` | 分解者 | 控制霉菌和软腐殖质 |
| `dwarf_white_isopod` | 分解者 | 处理落叶和腐木 |
| `tropical_isopod` | 分解者 | 处理落叶和树皮 |
| `soil_mite` | 分解者 | 消耗真菌和细碎腐殖质 |
| `enchytraeid_worm` | 分解者 | 处理潮湿有机质 |
| `nematode_mix` | 微型消费者 | 消耗微生物和溶解有机质 |
| `micro_snail` | 小型消费者 | 吃生物膜和嫩藻 |
| `tiny_slug` | 小型消费者 | 吃生物膜和柔软植物组织 |
| `aquatic_ostracod` | 小型消费者 | 吃湿润生物膜和悬浮碎屑 |
| `fungus_gnat_larva` | 小型消费者 | 吃真菌、腐殖质和细根 |

动物也有生存状态、种群趋势和繁殖进度。繁殖被刻意做得比较谨慎，会受到空间、食物、氧气、水分和环境压力限制。

### 模拟逻辑

每个 tick 表示 1 个模拟小时。封瓶后，系统会按时间倍率自动推进，并在出现标志性事件时打印观察日志。

模型主要考虑：

- 光照：窗户方向、瓶子朝向、直射/散射、昼夜、季节、天气、苔藓灯、外部遮阳伞
- 温度：随光照、窗户方向、季节、天气和灯光变化
- 水循环：土壤孔隙水、游离水、水汽、凝结水和表面湿润度
- 碳循环：光合作用消耗二氧化碳并释放氧气，呼吸和分解消耗氧气并释放二氧化碳
- 营养循环：土壤释放营养，植物和藻类消耗营养，分解过程把有机物重新转化为可用资源
- 可见生态：生物膜、霉菌、落叶层、根区氧气、叶片损伤和动物活动
- 局部环境：坐标、坡度、低洼处、硬景阴影、附着面、植物重叠和动物活动空间

自动日志尽量报告玩家能看到的证据，而不是直接输出内部诊断。例如：

```text
[B01] survival day 4 10:00 - INCIDENT: a sharper sun patch crosses the planting surface
[B01] survival day 6 12:00 - FLORA: Mini fittonia has a paler new tip near the window side
[B01] survival day 8 00:00 - DAILY: plants look steady; springtails are still active under the litter
```

死亡定义是：所有明确加入的植物和动物全部死亡。死亡后自动模拟会停止。

### 开发与测试

```powershell
python -m py_compile terrarium\*.py
python -m unittest discover -s tests
```

项目核心模拟主要在 `terrarium/model.py`，命令行交互在 `terrarium/cli.py`，终端展示在 `terrarium/render.py`。

## English

Terrarium Simulation is a terminal-first closed terrarium crafting and ecosystem simulation game. The player builds a bottle step by step, choosing the container, substrate layers, mesh screen, moisture, hardscape, plants, animals, window placement, lamp, and external shade. After sealing the bottle, the simulation runs automatically and reports visible ecological changes.

The goal is not to judge a bottle instantly during crafting. Instead, the game gives the player broad freedom, then lets the sealed system reveal whether the choices form a stable ecosystem.

### Current State

The current CLI prototype supports the full loop from crafting to sealed simulation:

- Multiple container sizes, including tiny vials, upright jars, wide jars, tall jars, horizontal jars, and long low tanks
- Ordered substrate layers with mixed material percentages, slopes, and digging
- Optional mesh screen, soil moistening, and misting
- Window direction, terrarium facing angle, moss lamp, and external shade umbrella
- Stones, driftwood, bark, gravel patches, and decorative hardscape
- Planting on soil, hardscape tops, sides, cracks, grooves, and undersides
- Small animal groups such as springtails, isopods, mites, nematodes, and micro snails
- Automatic sealed-bottle simulation
- Multiple bottles running in the background
- Pause, resume, inspect, and remove sealed bottles
- Visible event reports instead of only raw numbers

The project is still a prototype, but the simulation core is already usable. Future work can build a graphical interface, pseudo-3D pixel view, more species, predators, and richer observation tools on top of the existing model.

### Install And Run

From the project directory:

```powershell
python -m terrarium shell
```

To install the `terrarium` command:

```powershell
.\scripts\install-command.ps1
```

Open a new terminal after installation, then run:

```powershell
terrarium
```

Batch simulation is also available:

```powershell
terrarium run --ticks 168 --interval 12
```

This runs 168 simulated hours and prints a status every 12 simulated hours.

To build a standalone Windows executable:

```powershell
.\scripts\build-windows-exe.ps1
```

The result is written to `dist\terrarium.exe`.

### Basic Gameplay

The interactive shell accepts one command per line. You can paste multiple lines, or join commands with semicolons:

```text
moisten 30ml; spray 5; seal
```

Example stable bottle recipe:

```text
make stable_umbrella_test
container set wide_jar
placement window east
placement face 90
placement umbrella 125% center leaning_west
placement lamp 230 0.18 schedule 18-21
substrate add drainage 1.6cm leca=70,pumice=30 slope_x=0.2 slope_y=-0.1
mesh
substrate add soil 4.0cm peat_moss=45,compost=20,sphagnum_moss=20,perlite=15 slope_x=0.5 slope_y=-0.2
substrate add amendment 0.5cm akadama=50,perlite=30,kanuma=20 slope_x=0.3 slope_y=-0.1
moisten 72ml
spray 5
hardscape place driftwood 10% center arch x=48 y=55 angle=35 tilt=14
plant add cushion_moss 7% surface x=45 y=68
plant add sheet_moss 5% hardscape:H01:groove
plant add fittonia_mini 5% surface x=35 y=36
plant add fittonia_white 5% surface x=58 y=38
animal add springtail 32 soil x=48 y=52
animal add dwarf_white_isopod 6 leaf_litter x=56 y=56
seal
```

After sealing:

```text
bottles
bottle status B01
bottle plants B01
bottle placement B01 status
```

### Player Controls

Crafting is intentionally permissive. Most steps are optional, and the game does not block every potentially bad design. It checks basic constraints such as:

- container capacity
- substrate layer order
- minimum planting area
- coordinates inside the footprint
- severe hardscape, plant, or animal collisions

The long-term result is decided by the sealed simulation.

After sealing, players can manage background bottles:

```text
bottles
bottle status B01
bottle plants B01
bottle pause B01
bottle resume B01
bottle remove B01
make second_bottle
```

### Containers

Containers define capacity, base area, height, and footprint shape.

| key | container | capacity | height | shape |
| --- | --- | ---: | ---: | --- |
| `tiny_vial` | Tiny 150ml vial | 150ml | 9cm | round |
| `nano_jar` | Nano 300ml jar | 300ml | 8cm | round |
| `standard_1l` | Standard 1L upright jar | 1000ml | 16.7cm | round |
| `wide_jar` | Wide 1.5L jar | 1500ml | 14cm | round |
| `tall_2l` | Tall 2L display jar | 2000ml | 24cm | round |
| `horizontal_jar` | Horizontal 1.2L long jar | 1200ml | 8cm | rectangular |
| `long_low_tank` | Long low 800ml tank | 800ml | 6cm | rectangular |

The container budget is three-dimensional. Water, layers, soil, hardscape, roots, canopy, and animals all occupy space. Whatever remains becomes air volume.

### Substrates And Soil

Substrate layers have an enforced order, but each layer is optional:

1. drainage and water barrier
2. purification and buffer
3. core moisture and nutrition layer
4. granular amendments

Examples:

```text
substrate add drainage 2cm leca=70,pumice=30
substrate add purification 5% activated_charcoal=100
substrate add soil 4cm peat_moss=50,compost=30,perlite=20 slope=0.6,-0.2
substrate add amendment 0.8cm akadama=45,kanuma=25,perlite=30
substrate dig 1cm
```

Available materials:

| material | layer | purpose |
| --- | --- | --- |
| `leca` | drainage | lightweight clay aggregate for drainage and air space |
| `pumice` | drainage | porous stone with moderate water retention |
| `volcanic_rock` | drainage | stable mineral structure |
| `activated_charcoal` | purification | absorbs odor and some pollutants |
| `peat_moss` | soil | acidic, water-retentive, moderately nutritious |
| `sphagnum_moss` | soil | very water-retentive, airy, low nutrition |
| `compost` | soil | nutrient-rich but riskier for rot |
| `akadama` | amendment | balanced moisture and aeration |
| `kanuma` | amendment | light, acidic mineral medium |
| `perlite` | amendment | improves aeration, low nutrition |
| `vermiculite` | amendment | improves water retention and nutrient buffering |

Not every substrate has pH or nutrition. Structural media mainly affect water, aeration, and space.

### Mesh, Moistening, And Misting

The optional mesh screen separates drainage from upper soil:

```text
mesh
```

Moisten soil in milliliters:

```text
moisten 60ml
```

Mist by spray count. The current assumption is about 0.8ml per spray:

```text
spray 5
```

### Light And Placement

Players can choose the window direction and the terrarium angle facing the window:

```text
placement window east
placement face 90
```

Angle convention:

| angle | direction |
| ---: | --- |
| 0 | north |
| 90 | east |
| 180 | south |
| 270 | west |

Moss lamps have an angle, intensity, and schedule:

```text
placement lamp 230 0.18 schedule 18-21
```

The shade umbrella is an external light-control object, not an in-bottle hardscape. It does not occupy bottle volume or reduce plantable area. Its canopy area is measured as a percentage of the bottle projection, from 105% to 180%, with a default of 120%:

```text
placement umbrella 125% center leaning_west
placement umbrella 135% x=55 y=70 angle=180 tilt=20
placement umbrella off
```

Season and weather are simulated, not directly chosen by the player. They affect day length, direct light, diffuse light, and heat.

### Hardscape

Hardscape affects plantable area, local shade, moist edges, attachment surfaces, animal shelter, and volume:

```text
hardscape place driftwood 12% west leaning_east x=35 y=55 angle=25
hardscape place slate 14% center flat tilt=22 angle=120
hardscape pick H01
```

Available hardscape:

| key | type | shape | attachment surfaces |
| --- | --- | --- | --- |
| `pebble` | stone | small rounded cluster | top |
| `river_stone` | stone | smooth oval | top, side, crack |
| `slate` | stone | flat shard | top, side, crack, underside |
| `lava_rock` | stone | porous mound | top, side, crack |
| `pumice_stone` | stone | light porous mound | top, side, crack |
| `gravel_patch` | surface | scattered grains | top |
| `bark_chip` | wood | loose flakes | top, side, groove |
| `driftwood` | wood | branch or arch | top, side, groove, underside |
| `cork_bark` | wood | curved bark ridge | top, side, groove, underside |
| `ceramic_figure` | decor | solid ornament | top |

Hardscape is directional. Long driftwood, oval stones, and tilted slate shards affect collisions and local microclimates differently.

### Plants

Planting only checks minimum area and available space. Long-term suitability is handled by simulation.

```text
plant add fittonia_mini 5% surface x=35 y=36
plant add cushion_moss 4% hardscape:H01:groove
plant add rabbit_foot_fern 5% hardscape:H01:side
plant prune P01 roots 20%
```

Plant categories include:

- terrestrial ferns
- epiphytic ferns
- mosses
- lichens
- fittonias
- small carnivorous plants
- miniature bromeliads
- air bromeliads
- miniature orchids
- creeping plants

Each plant has its own area, mature spread, height, root length, humidity preference, temperature preference, light preference, water preference, nutrition preference, aeration preference, growth rate, reproduction mode, and resource use.

### Animals

Animals are optional. They act as decomposers, cleaners, consumers, or disturbance sources. Predators are planned for future work but are not currently active.

```text
animal add springtail 30 soil
animal add dwarf_white_isopod 8 leaf_litter
animal add micro_snail 3 moss x=45 y=60
animal remove A01
```

Available animals:

| key | role | purpose |
| --- | --- | --- |
| `springtail` | decomposer | controls mold and soft detritus |
| `dwarf_white_isopod` | decomposer | processes leaf litter and decaying wood |
| `tropical_isopod` | decomposer | processes leaf litter and bark |
| `soil_mite` | decomposer | consumes fungi and fine detritus |
| `enchytraeid_worm` | decomposer | processes wet organic matter |
| `nematode_mix` | micro-consumer | consumes microbes and dissolved organics |
| `micro_snail` | small consumer | eats biofilm and tender algae |
| `tiny_slug` | small consumer | eats biofilm and soft plant tissue |
| `aquatic_ostracod` | small consumer | eats wet biofilm and suspended detritus |
| `fungus_gnat_larva` | small consumer | eats fungus, detritus, and fine roots |

Animal survival and reproduction are limited by space, food, oxygen, water, and habitat quality.

### Simulation Model

Each tick is one simulated hour. After sealing, the game advances automatically and prints visible events.

The model includes:

- light: window direction, terrarium angle, direct and diffuse light, day/night cycle, season, weather, moss lamp, and external shade umbrella
- temperature: follows light, window warmth, season, weather, and lamp heat
- water cycle: pore water, free water, vapor, condensation, surface wetness
- carbon cycle: photosynthesis, respiration, decomposition, oxygen, and carbon dioxide
- nutrients: soil release, plant uptake, algae uptake, decomposition, and waste
- visible ecology: biofilm, mold, litter, root-zone oxygen, plant marks, and animal activity
- local environment: coordinates, slope, low spots, hardscape shade, attachment surfaces, plant overlap, and animal activity area

Automatic reports are written as visible observations rather than pure internal diagnostics:

```text
[B01] survival day 4 10:00 - INCIDENT: a sharper sun patch crosses the planting surface
[B01] survival day 6 12:00 - FLORA: Mini fittonia has a paler new tip near the window side
[B01] survival day 8 00:00 - DAILY: plants look steady; springtails are still active under the litter
```

A sealed terrarium is considered dead when all explicit plants and animals are dead. Dead bottles stop simulating automatically.

### Development And Tests

```powershell
python -m py_compile terrarium\*.py
python -m unittest discover -s tests
```

The core simulation lives in `terrarium/model.py`, CLI interaction in `terrarium/cli.py`, and terminal rendering in `terrarium/render.py`.
