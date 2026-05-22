from __future__ import annotations

from collections.abc import Iterable
from shutil import get_terminal_size

from .model import (
    ANIMALS,
    HARDSCAPES,
    PLANTS,
    SUBSTRATES,
    SUBSTRATE_LAYER_NAMES,
    Terrarium,
    TerrariumState,
    WEATHER_PROFILES,
    soil_layer_stats,
    substrate_layer_stats,
)


SHADES = " .:-=+*#%@"


def bar(value: float, width: int = 20) -> str:
    value = max(0.0, min(1.0, value))
    filled = round(value * width)
    return "#" * filled + "." * (width - filled)


def population_bar(value: float, scale: float, width: int = 20) -> str:
    return bar(min(1.0, value / scale), width)


def spark(values: Iterable[float], width: int = 36) -> str:
    items = list(values)[-width:]
    if not items:
        return ""
    low = min(items)
    high = max(items)
    if high - low < 1e-9:
        return SHADES[len(SHADES) // 2] * len(items)
    cells = []
    for value in items:
        idx = round(((value - low) / (high - low)) * (len(SHADES) - 1))
        cells.append(SHADES[idx])
    return "".join(cells)


def render_dashboard(sim: Terrarium, compact: bool = False) -> str:
    state = sim.state
    width = get_terminal_size((96, 24)).columns
    rule = "-" * min(width, 96)
    stability = sim.stability_score()
    history = sim.history
    oxygen_trend = spark(s.oxygen for s in history)
    plant_trend = spark(s.plants for s in history)
    events = " ".join(state.events) if state.events else "nominal"
    used_height = sim.substrate_height_cm()
    remaining_height = sim.remaining_substrate_height_cm()
    top_layer = state.substrate_layers[-1].layer_kind if state.substrate_layers else "none"
    mesh_count = sim.mesh_layer_count()
    hardscape = sim.hardscape_profile()
    planted_area = sim.planted_area_percent()
    remaining_plantable = sim.remaining_plantable_area_percent()
    space = sim.volume_profile()
    phase = f"sealed@{state.sealed_tick:05d}" if state.sealed and state.sealed_tick is not None else "open"
    lamp_end = (state.moss_lamp_start_hour + state.moss_lamp_duration_hours) % 24
    lamp = (
        f"{state.moss_lamp_angle_deg:03.0f}@{state.moss_lamp_intensity:0.2f}"
        f"/{state.moss_lamp_start_hour:02d}-{lamp_end:02d}"
        if state.moss_lamp_enabled
        else "off"
    )

    lines = [
        rule,
        (
            f"TICK {state.tick:05d}  HOUR {state.hour:02d}  "
            f"LIGHT {state.light:0.2f} SRC {sim.current_light_compass_deg():03.0f}/{state.sun_altitude_deg:02.0f}  "
            f"TEMP {state.temperature:05.2f}C  "
            f"STABILITY {stability:03d}/100  PHASE {phase}"
        ),
        (
            f"PLACE window {state.window_direction}@{state.window_azimuth_deg:03.0f}  "
            f"face {state.window_facing_deg:03.0f}  "
            f"daylight {state.season}/{state.weather_state}  "
            f"source {sim.current_light_compass_deg():03.0f}  lamp {lamp}  heat +{state.placement_heat_bias:0.1f}C"
        ),
        rule,
        f"ATM   O2  [{bar(state.oxygen)}] {state.oxygen:0.3f}   CO2 [{bar(state.carbon_dioxide)}] {state.carbon_dioxide:0.3f}",
        f"SOIL  H2O [{bar(state.water)}] {state.water:0.3f}   NUT [{bar(state.nutrients)}] {state.nutrients:0.3f}",
        f"WASTE DET [{bar(state.detritus)}] {state.detritus:0.3f}   TOX [{bar(state.toxicity)}] {state.toxicity:0.3f}",
        f"VISIBLE BIO [{bar(state.biofilm)}] {state.biofilm:0.3f}   MOLD [{bar(state.mold_pressure)}] {state.mold_pressure:0.3f}   ROOT_O2 {state.root_zone_oxygen:0.3f}",
        (
            f"SUBSTRATE {used_height:05.2f}/{state.container.height_cm:04.1f}cm  "
            f"FREE {remaining_height:05.2f}cm  TOP {top_layer}  "
            f"MESH {mesh_count:02d}  WATERED {state.soil_moistened_ml + state.sprayed_ml:0.0f}ml"
        ),
        (
            f"HARDSCAPE cover {hardscape['coverage_percent']:04.1f}%  "
            f"plantable {hardscape['plantable_percent']:04.1f}%  "
            f"shade {float(hardscape['shade']) * 100:04.1f}%  bias {hardscape['growth_bias']}"
        ),
        (
            f"PLANTINGS used {planted_area:04.1f}%  free {remaining_plantable:04.1f}%  "
            f"count {len(state.plantings):02d} alive {sim.living_planting_count():02d}"
        ),
        (
            f"ANIMALS groups {len(state.animal_groups):02d}  "
            f"count {sim.animal_count_total():04d} alive {sim.living_animal_count():04d}"
        ),
        (
            f"SPACE used {space['used_container_ml']:05.1f}/{space['capacity_ml']:04.0f}ml  "
            f"air {space['total_air_ml']:05.1f}ml  free_water {space['free_water_ml']:05.1f}ml"
        ),
        rule,
        f"PLANT  [{population_bar(state.plants, 180)}] {state.plants:07.2f} biomass",
        f"ALGAE  [{population_bar(state.algae, 90)}] {state.algae:07.2f} biomass",
        f"GRAZER [{population_bar(state.grazers, 45)}] {state.grazers:07.2f} biomass",
        f"MICRO  [{population_bar(state.microbes, 80)}] {state.microbes:07.2f} biomass",
    ]

    if not compact:
        f = state.flux
        lines.extend(
            [
                rule,
                (
                    "FLUX  "
                    f"photo={f.photosynthesis:+0.5f}  resp={f.respiration:+0.5f}  "
                    f"graze={f.grazing:+0.5f}  decay={f.decay:+0.5f}  stress={f.stress:+0.5f}"
                ),
                f"TREND O2     {oxygen_trend}",
                f"TREND PLANT  {plant_trend}",
            ]
        )
        if state.substrate_layers:
            lines.extend([rule, *render_substrate_stack(sim).splitlines()[1:]])
        if state.hardscape_items:
            lines.extend([rule, *render_hardscape(sim).splitlines()[1:]])
        if state.plantings:
            lines.extend([rule, *render_plantings(sim).splitlines()[1:]])
        if state.animal_groups:
            lines.extend([rule, *render_animals(sim).splitlines()[1:]])
        lines.extend([rule, *render_space(sim).splitlines()[1:]])

    lines.extend([rule, f"EVENTS {events}", rule])
    return "\n".join(lines)


def render_seal_report(sim: Terrarium) -> str:
    state = sim.state
    profile = sim.volume_profile()
    hardscape = sim.hardscape_profile()
    sealed_at = state.sealed_tick if state.sealed_tick is not None else state.tick
    water_total = state.soil_moistened_ml + state.sprayed_ml
    lamp_end = (state.moss_lamp_start_hour + state.moss_lamp_duration_hours) % 24
    living_summary = (
        f"{sim.living_planting_count()}/{len(state.plantings)} plantings alive / "
        f"{len(state.animal_groups)} animal groups / "
        f"{sim.living_animal_count()}/{sim.animal_count_total()} animals alive"
    )
    lines = [
        "SEALED TERRARIUM",
        f"  sealed_at_tick {sealed_at:05d}",
        f"  container {state.container.display_name} ({state.container.capacity_ml:0.0f}ml, {state.container.footprint_shape})",
        (
            f"  container {profile['used_container_ml']:0.1f}/{profile['capacity_ml']:0.0f}ml used  "
            f"free {profile['free_container_ml']:0.1f}ml  air {profile['total_air_ml']:0.1f}ml"
        ),
        (
            f"  substrate {sim.substrate_height_cm():0.2f}/{state.container.height_cm:0.2f}cm  "
            f"layers {sum(1 for layer in state.substrate_layers if layer.layer_kind != 'mesh')}  "
            f"mesh {sim.mesh_layer_count()}"
        ),
        (
            f"  water {water_total:0.1f}ml  "
            f"moisten {state.soil_moistened_ml:0.1f}ml  "
            f"spray {state.sprayed_ml:0.1f}ml/{state.spray_count}x"
        ),
        (
            f"  placement window {state.window_direction}@{state.window_azimuth_deg:03.0f}  "
            f"face {state.window_facing_deg:03.0f}  "
            f"daylight {state.season}/{state.weather_state}  "
            f"lamp {'off' if not state.moss_lamp_enabled else f'{state.moss_lamp_angle_deg:03.0f}@{state.moss_lamp_intensity:0.2f}/{state.moss_lamp_start_hour:02d}-{lamp_end:02d}'}"
        ),
        (
            f"  hardscape cover {hardscape['coverage_percent']:0.1f}%  "
            f"plantable {hardscape['plantable_percent']:0.1f}%  "
            f"bias {hardscape['growth_bias']}"
        ),
        (
            f"  plants used {sim.planted_area_percent():0.1f}%  "
            f"free {sim.remaining_plantable_area_percent():0.1f}%"
        ),
        f"  living {living_summary}",
        f"  stability {sim.stability_score():03d}/100",
        "  next step: use step/run/status/save to observe the sealed system",
    ]
    return "\n".join(lines)


def render_placement(sim: Terrarium) -> str:
    state = sim.state
    weather_label = WEATHER_PROFILES.get(state.weather_state, WEATHER_PROFILES["clear"])["label"]
    lamp = "off"
    if state.moss_lamp_enabled:
        end_hour = (state.moss_lamp_start_hour + state.moss_lamp_duration_hours) % 24
        lamp = (
            f"on angle {state.moss_lamp_angle_deg:0.1f}deg "
            f"intensity {state.moss_lamp_intensity:0.2f} "
            f"photoperiod {state.moss_lamp_start_hour:02d}:00-{end_hour:02d}:00"
        )
    umbrella_line = "  shade umbrella off"
    if state.umbrella_enabled:
        umbrella_line = (
            f"  shade umbrella area {state.umbrella_coverage_percent:0.0f}% "
            f"xy {state.umbrella_x_percent:0.0f},{state.umbrella_y_percent:0.0f} "
            f"angle {state.umbrella_angle_deg:0.0f}deg tilt {state.umbrella_tilt_deg:0.0f}deg"
        )
    return "\n".join(
        [
            "PLACEMENT",
            "  angle convention: 0=N, 90=E, 180=S, 270=W",
            (
                f"  window {state.window_direction} "
                f"({state.window_azimuth_deg:0.1f}deg), "
                f"terrarium face toward window {state.window_facing_deg:0.1f}deg"
            ),
            (
                "  window glass unchanged  "
                f"season {state.season} day {state.calendar_day_of_year:03d}  "
                f"weather {weather_label} (auto)"
            ),
            f"  moss lamp {lamp}",
            umbrella_line,
            (
                f"  current source {sim.current_light_compass_deg():0.1f}deg  "
                f"altitude {state.sun_altitude_deg:0.1f}deg  "
                f"light {state.light:0.2f} "
                f"(sun patch {state.window_direct_light:0.2f}, sky glow {state.window_diffuse_light:0.2f}, "
                f"lamp {state.moss_lamp_light:0.2f})  "
                f"heat bias +{state.placement_heat_bias:0.1f}C"
            ),
        ]
    )


def render_space(sim: Terrarium) -> str:
    profile = sim.volume_profile()
    animal_space = sim.animal_spatial_profile()
    lines = [
        (
            f"SPACE used {profile['used_container_ml']:0.1f}/{profile['capacity_ml']:0.0f}ml  "
            f"free {profile['free_container_ml']:0.1f}ml  "
            f"over {profile['overfilled_ml']:0.1f}ml"
        ),
        (
            f"  layers {profile['layer_volume_ml']:0.1f}ml  "
            f"solid {profile['substrate_solid_ml']:0.1f}ml  "
            f"pores {profile['pore_capacity_ml']:0.1f}ml  pore_air {profile['pore_air_ml']:0.1f}ml"
        ),
        (
            f"  water added {profile['water_added_ml']:0.1f}ml  "
            f"moisten {profile['soil_moistened_ml']:0.1f}ml  "
            f"spray {profile['sprayed_ml']:0.1f}ml/{profile['spray_count']:0.0f}x  "
            f"in_pores {profile['water_in_pores_ml']:0.1f}ml  "
            f"free_water {profile['free_water_ml']:0.1f}ml"
        ),
        (
            f"  cycle liquid {profile['liquid_water_ml']:0.1f}ml  "
            f"vapor {profile['vapor_water_ml']:0.1f}ml  "
            f"glass {profile['condensation_ml']:0.1f}ml  "
            f"surface {float(profile['surface_wetness']) * 100:0.0f}%  "
            f"biofilm {float(profile['biofilm']) * 100:0.0f}%  "
            f"mold {float(profile['mold_pressure']) * 100:0.0f}%"
        ),
        (
            f"  hardscape {profile['hardscape_volume_ml']:0.1f}ml  "
            f"roots {profile['plant_root_volume_ml']:0.1f}ml  "
            f"canopy {profile['plant_canopy_volume_ml']:0.1f}ml  "
            f"animals {profile['animal_volume_ml']:0.2f}ml  "
            f"open_air {profile['open_air_ml']:0.1f}ml"
        ),
        (
            f"  animal activity {animal_space['activity_area_cm2']:0.2f}/"
            f"{animal_space['habitat_area_cm2']:0.2f}cm2  "
            f"habitat_space {animal_space['habitat_space_score'] * 100:0.0f}%"
        ),
    ]
    return "\n".join(lines)


def render_plantings(sim: Terrarium) -> str:
    lines = [
        (
            f"PLANTINGS used {sim.planted_area_percent():0.1f}%  "
            f"free {sim.remaining_plantable_area_percent():0.1f}%"
        )
    ]
    if not sim.state.plantings:
        lines.append("  empty")
        return "\n".join(lines)

    for planting in sim.state.plantings:
        definition = PLANTS[planting.plant]
        lines.append(
            f"  {planting.planting_id} {definition.display_name:22s} "
            f"{planting.area_percent:04.1f}%  {planting.site:14s} "
            f"xyz {planting.x_percent:04.1f},{planting.y_percent:04.1f},{planting.z_cm:04.1f}cm  "
            f"ori {planting.yaw_deg:03.0f}/{planting.pitch_deg:03.0f}/{planting.lean_deg:02.0f} {planting.lean_reason or '-'}  "
            f"shape {planting.shape_state}:{planting.footprint_aspect_ratio:0.1f}@{planting.spread_direction_deg:03.0f}  "
            f"roots {planting.root_mass_percent:05.1f}%  "
            f"parts stem {planting.stem_count:02d} leaf {planting.leaf_count:03d} "
            f"new {planting.new_growth_count:02d} dmg {planting.damaged_leaf_count:02d} "
            f"anchor {planting.root_anchor_count:02d} tips {planting.root_tip_count:02d}  "
            f"marks {planting.visible_damage_percent:04.1f}% mold {planting.mold_contact_percent:04.1f}%  "
            f"prune {planting.prune_stress:04.1f}  "
            f"{planting.survival_state}/{planting.growth_stage}  "
            f"grow {planting.growth_rate:0.4f}  "
            f"repro {planting.reproduction_progress:05.1f}%  "
            f"offspring {planting.offspring_potential:02d}  {planting.status}"
        )
    return "\n".join(lines)


def render_plant_growth(sim: Terrarium) -> str:
    lines = [
        (
            f"PLANT GROWTH alive {sim.living_planting_count():d}/{len(sim.state.plantings):d}  "
            f"area {sim.planted_area_percent():0.1f}%  "
            f"free {sim.remaining_plantable_area_percent():0.1f}%"
        )
    ]
    if not sim.state.plantings:
        lines.append("  empty")
        return "\n".join(lines)

    for planting in sim.state.plantings:
        definition = PLANTS[planting.plant]
        age_days = planting.age_ticks / 24.0
        reproductive_age_days = definition.min_reproductive_age_ticks / 24.0
        maturity = planting.area_percent / max(definition.mature_area_percent, 1.0) * 100.0
        lines.extend(
            [
                (
                    f"  {planting.planting_id} {definition.display_name:22s} "
                    f"{planting.survival_state}/{planting.growth_stage}  "
                    f"health {planting.health:05.1f}%  age {age_days:05.1f}d"
                ),
                (
                    f"      area {planting.area_percent:04.1f}%  "
                    f"maturity {maturity:05.1f}%  site {planting.site:14s}  "
                    f"xyz {planting.x_percent:0.1f},{planting.y_percent:0.1f},{planting.z_cm:0.1f}cm  "
                    f"surface {planting.attachment_surface or '-'}  feature {planting.attachment_feature or '-'}  "
                    f"contact {planting.attachment_contact_area_cm2:0.2f}cm2@{planting.attachment_normal_deg:03.0f}"
                ),
                (
                    f"      size footprint {planting.footprint_cm2:0.2f}cm2  "
                    f"height {planting.height_cm:0.1f}cm  "
                    f"root_len {planting.root_length_cm:0.1f}cm  "
                    f"roots {planting.root_mass_percent:05.1f}%/{planting.root_health:05.1f}%  prune {planting.prune_stress:04.1f}  "
                    f"orientation yaw {planting.yaw_deg:03.0f} pitch {planting.pitch_deg:03.0f} "
                    f"lean {planting.lean_deg:02.0f} {planting.lean_reason or '-'}"
                ),
                (
                    f"      shape {planting.shape_state}  aspect {planting.footprint_aspect_ratio:0.2f}  "
                    f"spread_dir {planting.spread_direction_deg:03.0f}"
                ),
                f"      light note {sim.plant_light_observation(planting)}",
                (
                    f"      visible structure stems {planting.stem_count:d}  "
                    f"leaves {planting.leaf_count:d}  new {planting.new_growth_count:d}  "
                    f"damaged {planting.damaged_leaf_count:d}  flowers {planting.flower_count:d}  "
                    f"anchors {planting.root_anchor_count:d}  root_tips {planting.root_tip_count:d}  "
                    f"density {planting.canopy_density_percent:0.1f}%  "
                    f"edge_marks {planting.visible_damage_percent:0.1f}%  "
                    f"mold_contact {planting.mold_contact_percent:0.1f}%"
                ),
                (
                    f"      growth_rate {planting.growth_rate:+0.4f}/h  "
                    f"repro {planting.reproduction_progress:05.1f}%  "
                    f"offspring {planting.offspring_potential:02d}  "
                    f"mode {definition.reproduction_mode}  "
                    f"age_gate {age_days:0.1f}/{reproductive_age_days:0.1f}d"
                ),
            ]
        )
        if planting.last_interaction:
            lines.append(f"      recent visible sign: {planting.last_interaction}")
    return "\n".join(lines)


def render_animals(sim: Terrarium) -> str:
    lines = [
        (
            f"ANIMALS groups {len(sim.state.animal_groups):d}  "
            f"count {sim.animal_count_total():d}  alive {sim.living_animal_count():d}"
        )
    ]
    if not sim.state.animal_groups:
        lines.append("  empty")
        return "\n".join(lines)

    for group in sim.state.animal_groups:
        definition = ANIMALS[group.animal]
        lines.append(
            f"  {group.group_id} {definition.display_name:22s} "
            f"x{group.count:03d}  {group.site:14s} "
            f"xyz {group.x_percent:04.1f},{group.y_percent:04.1f},{group.z_cm:04.1f}cm  "
            f"{definition.role:14s}  {group.survival_state}/{group.population_trend}  "
            f"habitat {group.microhabitat:18s} visible {group.visible_activity:04.1f}%  shelter {group.shelter_use:04.1f}%  "
            f"move {group.movement_state}:{group.distance_moved_cm:0.2f}cm {group.movement_reason or '-'}  "
            f"area {group.activity_area_cm2:0.2f}cm2  "
            f"grow {group.growth_rate:0.4f}  "
            f"repro {group.reproduction_progress:05.1f}%  "
            f"crowd {group.crowding_pressure:04.1f}"
        )
    return "\n".join(lines)


def render_hardscape(sim: Terrarium) -> str:
    profile = sim.hardscape_profile()
    surface_ecology = sim.hardscape_surface_ecology()
    lines = [
        (
            f"HARDSCAPE cover {profile['coverage_percent']:0.1f}%  "
            f"blocked {profile['blocked_percent']:0.1f}%  "
            f"plantable {profile['plantable_percent']:0.1f}%  "
            f"evap_shield {float(profile['evaporation_shield']) * 100:0.1f}%  "
            f"edge_moisture {float(profile['edge_moisture']) * 100:0.1f}%  "
            f"bias {profile['growth_bias']}  "
            f"surface biofilm {surface_ecology['biofilm'] * 100:0.0f}% "
            f"mold {surface_ecology['mold'] * 100:0.0f}% shelter {surface_ecology['shelter'] * 100:0.0f}%"
        )
    ]
    if not sim.state.hardscape_items:
        lines.append("  empty")
        return "\n".join(lines)

    for item in sim.state.hardscape_items:
        definition = HARDSCAPES[item.kind]
        surfaces = ",".join(definition.attach_surfaces) or "-"
        lines.append(
            f"  {item.item_id} {definition.display_name:16s} "
            f"{item.coverage_percent:04.1f}%  {item.position:9s} {item.orientation:13s} "
            f"xyz {item.x_percent:04.1f},{item.y_percent:04.1f},{item.z_top_cm:04.1f}cm  "
            f"angle {item.rotation_deg:03.0f} tilt {item.tilt_deg:+03.0f}  "
            f"aspect {definition.footprint_aspect_ratio:0.1f} geometry {definition.geometry_profile}  "
            f"surfaces {surfaces}  "
            f"{definition.shape}"
        )
        if definition.surface_features:
            surface_notes = []
            for surface in definition.attach_surfaces:
                traits = sim._hardscape_surface_traits(item, surface)
                surface_notes.append(
                    f"{surface}:wet {traits['moisture']:+0.2f} shelter {traits['shelter']:0.2f} attach {traits['attachment']:0.2f}"
                )
            lines.append(f"      features {', '.join(definition.surface_features)}")
            if surface_notes:
                lines.append(f"      surface ecology {'; '.join(surface_notes)}")
    return "\n".join(lines)


def render_substrate_stack(sim: Terrarium) -> str:
    state = sim.state
    if state.container.footprint_shape == "round":
        container_shape = f"dia {state.container.diameter_cm:0.1f}cm"
    else:
        container_shape = f"{state.container.length_cm:0.1f}x{state.container.width_cm:0.1f}cm"
    lines = [
        (
            f"SUBSTRATE STACK {sim.substrate_height_cm():0.2f}/{state.container.height_cm:0.2f}cm "
            f"(free {sim.remaining_substrate_height_cm():0.2f}cm, "
            f"container {state.container.key} {state.container.capacity_ml:g}ml, {container_shape}, "
            f"base {state.container.base_area_cm2:0.2f}cm2, "
            f"mesh {sim.mesh_layer_count():02d}, watered {state.soil_moistened_ml + state.sprayed_ml:0.0f}ml)"
        )
    ]
    if not state.substrate_layers:
        lines.append("  empty")
        return "\n".join(lines)

    for index, layer in enumerate(state.substrate_layers, start=1):
        if layer.layer_kind == "mesh":
            lines.append(f"  L{index:02d} {SUBSTRATE_LAYER_NAMES[layer.layer_kind]:22s} 00.00cm (00.0%)  Mesh screen")
            continue
        stats = substrate_layer_stats(layer)
        soil_stats = soil_layer_stats(layer)
        height_percent = layer.height_cm / state.container.height_cm * 100.0
        mixture = " + ".join(
            f"{SUBSTRATES[portion.substrate].display_name} {portion.percent:g}%"
            for portion in layer.portions
        )
        lines.append(
            f"  L{index:02d} {SUBSTRATE_LAYER_NAMES[layer.layer_kind]:22s} "
            f"{layer.height_cm:05.2f}cm ({height_percent:04.1f}%)  "
            f"slope {layer.slope_x_cm:+0.2f},{layer.slope_y_cm:+0.2f}cm  {mixture}"
        )
        lines.append(
            f"      water_ret={stats['water_retention']:0.1f}/10  aeration={stats['aeration']:0.1f}/10"
        )
        if soil_stats["ph"] is not None:
            lines.append(
                f"      root_zone_pH={soil_stats['ph']:0.1f}  "
                f"soil_nutrients={soil_stats['nutrients']:0.1f}/10"
            )
    return "\n".join(lines)


def render_log_line(state: TerrariumState, stability: int) -> str:
    events = ",".join(state.events) if state.events else "-"
    source_compass = (90.0 - state.sun_azimuth_deg) % 360.0
    return (
        f"{state.tick:05d} h={state.hour:02d} "
        f"L={state.light:0.2f} src={source_compass:03.0f}/{state.sun_altitude_deg:02.0f} T={state.temperature:05.2f} "
        f"O2={state.oxygen:0.3f} CO2={state.carbon_dioxide:0.3f} "
        f"H2O={state.water:0.3f} NUT={state.nutrients:0.3f} "
        f"P={state.plants:07.2f} A={state.algae:06.2f} "
        f"G={state.grazers:06.2f} M={state.microbes:06.2f} "
        f"S={stability:03d} E={events}"
    )
