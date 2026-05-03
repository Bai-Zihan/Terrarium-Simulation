# Terrarium Sim

一个先从终端开始的生态瓶模拟游戏。当前版本偏“硬核计算风格”：你可以在 CLI 里观察光照、温度、水分、营养盐、氧气、二氧化碳、腐殖质、毒性和种群生物量之间的动态反馈。

后续的精美 UI 模式应该复用 `terrarium/model.py`，把展示层换成图形界面即可。

## 快速开始

```powershell
python -m terrarium run --ticks 168 --interval 24
```

输出会显示一个终端仪表盘：

```text
TICK 00024  HOUR 00  LIGHT 0.00  TEMP 20.10C  STABILITY 089/100
ATM   O2  [############........] 0.615   CO2 [########............] 0.384
SOIL  H2O [###############.....] 0.741   NUT [############........] 0.575
```

## 常用命令

批处理运行一周：

```powershell
python -m terrarium run --ticks 168 --interval 12
```

输出紧凑日志，适合重定向分析：

```powershell
python -m terrarium run --ticks 240 --log --interval 6 --seed 42
```

导出每小时快照：

```powershell
python -m terrarium run --ticks 240 --export sim.jsonl
```

进入交互式模拟器：

```powershell
python -m terrarium shell --seed 42
```

交互式命令：

```text
status
step 12
run 72 12
set water 0.82
set light_intensity 0.65
add grazers 3
save state.json
quit
```

## 模型概要

- 每个 tick 表示 1 个模拟小时。
- 光照按昼夜周期变化，温度跟随光照滞后变化。
- 植物和藻类进行光合作用：消耗水分、营养盐和二氧化碳，增加氧气和生物量。
- 植食者消耗植物/藻类，产生生长、呼吸和废弃物。
- 微生物分解腐殖质，释放营养盐，同时消耗氧气并产生二氧化碳。
- 低氧、干旱、缺营养、高毒性、过冷/过热会造成种群压力。

## 开发验证

```powershell
python -m py_compile terrarium\*.py
python -m unittest discover -s tests
```
