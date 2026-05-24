from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
from shutil import get_terminal_size
from textwrap import shorten
import threading
import time

from .model import (
    ANIMALS,
    CONTAINERS,
    HARDSCAPES,
    HARDSCAPE_ORIENTATIONS,
    HARDSCAPE_POSITIONS,
    MAX_HARDSCAPE_COVERAGE,
    PLANTS,
    SUBSTRATES,
    SUBSTRATE_LAYER_NAMES,
    SUBSTRATE_LAYER_ORDER,
    SimulationConfig,
    Terrarium,
    TerrariumState,
    canonical_animal_key,
    canonical_container_key,
    canonical_plant_key,
    container_spec,
)
from .render import (
    render_animals,
    render_dashboard,
    render_hardscape,
    render_log_line,
    render_placement,
    render_plant_growth,
    render_plantings,
    render_seal_report,
    render_space,
    render_substrate_stack,
)


POOLS = {"water", "nutrients", "oxygen", "carbon_dioxide", "detritus", "toxicity", "temperature", "light_intensity"}
POPS = {"plants", "algae", "grazers", "microbes"}
DEFAULT_SURVIVAL_TIME_SCALE = 240.0
SIM_SECONDS_PER_TICK = 3600.0
MAX_AUTORUN_STEPS_PER_CYCLE = 4
MAX_RUNNING_BOTTLES = 8
LIFE_EVENT_COOLDOWN_TICKS = 8
GAME_STATE_VERSION = 1
INITIAL_STATE_ARGS = ("seed", "container", "light", "water", "nutrients", "plants", "algae", "grazers", "microbes")


EVENT_MESSAGES = {
    "O2_CRASH": "small animals are sluggish near the surface and under stones",
    "CO2_SATURATION": "lower leaves stay limp through the dark hours",
    "DROUGHT": "condensation fades from the glass and exposed moss looks dry",
    "CONDENSATION_BEADS": "small beads of water collect on the glass",
    "GLASS_DRYING": "the glass is nearly dry and the exposed surface looks matte",
    "WATER_POOLING": "water is visibly pooling below the lower layer",
    "SOIL_WATERLOGGED": "the root zone looks glassy and heavy against the container wall",
    "ROOT_ZONE_DULL": "root tips visible near the glass look dull and oxygen-starved",
    "SURFACE_GLISTENING": "the moss and soil surface still glisten",
    "BIOFILM_FILM": "a faint slick film is visible on wet glass and hardscape",
    "MOLD_PATCHES": "small pale mold patches are visible in the litter",
    "LITTER_MAT": "leaf litter has formed a dark matted layer",
    "NUTRIENT_LIMIT": "new foliage looks smaller and paler than older leaves",
    "ROT_SPIKE": "dark detritus is collecting under the leaves",
    "TOXICITY_RISE": "fresh tips dull and root tips near the glass turn brown",
    "PLANT_COLLAPSE": "plant cover is visibly thinning",
    "GRAZER_LOSS": "the small consumer layer is hard to spot",
    "PLANTING_SPACE_LIMIT": "open planting surface is getting crowded",
    "PROPAGATION_READY": "a plant has a separable offset or clump forming",
    "ANIMAL_CROWDING": "animals are clustering in the same damp pockets",
    "PLANT_SPATIAL_PRESSURE": "nearby plantings are pressing into each other",
    "LOW_SPOT_WET": "a low corner stays wet while higher patches dry first",
    "VISIBLE_PLANT_GRAZING": "small bite marks or translucent grazed edges are visible on tender growth",
    "MOLD_TOUCHING_PLANT": "pale fuzz is touching a plant's lower leaves or moss edge",
    "HARDSCAPE_FILM": "wet grooves and stone edges show a faint living film",
    "PROTECTED_SURFACE_MOLD": "pale fuzz is settling into protected cracks or undersides",
    "WINDOW_BRIGHT_SIDE": "the window-facing side of the bottle is visibly brighter",
    "DIRECT_SUN_PATCH": "a sharper sun patch crosses the planting surface",
    "DIFFUSE_WINDOW_LIGHT": "the light is soft and spread out with weak shadows",
    "CLOUD_MUTED_LIGHT": "the bottle looks muted under cloudy window light",
    "SHORT_WINTER_DAY": "the window side dims early in the afternoon",
    "LONG_SUMMER_LIGHT": "late light is still reaching the leaves",
    "WINDOW_WARM_EDGE": "the bright side dries first and the glass looks warmer there",
    "MOSS_LAMP_GLOW": "the moss lamp casts a steady highlight across the nearest surface",
    "MOSS_LAMP_DRY_EDGE": "tips nearest the moss lamp look a little more matte",
    "SHADE_LINE_VISIBLE": "stone and wood are casting a clear shade line",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="terrarium",
        description="Closed terrarium ecosystem simulator.",
        epilog="Run 'terrarium' with no subcommand to start the interactive game shell.",
    )
    add_initial_state_args(parser, suppress_defaults=True)

    subparsers = parser.add_subparsers(dest="command")

    run = subparsers.add_parser("run", help="run a batch simulation")
    add_initial_state_args(run, suppress_defaults=True)
    run.add_argument("--ticks", type=int, default=168, help="number of simulated hours")
    run.add_argument("--interval", type=int, default=12, help="print every N ticks")
    run.add_argument("--speed", type=float, default=0.0, help="seconds to sleep between printed frames")
    run.add_argument("--compact", action="store_true", help="render fewer dashboard lines")
    run.add_argument("--log", action="store_true", help="print one-line metrics instead of dashboards")
    run.add_argument("--export", type=Path, default=None, help="write JSONL snapshots to a file")

    shell = subparsers.add_parser("shell", help="start an interactive simulation console")
    add_initial_state_args(shell, suppress_defaults=True)
    shell.add_argument("--load", type=Path, default=None, help="load state JSON saved by the shell")

    return parser


def add_initial_state_args(parser: argparse.ArgumentParser, suppress_defaults: bool = False) -> None:
    default = argparse.SUPPRESS if suppress_defaults else None
    parser.add_argument("--seed", type=int, default=default, help="deterministic random seed")
    parser.add_argument(
        "--container",
        default=argparse.SUPPRESS if suppress_defaults else "standard_1l",
        help="container key, e.g. tiny_vial, standard_1l, horizontal_jar",
    )
    parser.add_argument(
        "--light",
        type=float,
        default=argparse.SUPPRESS if suppress_defaults else 0.86,
        help="lamp/daylight intensity, 0..1",
    )
    parser.add_argument(
        "--water",
        type=float,
        default=argparse.SUPPRESS if suppress_defaults else 0.74,
        help="initial available water, 0..1",
    )
    parser.add_argument(
        "--nutrients",
        type=float,
        default=argparse.SUPPRESS if suppress_defaults else 0.58,
        help="initial soil nutrients, 0..1",
    )
    parser.add_argument(
        "--plants",
        type=float,
        default=argparse.SUPPRESS if suppress_defaults else 72.0,
        help="initial plant biomass",
    )
    parser.add_argument(
        "--algae",
        type=float,
        default=argparse.SUPPRESS if suppress_defaults else 18.0,
        help="initial algae biomass",
    )
    parser.add_argument(
        "--grazers",
        type=float,
        default=argparse.SUPPRESS if suppress_defaults else 9.0,
        help="initial grazer biomass",
    )
    parser.add_argument(
        "--microbes",
        type=float,
        default=argparse.SUPPRESS if suppress_defaults else 20.0,
        help="initial microbe biomass",
    )


def make_sim(args: argparse.Namespace) -> Terrarium:
    light = getattr(args, "light", 0.86)
    seed = getattr(args, "seed", None)
    config = SimulationConfig(light_intensity=max(0.0, min(1.0, light)))
    selected_container = container_spec(getattr(args, "container", "standard_1l"))
    state = TerrariumState(
        water=max(0.0, min(1.0, getattr(args, "water", 0.74))),
        nutrients=max(0.0, min(1.0, getattr(args, "nutrients", 0.58))),
        plants=max(0.0, getattr(args, "plants", 72.0)),
        algae=max(0.0, getattr(args, "algae", 18.0)),
        grazers=max(0.0, getattr(args, "grazers", 9.0)),
        microbes=max(0.0, getattr(args, "microbes", 20.0)),
        container=selected_container,
        seed=seed,
    )
    return Terrarium(state=state, config=config, seed=seed)


@dataclass
class ManagedBottle:
    bottle_id: str
    sim: Terrarium
    running: bool = True
    name: str = ""
    source_path: str = ""
    accumulated_sim_seconds: float = 0.0
    last_wall_time: float = field(default_factory=time.monotonic)
    last_reported_day: int = 0
    last_events: set[str] = field(default_factory=set)
    stability_band: str = ""
    dead: bool = False
    death_tick: int | None = None
    death_reason: str = ""
    last_plant_records: dict[str, tuple[str, str, int, int]] = field(default_factory=dict)
    last_animal_records: dict[str, tuple[int, str, str]] = field(default_factory=dict)
    last_life_message_ticks: dict[str, int] = field(default_factory=dict)
    report_variant_counts: dict[str, int] = field(default_factory=dict)


