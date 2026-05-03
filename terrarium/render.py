from __future__ import annotations

from collections.abc import Iterable
from shutil import get_terminal_size

from .model import Terrarium, TerrariumState


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

    lines = [
        rule,
        (
            f"TICK {state.tick:05d}  HOUR {state.hour:02d}  "
            f"LIGHT {state.light:0.2f}  TEMP {state.temperature:05.2f}C  "
            f"STABILITY {stability:03d}/100"
        ),
        rule,
        f"ATM   O2  [{bar(state.oxygen)}] {state.oxygen:0.3f}   CO2 [{bar(state.carbon_dioxide)}] {state.carbon_dioxide:0.3f}",
        f"SOIL  H2O [{bar(state.water)}] {state.water:0.3f}   NUT [{bar(state.nutrients)}] {state.nutrients:0.3f}",
        f"WASTE DET [{bar(state.detritus)}] {state.detritus:0.3f}   TOX [{bar(state.toxicity)}] {state.toxicity:0.3f}",
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

    lines.extend([rule, f"EVENTS {events}", rule])
    return "\n".join(lines)


def render_log_line(state: TerrariumState, stability: int) -> str:
    events = ",".join(state.events) if state.events else "-"
    return (
        f"{state.tick:05d} h={state.hour:02d} "
        f"L={state.light:0.2f} T={state.temperature:05.2f} "
        f"O2={state.oxygen:0.3f} CO2={state.carbon_dioxide:0.3f} "
        f"H2O={state.water:0.3f} NUT={state.nutrients:0.3f} "
        f"P={state.plants:07.2f} A={state.algae:06.2f} "
        f"G={state.grazers:06.2f} M={state.microbes:06.2f} "
        f"S={stability:03d} E={events}"
    )
