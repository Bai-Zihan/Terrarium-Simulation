from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import math
import random
from typing import Any


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


@dataclass(slots=True)
class SimulationConfig:
    """Tunable constants for the closed ecosystem model."""

    light_intensity: float = 0.86
    day_length: int = 24
    base_temperature: float = 18.0
    heat_gain: float = 8.0
    noise: float = 0.014
    carrying_capacity: float = 220.0


@dataclass(slots=True)
class FluxReport:
    photosynthesis: float = 0.0
    respiration: float = 0.0
    grazing: float = 0.0
    decay: float = 0.0
    stress: float = 0.0

    def as_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(slots=True)
class TerrariumState:
    tick: int = 0
    hour: int = 0
    light: float = 0.0
    temperature: float = 20.0
    water: float = 0.74
    nutrients: float = 0.58
    oxygen: float = 0.62
    carbon_dioxide: float = 0.39
    detritus: float = 0.22
    toxicity: float = 0.04
    plants: float = 72.0
    algae: float = 18.0
    grazers: float = 9.0
    microbes: float = 20.0
    seed: int | None = None
    events: list[str] = field(default_factory=list)
    flux: FluxReport = field(default_factory=FluxReport)

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return data

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True)


class Terrarium:
    """Small deterministic ecosystem model for a closed terrarium.

    The model is intentionally game-like rather than biologically exact. Each
    tick represents one simulated hour, and all resource pools are normalized
    to the 0..1 range while populations are tracked as abstract biomass units.
    """

    def __init__(
        self,
        state: TerrariumState | None = None,
        config: SimulationConfig | None = None,
        seed: int | None = None,
    ) -> None:
        self.config = config or SimulationConfig()
        self.state = state or TerrariumState(seed=seed)
        if seed is not None:
            self.state.seed = seed
        self._random = random.Random(self.state.seed)
        self.history: list[TerrariumState] = [self.snapshot()]

    @classmethod
    def from_json(cls, payload: str) -> "Terrarium":
        data = json.loads(payload)
        flux_data = data.pop("flux", {})
        data["flux"] = FluxReport(**flux_data)
        state = TerrariumState(**data)
        return cls(state=state, seed=state.seed)

    def snapshot(self) -> TerrariumState:
        state = self.state
        return TerrariumState(
            tick=state.tick,
            hour=state.hour,
            light=state.light,
            temperature=state.temperature,
            water=state.water,
            nutrients=state.nutrients,
            oxygen=state.oxygen,
            carbon_dioxide=state.carbon_dioxide,
            detritus=state.detritus,
            toxicity=state.toxicity,
            plants=state.plants,
            algae=state.algae,
            grazers=state.grazers,
            microbes=state.microbes,
            seed=state.seed,
            events=list(state.events),
            flux=FluxReport(**state.flux.as_dict()),
        )

    def run(self, ticks: int) -> TerrariumState:
        for _ in range(ticks):
            self.step()
        return self.state

    def step(self) -> TerrariumState:
        s = self.state
        c = self.config
        events: list[str] = []

        s.tick += 1
        s.hour = s.tick % c.day_length
        s.light = self._daylight(s.hour)
        target_temperature = c.base_temperature + c.heat_gain * s.light
        s.temperature += (target_temperature - s.temperature) * 0.31
        s.temperature += self._random.uniform(-0.18, 0.18)

        temp_factor = self._temperature_factor(s.temperature)
        resource_factor = max(0.0, min(s.water, s.nutrients, s.carbon_dioxide))
        density = (s.plants + s.algae + s.grazers + s.microbes) / c.carrying_capacity
        crowding = clamp(1.0 - density * 0.45, 0.22, 1.0)

        plant_photo = s.plants * 0.010 * s.light * resource_factor * temp_factor * crowding
        algae_photo = s.algae * 0.016 * s.light * min(s.water, s.carbon_dioxide) * temp_factor
        photosynthesis = plant_photo + algae_photo

        plant_respiration = s.plants * 0.0011 * temp_factor
        algae_respiration = s.algae * 0.0018 * temp_factor
        grazer_respiration = s.grazers * 0.0075 * temp_factor
        microbe_respiration = s.microbes * 0.0042 * temp_factor
        respiration = plant_respiration + algae_respiration + grazer_respiration + microbe_respiration

        plant_food = max(0.0, s.plants - 8.0) * 0.010
        algae_food = max(0.0, s.algae - 4.0) * 0.021
        grazer_appetite = s.grazers * 0.036 * temp_factor
        grazing = min(grazer_appetite, plant_food + algae_food)
        plant_share = plant_food / (plant_food + algae_food) if plant_food + algae_food > 0 else 0.0
        eaten_plants = grazing * plant_share
        eaten_algae = grazing - eaten_plants

        decay_capacity = s.microbes * 0.012 * temp_factor * clamp(s.oxygen * 1.4)
        decay = min(s.detritus, decay_capacity)

        plant_stress = self._plant_stress()
        algae_stress = self._algae_stress()
        grazer_stress = self._grazer_stress(grazing)
        microbe_stress = self._microbe_stress()
        stress_loss = (
            s.plants * plant_stress
            + s.algae * algae_stress
            + s.grazers * grazer_stress
            + s.microbes * microbe_stress
        )

        plant_growth = plant_photo * 8.8
        algae_growth = algae_photo * 7.2
        grazer_growth = grazing * 0.48 * clamp(s.oxygen * 1.2)
        microbe_growth = decay * 1.55

        s.plants += plant_growth - eaten_plants - s.plants * plant_stress
        s.algae += algae_growth - eaten_algae - s.algae * algae_stress
        s.grazers += grazer_growth - s.grazers * grazer_stress
        s.microbes += microbe_growth - s.microbes * microbe_stress

        s.detritus += stress_loss * 0.018 + grazing * 0.20 - decay
        s.nutrients += decay * 0.055 - photosynthesis * 0.060 - algae_photo * 0.015
        s.water += respiration * 0.006 + decay * 0.004 - photosynthesis * 0.018
        s.oxygen += photosynthesis * 0.115 - respiration * 0.034 - decay * 0.012
        s.carbon_dioxide += respiration * 0.031 + decay * 0.014 - photosynthesis * 0.105
        s.toxicity += (s.detritus - 0.55) * 0.002 if s.detritus > 0.55 else -0.002

        self._apply_small_random_drift()
        self._clamp_state()
        self._collect_events(events)

        s.flux = FluxReport(
            photosynthesis=photosynthesis,
            respiration=respiration,
            grazing=grazing,
            decay=decay,
            stress=stress_loss,
        )
        s.events = events
        self.history.append(self.snapshot())
        if len(self.history) > 720:
            self.history.pop(0)
        return s

    def stability_score(self) -> int:
        s = self.state
        score = 100.0
        score -= abs(s.oxygen - 0.62) * 42
        score -= abs(s.carbon_dioxide - 0.38) * 32
        score -= abs(s.water - 0.70) * 28
        score -= abs(s.nutrients - 0.52) * 22
        score -= max(0.0, s.detritus - 0.45) * 34
        score -= s.toxicity * 55
        score -= max(0.0, 12.0 - s.temperature) * 2.8
        score -= max(0.0, s.temperature - 31.0) * 2.8
        score -= 35.0 if s.plants < 8.0 else 0.0
        score -= 25.0 if s.grazers < 1.0 and s.plants > 160.0 else 0.0
        return int(clamp(score / 100.0) * 100)

    def add_population(self, name: str, amount: float) -> None:
        if name not in {"plants", "algae", "grazers", "microbes"}:
            raise ValueError(f"unknown population: {name}")
        setattr(self.state, name, max(0.0, getattr(self.state, name) + amount))

    def set_pool(self, name: str, value: float) -> None:
        if name == "temperature":
            self.state.temperature = value
            return
        if name == "light_intensity":
            self.config.light_intensity = clamp(value)
            return
        if name not in {"water", "nutrients", "oxygen", "carbon_dioxide", "detritus", "toxicity"}:
            raise ValueError(f"unknown pool: {name}")
        setattr(self.state, name, clamp(value))

    def _daylight(self, hour: int) -> float:
        phase = (hour / self.config.day_length) * math.tau
        daylight = max(0.0, math.sin(phase - math.pi / 2))
        return clamp(daylight * self.config.light_intensity)

    def _temperature_factor(self, temperature: float) -> float:
        distance = abs(temperature - 23.0)
        return clamp(1.0 - distance / 18.0, 0.08, 1.0)

    def _plant_stress(self) -> float:
        s = self.state
        stress = 0.0015
        stress += max(0.0, 0.28 - s.water) * 0.030
        stress += max(0.0, 0.20 - s.nutrients) * 0.026
        stress += max(0.0, 0.16 - s.carbon_dioxide) * 0.020
        stress += max(0.0, s.toxicity - 0.22) * 0.040
        stress += max(0.0, s.temperature - 32.0) * 0.004
        stress += max(0.0, 10.0 - s.temperature) * 0.004
        return stress

    def _algae_stress(self) -> float:
        s = self.state
        stress = 0.002
        stress += max(0.0, 0.38 - s.water) * 0.022
        stress += max(0.0, 0.18 - s.carbon_dioxide) * 0.020
        stress += max(0.0, s.toxicity - 0.30) * 0.035
        return stress

    def _grazer_stress(self, grazing: float) -> float:
        s = self.state
        food_need = max(0.05, s.grazers * 0.030)
        food_shortage = max(0.0, 1.0 - grazing / food_need)
        stress = 0.004 + food_shortage * 0.018
        stress += max(0.0, 0.24 - s.oxygen) * 0.060
        stress += max(0.0, s.carbon_dioxide - 0.78) * 0.020
        stress += max(0.0, s.toxicity - 0.18) * 0.050
        stress += max(0.0, s.temperature - 31.0) * 0.004
        stress += max(0.0, 12.0 - s.temperature) * 0.004
        return stress

    def _microbe_stress(self) -> float:
        s = self.state
        stress = 0.003
        stress += max(0.0, 0.18 - s.water) * 0.015
        stress += max(0.0, 0.10 - s.oxygen) * 0.035
        stress += max(0.0, s.toxicity - 0.62) * 0.018
        return stress

    def _apply_small_random_drift(self) -> None:
        s = self.state
        n = self.config.noise
        if n <= 0:
            return
        s.water += self._random.uniform(-n, n) * 0.08
        s.nutrients += self._random.uniform(-n, n) * 0.05
        s.oxygen += self._random.uniform(-n, n) * 0.04
        s.carbon_dioxide += self._random.uniform(-n, n) * 0.04
        s.detritus += self._random.uniform(-n, n) * 0.04

    def _clamp_state(self) -> None:
        s = self.state
        for pool in ("water", "nutrients", "oxygen", "carbon_dioxide", "detritus", "toxicity"):
            setattr(s, pool, clamp(getattr(s, pool)))
        for pop in ("plants", "algae", "grazers", "microbes"):
            setattr(s, pop, max(0.0, getattr(s, pop)))

    def _collect_events(self, events: list[str]) -> None:
        s = self.state
        if s.oxygen < 0.22:
            events.append("O2_CRASH")
        if s.carbon_dioxide > 0.82:
            events.append("CO2_SATURATION")
        if s.water < 0.25:
            events.append("DROUGHT")
        if s.nutrients < 0.16:
            events.append("NUTRIENT_LIMIT")
        if s.detritus > 0.62:
            events.append("ROT_SPIKE")
        if s.toxicity > 0.36:
            events.append("TOXICITY_RISE")
        if s.plants < 6.0:
            events.append("PLANT_COLLAPSE")
        if s.grazers < 0.8:
            events.append("GRAZER_LOSS")