class SurvivalManager:
    def __init__(
        self,
        time_scale: float = DEFAULT_SURVIVAL_TIME_SCALE,
        max_running: int = MAX_RUNNING_BOTTLES,
    ) -> None:
        self.time_scale = time_scale
        self.max_running = max_running
        self.lock = threading.RLock()
        self._bottles: list[ManagedBottle] = []
        self._seen_sim_ids: dict[int, str] = {}
        self._deleted_sources: set[str] = set()
        self._serial = 0
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run_loop, name="terrarium-survival", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)

    def register(self, sim: Terrarium, name: str = "", source_path: str = "") -> ManagedBottle:
        if not sim.state.sealed:
            raise ValueError("only sealed terrariums can enter auto survival")
        with self.lock:
            existing_id = self._seen_sim_ids.get(id(sim))
            if existing_id is not None:
                return self.get(existing_id)

            self._serial += 1
            dead = sim.all_explicit_life_dead()
            running = not dead and self.running_count() < self.max_running
            bottle = ManagedBottle(
                bottle_id=f"B{self._serial:02d}",
                sim=sim,
                running=running,
                name=name,
                source_path=source_path,
                last_reported_day=self.completed_days(sim),
                last_events=set(sim.state.events),
                stability_band=self.stability_band(sim.stability_score()),
                dead=dead,
                death_tick=sim.state.tick if dead else None,
                death_reason=sim.explicit_life_death_reason() if dead else "",
                last_plant_records=self.plant_records(sim),
                last_animal_records=self.animal_records(sim),
            )
            self._bottles.append(bottle)
            self._seen_sim_ids[id(sim)] = bottle.bottle_id
            return bottle

    def get(self, bottle_id: str) -> ManagedBottle:
        normalized_id = bottle_id.strip().upper()
        for bottle in self._bottles:
            if bottle.bottle_id == normalized_id:
                return bottle
        raise ValueError(f"unknown bottle id '{bottle_id}'")

    def pause(self, bottle_id: str) -> ManagedBottle:
        with self.lock:
            bottle = self.get(bottle_id)
            bottle.running = False
            bottle.accumulated_sim_seconds = 0.0
            bottle.last_wall_time = time.monotonic()
            return bottle

    def resume(self, bottle_id: str) -> ManagedBottle:
        with self.lock:
            bottle = self.get(bottle_id)
            if bottle.dead:
                raise ValueError("bottle is dead and cannot resume")
            bottle.running = True
            bottle.last_wall_time = time.monotonic()
            return bottle

    def remove(self, bottle_id: str) -> ManagedBottle:
        with self.lock:
            bottle = self.get(bottle_id)
            self._bottles = [item for item in self._bottles if item.bottle_id != bottle.bottle_id]
            self._seen_sim_ids.pop(id(bottle.sim), None)
            if bottle.source_path:
                self._deleted_sources.add(bottle.source_path)
            bottle.running = False
            bottle.accumulated_sim_seconds = 0.0
            return bottle

    def running_count(self) -> int:
        return sum(1 for bottle in self._bottles if bottle.running and not bottle.dead)

    def render_list(self) -> str:
        with self.lock:
            lines = [
                (
                    f"BOTTLES running {self.running_count()}/{len(self._bottles)}  "
                    f"scale {self.time_scale:g}x"
                )
            ]
            if not self._bottles:
                lines.append("  empty")
                return "\n".join(lines)
            for bottle in self._bottles:
                state = bottle.sim.state
                day, hour = self.survival_day_hour(bottle.sim)
                status = "dead" if bottle.dead else ("running" if bottle.running else "paused")
                name = f" {bottle.name}" if bottle.name else ""
                reason = f"  {bottle.death_reason}" if bottle.dead and bottle.death_reason else ""
                lines.append(
                    f"  {bottle.bottle_id}{name} {status:7s} "
                    f"day {day} {hour:02d}:00  tick {state.tick:05d}  "
                    f"stability {bottle.sim.stability_score():03d}/100{reason}"
                )
            return "\n".join(lines)

    def completed_days(self, sim: Terrarium) -> int:
        sealed_tick = sim.state.sealed_tick or 0
        elapsed_hours = max(0, sim.state.tick - sealed_tick)
        return elapsed_hours // 24

    def survival_day_hour(self, sim: Terrarium) -> tuple[int, int]:
        sealed_tick = sim.state.sealed_tick or 0
        elapsed_hours = max(0, sim.state.tick - sealed_tick)
        return elapsed_hours // 24 + 1, elapsed_hours % 24

    def stability_band(self, score: int) -> str:
        if score < 35:
            return "critical"
        if score < 60:
            return "warning"
        if score < 82:
            return "stable"
        return "thriving"

    def plant_records(self, sim: Terrarium) -> dict[str, tuple[str, str, int, int]]:
        return {
            planting.planting_id: (
                planting.survival_state,
                planting.growth_stage,
                int(planting.reproduction_progress // 25),
                planting.offspring_potential,
            )
            for planting in sim.state.plantings
        }

    def animal_records(self, sim: Terrarium) -> dict[str, tuple[int, str, str]]:
        return {
            group.group_id: (
                group.count,
                group.survival_state,
                group.population_trend,
            )
            for group in sim.state.animal_groups
        }

    def _run_loop(self) -> None:
        while not self._stop.is_set():
            time.sleep(0.25)
            messages: list[str] = []
            with self.lock:
                now = time.monotonic()
                for bottle in self._bottles:
                    if bottle.dead or not bottle.running:
                        bottle.last_wall_time = now
                        continue
                    elapsed_wall = max(0.0, now - bottle.last_wall_time)
                    bottle.last_wall_time = now
                    bottle.accumulated_sim_seconds += elapsed_wall * self.time_scale
                    due_steps = int(bottle.accumulated_sim_seconds // SIM_SECONDS_PER_TICK)
                    if due_steps <= 0:
                        continue
                    if due_steps > MAX_AUTORUN_STEPS_PER_CYCLE:
                        due_steps = MAX_AUTORUN_STEPS_PER_CYCLE
                        bottle.accumulated_sim_seconds = 0.0
                    else:
                        bottle.accumulated_sim_seconds -= due_steps * SIM_SECONDS_PER_TICK
                    for _ in range(due_steps):
                        bottle.sim.step()
                        messages.extend(self._messages_for_step(bottle))
                        messages.extend(self._death_messages_if_needed(bottle))
                        if bottle.dead:
                            break
            for message in messages:
                print(message)

    def _messages_for_step(self, bottle: ManagedBottle) -> list[str]:
        sim = bottle.sim
        state = sim.state
        day, hour = self.survival_day_hour(sim)
        prefix = f"[{bottle.bottle_id}] survival day {day} {hour:02d}:00"
        messages: list[str] = []

        completed_days = self.completed_days(sim)
        if completed_days > bottle.last_reported_day:
            bottle.last_reported_day = completed_days
            messages.append(self._daily_message(prefix, bottle, completed_days, sim))

        current_events = set(state.events)
        for event in sorted(current_events - bottle.last_events):
            messages.append(f"{prefix} - INCIDENT: {self._event_message(bottle, event)}")
        bottle.last_events = current_events

        band = self.stability_band(sim.stability_score())
        if band != bottle.stability_band:
            messages.append(f"{prefix} - STATUS: {self._stability_band_message(band)}")
            bottle.stability_band = band

        messages.extend(self._life_change_messages(bottle, prefix))

        return messages

    def _life_change_messages(self, bottle: ManagedBottle, prefix: str) -> list[str]:
        messages: list[str] = []
        sim = bottle.sim
        current_plants = self.plant_records(sim)
        for planting in sim.state.plantings:
            current = current_plants[planting.planting_id]
            previous = bottle.last_plant_records.get(planting.planting_id)
            if previous is None:
                continue
            if current[0] != previous[0]:
                key = f"plant:{planting.planting_id}:state"
                if self._should_report_life_message(bottle, key, important=current[0] == "dead"):
                    messages.append(self._plant_state_message(bottle, prefix, planting))
            if current[1] != previous[1]:
                messages.append(self._plant_stage_message(bottle, prefix, planting))
            if current[2] > previous[2] and planting.reproduction_progress > 0:
                messages.append(self._plant_reproduction_message(bottle, prefix, planting))
            if current[3] > previous[3]:
                messages.append(self._plant_division_message(bottle, prefix, planting))
        bottle.last_plant_records = current_plants

        current_animals = self.animal_records(sim)
        for group in sim.state.animal_groups:
            current = current_animals[group.group_id]
            previous = bottle.last_animal_records.get(group.group_id)
            if previous is None:
                continue
            definition = ANIMALS[group.animal]
            if current[0] > previous[0]:
                messages.append(
                    f"{prefix} - FAUNA: "
                    f"{self._animal_count_message(bottle, group, definition.display_name, increasing=True)}"
                )
            elif current[0] < previous[0]:
                messages.append(
                    f"{prefix} - FAUNA: "
                    f"{self._animal_count_message(bottle, group, definition.display_name, increasing=False)}"
                )
            if current[1] != previous[1]:
                key = f"animal:{group.group_id}:state"
                if self._should_report_life_message(bottle, key, important=current[1] == "dead"):
                    messages.append(self._animal_state_message(bottle, prefix, group))
            if current[2] != previous[2]:
                key = f"animal:{group.group_id}:trend"
                if self._should_report_life_message(bottle, key):
                    messages.append(self._animal_trend_message(bottle, prefix, group))
        bottle.last_animal_records = current_animals
        return messages

    def _should_report_life_message(self, bottle: ManagedBottle, key: str, important: bool = False) -> bool:
        now = bottle.sim.state.tick
        previous = bottle.last_life_message_ticks.get(key)
        if important or previous is None or now - previous >= LIFE_EVENT_COOLDOWN_TICKS:
            bottle.last_life_message_ticks[key] = now
            return True
        return False

    def _pick_report_variant(self, bottle: ManagedBottle, key: str, variants: list[str]) -> str:
        if not variants:
            return ""
        index = bottle.report_variant_counts.get(key, 0)
        bottle.report_variant_counts[key] = index + 1
        return variants[index % len(variants)]

    def _daily_message(
        self,
        prefix: str,
        bottle: ManagedBottle,
        completed_days: int,
        sim: Terrarium,
    ) -> str:
        observation = self._stability_observation(sim)
        text = self._pick_report_variant(
            bottle,
            "daily_marker",
            [
                f"survived {completed_days} day(s); {observation}",
                f"day {completed_days} closeout; {observation}",
                f"daily glass check recorded; {observation}",
                f"{completed_days} day(s) sealed; {observation}",
            ],
        )
        life_summary = self._daily_life_summary(sim)
        if life_summary:
            text = f"{text} | {life_summary}"
        return f"{prefix} - DAILY: {text}"

    def _event_message(self, bottle: ManagedBottle, event: str) -> str:
        variants = {
            "CONDENSATION_BEADS": [
                "small beads of water collect on the glass",
                "fine droplets have formed along the brighter glass",
                "condensation is visible as scattered pinpoints",
            ],
            "GLASS_DRYING": [
                "the glass is nearly dry and the exposed surface looks matte",
                "condensation has thinned; upper glass reads mostly clear",
                "dry patches are spreading across the inner wall",
            ],
            "DROUGHT": [
                "condensation fades from the glass and exposed moss looks dry",
                "upper moss edges look matte while the glass stays clear",
                "the surface has lost its usual damp sheen",
            ],
            "WATER_POOLING": [
                "water is visibly pooling below the lower layer",
                "a clear water line is forming near the base",
                "the bottom layer shows standing water against the glass",
            ],
            "SOIL_WATERLOGGED": [
                "the root zone looks glassy and heavy against the container wall",
                "soil at the glass has a dark, saturated look",
                "the lower soil face appears compact and wet",
            ],
            "MOLD_PATCHES": [
                "small pale mold patches are visible in the litter",
                "pale fuzz is appearing where litter stays damp",
                "white flecks have spread across protected organic debris",
            ],
            "ROT_SPIKE": [
                "dark detritus is collecting under the leaves",
                "lower leaf litter is darkening into a soft layer",
                "debris is accumulating below the canopy",
            ],
            "WINDOW_BRIGHT_SIDE": [
                "the window-facing side of the bottle is visibly brighter",
                "one side of the planting surface has a stronger light edge",
                "the window side shows the clearest highlight",
            ],
        }.get(event)
        if variants:
            return self._pick_report_variant(bottle, f"event:{event}", variants)
        return EVENT_MESSAGES.get(event, event.lower())

    def _plant_state_message(self, bottle: ManagedBottle, prefix: str, planting) -> str:
        name = PLANTS[planting.plant].display_name
        appearance = self._plant_appearance(planting)
        variants = {
            "thriving": [
                f"{name}: new tissue reads strong; {appearance}",
                f"{name}: canopy color is clean; {appearance}",
                f"{name}: growth front is easy to see; {appearance}",
            ],
            "settling": [
                f"{name}: establishment signs are visible; {appearance}",
                f"{name}: the planting has seated into its spot; {appearance}",
                f"{name}: older tissue is steady while new tips adjust; {appearance}",
            ],
            "stable": [
                f"{name}: outline remains unchanged; {appearance}",
                f"{name}: no fresh decline is visible; {appearance}",
                f"{name}: structure is holding; {appearance}",
            ],
            "stressed": [
                f"{name}: stress signs are visible; {appearance}",
                f"{name}: leaf texture has softened; {appearance}",
                f"{name}: the lower edge shows strain; {appearance}",
            ],
            "declining": [
                f"{name}: decline is visible since the last check; {appearance}",
                f"{name}: weaker tissue is spreading from the base; {appearance}",
                f"{name}: color and lift have both slipped; {appearance}",
            ],
            "dead": [
                f"{name}: no living tissue remains; {appearance}",
                f"{name}: the planting has collapsed; {appearance}",
            ],
        }.get(planting.survival_state, [f"{name}: state reads {planting.survival_state}; {appearance}"])
        return f"{prefix} - FLORA: {self._pick_report_variant(bottle, f'plant_state:{planting.plant}:{planting.survival_state}', variants)}"

    def _plant_appearance(self, planting) -> str:
        definition = PLANTS[planting.plant]
        if planting.survival_state == "dead" or planting.status == "dead":
            return "tissue has collapsed and no fresh color remains"

        if definition.category == "moss":
            if planting.health >= 85:
                return "the cushion looks plump and evenly colored"
            if planting.health >= 60:
                return "the mat is a little flatter but still holding color"
            if planting.health >= 35:
                return "the tips look dull and some edges are drying"
            return "the patch is flattening with brown, tired edges"
        if definition.category == "lichen":
            if planting.health >= 85:
                return "the patch looks crisp and pale in a normal way"
            if planting.health >= 60:
                return "the edges are less crisp but the patch is intact"
            if planting.health >= 35:
                return "the surface looks dusty and uneven"
            return "the patch is breaking up and losing definition"
        if definition.category in {"bromeliad_air", "orchid_mini", "epiphytic_fern"}:
            if planting.health >= 85:
                return "the crown holds firm and the exposed roots look clean"
            if planting.health >= 60:
                return "the crown is firm but the oldest edges look tired"
            if planting.health >= 35:
                return "older edges curl and the crown sits less upright"
            return "the crown is soft and the oldest tissue is collapsing"
        if definition.category == "carnivorous":
            if planting.health >= 85:
                return "traps look clean and held open"
            if planting.health >= 60:
                return "some traps are smaller but still responsive-looking"
            if planting.health >= 35:
                return "trap edges darken and new leaves look hesitant"
            return "most traps are dark or folded down"
        if planting.health >= 85:
            return "leaves are firm, lifted, and evenly colored"
        if planting.health >= 60:
            return "leaves hold shape with a little edge curl"
        if planting.health >= 35:
            return "leaves look softer and lower leaves are paling"
        return "stems slump and the lowest leaves are collapsing"

    def _plant_stage_message(self, bottle: ManagedBottle, prefix: str, planting) -> str:
        name = PLANTS[planting.plant].display_name
        variants = {
            "establishing": [
                "rooting-in still looks tentative",
                "the base is seated but not yet spreading",
                "new contact points are forming at the surface",
            ],
            "growing": [
                "fresh tips are visible",
                "new leaf points are easier to pick out",
                "the growth edge has advanced slightly",
            ],
            "mature": [
                "the planting has filled into its space",
                "the clump outline has become denser",
                "older and newer tissue now form a continuous patch",
            ],
            "reproductive": [
                "nodes and crowns look ready to spread",
                "new growth points are visible near the edge",
                "a few side points have become distinct",
            ],
            "dividable": [
                "a separable clump or offset is visible",
                "one side piece now has its own outline",
                "a division point can be seen at the base",
            ],
            "dead": [
                "no living growth remains",
                "the remaining tissue is collapsed",
            ],
        }.get(planting.growth_stage, [f"stage reads {planting.growth_stage}"])
        text = self._pick_report_variant(bottle, f"plant_stage:{planting.plant}:{planting.growth_stage}", variants)
        return f"{prefix} - FLORA: {name}: {text}"

    def _plant_reproduction_message(self, bottle: ManagedBottle, prefix: str, planting) -> str:
        name = PLANTS[planting.plant].display_name
        definition = PLANTS[planting.plant]
        if definition.reproduction_mode in {"mat_spread", "fragment_spread", "runner_spread"}:
            variants = [
                "edges are starting to creep into nearby open surface",
                "the mat edge has moved into an adjacent damp patch",
                "a thin fringe is visible beyond the original outline",
            ]
        elif definition.reproduction_mode in {"rhizome_division", "division"}:
            variants = [
                "a side growth is thickening near the base",
                "a secondary crown is easier to distinguish",
                "a small offset has gained its own outline",
            ]
        elif definition.reproduction_mode in {"pups", "offset_or_seed"}:
            variants = [
                "a small offset is forming near the crown",
                "a new point is visible beside the main crown",
                "the crown edge shows a separate nub",
            ]
        else:
            variants = [
                "new growth points are becoming easier to spot",
                "small new points are visible along the edge",
                "fresh growth is appearing outside the original center",
            ]
        text = self._pick_report_variant(bottle, f"plant_repro:{planting.plant}", variants)
        return f"{prefix} - FLORA: {name}: {text}"

    def _plant_division_message(self, bottle: ManagedBottle, prefix: str, planting) -> str:
        name = PLANTS[planting.plant].display_name
        text = self._pick_report_variant(
            bottle,
            f"plant_division:{planting.plant}",
            [
                "a distinct new piece could be separated later",
                "one offset now reads as its own small unit",
                "the clump has a visible break point for future division",
            ],
        )
        return f"{prefix} - FLORA: {name}: {text}"

    def _animal_count_message(
        self,
        bottle: ManagedBottle,
        group,
        display_name: str,
        increasing: bool,
    ) -> str:
        label = self._animal_label(display_name)
        if increasing:
            variants = [
                f"{label}: new tiny young are visible",
                f"{label}: more pinprick movement appears in the damp pockets",
                f"{label}: the visible count has increased during inspection",
            ]
        else:
            variants = [
                f"{label}: fewer individuals appear during inspection",
                f"{label}: the usual damp pockets show less movement",
                f"{label}: visible activity has thinned out",
            ]
        return self._pick_report_variant(bottle, f"animal_count:{group.animal}:{increasing}", variants)

    def _animal_state_message(self, bottle: ManagedBottle, prefix: str, group) -> str:
        definition = ANIMALS[group.animal]
        label = self._animal_label(definition.display_name)
        appearance = self._animal_appearance(group)
        variants = {
            "thriving": [
                f"{label}: activity is easy to spot; {appearance}",
                f"{label}: movement shows in several pockets; {appearance}",
                f"{label}: the surface check shows frequent movement; {appearance}",
            ],
            "settling": [
                f"{label}: activity has shifted into the substrate; {appearance}",
                f"{label}: a few individuals appear in sheltered damp spots; {appearance}",
                f"{label}: movement is present but localized; {appearance}",
            ],
            "stable": [
                f"{label}: visible activity is steady; {appearance}",
                f"{label}: movement remains regular; {appearance}",
                f"{label}: the usual pockets still show activity; {appearance}",
            ],
            "stressed": [
                f"{label}: stress signs are visible; {appearance}",
                f"{label}: activity is compressed into sheltered spots; {appearance}",
                f"{label}: movement is reduced outside the wettest pockets; {appearance}",
            ],
            "declining": [
                f"{label}: activity has thinned; {appearance}",
                f"{label}: fewer individuals appear at the glass; {appearance}",
                f"{label}: the usual inspection points look quiet; {appearance}",
            ],
            "dead": [
                f"{label}: no movement remains visible; {appearance}",
                f"{label}: the group has disappeared from inspection points; {appearance}",
            ],
        }.get(group.survival_state, [f"{label}: state reads {group.survival_state}; {appearance}"])
        return f"{prefix} - FAUNA: {self._pick_report_variant(bottle, f'animal_state:{group.animal}:{group.survival_state}', variants)}"

    def _animal_label(self, display_name: str) -> str:
        return display_name if "colony" in display_name.lower() else f"{display_name} group"

    def _animal_appearance(self, group) -> str:
        if group.survival_state == "dead" or group.count <= 0:
            return "no movement is visible in their usual pockets"
        if group.survival_state == "thriving":
            return "movement is easy to catch under leaf litter and stones"
        if group.survival_state == "settling":
            return "a few individuals appear when the damp spots are disturbed"
        if group.survival_state == "stable":
            return "activity is visible but not crowded"
        if group.survival_state == "stressed":
            return "individuals cluster tightly in the wettest shelter"
        if group.survival_state == "declining":
            return "only occasional movement shows during inspection"
        return "activity is subtle"

    def _animal_trend_message(self, bottle: ManagedBottle, prefix: str, group) -> str:
        definition = ANIMALS[group.animal]
        label = self._animal_label(definition.display_name)
        variants = {
            "growing": [
                "more movement shows up around the damp pockets",
                "the visible activity band has widened",
                "additional movement appears near the litter edge",
            ],
            "reproducing": [
                "new tiny young are visible",
                "tiny pale specks are moving near sheltered litter",
                "the smallest individuals are now visible at the surface",
            ],
            "steady": [
                "activity looks balanced",
                "movement is present without crowding",
                "the same pockets show regular movement",
            ],
            "stalled": [
                "activity has gone quiet",
                "movement is limited to brief flashes under cover",
                "the surface check shows little change",
            ],
            "crowded": [
                "individuals cluster and avoid spreading out",
                "movement is concentrated in a few damp shelters",
                "the population appears packed into limited pockets",
            ],
            "declining": [
                "fewer individuals appear during inspection",
                "the visible activity line has pulled back",
                "usual pockets show less movement than before",
            ],
        }.get(group.population_trend, [f"trend reads {group.population_trend}"])
        text = self._pick_report_variant(bottle, f"animal_trend:{group.animal}:{group.population_trend}", variants)
        return f"{prefix} - FAUNA: {label}: {text}"

    def _daily_life_summary(self, sim: Terrarium) -> str:
        sections: list[str] = []
        if sim.state.plantings:
            plant_notes: list[str] = []
            for planting in sorted(sim.state.plantings, key=self._plant_daily_priority, reverse=True):
                definition = PLANTS[planting.plant]
                plant_notes.append(f"{definition.display_name}: {self._short_plant_observation(planting)}")
            sections.append("plant changes: " + "; ".join(plant_notes))
        if sim.state.animal_groups:
            animal_notes: list[str] = []
            for group in sorted(sim.state.animal_groups, key=self._animal_daily_priority, reverse=True):
                definition = ANIMALS[group.animal]
                animal_notes.append(f"{definition.display_name}: {self._short_animal_observation(group)}")
            sections.append("animal changes: " + "; ".join(animal_notes))
        return " | ".join(sections)

    def _plant_daily_priority(self, planting) -> float:
        priority = 0.0
        if planting.survival_state == "dead" or planting.status == "dead":
            priority += 130.0
        if planting.offspring_potential > 0:
            priority += 120.0
        if planting.reproduction_progress >= 70.0:
            priority += 90.0
        elif planting.reproduction_progress >= 35.0:
            priority += 45.0
        if planting.growth_stage in {"dividable", "reproductive"}:
            priority += 70.0
        elif planting.growth_stage in {"growing", "mature"}:
            priority += 35.0
        priority += min(30.0, planting.new_growth_count * 5.0)
        if planting.survival_state in {"stressed", "declining"}:
            priority += 25.0
        return priority

    def _animal_daily_priority(self, group) -> float:
        priority = 0.0
        if group.count <= 0 or group.survival_state == "dead":
            priority += 130.0
        if group.population_trend == "reproducing":
            priority += 110.0
        elif group.population_trend == "growing":
            priority += 75.0
        elif group.population_trend in {"declining", "crowded"}:
            priority += 55.0
        elif group.population_trend == "stalled":
            priority += 35.0
        if group.survival_state in {"stressed", "declining"}:
            priority += 45.0
        priority += min(25.0, group.visible_activity / 4.0)
        return priority

    def _short_plant_observation(self, planting) -> str:
        definition = PLANTS[planting.plant]
        mode = definition.reproduction_mode
        if planting.survival_state == "dead" or planting.status == "dead":
            return "no living tissue remains"
        if planting.offspring_potential > 0:
            if mode in {"mat_spread", "fragment_spread", "runner_spread"}:
                return "a new separate edge is visible beyond the original patch"
            if mode in {"rhizome_division", "division"}:
                return "a side crown has its own visible outline"
            if mode in {"pups", "offset_or_seed"}:
                return "a small offset is visible beside the crown"
            return "a distinct new growth point can be picked out"
        if planting.reproduction_progress >= 70.0:
            if mode in {"mat_spread", "fragment_spread", "runner_spread"}:
                return "the edge is creeping into nearby open surface"
            if mode in {"rhizome_division", "division"}:
                return "a secondary crown is becoming distinct"
            if mode in {"pups", "offset_or_seed"}:
                return "the crown edge shows a small new point"
            return "new growth points are becoming easier to spot"
        if planting.growth_stage == "reproductive":
            return "side points are visible around the established growth"
        if planting.growth_stage == "dividable":
            return "one piece reads as a separable clump"
        if planting.growth_stage == "mature":
            return "the outline looks denser than the original planting"
        if planting.growth_stage == "growing":
            if planting.new_growth_count >= 3:
                return "several fresh tips are visible"
            return "fresh tips are visible"
        if planting.growth_stage == "establishing":
            return "the base is still seating into the surface"
        if planting.survival_state == "thriving":
            return "fresh and upright"
        if planting.survival_state == "settling":
            return "mostly settled"
        if planting.survival_state == "stable":
            return "holding shape"
        if planting.survival_state == "stressed":
            return "softened edges"
        if planting.survival_state == "declining":
            return "losing color"
        return planting.survival_state

    def _short_animal_observation(self, group) -> str:
        if group.count <= 0 or group.survival_state == "dead":
            return "no visible movement remains"
        if group.population_trend == "reproducing":
            return "tiny young are visible in sheltered damp pockets"
        if group.population_trend in {"growing", "reproducing"}:
            return "the visible activity band has widened"
        if group.population_trend == "steady":
            if group.visible_activity >= 60.0:
                return "regular movement is easy to spot"
            return "regular activity remains visible"
        if group.population_trend == "stalled":
            return "the usual pockets look quiet"
        if group.population_trend == "crowded":
            return "individuals are clustered tightly in limited shelters"
        if group.population_trend == "declining":
            return "movement is harder to spot than before"
        return group.population_trend

    def _stability_observation(self, sim: Terrarium) -> str:
        return self._stability_band_message(self.stability_band(sim.stability_score()))

    def _stability_band_message(self, band: str) -> str:
        if band == "thriving":
            return "the bottle looks lively and well-balanced"
        if band == "stable":
            return "the bottle looks steady"
        if band == "warning":
            return "the bottle shows visible strain"
        return "the bottle looks close to collapse"

    def _death_messages_if_needed(self, bottle: ManagedBottle) -> list[str]:
        if bottle.dead or not bottle.sim.all_explicit_life_dead():
            return []
        bottle.dead = True
        bottle.running = False
        bottle.death_tick = bottle.sim.state.tick
        bottle.death_reason = bottle.sim.explicit_life_death_reason()
        day, hour = self.survival_day_hour(bottle.sim)
        prefix = f"[{bottle.bottle_id}] survival day {day} {hour:02d}:00"
        return [f"{prefix} - terrarium died: all plants and animals are dead ({bottle.death_reason})"]


def command_run(args: argparse.Namespace) -> int:
    sim = make_sim(args)
    export_handle = args.export.open("w", encoding="utf-8") if args.export else None
    try:
        for _ in range(args.ticks):
            state = sim.step()
            if export_handle:
                export_handle.write(state.to_json() + "\n")
            should_print = state.tick == 1 or state.tick % args.interval == 0 or state.tick == args.ticks
            if should_print:
                if args.log:
                    print(render_log_line(state, sim.stability_score()))
                else:
                    print(render_dashboard(sim, compact=args.compact))
                if args.speed > 0 and state.tick != args.ticks:
                    time.sleep(args.speed)
    finally:
        if export_handle:
            export_handle.close()
    return 0


def has_initial_overrides(args: argparse.Namespace) -> bool:
    return any(hasattr(args, name) for name in INITIAL_STATE_ARGS)


def default_game_state_path() -> Path:
    home_override = os.environ.get("TERRARIUM_HOME")
    base = Path(home_override) if home_override else Path.home() / ".terrarium"
    return base / "game.json"


def normalized_source_path(path: Path) -> str:
    try:
        return str(path.resolve())
    except OSError:
        return str(path.absolute())


def bottle_state_fingerprint(sim: Terrarium) -> str:
    return sim.state.to_json()


def matching_bottle_by_state(manager: SurvivalManager, sim: Terrarium) -> ManagedBottle | None:
    fingerprint = bottle_state_fingerprint(sim)
    for bottle in manager._bottles:
        if bottle_state_fingerprint(bottle.sim) == fingerprint:
            return bottle
    return None


def default_import_dirs(game_state_path: Path) -> list[Path]:
    import_override = os.environ.get("TERRARIUM_IMPORT_DIR")
    if import_override:
        return [Path(import_override)]
    if os.environ.get("TERRARIUM_HOME"):
        return [game_state_path.parent / "bottles"]
    candidates = [
        Path.cwd(),
        Path(__file__).resolve().parent.parent,
        game_state_path.parent / "bottles",
    ]
    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        source = normalized_source_path(candidate)
        if source not in seen:
            seen.add(source)
            unique.append(candidate)
    return unique


def known_bottle_sources(manager: SurvivalManager) -> set[str]:
    sources = {bottle.source_path for bottle in manager._bottles if bottle.source_path}
    sources.update(manager._deleted_sources)
    return sources


def load_standalone_bottle(path: Path) -> Terrarium | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict) or "sealed" not in data:
        return None
    try:
        sim = Terrarium.from_json(json.dumps(data))
    except (TypeError, ValueError, KeyError):
        return None
    return sim if sim.state.sealed else None


def load_game_state(manager: SurvivalManager, path: Path) -> int:
    if not path.exists():
        return 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print_command_notice(f"could not load saved terrariums from {path}: {exc}", "Starting without saved bottles.")
        return 0

    entries = data.get("bottles", []) if isinstance(data, dict) else []
    deleted_sources = data.get("deleted_sources", []) if isinstance(data, dict) else []
    manager._deleted_sources.update(str(source) for source in deleted_sources if source)
    loaded = 0
    for entry in entries:
        if not isinstance(entry, dict) or "state" not in entry:
            continue
        try:
            sim = Terrarium.from_json(json.dumps(entry["state"]))
        except (TypeError, ValueError, KeyError) as exc:
            print_command_notice(f"skipped a saved bottle: {exc}", "The rest of the save file will still load.")
            continue
        if not sim.state.sealed:
            continue
        source_path = str(entry.get("source", ""))
        duplicate = matching_bottle_by_state(manager, sim)
        if duplicate is not None:
            if source_path and not duplicate.source_path:
                duplicate.source_path = source_path
            continue
        bottle = manager.register(sim, str(entry.get("name", "")), source_path)
        desired_running = bool(entry.get("running", bottle.running))
        if not desired_running or bottle.dead:
            bottle.running = False
        loaded += 1
    return loaded


def import_standalone_bottle_saves(manager: SurvivalManager, game_state_path: Path) -> int:
    imported = 0
    skipped_sources = known_bottle_sources(manager)
    try:
        game_state_source = normalized_source_path(game_state_path)
    except OSError:
        game_state_source = str(game_state_path)
    for directory in default_import_dirs(game_state_path):
        if not directory.exists() or not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.json")):
            source = normalized_source_path(path)
            if source == game_state_source or source in skipped_sources:
                continue
            sim = load_standalone_bottle(path)
            if sim is None:
                continue
            duplicate = matching_bottle_by_state(manager, sim)
            if duplicate is not None:
                if not duplicate.source_path:
                    duplicate.source_path = source
                skipped_sources.add(source)
                continue
            bottle = manager.register(sim, path.stem, source)
            skipped_sources.add(source)
            imported += 1
            if not bottle.dead and manager.running_count() > manager.max_running:
                bottle.running = False
    return imported


def save_game_state(manager: SurvivalManager, path: Path) -> None:
    with manager.lock:
        bottles = [
            {
                "name": bottle.name,
                "running": bottle.running and not bottle.dead,
                "source": bottle.source_path,
                "state": json.loads(bottle.sim.state.to_json()),
            }
            for bottle in manager._bottles
        ]
        deleted_sources = sorted(manager._deleted_sources)
    if not bottles and not deleted_sources:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": GAME_STATE_VERSION, "bottles": bottles, "deleted_sources": deleted_sources}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def command_shell(args: argparse.Namespace) -> int:
    load_path = getattr(args, "load", None)
    manager = SurvivalManager()
    game_state_path = default_game_state_path()
    sim: Terrarium | None = None
    open_name = ""
    creation_serial = 0

    try:
        startup_messages: list[str] = []
        loaded_count = load_game_state(manager, game_state_path)
        if loaded_count:
            startup_messages.append(
                f"Loaded {loaded_count} saved terrarium(s); auto-survival is running at {manager.time_scale:g}x."
            )

        if load_path:
            load_source = normalized_source_path(load_path)
            loaded_sim = Terrarium.from_json(load_path.read_text(encoding="utf-8"))
            if loaded_sim.state.sealed:
                bottle = manager.register(loaded_sim, load_path.stem, load_source)
                startup_messages.append(
                    f"Loaded sealed terrarium as {bottle.bottle_id}; auto-survival is running at {manager.time_scale:g}x."
                )
            else:
                sim = loaded_sim
                open_name = load_path.stem
                startup_messages.append("Loaded open terrarium for crafting.")
        imported_count = import_standalone_bottle_saves(manager, game_state_path)
        if imported_count:
            startup_messages.append(
                f"Imported {imported_count} standalone bottle save(s); auto-survival is running at {manager.time_scale:g}x."
            )
        if not load_path and has_initial_overrides(args):
            sim = make_sim(args)
            open_name = ""
            startup_messages.append("Started an open terrarium from launch options.")

        manager.start()
        for message in startup_messages:
            print(message)

        print(render_shell_home(sim, manager))
        pending_commands: list[str] = []
        while True:
            try:
                if pending_commands:
                    raw = pending_commands.pop(0).strip()
                else:
                    raw = input("terrarium> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return 0
            if not raw:
                continue

            batch = split_command_batch(raw)
            if not batch:
                continue
            raw = batch[0]
            if len(batch) > 1:
                pending_commands = batch[1:] + pending_commands

            parts = raw.split()
            command = parts[0].lower()
            try:
                with manager.lock:
                    if command in {"quit", "exit", "q"}:
                        return 0
                    if command in {"help", "h", "?"}:
                        print_help()
                    elif command in {"status", "s"}:
                        if sim is None:
                            print(manager.render_list())
                        else:
                            print(render_dashboard(sim))
                    elif command == "step":
                        if sim is None:
                            print_command_notice("there is no open terrarium to step.", "Use bottle status B01 or make a new terrarium.")
                            continue
                        ticks = int(parts[1]) if len(parts) > 1 else 1
                        sim.run(ticks)
                        print(render_dashboard(sim))
                    elif command == "run":
                        if sim is None:
                            print_command_notice("there is no open terrarium to run manually.", "Use bottle status B01 or make a new terrarium.")
                            continue
                        ticks = int(parts[1]) if len(parts) > 1 else 24
                        interval = int(parts[2]) if len(parts) > 2 else max(1, ticks // 6)
                        for _ in range(ticks):
                            state = sim.step()
                            if state.tick % interval == 0:
                                print(render_log_line(state, sim.stability_score()))
                        print(render_dashboard(sim))
                    elif command == "set":
                        if len(parts) != 3:
                            raise ValueError("usage: set <pool> <value>")
                        name = normalize_name(parts[1])
                        if name not in POOLS:
                            raise ValueError(f"pool must be one of: {', '.join(sorted(POOLS))}")
                        if sim is None:
                            print_command_notice("there is no open terrarium to edit.", "Use make [name] to start crafting.")
                            continue
                        sim.set_pool(name, float(parts[2]))
                        print(render_dashboard(sim, compact=True))
                    elif command == "add":
                        if len(parts) != 3:
                            raise ValueError("usage: add <population> <amount>")
                        name = normalize_name(parts[1])
                        if name not in POPS:
                            raise ValueError(f"population must be one of: {', '.join(sorted(POPS))}")
                        if sim is None:
                            print_command_notice("there is no open terrarium to edit.", "Use make [name] to start crafting.")
                            continue
                        sim.add_population(name, float(parts[2]))
                        print(render_dashboard(sim, compact=True))
                    elif command in {"substrate", "sub"}:
                        if sim is None:
                            print_command_notice("there is no open terrarium to craft.", "Use make [name] to start crafting.")
                            continue
                        handle_substrate_command(sim, parts[1:])
                    elif command in {"mesh", "screen"}:
                        if sim is None:
                            print_command_notice("there is no open terrarium to craft.", "Use make [name] to start crafting.")
                            continue
                        handle_substrate_command(sim, ["mesh", *parts[1:]])
                    elif command in {"hardscape", "scape", "decor", "deco", "rock"}:
                        if sim is None:
                            print_command_notice("there is no open terrarium to craft.", "Use make [name] to start crafting.")
                            continue
                        handle_hardscape_command(sim, parts[1:])
                    elif command in {"plant", "plants"}:
                        if sim is None:
                            print_command_notice("there is no open terrarium to craft.", "Use make [name] to start crafting.")
                            continue
                        handle_plant_command(sim, parts[1:])
                    elif command in {"animal", "animals", "fauna"}:
                        if sim is None:
                            print_command_notice("there is no open terrarium to craft.", "Use make [name] to start crafting.")
                            continue
                        handle_animal_command(sim, parts[1:])
                    elif command in {"container", "jar", "bottle_size"}:
                        if sim is None:
                            print_command_notice("there is no open terrarium to configure.", "Use make [name] to start crafting.")
                            continue
                        handle_container_command(sim, parts[1:])
                    elif command in {"placement", "position", "light"}:
                        if sim is None:
                            print_command_notice(
                                "there is no open terrarium to place.",
                                "Use bottle placement B01 status for a sealed bottle or make [name] to start crafting.",
                            )
                            continue
                        handle_placement_command(sim, parts[1:])
                    elif command in {"moisten", "wet"}:
                        if sim is None:
                            print_command_notice("there is no open terrarium to craft.", "Use make [name] to start crafting.")
                            continue
                        handle_moisten_command(sim, parts[1:])
                    elif command in {"spray", "mist"}:
                        if sim is None:
                            print_command_notice("there is no open terrarium to craft.", "Use make [name] to start crafting.")
                            continue
                        handle_spray_command(sim, parts[1:])
                    elif command in {"seal", "finish", "complete"}:
                        if sim is None:
                            print_command_notice("there is no open terrarium to seal.", "Use make [name] to start crafting.")
                            continue
                        if handle_seal_command(sim, parts[1:]):
                            bottle = manager.register(sim, open_name)
                            state = "dead" if bottle.dead else ("running" if bottle.running else "paused")
                            print(
                                f"Auto-survival started as {bottle.bottle_id} "
                                f"({state}, {manager.time_scale:g}x)."
                            )
                            sim = None
                            open_name = ""
                    elif command in {"make", "craft", "new"}:
                        if len(parts) > 2:
                            print_command_notice("make accepts at most one optional name.", "Try: make second_bottle")
                        elif sim is not None and not sim.state.sealed and has_crafting_content(sim):
                            print_command_notice(
                                "finish or seal the current open terrarium before starting another.",
                                "Try: seal",
                            )
                        else:
                            creation_serial += 1
                            sim = make_followup_sim(args, creation_serial)
                            open_name = parts[1] if len(parts) == 2 else ""
                            name = f" '{open_name}'" if open_name else ""
                            print(f"Started a new open terrarium{name}.")
                            print(render_dashboard(sim, compact=True))
                    elif command in {"bottles", "terrariums"}:
                        print(manager.render_list())
                    elif command in {"source", "play", "script"}:
                        source_target = raw.split(maxsplit=1)
                        if len(source_target) != 2:
                            print_command_notice(f"{command} needs a command file path.", f"Try: {command} recipe.txt")
                            continue
                        path = Path(source_target[1])
                        try:
                            commands = split_command_batch(path.read_text(encoding="utf-8"))
                        except OSError as exc:
                            print_command_notice(f"could not read {path}: {exc}", "Nothing changed.")
                            continue
                        if not commands:
                            print_command_notice(f"{path} contains no commands.", "Nothing changed.")
                            continue
                        pending_commands = commands + pending_commands
                        print(f"queued {len(commands)} command(s) from {path}")
                    elif command in {"pause", "resume", "sleep", "wake", "discard", "delete", "remove"}:
                        if len(parts) != 2:
                            print_command_notice(f"{command} needs a bottle id.", f"Try: {command} B01")
                        else:
                            try:
                                if command in {"pause", "sleep"}:
                                    bottle = manager.pause(parts[1])
                                elif command in {"discard", "delete", "remove"}:
                                    bottle = manager.remove(parts[1])
                                else:
                                    bottle = manager.resume(parts[1])
                            except ValueError as exc:
                                print_bottle_notice(str(exc))
                                continue
                            if command in {"discard", "delete", "remove"}:
                                name = f" {bottle.name}" if bottle.name else ""
                                print(f"{bottle.bottle_id}{name} removed from the bottle list.")
                            else:
                                status = "paused" if command in {"pause", "sleep"} else "running"
                                print(f"{bottle.bottle_id} is now {status}.")
                    elif command == "bottle":
                        handle_bottle_command(manager, parts[1:])
                    elif command == "space":
                        if sim is None:
                            print_command_notice("there is no open terrarium to inspect.", "Use bottle status B01 or make a new terrarium.")
                            continue
                        handle_space_command(sim, parts[1:])
                    elif command == "save":
                        if len(parts) != 2:
                            raise ValueError("usage: save <path>")
                        managed_bottle = None if sim is not None else first_managed_bottle(manager)
                        target = sim or (managed_bottle.sim if managed_bottle is not None else None)
                        if target is None:
                            print_command_notice("there is no terrarium to save.", "Use make [name] to start crafting.")
                            continue
                        save_path = Path(parts[1])
                        save_path.write_text(target.state.to_json() + "\n", encoding="utf-8")
                        if managed_bottle is not None:
                            source = normalized_source_path(save_path)
                            managed_bottle.source_path = source
                            manager._deleted_sources.discard(source)
                        print(f"saved {parts[1]}")
                    else:
                        print(f"Nothing changed: unknown command '{command}'. Type 'help' to see available commands.")
            except ValueError as exc:
                print_command_notice(str(exc), "Type 'help' to see the command list.")
    finally:
        save_game_state(manager, game_state_path)
        manager.stop()
    return 0


def normalize_name(name: str) -> str:
    return name.lower().replace("-", "_")


def split_command_batch(raw: str) -> list[str]:
    commands: list[str] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        for segment in stripped.split(";"):
            command = segment.strip()
            if command and not command.startswith("#"):
                commands.append(command)
    return commands


def render_shell_home(sim: Terrarium | None, manager: SurvivalManager) -> str:
    width = min(get_terminal_size((96, 24)).columns, 118)
    width = max(width, 58)
    inner = width - 2
    rule = "+" + "-" * inner + "+"

    def fit_text(text: str, width: int) -> str:
        if width <= 0:
            return ""
        if len(text) <= width:
            return text
        if width <= 3:
            return "." * width
        return shorten(text, width=width, placeholder="...")

    def row(text: str = "") -> str:
        fitted = fit_text(text, inner - 2)
        return "| " + fitted.ljust(inner - 2) + " |"

    def bottle_summary(bottle: ManagedBottle, hint_width: int) -> str:
        day, hour = manager.survival_day_hour(bottle.sim)
        status = "dead" if bottle.dead else ("running" if bottle.running else "paused")
        score = bottle.sim.stability_score()
        name = bottle.name or "unnamed"
        full = (
            f"{bottle.bottle_id} {name} {status} day {day} {hour:02d}:00 "
            f"tick {bottle.sim.state.tick:05d} stability {score:03d}/100"
        )
        if len(full) <= hint_width:
            return full

        fixed = (
            f"{bottle.bottle_id}  {status} day {day} {hour:02d}:00 "
            f"tick {bottle.sim.state.tick:05d} stability {score:03d}/100"
        )
        name_width = max(0, hint_width - len(fixed))
        if name_width >= 4:
            clipped_name = fit_text(name, name_width)
            candidate = (
                f"{bottle.bottle_id} {clipped_name} {status} day {day} {hour:02d}:00 "
                f"tick {bottle.sim.state.tick:05d} stability {score:03d}/100"
            )
            if len(candidate) <= hint_width:
                return candidate

        no_name = (
            f"{bottle.bottle_id} {status} day {day} {hour:02d}:00 "
            f"tick {bottle.sim.state.tick:05d} stability {score:03d}/100"
        )
        if len(no_name) <= hint_width:
            return no_name

        compact = f"{bottle.bottle_id} {status} d{day} {hour:02d}:00 stability {score:03d}/100"
        if len(compact) <= hint_width:
            return compact
        return f"{bottle.bottle_id} {status} stability {score:03d}/100"

    bottle_art = [
        "      _______",
        "     /       \\",
        "    /  . . .  \\",
        "   |  /_/_/   |",
        "   |  terr    |",
        "   |__________|",
    ]
    lines = [
        rule,
        row("TERRARIUM"),
        row("closed ecosystem terminal game"),
        row(),
    ]

    if sim is None:
        gap = "   "
        available = inner - 2
        hint_width = max(24, available - max(len(art) for art in bottle_art) - len(gap))
        with manager.lock:
            bottles = list(manager._bottles)
            running_count = sum(1 for bottle in bottles if bottle.running and not bottle.dead)
        hints = [
            f"BOTTLES running {running_count}/{len(bottles)}  scale {manager.time_scale:g}x",
        ]
        if bottles:
            visible_bottles = bottles[:4]
            hints.extend(bottle_summary(bottle, hint_width) for bottle in visible_bottles)
            remaining = len(bottles) - len(visible_bottles)
            if remaining > 0:
                hints.append(f"... {remaining} more bottle(s); use bottles")
        else:
            hints.append("empty")
        hints.extend(
            [
                "make [name] starts a new bottle",
                "bottle status B01 observes a sealed one",
                "paste commands or use source recipe.txt",
                "help shows every command",
            ]
        )
    else:
        state = sim.state
        phase = "sealed" if state.sealed else "crafting"
        used_height = sim.substrate_height_cm()
        watered = state.soil_moistened_ml + state.sprayed_ml
        hints = [
            f"mode: {phase}   container: {state.container.key}",
            f"substrate: {used_height:0.1f}/{state.container.height_cm:0.1f}cm   watered: {watered:0.0f}ml",
            f"plants: {len(state.plantings)}   animals: {len(state.animal_groups)}",
            "next: substrate -> water -> hardscape -> life -> seal",
            "paste commands or use source recipe.txt",
            "status opens the full dashboard",
        ]

    gap = "   "
    for index in range(max(len(bottle_art), len(hints))):
        art = bottle_art[index] if index < len(bottle_art) else ""
        hint = hints[index] if index < len(hints) else ""
        prefix = art + gap if art else ""
        hint_width = max(0, inner - 2 - len(prefix))
        lines.append(row(prefix + fit_text(hint, hint_width)))

    lines.extend(
        [
            row(),
            row("quick: help | status | source recipe.txt | bottles | quit"),
            rule,
        ]
    )
    return "\n".join(lines)


def make_followup_sim(args: argparse.Namespace, serial: int) -> Terrarium:
    followup_args = argparse.Namespace(**vars(args))
    if getattr(args, "seed", None) is not None:
        followup_args.seed = args.seed + serial
    return make_sim(followup_args)


def has_crafting_content(sim: Terrarium) -> bool:
    state = sim.state
    return any(
        (
            state.substrate_layers,
            state.hardscape_items,
            state.plantings,
            state.animal_groups,
            state.soil_moistened_ml > 0,
            state.sprayed_ml > 0,
            state.container.key != "standard_1l",
        )
    )


def first_managed_sim(manager: SurvivalManager) -> Terrarium | None:
    bottle = first_managed_bottle(manager)
    return bottle.sim if bottle is not None else None


def first_managed_bottle(manager: SurvivalManager) -> ManagedBottle | None:
    if not manager._bottles:
        return None
    return manager._bottles[0]


def parse_height(value: str, container_height_cm: float) -> float:
    raw = value.strip().lower()
    try:
        if raw.endswith("%"):
            percent = float(raw[:-1])
            return container_height_cm * percent / 100.0
        if raw.endswith("cm"):
            return float(raw[:-2])
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"invalid height '{value}', use a value like 2cm or 10%") from exc


def parse_substrate_mix(value: str) -> dict[str, float]:
    mix: dict[str, float] = {}
    for entry in value.replace(";", ",").split(","):
        item = entry.strip()
        if not item:
            continue
        if "=" not in item:
            raise ValueError("mixture entries must look like material=percent")
        name, percent = item.split("=", 1)
        key = normalize_name(name.strip())
        try:
            parsed_percent = float(percent.strip().rstrip("%"))
        except ValueError as exc:
            raise ValueError(f"invalid percent '{percent.strip()}', use numbers like 30 or 30%") from exc
        mix[key] = mix.get(key, 0.0) + parsed_percent
    if not mix:
        raise ValueError("mixture cannot be empty")
    return mix


def parse_percent(value: str) -> float:
    raw = value.strip().rstrip("%")
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"invalid percent '{value}', use a value like 8% or 8") from exc


def parse_ml(value: str) -> float:
    raw = value.strip().lower()
    if raw.endswith("ml"):
        raw = raw[:-2]
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"invalid milliliter amount '{value}', use a value like 30ml or 30") from exc


