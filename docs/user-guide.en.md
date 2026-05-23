# Terrarium Simulation User Guide

Terrarium Simulation is a terminal-first closed terrarium crafting and ecosystem simulation game. The player builds a bottle step by step, choosing the container, substrate layers, mesh screen, moisture, hardscape, plants, animals, window placement, lamp, and external shade. After sealing the bottle, the simulation runs automatically and reports visible ecological changes.

The project is not meant to be a simple number checker. It is a crafting and observation game. Players can make very free-form bottles, and the sealed ecosystem answers over time whether those choices can stay stable.

## Running The Game

After installing the command, you can start the game from any directory:

```powershell
terrarium
```

From the project directory, you can also run:

```powershell
python -m terrarium shell
```

Batch simulation is available with:

```powershell
terrarium run --ticks 168 --interval 12
```

This means: run 168 simulated hours and print a status every 12 simulated hours.

The interactive shell supports pasted multi-line recipes. It also supports multiple commands on one line when separated by semicolons:

```text
moisten 30ml; spray 5; seal
```

## What Players Control

Players mainly control two things: the crafting choices before sealing, and the management of sealed bottles afterward.

During crafting, almost every step is optional. A player can skip hardscape, animals, lights, umbrellas, or mesh. The game does not try to decide immediately whether the design is "good". It only checks basic constraints, such as available space, valid layer order, coordinates inside the container footprint, and minimum planting area. The real outcome is left to the sealed simulation.

A typical crafting flow looks like this:

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

After sealing, existing bottles keep simulating in the background. Players can inspect, pause, resume, remove, or create another bottle:

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

## Containers

Containers define total capacity, base area, height, and footprint shape.

| key | name | capacity | height | shape |
| --- | --- | ---: | ---: | --- |
| `tiny_vial` | Tiny 150ml vial | 150ml | 9cm | round |
| `nano_jar` | Nano 300ml jar | 300ml | 8cm | round |
| `standard_1l` | Standard 1L upright jar | 1000ml | 16.7cm | round |
| `wide_jar` | Wide 1.5L jar | 1500ml | 14cm | round |
| `tall_2l` | Tall 2L display jar | 2000ml | 24cm | round |
| `horizontal_jar` | Horizontal 1.2L long jar | 1200ml | 8cm | rectangular |
| `long_low_tank` | Long low 800ml tank | 800ml | 6cm | rectangular |

The bottle is treated as three-dimensional space. Substrate, soil, water, roots, canopy, hardscape, and animals all occupy volume. The remaining volume becomes air.

## Substrates And Soil

Substrate layers must follow a fixed order, but every layer is optional:

1. drainage and water barrier
2. purification and buffer
3. core moisture and nutrition layer
4. granular amendments

The player can add mixed materials by percentage and can dig out only the current top layer:

```text
substrate add drainage 2cm leca=70,pumice=30
substrate add purification 5% activated_charcoal=100
substrate add soil 4cm peat_moss=50,compost=30,perlite=20 slope=0.6,-0.2
substrate add amendment 0.8cm akadama=45,kanuma=25,perlite=30
substrate dig 1cm
```

Available materials:

| material | layer | role |
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

Structural media do not all have pH or nutrition. Many materials mainly change water retention, aeration, drainage, and available pore space.

## Mesh, Moistening, And Misting

The mesh screen is optional. It separates drainage from upper soil and can reduce substrate migration:

```text
mesh
```

Soil moistening is measured in milliliters:

```text
moisten 60ml
```

Misting is measured by spray count. The current assumption is about 0.8ml per spray:

```text
spray 5
```

## Light And Placement

Players choose the window direction and the angle of the bottle facing the window:

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

The player can change the window or facing direction later:

```text
bottle placement B01 window south
bottle placement B01 face 135
```

Moss lamps have an angle, intensity, and schedule:

```text
placement lamp 230 0.18 schedule 18-21
```

The external shade umbrella is a small scaled-down object outside the bottle. It does not occupy bottle volume or reduce plantable area. Instead, it changes the amount and character of incoming light, similar to adjusting direct and diffuse sunlight:

```text
placement umbrella 125% center leaning_west
placement umbrella 135% x=55 y=70 angle=180 tilt=20
placement umbrella off
```

Season and weather are simulated automatically. They are not chosen directly by the player. They affect day length, direct light, diffuse light, heat, and condensation.

## Hardscape And Decoration

Hardscape affects planting space, local shade, moist edges, attachment surfaces, animal shelter, and volume:

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

Hardscape has orientation. Long driftwood, oval stones, and tilted slate shards use directional collision and can create different microclimates around their top, side, crack, groove, or underside surfaces.

## Plants

Planting checks minimum area and available space. It does not decide whether the plant will thrive. Survival and growth are handled after sealing.

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

Each plant has its own footprint, mature spread, height, root length, humidity preference, temperature preference, light preference, water preference, nutrition preference, aeration preference, growth rate, reproduction mode, and resource use.

Plants can also gain local orientation. They may lean toward light, grow close to a hardscape side, or be visually pushed by nearby stones or wood. These details are used by the simulation and will also matter for future pseudo-3D views.

## Animals

Animals are optional. They can act as decomposers, cleaners, small consumers, or disturbance sources. Predators are planned for future work but are not active yet.

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

Animal survival and reproduction are limited by space, food, oxygen, water, habitat quality, and crowding. Reproduction is intentionally conservative so the bottle does not fill with animals too easily.

## Simulation Logic

Each tick is one simulated hour. After sealing, bottles advance automatically while the game is open. Multiple bottles can run at the same time, and players can pause bottles to reduce simulation load.

The model includes:

- light: window direction, bottle angle, direct and diffuse light, day/night cycle, season, weather, moss lamp, and external shade umbrella
- temperature: follows light, window warmth, season, weather, and lamp heat
- water cycle: pore water, free water, vapor, condensation, surface wetness, dry patches, and waterlogging
- carbon cycle: photosynthesis, respiration, decomposition, oxygen, and carbon dioxide
- nutrients: soil release, plant uptake, algae uptake, decomposition, waste, and root-zone depletion
- local environment: coordinates, slope, low spots, hardscape shade, attachment surfaces, plant overlap, root crowding, and animal activity area
- visible ecology: biofilm, mold, litter, plant marks, condensation, algae film, root stress, and animal movement

Automatic reports avoid exposing every hidden number. They focus on things the player could plausibly observe:

```text
[B01] survival day 4 10:00 - INCIDENT: a sharper sun patch crosses the planting surface
[B01] survival day 6 12:00 - FLORA: Mini fittonia has a paler new tip near the window side
[B01] survival day 8 00:00 - DAILY: plants look steady; springtails are still active under the litter
```

A sealed terrarium is considered dead when all explicit plants and animals are dead. Dead bottles stop simulating automatically.

## Saving And Loading

The installed game keeps standalone bottle data in the player's terrarium save directory. When the game starts, it imports existing bottle saves and can run them automatically depending on their state.

Useful commands:

```text
save stable_bottle.json
load stable_bottle.json
bottles
bottle status B01
bottle remove B01
```

The goal is for the game to feel like a small installed system command rather than a script that only works from the project directory.

## Development And Tests

For development:

```powershell
python -m py_compile terrarium\*.py
python -m unittest discover -s tests
```

The core simulation lives in `terrarium/model.py`, CLI interaction in `terrarium/cli.py`, and terminal rendering in `terrarium/render.py`.
