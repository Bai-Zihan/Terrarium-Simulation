# Hardscape Grid Backlog

This note preserves the later grid-based hardscape design. The current game
uses percentage-based hardscape coverage. Do not implement this grid model
until planting, container selection, and the percentage hardscape rules have
settled.

## Why Defer The Grid

The current simulation is a global-pool model: water, nutrients, gases, plants,
algae, grazers, and microbes are stored as whole-terrarium values. A grid turns
the surface into a spatial simulation. That means each cell can have separate
occupation, moisture, shade, planting space, and growth direction. This is a
larger model change, not just a richer renderer.

## Suggested Surface Model

- Default surface: 5x5 cells for the current 1L cylinder.
- Future containers can choose grid dimensions based on usable base area.
- Each cell stores occupancy, moisture bias, shade bias, plantability, and
  optional plant or hardscape id.
- Coordinates should use readable labels like A1, A2, B1, B2.

Example:

```text
A1 A2 A3 A4 A5
B1 B2 B3 B4 B5
C1 C2 C3 C4 C5
D1 D2 D3 D4 D5
E1 E2 E3 E4 E5
```

## Future Commands

```text
hardscape grid
hardscape place pebble A2 1cell
hardscape place slate C3 3cells leaning_north
hardscape pick H01
plant place fittonia B3
```

## Future Data Shape

```text
SurfaceGrid
  rows
  cols
  cells[]

SurfaceCell
  coord
  hardscape_id
  plant_id
  plantable
  moisture_bias
  shade
  slope
```

## Simulation Hooks

- Plantable area becomes a count of unblocked cells instead of a percentage.
- Surface evaporation depends on exposed cells and cover type.
- Moss and microbes can gain bonuses along damp stone edges.
- Tall or leaning objects can add directional shade.
- Plant growth direction can prefer nearby open cells, moist edges, or light.

## Migration Path

1. Keep percentage hardscape as the source of gameplay in the current version.
2. Add plant selection and planting commands against global plantable area.
3. Add container selection so base area can influence grid dimensions.
4. Convert existing percentage hardscape objects into approximate grid
   footprints when the grid feature is introduced.
5. Preserve old saves by deriving grid occupancy from stored coverage values.