def parse_count(value: str) -> int:
    try:
        count = int(value.strip())
    except ValueError as exc:
        raise ValueError(f"invalid count '{value}', use a whole number like 5") from exc
    return count


def parse_coordinate(value: str) -> float:
    raw = value.strip().rstrip("%")
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"invalid coordinate '{value}', use a number from 0 to 100") from exc


def parse_degrees(value: str) -> float:
    raw = value.strip().lower()
    if raw.endswith("deg"):
        raw = raw[:-3]
    elif raw.endswith("d"):
        raw = raw[:-1]
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"invalid angle '{value}', use degrees like 45 or 45deg") from exc


def parse_ratio(value: str) -> float:
    raw = value.strip().lower()
    try:
        if raw.endswith("%"):
            return float(raw[:-1]) / 100.0
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"invalid ratio '{value}', use 0.35 or 35%") from exc


def parse_hour(value: str) -> int:
    raw = value.strip().lower()
    if raw.endswith(":00"):
        raw = raw[:-3]
    if raw.endswith("h"):
        raw = raw[:-1]
    try:
        hour = int(raw)
    except ValueError as exc:
        raise ValueError(f"invalid hour '{value}', use whole hours like 7 or 19") from exc
    if hour < 0 or hour > 24:
        raise ValueError("hour must be between 0 and 24")
    return 0 if hour == 24 else hour


def parse_duration_hours(value: str) -> int:
    raw = value.strip().lower()
    if raw.endswith("hours"):
        raw = raw[:-5]
    elif raw.endswith("hour"):
        raw = raw[:-4]
    elif raw.endswith("hrs"):
        raw = raw[:-3]
    elif raw.endswith("hr"):
        raw = raw[:-2]
    elif raw.endswith("h"):
        raw = raw[:-1]
    try:
        duration = int(raw)
    except ValueError as exc:
        raise ValueError(f"invalid duration '{value}', use whole hours like 10h or 10") from exc
    return duration


def parse_hour_range(value: str) -> tuple[int, int]:
    if "-" not in value:
        raise ValueError("lamp schedule must look like 7-19")
    start_raw, end_raw = value.split("-", 1)
    start = parse_hour(start_raw)
    end = parse_hour(end_raw)
    duration = (end - start) % 24
    if duration == 0:
        duration = 24
    return start, duration


def parse_slope_value(value: str) -> float:
    raw = value.strip().lower()
    if raw.endswith("cm"):
        raw = raw[:-2]
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"invalid slope '{value}', use values like 0.6 or -0.4cm") from exc


def parse_layer_slope(value: str) -> tuple[float, float]:
    raw = value.strip()
    if not raw:
        raise ValueError("slope cannot be empty")
    x_slope = 0.0
    y_slope = 0.0
    if ":" in raw:
        for entry in raw.replace(";", ",").split(","):
            if not entry.strip():
                continue
            if ":" not in entry:
                raise ValueError("slope entries must look like x:0.5,y:-0.2")
            axis, amount = entry.split(":", 1)
            axis_key = normalize_name(axis)
            if axis_key not in {"x", "y"}:
                raise ValueError("slope axes must be x or y")
            if axis_key == "x":
                x_slope = parse_slope_value(amount)
            else:
                y_slope = parse_slope_value(amount)
        return x_slope, y_slope

    parts = [part.strip() for part in raw.split(",")]
    if len(parts) == 1:
        return parse_slope_value(parts[0]), 0.0
    if len(parts) == 2:
        return parse_slope_value(parts[0]), parse_slope_value(parts[1])
    raise ValueError("slope must look like slope=0.6,-0.2 or slope=x:0.6,y:-0.2")


def looks_like_percent(value: str) -> bool:
    raw = value.strip()
    if raw.endswith("%"):
        raw = raw[:-1]
    try:
        float(raw)
    except ValueError:
        return False
    return True


def looks_like_count(value: str) -> bool:
    raw = value.strip()
    numeric = raw.lstrip("+-")
    return numeric.isdigit() or (numeric.count(".") == 1 and numeric.replace(".", "").isdigit())


def split_coordinate_options(tokens: list[str]) -> tuple[list[str], float | None, float | None]:
    remaining: list[str] = []
    x: float | None = None
    y: float | None = None
    for token in tokens:
        lower = token.lower()
        if lower.startswith("x="):
            x = parse_coordinate(token.split("=", 1)[1])
        elif lower.startswith("y="):
            y = parse_coordinate(token.split("=", 1)[1])
        else:
            remaining.append(token)
    return remaining, x, y


def handle_substrate_command(sim: Terrarium, args: list[str]) -> None:
    if not args or args[0] in {"status", "layers", "stack"}:
        print(render_substrate_stack(sim))
        return

    subcommand = args[0].lower()
    if subcommand in {"help", "h", "?"}:
        print_substrate_help()
        return
    if subcommand in {"catalog", "list"}:
        print_substrate_catalog()
        return
    if subcommand == "mesh":
        if len(args) != 1:
            print_command_notice("substrate mesh takes no extra arguments.", "Try: substrate mesh")
            return
        try:
            sim.install_mesh_barrier()
        except ValueError as exc:
            print_substrate_notice(str(exc))
            return
        print("placed mesh screen layer")
        print(render_substrate_stack(sim))
        return
    if subcommand == "add":
        if len(args) < 4:
            print_command_notice(
                "substrate add needs a layer, height, and mixture.",
                "Try: substrate add drainage 2cm leca=70,pumice=30",
            )
            return
        layer_kind = args[1]
        try:
            height_cm = parse_height(args[2], sim.state.container.height_cm)
            mix_tokens: list[str] = []
            slope_x = 0.0
            slope_y = 0.0
            for token in args[3:]:
                key, separator, value = token.partition("=")
                option = normalize_name(key)
                if separator and option == "slope":
                    slope_x, slope_y = parse_layer_slope(value)
                elif separator and option in {"slopex", "slope_x", "x_slope"}:
                    slope_x = parse_slope_value(value)
                elif separator and option in {"slopey", "slope_y", "y_slope"}:
                    slope_y = parse_slope_value(value)
                else:
                    mix_tokens.append(token)
            mixture = parse_substrate_mix(",".join(mix_tokens))
            layer = sim.add_substrate(layer_kind, height_cm, mixture, slope_x, slope_y)
        except ValueError as exc:
            print_substrate_notice(str(exc))
            return
        print(f"added {layer.height_cm:0.2f} cm to {layer.layer_kind}")
        print(render_substrate_stack(sim))
        return
    if subcommand in {"dig", "remove"}:
        if len(args) != 2:
            print_command_notice(
                "substrate dig needs exactly one height.",
                "Try: substrate dig 1cm",
            )
            return
        try:
            height_cm = parse_height(args[1], sim.state.container.height_cm)
            removed = sim.dig_substrate(height_cm)
        except ValueError as exc:
            print_substrate_notice(str(exc))
            return
        print(f"dug out {removed.height_cm:0.2f} cm from {removed.layer_kind}")
        print(render_substrate_stack(sim))
        return

    print_command_notice(
        f"unknown substrate action '{subcommand}'.",
        "Use: substrate status, substrate catalog, substrate add, or substrate dig.",
    )


def handle_hardscape_command(sim: Terrarium, args: list[str]) -> None:
    if not args or args[0] in {"status", "list"}:
        print(render_hardscape(sim))
        return

    subcommand = args[0].lower()
    if subcommand in {"help", "h", "?"}:
        print_hardscape_help()
        return
    if subcommand == "catalog":
        print_hardscape_catalog()
        return
    if subcommand in {"place", "add"}:
        if len(args) < 2:
            print_command_notice(
                "hardscape place needs a decoration kind.",
                "Try: hardscape place river_stone 8% edge flat",
            )
            return
        kind = args[1]
        try:
            option_tokens, x_percent, y_percent = split_coordinate_options(args[2:])
            coverage = None
            position = "center"
            orientation = "flat"
            angle_deg = None
            tilt_deg = None
            for token in option_tokens:
                normalized = normalize_name(token)
                if coverage is None and looks_like_percent(token):
                    coverage = parse_percent(token)
                elif normalized in HARDSCAPE_POSITIONS:
                    position = token
                elif normalized in HARDSCAPE_ORIENTATIONS:
                    orientation = token
                elif normalized.startswith("angle=") or normalized.startswith("rot=") or normalized.startswith("rotation="):
                    angle_deg = parse_degrees(token.split("=", 1)[1])
                elif normalized.startswith("tilt="):
                    tilt_deg = parse_degrees(token.split("=", 1)[1])
                else:
                    raise ValueError(f"unknown hardscape option '{token}'")
            item = sim.place_hardscape(kind, coverage, position, orientation, x_percent, y_percent, angle_deg, tilt_deg)
        except ValueError as exc:
            print_hardscape_notice(str(exc))
            return
        placed = HARDSCAPES[item.kind].display_name
        print(f"placed {item.item_id} {placed} covering {item.coverage_percent:0.1f}%")
        print(render_hardscape(sim))
        return
    if subcommand in {"pick", "remove"}:
        if len(args) != 2:
            print_command_notice("hardscape pick needs an item id.", "Try: hardscape pick H01")
            return
        try:
            item = sim.pick_hardscape(args[1])
        except ValueError as exc:
            print_hardscape_notice(str(exc))
            return
        print(f"picked {item.item_id} {HARDSCAPES[item.kind].display_name}")
        print(render_hardscape(sim))
        return

    print_command_notice(
        f"unknown hardscape action '{subcommand}'.",
        "Use: hardscape status, hardscape catalog, hardscape place, or hardscape pick.",
    )


def handle_plant_command(sim: Terrarium, args: list[str]) -> None:
    if not args or args[0] in {"status", "list"}:
        print(render_plantings(sim))
        return

    subcommand = args[0].lower()
    if subcommand in {"help", "h", "?"}:
        print_plant_help()
        return
    if subcommand in {"growth", "grow", "life"}:
        print(render_plant_growth(sim))
        return
    if subcommand == "catalog":
        category = args[1] if len(args) > 1 else None
        print_plant_catalog(category)
        return
    if subcommand == "info":
        if len(args) != 2:
            print_command_notice("plant info needs a plant key.", "Try: plant info fittonia_mini")
            return
        try:
            print_plant_info(args[1])
        except ValueError as exc:
            print_plant_notice(str(exc))
        return
    if subcommand in {"add", "place"}:
        if len(args) < 2:
            print_command_notice("plant add needs a plant key.", "Try: plant add fittonia_mini 5% soil")
            return
        plant = args[1]
        area = None
        site = "surface"
        try:
            option_tokens, x_percent, y_percent = split_coordinate_options(args[2:])
            for token in option_tokens:
                if area is None and looks_like_percent(token):
                    area = parse_percent(token)
                elif token.lower().startswith("site="):
                    site = token.split("=", 1)[1]
                elif site == "surface":
                    site = token
                else:
                    raise ValueError(f"unknown plant option '{token}'")
            planting = sim.add_planting(plant, area, site, x_percent, y_percent)
        except ValueError as exc:
            print_plant_notice(str(exc))
            return
        print(f"planted {planting.planting_id} {PLANTS[planting.plant].display_name} using {planting.area_percent:0.1f}%")
        print(render_plantings(sim))
        return
    if subcommand in {"remove", "pick"}:
        if len(args) != 2:
            print_command_notice("plant remove needs a planting id.", "Try: plant remove P01")
            return
        try:
            planting = sim.remove_planting(args[1])
        except ValueError as exc:
            print_plant_notice(str(exc))
            return
        print(f"removed {planting.planting_id} {PLANTS[planting.plant].display_name}")
        print(render_plantings(sim))
        return
    if subcommand == "prune":
        if len(args) != 4 or args[2].lower() != "roots":
            print_command_notice("plant prune needs an id and root percent.", "Try: plant prune P01 roots 20%")
            return
        try:
            percent = parse_percent(args[3])
            planting = sim.prune_roots(args[1], percent)
        except ValueError as exc:
            print_plant_notice(str(exc))
            return
        print(
            f"pruned {planting.planting_id} roots by {percent:0.1f}% "
            f"(root mass {planting.root_mass_percent:0.1f}%, stress {planting.prune_stress:0.1f})"
        )
        print(render_plantings(sim))
        return

    print_command_notice(
        f"unknown plant action '{subcommand}'.",
        "Use: plant status, plant growth, plant catalog, plant info, plant add, plant remove, or plant prune.",
    )


def handle_animal_command(sim: Terrarium, args: list[str]) -> None:
    if not args or args[0] in {"status", "list"}:
        print(render_animals(sim))
        return

    subcommand = args[0].lower()
    if subcommand in {"help", "h", "?"}:
        print_animal_help()
        return
    if subcommand == "catalog":
        role = args[1] if len(args) > 1 else None
        print_animal_catalog(role)
        return
    if subcommand == "info":
        if len(args) != 2:
            print_command_notice("animal info needs an animal key.", "Try: animal info springtail")
            return
        try:
            print_animal_info(args[1])
        except ValueError as exc:
            print_animal_notice(str(exc))
        return
    if subcommand in {"add", "place"}:
        if len(args) < 2:
            print_command_notice("animal add needs an animal key.", "Try: animal add springtail 30 soil")
            return
        animal = args[1]
        count = None
        site = "substrate"
        try:
            option_tokens, x_percent, y_percent = split_coordinate_options(args[2:])
            for token in option_tokens:
                if count is None and looks_like_count(token):
                    count = parse_count(token)
                elif token.lower().startswith("site="):
                    site = token.split("=", 1)[1]
                elif site == "substrate":
                    site = token
                else:
                    raise ValueError(f"unknown animal option '{token}'")
            group = sim.add_animals(animal, count, site, x_percent, y_percent)
        except ValueError as exc:
            print_animal_notice(str(exc))
            return
        print(f"added {group.group_id} {ANIMALS[group.animal].display_name} x{group.count}")
        print(render_animals(sim))
        return
    if subcommand in {"remove", "pick"}:
        if len(args) != 2:
            print_command_notice("animal remove needs a group id.", "Try: animal remove A01")
            return
        try:
            group = sim.remove_animal_group(args[1])
        except ValueError as exc:
            print_animal_notice(str(exc))
            return
        print(f"removed {group.group_id} {ANIMALS[group.animal].display_name} x{group.count}")
        print(render_animals(sim))
        return

    print_command_notice(
        f"unknown animal action '{subcommand}'.",
        "Use: animal status, animal catalog, animal info, animal add, or animal remove.",
    )


def handle_moisten_command(sim: Terrarium, args: list[str]) -> None:
    if not args:
        print_command_notice("moisten needs an amount in milliliters.", "Try: moisten 30ml")
        return
    amount_token = args[1] if len(args) == 2 and args[0].lower() == "soil" else args[0]
    if len(args) > 2 or (len(args) == 2 and args[0].lower() != "soil"):
        print_command_notice("moisten only needs an optional 'soil' and an ml amount.", "Try: moisten soil 30ml")
        return
    try:
        amount_ml = parse_ml(amount_token)
        sim.moisten_soil(amount_ml)
    except ValueError as exc:
        print_moisten_notice(str(exc))
        return
    print(f"moistened soil with {amount_ml:0.1f} ml")
    print(render_substrate_stack(sim))


def handle_spray_command(sim: Terrarium, args: list[str]) -> None:
    if len(args) != 1:
        print_command_notice("spray needs a number of pumps.", "Try: spray 5")
        return
    try:
        pumps = parse_count(args[0])
        amount_ml = sim.spray(pumps)
    except ValueError as exc:
        print_spray_notice(str(exc))
        return
    print(f"sprayed {pumps} time(s), adding about {amount_ml:0.1f} ml")
    print(render_space(sim))


def handle_space_command(sim: Terrarium, args: list[str]) -> None:
    if args and args[0] not in {"status", "s"}:
        print_command_notice("space only supports status for now.", "Try: space status")
        return
    print(render_space(sim))


def handle_container_command(sim: Terrarium, args: list[str]) -> None:
    if not args or args[0] in {"status", "s"}:
        print_container_status(sim)
        return

    subcommand = args[0].lower()
    if subcommand in {"help", "h", "?"}:
        print_container_help()
        return
    if subcommand in {"catalog", "list"}:
        print_container_catalog()
        return
    if subcommand in {"set", "use", "select"}:
        if len(args) != 2:
            print_command_notice("container set needs a container key.", "Try: container set horizontal_jar")
            return
        try:
            selected = sim.set_container(args[1])
        except ValueError as exc:
            print_container_notice(str(exc))
            return
        print(f"selected container {selected.key}: {selected.display_name}")
        print_container_status(sim)
        return

    print_command_notice(
        f"unknown container action '{subcommand}'.",
        "Use: container status, container catalog, or container set <key>.",
    )


def handle_placement_command(sim: Terrarium, args: list[str]) -> None:
    if not args or args[0] in {"status", "s"}:
        print(render_placement(sim))
        return

    subcommand = args[0].lower()
    if subcommand in {"help", "h", "?"}:
        print_placement_help()
        return
    if subcommand == "window":
        if len(args) != 2:
            print_command_notice("placement window needs a direction.", "Try: placement window east")
            return
        try:
            direction = sim.set_window(args[1])
        except ValueError as exc:
            print_placement_notice(str(exc))
            return
        print(f"set window to {direction}-facing")
        print(render_placement(sim))
        return
    if subcommand in {"face", "facing", "angle"}:
        if len(args) != 2:
            print_command_notice("placement face needs an angle.", "Try: placement face 135")
            return
        try:
            angle = sim.set_window_facing(parse_degrees(args[1]))
        except ValueError as exc:
            print_placement_notice(str(exc))
            return
        print(f"set terrarium face toward window to {angle:0.1f}deg")
        print(render_placement(sim))
        return
    if subcommand in {"umbrella", "parasol", "sunshade", "shade"}:
        umbrella_args = args[1:]
        if umbrella_args and umbrella_args[0].lower() in {"off", "remove", "pick", "none"}:
            if not sim.state.umbrella_enabled:
                print_command_notice("the shade umbrella is already off.", "Try: placement umbrella 120% south leaning_north")
                return
            sim.clear_umbrella()
            print("turned shade umbrella off")
            print(render_placement(sim))
            return
        try:
            option_tokens, x_percent, y_percent = split_coordinate_options(umbrella_args)
            coverage = None
            position = "center"
            orientation = "flat"
            angle_deg = None
            tilt_deg = None
            for token in option_tokens:
                normalized = normalize_name(token)
                if coverage is None and looks_like_percent(token):
                    coverage = parse_percent(token)
                elif normalized in HARDSCAPE_POSITIONS:
                    position = token
                elif normalized in HARDSCAPE_ORIENTATIONS:
                    orientation = token
                elif normalized.startswith("angle=") or normalized.startswith("rot=") or normalized.startswith("rotation="):
                    angle_deg = parse_degrees(token.split("=", 1)[1])
                elif normalized.startswith("tilt="):
                    tilt_deg = parse_degrees(token.split("=", 1)[1])
                else:
                    raise ValueError(f"unknown umbrella option '{token}'")
            sim.set_umbrella(coverage, position, orientation, x_percent, y_percent, angle_deg, tilt_deg)
        except ValueError as exc:
            print_placement_notice(str(exc))
            return
        print(f"set shade umbrella area {sim.state.umbrella_coverage_percent:0.1f}%")
        print(render_placement(sim))
        return
    if subcommand in {"lamp", "moss_lamp", "mosslight"}:
        if len(args) == 2 and args[1].lower() in {"off", "remove", "none"}:
            sim.clear_moss_lamp()
            print("turned moss lamp off")
            print(render_placement(sim))
            return
        if len(args) == 3 and args[1].lower() == "schedule":
            try:
                start, duration = parse_hour_range(args[2])
                sim.set_moss_lamp_schedule(start, duration)
            except ValueError as exc:
                print_placement_notice(str(exc))
                return
            print(f"set moss lamp schedule to {start:02d}:00 for {duration}h")
            print(render_placement(sim))
            return
        if len(args) == 3 and args[1].lower() == "timer":
            try:
                duration = parse_duration_hours(args[2])
                sim.set_moss_lamp_schedule(sim.state.moss_lamp_start_hour, duration)
            except ValueError as exc:
                print_placement_notice(str(exc))
                return
            print(f"set moss lamp timer to {duration}h")
            print(render_placement(sim))
            return
        if len(args) not in {2, 3, 5}:
            print_command_notice("placement lamp needs an angle and optional intensity.", "Try: placement lamp 45 0.35 schedule 7-19")
            return
        try:
            angle = parse_degrees(args[1])
            intensity = parse_ratio(args[2]) if len(args) == 3 else None
            if len(args) == 5:
                intensity = parse_ratio(args[2])
                if args[3].lower() == "schedule":
                    start, duration = parse_hour_range(args[4])
                    sim.set_moss_lamp_schedule(start, duration)
                elif args[3].lower() == "timer":
                    duration = parse_duration_hours(args[4])
                    sim.set_moss_lamp_schedule(sim.state.moss_lamp_start_hour, duration)
                else:
                    raise ValueError("lamp extra option must be schedule or timer")
            sim.set_moss_lamp(angle, intensity)
        except ValueError as exc:
            print_placement_notice(str(exc))
            return
        print(f"set moss lamp to {sim.state.moss_lamp_angle_deg:0.1f}deg")
        print(render_placement(sim))
        return

    print_command_notice(
        f"unknown placement action '{subcommand}'.",
        "Use: placement status, placement window, placement face, placement umbrella, or placement lamp.",
    )


def handle_seal_command(sim: Terrarium, args: list[str]) -> bool:
    if args:
        print_command_notice("seal takes no extra arguments.", "Try: seal")
        return False
    try:
        sim.seal()
    except ValueError as exc:
        print_seal_notice(str(exc))
        return False
    print(render_seal_report(sim))
    return True


def handle_bottle_command(manager: SurvivalManager, args: list[str]) -> None:
    if not args or args[0] in {"list", "status"} and len(args) == 1:
        print(manager.render_list())
        return

    subcommand = args[0].lower()
    if subcommand in {"help", "h", "?"}:
        print_bottle_help()
        return
    if subcommand == "status":
        if len(args) != 2:
            print_command_notice("bottle status needs a bottle id.", "Try: bottle status B01")
            return
        try:
            bottle = manager.get(args[1])
        except ValueError as exc:
            print_bottle_notice(str(exc))
            return
        print(render_dashboard(bottle.sim))
        return
    if subcommand in {"plants", "plant", "growth", "grow"}:
        if len(args) != 2:
            print_command_notice("bottle plants needs a bottle id.", "Try: bottle plants B01")
            return
        try:
            bottle = manager.get(args[1])
        except ValueError as exc:
            print_bottle_notice(str(exc))
            return
        print(render_plant_growth(bottle.sim))
        return
    if subcommand in {"placement", "position", "light"}:
        if len(args) < 2:
            print_command_notice("bottle placement needs a bottle id.", "Try: bottle placement B01 status")
            return
        try:
            bottle = manager.get(args[1])
        except ValueError as exc:
            print_bottle_notice(str(exc))
            return
        handle_placement_command(bottle.sim, args[2:])
        return
    if subcommand == "pause":
        if len(args) != 2:
            print_command_notice("bottle pause needs a bottle id.", "Try: bottle pause B01")
            return
        try:
            bottle = manager.pause(args[1])
        except ValueError as exc:
            print_bottle_notice(str(exc))
            return
        print(f"{bottle.bottle_id} is now paused.")
        return
    if subcommand == "resume":
        if len(args) != 2:
            print_command_notice("bottle resume needs a bottle id.", "Try: bottle resume B01")
            return
        try:
            bottle = manager.resume(args[1])
        except ValueError as exc:
            print_bottle_notice(str(exc))
            return
        print(f"{bottle.bottle_id} is now running.")
        return
    if subcommand in {"remove", "delete", "discard", "drop"}:
        if len(args) != 2:
            print_command_notice("bottle remove needs a bottle id.", "Try: bottle remove B01")
            return
        try:
            bottle = manager.remove(args[1])
        except ValueError as exc:
            print_bottle_notice(str(exc))
            return
        name = f" {bottle.name}" if bottle.name else ""
        print(f"{bottle.bottle_id}{name} removed from the bottle list.")
        return

    print_command_notice(
        f"unknown bottle action '{subcommand}'.",
        "Use: bottle list, bottle status, bottle plants, bottle pause, bottle resume, or bottle remove.",
    )


def print_command_notice(message: str, suggestion: str | None = None) -> None:
    print(f"Nothing changed: {message}")
    if suggestion:
        print(f"Try again: {suggestion}")


def print_substrate_notice(message: str) -> None:
    suggestion = "Use 'substrate help' for examples or 'substrate status' to inspect the stack."
    if "must total 100 percent" in message:
        suggestion = "Make the mixture add up to 100, for example peat_moss=50,compost=30,perlite=20."
    elif "terrarium is sealed" in message:
        suggestion = "The bottle is sealed; use status, step, run, or save."
    elif "can only dig the current top layer" in message:
        suggestion = "Dig less, or remove the current top layer first before reaching lower layers."
    elif "not enough container height" in message:
        suggestion = "Use a smaller height or dig out some substrate first."
    elif "not enough container volume" in message:
        suggestion = "Use less height, remove bulky hardscape, or remove some plantings first."
    elif "unknown substrate" in message:
        suggestion = "Use 'substrate catalog' to see the available materials."
    elif "unknown substrate layer" in message:
        suggestion = "Use one of: drainage, purification, soil, amendment."
    elif "invalid height" in message:
        suggestion = "Use heights like 2cm, 0.5cm, or 10%."
    elif "slope" in message:
        suggestion = "Use a small slope like slope=0.6,-0.2 or slope=x:0.6,y:-0.2."
    elif "material=percent" in message or "invalid percent" in message:
        suggestion = "Write mixtures like leca=70,pumice=30."

    print_command_notice(message, suggestion)


def print_hardscape_notice(message: str) -> None:
    suggestion = "Use 'hardscape help' for examples or 'hardscape catalog' to inspect choices."
    if "unknown hardscape" in message:
        suggestion = "Use 'hardscape catalog' to see available decorations."
    elif "terrarium is sealed" in message:
        suggestion = "The bottle is sealed; use status, step, run, or save."
    elif "coverage should be between" in message:
        suggestion = "Use a coverage percentage inside the suggested range for that object."
    elif "not enough open surface" in message:
        suggestion = f"Keep total hardscape coverage at or below {MAX_HARDSCAPE_COVERAGE:g}%."
    elif "not enough container volume" in message:
        suggestion = "Use a smaller object or free some volume first."
    elif "hardscape collision" in message or "no clear hardscape placement" in message:
        suggestion = "Move it with x= and y=, use a smaller object, or pick another hardscape first."
    elif "unknown hardscape position" in message:
        suggestion = f"Use one of: {', '.join(HARDSCAPE_POSITIONS)}."
    elif "unknown hardscape orientation" in message:
        suggestion = f"Use one of: {', '.join(HARDSCAPE_ORIENTATIONS)}."
    elif "invalid percent" in message:
        suggestion = "Use percentages like 8%, 12.5%, or 8."
    elif "coordinates" in message or "coordinate" in message:
        suggestion = "Use x=0..100 and y=0..100 inside the round bottle footprint."
    elif "angle" in message or "tilt" in message:
        suggestion = "Use degrees like angle=35 or tilt=18."
    elif "unknown hardscape id" in message:
        suggestion = "Use 'hardscape status' to see placed item ids."

    print_command_notice(message, suggestion)


def print_plant_notice(message: str) -> None:
    suggestion = "Use 'plant help' for examples or 'plant catalog' to inspect choices."
    if "unknown plant" in message:
        suggestion = "Use 'plant catalog' to see available plants."
    elif "terrarium is sealed" in message:
        suggestion = "The bottle is sealed; use status, step, run, or save."
    elif "at least" in message and "planting area" in message:
        suggestion = "Use a larger area, or omit the area to use the plant's default starter size."
    elif "not enough plantable area" in message:
        suggestion = "Remove plants, pick hardscape, or choose a smaller starter plant."
    elif "not enough container volume" in message:
        suggestion = "Remove bulky hardscape or choose a smaller planting."
    elif "root zone collides" in message or "planting overlaps" in message or "no clear planting space" in message:
        suggestion = "Move it with x= and y=, use a smaller area, or remove nearby objects first."
    elif "unknown planting id" in message:
        suggestion = "Use 'plant status' to see planted ids."
    elif "unknown hardscape target" in message:
        suggestion = "Use 'hardscape status' to see available hardscape ids."
    elif "hardscape surface" in message or "has no" in message:
        suggestion = "Use hardscape:H01, hardscape:H01:side, :crack, :groove, or :underside if that object supports it."
    elif "cannot attach to hardscape" in message:
        suggestion = "Use moss, lichen, epiphytic ferns, mini orchids, or air bromeliads on hardscape."
    elif "not enough hardscape planting surface" in message:
        suggestion = "Use a smaller area, choose another hardscape, or place a larger stone/wood piece."
    elif "unknown planting site" in message:
        suggestion = "Use surface, soil, substrate, air, water, or hardscape:<id>[:surface]."
    elif "root prune percent" in message:
        suggestion = "Use a root prune between 1% and 90%, for example plant prune P01 roots 20%."
    elif "invalid percent" in message:
        suggestion = "Use percentages like 5%, 12.5%, or 5."
    elif "coordinates" in message or "coordinate" in message:
        suggestion = "Use x=0..100 and y=0..100 inside the round bottle footprint."

    print_command_notice(message, suggestion)


def print_animal_notice(message: str) -> None:
    suggestion = "Use 'animal help' for examples or 'animal catalog' to inspect choices."
    if "unknown animal" in message:
        suggestion = "Use 'animal catalog' to see available decomposers and small consumers."
    elif "terrarium is sealed" in message:
        suggestion = "The bottle is sealed; use status, step, run, or save."
    elif "at least" in message and "individual" in message:
        suggestion = "Use a count at or above that animal group's minimum, or omit the count."
    elif "at most" in message:
        suggestion = "Use fewer individuals; the active animal groups are intentionally space-limited."
    elif "not enough container volume" in message:
        suggestion = "Use fewer animals or free some container volume first."
    elif "unknown animal group id" in message:
        suggestion = "Use 'animal status' to see animal group ids."
    elif "unknown hardscape target" in message:
        suggestion = "Use 'hardscape status' to see available hardscape ids."
    elif "unknown animal site" in message:
        suggestion = "Use substrate, soil, leaf_litter, moss, surface, water, hardscape, or hardscape:<id>."
    elif "invalid count" in message:
        suggestion = "Use a whole number, for example animal add springtail 30."
    elif "coordinates" in message or "coordinate" in message:
        suggestion = "Use x=0..100 and y=0..100 inside the container footprint."

    print_command_notice(message, suggestion)


def print_moisten_notice(message: str) -> None:
    suggestion = "Use an amount in milliliters, for example moisten 30ml."
    if "too much water" in message:
        suggestion = "Use a smaller initial moistening amount, for example 20ml or 40ml."
    elif "terrarium is sealed" in message:
        suggestion = "The bottle is sealed; use status, step, run, or save."
    elif "not enough container volume" in message:
        suggestion = "Use less water or remove volume from the container first."
    elif "greater than 0 ml" in message:
        suggestion = "Use a positive amount, for example moisten 30ml."
    elif "invalid milliliter" in message:
        suggestion = "Write the amount as 30ml or 30."

    print_command_notice(message, suggestion)


def print_spray_notice(message: str) -> None:
    suggestion = "Use a positive whole number of sprays, for example spray 5."
    if "too high" in message:
        suggestion = "Use fewer sprays in one action."
    elif "terrarium is sealed" in message:
        suggestion = "The bottle is sealed; use status, step, run, or save."
    elif "not enough container volume" in message:
        suggestion = "Use fewer sprays or free some container volume first."
    elif "invalid count" in message:
        suggestion = "Use a whole number, for example spray 5."

    print_command_notice(message, suggestion)


def print_seal_notice(message: str) -> None:
    suggestion = "Use status, step, run, or save to continue observing."
    if "already sealed" in message:
        suggestion = "This bottle is already sealed; use status, step, run, or save."
    elif "not enough container volume" in message:
        suggestion = "Free some container volume before sealing."

    print_command_notice(message, suggestion)


def print_bottle_notice(message: str) -> None:
    suggestion = "Use 'bottles' to see current bottle ids."
    if "dead and cannot resume" in message:
        suggestion = "Dead bottles can be inspected or saved, but cannot be resumed."
    elif "unknown bottle id" in message:
        suggestion = "Use 'bottles' to see current bottle ids."

    print_command_notice(message, suggestion)


def print_placement_notice(message: str) -> None:
    suggestion = "Use 'placement help' for examples. Angles use 0=N, 90=E, 180=S, 270=W."
    if "window direction" in message:
        suggestion = "Use north, east, south, or west."
    elif "umbrella" in message or "hardscape" in message:
        suggestion = "Use placement umbrella 120% south leaning_north x=50 y=70 angle=180 tilt=20."
    elif "schedule" in message or "hour" in message or "duration" in message:
        suggestion = "Use schedules like placement lamp schedule 7-19 or placement lamp timer 10h."
    elif "intensity" in message or "ratio" in message:
        suggestion = "Use a lamp intensity from 0 to 1, for example 0.35 or 35%."
    elif "angle" in message:
        suggestion = "Use degrees like 45, 180, 270, or 45deg."
    print_command_notice(message, suggestion)


def print_container_notice(message: str) -> None:
    suggestion = "Use 'container catalog' to see available container keys."
    if "before adding" in message:
        suggestion = "Choose the container first, before water, substrate, hardscape, plants, or animals."
    elif "unknown container" in message:
        suggestion = "Use 'container catalog' and then 'container set <key>'."
    elif "sealed" in message:
        suggestion = "This bottle is sealed; start a new one with make [name]."
    print_command_notice(message, suggestion)


def print_container_status(sim: Terrarium) -> None:
    container = sim.state.container
    if container.footprint_shape == "round":
        shape = f"round dia {container.diameter_cm:0.1f}cm"
    else:
        shape = f"{container.footprint_shape} {container.length_cm:0.1f}x{container.width_cm:0.1f}cm"
    print(
        f"CONTAINER {container.key} - {container.display_name}\n"
        f"  capacity {container.capacity_ml:0.0f}ml  height {container.height_cm:0.1f}cm  {shape}\n"
        f"  base_area {container.base_area_cm2:0.2f}cm2  footprint {container.footprint_shape}"
    )


def print_container_catalog() -> None:
    print("Container choices are optional; default is standard_1l.")
    print("Choose before adding physical contents. Long containers use rectangular x/y coordinates.")
    for definition in CONTAINERS.values():
        spec = definition.spec()
        if spec.footprint_shape == "round":
            shape = f"round dia {spec.diameter_cm:0.1f}cm"
        else:
            shape = f"{spec.footprint_shape} {spec.length_cm:0.1f}x{spec.width_cm:0.1f}cm"
        aliases = f" aliases={','.join(definition.aliases)}" if definition.aliases else ""
        print(
            f"  {spec.key:16s} {spec.capacity_ml:4.0f}ml  "
            f"h={spec.height_cm:04.1f}cm  base={spec.base_area_cm2:06.2f}cm2  "
            f"{shape}  {spec.display_name}{aliases}"
        )


def print_container_help() -> None:
    print(
        "\n".join(
            [
                "Container commands:",
                "  container status",
                "  container catalog",
                "  container set <key>",
                "Examples:",
                "  container set tiny_vial",
                "  container set horizontal_jar",
                "  terrarium --container long_low_tank",
                "Container choice is optional, but must happen before adding physical contents.",
            ]
        )
    )


def print_placement_help() -> None:
    print(
        "\n".join(
            [
                "Placement commands:",
                "  placement status",
                "  placement window <north|east|south|west>",
                "  placement face <degrees>",
                "  placement umbrella [coverage%] [position] [orientation] [x=.. y=.. angle=.. tilt=..]",
                "  placement umbrella off",
                "  placement lamp <degrees> [intensity]",
                "  placement lamp <degrees> <intensity> schedule <start-end>",
                "  placement lamp schedule <start-end>",
                "  placement lamp timer <hours>",
                "  placement lamp off",
                "Examples:",
                "  placement window east",
                "  placement face 135",
                "  placement umbrella 120% south leaning_north",
                "  placement umbrella 135% x=55 y=70 angle=180 tilt=20",
                "  placement lamp 45 0.35",
                "  placement lamp 45 0.35 schedule 7-19",
                "  placement lamp timer 10h",
                "  bottle placement B01 lamp 270 25%",
                "Angle convention: 0=N, 90=E, 180=S, 270=W.",
            ]
        )
    )


def print_substrate_catalog() -> None:
    default = CONTAINERS["standard_1l"].spec()
    print(
        f"Default container: {default.capacity_ml:0.0f} ml cylinder, "
        f"height {default.height_cm:0.1f} cm, diameter {default.diameter_cm:0.1f} cm."
    )
    print("Use 'container catalog' before crafting to pick tiny, wide, tall, or horizontal containers.")
    print("Substrate groups are optional and can be layered freely:")
    for index, layer_kind in enumerate(SUBSTRATE_LAYER_ORDER, start=1):
        print(f"  {index}. {layer_kind:12s} {SUBSTRATE_LAYER_NAMES[layer_kind]}")
        for definition in SUBSTRATES.values():
            if definition.layer_kind != layer_kind:
                continue
            mix_note = " (can mix into soil)" if "soil" in definition.can_mix_in else ""
            print(
                f"     {definition.key:18s} water_ret={definition.water_retention:g}/10 "
                f"aeration={definition.aeration:g}/10{mix_note}"
            )


def print_hardscape_catalog() -> None:
    print(f"Hardscape can cover up to {MAX_HARDSCAPE_COVERAGE:g}% of the visible surface.")
    print("More cover reduces plantable area, but can reduce evaporation or create damp edges.")
    print("Fields: key, display name, coverage range, shape, geometry, aspect, surfaces, planting effects.")
    for definition in HARDSCAPES.values():
        surfaces = ",".join(definition.attach_surfaces) or "-"
        features = ",".join(definition.surface_features) if definition.surface_features else "-"
        print(
            f"  {definition.key:15s} {definition.display_name:16s} "
            f"{definition.min_coverage:g}-{definition.max_coverage:g}% default {definition.default_coverage:g}%  "
            f"{definition.shape}; geometry={definition.geometry_profile} "
            f"aspect={definition.footprint_aspect_ratio:0.1f} surfaces={surfaces} features={features} "
            f"block={definition.block_factor:0.2f} "
            f"shade={definition.shade_factor:0.2f} moisture_edge={definition.edge_moisture:0.2f}"
        )


def print_plant_catalog(category: str | None = None) -> None:
    selected_category = normalize_name(category) if category else None
    categories = sorted({definition.category for definition in PLANTS.values()})
    if selected_category and selected_category not in categories:
        print_command_notice(
            f"unknown plant category '{category}'.",
            f"Use one of: {', '.join(categories)}.",
        )
        return

    print("Planting only checks minimum area and remaining plantable space.")
    print("Environment needs are used during survival simulation, not as planting gates.")
    current = None
    for definition in sorted(PLANTS.values(), key=lambda item: (item.category, item.key)):
        if selected_category and definition.category != selected_category:
            continue
        if definition.category != current:
            current = definition.category
            print(f"{current}:")
        print(
            f"  {definition.key:24s} min {definition.min_area_percent:g}% "
            f"default {definition.default_area_percent:g}% mature {definition.mature_area_percent:g}%  "
            f"{definition.display_name}"
        )


def print_plant_info(name: str) -> None:
    definition = PLANTS[normalize_plant_key_for_cli(name)]
    print(f"{definition.key} - {definition.display_name}")
    print(f"  category={definition.category} form={definition.growth_form}")
    print(
        f"  area min/default/mature = {definition.min_area_percent:g}%/"
        f"{definition.default_area_percent:g}%/{definition.mature_area_percent:g}%"
    )
    print(f"  height={definition.height_cm:g}cm root_depth={definition.root_depth_cm:g}cm")
    print(
        "  needs "
        f"humidity={format_range(definition.humidity_range)} "
        f"temp={format_range(definition.temperature_range)}C "
        f"light={format_range(definition.light_range)} "
        f"water={format_range(definition.water_range)} "
        f"nutrition={format_range(definition.nutrition_range)} "
        f"aeration={format_range(definition.aeration_range)}"
    )
    print(
        "  physiology "
        f"photo={definition.photosynthesis_efficiency:0.2f} "
        f"nutrient_demand={definition.nutrient_demand:0.2f} "
        f"water_use={definition.water_use_rate:0.2f} "
        f"respiration={definition.respiration_rate:0.2f}"
    )
    print("  planting check: minimum area only; survival uses these needs after sealing.")
    if definition.notes:
        print(f"  note: {definition.notes}")


def print_animal_catalog(role: str | None = None) -> None:
    selected_role = normalize_name(role) if role else None
    roles = sorted({definition.role for definition in ANIMALS.values()})
    if selected_role and selected_role not in roles:
        print_command_notice(
            f"unknown animal role '{role}'.",
            f"Use one of: {', '.join(roles)}.",
        )
        return

    print("Animals are stored as groups, not individual named pets.")
    print("Predators are intentionally held for a future pest-control simulation.")
    current = None
    for definition in sorted(ANIMALS.values(), key=lambda item: (item.role, item.key)):
        if selected_role and definition.role != selected_role:
            continue
        if definition.role != current:
            current = definition.role
            print(f"{current}:")
        print(
            f"  {definition.key:22s} min {definition.min_count:g} "
            f"default {definition.default_count:g} max {definition.max_reasonable_count:g}  "
            f"{definition.display_name}"
        )


def print_animal_info(name: str) -> None:
    definition = ANIMALS[normalize_animal_key_for_cli(name)]
    print(f"{definition.key} - {definition.display_name}")
    print(f"  role={definition.role} size={definition.size_class} food={definition.food_source}")
    print(
        f"  count min/default/max = {definition.min_count}/"
        f"{definition.default_count}/{definition.max_reasonable_count}"
    )
    print(
        "  needs "
        f"humidity={format_range(definition.humidity_range)} "
        f"temp={format_range(definition.temperature_range)}C "
        f"water={format_range(definition.water_range)} "
        f"oxygen={format_range(definition.oxygen_range)}"
    )
    print(
        "  effects "
        f"detritus={definition.detritus_processing:0.2f} "
        f"mold={definition.mold_control:0.2f} "
        f"plant_risk={definition.plant_risk:0.2f}"
    )
    diet = ", ".join(f"{food}:{weight * 100:0.0f}%" for food, weight in definition.diet_weights)
    print(
        "  feeding "
        f"rate={definition.feeding_rate:0.2f} "
        f"assimilation={definition.assimilation_efficiency:0.2f} "
        f"waste={definition.waste_rate:0.2f} "
        f"respiration={definition.respiration_rate:0.2f} "
        f"diet={diet}"
    )
    print(
        "  life "
        f"growth={definition.base_growth_rate:0.4f} "
        f"repro={definition.reproduction_rate:0.4f} "
        f"mode={definition.reproduction_mode}"
    )
    print("  reproduction is slow and space-gated; predators are not active yet.")
    if definition.notes:
        print(f"  note: {definition.notes}")


def normalize_plant_key_for_cli(name: str) -> str:
    return canonical_plant_key(name)


def normalize_animal_key_for_cli(name: str) -> str:
    return canonical_animal_key(name)


def format_range(values: tuple[float, float]) -> str:
    return f"{values[0]:g}-{values[1]:g}"


def print_substrate_help() -> None:
    print(
        "\n".join(
            [
                "Substrate commands:",
                "  substrate status",
                "  substrate catalog",
                "  substrate mesh",
                "  substrate add <layer> <height> <material=percent,...> [slope=x,y]",
                "  substrate dig <height>",
                "Examples:",
                "  substrate add drainage 2cm leca=70,pumice=30",
                "  substrate mesh",
                "  substrate add purification 5% activated_charcoal=100",
                "  substrate add soil 4cm peat_moss=50,compost=30,perlite=20 slope=0.6,-0.2",
                "  substrate dig 1cm",
                "Heights accept cm or percent of the selected container height; slope is west-east,south-north cm.",
            ]
        )
    )


def print_hardscape_help() -> None:
    print(
        "\n".join(
            [
                "Hardscape commands:",
                "  hardscape status",
                "  hardscape catalog",
                "  hardscape place <kind> [coverage%] [position] [orientation] [x=0..100 y=0..100] [angle=deg tilt=deg]",
                "  hardscape pick <id>",
                "Examples:",
                "  hardscape place river_stone 8% edge flat",
                "  hardscape place driftwood 12% west leaning_east x=35 y=55 angle=25",
                "  hardscape place slate 14% center flat tilt=22 angle=120",
                "  hardscape place gravel_patch 18% center scattered",
                "  hardscape pick H01",
            ]
        )
    )


def print_plant_help() -> None:
    print(
        "\n".join(
            [
                "Plant commands:",
                "  plant status",
                "  plant growth",
                "  plant catalog [category]",
                "  plant info <plant>",
                "  plant add <plant> [area%] [site] [x=0..100 y=0..100]",
                "  plant remove <id>",
                "  plant prune <id> roots <percent%>",
                "Examples:",
                "  plant add fittonia_mini",
                "  plant add cushion_moss 10% surface",
                "  plant add rabbit_foot_fern 5% hardscape:H01:side",
                "  plant add cushion_moss 4% hardscape:H01:groove",
                "  plant add cushion_moss 6% x=35 y=55",
                "  plant prune P01 roots 20%",
                "Planting only checks minimum area and remaining plantable area.",
            ]
        )
    )


def print_animal_help() -> None:
    print(
        "\n".join(
            [
                "Animal commands:",
                "  animal status",
                "  animal catalog [role]",
                "  animal info <animal>",
                "  animal add <animal> [count] [site] [x=0..100 y=0..100]",
                "  animal remove <id>",
                "Examples:",
                "  animal add springtail 30 soil",
                "  animal add dwarf_white_isopod 8 leaf_litter",
                "  animal add micro_snail 3 moss x=45 y=60",
                "  animal remove A01",
                "Animals are optional groups; survival and reproduction are habitat-space limited.",
            ]
        )
    )


def print_bottle_help() -> None:
    print(
        "\n".join(
            [
                "Bottle commands:",
                "  bottles",
                "  bottle status <id>",
                "  bottle plants <id>",
                "  bottle placement <id> ...",
                "  bottle pause <id>",
                "  bottle resume <id>",
                "  bottle remove <id>",
                "  make [name]",
                "Examples:",
                "  bottles",
                "  bottle status B01",
                "  bottle plants B01",
                "  bottle placement B01 status",
                "  pause B01",
                "  bottle remove B01",
                "  make second_bottle",
            ]
        )
    )


def print_help() -> None:
    print(
        "\n".join(
            [
                "Commands:",
                "  status                 show full dashboard",
                "  step [n]               advance n hours, default 1",
                "  run [n] [interval]     advance n hours and print metrics",
                "  set <pool> <value>     set water/nutrients/oxygen/carbon_dioxide/detritus/toxicity/temperature/light_intensity",
                "  add <pop> <amount>     add plants/algae/grazers/microbes biomass",
                "  container ...          choose/list container sizes before crafting",
                "  substrate ...          add/dig/list terrarium substrate layers",
                "  mesh                   place an optional mesh screen layer",
                "  hardscape ...          place/pick/list surface decorations",
                "  placement ...          choose window, terrarium angle, shade umbrella, and moss lamp",
                "  plant ...              catalog/place/remove/prune/growth planted specimens",
                "  animal ...             catalog/add/remove animal groups",
                "  moisten <ml>           optionally moisten the soil before planting",
                "  spray <count>          mist the container; assumes 0.8ml per spray",
                "  seal                   finish crafting and close the bottle",
                "  make [name]            start crafting another terrarium after sealing",
                "  bottles                list sealed terrariums running in the background",
                "  pause/resume <id>      pause or resume a sealed terrarium simulation",
                "  discard/delete <id>    remove a sealed terrarium from the bottle list",
                "  space status           show 3D container volume budget",
                "  source <path>          run commands from a text recipe file",
                "  save <path>            save current state JSON",
                "  quit                   exit",
                "Multiple commands can share one line with ';'. Pasted multi-line commands run one line at a time.",
            ]
        )
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        return command_run(args)
    return command_shell(args)
