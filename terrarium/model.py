from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import math
import random
from typing import Any


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


SPRAY_ML_PER_PUMP = 0.8
COMPASS_DIRECTIONS = {
    "north": 0.0,
    "east": 90.0,
    "south": 180.0,
    "west": 270.0,
}
WINDOW_DIRECTION_ALIASES = {
    "n": "north",
    "north": "north",
    "北": "north",
    "e": "east",
    "east": "east",
    "东": "east",
    "s": "south",
    "south": "south",
    "南": "south",
    "w": "west",
    "west": "west",
    "西": "west",
}
WINDOW_LIGHT_PROFILES = {
    "north": {"diffuse": 0.30, "direct": 0.10, "warmth": 0.45},
    "east": {"diffuse": 0.14, "direct": 0.88, "warmth": 0.82},
    "south": {"diffuse": 0.20, "direct": 0.92, "warmth": 1.0},
    "west": {"diffuse": 0.14, "direct": 0.88, "warmth": 0.86},
}
WINDOW_LIGHT_MODE_ALIASES = {
    "mixed": "mixed",
    "normal": "mixed",
    "auto": "mixed",
    "direct": "direct",
    "sun": "direct",
    "sunny": "direct",
    "diffuse": "diffuse",
    "scatter": "diffuse",
    "scattered": "diffuse",
    "indirect": "diffuse",
}
SEASON_PROFILES = {
    "spring": {"daylight": 0.50, "altitude": 1.00, "light": 1.00, "heat": 1.00},
    "summer": {"daylight": 0.58, "altitude": 1.10, "light": 1.08, "heat": 1.18},
    "autumn": {"daylight": 0.48, "altitude": 0.88, "light": 0.88, "heat": 0.82},
    "winter": {"daylight": 0.40, "altitude": 0.62, "light": 0.64, "heat": 0.48},
}
SEASON_ALIASES = {
    "spring": "spring",
    "spr": "spring",
    "春": "spring",
    "summer": "summer",
    "sum": "summer",
    "夏": "summer",
    "autumn": "autumn",
    "fall": "autumn",
    "aut": "autumn",
    "秋": "autumn",
    "winter": "winter",
    "win": "winter",
    "冬": "winter",
}
WEATHER_PROFILES = {
    "clear": {"light": 1.05, "direct": 1.10, "diffuse": 0.90, "heat": 1.05, "label": "clear"},
    "partly_cloudy": {"light": 0.86, "direct": 0.58, "diffuse": 1.18, "heat": 0.82, "label": "partly cloudy"},
    "overcast": {"light": 0.52, "direct": 0.08, "diffuse": 1.36, "heat": 0.58, "label": "overcast"},
    "rainy": {"light": 0.38, "direct": 0.02, "diffuse": 1.20, "heat": 0.45, "label": "rainy"},
}
WEATHER_ALIASES = {
    "clear": "clear",
    "sunny": "clear",
    "晴": "clear",
    "partly": "partly_cloudy",
    "partly_cloudy": "partly_cloudy",
    "cloudy": "partly_cloudy",
    "broken": "partly_cloudy",
    "多云": "partly_cloudy",
    "overcast": "overcast",
    "grey": "overcast",
    "gray": "overcast",
    "阴": "overcast",
    "rain": "rainy",
    "rainy": "rainy",
    "wet": "rainy",
    "雨": "rainy",
    "variable": "variable",
    "random": "variable",
    "auto": "variable",
    "随机": "variable",
}
DEFAULT_MOSS_LAMP_INTENSITY = 0.24
MOSS_LAMP_START_HOUR = 8
MOSS_LAMP_DURATION_HOURS = 12
MOSS_LAMP_ALTITUDE_DEG = 54.0
UMBRELLA_MIN_COVERAGE = 105.0
UMBRELLA_MAX_COVERAGE = 180.0
UMBRELLA_DEFAULT_COVERAGE = 120.0
UMBRELLA_DEFAULT_TILT_DEG = 22.0


def canonical_window_direction(direction: str) -> str:
    key = normalize_key(direction)
    if key not in WINDOW_DIRECTION_ALIASES:
        raise ValueError("window direction must be north, east, south, or west")
    return WINDOW_DIRECTION_ALIASES[key]


def canonical_window_light_mode(mode: str) -> str:
    key = normalize_key(mode)
    if key not in WINDOW_LIGHT_MODE_ALIASES:
        raise ValueError("window exposure must be direct, diffuse, or mixed")
    return WINDOW_LIGHT_MODE_ALIASES[key]


def canonical_season(season: str) -> str:
    key = normalize_key(season)
    if key not in SEASON_ALIASES:
        raise ValueError("season must be spring, summer, autumn, or winter")
    return SEASON_ALIASES[key]


def canonical_weather_mode(weather: str) -> str:
    key = normalize_key(weather)
    if key not in WEATHER_ALIASES:
        raise ValueError("weather must be clear, partly_cloudy, overcast, rainy, or variable")
    return WEATHER_ALIASES[key]


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


SUBSTRATE_LAYER_ORDER = ("drainage", "purification", "soil", "amendment")
SUBSTRATE_LAYER_NAMES = {
    "drainage": "drainage/water barrier",
    "purification": "purification/buffer",
    "soil": "core soil",
    "amendment": "granular amendment",
    "mesh": "mesh screen",
}
SUBSTRATE_LAYER_ALIASES = {
    "drainage": "drainage",
    "drain": "drainage",
    "bottom": "drainage",
    "barrier": "drainage",
    "purification": "purification",
    "buffer": "purification",
    "charcoal": "purification",
    "filter": "purification",
    "soil": "soil",
    "core": "soil",
    "middle": "soil",
    "nutrition": "soil",
    "nutrient": "soil",
    "amendment": "amendment",
    "granular": "amendment",
    "grit": "amendment",
    "modifier": "amendment",
}


def normalize_key(name: str) -> str:
    return name.strip().lower().replace("-", "_").replace(" ", "_")


@dataclass(slots=True, frozen=True)
class ContainerSpec:
    """Container geometry used by the crafting and survival simulation."""

    key: str = "standard_1l"
    display_name: str = "Standard 1L upright jar"
    capacity_ml: float = 1000.0
    height_cm: float = 16.7
    diameter_cm: float = 9.3
    length_cm: float = 9.3
    width_cm: float = 9.3
    footprint_shape: str = "round"
    external_base_area_cm2: float = math.pi * (9.3 / 2) ** 2
    base_area_cm2: float = 1000.0 / 16.7


@dataclass(slots=True, frozen=True)
class ContainerDefinition:
    key: str
    display_name: str
    capacity_ml: float
    height_cm: float
    footprint_shape: str = "round"
    diameter_cm: float | None = None
    length_cm: float | None = None
    width_cm: float | None = None
    aliases: tuple[str, ...] = ()

    def spec(self) -> ContainerSpec:
        base_area = self.capacity_ml / self.height_cm
        if self.footprint_shape == "round":
            diameter = self.diameter_cm if self.diameter_cm is not None else (base_area / math.pi) ** 0.5 * 2.0
            length = width = diameter
            external_area = math.pi * (diameter / 2.0) ** 2
        else:
            length = self.length_cm if self.length_cm is not None else (base_area ** 0.5)
            width = self.width_cm if self.width_cm is not None else base_area / max(length, 1e-9)
            diameter = self.diameter_cm if self.diameter_cm is not None else min(length, width)
            external_area = length * width
            base_area = external_area
        return ContainerSpec(
            key=self.key,
            display_name=self.display_name,
            capacity_ml=self.capacity_ml,
            height_cm=self.height_cm,
            diameter_cm=diameter,
            length_cm=length,
            width_cm=width,
            footprint_shape=self.footprint_shape,
            external_base_area_cm2=external_area,
            base_area_cm2=base_area,
        )


def _container(
    key: str,
    display_name: str,
    capacity_ml: float,
    height_cm: float,
    footprint_shape: str = "round",
    diameter_cm: float | None = None,
    length_cm: float | None = None,
    width_cm: float | None = None,
    aliases: tuple[str, ...] = (),
) -> ContainerDefinition:
    return ContainerDefinition(
        key=key,
        display_name=display_name,
        capacity_ml=capacity_ml,
        height_cm=height_cm,
        footprint_shape=footprint_shape,
        diameter_cm=diameter_cm,
        length_cm=length_cm,
        width_cm=width_cm,
        aliases=aliases,
    )


CONTAINERS = {
    item.key: item
    for item in (
        _container("tiny_vial", "Tiny 150ml vial", 150.0, 9.0, diameter_cm=4.6, aliases=("vial", "tiny")),
        _container("nano_jar", "Nano 300ml jar", 300.0, 8.0, diameter_cm=6.9, aliases=("nano", "small")),
        _container("standard_1l", "Standard 1L upright jar", 1000.0, 16.7, diameter_cm=9.3, aliases=("standard", "one_liter", "1l")),
        _container("wide_jar", "Wide 1.5L jar", 1500.0, 14.0, diameter_cm=11.7, aliases=("wide", "wide_1_5l")),
        _container("tall_2l", "Tall 2L display jar", 2000.0, 24.0, diameter_cm=10.3, aliases=("tall", "large")),
        _container(
            "horizontal_jar",
            "Horizontal 1.2L long jar",
            1200.0,
            8.0,
            footprint_shape="rect",
            length_cm=22.0,
            width_cm=1200.0 / 8.0 / 22.0,
            aliases=("horizontal", "long", "sideways"),
        ),
        _container(
            "long_low_tank",
            "Long low 800ml tank",
            800.0,
            6.0,
            footprint_shape="rect",
            length_cm=24.0,
            width_cm=800.0 / 6.0 / 24.0,
            aliases=("long_low", "low_tank", "tray"),
        ),
    )
}

CONTAINER_ALIASES: dict[str, str] = {}
for container_key, definition in CONTAINERS.items():
    CONTAINER_ALIASES[normalize_key(container_key)] = container_key
    CONTAINER_ALIASES[normalize_key(definition.display_name)] = container_key
    for alias in definition.aliases:
        CONTAINER_ALIASES[normalize_key(alias)] = container_key


def canonical_container_key(name: str) -> str:
    key = normalize_key(name)
    try:
        return CONTAINER_ALIASES[key]
    except KeyError as exc:
        allowed = ", ".join(sorted(CONTAINERS))
        raise ValueError(f"unknown container '{name}', expected one of: {allowed}") from exc


def container_spec(name: str) -> ContainerSpec:
    return CONTAINERS[canonical_container_key(name)].spec()


@dataclass(slots=True, frozen=True)
class SubstrateDefinition:
    key: str
    layer_kind: str
    display_name: str
    water_retention: float
    aeration: float
    solid_fraction: float
    pore_fraction: float
    aliases: tuple[str, ...] = ()
    can_mix_in: tuple[str, ...] = ()
    soil_ph: float | None = None
    soil_nutrients: float | None = None

    @property
    def allowed_layer_kinds(self) -> tuple[str, ...]:
        return (self.layer_kind, *self.can_mix_in)


def _substrate(
    key: str,
    layer_kind: str,
    display_name: str,
    water_retention: float,
    aeration: float,
    solid_fraction: float,
    pore_fraction: float,
    aliases: tuple[str, ...] = (),
    can_mix_in: tuple[str, ...] = (),
    soil_ph: float | None = None,
    soil_nutrients: float | None = None,
) -> SubstrateDefinition:
    return SubstrateDefinition(
        key=key,
        layer_kind=layer_kind,
        display_name=display_name,
        water_retention=water_retention,
        aeration=aeration,
        solid_fraction=solid_fraction,
        pore_fraction=pore_fraction,
        aliases=aliases,
        can_mix_in=can_mix_in,
        soil_ph=soil_ph,
        soil_nutrients=soil_nutrients,
    )


SUBSTRATES = {
    item.key: item
    for item in (
        _substrate("leca", "drainage", "LECA", 2, 10, 0.42, 0.58, aliases=("clay_pebbles", "expanded_clay")),
        _substrate("pumice", "drainage", "Pumice", 4, 8, 0.48, 0.52),
        _substrate("volcanic_rock", "drainage", "Volcanic rock", 2, 8, 0.58, 0.42, aliases=("lava_rock",)),
        _substrate("activated_charcoal", "purification", "Activated charcoal", 3, 7, 0.45, 0.55, aliases=("charcoal",)),
        _substrate("peat_moss", "soil", "Peat moss", 9, 3, 0.28, 0.72, aliases=("peat",), soil_ph=4.2, soil_nutrients=6),
        _substrate(
            "sphagnum_moss",
            "soil",
            "Sphagnum moss",
            10,
            6,
            0.18,
            0.82,
            aliases=("sphagnum", "moss"),
            soil_ph=4.8,
            soil_nutrients=1,
        ),
        _substrate("compost", "soil", "Compost", 7, 4, 0.38, 0.62, aliases=("humus", "leaf_mold"), soil_ph=6.5, soil_nutrients=10),
        _substrate("akadama", "amendment", "Akadama soil", 6, 7, 0.55, 0.45, aliases=("akadama_soil",), can_mix_in=("soil",)),
        _substrate("kanuma", "amendment", "Kanuma soil", 5, 8, 0.50, 0.50, aliases=("kanuma_soil",), can_mix_in=("soil",)),
        _substrate("perlite", "amendment", "Perlite", 1, 9, 0.18, 0.82, can_mix_in=("soil",)),
        _substrate("vermiculite", "amendment", "Vermiculite", 8, 5, 0.30, 0.70, can_mix_in=("soil",)),
    )
}

SUBSTRATE_ALIASES: dict[str, str] = {}
for substrate_key, definition in SUBSTRATES.items():
    SUBSTRATE_ALIASES[normalize_key(substrate_key)] = substrate_key
    SUBSTRATE_ALIASES[normalize_key(definition.display_name)] = substrate_key
    for alias in definition.aliases:
        SUBSTRATE_ALIASES[normalize_key(alias)] = substrate_key


@dataclass(slots=True)
class SubstratePortion:
    substrate: str
    percent: float


@dataclass(slots=True)
class SubstrateLayer:
    layer_kind: str
    height_cm: float
    portions: list[SubstratePortion] = field(default_factory=list)
    slope_x_cm: float = 0.0
    slope_y_cm: float = 0.0


def canonical_substrate_layer(name: str) -> str:
    key = normalize_key(name)
    try:
        return SUBSTRATE_LAYER_ALIASES[key]
    except KeyError as exc:
        allowed = ", ".join(SUBSTRATE_LAYER_ORDER)
        raise ValueError(f"unknown substrate layer '{name}', expected one of: {allowed}") from exc


def canonical_substrate_key(name: str) -> str:
    key = normalize_key(name)
    try:
        return SUBSTRATE_ALIASES[key]
    except KeyError as exc:
        allowed = ", ".join(sorted(SUBSTRATES))
        raise ValueError(f"unknown substrate '{name}', expected one of: {allowed}") from exc


def substrate_layer_index(layer_kind: str) -> int:
    return SUBSTRATE_LAYER_ORDER.index(canonical_substrate_layer(layer_kind))


def normalize_substrate_mixture(layer_kind: str, mixture: dict[str, float]) -> list[SubstratePortion]:
    canonical_layer = canonical_substrate_layer(layer_kind)
    if not mixture:
        raise ValueError("substrate mixture cannot be empty")

    portions_by_key: dict[str, float] = {}
    for raw_name, raw_percent in mixture.items():
        substrate_key = canonical_substrate_key(raw_name)
        definition = SUBSTRATES[substrate_key]
        if canonical_layer not in definition.allowed_layer_kinds:
            allowed = ", ".join(definition.allowed_layer_kinds)
            raise ValueError(f"{substrate_key} can be used in layer(s): {allowed}")
        percent = float(raw_percent)
        if percent <= 0:
            raise ValueError("substrate percentages must be positive")
        portions_by_key[substrate_key] = portions_by_key.get(substrate_key, 0.0) + percent

    total = sum(portions_by_key.values())
    if abs(total - 100.0) > 0.01:
        raise ValueError(f"substrate mixture must total 100 percent, got {total:g}")

    return [SubstratePortion(substrate=key, percent=percent) for key, percent in portions_by_key.items()]


def substrate_layer_stats(layer: SubstrateLayer) -> dict[str, float]:
    stats = {"water_retention": 0.0, "aeration": 0.0}
    for portion in layer.portions:
        definition = SUBSTRATES[portion.substrate]
        weight = portion.percent / 100.0
        stats["water_retention"] += definition.water_retention * weight
        stats["aeration"] += definition.aeration * weight
    return stats


def soil_layer_stats(layer: SubstrateLayer) -> dict[str, float | None]:
    if layer.layer_kind != "soil":
        return {"ph": None, "nutrients": None}

    ph_total = 0.0
    ph_weight = 0.0
    nutrients = 0.0
    for portion in layer.portions:
        definition = SUBSTRATES[portion.substrate]
        weight = portion.percent / 100.0
        if definition.soil_ph is not None:
            ph_total += definition.soil_ph * weight
            ph_weight += weight
        if definition.soil_nutrients is not None:
            nutrients += definition.soil_nutrients * weight

    ph = ph_total / ph_weight if ph_weight > 0 else None
    return {"ph": ph, "nutrients": nutrients}


def copy_substrate_layers(layers: list[SubstrateLayer]) -> list[SubstrateLayer]:
    return [
        SubstrateLayer(
            layer_kind=layer.layer_kind,
            height_cm=layer.height_cm,
            portions=[SubstratePortion(substrate=portion.substrate, percent=portion.percent) for portion in layer.portions],
            slope_x_cm=layer.slope_x_cm,
            slope_y_cm=layer.slope_y_cm,
        )
        for layer in layers
    ]


HARDSCAPE_POSITIONS = (
    "center",
    "edge",
    "north",
    "south",
    "east",
    "west",
    "northeast",
    "northwest",
    "southeast",
    "southwest",
)
HARDSCAPE_ORIENTATIONS = (
    "flat",
    "upright",
    "scattered",
    "arch",
    "leaning_north",
    "leaning_south",
    "leaning_east",
    "leaning_west",
)
HARDSCAPE_SURFACES = ("top", "side", "crack", "groove", "underside")
HARDSCAPE_POSITION_ANGLES = {
    "center": 0.0,
    "edge": 0.0,
    "north": 0.0,
    "south": 0.0,
    "east": 90.0,
    "west": 90.0,
    "northeast": 45.0,
    "northwest": 135.0,
    "southeast": 135.0,
    "southwest": 45.0,
}
HARDSCAPE_ORIENTATION_ANGLES = {
    "flat": None,
    "upright": None,
    "scattered": None,
    "arch": None,
    "leaning_east": 0.0,
    "leaning_north": 90.0,
    "leaning_west": 180.0,
    "leaning_south": 270.0,
}
MAX_HARDSCAPE_COVERAGE = 85.0
MAX_LAYER_SLOPE_CM = 3.0
HARDSCAPE_CORE_FACTORS = {"stone": 0.68, "wood": 0.58, "decor": 0.74, "surface": 0.38}
SURFACE_CAPACITY_FACTORS = {"top": 1.25, "side": 0.70, "crack": 0.45, "groove": 0.55, "underside": 0.25}
SURFACE_MICROCLIMATE_TRAITS = {
    "top": {
        "moisture": -0.03,
        "shade": 0.00,
        "shelter": 0.02,
        "aeration": 0.05,
        "biofilm": 0.02,
        "mold": -0.01,
        "attachment": 0.64,
    },
    "side": {
        "moisture": 0.02,
        "shade": 0.04,
        "shelter": 0.10,
        "aeration": 0.08,
        "biofilm": 0.04,
        "mold": 0.02,
        "attachment": 0.74,
    },
    "crack": {
        "moisture": 0.15,
        "shade": 0.12,
        "shelter": 0.28,
        "aeration": -0.03,
        "biofilm": 0.10,
        "mold": 0.13,
        "attachment": 0.96,
    },
    "groove": {
        "moisture": 0.12,
        "shade": 0.08,
        "shelter": 0.22,
        "aeration": 0.00,
        "biofilm": 0.12,
        "mold": 0.10,
        "attachment": 0.90,
    },
    "underside": {
        "moisture": 0.10,
        "shade": 0.22,
        "shelter": 0.35,
        "aeration": -0.06,
        "biofilm": 0.09,
        "mold": 0.16,
        "attachment": 0.70,
    },
}
POSITION_COORDINATES = {
    "center": (50.0, 50.0),
    "edge": (50.0, 88.0),
    "north": (50.0, 82.0),
    "south": (50.0, 18.0),
    "east": (82.0, 50.0),
    "west": (18.0, 50.0),
    "northeast": (76.0, 76.0),
    "northwest": (24.0, 76.0),
    "southeast": (76.0, 24.0),
    "southwest": (24.0, 24.0),
}


@dataclass(slots=True, frozen=True)
class HardscapeDefinition:
    key: str
    display_name: str
    category: str
    shape: str
    min_coverage: float
    max_coverage: float
    default_coverage: float
    height_cm: float
    block_factor: float
    shade_factor: float
    evaporation_shield: float
    edge_moisture: float
    volume_factor: float
    aliases: tuple[str, ...] = ()
    footprint_aspect_ratio: float = 1.0
    default_tilt_deg: float = 0.0
    attach_surfaces: tuple[str, ...] = ("top",)
    geometry_profile: str = "oval"
    surface_complexity: float = 0.0
    surface_features: tuple[str, ...] = ()


def _hardscape(
    key: str,
    display_name: str,
    category: str,
    shape: str,
    min_coverage: float,
    max_coverage: float,
    default_coverage: float,
    height_cm: float,
    block_factor: float,
    shade_factor: float,
    evaporation_shield: float,
    edge_moisture: float,
    volume_factor: float,
    aliases: tuple[str, ...] = (),
    footprint_aspect_ratio: float = 1.0,
    default_tilt_deg: float = 0.0,
    attach_surfaces: tuple[str, ...] = ("top",),
    geometry_profile: str = "oval",
    surface_complexity: float = 0.0,
    surface_features: tuple[str, ...] = (),
) -> HardscapeDefinition:
    return HardscapeDefinition(
        key=key,
        display_name=display_name,
        category=category,
        shape=shape,
        min_coverage=min_coverage,
        max_coverage=max_coverage,
        default_coverage=default_coverage,
        height_cm=height_cm,
        block_factor=block_factor,
        shade_factor=shade_factor,
        evaporation_shield=evaporation_shield,
        edge_moisture=edge_moisture,
        volume_factor=volume_factor,
        aliases=aliases,
        footprint_aspect_ratio=max(1.0, footprint_aspect_ratio),
        default_tilt_deg=default_tilt_deg,
        attach_surfaces=attach_surfaces,
        geometry_profile=geometry_profile,
        surface_complexity=clamp(surface_complexity, 0.0, 0.35),
        surface_features=surface_features,
    )


HARDSCAPES = {
    item.key: item
    for item in (
        _hardscape("pebble", "Pebble cluster", "stone", "small rounded cluster", 1, 8, 4, 1.0, 0.75, 0.03, 0.35, 0.05, 0.55, footprint_aspect_ratio=1.2, geometry_profile="cluster", surface_complexity=0.09, surface_features=("rounded lobe", "shallow seam")),
        _hardscape("river_stone", "River stone", "stone", "smooth oval", 4, 16, 9, 2.0, 0.95, 0.08, 0.45, 0.06, 0.70, aliases=("round_stone",), footprint_aspect_ratio=1.7, attach_surfaces=("top", "side", "crack"), geometry_profile="smooth_oval", surface_complexity=0.04, surface_features=("polished top", "hairline crack", "wet side")),
        _hardscape("slate", "Slate shard", "stone", "flat slab", 5, 22, 12, 1.2, 1.00, 0.12, 0.60, 0.03, 0.55, aliases=("flat_stone",), footprint_aspect_ratio=2.8, default_tilt_deg=18.0, attach_surfaces=("top", "side", "crack", "underside"), geometry_profile="shard", surface_complexity=0.13, surface_features=("sharp ledge", "thin crack", "under shelf")),
        _hardscape("lava_rock", "Lava rock", "stone", "porous mound", 4, 18, 10, 2.4, 0.85, 0.10, 0.45, 0.18, 0.58, footprint_aspect_ratio=1.35, attach_surfaces=("top", "side", "crack"), geometry_profile="porous_lobed", surface_complexity=0.19, surface_features=("pore pocket", "rough ridge", "dark crevice")),
        _hardscape("pumice_stone", "Pumice stone", "stone", "light porous mound", 3, 14, 7, 1.8, 0.80, 0.07, 0.40, 0.14, 0.45, footprint_aspect_ratio=1.35, attach_surfaces=("top", "side", "crack"), geometry_profile="porous_lobed", surface_complexity=0.16, surface_features=("pale pore", "soft ridge", "small crevice")),
        _hardscape("gravel_patch", "Gravel patch", "surface", "scattered small grains", 4, 30, 12, 0.3, 0.45, 0.01, 0.55, 0.04, 0.65, footprint_aspect_ratio=1.4, geometry_profile="scattered_patch", surface_complexity=0.12, surface_features=("grain pocket", "open grit")),
        _hardscape("bark_chip", "Bark chips", "wood", "loose flakes", 3, 18, 8, 0.7, 0.45, 0.04, 0.35, 0.10, 0.38, aliases=("bark",), footprint_aspect_ratio=2.2, attach_surfaces=("top", "side", "groove"), geometry_profile="bark_ridge", surface_complexity=0.17, surface_features=("bark groove", "flake edge", "fibrous ridge")),
        _hardscape("driftwood", "Driftwood", "wood", "branch or arch", 4, 24, 11, 3.0, 0.55, 0.20, 0.25, 0.16, 0.35, aliases=("wood", "branch"), footprint_aspect_ratio=4.3, default_tilt_deg=10.0, attach_surfaces=("top", "side", "groove", "underside"), geometry_profile="segmented_wood", surface_complexity=0.18, surface_features=("branch node", "long groove", "side ridge", "under overhang")),
        _hardscape("cork_bark", "Cork bark", "wood", "curved ridge", 5, 22, 10, 2.6, 0.60, 0.18, 0.28, 0.15, 0.32, aliases=("cork",), footprint_aspect_ratio=3.2, default_tilt_deg=14.0, attach_surfaces=("top", "side", "groove", "underside"), geometry_profile="bark_ridge", surface_complexity=0.20, surface_features=("cork groove", "raised ridge", "shadowed underside")),
        _hardscape("ceramic_figure", "Ceramic figure", "decor", "solid ornament", 2, 12, 5, 2.2, 1.00, 0.12, 0.30, 0.00, 0.80, aliases=("figurine",), geometry_profile="solid_ornament", surface_complexity=0.02, surface_features=("smooth glaze",)),
    )
}

HARDSCAPE_ALIASES: dict[str, str] = {}
for hardscape_key, definition in HARDSCAPES.items():
    HARDSCAPE_ALIASES[normalize_key(hardscape_key)] = hardscape_key
    HARDSCAPE_ALIASES[normalize_key(definition.display_name)] = hardscape_key
    for alias in definition.aliases:
        HARDSCAPE_ALIASES[normalize_key(alias)] = hardscape_key


@dataclass(slots=True)
class HardscapeItem:
    item_id: str
    kind: str
    coverage_percent: float
    position: str = "center"
    orientation: str = "flat"
    rotation_deg: float = 0.0
    tilt_deg: float = 0.0
    x_percent: float = 50.0
    y_percent: float = 50.0
    z_base_cm: float = 0.0
    z_top_cm: float = 0.0
    geometry_seed: int = 0


def canonical_hardscape_key(name: str) -> str:
    key = normalize_key(name)
    try:
        return HARDSCAPE_ALIASES[key]
    except KeyError as exc:
        allowed = ", ".join(sorted(HARDSCAPES))
        raise ValueError(f"unknown hardscape '{name}', expected one of: {allowed}") from exc


def copy_hardscape_items(items: list[HardscapeItem]) -> list[HardscapeItem]:
    return [
        HardscapeItem(
            item_id=item.item_id,
            kind=item.kind,
            coverage_percent=item.coverage_percent,
            position=item.position,
            orientation=item.orientation,
            rotation_deg=item.rotation_deg,
            tilt_deg=item.tilt_deg,
            x_percent=item.x_percent,
            y_percent=item.y_percent,
            z_base_cm=item.z_base_cm,
            z_top_cm=item.z_top_cm,
            geometry_seed=item.geometry_seed,
        )
        for item in items
    ]


PLANTING_SITES = ("surface", "soil", "substrate", "air", "water")


@dataclass(slots=True, frozen=True)
class PlantDefinition:
    key: str
    display_name: str
    category: str
    growth_form: str
    min_area_percent: float
    default_area_percent: float
    mature_area_percent: float
    height_cm: float
    root_depth_cm: float
    humidity_range: tuple[float, float]
    temperature_range: tuple[float, float]
    light_range: tuple[float, float]
    water_range: tuple[float, float]
    nutrition_range: tuple[float, float]
    aeration_range: tuple[float, float]
    aliases: tuple[str, ...] = ()
    notes: str = ""
    root_volume_factor: float = 0.35
    canopy_volume_factor: float = 0.22
    base_growth_rate: float = 0.012
    reproduction_rate: float = 0.0
    reproduction_mode: str = "none"
    min_reproductive_age_ticks: int = 720
    life_strategy: str = "steady"
    photosynthesis_efficiency: float = 1.0
    nutrient_demand: float = 1.0
    water_use_rate: float = 1.0
    respiration_rate: float = 1.0


def _plant(
    key: str,
    display_name: str,
    category: str,
    growth_form: str,
    min_area_percent: float,
    default_area_percent: float,
    mature_area_percent: float,
    height_cm: float,
    root_depth_cm: float,
    humidity_range: tuple[float, float],
    temperature_range: tuple[float, float],
    light_range: tuple[float, float],
    water_range: tuple[float, float],
    nutrition_range: tuple[float, float],
    aeration_range: tuple[float, float],
    aliases: tuple[str, ...] = (),
    notes: str = "",
    root_volume_factor: float | None = None,
    canopy_volume_factor: float | None = None,
    base_growth_rate: float | None = None,
    reproduction_rate: float | None = None,
    reproduction_mode: str | None = None,
    min_reproductive_age_ticks: int | None = None,
    life_strategy: str | None = None,
    photosynthesis_efficiency: float | None = None,
    nutrient_demand: float | None = None,
    water_use_rate: float | None = None,
    respiration_rate: float | None = None,
) -> PlantDefinition:
    if root_volume_factor is None:
        root_volume_factor = 0.12 if root_depth_cm <= 0 else 0.35
    if canopy_volume_factor is None:
        canopy_volume_factor = 0.12 if category in {"moss", "lichen"} else 0.22
    default_growth, default_reproduction, default_mode, default_age, default_strategy = _plant_life_defaults(
        category,
        growth_form,
    )
    default_photo, default_nutrient, default_water, default_respiration = _plant_resource_defaults(
        category,
        growth_form,
    )
    return PlantDefinition(
        key=key,
        display_name=display_name,
        category=category,
        growth_form=growth_form,
        min_area_percent=min_area_percent,
        default_area_percent=default_area_percent,
        mature_area_percent=mature_area_percent,
        height_cm=height_cm,
        root_depth_cm=root_depth_cm,
        humidity_range=humidity_range,
        temperature_range=temperature_range,
        light_range=light_range,
        water_range=water_range,
        nutrition_range=nutrition_range,
        aeration_range=aeration_range,
        aliases=aliases,
        notes=notes,
        root_volume_factor=root_volume_factor,
        canopy_volume_factor=canopy_volume_factor,
        base_growth_rate=default_growth if base_growth_rate is None else base_growth_rate,
        reproduction_rate=default_reproduction if reproduction_rate is None else reproduction_rate,
        reproduction_mode=default_mode if reproduction_mode is None else reproduction_mode,
        min_reproductive_age_ticks=default_age if min_reproductive_age_ticks is None else min_reproductive_age_ticks,
        life_strategy=default_strategy if life_strategy is None else life_strategy,
        photosynthesis_efficiency=default_photo if photosynthesis_efficiency is None else photosynthesis_efficiency,
        nutrient_demand=default_nutrient if nutrient_demand is None else nutrient_demand,
        water_use_rate=default_water if water_use_rate is None else water_use_rate,
        respiration_rate=default_respiration if respiration_rate is None else respiration_rate,
    )


def _plant_life_defaults(category: str, growth_form: str) -> tuple[float, float, str, int, str]:
    if category == "moss":
        return (0.018, 0.030, "mat_spread", 336, "surface_colonizer")
    if category == "lichen":
        return (0.006, 0.006, "fragment_spread", 1440, "slow_colonizer")
    if category == "fittonia":
        return (0.017, 0.016, "cutting_or_node", 720, "creeping_foliage")
    if category == "creeper":
        return (0.020, 0.020, "runner_spread", 504, "spreader")
    if category in {"terrestrial_fern", "epiphytic_fern"}:
        mode = "rhizome_division" if "rhizome" in growth_form or "creeping" in growth_form else "spores"
        return (0.012, 0.010, mode, 1008, "slow_fern")
    if category == "carnivorous":
        return (0.010, 0.006, "offset_or_seed", 1440, "specialist")
    if category == "bromeliad_tank":
        return (0.010, 0.007, "pups", 1800, "rosette")
    if category == "bromeliad_air":
        return (0.008, 0.005, "pups", 2160, "air_rosette")
    if category == "orchid_mini":
        return (0.007, 0.004, "division", 2160, "slow_epiphyte")
    return (0.010, 0.004, "none", 1440, "steady")


def _plant_resource_defaults(category: str, growth_form: str) -> tuple[float, float, float, float]:
    if category == "moss":
        water = 0.90 if "wet" in growth_form else 0.58
        return (0.76, 0.34, water, 0.62)
    if category == "lichen":
        return (0.46, 0.16, 0.28, 0.42)
    if category == "fittonia":
        return (1.12, 1.24, 1.05, 1.04)
    if category == "creeper":
        return (1.06, 1.12, 0.92, 0.98)
    if category == "terrestrial_fern":
        return (0.98, 0.92, 1.00, 0.98)
    if category == "epiphytic_fern":
        return (0.86, 0.58, 0.74, 0.82)
    if category == "carnivorous":
        return (0.96, 0.20, 1.02, 0.90)
    if category == "bromeliad_tank":
        return (0.92, 0.55, 0.76, 0.88)
    if category == "bromeliad_air":
        return (0.78, 0.24, 0.40, 0.72)
    if category == "orchid_mini":
        return (0.72, 0.46, 0.62, 0.76)
    return (1.0, 1.0, 1.0, 1.0)


PLANTS = {
    item.key: item
    for item in (
        _plant("lemon_button_fern", "Lemon button fern", "terrestrial_fern", "clumping fern", 4, 6, 14, 18, 4, (70, 95), (18, 27), (0.20, 0.55), (0.45, 0.85), (3, 6), (4, 8), aliases=("button_fern",)),
        _plant("maidenhair_fern", "Maidenhair fern", "terrestrial_fern", "delicate clump", 5, 7, 16, 22, 5, (78, 98), (18, 26), (0.18, 0.45), (0.55, 0.90), (3, 6), (5, 9)),
        _plant("heart_fern", "Heart fern", "terrestrial_fern", "compact rosette", 3, 5, 10, 14, 3, (75, 96), (19, 28), (0.18, 0.50), (0.45, 0.85), (2, 5), (5, 8)),
        _plant("silver_pteris", "Silver pteris", "terrestrial_fern", "upright fern", 5, 7, 17, 24, 5, (65, 92), (18, 28), (0.25, 0.60), (0.40, 0.80), (3, 7), (5, 9)),
        _plant("dwarf_boston_fern", "Dwarf Boston fern", "terrestrial_fern", "arching clump", 6, 8, 20, 24, 6, (70, 95), (18, 27), (0.18, 0.55), (0.45, 0.85), (3, 7), (5, 8)),
        _plant("rabbit_foot_fern", "Rabbit foot fern", "epiphytic_fern", "rhizome creeper", 4, 6, 16, 16, 2, (65, 92), (18, 28), (0.25, 0.65), (0.35, 0.75), (2, 5), (6, 10)),
        _plant("mini_bird_nest_fern", "Mini bird nest fern", "epiphytic_fern", "rosette epiphyte", 5, 7, 18, 20, 2, (70, 96), (19, 29), (0.20, 0.55), (0.40, 0.80), (2, 5), (6, 10)),
        _plant("creeping_microsorum", "Creeping microsorum", "epiphytic_fern", "creeping rhizome", 3, 5, 14, 12, 2, (68, 94), (18, 28), (0.20, 0.60), (0.35, 0.75), (1, 4), (6, 10)),
        _plant("pyrrosia", "Pyrrosia fern", "epiphytic_fern", "small shingle fern", 3, 5, 12, 10, 1, (55, 88), (17, 30), (0.25, 0.70), (0.25, 0.65), (1, 4), (7, 10)),
        _plant("button_epiphyte_fern", "Button epiphyte fern", "epiphytic_fern", "small rhizome fern", 3, 4, 11, 10, 1, (65, 92), (18, 28), (0.25, 0.65), (0.30, 0.70), (1, 4), (7, 10)),
        _plant("cushion_moss", "Cushion moss", "moss", "cushion mat", 4, 8, 24, 3, 0, (80, 100), (12, 25), (0.10, 0.45), (0.55, 0.95), (0, 3), (3, 8)),
        _plant("sheet_moss", "Sheet moss", "moss", "sheet mat", 5, 10, 35, 2, 0, (78, 100), (12, 26), (0.08, 0.45), (0.55, 0.95), (0, 3), (3, 8)),
        _plant("mood_moss", "Mood moss", "moss", "tufted mat", 5, 9, 28, 5, 0, (75, 98), (10, 24), (0.10, 0.42), (0.50, 0.90), (0, 3), (4, 8)),
        _plant("fern_moss", "Fern moss", "moss", "feathery mat", 4, 8, 26, 4, 0, (78, 100), (12, 25), (0.10, 0.45), (0.50, 0.92), (0, 3), (4, 8)),
        _plant("sphagnum_live", "Live sphagnum", "moss", "wet moss strand", 5, 10, 30, 6, 0, (85, 100), (12, 25), (0.15, 0.55), (0.70, 1.00), (0, 2), (4, 8), aliases=("live_sphagnum",)),
        _plant("reindeer_lichen", "Reindeer lichen", "lichen", "branching cushion", 3, 5, 14, 5, 0, (45, 80), (8, 24), (0.35, 0.80), (0.15, 0.55), (0, 2), (7, 10)),
        _plant("cup_lichen", "Cup lichen", "lichen", "tiny cups", 2, 4, 10, 3, 0, (45, 82), (8, 24), (0.35, 0.80), (0.15, 0.55), (0, 2), (7, 10)),
        _plant("crust_lichen", "Crust lichen", "lichen", "thin crust", 2, 3, 8, 1, 0, (40, 78), (8, 26), (0.35, 0.85), (0.10, 0.50), (0, 1), (8, 10)),
        _plant("foliose_lichen", "Foliose lichen", "lichen", "leafy patches", 3, 5, 12, 2, 0, (45, 82), (8, 24), (0.30, 0.75), (0.15, 0.55), (0, 2), (7, 10)),
        _plant("fittonia_white", "White nerve plant", "fittonia", "creeping foliage", 4, 6, 18, 10, 3, (75, 98), (18, 29), (0.15, 0.50), (0.45, 0.85), (3, 7), (4, 8), aliases=("white_fittonia",)),
        _plant("fittonia_pink", "Pink nerve plant", "fittonia", "creeping foliage", 4, 6, 18, 10, 3, (75, 98), (18, 29), (0.15, 0.50), (0.45, 0.85), (3, 7), (4, 8), aliases=("pink_fittonia",)),
        _plant("fittonia_red", "Red nerve plant", "fittonia", "creeping foliage", 4, 6, 18, 10, 3, (75, 98), (18, 29), (0.15, 0.50), (0.45, 0.85), (3, 7), (4, 8), aliases=("red_fittonia",)),
        _plant("fittonia_mini", "Mini fittonia", "fittonia", "mini creeping foliage", 3, 5, 14, 8, 2, (75, 98), (18, 29), (0.15, 0.50), (0.45, 0.85), (3, 7), (4, 8)),
        _plant("fittonia_josanii", "Fittonia Josan", "fittonia", "compact foliage", 4, 6, 16, 9, 3, (75, 98), (18, 29), (0.15, 0.50), (0.45, 0.85), (3, 7), (4, 8)),
        _plant("drosera_spatulata", "Spoonleaf sundew", "carnivorous", "sticky rosette", 3, 5, 12, 5, 2, (65, 95), (18, 30), (0.35, 0.85), (0.60, 1.00), (0, 2), (4, 8)),
        _plant("drosera_capensis", "Cape sundew", "carnivorous", "strap-leaf rosette", 5, 7, 18, 18, 4, (60, 92), (16, 30), (0.40, 0.90), (0.55, 1.00), (0, 2), (4, 8)),
        _plant("pinguicula_esseriana", "Pinguicula esseriana", "carnivorous", "butterwort rosette", 3, 5, 10, 4, 1, (55, 90), (16, 28), (0.30, 0.75), (0.35, 0.80), (0, 2), (5, 9)),
        _plant("pinguicula_moranensis", "Pinguicula moranensis", "carnivorous", "butterwort rosette", 4, 6, 14, 8, 2, (55, 90), (16, 29), (0.30, 0.80), (0.35, 0.80), (0, 2), (5, 9)),
        _plant("utricularia_sandersonii", "Sanderson bladderwort", "carnivorous", "tiny flowering mat", 4, 7, 22, 4, 1, (75, 100), (16, 28), (0.25, 0.70), (0.65, 1.00), (0, 2), (4, 8)),
        _plant("neoregelia_fireball", "Neoregelia Fireball", "bromeliad_tank", "tank rosette", 5, 8, 18, 12, 2, (60, 92), (18, 30), (0.35, 0.85), (0.30, 0.75), (1, 4), (6, 10)),
        _plant("neoregelia_liliputiana", "Neoregelia liliputiana", "bromeliad_tank", "mini tank rosette", 4, 6, 14, 8, 2, (60, 92), (18, 30), (0.35, 0.85), (0.30, 0.75), (1, 4), (6, 10)),
        _plant("cryptanthus_dwarf", "Dwarf earth star", "bromeliad_tank", "flat rosette", 5, 8, 18, 8, 3, (60, 90), (18, 30), (0.30, 0.75), (0.35, 0.75), (2, 5), (5, 9)),
        _plant("tillandsia_ionantha", "Tillandsia ionantha", "bromeliad_air", "air rosette", 3, 5, 10, 6, 0, (45, 80), (16, 32), (0.40, 0.90), (0.15, 0.55), (0, 2), (8, 10)),
        _plant("tillandsia_bulbosa", "Tillandsia bulbosa", "bromeliad_air", "air rosette", 4, 6, 12, 10, 0, (45, 80), (16, 32), (0.40, 0.90), (0.15, 0.55), (0, 2), (8, 10)),
        _plant("tillandsia_fuchsii", "Tillandsia fuchsii", "bromeliad_air", "fine air tuft", 3, 5, 10, 9, 0, (45, 78), (16, 32), (0.45, 0.90), (0.15, 0.50), (0, 2), (8, 10)),
        _plant("masdevallia_mini", "Mini Masdevallia", "orchid_mini", "cool orchid fan", 4, 6, 14, 12, 1, (70, 95), (12, 24), (0.20, 0.55), (0.35, 0.75), (1, 4), (7, 10)),
        _plant("pleurothallis", "Pleurothallis", "orchid_mini", "tiny orchid fan", 3, 5, 12, 10, 1, (70, 96), (16, 27), (0.20, 0.60), (0.35, 0.80), (1, 4), (7, 10)),
        _plant("restrepia", "Restrepia", "orchid_mini", "small orchid fan", 3, 5, 12, 10, 1, (70, 95), (14, 26), (0.20, 0.55), (0.35, 0.75), (1, 4), (7, 10)),
        _plant("jewel_orchid_mini", "Mini jewel orchid", "orchid_mini", "terrestrial orchid", 4, 6, 16, 12, 3, (70, 95), (18, 28), (0.12, 0.45), (0.45, 0.85), (3, 6), (5, 9)),
        _plant("bulbophyllum_mini", "Mini Bulbophyllum", "orchid_mini", "creeping orchid", 4, 6, 16, 9, 1, (70, 95), (18, 29), (0.22, 0.60), (0.35, 0.75), (1, 4), (7, 10)),
        _plant("peperomia_prostrata", "String of turtles", "creeper", "trailing peperomia", 4, 6, 18, 6, 2, (60, 90), (18, 29), (0.25, 0.65), (0.30, 0.70), (2, 5), (5, 9)),
        _plant("pilea_glauca", "Pilea glauca", "creeper", "fine creeping stems", 4, 7, 22, 8, 2, (65, 92), (18, 29), (0.20, 0.60), (0.35, 0.80), (2, 6), (5, 9)),
        _plant("ficus_pumila_minima", "Mini creeping fig", "creeper", "clinging creeper", 5, 8, 30, 10, 4, (65, 95), (18, 30), (0.20, 0.65), (0.40, 0.85), (3, 7), (5, 9)),
        _plant("selaginella", "Selaginella", "creeper", "clubmoss mat", 5, 8, 28, 6, 2, (75, 100), (16, 28), (0.12, 0.45), (0.50, 0.95), (1, 4), (4, 8)),
        _plant("marcgravia_mini", "Mini Marcgravia", "creeper", "shingling vine", 4, 6, 20, 8, 2, (70, 96), (18, 29), (0.20, 0.60), (0.40, 0.85), (2, 5), (6, 10)),
    )
}

PLANT_ALIASES: dict[str, str] = {}
for plant_key, definition in PLANTS.items():
    PLANT_ALIASES[normalize_key(plant_key)] = plant_key
    PLANT_ALIASES[normalize_key(definition.display_name)] = plant_key
    for alias in definition.aliases:
        PLANT_ALIASES[normalize_key(alias)] = plant_key


@dataclass(slots=True)
class Planting:
    planting_id: str
    plant: str
    area_percent: float
    site: str = "surface"
    root_mass_percent: float = 100.0
    root_pruned_percent: float = 0.0
    prune_stress: float = 0.0
    health: float = 100.0
    status: str = "planted"
    survival_state: str = "adapting"
    growth_stage: str = "establishing"
    growth_rate: float = 0.0
    reproduction_progress: float = 0.0
    offspring_potential: int = 0
    population_pressure: float = 0.0
    age_ticks: int = 0
    x_percent: float = 50.0
    y_percent: float = 50.0
    z_cm: float = 0.0
    footprint_cm2: float = 0.0
    initial_footprint_cm2: float = 0.0
    height_cm: float = 0.0
    root_length_cm: float = 0.0
    attached_to: str = ""
    attachment_surface: str = ""
    yaw_deg: float = 0.0
    pitch_deg: float = 90.0
    lean_deg: float = 0.0
    lean_reason: str = ""
    footprint_aspect_ratio: float = 1.0
    spread_direction_deg: float = 0.0
    shape_state: str = "round"
    root_health: float = 100.0
    attachment_feature: str = ""
    stem_count: int = 1
    leaf_count: int = 0
    root_anchor_count: int = 0
    visible_damage_percent: float = 0.0
    mold_contact_percent: float = 0.0
    last_interaction: str = ""
    damaged_leaf_count: int = 0
    new_growth_count: int = 0
    root_tip_count: int = 0
    flower_count: int = 0
    canopy_density_percent: float = 0.0
    attachment_normal_deg: float = 0.0
    attachment_contact_area_cm2: float = 0.0
    death_processed: bool = False


def canonical_plant_key(name: str) -> str:
    key = normalize_key(name)
    try:
        return PLANT_ALIASES[key]
    except KeyError as exc:
        allowed = ", ".join(sorted(PLANTS))
        raise ValueError(f"unknown plant '{name}', expected one of: {allowed}") from exc


def copy_plantings(plantings: list[Planting]) -> list[Planting]:
    return [
        Planting(
            planting_id=planting.planting_id,
            plant=planting.plant,
            area_percent=planting.area_percent,
            site=planting.site,
            root_mass_percent=planting.root_mass_percent,
            root_pruned_percent=planting.root_pruned_percent,
            prune_stress=planting.prune_stress,
            health=planting.health,
            status=planting.status,
            survival_state=planting.survival_state,
            growth_stage=planting.growth_stage,
            growth_rate=planting.growth_rate,
            reproduction_progress=planting.reproduction_progress,
            offspring_potential=planting.offspring_potential,
            population_pressure=planting.population_pressure,
            age_ticks=planting.age_ticks,
            x_percent=planting.x_percent,
            y_percent=planting.y_percent,
            z_cm=planting.z_cm,
            footprint_cm2=planting.footprint_cm2,
            initial_footprint_cm2=planting.initial_footprint_cm2,
            height_cm=planting.height_cm,
            root_length_cm=planting.root_length_cm,
            attached_to=planting.attached_to,
            attachment_surface=planting.attachment_surface,
            yaw_deg=planting.yaw_deg,
            pitch_deg=planting.pitch_deg,
            lean_deg=planting.lean_deg,
            lean_reason=planting.lean_reason,
            footprint_aspect_ratio=planting.footprint_aspect_ratio,
            spread_direction_deg=planting.spread_direction_deg,
            shape_state=planting.shape_state,
            root_health=planting.root_health,
            attachment_feature=planting.attachment_feature,
            stem_count=planting.stem_count,
            leaf_count=planting.leaf_count,
            root_anchor_count=planting.root_anchor_count,
            visible_damage_percent=planting.visible_damage_percent,
            mold_contact_percent=planting.mold_contact_percent,
            last_interaction=planting.last_interaction,
            damaged_leaf_count=planting.damaged_leaf_count,
            new_growth_count=planting.new_growth_count,
            root_tip_count=planting.root_tip_count,
            flower_count=planting.flower_count,
            canopy_density_percent=planting.canopy_density_percent,
            attachment_normal_deg=planting.attachment_normal_deg,
            attachment_contact_area_cm2=planting.attachment_contact_area_cm2,
            death_processed=planting.death_processed,
        )
        for planting in plantings
    ]


ANIMAL_SITES = ("substrate", "soil", "leaf_litter", "moss", "surface", "water", "hardscape")


@dataclass(slots=True, frozen=True)
class AnimalDefinition:
    key: str
    display_name: str
    role: str
    size_class: str
    min_count: int
    default_count: int
    max_reasonable_count: int
    space_ml_per_count: float
    humidity_range: tuple[float, float]
    temperature_range: tuple[float, float]
    water_range: tuple[float, float]
    oxygen_range: tuple[float, float]
    food_source: str
    detritus_processing: float
    mold_control: float
    plant_risk: float
    base_growth_rate: float
    reproduction_rate: float
    min_reproductive_count: int
    reproduction_mode: str
    aliases: tuple[str, ...] = ()
    notes: str = ""
    activity_area_cm2_per_count: float = 0.08
    minimum_activity_area_cm2: float = 0.25
    movement_range_cm: float = 2.0
    feeding_rate: float = 1.0
    assimilation_efficiency: float = 0.42
    waste_rate: float = 1.0
    respiration_rate: float = 1.0
    diet_weights: tuple[tuple[str, float], ...] = ()


def _animal(
    key: str,
    display_name: str,
    role: str,
    size_class: str,
    min_count: int,
    default_count: int,
    max_reasonable_count: int,
    space_ml_per_count: float,
    humidity_range: tuple[float, float],
    temperature_range: tuple[float, float],
    water_range: tuple[float, float],
    oxygen_range: tuple[float, float],
    food_source: str,
    detritus_processing: float,
    mold_control: float,
    plant_risk: float,
    base_growth_rate: float,
    reproduction_rate: float,
    min_reproductive_count: int,
    reproduction_mode: str,
    aliases: tuple[str, ...] = (),
    notes: str = "",
    activity_area_cm2_per_count: float | None = None,
    minimum_activity_area_cm2: float | None = None,
    movement_range_cm: float | None = None,
    feeding_rate: float | None = None,
    assimilation_efficiency: float | None = None,
    waste_rate: float | None = None,
    respiration_rate: float | None = None,
    diet_weights: tuple[tuple[str, float], ...] | None = None,
) -> AnimalDefinition:
    if activity_area_cm2_per_count is None:
        activity_area_cm2_per_count = {
            "micro": 0.045,
            "tiny": 0.22,
            "small": 0.65,
        }.get(size_class, 0.18)
    if minimum_activity_area_cm2 is None:
        minimum_activity_area_cm2 = {
            "micro": 0.35,
            "tiny": 0.80,
            "small": 1.40,
        }.get(size_class, 0.60)
    if movement_range_cm is None:
        movement_range_cm = {
            "micro": 1.4,
            "tiny": 2.2,
            "small": 3.4,
        }.get(size_class, 2.0)
    default_feeding, default_assimilation, default_waste, default_respiration = _animal_resource_defaults(role, size_class)
    return AnimalDefinition(
        key=key,
        display_name=display_name,
        role=role,
        size_class=size_class,
        min_count=min_count,
        default_count=default_count,
        max_reasonable_count=max_reasonable_count,
        space_ml_per_count=space_ml_per_count,
        humidity_range=humidity_range,
        temperature_range=temperature_range,
        water_range=water_range,
        oxygen_range=oxygen_range,
        food_source=food_source,
        detritus_processing=detritus_processing,
        mold_control=mold_control,
        plant_risk=plant_risk,
        base_growth_rate=base_growth_rate,
        reproduction_rate=reproduction_rate,
        min_reproductive_count=min_reproductive_count,
        reproduction_mode=reproduction_mode,
        aliases=aliases,
        notes=notes,
        activity_area_cm2_per_count=activity_area_cm2_per_count,
        minimum_activity_area_cm2=minimum_activity_area_cm2,
        movement_range_cm=movement_range_cm,
        feeding_rate=default_feeding if feeding_rate is None else feeding_rate,
        assimilation_efficiency=default_assimilation if assimilation_efficiency is None else assimilation_efficiency,
        waste_rate=default_waste if waste_rate is None else waste_rate,
        respiration_rate=default_respiration if respiration_rate is None else respiration_rate,
        diet_weights=_animal_diet_defaults(role, detritus_processing, mold_control, plant_risk) if diet_weights is None else _normalize_diet_weights(diet_weights),
    )


def _animal_resource_defaults(role: str, size_class: str) -> tuple[float, float, float, float]:
    feeding = {"micro": 0.56, "tiny": 0.86, "small": 1.12}.get(size_class, 0.78)
    respiration = {"micro": 0.58, "tiny": 0.86, "small": 1.20}.get(size_class, 0.85)
    if role == "decomposer":
        return (feeding * 0.92, 0.34, 1.18, respiration * 0.90)
    if role == "micro_consumer":
        return (feeding * 0.98, 0.38, 1.06, respiration * 0.96)
    if role == "small_consumer":
        return (feeding * 1.08, 0.46, 0.92, respiration * 1.08)
    return (feeding, 0.42, 1.0, respiration)


def _normalize_diet_weights(weights: tuple[tuple[str, float], ...]) -> tuple[tuple[str, float], ...]:
    allowed = {"plants", "algae", "detritus", "microbes", "mold", "biofilm"}
    totals: dict[str, float] = {}
    for food, weight in weights:
        key = normalize_key(food)
        if key not in allowed:
            continue
        amount = max(0.0, float(weight))
        if amount > 0:
            totals[key] = totals.get(key, 0.0) + amount
    total = sum(totals.values())
    if total <= 0.0:
        return (("detritus", 1.0),)
    return tuple(sorted((food, weight / total) for food, weight in totals.items()))


def _animal_diet_defaults(
    role: str,
    detritus_processing: float,
    mold_control: float,
    plant_risk: float,
) -> tuple[tuple[str, float], ...]:
    if role == "decomposer":
        return _normalize_diet_weights(
            (
                ("detritus", 0.62 + detritus_processing * 0.18),
                ("mold", 0.18 + mold_control * 0.18),
                ("biofilm", 0.12),
                ("plants", plant_risk * 0.10),
            )
        )
    if role == "micro_consumer":
        return _normalize_diet_weights(
            (
                ("microbes", 0.50),
                ("biofilm", 0.32),
                ("mold", 0.12 + mold_control * 0.08),
                ("detritus", 0.06 + detritus_processing * 0.08),
                ("plants", plant_risk * 0.06),
            )
        )
    if role == "small_consumer":
        return _normalize_diet_weights(
            (
                ("biofilm", 0.34),
                ("algae", 0.28),
                ("plants", 0.10 + plant_risk * 0.34),
                ("detritus", 0.08 + detritus_processing * 0.05),
                ("mold", 0.06 + mold_control * 0.05),
            )
        )
    return _normalize_diet_weights((("plants", 0.45), ("algae", 0.55)))


ANIMALS = {
    item.key: item
    for item in (
        _animal(
            "springtail",
            "Springtail colony",
            "decomposer",
            "micro",
            5,
            30,
            350,
            0.003,
            (70, 100),
            (16, 28),
            (0.45, 0.95),
            (0.25, 1.00),
            "mold and soft detritus",
            0.75,
            0.90,
            0.00,
            0.020,
            0.055,
            20,
            "eggs in damp litter",
            aliases=("collembola",),
            notes="Good first decomposer; population should still be space-limited.",
        ),
        _animal(
            "dwarf_white_isopod",
            "Dwarf white isopod",
            "decomposer",
            "small",
            2,
            8,
            80,
            0.120,
            (75, 100),
            (18, 28),
            (0.50, 0.95),
            (0.30, 1.00),
            "leaf litter and decaying wood",
            0.65,
            0.35,
            0.03,
            0.012,
            0.030,
            6,
            "brood pouch",
            aliases=("isopod", "woodlouse", "woodlice"),
            notes="Hardier than many tiny animals, but crowded bottles should not let it boom.",
        ),
        _animal(
            "tropical_isopod",
            "Small tropical isopod",
            "decomposer",
            "small",
            2,
            5,
            45,
            0.180,
            (70, 100),
            (18, 30),
            (0.45, 0.92),
            (0.35, 1.00),
            "leaf litter and rotting bark",
            0.70,
            0.25,
            0.06,
            0.010,
            0.022,
            4,
            "brood pouch",
        ),
        _animal(
            "soil_mite",
            "Soil mite culture",
            "decomposer",
            "micro",
            10,
            40,
            400,
            0.002,
            (65, 100),
            (14, 28),
            (0.35, 0.92),
            (0.20, 1.00),
            "fungi and fine detritus",
            0.45,
            0.55,
            0.00,
            0.016,
            0.045,
            25,
            "eggs in substrate",
            aliases=("mite",),
        ),
        _animal(
            "enchytraeid_worm",
            "Enchytraeid worm",
            "decomposer",
            "small",
            3,
            10,
            120,
            0.040,
            (80, 100),
            (10, 24),
            (0.55, 1.00),
            (0.25, 0.95),
            "wet organic matter",
            0.80,
            0.20,
            0.00,
            0.012,
            0.025,
            8,
            "cocoons",
            aliases=("white_worm",),
        ),
        _animal(
            "nematode_mix",
            "Nematode microfauna",
            "micro_consumer",
            "micro",
            20,
            80,
            900,
            0.0004,
            (70, 100),
            (12, 30),
            (0.45, 1.00),
            (0.15, 1.00),
            "microbes and dissolved organics",
            0.25,
            0.10,
            0.01,
            0.018,
            0.040,
            50,
            "eggs",
            aliases=("nematodes",),
        ),
        _animal(
            "micro_snail",
            "Micro snail",
            "small_consumer",
            "tiny",
            1,
            3,
            24,
            0.080,
            (70, 100),
            (16, 28),
            (0.55, 1.00),
            (0.25, 1.00),
            "biofilm and tender algae",
            0.20,
            0.20,
            0.12,
            0.008,
            0.018,
            3,
            "egg clusters",
            aliases=("tiny_snail",),
            notes="Useful for biofilm, but plant risk rises if food is scarce.",
        ),
        _animal(
            "tiny_slug",
            "Tiny slug",
            "small_consumer",
            "tiny",
            1,
            1,
            10,
            0.120,
            (80, 100),
            (14, 25),
            (0.60, 1.00),
            (0.25, 0.95),
            "biofilm and soft plant tissue",
            0.15,
            0.10,
            0.35,
            0.006,
            0.010,
            2,
            "egg clusters",
            notes="Included as a risky consumer; not a default cleanup animal.",
        ),
        _animal(
            "aquatic_ostracod",
            "Aquatic ostracod",
            "small_consumer",
            "micro",
            5,
            20,
            180,
            0.004,
            (75, 100),
            (12, 28),
            (0.65, 1.00),
            (0.20, 1.00),
            "wet biofilm and suspended detritus",
            0.35,
            0.10,
            0.00,
            0.012,
            0.028,
            15,
            "eggs",
            aliases=("seed_shrimp", "ostracod"),
        ),
        _animal(
            "fungus_gnat_larva",
            "Fungus gnat larva",
            "small_consumer",
            "tiny",
            1,
            4,
            40,
            0.020,
            (70, 100),
            (16, 28),
            (0.50, 1.00),
            (0.20, 1.00),
            "fungus, detritus, and fine roots",
            0.25,
            0.30,
            0.30,
            0.010,
            0.020,
            4,
            "eggs in wet soil",
            aliases=("gnat_larva",),
            notes="A possible ecosystem participant, but risky around tender roots.",
        ),
    )
}

ANIMAL_ALIASES: dict[str, str] = {}
for animal_key, definition in ANIMALS.items():
    ANIMAL_ALIASES[normalize_key(animal_key)] = animal_key
    ANIMAL_ALIASES[normalize_key(definition.display_name)] = animal_key
    for alias in definition.aliases:
        ANIMAL_ALIASES[normalize_key(alias)] = animal_key


@dataclass(slots=True)
class AnimalGroup:
    group_id: str
    animal: str
    count: int
    site: str = "substrate"
    survival_state: str = "adapting"
    growth_rate: float = 0.0
    reproduction_progress: float = 0.0
    population_trend: str = "settling"
    crowding_pressure: float = 0.0
    mortality_pressure: float = 0.0
    age_ticks: int = 0
    x_percent: float = 50.0
    y_percent: float = 50.0
    z_cm: float = 0.0
    activity_area_cm2: float = 0.0
    attached_to: str = ""
    attachment_surface: str = ""
    microhabitat: str = "open"
    visible_activity: float = 0.0
    shelter_use: float = 0.0
    last_x_percent: float = 50.0
    last_y_percent: float = 50.0
    target_x_percent: float = 50.0
    target_y_percent: float = 50.0
    movement_state: str = "settled"
    movement_reason: str = ""
    distance_moved_cm: float = 0.0


def canonical_animal_key(name: str) -> str:
    key = normalize_key(name)
    try:
        return ANIMAL_ALIASES[key]
    except KeyError as exc:
        allowed = ", ".join(sorted(ANIMALS))
        raise ValueError(f"unknown animal '{name}', expected one of: {allowed}") from exc


def copy_animal_groups(groups: list[AnimalGroup]) -> list[AnimalGroup]:
    return [
        AnimalGroup(
            group_id=group.group_id,
            animal=group.animal,
            count=group.count,
            site=group.site,
            survival_state=group.survival_state,
            growth_rate=group.growth_rate,
            reproduction_progress=group.reproduction_progress,
            population_trend=group.population_trend,
            crowding_pressure=group.crowding_pressure,
            mortality_pressure=group.mortality_pressure,
            age_ticks=group.age_ticks,
            x_percent=group.x_percent,
            y_percent=group.y_percent,
            z_cm=group.z_cm,
            activity_area_cm2=group.activity_area_cm2,
            attached_to=group.attached_to,
            attachment_surface=group.attachment_surface,
            microhabitat=group.microhabitat,
            visible_activity=group.visible_activity,
            shelter_use=group.shelter_use,
            last_x_percent=group.last_x_percent,
            last_y_percent=group.last_y_percent,
            target_x_percent=group.target_x_percent,
            target_y_percent=group.target_y_percent,
            movement_state=group.movement_state,
            movement_reason=group.movement_reason,
            distance_moved_cm=group.distance_moved_cm,
        )
        for group in groups
    ]


@dataclass(slots=True)
class TerrariumState:
    tick: int = 0
    hour: int = 0
    light: float = 0.0
    sun_azimuth_deg: float = 180.0
    sun_altitude_deg: float = 0.0
    window_direction: str = "south"
    window_azimuth_deg: float = 180.0
    window_facing_deg: float = 180.0
    window_light_mode: str = "mixed"
    calendar_start_day_of_year: int = 140
    calendar_day_of_year: int = 140
    season: str = "spring"
    weather_mode: str = "variable"
    weather_state: str = "clear"
    weather_day: int = -1
    moss_lamp_enabled: bool = False
    moss_lamp_angle_deg: float = 0.0
    moss_lamp_intensity: float = DEFAULT_MOSS_LAMP_INTENSITY
    moss_lamp_start_hour: int = MOSS_LAMP_START_HOUR
    moss_lamp_duration_hours: int = MOSS_LAMP_DURATION_HOURS
    umbrella_enabled: bool = False
    umbrella_coverage_percent: float = UMBRELLA_DEFAULT_COVERAGE
    umbrella_x_percent: float = 50.0
    umbrella_y_percent: float = 50.0
    umbrella_angle_deg: float = 180.0
    umbrella_tilt_deg: float = UMBRELLA_DEFAULT_TILT_DEG
    window_light: float = 0.0
    window_direct_light: float = 0.0
    window_diffuse_light: float = 0.0
    moss_lamp_light: float = 0.0
    placement_heat_bias: float = 0.0
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
    container: ContainerSpec = field(default_factory=ContainerSpec)
    substrate_layers: list[SubstrateLayer] = field(default_factory=list)
    mesh_barrier: bool = False
    soil_moistened_ml: float = 0.0
    sprayed_ml: float = 0.0
    spray_count: int = 0
    liquid_water_ml: float = 0.0
    vapor_water_ml: float = 0.0
    condensation_ml: float = 0.0
    surface_wetness: float = 0.0
    biofilm: float = 0.08
    mold_pressure: float = 0.06
    root_zone_oxygen: float = 0.72
    leaf_litter_cover: float = 0.08
    water_cycle_initialized: bool = False
    hardscape_items: list[HardscapeItem] = field(default_factory=list)
    hardscape_serial: int = 0
    plantings: list[Planting] = field(default_factory=list)
    planting_serial: int = 0
    animal_groups: list[AnimalGroup] = field(default_factory=list)
    animal_serial: int = 0
    sealed: bool = False
    sealed_tick: int | None = None
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
        container_data = data.pop("container", None)
        data["container"] = ContainerSpec(**container_data) if container_data else ContainerSpec()
        layer_data = data.pop("substrate_layers", [])
        data["substrate_layers"] = [
            SubstrateLayer(
                layer_kind=item["layer_kind"],
                height_cm=item["height_cm"],
                portions=[SubstratePortion(**portion) for portion in item.get("portions", [])],
                slope_x_cm=item.get("slope_x_cm", 0.0),
                slope_y_cm=item.get("slope_y_cm", 0.0),
            )
            for item in layer_data
        ]
        item_data = data.pop("hardscape_items", [])
        legacy_umbrellas = [item for item in item_data if item.get("kind") == "mini_umbrella"]
        if legacy_umbrellas and not data.get("umbrella_enabled", False):
            umbrella = legacy_umbrellas[-1]
            legacy_coverage = float(umbrella.get("coverage_percent", UMBRELLA_DEFAULT_COVERAGE))
            if legacy_coverage < UMBRELLA_MIN_COVERAGE:
                legacy_coverage = UMBRELLA_DEFAULT_COVERAGE
            data["umbrella_enabled"] = True
            data["umbrella_coverage_percent"] = clamp(legacy_coverage, UMBRELLA_MIN_COVERAGE, UMBRELLA_MAX_COVERAGE)
            data["umbrella_x_percent"] = umbrella.get("x_percent", 50.0)
            data["umbrella_y_percent"] = umbrella.get("y_percent", 50.0)
            data["umbrella_angle_deg"] = umbrella.get("rotation_deg", 180.0)
            data["umbrella_tilt_deg"] = umbrella.get("tilt_deg", UMBRELLA_DEFAULT_TILT_DEG)
        item_data = [item for item in item_data if item.get("kind") != "mini_umbrella"]
        data["hardscape_items"] = [HardscapeItem(**item) for item in item_data]
        planting_data = data.pop("plantings", [])
        data["plantings"] = [Planting(**planting) for planting in planting_data]
        animal_data = data.pop("animal_groups", [])
        data["animal_groups"] = [AnimalGroup(**group) for group in animal_data]
        data.pop("window_cover", None)
        state = TerrariumState(**data)
        if state.umbrella_enabled:
            if state.umbrella_coverage_percent < UMBRELLA_MIN_COVERAGE:
                state.umbrella_coverage_percent = UMBRELLA_DEFAULT_COVERAGE
            state.umbrella_coverage_percent = clamp(
                state.umbrella_coverage_percent,
                UMBRELLA_MIN_COVERAGE,
                UMBRELLA_MAX_COVERAGE,
            )
        return cls(state=state, seed=state.seed)

    def snapshot(self) -> TerrariumState:
        state = self.state
        return TerrariumState(
            tick=state.tick,
            hour=state.hour,
            light=state.light,
            sun_azimuth_deg=state.sun_azimuth_deg,
            sun_altitude_deg=state.sun_altitude_deg,
            window_direction=state.window_direction,
            window_azimuth_deg=state.window_azimuth_deg,
            window_facing_deg=state.window_facing_deg,
            window_light_mode=state.window_light_mode,
            calendar_start_day_of_year=state.calendar_start_day_of_year,
            calendar_day_of_year=state.calendar_day_of_year,
            season=state.season,
            weather_mode=state.weather_mode,
            weather_state=state.weather_state,
            weather_day=state.weather_day,
            moss_lamp_enabled=state.moss_lamp_enabled,
            moss_lamp_angle_deg=state.moss_lamp_angle_deg,
            moss_lamp_intensity=state.moss_lamp_intensity,
            moss_lamp_start_hour=state.moss_lamp_start_hour,
            moss_lamp_duration_hours=state.moss_lamp_duration_hours,
            umbrella_enabled=state.umbrella_enabled,
            umbrella_coverage_percent=state.umbrella_coverage_percent,
            umbrella_x_percent=state.umbrella_x_percent,
            umbrella_y_percent=state.umbrella_y_percent,
            umbrella_angle_deg=state.umbrella_angle_deg,
            umbrella_tilt_deg=state.umbrella_tilt_deg,
            window_light=state.window_light,
            window_direct_light=state.window_direct_light,
            window_diffuse_light=state.window_diffuse_light,
            moss_lamp_light=state.moss_lamp_light,
            placement_heat_bias=state.placement_heat_bias,
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
            container=ContainerSpec(**asdict(state.container)),
            substrate_layers=copy_substrate_layers(state.substrate_layers),
            mesh_barrier=state.mesh_barrier,
            soil_moistened_ml=state.soil_moistened_ml,
            sprayed_ml=state.sprayed_ml,
            spray_count=state.spray_count,
            liquid_water_ml=state.liquid_water_ml,
            vapor_water_ml=state.vapor_water_ml,
            condensation_ml=state.condensation_ml,
            surface_wetness=state.surface_wetness,
            biofilm=state.biofilm,
            mold_pressure=state.mold_pressure,
            root_zone_oxygen=state.root_zone_oxygen,
            leaf_litter_cover=state.leaf_litter_cover,
            water_cycle_initialized=state.water_cycle_initialized,
            hardscape_items=copy_hardscape_items(state.hardscape_items),
            hardscape_serial=state.hardscape_serial,
            plantings=copy_plantings(state.plantings),
            planting_serial=state.planting_serial,
            animal_groups=copy_animal_groups(state.animal_groups),
            animal_serial=state.animal_serial,
            sealed=state.sealed,
            sealed_tick=state.sealed_tick,
            seed=state.seed,
            events=list(state.events),
            flux=FluxReport(**state.flux.as_dict()),
        )

    def run(self, ticks: int) -> TerrariumState:
        for _ in range(ticks):
            self.step()
        return self.state

    def _plant_resource_profile(self) -> dict[str, float]:
        s = self.state
        if not s.plantings:
            return {
                "photosynthesis_efficiency": 1.0,
                "nutrient_demand": 1.0,
                "water_use_rate": 1.0,
                "respiration_rate": 1.0,
            }

        totals = {
            "photosynthesis_efficiency": 0.0,
            "nutrient_demand": 0.0,
            "water_use_rate": 0.0,
            "respiration_rate": 0.0,
        }
        weight_total = 0.0
        base_area = max(s.container.base_area_cm2, 1.0)
        for planting in s.plantings:
            if planting.status == "dead" or planting.survival_state == "dead" or planting.health <= 0.0:
                continue
            definition = PLANTS[planting.plant]
            footprint = planting.footprint_cm2 or base_area * planting.area_percent / 100.0
            footprint_signal = max(0.10, footprint / base_area * 100.0)
            vitality = clamp(planting.health / 100.0 * 0.70 + planting.root_health / 100.0 * 0.30, 0.12, 1.0)
            weight = footprint_signal * vitality
            totals["photosynthesis_efficiency"] += definition.photosynthesis_efficiency * weight
            totals["nutrient_demand"] += definition.nutrient_demand * weight
            totals["water_use_rate"] += definition.water_use_rate * weight
            totals["respiration_rate"] += definition.respiration_rate * weight
            weight_total += weight

        if weight_total <= 0.0:
            return {
                "photosynthesis_efficiency": 0.55,
                "nutrient_demand": 0.40,
                "water_use_rate": 0.40,
                "respiration_rate": 0.55,
            }
        return {key: totals[key] / weight_total for key in totals}

    def _animal_resource_profile(self) -> dict[str, float | dict[str, float]]:
        diet_keys = ("plants", "algae", "detritus", "microbes", "mold", "biofilm")
        if not self.state.animal_groups:
            return {
                "feeding_rate": 1.0,
                "assimilation_efficiency": 0.42,
                "waste_rate": 1.0,
                "respiration_rate": 1.0,
                "diet": {"plants": 0.45, "algae": 0.55, "detritus": 0.0, "microbes": 0.0, "mold": 0.0, "biofilm": 0.0},
            }

        totals = {
            "feeding_rate": 0.0,
            "assimilation_efficiency": 0.0,
            "waste_rate": 0.0,
            "respiration_rate": 0.0,
        }
        diet = {key: 0.0 for key in diet_keys}
        weight_total = 0.0
        for group in self.state.animal_groups:
            if group.count <= 0 or group.survival_state == "dead":
                continue
            definition = ANIMALS[group.animal]
            size_signal = {"micro": 0.35, "tiny": 0.72, "small": 1.45}.get(definition.size_class, 0.65)
            activity = clamp(0.55 + group.visible_activity / 100.0 * 0.45, 0.40, 1.0)
            weight = max(0.01, group.count * size_signal * activity)
            totals["feeding_rate"] += definition.feeding_rate * weight
            totals["assimilation_efficiency"] += definition.assimilation_efficiency * weight
            totals["waste_rate"] += definition.waste_rate * weight
            totals["respiration_rate"] += definition.respiration_rate * weight
            for food, diet_weight in definition.diet_weights:
                diet[food] = diet.get(food, 0.0) + diet_weight * weight * definition.feeding_rate
            weight_total += weight

        if weight_total <= 0.0:
            return {
                "feeding_rate": 0.35,
                "assimilation_efficiency": 0.30,
                "waste_rate": 0.80,
                "respiration_rate": 0.45,
                "diet": {key: 0.0 for key in diet_keys},
            }
        diet_total = sum(diet.values())
        if diet_total > 0.0:
            diet = {key: value / diet_total for key, value in diet.items()}
        return {
            "feeding_rate": totals["feeding_rate"] / weight_total,
            "assimilation_efficiency": totals["assimilation_efficiency"] / weight_total,
            "waste_rate": totals["waste_rate"] / weight_total,
            "respiration_rate": totals["respiration_rate"] / weight_total,
            "diet": diet,
        }

    def _animal_food_availability(self, diet: dict[str, float]) -> dict[str, float]:
        s = self.state
        raw_food = {
            "plants": max(0.0, s.plants - 8.0) * 0.010,
            "algae": max(0.0, s.algae - 4.0) * 0.021,
            "detritus": s.detritus * 0.080 + s.leaf_litter_cover * 0.020,
            "microbes": max(0.0, s.microbes - 2.0) * 0.010,
            "mold": s.mold_pressure * 0.030,
            "biofilm": s.biofilm * 0.036,
        }
        return {food: raw_food[food] * clamp(diet.get(food, 0.0)) for food in raw_food}

    def step(self) -> TerrariumState:
        s = self.state
        c = self.config
        events: list[str] = []

        s.tick += 1
        s.hour = s.tick % c.day_length
        s.light, s.sun_azimuth_deg, s.sun_altitude_deg = self._sun_conditions(s.hour)
        target_temperature = self._target_temperature()
        s.temperature += (target_temperature - s.temperature) * 0.31
        s.temperature += self._random.uniform(-0.18, 0.18)

        hardscape = self.hardscape_profile()
        self._advance_water_cycle(hardscape)
        effective_light = clamp(s.light * (1.0 - hardscape["shade"] * 0.55))
        effective_capacity = c.carrying_capacity * clamp(hardscape["plantable_percent"] / 100.0, 0.12, 1.0)
        temp_factor = self._temperature_factor(s.temperature)
        plant_profile = self._plant_resource_profile()
        animal_profile = self._animal_resource_profile()
        water_resource = clamp(s.water / max(0.10, 0.70 * float(plant_profile["water_use_rate"])))
        nutrient_resource = clamp(s.nutrients / max(0.08, 0.52 * float(plant_profile["nutrient_demand"])))
        plant_resource_factor = max(0.0, min(water_resource, nutrient_resource, s.carbon_dioxide))
        density = (s.plants + s.algae + s.grazers + s.microbes) / effective_capacity
        crowding = clamp(1.0 - density * 0.45, 0.22, 1.0)

        algae_resource = self._algae_resource_factor()
        algae_capacity = self._algae_carrying_capacity(hardscape)
        algae_density = s.algae / max(algae_capacity, 1.0)
        algae_crowding = clamp(1.0 - max(0.0, algae_density - 0.70) * 0.18, 0.08, 1.0)

        plant_photo = (
            s.plants
            * 0.010
            * effective_light
            * plant_resource_factor
            * temp_factor
            * crowding
            * float(plant_profile["photosynthesis_efficiency"])
        )
        algae_photo = s.algae * 0.016 * effective_light * min(s.water, s.carbon_dioxide, algae_resource) * temp_factor * algae_crowding
        algae_photo *= 1.0 + hardscape["edge_moisture"] * 0.20
        photosynthesis = plant_photo + algae_photo

        plant_respiration = s.plants * 0.0011 * temp_factor * float(plant_profile["respiration_rate"])
        algae_respiration = s.algae * 0.0018 * temp_factor
        grazer_respiration = s.grazers * 0.0075 * temp_factor * float(animal_profile["respiration_rate"])
        microbe_respiration = s.microbes * 0.0042 * temp_factor
        respiration = plant_respiration + algae_respiration + grazer_respiration + microbe_respiration

        food_availability = self._animal_food_availability(animal_profile["diet"])  # type: ignore[arg-type]
        grazer_appetite = s.grazers * 0.036 * temp_factor * float(animal_profile["feeding_rate"])
        food_capacity = sum(food_availability.values())
        grazing = min(grazer_appetite, food_capacity)
        eaten = (
            {food: grazing * available / food_capacity for food, available in food_availability.items()}
            if food_capacity > 0.0
            else {food: 0.0 for food in food_availability}
        )
        eaten_plants = eaten["plants"]
        eaten_algae = eaten["algae"]
        eaten_detritus = eaten["detritus"]
        eaten_microbes = eaten["microbes"]
        eaten_mold = eaten["mold"]
        eaten_biofilm = eaten["biofilm"]

        decay_capacity = (
            s.microbes
            * 0.00180
            * temp_factor
            * clamp(s.oxygen * 1.4)
            * clamp(0.35 + s.water * 0.95)
        )
        decay = min(s.detritus, decay_capacity)

        planting_pressure = max(0.0, s.plants - effective_capacity * 0.74) / max(1.0, effective_capacity)
        plant_stress = self._plant_stress() + planting_pressure * 0.010
        algae_stress = self._algae_stress(algae_capacity, algae_resource)
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
        assimilation_multiplier = clamp(float(animal_profile["assimilation_efficiency"]) / 0.42, 0.35, 1.45)
        grazer_growth = grazing * 0.48 * clamp(s.oxygen * 1.2) * assimilation_multiplier
        microbe_growth = decay * 1.55

        s.plants += plant_growth - eaten_plants - s.plants * plant_stress
        s.algae += algae_growth - eaten_algae - s.algae * algae_stress
        s.grazers += grazer_growth - s.grazers * grazer_stress
        s.microbes += microbe_growth - eaten_microbes * 0.72 - s.microbes * microbe_stress

        detrital_turnover = s.plants * (0.000020 + plant_stress * 0.0018) + s.algae * 0.000018
        s.detritus += (
            detrital_turnover
            + stress_loss * 0.010
            + grazing * 0.20 * float(animal_profile["waste_rate"])
            - decay
            - eaten_detritus * 0.45
        )
        s.leaf_litter_cover = clamp(s.leaf_litter_cover + detrital_turnover * 0.08)
        s.mold_pressure = max(0.0, s.mold_pressure - eaten_mold * 0.75)
        s.biofilm = max(0.0, s.biofilm - eaten_biofilm * 0.85)
        nutrient_release = self._soil_nutrient_release(decay, temp_factor)
        s.nutrients += (
            decay * 0.055
            + nutrient_release
            - plant_photo * 0.026 * float(plant_profile["nutrient_demand"])
            - algae_photo * 0.035
        )
        self._apply_biological_water_delta(
            respiration * 0.006
            + decay * 0.004
            - plant_photo * 0.0008 * float(plant_profile["water_use_rate"])
            - algae_photo * 0.0008
        )
        air_sensitivity = self._air_exchange_sensitivity()
        s.oxygen += (photosynthesis * 0.115 - respiration * 0.034 - decay * 0.012) * air_sensitivity
        s.carbon_dioxide += (respiration * 0.031 + decay * 0.014 - photosynthesis * 0.105) * air_sensitivity
        self._apply_waterlogged_gas_pressure()
        s.toxicity += (s.detritus - 0.55) * 0.002 if s.detritus > 0.55 else -0.002
        self._advance_visible_ecology(grazing, decay)

        self._apply_small_random_drift()
        self._clamp_state()
        self._advance_living_records()
        self._apply_local_ecological_interactions()
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

    def substrate_height_cm(self) -> float:
        return sum(layer.height_cm for layer in self.state.substrate_layers)

    def substrate_surface_height_cm(self, x_percent: float = 50.0, y_percent: float = 50.0) -> float:
        x, y = self._validate_xy(x_percent, y_percent)
        height = 0.0
        for layer in self.state.substrate_layers:
            if layer.layer_kind == "mesh":
                continue
            height += layer.height_cm
            height += layer.slope_x_cm * ((x - 50.0) / 100.0)
            height += layer.slope_y_cm * ((y - 50.0) / 100.0)
        return clamp(height / self.state.container.height_cm) * self.state.container.height_cm

    def _slope_gradient(self) -> tuple[float, float]:
        slope_x = 0.0
        slope_y = 0.0
        for layer in self.state.substrate_layers:
            if layer.layer_kind == "mesh":
                continue
            slope_x += layer.slope_x_cm
            slope_y += layer.slope_y_cm
        return slope_x, slope_y

    def _local_lowland_factor(self, x_percent: float, y_percent: float) -> float:
        slope_x, slope_y = self._slope_gradient()
        if abs(slope_x) < 1e-9 and abs(slope_y) < 1e-9:
            return 0.5
        normalized_drop = -(
            slope_x * ((x_percent - 50.0) / 50.0)
            + slope_y * ((y_percent - 50.0) / 50.0)
        )
        max_drop = max(abs(slope_x) + abs(slope_y), 1e-9)
        return clamp((normalized_drop / max_drop + 1.0) * 0.5)

    def _slope_strength(self) -> float:
        slope_x, slope_y = self._slope_gradient()
        return clamp(math.hypot(slope_x, slope_y) / 4.0)

    def max_substrate_surface_height_cm(self) -> float:
        height = 0.0
        for layer in self.state.substrate_layers:
            if layer.layer_kind == "mesh":
                continue
            height += layer.height_cm
            height += (abs(layer.slope_x_cm) + abs(layer.slope_y_cm)) * 0.5
        return height

    def remaining_substrate_height_cm(self) -> float:
        return max(0.0, self.state.container.height_cm - self.substrate_height_cm())

    def container_has_physical_contents(self) -> bool:
        return bool(
            self.state.substrate_layers
            or self.state.hardscape_items
            or self.state.plantings
            or self.state.animal_groups
            or self.state.soil_moistened_ml > 0
            or self.state.sprayed_ml > 0
            or self.state.liquid_water_ml > 0
            or self.state.vapor_water_ml > 0
            or self.state.condensation_ml > 0
            or self.state.surface_wetness > 0
        )

    def set_container(self, container: str | ContainerSpec) -> ContainerSpec:
        self._raise_if_sealed()
        if self.container_has_physical_contents():
            raise ValueError("container can only be selected before adding water, layers, hardscape, plants, or animals")
        self.state.container = container_spec(container) if isinstance(container, str) else container
        return self.state.container

    def set_window(self, direction: str) -> str:
        key = canonical_window_direction(direction)
        self.state.window_direction = key
        self.state.window_azimuth_deg = COMPASS_DIRECTIONS[key]
        return key

    def set_window_facing(self, angle_deg: float) -> float:
        self.state.window_facing_deg = self._normalize_degrees(angle_deg)
        return self.state.window_facing_deg

    def set_window_light_mode(self, mode: str) -> str:
        self.state.window_light_mode = canonical_window_light_mode(mode)
        return self.state.window_light_mode

    def set_umbrella(
        self,
        coverage_percent: float | None = None,
        position: str | None = None,
        orientation: str | None = None,
        x_percent: float | None = None,
        y_percent: float | None = None,
        angle_deg: float | None = None,
        tilt_deg: float | None = None,
    ) -> None:
        current = self.state
        coverage = (
            current.umbrella_coverage_percent
            if coverage_percent is None and current.umbrella_enabled
            else UMBRELLA_DEFAULT_COVERAGE if coverage_percent is None
            else float(coverage_percent)
        )
        if coverage < UMBRELLA_MIN_COVERAGE or coverage > UMBRELLA_MAX_COVERAGE:
            raise ValueError(
                f"umbrella coverage should be between {UMBRELLA_MIN_COVERAGE:g}% and {UMBRELLA_MAX_COVERAGE:g}%"
            )

        normalized_position = normalize_key(position or "center")
        if position is not None and normalized_position not in HARDSCAPE_POSITIONS:
            raise ValueError(f"unknown umbrella position '{position}'")
        normalized_orientation = normalize_key(orientation or "flat")
        if orientation is not None and normalized_orientation not in HARDSCAPE_ORIENTATIONS:
            raise ValueError(f"unknown umbrella orientation '{orientation}'")

        if x_percent is None and y_percent is None and position is None and current.umbrella_enabled:
            x = current.umbrella_x_percent
            y = current.umbrella_y_percent
        elif x_percent is None and y_percent is None:
            x, y = POSITION_COORDINATES[normalized_position]
        else:
            x, y = self._validate_xy(50.0 if x_percent is None else x_percent, 50.0 if y_percent is None else y_percent)

        if angle_deg is None and orientation is None and current.umbrella_enabled:
            angle = current.umbrella_angle_deg
        else:
            angle = self._hardscape_rotation_deg(normalized_position, normalized_orientation, angle_deg)
        if tilt_deg is None and orientation is None and current.umbrella_enabled:
            tilt = current.umbrella_tilt_deg
        else:
            tilt = self._umbrella_tilt_deg(normalized_orientation, tilt_deg)

        current.umbrella_enabled = True
        current.umbrella_coverage_percent = coverage
        current.umbrella_x_percent = x
        current.umbrella_y_percent = y
        current.umbrella_angle_deg = angle
        current.umbrella_tilt_deg = tilt

    def clear_umbrella(self) -> None:
        self.state.umbrella_enabled = False

    def set_moss_lamp(self, angle_deg: float, intensity: float | None = None) -> None:
        if intensity is None:
            intensity = self.state.moss_lamp_intensity or DEFAULT_MOSS_LAMP_INTENSITY
        if intensity < 0.0 or intensity > 1.0:
            raise ValueError("moss lamp intensity must be between 0 and 1")
        self.state.moss_lamp_enabled = True
        self.state.moss_lamp_angle_deg = self._normalize_degrees(angle_deg)
        self.state.moss_lamp_intensity = float(intensity)

    def clear_moss_lamp(self) -> None:
        self.state.moss_lamp_enabled = False

    def set_moss_lamp_schedule(self, start_hour: int, duration_hours: int) -> None:
        if start_hour < 0 or start_hour >= self.config.day_length:
            raise ValueError(f"moss lamp start hour must be between 0 and {self.config.day_length - 1}")
        if duration_hours <= 0 or duration_hours > self.config.day_length:
            raise ValueError(f"moss lamp duration must be between 1 and {self.config.day_length} hours")
        self.state.moss_lamp_start_hour = int(start_hour)
        self.state.moss_lamp_duration_hours = int(duration_hours)

    def current_light_compass_deg(self) -> float:
        return self._model_to_compass_degrees(self.state.sun_azimuth_deg)

    def light_source_label(self) -> str:
        s = self.state
        if s.moss_lamp_light > s.window_light + 0.04:
            return "moss lamp"
        if s.window_light > 0.04 and s.moss_lamp_light > 0.04:
            return f"{self._window_light_label()} and moss lamp"
        if s.window_light > 0.04:
            return self._window_light_label()
        if s.moss_lamp_light > 0.04:
            return "moss lamp"
        return "no direct light"

    def _window_light_label(self) -> str:
        s = self.state
        weather = WEATHER_PROFILES.get(s.weather_state, WEATHER_PROFILES["clear"])["label"]
        if s.window_direct_light > s.window_diffuse_light * 1.25 and s.window_direct_light > 0.08:
            quality = "direct sun"
        elif s.window_diffuse_light > s.window_direct_light * 1.25 and s.window_diffuse_light > 0.08:
            quality = "diffuse sky light"
        else:
            quality = "mixed window light"
        return f"{quality} from the {s.window_direction} window ({weather}, {s.season})"

    def plant_light_observation(self, planting: Planting) -> str:
        env = self._local_life_environment(planting, self._life_environment())
        light = env["light"]
        if self.state.light <= 0.03:
            tone = "currently dark"
        elif light < 0.16:
            tone = "mostly shaded"
        elif light < 0.36:
            tone = "soft low light"
        elif light < 0.68:
            tone = "steady filtered light"
        else:
            tone = "bright exposed light"

        details: list[str] = [f"{tone} from {self.light_source_label()}"]
        if planting.lean_reason == "toward_light" and self.state.light > 0.03:
            details.append(f"leaning toward {self.current_light_compass_deg():03.0f}deg")
        if self.state.window_direct_light > self.state.window_diffuse_light * 1.4 and self.state.window_direct_light > 0.12:
            details.append("one side has a sharper sun patch")
        elif self.state.window_diffuse_light > self.state.window_direct_light * 1.4 and self.state.window_diffuse_light > 0.10:
            details.append("shadows look soft and spread out")
        if self.state.weather_state in {"overcast", "rainy"} and self.state.window_light > 0.04:
            details.append(f"{self.state.weather_state.replace('_', ' ')} weather mutes the color")
        if self.state.season == "winter" and self.state.hour >= 15:
            details.append("the day fades early")
        elif self.state.season == "summer" and self.state.hour >= 17 and self.state.window_light > 0.12:
            details.append("the long day still reaches the leaves")
        elif planting.lean_reason == "obstacle_pressure":
            details.append("tilted by nearby hardscape or growth")
        elif planting.attached_to and planting.attachment_surface:
            details.append(f"{planting.attachment_surface} attachment shapes the light")
        if env.get("local_overlap", 0.0) > 0.24:
            details.append("neighbor shade is visible")
        if planting.attached_to and env.get("surface_biofilm_bias", 0.0) > 0.08:
            details.append("wet surface film catches the light")
        return "; ".join(details)

    def seal(self) -> None:
        if self.state.sealed:
            raise ValueError("terrarium is already sealed")
        self._raise_if_container_volume_overflows()
        self._ensure_water_cycle_initialized()
        self.state.water = self._water_availability_score()
        self._synchronize_crafted_biomass()
        self.state.sealed = True
        self.state.sealed_tick = self.state.tick

    def _synchronize_crafted_biomass(self) -> None:
        s = self.state
        base_area = max(s.container.base_area_cm2, 1.0)

        plant_biomass = 0.0
        for planting in s.plantings:
            if planting.status == "dead" or planting.health <= 0.0:
                continue
            definition = PLANTS[planting.plant]
            footprint = planting.footprint_cm2 or base_area * planting.area_percent / 100.0
            planted_percent = footprint / base_area * 100.0
            height_factor = clamp(definition.height_cm / 18.0, 0.08, 1.25)
            root_factor = clamp((planting.root_mass_percent / 100.0) * (1.0 - planting.root_pruned_percent / 140.0), 0.18, 1.0)
            health_factor = clamp(planting.health / 100.0, 0.10, 1.0)
            epiphyte_factor = 0.86 if planting.attached_to else 1.0
            plant_biomass += planted_percent * (1.45 + height_factor * 0.50) * root_factor * health_factor * epiphyte_factor
        s.plants = max(0.0, min(140.0, plant_biomass))

        hardscape = self.hardscape_profile()
        wet_visible = clamp(s.surface_wetness * 0.58 + s.water * 0.26 + clamp(s.condensation_ml / 6.0) * 0.16)
        s.algae = max(
            0.0,
            min(
                24.0,
                0.8
                + wet_visible * 5.6
                + float(hardscape["coverage_percent"]) * 0.07
                + float(hardscape["edge_moisture"]) * 3.8
                + s.biofilm * 7.0,
            ),
        )

        animal_biomass = 0.0
        for group in s.animal_groups:
            if group.count <= 0 or group.survival_state == "dead":
                continue
            definition = ANIMALS[group.animal]
            size_factor = {"micro": 0.010, "tiny": 0.032, "small": 0.085}.get(definition.size_class, 0.025)
            role_factor = 1.18 if definition.role == "small_consumer" else 0.72
            animal_biomass += group.count * size_factor * role_factor
        s.grazers = max(0.0, min(32.0, animal_biomass))

        organic_signal = self._crafted_organic_signal()
        s.microbes = max(1.5, min(44.0, 5.0 + organic_signal * 23.0 + s.detritus * 7.0 + wet_visible * 4.0))
        s.detritus = clamp(0.10 + organic_signal * 0.20 + s.leaf_litter_cover * 0.12 + s.detritus * 0.35)

    def _crafted_organic_signal(self) -> float:
        s = self.state
        weighted_organic = 0.0
        total_height = 0.0
        organic_by_substrate = {
            "peat_moss": 0.66,
            "sphagnum_moss": 0.54,
            "compost": 1.0,
            "activated_charcoal": 0.06,
        }
        for layer in s.substrate_layers:
            if layer.layer_kind == "mesh":
                continue
            layer_organic = 0.0
            for portion in layer.portions:
                layer_organic += organic_by_substrate.get(portion.substrate, 0.02) * portion.percent / 100.0
            weighted_organic += layer_organic * layer.height_cm
            total_height += layer.height_cm
        substrate_signal = weighted_organic / total_height if total_height > 0.0 else 0.0

        wood_signal = 0.0
        for item in s.hardscape_items:
            definition = HARDSCAPES[item.kind]
            if definition.category == "wood":
                wood_signal += item.coverage_percent / 100.0 * 0.55
            elif definition.category == "surface":
                wood_signal += item.coverage_percent / 100.0 * 0.18
        return clamp(substrate_signal + wood_signal, 0.0, 1.0)

    def _raise_if_sealed(self) -> None:
        if self.state.sealed:
            raise ValueError("terrarium is sealed")

    def add_substrate(
        self,
        layer_kind: str,
        height_cm: float,
        mixture: dict[str, float],
        slope_x_cm: float = 0.0,
        slope_y_cm: float = 0.0,
    ) -> SubstrateLayer:
        self._raise_if_sealed()
        canonical_layer = canonical_substrate_layer(layer_kind)
        if height_cm <= 0:
            raise ValueError("substrate height must be greater than 0")
        if abs(slope_x_cm) > MAX_LAYER_SLOPE_CM or abs(slope_y_cm) > MAX_LAYER_SLOPE_CM:
            raise ValueError(f"substrate slope must be between {-MAX_LAYER_SLOPE_CM:g} and {MAX_LAYER_SLOPE_CM:g} cm")
        if height_cm > self.remaining_substrate_height_cm() + 1e-9:
            remaining = self.remaining_substrate_height_cm()
            raise ValueError(f"not enough container height remaining: {remaining:0.2f} cm")

        portions = normalize_substrate_mixture(canonical_layer, mixture)
        layer = SubstrateLayer(
            layer_kind=canonical_layer,
            height_cm=height_cm,
            portions=portions,
            slope_x_cm=float(slope_x_cm),
            slope_y_cm=float(slope_y_cm),
        )
        self.state.substrate_layers.append(layer)
        try:
            if self.max_substrate_surface_height_cm() > self.state.container.height_cm + 1e-9:
                raise ValueError(f"not enough container height remaining: {self.remaining_substrate_height_cm():0.2f} cm")
            self._raise_if_container_volume_overflows()
        except ValueError:
            self.state.substrate_layers.pop()
            raise
        return layer

    def dig_substrate(self, height_cm: float) -> SubstrateLayer:
        self._raise_if_sealed()
        if height_cm <= 0:
            raise ValueError("dig height must be greater than 0")
        if not self.state.substrate_layers:
            raise ValueError("there is no substrate to dig out")

        top_layer = self.state.substrate_layers[-1]
        if height_cm > top_layer.height_cm + 1e-9:
            raise ValueError(
                f"can only dig the current top layer ({top_layer.height_cm:0.2f} cm remaining)"
            )

        removed = SubstrateLayer(
            layer_kind=top_layer.layer_kind,
            height_cm=min(height_cm, top_layer.height_cm),
            portions=[SubstratePortion(substrate=portion.substrate, percent=portion.percent) for portion in top_layer.portions],
            slope_x_cm=top_layer.slope_x_cm,
            slope_y_cm=top_layer.slope_y_cm,
        )
        if abs(height_cm - top_layer.height_cm) <= 1e-9:
            self.state.substrate_layers.pop()
        else:
            top_layer.height_cm -= height_cm
        return removed

    def install_mesh_barrier(self) -> None:
        self._raise_if_sealed()
        layer = SubstrateLayer(layer_kind="mesh", height_cm=0.0, portions=[])
        self.state.substrate_layers.append(layer)
        self.state.mesh_barrier = True

    def moisten_soil(self, amount_ml: float) -> None:
        self._raise_if_sealed()
        if amount_ml <= 0:
            raise ValueError("moistening amount must be greater than 0 ml")
        if amount_ml > self.state.container.capacity_ml * 0.45:
            raise ValueError(f"too much water for initial moistening: {amount_ml:g} ml")
        self._ensure_water_cycle_initialized(infer_from_pool=False)
        old_surface = self.state.surface_wetness
        self.state.soil_moistened_ml += amount_ml
        self.state.liquid_water_ml += amount_ml
        self.state.surface_wetness = clamp(self.state.surface_wetness + amount_ml / 90.0)
        try:
            self._raise_if_container_volume_overflows()
        except ValueError:
            self.state.soil_moistened_ml -= amount_ml
            self.state.liquid_water_ml = max(0.0, self.state.liquid_water_ml - amount_ml)
            self.state.surface_wetness = old_surface
            raise
        self.state.water = clamp(self.state.water + amount_ml / self.state.container.capacity_ml * 0.65)

    def spray(self, pumps: int) -> float:
        self._raise_if_sealed()
        if pumps <= 0:
            raise ValueError("spray count must be greater than 0")
        if pumps > 200:
            raise ValueError("spray count is too high for one action")
        amount_ml = pumps * SPRAY_ML_PER_PUMP
        self._ensure_water_cycle_initialized(infer_from_pool=False)
        old_surface = self.state.surface_wetness
        self.state.spray_count += pumps
        self.state.sprayed_ml += amount_ml
        self.state.liquid_water_ml += amount_ml * 0.45
        self.state.condensation_ml += amount_ml * 0.25
        self.state.vapor_water_ml += amount_ml * 0.30
        self.state.surface_wetness = clamp(self.state.surface_wetness + amount_ml / 22.0)
        try:
            self._raise_if_container_volume_overflows()
        except ValueError:
            self.state.spray_count -= pumps
            self.state.sprayed_ml -= amount_ml
            self.state.liquid_water_ml = max(0.0, self.state.liquid_water_ml - amount_ml * 0.45)
            self.state.condensation_ml = max(0.0, self.state.condensation_ml - amount_ml * 0.25)
            self.state.vapor_water_ml = max(0.0, self.state.vapor_water_ml - amount_ml * 0.30)
            self.state.surface_wetness = old_surface
            raise
        self.state.water = clamp(self.state.water + amount_ml / self.state.container.capacity_ml * 0.45)
        return amount_ml

    def mesh_layer_count(self) -> int:
        count = sum(1 for layer in self.state.substrate_layers if layer.layer_kind == "mesh")
        if count == 0 and self.state.mesh_barrier:
            return 1
        return count

    def hardscape_coverage_percent(self) -> float:
        return sum(item.coverage_percent for item in self.state.hardscape_items)

    def hardscape_profile(self) -> dict[str, float | str]:
        raw_coverage = self.hardscape_coverage_percent()
        blocked = 0.0
        shade = 0.0
        evaporation_shield = 0.0
        edge_moisture = 0.0
        north = south = east = west = 0.0

        for item in self.state.hardscape_items:
            definition = HARDSCAPES[item.kind]
            weight = item.coverage_percent / 100.0
            blocked += item.coverage_percent * definition.block_factor
            shade += weight * definition.shade_factor
            evaporation_shield += weight * definition.evaporation_shield
            edge_moisture += weight * definition.edge_moisture

            direction_weight = item.coverage_percent * (0.5 + definition.height_cm / 6.0)
            if item.position in {"north", "northeast", "northwest"} or item.orientation == "leaning_south":
                south += direction_weight
            if item.position in {"south", "southeast", "southwest"} or item.orientation == "leaning_north":
                north += direction_weight
            if item.position in {"east", "northeast", "southeast"} or item.orientation == "leaning_west":
                west += direction_weight
            if item.position in {"west", "northwest", "southwest"} or item.orientation == "leaning_east":
                east += direction_weight

        bias = "balanced"
        vectors = {"north": north, "south": south, "east": east, "west": west}
        strongest = max(vectors, key=vectors.get)
        if vectors[strongest] >= max(5.0, raw_coverage * 0.35):
            bias = strongest

        return {
            "coverage_percent": clamp(raw_coverage / 100.0, 0.0, 1.0) * 100.0,
            "blocked_percent": clamp(blocked / 100.0, 0.0, 1.0) * 100.0,
            "plantable_percent": max(0.0, 100.0 - blocked),
            "shade": clamp(shade, 0.0, 0.45),
            "evaporation_shield": clamp(evaporation_shield, 0.0, 0.75),
            "edge_moisture": clamp(edge_moisture, 0.0, 0.25),
            "growth_bias": bias,
        }

    def place_hardscape(
        self,
        kind: str,
        coverage_percent: float | None = None,
        position: str = "center",
        orientation: str = "flat",
        x_percent: float | None = None,
        y_percent: float | None = None,
        angle_deg: float | None = None,
        tilt_deg: float | None = None,
    ) -> HardscapeItem:
        self._raise_if_sealed()
        canonical_kind = canonical_hardscape_key(kind)
        definition = HARDSCAPES[canonical_kind]
        coverage = definition.default_coverage if coverage_percent is None else float(coverage_percent)
        if coverage <= 0:
            raise ValueError("hardscape coverage must be greater than 0")
        if coverage < definition.min_coverage or coverage > definition.max_coverage:
            raise ValueError(
                f"{canonical_kind} coverage should be between "
                f"{definition.min_coverage:g}% and {definition.max_coverage:g}%"
            )

        normalized_position = normalize_key(position)
        normalized_orientation = normalize_key(orientation)
        if normalized_position not in HARDSCAPE_POSITIONS:
            raise ValueError(f"unknown hardscape position '{position}'")
        if normalized_orientation not in HARDSCAPE_ORIENTATIONS:
            raise ValueError(f"unknown hardscape orientation '{orientation}'")
        rotation = self._hardscape_rotation_deg(normalized_position, normalized_orientation, angle_deg)
        tilt = self._hardscape_tilt_deg(definition, normalized_orientation, tilt_deg)
        explicit_coordinates = x_percent is not None or y_percent is not None
        if explicit_coordinates:
            x, y = self._validate_xy(50.0 if x_percent is None else x_percent, 50.0 if y_percent is None else y_percent)
        else:
            x, y = self._choose_hardscape_xy(normalized_position, normalized_orientation, definition, coverage, rotation, tilt)

        if self.hardscape_coverage_percent() + coverage > MAX_HARDSCAPE_COVERAGE + 1e-9:
            remaining = MAX_HARDSCAPE_COVERAGE - self.hardscape_coverage_percent()
            raise ValueError(f"not enough open surface remaining: {remaining:0.1f}%")

        z_base = self.substrate_surface_height_cm(x, y)
        self.state.hardscape_serial += 1
        item = HardscapeItem(
            item_id=f"H{self.state.hardscape_serial:02d}",
            kind=canonical_kind,
            coverage_percent=coverage,
            position=normalized_position,
            orientation=normalized_orientation,
            rotation_deg=rotation,
            tilt_deg=tilt,
            x_percent=x,
            y_percent=y,
            z_base_cm=z_base,
            z_top_cm=min(self.state.container.height_cm, z_base + self._hardscape_effective_height_cm(definition, tilt)),
            geometry_seed=self._stable_seed(f"H{self.state.hardscape_serial:02d}", canonical_kind),
        )
        self._raise_if_hardscape_collision(item)
        self.state.hardscape_items.append(item)
        try:
            self._raise_if_container_volume_overflows()
        except ValueError:
            self.state.hardscape_items.pop()
            self.state.hardscape_serial -= 1
            raise
        return item

    def pick_hardscape(self, item_id: str) -> HardscapeItem:
        self._raise_if_sealed()
        normalized_id = item_id.strip().upper()
        for index, item in enumerate(self.state.hardscape_items):
            if item.item_id.upper() == normalized_id:
                return self.state.hardscape_items.pop(index)
        raise ValueError(f"unknown hardscape id '{item_id}'")

    def planted_area_percent(self) -> float:
        return sum(planting.area_percent for planting in self.state.plantings)

    def remaining_plantable_area_percent(self) -> float:
        plantable = float(self.hardscape_profile()["plantable_percent"])
        return max(0.0, plantable - self.planted_area_percent())

    def add_planting(
        self,
        plant: str,
        area_percent: float | None = None,
        site: str = "surface",
        x_percent: float | None = None,
        y_percent: float | None = None,
    ) -> Planting:
        self._raise_if_sealed()
        plant_key = canonical_plant_key(plant)
        definition = PLANTS[plant_key]
        area = definition.default_area_percent if area_percent is None else float(area_percent)
        if area < definition.min_area_percent:
            raise ValueError(
                f"{plant_key} needs at least {definition.min_area_percent:g}% planting area"
            )
        x, y = self._resolve_planting_xy(site, x_percent, y_percent)
        normalized_site = self._resolve_planting_site(plant_key, site, x, y, x_percent is not None or y_percent is not None)
        attached_to = ""
        attachment_surface = ""
        attachment_feature = ""
        if normalized_site.startswith("hardscape:"):
            target, surface = self._parse_hardscape_site(normalized_site)
            attached_to = target
            attachment_surface = surface
            if not self._plant_can_attach_to_hardscape(definition):
                raise ValueError(f"{plant_key} needs soil or substrate and cannot attach to hardscape")
            mounted = sum(
                planting.area_percent
                for planting in self.state.plantings
                if (
                    (planting.attached_to.upper() == target.upper() or planting.site.upper() == f"HARDSCAPE:{target.upper()}")
                    and (planting.attachment_surface or "top") == surface
                )
            )
            item = self._find_hardscape_item(target)
            attachment_feature = self._hardscape_surface_detail_at_xy(item, x, y)
            capacity = item.coverage_percent * SURFACE_CAPACITY_FACTORS.get(surface, 0.5)
            if mounted + area > capacity + 1e-9:
                raise ValueError(f"not enough hardscape planting surface on {target}:{surface}: {max(0.0, capacity - mounted):0.1f}%")
        elif area > self.remaining_plantable_area_percent() + 1e-9:
            raise ValueError(
                f"not enough plantable area remaining: {self.remaining_plantable_area_percent():0.1f}%"
            )

        footprint, height, root_length = self._sample_plant_dimensions(definition, area)
        z = self._planting_z_cm(normalized_site, x, y)
        self.state.planting_serial += 1
        planting = Planting(
            planting_id=f"P{self.state.planting_serial:02d}",
            plant=plant_key,
            area_percent=area,
            site=normalized_site,
            growth_rate=definition.base_growth_rate,
            x_percent=x,
            y_percent=y,
            z_cm=z,
            footprint_cm2=footprint,
            initial_footprint_cm2=footprint,
            height_cm=height,
            root_length_cm=root_length,
            attached_to=attached_to,
            attachment_surface=attachment_surface,
            attachment_feature=attachment_feature,
        )
        if x_percent is None and y_percent is None and not planting.attached_to:
            self._choose_planting_xy(planting)
        self._raise_if_plant_collision(planting)
        self._set_plant_attachment_patch(planting)
        self._set_initial_plant_orientation(planting)
        self._set_initial_plant_shape(planting)
        self._set_initial_plant_structure(planting)
        self.state.plantings.append(planting)
        try:
            self._raise_if_container_volume_overflows()
        except ValueError:
            self.state.plantings.pop()
            self.state.planting_serial -= 1
            raise
        return planting

    def remove_planting(self, planting_id: str) -> Planting:
        self._raise_if_sealed()
        normalized_id = planting_id.strip().upper()
        for index, planting in enumerate(self.state.plantings):
            if planting.planting_id.upper() == normalized_id:
                return self.state.plantings.pop(index)
        raise ValueError(f"unknown planting id '{planting_id}'")

    def prune_roots(self, planting_id: str, percent: float) -> Planting:
        self._raise_if_sealed()
        if percent <= 0 or percent > 90:
            raise ValueError("root prune percent must be greater than 0 and at most 90")
        planting = self._find_planting(planting_id)
        planting.root_mass_percent = max(1.0, planting.root_mass_percent * (1.0 - percent / 100.0))
        planting.root_pruned_percent = clamp(planting.root_pruned_percent + percent, 0.0, 100.0)
        planting.prune_stress = clamp(planting.prune_stress + percent * 1.35, 0.0, 100.0)
        planting.status = "recovering" if percent < 35 else "shocked"
        planting.health = max(1.0, planting.health - percent * 0.35)
        planting.growth_rate = max(0.0, planting.growth_rate * (1.0 - percent / 120.0))
        planting.reproduction_progress = max(0.0, planting.reproduction_progress - percent * 0.30)
        planting.population_pressure = clamp(planting.population_pressure + percent * 0.15, 0.0, 100.0)
        return planting

    def animal_count_total(self) -> int:
        return sum(group.count for group in self.state.animal_groups)

    def living_planting_count(self) -> int:
        return sum(
            1
            for planting in self.state.plantings
            if planting.status != "dead" and planting.survival_state != "dead" and planting.health > 0.0
        )

    def living_animal_count(self) -> int:
        return sum(
            group.count
            for group in self.state.animal_groups
            if group.survival_state != "dead" and group.count > 0
        )

    def has_explicit_life(self) -> bool:
        return bool(self.state.plantings or self.state.animal_groups)

    def all_explicit_life_dead(self) -> bool:
        if not self.has_explicit_life():
            return True
        return self.living_planting_count() == 0 and self.living_animal_count() == 0

    def explicit_life_death_reason(self) -> str:
        if not self.has_explicit_life():
            return "no plants or animals were added"
        dead_plants = len(self.state.plantings) - self.living_planting_count()
        if self.living_planting_count() == 0 and self.living_animal_count() == 0:
            if not self.state.plantings:
                return "no plant plantings remain and all animal groups extinct"
            if not self.state.animal_groups:
                return f"{dead_plants} plant planting(s) dead and no animal groups remain"
            return f"{dead_plants} plant planting(s) dead and all animal groups extinct"
        if self.living_planting_count() == 0:
            return f"{dead_plants} plant planting(s) dead"
        if self.living_animal_count() == 0:
            return "all animal groups extinct"
        return "living organisms remain"

    def add_animals(
        self,
        animal: str,
        count: int | None = None,
        site: str = "substrate",
        x_percent: float | None = None,
        y_percent: float | None = None,
    ) -> AnimalGroup:
        self._raise_if_sealed()
        animal_key = canonical_animal_key(animal)
        definition = ANIMALS[animal_key]
        amount = definition.default_count if count is None else int(count)
        if amount < definition.min_count:
            raise ValueError(f"{animal_key} needs at least {definition.min_count} individual(s)")
        if amount > definition.max_reasonable_count:
            raise ValueError(
                f"{animal_key} count should be at most {definition.max_reasonable_count} in this container"
            )

        normalized_site = self._normalize_animal_site(site)
        x, y = self._resolve_animal_xy(normalized_site, x_percent, y_percent)
        z = self._animal_z_cm(normalized_site, x, y)
        attached_to = ""
        attachment_surface = ""
        if normalized_site.startswith("hardscape:"):
            attached_to, attachment_surface = self._parse_hardscape_site(normalized_site)
        self.state.animal_serial += 1
        group = AnimalGroup(
            group_id=f"A{self.state.animal_serial:02d}",
            animal=animal_key,
            count=amount,
            site=normalized_site,
            growth_rate=definition.base_growth_rate,
            x_percent=x,
            y_percent=y,
            z_cm=z,
            activity_area_cm2=self._animal_activity_area(definition, amount),
            attached_to=attached_to,
            attachment_surface=attachment_surface,
            last_x_percent=x,
            last_y_percent=y,
            target_x_percent=x,
            target_y_percent=y,
        )
        if x_percent is None and y_percent is None and not attached_to:
            self._choose_animal_xy(group)
        self._set_initial_animal_microhabitat(group)
        self.state.animal_groups.append(group)
        try:
            self._raise_if_container_volume_overflows()
        except ValueError:
            self.state.animal_groups.pop()
            self.state.animal_serial -= 1
            raise
        return group

    def remove_animal_group(self, group_id: str) -> AnimalGroup:
        self._raise_if_sealed()
        normalized_id = group_id.strip().upper()
        for index, group in enumerate(self.state.animal_groups):
            if group.group_id.upper() == normalized_id:
                return self.state.animal_groups.pop(index)
        raise ValueError(f"unknown animal group id '{group_id}'")

    def animal_activity_area_cm2(self) -> float:
        return sum(self._animal_group_activity_area(group) for group in self.state.animal_groups if group.count > 0)

    def animal_spatial_profile(self) -> dict[str, float]:
        capacities: dict[str, float] = {}
        used = 0.0
        for group in self.state.animal_groups:
            if group.count <= 0 or group.survival_state == "dead":
                continue
            definition = ANIMALS[group.animal]
            habitat_key = self._animal_habitat_key(group)
            capacities[habitat_key] = max(capacities.get(habitat_key, 0.0), self._animal_habitat_area_cm2(group))
            used += self._animal_group_activity_area(group, definition)
        capacity = sum(capacities.values())
        return {
            "activity_area_cm2": used,
            "habitat_area_cm2": capacity,
            "habitat_space_score": clamp(capacity / max(used, 1e-9)) if used > 0 else 1.0,
        }

    def _find_animal_group(self, group_id: str) -> AnimalGroup:
        normalized_id = group_id.strip().upper()
        for group in self.state.animal_groups:
            if group.group_id.upper() == normalized_id:
                return group
        raise ValueError(f"unknown animal group id '{group_id}'")

    def _find_planting(self, planting_id: str) -> Planting:
        normalized_id = planting_id.strip().upper()
        for planting in self.state.plantings:
            if planting.planting_id.upper() == normalized_id:
                return planting
        raise ValueError(f"unknown planting id '{planting_id}'")

    def _find_hardscape_item(self, item_id: str) -> HardscapeItem:
        normalized_id = item_id.strip().upper()
        for item in self.state.hardscape_items:
            if item.item_id.upper() == normalized_id:
                return item
        raise ValueError(f"unknown hardscape id '{item_id}'")

    def _validate_xy(self, x_percent: float, y_percent: float) -> tuple[float, float]:
        try:
            x = float(x_percent)
            y = float(y_percent)
        except (TypeError, ValueError) as exc:
            raise ValueError("x and y coordinates must be numbers from 0 to 100") from exc
        if x < 0.0 or x > 100.0 or y < 0.0 or y > 100.0:
            raise ValueError("x and y coordinates must be between 0 and 100")
        if self.state.container.footprint_shape != "round":
            return x, y
        dx = (x - 50.0) / 50.0
        dy = (y - 50.0) / 50.0
        if dx * dx + dy * dy > 1.0 + 1e-9:
            raise ValueError("x and y coordinates must fall inside the round container footprint")
        return x, y

    def _coord_to_cm(self, x_percent: float, y_percent: float) -> tuple[float, float]:
        if self.state.container.footprint_shape != "round":
            return (
                (x_percent - 50.0) / 100.0 * self.state.container.length_cm,
                (y_percent - 50.0) / 100.0 * self.state.container.width_cm,
            )
        radius = (self.state.container.base_area_cm2 / math.pi) ** 0.5
        return (x_percent - 50.0) / 50.0 * radius, (y_percent - 50.0) / 50.0 * radius

    def _cm_to_coord(self, x_cm: float, y_cm: float) -> tuple[float, float]:
        if self.state.container.footprint_shape != "round":
            return (
                50.0 + x_cm / max(self.state.container.length_cm, 1e-9) * 100.0,
                50.0 + y_cm / max(self.state.container.width_cm, 1e-9) * 100.0,
            )
        radius = (self.state.container.base_area_cm2 / math.pi) ** 0.5
        return 50.0 + x_cm / max(radius, 1e-9) * 50.0, 50.0 + y_cm / max(radius, 1e-9) * 50.0

    def _normalize_degrees(self, angle: float) -> float:
        return float(angle) % 360.0

    def _compass_to_model_degrees(self, angle: float) -> float:
        return self._normalize_degrees(90.0 - angle)

    def _model_to_compass_degrees(self, angle: float) -> float:
        return self._normalize_degrees(90.0 - angle)

    def _angle_delta_deg(self, left: float, right: float) -> float:
        return (right - left + 180.0) % 360.0 - 180.0

    def _turn_toward_angle(self, current: float, target: float, amount: float) -> float:
        return self._normalize_degrees(current + self._angle_delta_deg(current, target) * clamp(amount))

    def _vector_angle_deg(self, dx: float, dy: float) -> float:
        if abs(dx) <= 1e-12 and abs(dy) <= 1e-12:
            return 0.0
        return self._normalize_degrees(math.degrees(math.atan2(dy, dx)))

    def _bearing_between_coords(self, ax: float, ay: float, bx: float, by: float) -> float:
        acx, acy = self._coord_to_cm(ax, ay)
        bcx, bcy = self._coord_to_cm(bx, by)
        return self._vector_angle_deg(bcx - acx, bcy - acy)

    def _stable_seed(self, *parts: object) -> int:
        text = "|".join(str(part) for part in parts)
        value = 2166136261
        for char in text:
            value ^= ord(char)
            value = (value * 16777619) % 4294967291
        return value

    def _stable_unit(self, *parts: object) -> float:
        return self._stable_seed(*parts) / 4294967291.0

    def _hardscape_rotation_deg(self, position: str, orientation: str, angle_deg: float | None = None) -> float:
        if angle_deg is not None:
            return self._normalize_degrees(angle_deg)
        oriented = HARDSCAPE_ORIENTATION_ANGLES.get(orientation)
        if oriented is not None:
            return self._normalize_degrees(oriented)
        base = HARDSCAPE_POSITION_ANGLES.get(position, 0.0)
        if orientation == "scattered":
            base += 23.0
        elif orientation == "arch":
            base += 12.0
        return self._normalize_degrees(base)

    def _hardscape_tilt_deg(
        self,
        definition: HardscapeDefinition,
        orientation: str,
        tilt_deg: float | None = None,
    ) -> float:
        if tilt_deg is not None:
            if tilt_deg < -80.0 or tilt_deg > 80.0:
                raise ValueError("hardscape tilt must be between -80 and 80 degrees")
            return float(tilt_deg)
        if orientation == "upright":
            return max(50.0, definition.default_tilt_deg + 28.0)
        if orientation.startswith("leaning_"):
            return max(18.0, definition.default_tilt_deg)
        if orientation == "arch":
            return max(8.0, definition.default_tilt_deg * 0.6)
        return definition.default_tilt_deg

    def _umbrella_tilt_deg(self, orientation: str, tilt_deg: float | None = None) -> float:
        if tilt_deg is not None:
            if tilt_deg < -80.0 or tilt_deg > 80.0:
                raise ValueError("umbrella tilt must be between -80 and 80 degrees")
            return float(tilt_deg)
        if orientation == "upright":
            return 55.0
        if orientation.startswith("leaning_"):
            return UMBRELLA_DEFAULT_TILT_DEG
        if orientation == "arch":
            return 14.0
        return UMBRELLA_DEFAULT_TILT_DEG

    def _hardscape_effective_height_cm(self, definition: HardscapeDefinition, tilt_deg: float) -> float:
        tilt_lift = clamp(abs(tilt_deg) / 70.0, 0.0, 1.0) * 0.55
        return definition.height_cm * (1.0 + tilt_lift)

    def _hardscape_radius_cm(self, item: HardscapeItem) -> float:
        major, _ = self._hardscape_axes_cm(item)
        return major

    def _hardscape_core_radius_cm(self, item: HardscapeItem) -> float:
        major, _ = self._hardscape_axes_cm(item, core=True)
        return major

    def _hardscape_axes_cm(self, item: HardscapeItem, core: bool = False) -> tuple[float, float]:
        definition = HARDSCAPES[item.kind]
        footprint = self.state.container.base_area_cm2 * item.coverage_percent / 100.0
        aspect = max(1.0, definition.footprint_aspect_ratio)
        major = (footprint * aspect / math.pi) ** 0.5
        minor = (footprint / (aspect * math.pi)) ** 0.5
        if core:
            factor = HARDSCAPE_CORE_FACTORS.get(definition.category, 0.65)
            major *= factor
            minor *= factor
        return max(0.01, major), max(0.01, minor)

    def _hardscape_local_point_cm(self, item: HardscapeItem, x_percent: float, y_percent: float) -> tuple[float, float]:
        ix, iy = self._coord_to_cm(item.x_percent, item.y_percent)
        px, py = self._coord_to_cm(x_percent, y_percent)
        dx = px - ix
        dy = py - iy
        angle = math.radians(item.rotation_deg)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return dx * cos_a + dy * sin_a, -dx * sin_a + dy * cos_a

    def _hardscape_support_radius_cm(self, item: HardscapeItem, angle_deg: float, core: bool = False) -> float:
        major, minor = self._hardscape_axes_cm(item, core=core)
        local = math.radians(self._angle_delta_deg(item.rotation_deg, angle_deg))
        cos_a = math.cos(local)
        sin_a = math.sin(local)
        base = 1.0 / max(((cos_a / major) ** 2 + (sin_a / minor) ** 2) ** 0.5, 1e-9)
        return base * self._hardscape_irregular_factor(item, local, core=core)

    def _hardscape_irregular_factor(self, item: HardscapeItem, local_angle_rad: float, core: bool = False) -> float:
        definition = HARDSCAPES[item.kind]
        complexity = definition.surface_complexity * (0.42 if core else 1.0)
        if complexity <= 0.0:
            return 1.0
        seed = item.geometry_seed or self._stable_seed(item.item_id, item.kind)
        phase_a = self._stable_unit(seed, "a") * math.tau
        phase_b = self._stable_unit(seed, "b") * math.tau
        phase_c = self._stable_unit(seed, "c") * math.tau
        a = local_angle_rad
        profile = definition.geometry_profile
        if profile == "segmented_wood":
            long_axis = abs(math.cos(a))
            nodes = math.sin(4.0 * a + phase_a) * 0.65 + math.sin(7.0 * a + phase_b) * 0.30
            factor = 1.0 + complexity * (0.80 * long_axis + nodes)
        elif profile == "bark_ridge":
            factor = 1.0 + complexity * (0.55 * math.sin(3.0 * a + phase_a) + 0.35 * math.sin(8.0 * a + phase_b))
        elif profile == "shard":
            facet = 1.0 - abs(math.sin(3.0 * a + phase_a)) * 0.65
            factor = 1.0 + complexity * (facet + 0.32 * math.sin(5.0 * a + phase_b) - 0.22)
        elif profile == "porous_lobed":
            factor = 1.0 + complexity * (0.62 * math.sin(5.0 * a + phase_a) + 0.42 * math.sin(9.0 * a + phase_b))
        elif profile == "cluster":
            factor = 1.0 + complexity * (0.72 * math.sin(4.0 * a + phase_a) + 0.36 * math.sin(6.0 * a + phase_c))
        elif profile == "scattered_patch":
            factor = 1.0 + complexity * (0.35 * math.sin(6.0 * a + phase_a) + 0.55 * math.sin(11.0 * a + phase_b))
        elif profile == "smooth_oval":
            factor = 1.0 + complexity * 0.35 * math.sin(2.0 * a + phase_a)
        else:
            factor = 1.0 + complexity * 0.20 * math.sin(3.0 * a + phase_a)
        return clamp(factor, 0.72, 1.32)

    def _hardscape_normal_deg(self, item: HardscapeItem, x_percent: float, y_percent: float) -> float:
        lx, ly = self._hardscape_local_point_cm(item, x_percent, y_percent)
        major, minor = self._hardscape_axes_cm(item)
        nx = lx / (major * major)
        ny = ly / (minor * minor)
        if abs(nx) <= 1e-12 and abs(ny) <= 1e-12:
            nx, ny = 0.0, 1.0
        angle = math.radians(item.rotation_deg)
        wx = nx * math.cos(angle) - ny * math.sin(angle)
        wy = nx * math.sin(angle) + ny * math.cos(angle)
        return self._vector_angle_deg(wx, wy)

    def _hardscape_surface_at_xy(self, item: HardscapeItem, x_percent: float, y_percent: float) -> str | None:
        definition = HARDSCAPES[item.kind]
        lx, ly = self._hardscape_local_point_cm(item, x_percent, y_percent)
        major, minor = self._hardscape_axes_cm(item)
        local_angle = math.atan2(ly, lx)
        distance = math.hypot(lx, ly)
        world_angle = self._normalize_degrees(item.rotation_deg + math.degrees(local_angle))
        boundary = self._hardscape_support_radius_cm(item, world_angle)
        normalized_radius = distance / max(boundary, 1e-9)
        if normalized_radius > 1.0 + 1e-9:
            return None
        surfaces = set(definition.attach_surfaces)
        if "groove" in surfaces and abs(ly) / minor < 0.24 and 0.18 < abs(lx) / major < 0.88:
            return "groove"
        if "crack" in surfaces and 0.22 < normalized_radius < 0.72:
            waviness = math.sin((lx / major) * math.pi) * 0.18 * minor
            if abs(ly - waviness) < minor * 0.16:
                return "crack"
        if "side" in surfaces and normalized_radius > 0.73:
            return "side"
        if "top" in surfaces:
            return "top"
        return definition.attach_surfaces[0] if definition.attach_surfaces else None

    def _hardscape_surface_detail_at_xy(self, item: HardscapeItem, x_percent: float, y_percent: float) -> str:
        definition = HARDSCAPES[item.kind]
        if not definition.surface_features:
            return "plain surface"
        lx, ly = self._hardscape_local_point_cm(item, x_percent, y_percent)
        major, minor = self._hardscape_axes_cm(item)
        local_angle = math.atan2(ly, lx)
        normalized_x = abs(lx) / max(major, 1e-9)
        normalized_y = abs(ly) / max(minor, 1e-9)
        surface = self._hardscape_surface_at_xy(item, x_percent, y_percent) or "top"
        if surface == "groove":
            candidates = [feature for feature in definition.surface_features if "groove" in feature]
        elif surface == "crack":
            candidates = [feature for feature in definition.surface_features if "crack" in feature or "crevice" in feature]
        elif surface == "underside":
            candidates = [feature for feature in definition.surface_features if "under" in feature or "shelf" in feature]
        elif normalized_x > 0.72 or normalized_y > 0.72:
            candidates = [feature for feature in definition.surface_features if "edge" in feature or "side" in feature or "ridge" in feature]
        else:
            candidates = list(definition.surface_features)
        if not candidates:
            candidates = list(definition.surface_features)
        index = int(self._stable_unit(item.geometry_seed, round(local_angle, 2), surface) * len(candidates)) % len(candidates)
        return candidates[index]

    def _hardscape_surface_traits(self, item: HardscapeItem, surface: str) -> dict[str, float]:
        definition = HARDSCAPES[item.kind]
        surface_key = surface if surface in SURFACE_MICROCLIMATE_TRAITS else "top"
        traits = dict(SURFACE_MICROCLIMATE_TRAITS[surface_key])
        complexity = definition.surface_complexity
        porous = 1.0 if definition.geometry_profile in {"porous_lobed", "cluster", "scattered_patch"} else 0.0
        ridged = 1.0 if definition.geometry_profile in {"segmented_wood", "bark_ridge", "shard"} else 0.0

        traits["moisture"] += complexity * (0.20 + porous * 0.20 + ridged * 0.08)
        traits["shelter"] += complexity * (0.18 + ridged * 0.18)
        traits["biofilm"] += complexity * (0.16 + porous * 0.16)
        traits["mold"] += complexity * (0.12 + (0.16 if definition.category == "wood" else 0.0))
        traits["attachment"] += complexity * (0.22 if definition.category in {"stone", "wood"} else 0.08)
        if definition.category == "wood":
            traits["moisture"] += 0.035
            traits["mold"] += 0.055
            traits["attachment"] += 0.055
        elif definition.category == "stone":
            traits["biofilm"] += 0.035
        elif definition.category == "decor":
            traits["biofilm"] -= 0.020
            traits["mold"] -= 0.030
            traits["attachment"] -= 0.080

        return {
            "moisture": clamp(traits["moisture"], -0.10, 0.36),
            "shade": clamp(traits["shade"], 0.0, 0.42),
            "shelter": clamp(traits["shelter"], 0.0, 0.62),
            "aeration": clamp(traits["aeration"], -0.18, 0.18),
            "biofilm": clamp(traits["biofilm"], -0.04, 0.34),
            "mold": clamp(traits["mold"], -0.04, 0.36),
            "attachment": clamp(traits["attachment"], 0.25, 1.0),
        }

    def hardscape_surface_ecology(self) -> dict[str, float]:
        if not self.state.hardscape_items:
            return {"moisture": 0.0, "shelter": 0.0, "biofilm": 0.0, "mold": 0.0, "attachment": 0.0}
        totals = {"moisture": 0.0, "shelter": 0.0, "biofilm": 0.0, "mold": 0.0, "attachment": 0.0}
        weight_total = 0.0
        for item in self.state.hardscape_items:
            definition = HARDSCAPES[item.kind]
            for surface in definition.attach_surfaces:
                weight = item.coverage_percent * SURFACE_CAPACITY_FACTORS.get(surface, 0.45)
                if surface in {"crack", "groove", "underside"}:
                    weight *= 1.25
                traits = self._hardscape_surface_traits(item, surface)
                for key in totals:
                    totals[key] += traits[key] * weight
                weight_total += weight
        if weight_total <= 0.0:
            return totals
        return {key: totals[key] / weight_total for key in totals}

    def hardscape_contact_patch(
        self,
        item_id: str,
        surface: str = "top",
        x_percent: float | None = None,
        y_percent: float | None = None,
    ) -> dict[str, float | str]:
        item = self._find_hardscape_item(item_id)
        requested_surface = normalize_key(surface or "top")
        definition = HARDSCAPES[item.kind]
        if requested_surface not in definition.attach_surfaces:
            allowed = ", ".join(definition.attach_surfaces)
            raise ValueError(f"{item.item_id} has no {requested_surface} surface; available: {allowed}")
        if x_percent is None or y_percent is None:
            x, y = self._default_surface_xy(item, requested_surface)
        else:
            x, y = self._validate_xy(x_percent, y_percent)
        actual_surface = self._hardscape_surface_at_xy(item, x, y)
        if actual_surface is None:
            x, y = self._default_surface_xy(item, requested_surface)
            actual_surface = self._hardscape_surface_at_xy(item, x, y) or requested_surface
        if actual_surface not in definition.attach_surfaces:
            actual_surface = requested_surface

        height = max(0.0, item.z_top_cm - item.z_base_cm)
        if actual_surface == "top":
            z = item.z_top_cm
            normal = self._normalize_degrees(item.rotation_deg + 90.0)
            tangent = item.rotation_deg
            exposure = 0.88
        elif actual_surface == "underside":
            z = min(self.state.container.height_cm, item.z_base_cm + height * 0.15)
            normal = self._normalize_degrees(item.rotation_deg + 180.0)
            tangent = item.rotation_deg
            exposure = 0.22
        elif actual_surface == "groove":
            z = min(self.state.container.height_cm, item.z_base_cm + height * 0.62)
            normal = self._hardscape_normal_deg(item, x, y)
            tangent = item.rotation_deg
            exposure = 0.48
        elif actual_surface == "crack":
            z = min(self.state.container.height_cm, item.z_base_cm + height * 0.72)
            normal = self._hardscape_normal_deg(item, x, y)
            tangent = self._normalize_degrees(normal + 90.0)
            exposure = 0.42
        else:
            z = min(self.state.container.height_cm, item.z_base_cm + height * 0.55)
            normal = self._hardscape_normal_deg(item, x, y)
            tangent = self._normalize_degrees(normal + 90.0)
            exposure = 0.55

        surface_factor = SURFACE_CAPACITY_FACTORS.get(actual_surface, 0.5)
        local_area = self.state.container.base_area_cm2 * item.coverage_percent / 100.0
        contact_area = local_area * surface_factor * (0.08 if actual_surface in {"crack", "groove"} else 0.14)
        local_effects = self._local_hardscape_effects(x, y)
        traits = self._hardscape_surface_traits(item, actual_surface)
        return {
            "item_id": item.item_id,
            "surface": actual_surface,
            "feature": self._hardscape_surface_detail_at_xy(item, x, y),
            "x_percent": x,
            "y_percent": y,
            "z_cm": z,
            "normal_deg": normal,
            "tangent_deg": tangent,
            "contact_area_cm2": max(0.01, contact_area),
            "exposure": clamp(exposure),
            "shade": clamp(local_effects["shade"]),
            "edge_moisture": clamp(local_effects["edge_moisture"]),
            "moisture_bias": traits["moisture"],
            "shelter_bias": traits["shelter"],
            "aeration_bias": traits["aeration"],
            "biofilm_bias": traits["biofilm"],
            "mold_bias": traits["mold"],
            "attachment_support": traits["attachment"],
        }

    def _set_plant_attachment_patch(self, planting: Planting) -> None:
        if not planting.attached_to:
            planting.attachment_normal_deg = planting.yaw_deg
            planting.attachment_contact_area_cm2 = max(0.01, planting.footprint_cm2 * 0.45)
            return
        patch = self.hardscape_contact_patch(
            planting.attached_to,
            planting.attachment_surface or "top",
            planting.x_percent,
            planting.y_percent,
        )
        planting.attachment_surface = str(patch["surface"])
        planting.attachment_feature = str(patch["feature"])
        planting.z_cm = float(patch["z_cm"])
        planting.attachment_normal_deg = float(patch["normal_deg"])
        planting.attachment_contact_area_cm2 = min(planting.footprint_cm2, float(patch["contact_area_cm2"]))

    def _hardscape_silhouette_points(self, item: HardscapeItem, samples: int = 16) -> list[tuple[float, float, float]]:
        samples = max(8, samples)
        center_x, center_y = self._coord_to_cm(item.x_percent, item.y_percent)
        points: list[tuple[float, float, float]] = []
        for index in range(samples):
            angle = index / samples * 360.0
            radius = self._hardscape_support_radius_cm(item, angle)
            radians = math.radians(angle)
            x, y = self._cm_to_coord(center_x + math.cos(radians) * radius, center_y + math.sin(radians) * radius)
            points.append((x, y, item.z_base_cm))
        return points

    def _plant_silhouette_points(self, planting: Planting, samples: int = 12) -> list[tuple[float, float, float]]:
        samples = max(8, samples)
        center_x, center_y = self._coord_to_cm(planting.x_percent, planting.y_percent)
        points: list[tuple[float, float, float]] = []
        for index in range(samples):
            angle = index / samples * 360.0
            radius = self._plant_support_radius_cm(planting, angle)
            radians = math.radians(angle)
            x, y = self._cm_to_coord(center_x + math.cos(radians) * radius, center_y + math.sin(radians) * radius)
            points.append((x, y, planting.z_cm))
        return points

    def _project_scene_point(self, x_percent: float, y_percent: float, z_cm: float, view_angle_deg: float) -> tuple[float, float, float]:
        x_cm, y_cm = self._coord_to_cm(x_percent, y_percent)
        angle = math.radians(view_angle_deg)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        side = x_cm * cos_a + y_cm * sin_a
        depth = -x_cm * sin_a + y_cm * cos_a
        screen_y = depth * 0.34 - z_cm
        return side, screen_y, depth

    def pseudo3d_scene(self, view_angle_deg: float = 0.0) -> list[dict[str, Any]]:
        primitives: list[dict[str, Any]] = []

        for item in self.state.hardscape_items:
            definition = HARDSCAPES[item.kind]
            projected = [
                self._project_scene_point(x, y, z, view_angle_deg)
                for x, y, z in self._hardscape_silhouette_points(item, samples=18)
            ]
            top_projected = self._project_scene_point(item.x_percent, item.y_percent, item.z_top_cm, view_angle_deg)
            xs = [point[0] for point in projected]
            ys = [point[1] for point in projected] + [top_projected[1]]
            center = self._project_scene_point(item.x_percent, item.y_percent, item.z_top_cm, view_angle_deg)
            primitives.append(
                {
                    "id": item.item_id,
                    "type": "hardscape",
                    "kind": item.kind,
                    "label": definition.display_name,
                    "sprite_profile": definition.geometry_profile,
                    "x_percent": item.x_percent,
                    "y_percent": item.y_percent,
                    "z_base_cm": item.z_base_cm,
                    "z_top_cm": item.z_top_cm,
                    "screen_x": center[0],
                    "screen_y": center[1],
                    "depth_key": center[2] + item.z_top_cm * 0.18,
                    "bbox": (min(xs), min(ys), max(xs), max(ys)),
                    "rotation_deg": item.rotation_deg,
                    "tilt_deg": item.tilt_deg,
                    "surfaces": ",".join(definition.attach_surfaces),
                }
            )

        for planting in self.state.plantings:
            definition = PLANTS[planting.plant]
            projected = [
                self._project_scene_point(x, y, z, view_angle_deg)
                for x, y, z in self._plant_silhouette_points(planting, samples=12)
            ]
            top = self._project_scene_point(planting.x_percent, planting.y_percent, planting.z_cm + planting.height_cm, view_angle_deg)
            center = self._project_scene_point(planting.x_percent, planting.y_percent, planting.z_cm, view_angle_deg)
            xs = [point[0] for point in projected]
            ys = [point[1] for point in projected] + [top[1]]
            primitives.append(
                {
                    "id": planting.planting_id,
                    "type": "plant",
                    "kind": planting.plant,
                    "label": definition.display_name,
                    "sprite_profile": planting.shape_state,
                    "x_percent": planting.x_percent,
                    "y_percent": planting.y_percent,
                    "z_base_cm": planting.z_cm,
                    "z_top_cm": planting.z_cm + planting.height_cm,
                    "screen_x": center[0],
                    "screen_y": center[1],
                    "depth_key": center[2] + (planting.z_cm + planting.height_cm * 0.45) * 0.18,
                    "bbox": (min(xs), min(ys), max(xs), max(ys)),
                    "yaw_deg": planting.yaw_deg,
                    "pitch_deg": planting.pitch_deg,
                    "lean_deg": planting.lean_deg,
                    "surface": planting.attachment_surface or "ground",
                    "feature": planting.attachment_feature,
                }
            )

        for group in self.state.animal_groups:
            if group.count <= 0:
                continue
            definition = ANIMALS[group.animal]
            radius = self._animal_group_radius_cm(group, definition)
            center = self._project_scene_point(group.x_percent, group.y_percent, group.z_cm, view_angle_deg)
            primitives.append(
                {
                    "id": group.group_id,
                    "type": "animal",
                    "kind": group.animal,
                    "label": definition.display_name,
                    "sprite_profile": f"{definition.size_class}_{group.microhabitat.replace(' ', '_')}",
                    "x_percent": group.x_percent,
                    "y_percent": group.y_percent,
                    "z_base_cm": group.z_cm,
                    "z_top_cm": group.z_cm + 0.15,
                    "screen_x": center[0],
                    "screen_y": center[1],
                    "depth_key": center[2] + group.z_cm * 0.18,
                    "bbox": (center[0] - radius, center[1] - radius * 0.4, center[0] + radius, center[1] + radius * 0.4),
                    "movement": group.movement_state,
                    "habitat": group.microhabitat,
                }
            )

        primitives.sort(key=lambda item: (float(item["depth_key"]), float(item["z_base_cm"])))
        return primitives

    def _default_surface_xy(self, item: HardscapeItem, surface: str) -> tuple[float, float]:
        center_x, center_y = self._coord_to_cm(item.x_percent, item.y_percent)
        angle = item.rotation_deg
        amount = 0.0
        if surface == "side":
            angle = item.rotation_deg + 90.0
            amount = self._hardscape_support_radius_cm(item, angle) * 0.86
        elif surface in {"groove", "crack"}:
            angle = item.rotation_deg
            amount = self._hardscape_support_radius_cm(item, angle) * 0.35
        elif surface == "underside":
            angle = item.rotation_deg - 90.0
            amount = self._hardscape_support_radius_cm(item, angle) * 0.45
        radians = math.radians(angle)
        x, y = self._cm_to_coord(center_x + math.cos(radians) * amount, center_y + math.sin(radians) * amount)
        return self._validate_xy(x, y)

    def _plant_radius_cm(self, planting: Planting) -> float:
        major, _ = self._plant_axes_cm(planting)
        return major

    def _plant_axes_cm(self, planting: Planting) -> tuple[float, float]:
        area = planting.footprint_cm2 or self.state.container.base_area_cm2 * planting.area_percent / 100.0
        aspect = max(1.0, planting.footprint_aspect_ratio)
        major = (area * aspect / math.pi) ** 0.5
        minor = (area / (aspect * math.pi)) ** 0.5
        return max(0.01, major), max(0.01, minor)

    def _plant_support_radius_cm(self, planting: Planting, angle_deg: float) -> float:
        major, minor = self._plant_axes_cm(planting)
        local = math.radians(self._angle_delta_deg(planting.spread_direction_deg, angle_deg))
        cos_a = math.cos(local)
        sin_a = math.sin(local)
        return 1.0 / max(((cos_a / major) ** 2 + (sin_a / minor) ** 2) ** 0.5, 1e-9)

    def _plant_overlap_fraction(self, left: Planting, right: Planting, distance: float) -> float:
        angle = self._bearing_between_coords(left.x_percent, left.y_percent, right.x_percent, right.y_percent)
        left_radius = self._plant_support_radius_cm(left, angle)
        right_radius = self._plant_support_radius_cm(right, self._normalize_degrees(angle + 180.0))
        return self._circle_overlap_fraction(left_radius, right_radius, distance)

    def _plant_hardscape_overlap_fraction(self, planting: Planting, item: HardscapeItem, distance: float, core: bool = True) -> float:
        angle_from_item = self._bearing_between_coords(item.x_percent, item.y_percent, planting.x_percent, planting.y_percent)
        plant_angle = self._normalize_degrees(angle_from_item + 180.0)
        plant_radius = self._plant_support_radius_cm(planting, plant_angle)
        hardscape_radius = self._hardscape_support_radius_cm(item, angle_from_item, core=core)
        return self._circle_overlap_fraction(plant_radius, hardscape_radius, distance)

    def _animal_activity_area(self, definition: AnimalDefinition, count: int) -> float:
        return max(definition.minimum_activity_area_cm2, count * definition.activity_area_cm2_per_count)

    def _animal_group_activity_area(self, group: AnimalGroup, definition: AnimalDefinition | None = None) -> float:
        definition = ANIMALS[group.animal] if definition is None else definition
        return max(group.activity_area_cm2, self._animal_activity_area(definition, group.count))

    def _animal_group_radius_cm(self, group: AnimalGroup, definition: AnimalDefinition | None = None) -> float:
        definition = ANIMALS[group.animal] if definition is None else definition
        area = self._animal_group_activity_area(group, definition)
        return (area / math.pi) ** 0.5 + definition.movement_range_cm * 0.35

    def _distance_cm(self, ax: float, ay: float, bx: float, by: float) -> float:
        acx, acy = self._coord_to_cm(ax, ay)
        bcx, bcy = self._coord_to_cm(bx, by)
        return math.hypot(acx - bcx, acy - bcy)

    def _placement_candidates(self, preferred: tuple[float, float]) -> list[tuple[float, float]]:
        candidates = [preferred, (50.0, 50.0)]
        for radius in (18.0, 28.0, 38.0, 46.0):
            for angle in (0, 45, 90, 135, 180, 225, 270, 315):
                radians = math.radians(angle)
                candidates.append((50.0 + math.cos(radians) * radius, 50.0 + math.sin(radians) * radius))
        candidates.extend(
            [
                (24.0, 50.0),
                (76.0, 50.0),
                (50.0, 24.0),
                (50.0, 76.0),
                (30.0, 30.0),
                (70.0, 30.0),
                (30.0, 70.0),
                (70.0, 70.0),
            ]
        )
        deduped: list[tuple[float, float]] = []
        seen: set[tuple[int, int]] = set()
        for x, y in candidates:
            key = (round(x), round(y))
            if key in seen:
                continue
            seen.add(key)
            deduped.append((x, y))
        return deduped

    def _circle_overlap_area(self, radius_a: float, radius_b: float, distance: float) -> float:
        if radius_a <= 0.0 or radius_b <= 0.0:
            return 0.0
        if distance >= radius_a + radius_b:
            return 0.0
        if distance <= abs(radius_a - radius_b):
            return math.pi * min(radius_a, radius_b) ** 2
        a2 = radius_a * radius_a
        b2 = radius_b * radius_b
        alpha = math.acos(clamp((distance * distance + a2 - b2) / (2.0 * distance * radius_a), -1.0, 1.0))
        beta = math.acos(clamp((distance * distance + b2 - a2) / (2.0 * distance * radius_b), -1.0, 1.0))
        term = max(0.0, (-distance + radius_a + radius_b) * (distance + radius_a - radius_b) * (distance - radius_a + radius_b) * (distance + radius_a + radius_b))
        return a2 * alpha + b2 * beta - 0.5 * term ** 0.5

    def _circle_overlap_fraction(self, radius_a: float, radius_b: float, distance: float) -> float:
        overlap = self._circle_overlap_area(radius_a, radius_b, distance)
        smaller = math.pi * min(radius_a, radius_b) ** 2
        if smaller <= 0.0:
            return 0.0
        return overlap / smaller

    def _umbrella_overlap_fraction(self) -> float:
        s = self.state
        if not s.umbrella_enabled:
            return 0.0
        bottle_radius = (s.container.base_area_cm2 / math.pi) ** 0.5
        canopy_radius = bottle_radius * (clamp(s.umbrella_coverage_percent / 100.0, 0.01, 3.0) ** 0.5)
        x_cm, y_cm = self._coord_to_cm(s.umbrella_x_percent, s.umbrella_y_percent)
        overlap = self._circle_overlap_area(bottle_radius, canopy_radius, math.hypot(x_cm, y_cm))
        bottle_area = math.pi * bottle_radius * bottle_radius
        if bottle_area <= 0.0:
            return 0.0
        return clamp(overlap / bottle_area)

    def _umbrella_light_filter(self, direct_azimuth: float) -> dict[str, float]:
        s = self.state
        overlap = self._umbrella_overlap_fraction()
        if overlap <= 0.0:
            return {"direct": 1.0, "diffuse": 1.0, "scatter": 0.0, "shade": 0.0}
        area_signal = clamp((s.umbrella_coverage_percent - 100.0) / 80.0)
        tilt_signal = clamp(abs(s.umbrella_tilt_deg) / 45.0)
        alignment = max(0.0, math.cos(math.radians(self._angle_delta_deg(s.umbrella_angle_deg, direct_azimuth))))
        directional = 0.75 + 0.25 * (alignment * tilt_signal + (1.0 - tilt_signal) * 0.65)
        shade = clamp(overlap * (0.55 + area_signal * 0.24) * directional)
        return {
            "direct": 1.0 - min(0.82, shade),
            "diffuse": 1.0 - min(0.34, shade * 0.35),
            "scatter": min(0.18, shade * 0.16),
            "shade": shade,
        }

    def _vertical_intervals_overlap(self, a_low: float, a_high: float, b_low: float, b_high: float) -> bool:
        return min(a_high, b_high) > max(a_low, b_low)

    def _choose_hardscape_xy(
        self,
        position: str,
        orientation: str,
        definition: HardscapeDefinition,
        coverage_percent: float,
        rotation_deg: float,
        tilt_deg: float,
    ) -> tuple[float, float]:
        preferred = POSITION_COORDINATES[position]
        candidates = self._placement_candidates(preferred)
        seen: set[tuple[float, float]] = set()
        for x, y in candidates:
            key = (x, y)
            if key in seen:
                continue
            seen.add(key)
            try:
                x, y = self._validate_xy(x, y)
            except ValueError:
                continue
            z_base = self.substrate_surface_height_cm(x, y)
            probe = HardscapeItem(
                item_id="_probe",
                kind=definition.key,
                coverage_percent=coverage_percent,
                position=position,
                orientation=orientation,
                rotation_deg=rotation_deg,
                tilt_deg=tilt_deg,
                x_percent=x,
                y_percent=y,
                z_base_cm=z_base,
                z_top_cm=min(self.state.container.height_cm, z_base + self._hardscape_effective_height_cm(definition, tilt_deg)),
                geometry_seed=self._stable_seed("_probe", definition.key, x, y),
            )
            try:
                self._raise_if_hardscape_collision(probe)
            except ValueError:
                continue
            return x, y
        raise ValueError("no clear hardscape placement space remains; use explicit x= y= coordinates or pick another item")

    def _raise_if_hardscape_collision(self, item: HardscapeItem) -> None:
        definition = HARDSCAPES[item.kind]
        for other in self.state.hardscape_items:
            distance = self._distance_cm(item.x_percent, item.y_percent, other.x_percent, other.y_percent)
            item_angle = self._bearing_between_coords(item.x_percent, item.y_percent, other.x_percent, other.y_percent)
            other_angle = self._normalize_degrees(item_angle + 180.0)
            item_core = self._hardscape_support_radius_cm(item, item_angle, core=True)
            other_core = self._hardscape_support_radius_cm(other, other_angle, core=True)
            if distance < item_core + other_core - 1e-9:
                raise ValueError(f"hardscape collision with {other.item_id}; move it or choose a smaller piece")

        for planting in self.state.plantings:
            if planting.status == "dead":
                continue
            distance = self._distance_cm(item.x_percent, item.y_percent, planting.x_percent, planting.y_percent)
            item_angle = self._bearing_between_coords(item.x_percent, item.y_percent, planting.x_percent, planting.y_percent)
            item_radius = self._hardscape_support_radius_cm(item, item_angle)
            plant_radius = self._plant_support_radius_cm(planting, self._normalize_degrees(item_angle + 180.0))
            overlap = self._circle_overlap_fraction(item_radius, plant_radius, distance)
            if overlap <= 0.18:
                continue
            plant_low, plant_high = self._plant_canopy_interval_cm(planting)
            if self._vertical_intervals_overlap(item.z_base_cm, item.z_top_cm, plant_low, plant_high):
                raise ValueError(f"hardscape collision with planting {planting.planting_id}")

    def _hardscape_contains_xy(self, item: HardscapeItem, x_percent: float, y_percent: float) -> bool:
        lx, ly = self._hardscape_local_point_cm(item, x_percent, y_percent)
        local_angle = math.atan2(ly, lx)
        distance = math.hypot(lx, ly)
        world_angle = self._normalize_degrees(item.rotation_deg + math.degrees(local_angle))
        return distance <= self._hardscape_support_radius_cm(item, world_angle) + 1e-9

    def _hardscape_at_xy(self, x_percent: float, y_percent: float) -> HardscapeItem | None:
        matches = [item for item in self.state.hardscape_items if self._hardscape_contains_xy(item, x_percent, y_percent)]
        if not matches:
            return None
        return max(matches, key=lambda item: item.z_top_cm)

    def _plant_can_attach_to_hardscape(self, definition: PlantDefinition) -> bool:
        return definition.category in {"moss", "lichen", "epiphytic_fern", "bromeliad_air", "orchid_mini"}

    def _set_initial_plant_orientation(self, planting: Planting) -> None:
        definition = PLANTS[planting.plant]
        if planting.attached_to:
            self._orient_plant_to_hardscape(planting, definition, immediate=True)
            return
        planting.yaw_deg = self._normalize_degrees(self.state.sun_azimuth_deg)
        planting.pitch_deg = 90.0 if definition.category not in {"moss", "lichen"} else 12.0
        planting.lean_deg = 0.0
        planting.lean_reason = "upright" if planting.pitch_deg >= 60.0 else "surface_mat"

    def _base_plant_shape(self, definition: PlantDefinition) -> tuple[float, str]:
        if definition.category in {"moss", "lichen"}:
            return (1.9, "surface_mat")
        if definition.category == "creeper":
            return (2.2, "runner")
        if definition.category == "fittonia":
            return (1.45, "creeping_clump")
        if definition.category in {"epiphytic_fern", "orchid_mini"}:
            return (1.55, "fan")
        if definition.category in {"bromeliad_air", "bromeliad_tank", "carnivorous"}:
            return (1.12, "rosette")
        if definition.category == "terrestrial_fern":
            return (1.35, "clump")
        return (1.0, "round")

    def _set_initial_plant_shape(self, planting: Planting) -> None:
        definition = PLANTS[planting.plant]
        aspect, shape = self._base_plant_shape(definition)
        if planting.attached_to:
            aspect, shape, direction = self._mounted_plant_shape(planting, definition, aspect, shape)
        else:
            direction = planting.yaw_deg
        planting.footprint_aspect_ratio = aspect
        planting.spread_direction_deg = self._normalize_degrees(direction)
        planting.shape_state = shape

    def _set_initial_plant_structure(self, planting: Planting) -> None:
        definition = PLANTS[planting.plant]
        scale = max(1.0, planting.area_percent / max(definition.default_area_percent, 1.0))
        jitter = self._stable_unit(planting.planting_id, planting.plant)
        category = definition.category
        if category in {"moss", "lichen"}:
            planting.stem_count = max(1, int(round(8 * scale + jitter * 6)))
            planting.leaf_count = 0
            planting.root_anchor_count = 0
            planting.new_growth_count = max(1, int(round(planting.stem_count * 0.18)))
            planting.root_tip_count = 0
        elif category in {"fittonia", "creeper"}:
            planting.stem_count = max(1, int(round(2 * scale + jitter * 2)))
            planting.leaf_count = max(2, int(round(planting.stem_count * (4 + jitter * 4))))
            planting.root_anchor_count = max(1, int(round(planting.stem_count * (1.2 + scale * 0.3))))
            planting.new_growth_count = max(1, planting.stem_count)
            planting.root_tip_count = max(1, planting.root_anchor_count * 2)
        elif category in {"terrestrial_fern", "epiphytic_fern"}:
            planting.stem_count = 1
            planting.leaf_count = max(3, int(round(4 * scale + jitter * 4)))
            planting.root_anchor_count = max(1, int(round(2 + scale * 1.5)))
            planting.new_growth_count = 1
            planting.root_tip_count = max(2, planting.root_anchor_count * 2)
        elif category in {"bromeliad_air", "bromeliad_tank", "carnivorous"}:
            planting.stem_count = 1
            planting.leaf_count = max(5, int(round(7 * scale + jitter * 5)))
            planting.root_anchor_count = 1 if category == "carnivorous" else max(0, int(round(1 + jitter * 2)))
            planting.new_growth_count = 1
            planting.root_tip_count = max(0, planting.root_anchor_count * 2)
        elif category == "orchid_mini":
            planting.stem_count = max(1, int(round(1 + jitter * 2)))
            planting.leaf_count = max(3, int(round(4 * scale + jitter * 5)))
            planting.root_anchor_count = max(2, int(round(3 * scale + jitter * 4)))
            planting.new_growth_count = max(1, planting.stem_count)
            planting.root_tip_count = max(2, planting.root_anchor_count * 2)
        else:
            planting.stem_count = 1
            planting.leaf_count = max(2, int(round(3 * scale + jitter * 3)))
            planting.root_anchor_count = max(1, int(round(scale)))
            planting.new_growth_count = 1
            planting.root_tip_count = max(1, planting.root_anchor_count)
        planting.damaged_leaf_count = 0
        planting.flower_count = 0
        self._refresh_plant_canopy_density(planting)

    def _advance_plant_structure(self, planting: Planting, definition: PlantDefinition, suitability: float) -> None:
        if planting.status == "dead" or planting.health <= 0.0:
            return
        grow_signal = planting.growth_rate * suitability
        if grow_signal > 0.004 and planting.age_ticks % 24 == 0:
            if definition.category in {"moss", "lichen"}:
                planting.stem_count += 1
                planting.new_growth_count += 1
            elif definition.category in {"fittonia", "creeper"}:
                if self._stable_unit(planting.planting_id, planting.age_ticks, "stem") > 0.62:
                    planting.stem_count += 1
                    planting.new_growth_count += 1
                leaves = max(1, int(round(planting.stem_count * 0.35)))
                planting.leaf_count += leaves
                planting.new_growth_count += max(1, leaves // 2)
            elif definition.category in {"terrestrial_fern", "epiphytic_fern"}:
                planting.leaf_count += 1
                planting.new_growth_count += 1
            elif definition.category in {"orchid_mini", "bromeliad_air", "bromeliad_tank", "carnivorous"}:
                if self._stable_unit(planting.planting_id, planting.age_ticks, "leaf") > 0.44:
                    planting.leaf_count += 1
                    planting.new_growth_count += 1
            else:
                planting.leaf_count += 1
                planting.new_growth_count += 1
        if planting.attached_to and planting.root_health > 64.0 and planting.age_ticks % 72 == 0:
            planting.root_anchor_count += 1
            planting.root_tip_count += 2
        elif not planting.attached_to and planting.root_health > 70.0 and definition.root_depth_cm > 0 and planting.age_ticks % 96 == 0:
            planting.root_tip_count += 1
        if planting.visible_damage_percent > 35.0 and planting.leaf_count > 0 and planting.age_ticks % 48 == 0:
            planting.leaf_count = max(0, planting.leaf_count - 1)
            planting.damaged_leaf_count += 1
        if planting.mold_contact_percent > 30.0 and planting.leaf_count > 0 and planting.age_ticks % 72 == 0:
            planting.damaged_leaf_count += 1
            planting.new_growth_count = max(0, planting.new_growth_count - 1)
        if self._plant_can_show_flower(definition, planting, suitability):
            planting.flower_count = max(planting.flower_count, 1)
        elif planting.health < 55.0 or suitability < 0.42:
            planting.flower_count = max(0, planting.flower_count - 1)
        planting.new_growth_count = max(0, int(round(planting.new_growth_count * 0.985)))
        if planting.damaged_leaf_count > 0 and planting.health > 72.0 and planting.age_ticks % 120 == 0:
            planting.damaged_leaf_count -= 1
        planting.visible_damage_percent = max(0.0, planting.visible_damage_percent - 0.015)
        planting.mold_contact_percent = max(0.0, planting.mold_contact_percent - 0.010)
        self._refresh_plant_canopy_density(planting)

    def _plant_can_show_flower(self, definition: PlantDefinition, planting: Planting, suitability: float) -> bool:
        if definition.category not in {"orchid_mini", "carnivorous", "bromeliad_tank", "bromeliad_air"}:
            return False
        if planting.age_ticks < definition.min_reproductive_age_ticks:
            return False
        if planting.health < 82.0 or suitability < 0.72:
            return False
        return self._stable_unit(planting.planting_id, planting.age_ticks // 168, "flower") > 0.58

    def _refresh_plant_canopy_density(self, planting: Planting) -> None:
        definition = PLANTS[planting.plant]
        if definition.category in {"moss", "lichen"}:
            density = 35.0 + planting.stem_count * 2.4
        else:
            density = 18.0 + planting.leaf_count * 3.1 + planting.stem_count * 4.0
        density -= planting.damaged_leaf_count * 5.0
        density -= planting.visible_damage_percent * 0.20
        density -= planting.mold_contact_percent * 0.16
        density *= clamp(planting.health / 100.0, 0.10, 1.0)
        planting.canopy_density_percent = clamp(density, 0.0, 100.0)

    def _mounted_plant_shape(
        self,
        planting: Planting,
        definition: PlantDefinition,
        base_aspect: float,
        base_shape: str,
    ) -> tuple[float, str, float]:
        try:
            item = self._find_hardscape_item(planting.attached_to)
        except ValueError:
            return base_aspect, base_shape, planting.yaw_deg
        surface = planting.attachment_surface or "top"
        direction = planting.yaw_deg
        aspect = base_aspect
        shape = base_shape
        if surface == "groove":
            direction = item.rotation_deg
            aspect = max(aspect, 2.8)
            shape = "tracking_groove"
        elif surface == "crack":
            direction = self._hardscape_normal_deg(item, planting.x_percent, planting.y_percent)
            aspect = max(aspect, 2.2)
            shape = "rooted_line"
        elif surface == "side":
            direction = item.rotation_deg
            aspect = max(aspect, 1.9)
            shape = "wall_hugging"
        elif surface == "underside":
            direction = item.rotation_deg
            aspect = max(aspect, 1.6)
            shape = "underside_patch"
        elif definition.category in {"moss", "lichen"}:
            direction = item.rotation_deg
            aspect = max(aspect, 1.7)
            shape = "attached_mat"
        return aspect, shape, direction

    def _advance_plant_shape(self, planting: Planting, definition: PlantDefinition, env: dict[str, float]) -> None:
        base_aspect, base_shape = self._base_plant_shape(definition)
        if planting.attached_to:
            target_aspect, target_shape, target_direction = self._mounted_plant_shape(planting, definition, base_aspect, base_shape)
        else:
            target_aspect = base_aspect
            target_shape = base_shape
            target_direction = planting.yaw_deg
            if definition.category in {"creeper", "fittonia"} and env.get("light", 0.0) > 0.02:
                target_aspect += min(0.55, planting.lean_deg / 45.0)
                target_direction = planting.yaw_deg
                target_shape = "light-reaching"
            if planting.lean_reason.startswith("pressed_by"):
                target_aspect += 0.45
                target_shape = "pressed_aside"
        maturity = clamp(planting.footprint_cm2 / max(planting.initial_footprint_cm2, 1e-9) - 1.0)
        target_aspect = clamp(target_aspect + maturity * 0.35, 1.0, 4.5)
        planting.footprint_aspect_ratio += (target_aspect - planting.footprint_aspect_ratio) * 0.18
        planting.spread_direction_deg = self._turn_toward_angle(planting.spread_direction_deg, target_direction, 0.16)
        planting.shape_state = target_shape

    def _orient_plant_to_hardscape(
        self,
        planting: Planting,
        definition: PlantDefinition,
        immediate: bool = False,
    ) -> None:
        try:
            item = self._find_hardscape_item(planting.attached_to)
        except ValueError:
            return
        surface = planting.attachment_surface or "top"
        target_yaw = self._hardscape_normal_deg(item, planting.x_percent, planting.y_percent)
        if surface == "top":
            target_pitch = 18.0 if definition.category in {"moss", "lichen"} else max(62.0, 90.0 - abs(item.tilt_deg) * 0.35)
            target_lean = min(18.0, abs(item.tilt_deg) * 0.35)
            reason = "settled_on_top"
        elif surface == "side":
            target_pitch = 9.0 if definition.category in {"moss", "lichen"} else 34.0
            target_lean = 24.0
            reason = "attached_side"
        elif surface == "groove":
            target_yaw = item.rotation_deg
            target_pitch = 7.0 if definition.category in {"moss", "lichen"} else 26.0
            target_lean = 18.0
            reason = "following_groove"
        elif surface == "crack":
            target_yaw = self._hardscape_normal_deg(item, planting.x_percent, planting.y_percent)
            target_pitch = 12.0 if definition.category in {"moss", "lichen"} else 38.0
            target_lean = 16.0
            reason = "rooted_in_crack"
        elif surface == "underside":
            target_yaw = item.rotation_deg
            target_pitch = -20.0 if definition.category not in {"moss", "lichen"} else -6.0
            target_lean = 32.0
            reason = "under_overhang"
        else:
            target_pitch = 80.0
            target_lean = 0.0
            reason = "attached"
        if immediate:
            planting.yaw_deg = self._normalize_degrees(target_yaw)
            planting.pitch_deg = target_pitch
            planting.lean_deg = target_lean
        else:
            planting.yaw_deg = self._turn_toward_angle(planting.yaw_deg, target_yaw, 0.22)
            planting.pitch_deg += (target_pitch - planting.pitch_deg) * 0.18
            planting.lean_deg += (target_lean - planting.lean_deg) * 0.16
        planting.lean_reason = reason

    def _advance_plant_orientation(self, planting: Planting, definition: PlantDefinition, env: dict[str, float]) -> None:
        if planting.status == "dead" or planting.health <= 0.0:
            return
        if planting.attached_to:
            self._orient_plant_to_hardscape(planting, definition)
            return
        nearest: tuple[float, HardscapeItem, float] | None = None
        radius = self._plant_radius_cm(planting)
        for item in self.state.hardscape_items:
            distance = self._distance_cm(planting.x_percent, planting.y_percent, item.x_percent, item.y_percent)
            angle = self._bearing_between_coords(item.x_percent, item.y_percent, planting.x_percent, planting.y_percent)
            support = self._hardscape_support_radius_cm(item, angle)
            clearance = distance - support - radius * 0.55
            if nearest is None or clearance < nearest[0]:
                nearest = (clearance, item, angle)
        if nearest is not None and nearest[0] < 0.9:
            _, item, away_angle = nearest
            planting.yaw_deg = self._turn_toward_angle(planting.yaw_deg, away_angle, 0.18)
            planting.lean_deg = clamp(planting.lean_deg + (min(28.0, 8.0 + (0.9 - nearest[0]) * 8.0) - planting.lean_deg) * 0.20, 0.0, 45.0)
            planting.pitch_deg = max(55.0, planting.pitch_deg - 1.2)
            planting.lean_reason = f"pressed_by_{item.item_id}"
            return
        if env.get("light", 0.0) > 0.02 and self.state.sun_altitude_deg > 0.0:
            light_need_mid = sum(definition.light_range) / 2.0
            light_gap = max(0.0, light_need_mid - env["light"])
            target_lean = clamp(4.0 + light_gap * 16.0 + self.state.light * 5.0, 0.0, 22.0)
            planting.yaw_deg = self._turn_toward_angle(planting.yaw_deg, self.state.sun_azimuth_deg, 0.10)
            planting.lean_deg += (target_lean - planting.lean_deg) * 0.10
            planting.pitch_deg += (90.0 - planting.pitch_deg) * 0.08
            planting.lean_reason = "toward_light"
        else:
            planting.lean_deg += (0.0 - planting.lean_deg) * 0.06
            planting.pitch_deg += (90.0 - planting.pitch_deg) * 0.04
            planting.lean_reason = "resting"

    def _choose_planting_xy(self, planting: Planting) -> None:
        for x, y in self._placement_candidates((planting.x_percent, planting.y_percent)):
            try:
                x, y = self._validate_xy(x, y)
            except ValueError:
                continue
            old_x, old_y, old_z = planting.x_percent, planting.y_percent, planting.z_cm
            planting.x_percent = x
            planting.y_percent = y
            planting.z_cm = self._planting_z_cm(planting.site, x, y)
            try:
                self._raise_if_plant_collision(planting)
            except ValueError:
                planting.x_percent, planting.y_percent, planting.z_cm = old_x, old_y, old_z
                continue
            return
        raise ValueError("no clear planting space remains; use explicit x= y= coordinates or remove nearby objects")

    def _plant_canopy_interval_cm(self, planting: Planting) -> tuple[float, float]:
        return planting.z_cm, planting.z_cm + max(0.1, planting.height_cm)

    def _plant_root_interval_cm(self, planting: Planting) -> tuple[float, float]:
        if planting.root_length_cm <= 0:
            return planting.z_cm, planting.z_cm
        return max(0.0, planting.z_cm - planting.root_length_cm), planting.z_cm

    def _allowed_plant_overlap(self, left: Planting, right: Planting) -> float:
        left_def = PLANTS[left.plant]
        right_def = PLANTS[right.plant]
        left_soft = left_def.category in {"moss", "lichen"}
        right_soft = right_def.category in {"moss", "lichen"}
        if left_soft and right_soft:
            return 0.75
        if left_soft or right_soft:
            return 0.55
        if left.attached_to and left.attached_to == right.attached_to:
            return 0.30
        if left_def.category == "creeper" or right_def.category == "creeper":
            return 0.35
        return 0.22

    def _raise_if_plant_collision(self, planting: Planting) -> None:
        definition = PLANTS[planting.plant]
        radius = self._plant_radius_cm(planting)
        if not planting.attached_to and definition.root_depth_cm > 0:
            for item in self.state.hardscape_items:
                distance = self._distance_cm(planting.x_percent, planting.y_percent, item.x_percent, item.y_percent)
                overlap = self._plant_hardscape_overlap_fraction(planting, item, distance, core=True)
                if overlap > 0.10:
                    raise ValueError(f"root zone collides with hardscape {item.item_id}; move the planting or use a hardscape-tolerant plant")

        for other in self.state.plantings:
            if other.status == "dead":
                continue
            distance = self._distance_cm(planting.x_percent, planting.y_percent, other.x_percent, other.y_percent)
            overlap = self._plant_overlap_fraction(planting, other, distance)
            if overlap <= 0.0:
                continue

            allowed = self._allowed_plant_overlap(planting, other)
            if overlap > allowed and self._vertical_intervals_overlap(*self._plant_canopy_interval_cm(planting), *self._plant_canopy_interval_cm(other)):
                raise ValueError(f"planting overlaps {other.planting_id} too much; choose another coordinate or a smaller area")

            if (
                not planting.attached_to
                and not other.attached_to
                and planting.root_length_cm > 0
                and other.root_length_cm > 0
                and overlap > min(0.35, allowed + 0.10)
                and self._vertical_intervals_overlap(*self._plant_root_interval_cm(planting), *self._plant_root_interval_cm(other))
            ):
                raise ValueError(f"root zone overlaps {other.planting_id} too much; choose another coordinate")

    def _raise_if_plant_growth_collision(self, planting: Planting) -> None:
        definition = PLANTS[planting.plant]
        radius = self._plant_radius_cm(planting)
        if not planting.attached_to and definition.root_depth_cm > 0:
            for item in self.state.hardscape_items:
                distance = self._distance_cm(planting.x_percent, planting.y_percent, item.x_percent, item.y_percent)
                overlap = self._plant_hardscape_overlap_fraction(planting, item, distance, core=True)
                if overlap > 0.18:
                    raise ValueError("growing root zone collides with hardscape")

        for other in self.state.plantings:
            if other is planting or other.status == "dead":
                continue
            distance = self._distance_cm(planting.x_percent, planting.y_percent, other.x_percent, other.y_percent)
            overlap = self._plant_overlap_fraction(planting, other, distance)
            if overlap <= 0.0:
                continue
            allowed = self._allowed_plant_overlap(planting, other) + 0.15
            if overlap > allowed and self._vertical_intervals_overlap(*self._plant_canopy_interval_cm(planting), *self._plant_canopy_interval_cm(other)):
                raise ValueError("growing canopy overlaps another planting")

    def _resolve_planting_xy(
        self,
        site: str,
        x_percent: float | None,
        y_percent: float | None,
    ) -> tuple[float, float]:
        if x_percent is not None or y_percent is not None:
            return self._validate_xy(50.0 if x_percent is None else x_percent, 50.0 if y_percent is None else y_percent)

        normalized = normalize_key(site)
        if site.lower().startswith("hardscape:"):
            target_id, surface = self._parse_hardscape_reference(site)
            item = self._find_hardscape_item(target_id)
            return self._default_surface_xy(item, surface)
        if normalized.startswith("hardscape_"):
            target_id, surface = self._parse_hardscape_reference(site)
            item = self._find_hardscape_item(target_id)
            return self._default_surface_xy(item, surface)
        if normalized.startswith("h") and (normalized[1:].isdigit() or "_" in normalized or ":" in site):
            target_id, surface = self._parse_hardscape_reference(site)
            item = self._find_hardscape_item(target_id)
            return self._default_surface_xy(item, surface)
        return 50.0, 50.0

    def _resolve_planting_site(
        self,
        plant_key: str,
        site: str,
        x_percent: float,
        y_percent: float,
        auto_attach: bool,
    ) -> str:
        normalized_site = self._normalize_planting_site(site)
        definition = PLANTS[plant_key]
        if auto_attach and normalized_site in {"surface", "soil", "substrate"} and self._plant_can_attach_to_hardscape(definition):
            item = self._hardscape_at_xy(x_percent, y_percent)
            if item is not None:
                surface = self._hardscape_surface_at_xy(item, x_percent, y_percent) or "top"
                return self._hardscape_site(item.item_id, surface)
        return normalized_site

    def _sample_plant_dimensions(self, definition: PlantDefinition, area_percent: float) -> tuple[float, float, float]:
        footprint = self.state.container.base_area_cm2 * area_percent / 100.0
        height_min = max(0.1, definition.height_cm * 0.72)
        height_max = max(height_min, definition.height_cm * 1.18)
        height = self._random.uniform(height_min, height_max)
        if definition.root_depth_cm <= 0:
            root_length = 0.0
        else:
            root_min = max(0.1, definition.root_depth_cm * 0.68)
            root_max = max(root_min, definition.root_depth_cm * 1.22)
            root_length = self._random.uniform(root_min, root_max)
        return footprint, height, root_length

    def _planting_z_cm(self, site: str, x_percent: float, y_percent: float) -> float:
        if site.startswith("hardscape:"):
            target_id, surface = self._parse_hardscape_site(site)
            item = self._find_hardscape_item(target_id)
            height = max(0.0, item.z_top_cm - item.z_base_cm)
            if surface == "top":
                return item.z_top_cm
            if surface == "underside":
                return min(self.state.container.height_cm, item.z_base_cm + height * 0.15)
            if surface == "side":
                return min(self.state.container.height_cm, item.z_base_cm + height * 0.55)
            if surface == "groove":
                return min(self.state.container.height_cm, item.z_base_cm + height * 0.62)
            if surface == "crack":
                return min(self.state.container.height_cm, item.z_base_cm + height * 0.72)
            return item.z_top_cm
        if site == "air":
            return min(self.state.container.height_cm, self.substrate_surface_height_cm(x_percent, y_percent) + 2.0)
        if site == "water":
            return 0.0
        return self.substrate_surface_height_cm(x_percent, y_percent)

    def _normalize_planting_site(self, site: str) -> str:
        raw = site.strip()
        normalized = normalize_key(raw)
        if normalized in PLANTING_SITES:
            return normalized

        if normalized.startswith("hardscape_"):
            target_id, surface = self._parse_hardscape_reference(raw)
            return self._hardscape_site(target_id, surface)
        if raw.lower().startswith("hardscape:"):
            target_id, surface = self._parse_hardscape_reference(raw)
            return self._hardscape_site(target_id, surface)
        if normalized.startswith("h") and (normalized[1:].isdigit() or "_" in normalized or ":" in raw):
            target_id, surface = self._parse_hardscape_reference(raw)
            return self._hardscape_site(target_id, surface)

        allowed = ", ".join(PLANTING_SITES)
        raise ValueError(f"unknown planting site '{site}', expected one of: {allowed}, hardscape:<id>[:surface]")

    def _resolve_animal_xy(
        self,
        site: str,
        x_percent: float | None,
        y_percent: float | None,
    ) -> tuple[float, float]:
        if x_percent is not None or y_percent is not None:
            return self._validate_xy(50.0 if x_percent is None else x_percent, 50.0 if y_percent is None else y_percent)

        if site.startswith("hardscape:"):
            target_id, surface = self._parse_hardscape_site(site)
            item = self._find_hardscape_item(target_id)
            return self._default_surface_xy(item, surface)
        if site == "hardscape" and self.state.hardscape_items:
            item = max(self.state.hardscape_items, key=lambda hardscape: hardscape.coverage_percent)
            return item.x_percent, item.y_percent
        if site == "moss":
            mosses = [
                planting
                for planting in self.state.plantings
                if PLANTS[planting.plant].category in {"moss", "lichen"} and planting.status != "dead"
            ]
            if mosses:
                planting = max(mosses, key=lambda item: item.footprint_cm2)
                return planting.x_percent, planting.y_percent
        if site == "leaf_litter" and self.state.plantings:
            planting = max(self.state.plantings, key=lambda item: item.footprint_cm2)
            return planting.x_percent, planting.y_percent
        return 50.0, 50.0

    def _choose_animal_xy(self, group: AnimalGroup) -> None:
        best: tuple[float, float, float] | None = None
        for x, y in self._placement_candidates((group.x_percent, group.y_percent)):
            try:
                x, y = self._validate_xy(x, y)
            except ValueError:
                continue
            old_x, old_y, old_z = group.x_percent, group.y_percent, group.z_cm
            group.x_percent = x
            group.y_percent = y
            group.z_cm = self._animal_z_cm(group.site, x, y)
            score = self._animal_space_score(group, ANIMALS[group.animal])
            overlap = self._animal_local_overlap_pressure(group)
            group.x_percent, group.y_percent, group.z_cm = old_x, old_y, old_z
            candidate = (score - overlap * 0.5, x, y)
            if best is None or candidate[0] > best[0]:
                best = candidate
        if best is not None:
            _, x, y = best
            group.x_percent = x
            group.y_percent = y
            group.z_cm = self._animal_z_cm(group.site, x, y)

    def _animal_z_cm(self, site: str, x_percent: float, y_percent: float) -> float:
        if site.startswith("hardscape:"):
            return self._planting_z_cm(site, x_percent, y_percent)
        if site == "hardscape":
            item = self._hardscape_at_xy(x_percent, y_percent)
            return item.z_top_cm if item is not None else self.substrate_surface_height_cm(x_percent, y_percent)
        if site == "water":
            return 0.0
        if site in {"soil", "substrate"}:
            return max(0.0, self.substrate_surface_height_cm(x_percent, y_percent) - 0.4)
        return self.substrate_surface_height_cm(x_percent, y_percent)

    def _normalize_animal_site(self, site: str) -> str:
        raw = site.strip()
        normalized = normalize_key(raw)
        if normalized in ANIMAL_SITES:
            return normalized

        if normalized.startswith("hardscape_"):
            target_id, surface = self._parse_hardscape_reference(raw)
            return self._hardscape_site(target_id, surface)
        if raw.lower().startswith("hardscape:"):
            target_id, surface = self._parse_hardscape_reference(raw)
            return self._hardscape_site(target_id, surface)
        if normalized.startswith("h") and (normalized[1:].isdigit() or "_" in normalized or ":" in raw):
            target_id, surface = self._parse_hardscape_reference(raw)
            return self._hardscape_site(target_id, surface)

        allowed = ", ".join(ANIMAL_SITES)
        raise ValueError(f"unknown animal site '{site}', expected one of: {allowed}, hardscape:<id>")

    def _parse_hardscape_reference(self, site: str) -> tuple[str, str]:
        raw = site.strip()
        if not raw:
            raise ValueError("hardscape target cannot be empty")
        if raw.lower().startswith("hardscape:"):
            parts = [part.strip() for part in raw.split(":") if part.strip()]
            if len(parts) < 2 or len(parts) > 3:
                raise ValueError("hardscape site should look like hardscape:H01 or hardscape:H01:side")
            target_id = parts[1].upper()
            surface = normalize_key(parts[2]) if len(parts) == 3 else "top"
            return target_id, surface
        if ":" in raw:
            parts = [part.strip() for part in raw.split(":") if part.strip()]
            if len(parts) == 2:
                return parts[0].upper(), normalize_key(parts[1])
        normalized = normalize_key(raw)
        if normalized.startswith("hardscape_"):
            normalized = normalized.removeprefix("hardscape_")
        parts = [part for part in normalized.split("_") if part]
        if not parts:
            raise ValueError("hardscape target cannot be empty")
        surface = "top"
        if parts[-1] in HARDSCAPE_SURFACES:
            surface = parts[-1]
            parts = parts[:-1]
        target_id = "_".join(parts).upper()
        return target_id, surface

    def _parse_hardscape_site(self, site: str) -> tuple[str, str]:
        if not site.startswith("hardscape:"):
            raise ValueError(f"unknown hardscape target '{site}'")
        _, rest = site.split(":", 1)
        parts = rest.split(":")
        target_id = parts[0].strip().upper()
        surface = parts[1].strip().lower() if len(parts) > 1 else "top"
        return target_id, surface

    def _hardscape_site(self, item_id: str, surface: str = "top") -> str:
        normalized_id = item_id.strip().upper()
        normalized_surface = normalize_key(surface or "top")
        if normalized_surface not in HARDSCAPE_SURFACES:
            allowed = ", ".join(HARDSCAPE_SURFACES)
            raise ValueError(f"unknown hardscape surface '{surface}', expected one of: {allowed}")
        for item in self.state.hardscape_items:
            if item.item_id.upper() != normalized_id:
                continue
            definition = HARDSCAPES[item.kind]
            if normalized_surface not in definition.attach_surfaces:
                allowed = ", ".join(definition.attach_surfaces)
                raise ValueError(f"{item.item_id} has no {normalized_surface} surface; available: {allowed}")
            if normalized_surface == "top":
                return f"hardscape:{item.item_id}"
            return f"hardscape:{item.item_id}:{normalized_surface}"
        raise ValueError(f"unknown hardscape target '{item_id}'")

    def volume_profile(self) -> dict[str, float]:
        capacity = self.state.container.capacity_ml
        base_area = self.state.container.base_area_cm2

        layer_volume = 0.0
        substrate_solid = 0.0
        pore_capacity = 0.0
        for layer in self.state.substrate_layers:
            if layer.layer_kind == "mesh":
                continue
            volume = layer.height_cm * base_area
            layer_volume += volume
            solid_fraction = 0.0
            pore_fraction = 0.0
            for portion in layer.portions:
                definition = SUBSTRATES[portion.substrate]
                weight = portion.percent / 100.0
                solid_fraction += definition.solid_fraction * weight
                pore_fraction += definition.pore_fraction * weight
            substrate_solid += volume * solid_fraction
            pore_capacity += volume * pore_fraction

        hardscape_volume = 0.0
        for item in self.state.hardscape_items:
            definition = HARDSCAPES[item.kind]
            footprint = base_area * item.coverage_percent / 100.0
            hardscape_volume += footprint * definition.height_cm * definition.volume_factor

        root_volume = 0.0
        canopy_volume = 0.0
        for planting in self.state.plantings:
            definition = PLANTS[planting.plant]
            footprint = planting.footprint_cm2 or base_area * planting.area_percent / 100.0
            root_length = planting.root_length_cm if planting.root_length_cm > 0 else definition.root_depth_cm
            height = planting.height_cm if planting.height_cm > 0 else definition.height_cm
            root_volume += (
                footprint
                * root_length
                * definition.root_volume_factor
                * planting.root_mass_percent
                / 100.0
            )
            canopy_volume += footprint * height * definition.canopy_volume_factor

        animal_volume = 0.0
        animal_activity_area = 0.0
        for group in self.state.animal_groups:
            definition = ANIMALS[group.animal]
            animal_volume += group.count * definition.space_ml_per_count
            if group.count > 0:
                animal_activity_area += self._animal_group_activity_area(group, definition)

        pore_after_roots = max(0.0, pore_capacity - root_volume)
        root_over_pores = max(0.0, root_volume - pore_capacity)
        liquid_water = self._effective_liquid_water_ml()
        recorded_water = self.state.soil_moistened_ml + self.state.sprayed_ml
        water_added = recorded_water if recorded_water > 0 else liquid_water + self.state.vapor_water_ml + self.state.condensation_ml
        water_in_pores = min(liquid_water, pore_after_roots)
        free_water = max(0.0, liquid_water - water_in_pores)
        pore_air = max(0.0, pore_after_roots - water_in_pores)

        used_container = (
            layer_volume
            + hardscape_volume
            + canopy_volume
            + animal_volume
            + root_over_pores
            + free_water
            + self.state.condensation_ml
        )
        open_air = max(0.0, capacity - used_container)
        total_air = open_air + pore_air
        overfilled = max(0.0, used_container - capacity)

        return {
            "capacity_ml": capacity,
            "used_container_ml": used_container,
            "free_container_ml": max(0.0, capacity - used_container),
            "overfilled_ml": overfilled,
            "layer_volume_ml": layer_volume,
            "substrate_solid_ml": substrate_solid,
            "pore_capacity_ml": pore_capacity,
            "pore_air_ml": pore_air,
            "water_added_ml": water_added,
            "soil_moistened_ml": self.state.soil_moistened_ml,
            "sprayed_ml": self.state.sprayed_ml,
            "spray_count": float(self.state.spray_count),
            "liquid_water_ml": liquid_water,
            "vapor_water_ml": self.state.vapor_water_ml,
            "condensation_ml": self.state.condensation_ml,
            "surface_wetness": self.state.surface_wetness,
            "biofilm": self.state.biofilm,
            "mold_pressure": self.state.mold_pressure,
            "root_zone_oxygen": self.state.root_zone_oxygen,
            "leaf_litter_cover": self.state.leaf_litter_cover,
            "water_in_pores_ml": water_in_pores,
            "free_water_ml": free_water,
            "hardscape_volume_ml": hardscape_volume,
            "plant_root_volume_ml": root_volume,
            "plant_canopy_volume_ml": canopy_volume,
            "animal_volume_ml": animal_volume,
            "animal_activity_area_cm2": animal_activity_area,
            "open_air_ml": open_air,
            "total_air_ml": total_air,
            "entity_volume_ml": substrate_solid + hardscape_volume + root_volume + canopy_volume + animal_volume,
        }

    def _raise_if_container_volume_overflows(self) -> None:
        profile = self.volume_profile()
        if profile["overfilled_ml"] > 0.1:
            raise ValueError(
                f"not enough container volume remaining: over by {profile['overfilled_ml']:0.1f} ml"
            )

    def _effective_liquid_water_ml(self) -> float:
        if self.state.water_cycle_initialized:
            return max(0.0, self.state.liquid_water_ml)
        return max(0.0, self.state.soil_moistened_ml + self.state.sprayed_ml)

    def _ensure_water_cycle_initialized(self, infer_from_pool: bool = True) -> None:
        s = self.state
        if s.water_cycle_initialized:
            return
        recorded_water = s.soil_moistened_ml + s.sprayed_ml
        inferred_water = s.water * s.container.capacity_ml * 0.08 if infer_from_pool and recorded_water <= 0 else 0.0
        total = max(0.0, recorded_water + inferred_water)
        s.liquid_water_ml = max(s.liquid_water_ml, total * 0.92)
        s.vapor_water_ml = max(s.vapor_water_ml, min(8.0, total * 0.05))
        s.condensation_ml = max(s.condensation_ml, min(5.0, total * 0.03))
        s.surface_wetness = clamp(max(s.surface_wetness, total / 95.0))
        s.water_cycle_initialized = True

    def _surface_evaporation(self, hardscape: dict[str, float | str]) -> float:
        s = self.state
        warmth = max(0.0, s.temperature - 16.0) / 18.0
        exposure = 1.0 - float(hardscape["evaporation_shield"])
        return 0.0012 * warmth * (0.35 + s.light) * exposure

    def _advance_water_cycle(self, hardscape: dict[str, float | str]) -> None:
        self._ensure_water_cycle_initialized()
        s = self.state
        warmth = max(0.0, s.temperature - 16.0) / 18.0
        exposure = 1.0 - float(hardscape["evaporation_shield"])
        exposed_liquid = clamp(s.liquid_water_ml / 85.0)
        evaporation = min(
            s.liquid_water_ml,
            (0.08 + 0.46 * s.light) * warmth * exposure * (0.45 + exposed_liquid),
        )
        remaining_liquid = max(0.0, s.liquid_water_ml - evaporation)
        transpiration = min(
            remaining_liquid,
            s.plants * 0.00055 * self._temperature_factor(s.temperature) * (0.18 + s.light),
        )

        s.liquid_water_ml = max(0.0, s.liquid_water_ml - evaporation - transpiration)
        s.vapor_water_ml += evaporation + transpiration

        cool_bias = max(0.0, 20.0 - s.temperature) * 0.035
        night_bias = max(0.0, 0.30 - s.light) * 0.75
        condensation = min(s.vapor_water_ml, 0.02 + cool_bias + night_bias)
        s.vapor_water_ml -= condensation
        s.condensation_ml += condensation

        drip_threshold = 3.2 + float(hardscape["evaporation_shield"]) * 2.8
        drip = max(0.0, s.condensation_ml - drip_threshold) * 0.18
        s.condensation_ml -= drip
        s.liquid_water_ml += drip

        slope_strength = self._slope_strength()
        lowland_pool = min(s.liquid_water_ml, slope_strength * max(0.0, s.liquid_water_ml - 18.0) * 0.045)
        lowland_shift = lowland_pool * 0.02
        s.liquid_water_ml -= lowland_shift
        s.condensation_ml += lowland_shift

        surface_gain = (
            drip * 0.028
            + s.condensation_ml * 0.0015
            + float(hardscape["edge_moisture"]) * 0.006
            + lowland_pool * 0.004
        )
        surface_loss = (0.007 + s.light * 0.030 + warmth * 0.012) * (0.75 + exposure * 0.45)
        highland_drying = slope_strength * s.light * 0.006
        s.surface_wetness = clamp(s.surface_wetness + surface_gain - surface_loss - highland_drying)
        s.water = self._water_availability_score()

    def _apply_biological_water_delta(self, normalized_delta: float) -> None:
        s = self.state
        amount_ml = normalized_delta * s.container.capacity_ml * 0.075
        if amount_ml < 0:
            needed = -amount_ml
            from_liquid = min(s.liquid_water_ml, needed)
            s.liquid_water_ml -= from_liquid
            needed -= from_liquid
            if needed > 0:
                from_condensation = min(s.condensation_ml, needed)
                s.condensation_ml -= from_condensation
        elif amount_ml > 0:
            s.vapor_water_ml += amount_ml * 0.70
            s.condensation_ml += amount_ml * 0.15
            s.surface_wetness = clamp(s.surface_wetness + amount_ml * 0.005)
        s.water = self._water_availability_score()

    def _water_availability_score(self) -> float:
        profile = self.volume_profile()
        root_capacity = self._root_zone_pore_capacity_ml()
        if root_capacity <= 0.0:
            root_capacity = max(profile["pore_capacity_ml"], 1.0)
        root_fill = clamp(profile["water_in_pores_ml"] / max(root_capacity, 1.0))
        retention_score = self._root_zone_water_retention_score()
        retention_bonus = clamp((retention_score - 5.0) / 5.0)
        ideal_fill = max(0.42, 0.62 - retention_bonus * 0.16)
        accessible_pore_water = clamp(root_fill / ideal_fill)
        if profile["pore_capacity_ml"] <= 0:
            accessible_pore_water = clamp(self.state.liquid_water_ml / 65.0)
        free_water_bonus = clamp(profile["free_water_ml"] / 35.0) * 0.08
        vapor_bonus = clamp(self.state.vapor_water_ml / 12.0) * 0.08
        condensation_bonus = clamp(self.state.condensation_ml / 7.0) * 0.15
        surface_bonus = self.state.surface_wetness * 0.22
        retention_water_bonus = retention_bonus * root_fill * 0.08
        return clamp(
            accessible_pore_water * 0.52
            + free_water_bonus
            + vapor_bonus
            + condensation_bonus
            + surface_bonus
            + retention_water_bonus
        )

    def _root_zone_pore_capacity_ml(self) -> float:
        base_area = self.state.container.base_area_cm2
        capacity = 0.0
        for layer in self.state.substrate_layers:
            if layer.layer_kind not in {"soil", "amendment"}:
                continue
            pore_fraction = 0.0
            for portion in layer.portions:
                definition = SUBSTRATES[portion.substrate]
                pore_fraction += definition.pore_fraction * portion.percent / 100.0
            capacity += layer.height_cm * base_area * pore_fraction
        return capacity

    def _root_zone_water_retention_score(self) -> float:
        weighted = 0.0
        height = 0.0
        for layer in self.state.substrate_layers:
            if layer.layer_kind not in {"soil", "amendment"}:
                continue
            stats = substrate_layer_stats(layer)
            weighted += stats["water_retention"] * layer.height_cm
            height += layer.height_cm
        if height <= 0.0:
            return 5.0
        return weighted / height

    def _air_exchange_sensitivity(self) -> float:
        total_air = max(self.volume_profile()["total_air_ml"], 90.0)
        return clamp(680.0 / total_air, 0.70, 2.25)

    def _apply_waterlogged_gas_pressure(self) -> None:
        profile = self.volume_profile()
        pore_capacity = profile["pore_capacity_ml"]
        if pore_capacity <= 0:
            return
        pore_saturation = profile["water_in_pores_ml"] / pore_capacity
        pressure = max(0.0, pore_saturation - 0.86)
        if profile["free_water_ml"] > 4.0:
            pressure += clamp(profile["free_water_ml"] / 45.0) * 0.16
        if pressure <= 0:
            return
        self.state.oxygen -= pressure * 0.010
        self.state.carbon_dioxide += pressure * 0.008

    def _advance_visible_ecology(self, grazing: float, decay: float) -> None:
        s = self.state
        profile = self.volume_profile()
        surface_ecology = self.hardscape_surface_ecology()
        pore_capacity = profile["pore_capacity_ml"]
        pore_air_ratio = profile["pore_air_ml"] / max(pore_capacity, 1.0) if pore_capacity > 0 else clamp(s.oxygen)
        pore_saturation = profile["water_in_pores_ml"] / max(pore_capacity, 1.0) if pore_capacity > 0 else clamp(s.liquid_water_ml / 65.0)
        root_pressure = clamp(profile["plant_root_volume_ml"] / max(pore_capacity, 1.0)) if pore_capacity > 0 else 0.0
        target_root_o2 = clamp(s.oxygen * 0.45 + pore_air_ratio * 0.65 - max(0.0, pore_saturation - 0.82) * 0.55 - root_pressure * 0.16)
        s.root_zone_oxygen += (target_root_o2 - s.root_zone_oxygen) * 0.20

        wet_visible = clamp(s.surface_wetness * 0.45 + s.condensation_ml / 9.0 * 0.35 + s.water * 0.20)
        grazer_groups = sum(group.count for group in s.animal_groups if ANIMALS[group.animal].role == "small_consumer" and group.count > 0)
        decomposer_groups = sum(group.count for group in s.animal_groups if ANIMALS[group.animal].role in {"decomposer", "micro_consumer"} and group.count > 0)
        biofilm_gain = wet_visible * clamp(s.algae / 70.0) * (0.010 + s.light * 0.010)
        biofilm_gain *= 1.0 + surface_ecology["biofilm"] * 1.2 + surface_ecology["moisture"] * 0.55
        biofilm_loss = grazing * 0.006 + clamp(grazer_groups / 80.0) * 0.018 + max(0.0, 0.22 - wet_visible) * 0.020
        s.biofilm = clamp(s.biofilm + biofilm_gain - biofilm_loss)

        litter_target = clamp(s.detritus * 0.72 + max(0.0, 65.0 - s.plants) / 160.0 + len([p for p in s.plantings if p.status == "dead"]) * 0.08)
        s.leaf_litter_cover += (litter_target - s.leaf_litter_cover) * 0.08

        mold_gain = wet_visible * clamp(s.detritus / 0.72) * clamp(s.microbes / 70.0) * (0.012 + (1.0 - s.light) * 0.010)
        mold_gain *= 1.0 + surface_ecology["mold"] * 1.25 + surface_ecology["shelter"] * 0.45
        mold_loss = decay * 0.006 + clamp(decomposer_groups / 220.0) * 0.016 + max(0.0, 0.34 - wet_visible) * 0.030
        s.mold_pressure = clamp(s.mold_pressure + mold_gain - mold_loss)
        for planting in s.plantings:
            if planting.status == "dead":
                continue
            target_root_health = clamp(
                s.root_zone_oxygen - max(0.0, pore_saturation - 0.88) * 0.55
            ) * 100.0
            if planting.attached_to:
                local_env = self._local_life_environment(planting, self._life_environment())
                support = local_env.get("attachment_support", 1.0)
                target_root_health = clamp(target_root_health / 100.0 + (support - 0.58) * 0.20 + local_env.get("surface_biofilm_bias", 0.0) * 0.05) * 100.0
            planting.root_health += (target_root_health - planting.root_health) * 0.06

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
        return self._sun_conditions(hour)[0]

    def _sun_conditions(self, hour: int) -> tuple[float, float, float]:
        self._update_calendar_for_tick()
        self._update_weather_for_day()
        season = SEASON_PROFILES[canonical_season(self.state.season)]
        daylight_span = self.config.day_length * season["daylight"]
        sunrise = (self.config.day_length - daylight_span) * 0.5
        progress = clamp((hour - sunrise) / max(daylight_span, 1e-9))
        daylight = math.sin(progress * math.pi) if 0.0 < progress < 1.0 else 0.0
        window_light, window_azimuth, window_altitude = self._window_light_conditions(daylight, progress)
        lamp_light = self._moss_lamp_light(hour)
        self.state.moss_lamp_light = lamp_light
        sources: list[tuple[float, float, float]] = []
        if window_light > 0.0:
            sources.append((window_light, window_azimuth, window_altitude))
        if lamp_light > 0.0:
            sources.append(
                (
                    lamp_light,
                    self._compass_to_model_degrees(self.state.moss_lamp_angle_deg),
                    MOSS_LAMP_ALTITUDE_DEG,
                )
            )
        if not sources:
            return 0.0, self._compass_to_model_degrees(self.state.window_facing_deg), 0.0

        total_light = clamp(sum(source[0] for source in sources))
        vector_x = 0.0
        vector_y = 0.0
        altitude_sum = 0.0
        for amount, azimuth, altitude in sources:
            radians = math.radians(azimuth)
            vector_x += math.cos(radians) * amount
            vector_y += math.sin(radians) * amount
            altitude_sum += altitude * amount
        if abs(vector_x) <= 1e-12 and abs(vector_y) <= 1e-12:
            azimuth = sources[0][1]
        else:
            azimuth = self._vector_angle_deg(vector_x, vector_y)
        altitude = altitude_sum / max(sum(source[0] for source in sources), 1e-9)
        return total_light, azimuth, altitude

    def _window_light_conditions(self, daylight: float, progress: float) -> tuple[float, float, float]:
        world_sun_compass = self._normalize_degrees(90.0 + progress * 180.0)
        season = SEASON_PROFILES[canonical_season(self.state.season)]
        weather = WEATHER_PROFILES.get(self.state.weather_state, WEATHER_PROFILES["clear"])
        altitude = max(0.0, math.sin(progress * math.pi)) * 68.0 * season["altitude"]
        window_direction = canonical_window_direction(self.state.window_direction)
        window_compass = COMPASS_DIRECTIONS[window_direction]
        self.state.window_direction = window_direction
        self.state.window_azimuth_deg = window_compass
        self.state.window_light_mode = canonical_window_light_mode(self.state.window_light_mode)
        self.state.season = canonical_season(self.state.season)
        local_offset = self._angle_delta_deg(window_compass, world_sun_compass)
        local_compass = self._normalize_degrees(self.state.window_facing_deg + local_offset)
        direct_azimuth = self._compass_to_model_degrees(local_compass)
        diffuse_azimuth = self._compass_to_model_degrees(self.state.window_facing_deg)
        if daylight <= 0.0:
            self.state.window_light = 0.0
            self.state.window_direct_light = 0.0
            self.state.window_diffuse_light = 0.0
            return 0.0, diffuse_azimuth, 0.0

        profile = WINDOW_LIGHT_PROFILES[window_direction]
        direct_alignment = max(0.0, math.cos(math.radians(abs(local_offset))))
        mode = self.state.window_light_mode
        direct_gain = profile["direct"] * direct_alignment
        diffuse_gain = profile["diffuse"]
        if mode == "direct":
            direct_gain *= 1.16
            diffuse_gain *= 0.35
        elif mode == "diffuse":
            direct_gain *= 0.12
            diffuse_gain *= 1.70
        direct_light = daylight * self.config.light_intensity * season["light"] * weather["light"] * direct_gain * weather["direct"]
        diffuse_light = daylight * self.config.light_intensity * season["light"] * weather["light"] * diffuse_gain * weather["diffuse"]
        umbrella_filter = self._umbrella_light_filter(direct_azimuth)
        raw_direct_light = direct_light
        direct_light *= umbrella_filter["direct"]
        diffuse_light = diffuse_light * umbrella_filter["diffuse"] + raw_direct_light * umbrella_filter["scatter"]
        self.state.window_direct_light = clamp(direct_light)
        self.state.window_diffuse_light = clamp(diffuse_light)
        light = clamp(self.state.window_direct_light + self.state.window_diffuse_light, 0.0, 1.0)
        self.state.window_light = light
        direct_x = math.cos(math.radians(direct_azimuth)) * self.state.window_direct_light
        direct_y = math.sin(math.radians(direct_azimuth)) * self.state.window_direct_light
        diffuse_x = math.cos(math.radians(diffuse_azimuth)) * self.state.window_diffuse_light * 0.55
        diffuse_y = math.sin(math.radians(diffuse_azimuth)) * self.state.window_diffuse_light * 0.55
        if light <= 1e-9:
            azimuth = diffuse_azimuth
        else:
            azimuth = self._vector_angle_deg(direct_x + diffuse_x, direct_y + diffuse_y)
        altitude *= 0.78 + profile["warmth"] * 0.22
        return light, azimuth, altitude

    def _update_calendar_for_tick(self) -> None:
        s = self.state
        start = int(clamp(float(s.calendar_start_day_of_year), 1.0, 365.0))
        elapsed_days = int(s.tick // max(self.config.day_length, 1))
        day = ((start - 1 + elapsed_days) % 365) + 1
        s.calendar_start_day_of_year = start
        s.calendar_day_of_year = day
        s.season = self._season_for_day(day)

    def _season_for_day(self, day_of_year: int) -> str:
        day = ((int(day_of_year) - 1) % 365) + 1
        if 60 <= day <= 151:
            return "spring"
        if 152 <= day <= 243:
            return "summer"
        if 244 <= day <= 334:
            return "autumn"
        return "winter"

    def _update_weather_for_day(self) -> None:
        s = self.state
        day = int(s.tick // max(self.config.day_length, 1))
        mode = canonical_weather_mode(s.weather_mode)
        s.weather_mode = mode
        if s.weather_day == day and (mode == "variable" or s.weather_state == mode):
            return
        if mode != "variable":
            s.weather_state = mode
            s.weather_day = day
            return
        roll = self._stable_unit(s.seed, day, s.season, s.window_direction, "weather")
        if roll < 0.34:
            weather = "clear"
        elif roll < 0.74:
            weather = "partly_cloudy"
        elif roll < 0.94:
            weather = "overcast"
        else:
            weather = "rainy"
        s.weather_state = weather
        s.weather_day = day

    def _moss_lamp_light(self, hour: int) -> float:
        if not self.state.moss_lamp_enabled:
            return 0.0
        elapsed = (hour - self.state.moss_lamp_start_hour) % max(self.config.day_length, 1)
        if elapsed >= self.state.moss_lamp_duration_hours:
            return 0.0
        return clamp(self.state.moss_lamp_intensity)

    def _target_temperature(self) -> float:
        s = self.state
        profile = WINDOW_LIGHT_PROFILES[canonical_window_direction(s.window_direction)]
        season = SEASON_PROFILES[canonical_season(s.season)]
        weather = WEATHER_PROFILES.get(s.weather_state, WEATHER_PROFILES["clear"])
        window_heat = (
            (s.window_direct_light + s.window_diffuse_light * 0.35)
            * self.config.heat_gain
            * profile["warmth"]
            * season["heat"]
            * weather["heat"]
        )
        hour = s.hour
        afternoon = clamp(1.0 - abs(hour - 16.0) / 3.0)
        noon = clamp(1.0 - abs(hour - 12.0) / 3.0)
        morning = clamp(1.0 - abs(hour - 9.0) / 3.0)
        directional_heat = 0.0
        if s.window_direction == "west":
            directional_heat = s.window_direct_light * afternoon * 1.45 * season["heat"] * weather["heat"]
        elif s.window_direction == "south":
            directional_heat = s.window_direct_light * noon * 0.95 * season["heat"] * weather["heat"]
        elif s.window_direction == "east":
            directional_heat = s.window_direct_light * morning * 0.65 * season["heat"] * weather["heat"]
        lamp_heat = s.moss_lamp_light * 1.10
        s.placement_heat_bias = directional_heat + lamp_heat
        return self.config.base_temperature + window_heat + s.placement_heat_bias

    def _temperature_factor(self, temperature: float) -> float:
        distance = abs(temperature - 23.0)
        return clamp(1.0 - distance / 18.0, 0.08, 1.0)

    def _algae_resource_factor(self) -> float:
        s = self.state
        detrital_trace = s.detritus * 0.12
        film_trace = s.biofilm * 0.05
        return clamp(s.nutrients * 1.25 + detrital_trace + film_trace)

    def _algae_carrying_capacity(self, hardscape: dict[str, float | str] | None = None) -> float:
        s = self.state
        hardscape = hardscape or self.hardscape_profile()
        plantable_capacity = self.config.carrying_capacity * clamp(float(hardscape["plantable_percent"]) / 100.0, 0.12, 1.0)
        wet_surface = clamp(
            s.water * 0.38
            + s.surface_wetness * 0.36
            + clamp(s.condensation_ml / 8.0) * 0.18
            + float(hardscape["edge_moisture"]) * 0.45
        )
        hardscape_film_area = float(hardscape["coverage_percent"]) * (0.45 + float(hardscape["edge_moisture"]) * 1.8)
        return max(18.0, plantable_capacity * (0.24 + wet_surface * 0.76) + hardscape_film_area)

    def _soil_nutrient_release(self, decay: float, temp_factor: float) -> float:
        s = self.state
        weighted_nutrients = 0.0
        total_height = 0.0
        for layer in s.substrate_layers:
            if layer.layer_kind != "soil":
                continue
            stats = soil_layer_stats(layer)
            if stats["nutrients"] is None:
                continue
            weighted_nutrients += stats["nutrients"] * layer.height_cm
            total_height += layer.height_cm
        if total_height <= 0.0:
            return 0.0
        soil_signal = clamp((weighted_nutrients / total_height) / 10.0)
        moisture = clamp(s.water * 1.15)
        oxygen = clamp(s.oxygen * 1.20)
        microbe_signal = clamp(s.microbes / 120.0)
        mineralization = 0.00045 + decay * 0.0045 + microbe_signal * 0.0012
        return soil_signal * moisture * oxygen * temp_factor * mineralization

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

    def _algae_stress(self, carrying_capacity: float | None = None, resource_factor: float | None = None) -> float:
        s = self.state
        capacity = carrying_capacity if carrying_capacity is not None else self._algae_carrying_capacity()
        resource = resource_factor if resource_factor is not None else self._algae_resource_factor()
        overload = max(0.0, s.algae / max(capacity, 1.0) - 1.0)
        stress = 0.002
        stress += max(0.0, 0.38 - s.water) * 0.022
        stress += max(0.0, 0.10 - resource) * 0.030
        stress += max(0.0, 0.18 - s.carbon_dioxide) * 0.020
        stress += max(0.0, s.toxicity - 0.30) * 0.035
        stress += clamp(overload / 6.0) * 0.045 + max(0.0, overload - 1.0) * 0.003
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

    def _advance_living_records(self) -> None:
        if not self.state.plantings and not self.state.animal_groups:
            return

        env = self._life_environment()
        for planting in self.state.plantings:
            self._advance_planting_record(planting, self._local_life_environment(planting, env))
        for group in self.state.animal_groups:
            self._advance_animal_group_record(group, env)

    def _life_environment(self) -> dict[str, float]:
        s = self.state
        hardscape = self.hardscape_profile()
        sealed_water_signal = clamp((s.liquid_water_ml + s.vapor_water_ml + s.condensation_ml) / 90.0)
        sealed_humidity_bonus = (0.08 + sealed_water_signal * 0.16) if s.sealed else 0.0
        humidity = clamp(
            s.water * 0.42
            + float(hardscape["evaporation_shield"]) * 0.14
            + float(hardscape["edge_moisture"]) * 0.22
            + clamp(s.vapor_water_ml / 12.0) * 0.18
            + clamp(s.condensation_ml / 5.5) * 0.32
            + s.surface_wetness * 0.24
            + sealed_humidity_bonus
        )
        if s.sealed and s.condensation_ml > 1.0:
            humidity = max(humidity, 0.72 + clamp(s.condensation_ml / 5.5) * 0.18)
        light = clamp(s.light * (1.0 - float(hardscape["shade"]) * 0.55))
        daily_light = self._daily_light_budget(hardscape)
        return {
            "humidity": humidity * 100.0,
            "temperature": s.temperature,
            "light": light,
            "daily_light": daily_light,
            "water": s.water,
            "nutrition": s.nutrients * 10.0,
            "aeration": self._substrate_aeration_score(),
            "oxygen": s.oxygen,
            "carbon_dioxide": s.carbon_dioxide,
            "detritus": s.detritus,
            "toxicity": s.toxicity,
            "microbes": s.microbes,
            "algae": s.algae,
            "plants": s.plants,
            "biofilm": s.biofilm,
            "mold": s.mold_pressure,
            "root_zone_oxygen": s.root_zone_oxygen,
            "leaf_litter": s.leaf_litter_cover,
            "sun_azimuth": s.sun_azimuth_deg,
            "sun_altitude": s.sun_altitude_deg,
        }

    def _local_life_environment(self, planting: Planting, base_env: dict[str, float]) -> dict[str, float]:
        env = dict(base_env)
        lowland = self._local_lowland_factor(planting.x_percent, planting.y_percent)
        highland = 1.0 - lowland
        local_hardscape = self._local_hardscape_effects(planting.x_percent, planting.y_percent)
        local_overlap = self._plant_local_overlap_pressure(planting)
        slope_strength = self._slope_strength()
        surface_traits = None
        if planting.attached_to:
            try:
                item = self._find_hardscape_item(planting.attached_to)
                surface_traits = self._hardscape_surface_traits(item, planting.attachment_surface or "top")
            except ValueError:
                surface_traits = None
        surface_moisture = surface_traits["moisture"] if surface_traits else 0.0
        surface_shelter = surface_traits["shelter"] if surface_traits else 0.0
        surface_shade = surface_traits["shade"] if surface_traits else 0.0
        surface_aeration = surface_traits["aeration"] if surface_traits else 0.0

        env["humidity"] = max(
            0.0,
            min(
                100.0,
                env["humidity"]
                + (lowland - 0.5) * slope_strength * 34.0
                + local_hardscape["edge_moisture"] * 42.0
                + local_hardscape["shelter"] * 16.0
                + surface_moisture * 34.0
                + surface_shelter * 10.0
                - highland * slope_strength * 13.0,
            ),
        )
        env["water"] = clamp(
            env["water"]
            + (lowland - 0.5) * slope_strength * 0.32
            + local_hardscape["edge_moisture"] * 0.18
            + surface_moisture * 0.24
            - highland * slope_strength * 0.10
        )
        env["light"] = clamp(
            env["light"]
            * self._directional_light_factor(planting.x_percent, planting.y_percent, planting.z_cm)
            * self._surface_light_factor(planting)
            * (1.0 - local_hardscape["shade"] * 0.70 - surface_shade * 0.45 - local_overlap * 0.22)
        )
        env["daily_light"] = clamp(
            env.get("daily_light", env["light"])
            * self._surface_light_factor(planting)
            * (1.0 - local_hardscape["shade"] * 0.45 - surface_shade * 0.35 - local_overlap * 0.14)
        )
        env["aeration"] = max(
            0.0,
            min(
                10.0,
                env["aeration"]
                - max(0.0, lowland - 0.62) * slope_strength * 3.8
                - local_hardscape["shelter"] * 0.7
                - local_overlap * 1.4
                + (surface_aeration + local_hardscape["aeration_bias"]) * 4.0
            ),
        )
        env["root_zone_oxygen"] = clamp(env["root_zone_oxygen"] + surface_aeration * 0.22 - max(0.0, surface_moisture - 0.14) * 0.08)
        env["surface_mold_bias"] = max(0.0, local_hardscape["mold_bias"], surface_traits["mold"] if surface_traits else 0.0)
        env["surface_biofilm_bias"] = max(0.0, local_hardscape["biofilm_bias"], surface_traits["biofilm"] if surface_traits else 0.0)
        env["attachment_support"] = surface_traits["attachment"] if surface_traits else 1.0
        env["local_overlap"] = local_overlap
        env["lowland"] = lowland
        return env

    def _daily_light_budget(self, hardscape: dict[str, float | str] | None = None) -> float:
        s = self.state
        hardscape = hardscape or self.hardscape_profile()
        window_direction = canonical_window_direction(s.window_direction)
        profile = WINDOW_LIGHT_PROFILES[window_direction]
        season = SEASON_PROFILES[canonical_season(s.season)]
        weather = WEATHER_PROFILES.get(s.weather_state, WEATHER_PROFILES["clear"])
        mode = canonical_window_light_mode(s.window_light_mode)

        direct_gain = profile["direct"]
        diffuse_gain = profile["diffuse"]
        if mode == "direct":
            direct_gain *= 1.16
            diffuse_gain *= 0.35
        elif mode == "diffuse":
            direct_gain *= 0.12
            diffuse_gain *= 1.70

        direct_alignment_mean = {
            "north": 0.10,
            "east": 0.38,
            "south": 0.52,
            "west": 0.38,
        }[window_direction]
        mean_daylight = season["daylight"] * (2.0 / math.pi)
        direct_component = direct_gain * direct_alignment_mean * weather["direct"]
        diffuse_component = diffuse_gain * weather["diffuse"]
        umbrella_filter = self._umbrella_light_filter(self._compass_to_model_degrees(s.window_facing_deg))
        window_budget = (
            mean_daylight
            * self.config.light_intensity
            * season["light"]
            * weather["light"]
            * (
                direct_component * umbrella_filter["direct"]
                + diffuse_component * umbrella_filter["diffuse"]
                + direct_component * umbrella_filter["scatter"]
            )
        )
        if s.moss_lamp_enabled:
            lamp_budget = (
                clamp(s.moss_lamp_intensity)
                * clamp(s.moss_lamp_duration_hours / max(self.config.day_length, 1))
                * 0.70
            )
        else:
            lamp_budget = 0.0
        return clamp((window_budget + lamp_budget) * (1.0 - float(hardscape["shade"]) * 0.55))

    def _local_hardscape_effects(self, x_percent: float, y_percent: float) -> dict[str, float]:
        effects = {"shade": 0.0, "edge_moisture": 0.0, "shelter": 0.0, "biofilm_bias": 0.0, "mold_bias": 0.0, "aeration_bias": 0.0}
        for item in self.state.hardscape_items:
            definition = HARDSCAPES[item.kind]
            distance = self._distance_cm(x_percent, y_percent, item.x_percent, item.y_percent)
            angle = self._bearing_between_coords(item.x_percent, item.y_percent, x_percent, y_percent)
            radius = self._hardscape_support_radius_cm(item, angle)
            influence = clamp(1.0 - distance / max(radius * 1.7, 1e-9))
            if influence <= 0.0:
                continue
            surface = self._hardscape_surface_at_xy(item, x_percent, y_percent) or ("side" if influence > 0.38 else "top")
            traits = self._hardscape_surface_traits(item, surface)
            height_factor = clamp(definition.height_cm / 5.0)
            effects["shade"] = max(effects["shade"], definition.shade_factor * influence * (0.5 + height_factor) + traits["shade"] * influence * 0.55)
            effects["edge_moisture"] = max(effects["edge_moisture"], definition.edge_moisture * influence * 1.5 + max(0.0, traits["moisture"]) * influence)
            effects["shelter"] = max(effects["shelter"], definition.evaporation_shield * influence + traits["shelter"] * influence)
            effects["biofilm_bias"] = max(effects["biofilm_bias"], traits["biofilm"] * influence)
            effects["mold_bias"] = max(effects["mold_bias"], traits["mold"] * influence)
            effects["aeration_bias"] += traits["aeration"] * influence * 0.35
        effects["shade"] = max(effects["shade"], 1.0 - self._directional_light_factor(x_percent, y_percent, self.substrate_surface_height_cm(x_percent, y_percent)))
        effects["aeration_bias"] = clamp(effects["aeration_bias"], -0.18, 0.18)
        return effects

    def _sun_vector_xy(self) -> tuple[float, float]:
        radians = math.radians(self.state.sun_azimuth_deg)
        return math.cos(radians), math.sin(radians)

    def _directional_light_factor(self, x_percent: float, y_percent: float, z_cm: float = 0.0) -> float:
        if self.state.light <= 0.0 or self.state.sun_altitude_deg <= 0.0:
            return 1.0
        px, py = self._coord_to_cm(x_percent, y_percent)
        sun_x, sun_y = self._sun_vector_xy()
        shadow_x = -sun_x
        shadow_y = -sun_y
        shade = 0.0
        altitude_tan = max(0.16, math.tan(math.radians(max(4.0, self.state.sun_altitude_deg))))
        for item in self.state.hardscape_items:
            definition = HARDSCAPES[item.kind]
            ix, iy = self._coord_to_cm(item.x_percent, item.y_percent)
            dx = px - ix
            dy = py - iy
            along = dx * shadow_x + dy * shadow_y
            if along <= 0.0:
                continue
            object_height = max(0.0, item.z_top_cm - max(z_cm, item.z_base_cm))
            if object_height <= 0.05:
                continue
            ray_angle = self._vector_angle_deg(shadow_x, shadow_y)
            support = self._hardscape_support_radius_cm(item, ray_angle)
            shadow_length = support + object_height / altitude_tan
            if along > shadow_length:
                continue
            lateral = abs(dx * -shadow_y + dy * shadow_x)
            width = support * (0.80 + 0.35 * (1.0 - along / max(shadow_length, 1e-9)))
            if lateral > width:
                continue
            depth = (1.0 - along / max(shadow_length, 1e-9)) * (1.0 - lateral / max(width, 1e-9))
            shade = max(shade, definition.shade_factor * (0.70 + clamp(object_height / 4.0) * 0.55) * depth)
        return clamp(1.0 - shade, 0.18, 1.0)

    def _surface_light_factor(self, planting: Planting) -> float:
        if not planting.attached_to or self.state.sun_altitude_deg <= 0.0:
            return 1.0
        try:
            item = self._find_hardscape_item(planting.attached_to)
        except ValueError:
            return 1.0
        surface = planting.attachment_surface or "top"
        altitude_factor = clamp(self.state.sun_altitude_deg / 68.0)
        if surface == "top":
            return clamp(0.64 + altitude_factor * 0.42, 0.25, 1.05)
        if surface == "underside":
            return 0.22
        normal = self._hardscape_normal_deg(item, planting.x_percent, planting.y_percent)
        nx = math.cos(math.radians(normal))
        ny = math.sin(math.radians(normal))
        sx, sy = self._sun_vector_xy()
        facing = max(0.0, nx * sx + ny * sy)
        base = 0.38 if surface in {"side", "groove"} else 0.46
        return clamp(base + facing * 0.60 + altitude_factor * 0.12, 0.18, 1.0)

    def _plant_local_overlap_pressure(self, planting: Planting) -> float:
        pressure = 0.0
        radius = self._plant_radius_cm(planting)
        for other in self.state.plantings:
            if other is planting or other.status == "dead":
                continue
            distance = self._distance_cm(planting.x_percent, planting.y_percent, other.x_percent, other.y_percent)
            overlap = self._circle_overlap_fraction(radius, self._plant_radius_cm(other), distance)
            if overlap <= 0:
                continue
            allowed = self._allowed_plant_overlap(planting, other)
            pressure += max(0.0, overlap - allowed * 0.55)
        return clamp(pressure)

    def _local_animal_environment(self, group: AnimalGroup, base_env: dict[str, float]) -> dict[str, float]:
        env = dict(base_env)
        lowland = self._local_lowland_factor(group.x_percent, group.y_percent)
        highland = 1.0 - lowland
        local_hardscape = self._local_hardscape_effects(group.x_percent, group.y_percent)
        local_overlap = self._animal_local_overlap_pressure(group)
        space_score = self._animal_space_score(group, ANIMALS[group.animal])
        slope_strength = self._slope_strength()

        shelter_bonus = 0.0
        water_bonus = 0.0
        aeration_penalty = 0.0
        surface_traits = None
        if group.site in {"moss", "leaf_litter"}:
            shelter_bonus += 8.0
            water_bonus += 0.05
        if group.site.startswith("hardscape") or group.site == "hardscape":
            shelter_bonus += local_hardscape["shelter"] * 18.0
            water_bonus += local_hardscape["edge_moisture"] * 0.12
            if group.attached_to:
                try:
                    item = self._find_hardscape_item(group.attached_to)
                    surface_traits = self._hardscape_surface_traits(item, group.attachment_surface or "top")
                except ValueError:
                    surface_traits = None
            elif group.site == "hardscape":
                item = self._hardscape_at_xy(group.x_percent, group.y_percent)
                if item is not None:
                    surface = self._hardscape_surface_at_xy(item, group.x_percent, group.y_percent) or "top"
                    surface_traits = self._hardscape_surface_traits(item, surface)
            if surface_traits:
                shelter_bonus += surface_traits["shelter"] * 30.0
                water_bonus += surface_traits["moisture"] * 0.22
                aeration_penalty -= surface_traits["aeration"] * 2.0
        if group.site == "soil":
            aeration_penalty += max(0.0, lowland - 0.65) * slope_strength * 1.5
        if group.site == "water":
            water_bonus += 0.18
            aeration_penalty += 0.6

        env["humidity"] = max(
            0.0,
            min(
                100.0,
                env["humidity"]
                + (lowland - 0.5) * slope_strength * 26.0
                + local_hardscape["edge_moisture"] * 34.0
                + shelter_bonus
                - highland * slope_strength * 8.0,
            ),
        )
        env["water"] = clamp(
            env["water"]
            + (lowland - 0.5) * slope_strength * 0.25
            + water_bonus
            - highland * slope_strength * 0.06
        )
        env["aeration"] = max(
            0.0,
            min(
                10.0,
                env["aeration"]
                - max(0.0, lowland - 0.72) * slope_strength * 2.2
                - local_overlap * 0.9
                - aeration_penalty,
            ),
        )
        env["oxygen"] = clamp(env["oxygen"] - local_overlap * 0.05 - max(0.0, 0.35 - space_score) * 0.05)
        if surface_traits:
            env["light"] = clamp(env["light"] * (1.0 - surface_traits["shade"] * 0.65))
            env["biofilm"] = clamp(env["biofilm"] + surface_traits["biofilm"] * 0.42 + max(0.0, surface_traits["moisture"]) * 0.14)
            env["mold"] = clamp(env["mold"] + surface_traits["mold"] * 0.38)
            env["detritus"] = clamp(env["detritus"] + surface_traits["shelter"] * 0.10)
        env["local_animal_overlap"] = local_overlap
        env["animal_space"] = space_score
        env["lowland"] = lowland
        env["local_shelter"] = clamp(local_hardscape["shelter"] + shelter_bonus / 40.0)
        env["local_edge_moisture"] = local_hardscape["edge_moisture"]
        env["local_shade"] = local_hardscape["shade"]
        env["surface_biofilm_bias"] = surface_traits["biofilm"] if surface_traits else local_hardscape["biofilm_bias"]
        env["surface_mold_bias"] = surface_traits["mold"] if surface_traits else local_hardscape["mold_bias"]
        return env

    def _animal_habitat_key(self, group: AnimalGroup) -> str:
        if group.site.startswith("hardscape:"):
            return group.site.lower()
        if group.site == "hardscape" and group.attached_to:
            suffix = f":{group.attachment_surface}" if group.attachment_surface and group.attachment_surface != "top" else ""
            return f"hardscape:{group.attached_to}{suffix}".lower()
        return group.site

    def _animal_habitat_area_cm2(self, group: AnimalGroup) -> float:
        base_area = self.state.container.base_area_cm2
        site = group.site
        if site.startswith("hardscape:"):
            try:
                item_id, surface = self._parse_hardscape_site(site)
                item = self._find_hardscape_item(item_id)
            except ValueError:
                return base_area * 0.04
            surface_factor = SURFACE_CAPACITY_FACTORS.get(surface, 0.45)
            traits = self._hardscape_surface_traits(item, surface)
            shelter_bonus = 1.0 + traits["shelter"] * 0.55 + traits["attachment"] * 0.18
            return base_area * item.coverage_percent / 100.0 * (0.55 + surface_factor) * shelter_bonus
        if site == "hardscape":
            return sum(base_area * item.coverage_percent / 100.0 for item in self.state.hardscape_items) * 1.20
        if site == "water":
            profile = self.volume_profile()
            return max(0.0, profile["free_water_ml"] * 0.55 + profile["liquid_water_ml"] * 0.08)
        if site == "moss":
            moss_area = sum(
                planting.footprint_cm2
                for planting in self.state.plantings
                if PLANTS[planting.plant].category in {"moss", "lichen"} and planting.status != "dead"
            )
            return moss_area + base_area * (0.04 + self.state.surface_wetness * 0.16)
        if site == "leaf_litter":
            wood_area = sum(
                base_area * item.coverage_percent / 100.0
                for item in self.state.hardscape_items
                if HARDSCAPES[item.kind].category == "wood"
            )
            return base_area * (0.08 + self.state.detritus * 0.55) + wood_area * 0.45
        if site == "soil":
            depth_factor = clamp(self.substrate_height_cm() / max(self.state.container.height_cm, 1e-9))
            return base_area * (0.12 + depth_factor * 2.2)
        if site == "substrate":
            depth_factor = clamp(self.substrate_height_cm() / max(self.state.container.height_cm, 1e-9))
            return base_area * (0.22 + depth_factor * 2.7)
        plantable = float(self.hardscape_profile()["plantable_percent"]) / 100.0
        return base_area * max(0.04, plantable)

    def _animal_space_score(self, group: AnimalGroup, definition: AnimalDefinition) -> float:
        habitat_key = self._animal_habitat_key(group)
        habitat_area = self._animal_habitat_area_cm2(group)
        used_area = 0.0
        for other in self.state.animal_groups:
            if other.count <= 0 or other.survival_state == "dead":
                continue
            if self._animal_habitat_key(other) != habitat_key:
                continue
            used_area += self._animal_group_activity_area(other)
        if group not in self.state.animal_groups:
            used_area += self._animal_group_activity_area(group, definition)
        capacity_score = clamp(habitat_area / max(used_area, definition.minimum_activity_area_cm2, 1e-9))
        return clamp(capacity_score - self._animal_local_overlap_pressure(group) * 0.35)

    def _animal_local_overlap_pressure(self, group: AnimalGroup) -> float:
        pressure = 0.0
        radius = self._animal_group_radius_cm(group)
        habitat_key = self._animal_habitat_key(group)
        for other in self.state.animal_groups:
            if other is group or other.count <= 0 or other.survival_state == "dead":
                continue
            if self._animal_habitat_key(other) != habitat_key:
                continue
            distance = self._distance_cm(group.x_percent, group.y_percent, other.x_percent, other.y_percent)
            overlap = self._circle_overlap_fraction(radius, self._animal_group_radius_cm(other), distance)
            pressure += max(0.0, overlap - 0.18)
        return clamp(pressure)

    def _set_initial_animal_microhabitat(self, group: AnimalGroup) -> None:
        if group.site.startswith("hardscape:"):
            surface = group.attachment_surface or "top"
            if surface in {"crack", "groove"}:
                group.microhabitat = f"{surface} shelter"
            elif surface == "underside":
                group.microhabitat = "under hardscape"
            elif surface == "side":
                group.microhabitat = "hardscape side"
            else:
                group.microhabitat = "hardscape top"
            group.shelter_use = 65.0 if surface in {"crack", "groove", "underside"} else 35.0
        elif group.site in {"soil", "substrate"}:
            group.microhabitat = "pore spaces"
            group.shelter_use = 55.0
        elif group.site == "leaf_litter":
            group.microhabitat = "litter pocket"
            group.shelter_use = 62.0
        elif group.site == "moss":
            group.microhabitat = "moss cushion"
            group.shelter_use = 58.0
        elif group.site == "water":
            group.microhabitat = "water film"
            group.shelter_use = 18.0
        else:
            group.microhabitat = "surface"
            group.shelter_use = 20.0
        group.visible_activity = 0.0

    def _advance_animal_microhabitat(
        self,
        group: AnimalGroup,
        definition: AnimalDefinition,
        env: dict[str, float],
        food_score: float,
        space_score: float,
    ) -> None:
        if group.count <= 0 or group.survival_state == "dead":
            group.microhabitat = "gone"
            group.visible_activity = 0.0
            group.shelter_use = 0.0
            return
        night = 1.0 - clamp(self.state.light / 0.55)
        damp = clamp(env["humidity"] / 100.0 * 0.55 + env["water"] * 0.45)
        shelter = clamp(env.get("local_shelter", 0.0) + (0.20 if group.site in {"soil", "substrate", "leaf_litter", "moss"} else 0.0))
        if group.site.startswith("hardscape:"):
            surface = group.attachment_surface or "top"
            shelter += 0.25 if surface in {"crack", "groove", "underside"} else 0.08
        group.shelter_use = clamp(shelter, 0.0, 1.0) * 100.0
        if env["oxygen"] < 0.18:
            group.microhabitat = "near air pockets"
        elif env["water"] < definition.water_range[0] * 0.85:
            group.microhabitat = "searching damp edges"
        elif env["water"] > definition.water_range[1] + 0.08:
            group.microhabitat = "climbing above wet spots"
        elif space_score < 0.28:
            group.microhabitat = "crowded refuge"
        elif food_score < 0.35:
            group.microhabitat = "foraging line"
        elif group.site.startswith("hardscape:") and (group.attachment_surface or "top") in {"crack", "groove", "underside"}:
            group.microhabitat = f"{group.attachment_surface} refuge"
        elif group.site == "moss":
            group.microhabitat = "inside moss cushion"
        elif group.site == "leaf_litter":
            group.microhabitat = "under leaf litter"
        elif group.site in {"soil", "substrate"}:
            group.microhabitat = "soil pore network"
        elif group.site == "water":
            group.microhabitat = "water film"
        else:
            group.microhabitat = "surface film"
        base_visibility = 0.22 + night * 0.34 + damp * 0.18 + max(0.0, 0.42 - food_score) * 0.30
        hide_penalty = shelter * 0.32 + max(0.0, self.state.light - 0.35) * 0.25
        if definition.size_class == "micro":
            base_visibility *= 0.45
        elif definition.size_class == "tiny":
            base_visibility *= 0.72
        group.visible_activity = clamp(base_visibility - hide_penalty, 0.0, 1.0) * 100.0

    def _substrate_aeration_score(self) -> float:
        weighted = 0.0
        total_height = 0.0
        for layer in self.state.substrate_layers:
            if layer.layer_kind == "mesh":
                continue
            stats = substrate_layer_stats(layer)
            weighted += stats["aeration"] * layer.height_cm
            total_height += layer.height_cm
        base = weighted / total_height if total_height > 0 else 5.0
        profile = self.volume_profile()
        pore_capacity = profile["pore_capacity_ml"]
        if pore_capacity > 0:
            pore_saturation = profile["water_in_pores_ml"] / pore_capacity
            base -= max(0.0, pore_saturation - 0.76) * 4.0
        if profile["free_water_ml"] > 0:
            base -= clamp(profile["free_water_ml"] / 45.0) * 2.0
        return clamp(base / 10.0) * 10.0

    def _advance_planting_record(self, planting: Planting, env: dict[str, float]) -> None:
        definition = PLANTS[planting.plant]
        if planting.status == "dead" or planting.survival_state == "dead":
            self._mark_plant_dead(planting)
            return

        planting.age_ticks += 1

        suitability = self._plant_preference_score(definition, env)
        root_recovery = clamp(1.0 - planting.prune_stress / 120.0, 0.05, 1.0)
        space_score = self._plant_reproduction_space_score(definition)
        self._apply_plant_mortality(planting, suitability, env)
        if planting.status == "dead":
            return

        planting.growth_rate = round(
            definition.base_growth_rate * suitability * root_recovery * (0.35 + space_score * 0.65),
            5,
        )
        self._advance_planting_space(planting, definition, suitability, root_recovery, space_score, env)
        self._advance_plant_orientation(planting, definition, env)
        self._advance_plant_shape(planting, definition, env)
        self._advance_plant_structure(planting, definition, suitability)

        planting.survival_state = self._living_state_from_score(suitability, planting.health)
        if planting.age_ticks < 24:
            planting.growth_stage = "establishing"
        elif planting.offspring_potential > 0:
            planting.growth_stage = "dividable"
        elif planting.reproduction_progress >= 60.0:
            planting.growth_stage = "reproductive"
        elif planting.age_ticks >= definition.min_reproductive_age_ticks:
            planting.growth_stage = "mature"
        else:
            planting.growth_stage = "growing"

        if self._plant_can_build_reproduction(definition, planting, suitability, space_score):
            gain = definition.reproduction_rate * suitability * root_recovery * space_score
            planting.reproduction_progress = clamp(planting.reproduction_progress + gain, 0.0, 100.0)
            planting.population_pressure = max(0.0, planting.population_pressure - 0.025)
        else:
            planting.reproduction_progress = max(0.0, planting.reproduction_progress - 0.010)
            if space_score < 0.30:
                planting.population_pressure = clamp(planting.population_pressure + (0.30 - space_score) * 0.35, 0.0, 100.0)

        if planting.reproduction_progress >= 100.0 and self._plant_can_form_offspring(definition, planting):
            planting.offspring_potential += 1
            planting.reproduction_progress = 0.0
            planting.growth_stage = "dividable"

    def _apply_plant_mortality(self, planting: Planting, suitability: float, env: dict[str, float]) -> None:
        stress = 0.0
        stress += max(0.0, 0.44 - suitability) * 2.4
        stress += max(0.0, 0.18 - env["oxygen"]) * 1.4
        stress += max(0.0, env["carbon_dioxide"] - 0.86) * 0.6
        stress += max(0.0, env["toxicity"] - 0.38) * 1.8
        stress += env.get("local_overlap", 0.0) * 0.34
        stress += max(0.0, 0.30 - env.get("root_zone_oxygen", 1.0)) * 1.2
        stress += max(0.0, 35.0 - planting.root_health) * 0.012
        stress += max(0.0, env.get("lowland", 0.5) - 0.78) * max(0.0, 3.5 - env["aeration"]) * 0.09
        stress += max(0.0, 0.48 - env.get("attachment_support", 1.0)) * (1.45 if planting.attached_to else 0.0)
        stress += env.get("surface_mold_bias", 0.0) * self.state.mold_pressure * (0.30 if planting.attached_to else 0.10)
        stress += planting.prune_stress * 0.0018
        if stress > 0:
            planting.health = max(0.0, planting.health - stress)
            planting.population_pressure = clamp(planting.population_pressure + stress * 0.08, 0.0, 100.0)
        elif suitability > 0.72 and planting.health < 100.0:
            planting.health = min(100.0, planting.health + 0.04)
            planting.prune_stress = max(0.0, planting.prune_stress - 0.035)
            if planting.attached_to and env.get("attachment_support", 0.0) > 0.76:
                planting.root_health = min(100.0, planting.root_health + 0.035)

        if planting.health <= 0.0:
            self._mark_plant_dead(planting)

    def _mark_plant_dead(self, planting: Planting) -> None:
        self._account_for_plant_death(planting)
        planting.health = 0.0
        planting.status = "dead"
        planting.survival_state = "dead"
        planting.growth_stage = "dead"
        planting.growth_rate = 0.0
        planting.reproduction_progress = 0.0
        planting.offspring_potential = 0
        planting.new_growth_count = 0
        planting.flower_count = 0
        planting.canopy_density_percent = 0.0

    def _account_for_plant_death(self, planting: Planting) -> None:
        if planting.death_processed:
            return
        definition = PLANTS[planting.plant]
        base_area = self.state.container.base_area_cm2
        footprint = planting.footprint_cm2 or base_area * planting.area_percent / 100.0
        mature_footprint = max(1.0, base_area * definition.mature_area_percent / 100.0)
        biomass_signal = clamp(footprint / mature_footprint, 0.15, 1.25)
        area_signal = max(planting.area_percent, definition.min_area_percent) / 100.0
        self.state.detritus += 0.040 * biomass_signal + 0.18 * area_signal
        self.state.leaf_litter_cover = clamp(self.state.leaf_litter_cover + 0.10 * biomass_signal + 0.22 * area_signal)
        if self.state.water > 0.55 or self.state.surface_wetness > 0.45:
            self.state.mold_pressure = clamp(self.state.mold_pressure + 0.025 * biomass_signal)
        planting.death_processed = True

    def _advance_planting_space(
        self,
        planting: Planting,
        definition: PlantDefinition,
        suitability: float,
        root_recovery: float,
        space_score: float,
        env: dict[str, float],
    ) -> None:
        if planting.status == "dead" or planting.health <= 0.0:
            return
        base_area = self.state.container.base_area_cm2
        mature_footprint = base_area * definition.mature_area_percent / 100.0
        if mature_footprint <= 0.0:
            return

        if planting.initial_footprint_cm2 <= 0.0:
            planting.initial_footprint_cm2 = planting.footprint_cm2 or base_area * planting.area_percent / 100.0
        if planting.footprint_cm2 <= 0.0:
            planting.footprint_cm2 = planting.initial_footprint_cm2

        headroom = max(0.0, mature_footprint - planting.footprint_cm2)
        if headroom <= 1e-9:
            return

        local_overlap = env.get("local_overlap", 0.0)
        local_space = max(0.0, space_score - local_overlap * 0.65)
        attachment_support = env.get("attachment_support", 1.0)
        if planting.attached_to:
            local_space *= clamp(0.50 + attachment_support * 0.62, 0.30, 1.12)
        if suitability < 0.42 or local_space <= 0.08:
            planting.population_pressure = clamp(planting.population_pressure + max(0.0, 0.42 - suitability) * 0.15 + local_overlap * 0.22, 0.0, 100.0)
            return

        category_factor = 1.0
        if definition.category in {"moss", "lichen"}:
            category_factor = 1.35
        elif definition.category in {"orchid_mini", "bromeliad_air", "bromeliad_tank"}:
            category_factor = 0.58
        elif definition.category in {"terrestrial_fern", "epiphytic_fern"}:
            category_factor = 0.82

        surface_bonus = 1.0
        if planting.attached_to:
            surface_bonus = clamp(0.62 + attachment_support * 0.58 + env.get("surface_biofilm_bias", 0.0) * 0.18, 0.45, 1.24)
        gain = headroom * definition.base_growth_rate * suitability * root_recovery * local_space * category_factor * surface_bonus * 0.018
        if gain <= 0.0:
            return

        old_footprint = planting.footprint_cm2
        old_area = planting.area_percent
        planting.footprint_cm2 = min(mature_footprint, planting.footprint_cm2 + gain)
        planting.area_percent = planting.footprint_cm2 / base_area * 100.0
        try:
            self._raise_if_plant_growth_collision(planting)
            self._raise_if_container_volume_overflows()
        except ValueError:
            planting.footprint_cm2 = old_footprint
            planting.area_percent = old_area
            planting.population_pressure = clamp(planting.population_pressure + 0.75 + local_overlap * 0.8, 0.0, 100.0)

    def _plant_preference_score(self, definition: PlantDefinition, env: dict[str, float]) -> float:
        light_value = env.get("daily_light", env["light"])
        if "daily_light" in env:
            light_value = clamp(light_value * 1.70)
        scores = (
            self._range_score(env["humidity"], definition.humidity_range, 28.0),
            self._range_score(env["temperature"], definition.temperature_range, 9.0),
            self._range_score(light_value, definition.light_range, 0.30),
            self._range_score(env["water"], definition.water_range, 0.32),
            self._range_score(env["nutrition"], definition.nutrition_range, 7.0),
            self._range_score(env["aeration"], definition.aeration_range, 4.0),
        )
        return min(scores)

    def _plant_reproduction_space_score(self, definition: PlantDefinition) -> float:
        profile = self.volume_profile()
        remaining_area = self.remaining_plantable_area_percent()
        area_score = clamp(remaining_area / max(definition.min_area_percent * 2.0, 1.0))
        volume_score = clamp(profile["free_container_ml"] / 160.0)
        return min(area_score, volume_score)

    def _plant_can_build_reproduction(
        self,
        definition: PlantDefinition,
        planting: Planting,
        suitability: float,
        space_score: float,
    ) -> bool:
        if definition.reproduction_mode == "none":
            return False
        if planting.age_ticks < definition.min_reproductive_age_ticks:
            return False
        if planting.health < 72.0 or planting.prune_stress > 35.0:
            return False
        if suitability < 0.62 or space_score < 0.45:
            return False
        return planting.area_percent >= definition.min_area_percent

    def _plant_can_form_offspring(self, definition: PlantDefinition, planting: Planting) -> bool:
        profile = self.volume_profile()
        remaining_area = self.remaining_plantable_area_percent()
        strict_modes = {"division", "pups", "rhizome_division", "offset_or_seed"}
        required_area = definition.min_area_percent * (2.4 if definition.reproduction_mode in strict_modes else 1.4)
        required_volume = 220.0 if definition.reproduction_mode in strict_modes else 120.0
        mature_fraction = planting.area_percent / max(definition.mature_area_percent, 1.0)
        required_maturity = 0.55 if definition.reproduction_mode not in strict_modes else 0.72
        return (
            remaining_area >= required_area
            and profile["free_container_ml"] >= required_volume
            and mature_fraction >= required_maturity
            and planting.population_pressure < 20.0
        )

    def _advance_animal_group_record(self, group: AnimalGroup, base_env: dict[str, float]) -> None:
        definition = ANIMALS[group.animal]
        if group.count <= 0 or group.survival_state == "dead":
            self._mark_animal_group_dead(group)
            return

        group.age_ticks += 1
        group.activity_area_cm2 = self._animal_activity_area(definition, group.count)

        env = self._local_animal_environment(group, base_env)
        suitability = self._animal_preference_score(definition, env)
        food_score = self._animal_food_score(definition, env)
        density_score = clamp(1.0 - group.count / max(definition.max_reasonable_count, 1), 0.0, 1.0)
        space_score = min(density_score, clamp(self.volume_profile()["free_container_ml"] / 140.0), env.get("animal_space", 1.0))
        self._apply_animal_mortality(group, suitability, food_score, env)
        if group.count <= 0:
            self._mark_animal_group_dead(group)
            return

        self._advance_animal_movement(group, definition, base_env, suitability, food_score, space_score)
        env = self._local_animal_environment(group, base_env)
        suitability = self._animal_preference_score(definition, env)
        food_score = self._animal_food_score(definition, env)
        density_score = clamp(1.0 - group.count / max(definition.max_reasonable_count, 1), 0.0, 1.0)
        space_score = min(density_score, clamp(self.volume_profile()["free_container_ml"] / 140.0), env.get("animal_space", 1.0))
        colony_viability = self._animal_colony_viability(definition, group)

        group.growth_rate = round(
            definition.base_growth_rate
            * suitability
            * food_score
            * (0.25 + space_score * 0.75)
            * (0.30 + colony_viability * 0.70)
            * clamp(definition.assimilation_efficiency / 0.42, 0.35, 1.45),
            5,
        )
        self._advance_animal_microhabitat(group, definition, env, food_score, space_score)

        group.survival_state = self._living_state_from_score(min(suitability, food_score, colony_viability), 100.0)
        if space_score < 0.22:
            group.population_trend = "crowded"
        elif group.count >= definition.max_reasonable_count:
            group.population_trend = "crowded"
        elif group.reproduction_progress >= 80.0:
            group.population_trend = "ready"
        elif colony_viability < 0.45:
            group.population_trend = "stalled"
        elif group.growth_rate > definition.base_growth_rate * 0.55:
            group.population_trend = "growing"
        elif min(suitability, food_score) < 0.35:
            group.population_trend = "stalled"
        else:
            group.population_trend = "steady"

        if self._animal_can_reproduce(definition, group, suitability, food_score, space_score):
            gain = (
                definition.reproduction_rate
                * suitability
                * food_score
                * space_score
                * clamp(definition.assimilation_efficiency / 0.42, 0.35, 1.45)
            )
            group.reproduction_progress = clamp(group.reproduction_progress + gain, 0.0, 100.0)
            group.crowding_pressure = max(0.0, group.crowding_pressure - 0.035)
        else:
            group.reproduction_progress = max(0.0, group.reproduction_progress - 0.012)
            if space_score < 0.30 or group.count >= definition.max_reasonable_count:
                group.crowding_pressure = clamp(group.crowding_pressure + max(0.0, 0.35 - space_score) * 0.45, 0.0, 100.0)

        if group.reproduction_progress >= 100.0:
            self._try_animal_birth(definition, group)

    def _animal_colony_viability(self, definition: AnimalDefinition, group: AnimalGroup) -> float:
        if definition.min_count <= 1:
            return 1.0
        return clamp((group.count / max(definition.min_count, 1)) ** 1.35)

    def _advance_animal_movement(
        self,
        group: AnimalGroup,
        definition: AnimalDefinition,
        base_env: dict[str, float],
        suitability: float,
        food_score: float,
        space_score: float,
    ) -> None:
        if definition.movement_range_cm <= 0.0 or group.count <= 0:
            group.movement_state = "settled"
            group.movement_reason = ""
            group.distance_moved_cm = 0.0
            return

        current_score = self._animal_position_score(group, definition, base_env)
        candidates = self._animal_movement_candidates(group, definition)
        best = (current_score, group.x_percent, group.y_percent, "holding")
        for x, y in candidates:
            if (round(x, 3), round(y, 3)) == (round(group.x_percent, 3), round(group.y_percent, 3)):
                continue
            if not self._animal_can_occupy_xy(group, x, y):
                continue
            old_x, old_y, old_z = group.x_percent, group.y_percent, group.z_cm
            group.x_percent, group.y_percent = x, y
            group.z_cm = self._animal_z_cm(group.site, x, y)
            score = self._animal_position_score(group, definition, base_env)
            group.x_percent, group.y_percent, group.z_cm = old_x, old_y, old_z
            reason = self._animal_movement_reason(definition, self._local_animal_environment(group, base_env), x, y, base_env)
            if score > best[0]:
                best = (score, x, y, reason)

        improvement = best[0] - current_score
        restless = food_score < 0.34 or suitability < 0.42 or space_score < 0.34
        threshold = 0.006 if restless else 0.024
        group.last_x_percent = group.x_percent
        group.last_y_percent = group.y_percent
        group.target_x_percent = best[1]
        group.target_y_percent = best[2]
        if improvement <= threshold:
            group.movement_state = "settled"
            group.movement_reason = "conditions acceptable"
            group.distance_moved_cm = 0.0
            return

        old_x, old_y = group.x_percent, group.y_percent
        group.x_percent = best[1]
        group.y_percent = best[2]
        group.z_cm = self._animal_z_cm(group.site, group.x_percent, group.y_percent)
        if group.site.startswith("hardscape:") and group.attached_to:
            surface = self._hardscape_surface_at_xy(self._find_hardscape_item(group.attached_to), group.x_percent, group.y_percent)
            if surface in HARDSCAPE_SURFACES:
                group.attachment_surface = surface or group.attachment_surface
                group.site = self._hardscape_site(group.attached_to, group.attachment_surface)
        group.distance_moved_cm = self._distance_cm(old_x, old_y, group.x_percent, group.y_percent)
        group.movement_state = "relocating" if group.distance_moved_cm > 0.08 else "settled"
        group.movement_reason = best[3]

    def _animal_movement_candidates(self, group: AnimalGroup, definition: AnimalDefinition) -> list[tuple[float, float]]:
        center_x, center_y = self._coord_to_cm(group.x_percent, group.y_percent)
        step = definition.movement_range_cm * (0.55 + self._stable_unit(group.group_id, group.age_ticks, "step") * 0.45)
        start = self._stable_unit(group.group_id, group.age_ticks, "angle") * 360.0
        candidates = [(group.x_percent, group.y_percent)]
        for index in range(8):
            angle = math.radians(start + index * 45.0)
            x, y = self._cm_to_coord(center_x + math.cos(angle) * step, center_y + math.sin(angle) * step)
            try:
                candidates.append(self._validate_xy(x, y))
            except ValueError:
                continue
        if group.site in {"moss", "leaf_litter"} and self.state.plantings:
            target = self._nearest_living_planting(group.x_percent, group.y_percent, definition.movement_range_cm * 3.5)
            if target is not None:
                candidates.append((target.x_percent, target.y_percent))
        if group.site.startswith("hardscape:") and group.attached_to:
            try:
                item = self._find_hardscape_item(group.attached_to)
            except ValueError:
                return candidates
            for surface in HARDSCAPES[item.kind].attach_surfaces:
                candidates.append(self._default_surface_xy(item, surface))
        return candidates

    def _animal_can_occupy_xy(self, group: AnimalGroup, x_percent: float, y_percent: float) -> bool:
        if group.site.startswith("hardscape:") and group.attached_to:
            try:
                item = self._find_hardscape_item(group.attached_to)
            except ValueError:
                return False
            surface = self._hardscape_surface_at_xy(item, x_percent, y_percent)
            return surface in HARDSCAPES[item.kind].attach_surfaces
        if self.state.container.footprint_shape == "round":
            x_cm, y_cm = self._coord_to_cm(x_percent, y_percent)
            radius = (self.state.container.base_area_cm2 / math.pi) ** 0.5
            return math.hypot(x_cm, y_cm) <= radius + 1e-9
        return 0.0 <= x_percent <= 100.0 and 0.0 <= y_percent <= 100.0

    def _animal_position_score(self, group: AnimalGroup, definition: AnimalDefinition, base_env: dict[str, float]) -> float:
        env = self._local_animal_environment(group, base_env)
        preference = self._animal_preference_score(definition, env)
        food = self._animal_food_score(definition, env)
        space = self._animal_space_score(group, definition)
        shelter = clamp(env.get("local_shelter", 0.0))
        damp_fit = self._range_score(env["water"], definition.water_range, 0.25)
        light_penalty = 0.0
        if definition.size_class in {"micro", "tiny"}:
            light_penalty = max(0.0, env["light"] - 0.38) * (0.22 if group.site not in {"soil", "substrate"} else 0.08)
        crowd_penalty = env.get("local_animal_overlap", 0.0) * 0.22
        return preference * 0.34 + food * 0.27 + space * 0.18 + shelter * 0.12 + damp_fit * 0.14 - light_penalty - crowd_penalty

    def _animal_movement_reason(
        self,
        definition: AnimalDefinition,
        old_env: dict[str, float],
        x_percent: float,
        y_percent: float,
        base_env: dict[str, float],
    ) -> str:
        probe = AnimalGroup(group_id="_probe", animal=definition.key, count=max(definition.min_count, 1), x_percent=x_percent, y_percent=y_percent)
        new_env = self._local_animal_environment(probe, base_env)
        if self._animal_food_score(definition, new_env) > self._animal_food_score(definition, old_env) + 0.08:
            return "following food film"
        if new_env.get("local_shelter", 0.0) > old_env.get("local_shelter", 0.0) + 0.12:
            return "seeking cover"
        if new_env["water"] > old_env["water"] + 0.05:
            return "seeking damp pocket"
        if new_env["oxygen"] > old_env["oxygen"] + 0.04:
            return "seeking air pocket"
        if new_env.get("animal_space", 1.0) > old_env.get("animal_space", 1.0) + 0.10:
            return "leaving crowded patch"
        return "foraging"

    def _apply_animal_mortality(
        self,
        group: AnimalGroup,
        suitability: float,
        food_score: float,
        env: dict[str, float],
    ) -> None:
        pressure = 0.0
        pressure += max(0.0, 0.22 - suitability) * 0.18
        pressure += max(0.0, 0.09 - food_score) * 0.12
        pressure += max(0.0, 0.10 - env["oxygen"]) * 0.45
        pressure += max(0.0, env["carbon_dioxide"] - 0.94) * 0.16
        pressure += max(0.0, env["toxicity"] - 0.55) * 0.28
        pressure += max(0.0, 0.30 - env.get("animal_space", 1.0)) * 0.22
        pressure += env.get("local_animal_overlap", 0.0) * 0.12
        if definition.min_count > 1 and group.count < definition.min_count:
            isolation = (definition.min_count - group.count) / max(definition.min_count, 1)
            pressure += 0.012 + isolation * 0.035
        if pressure <= 0:
            group.mortality_pressure = max(0.0, group.mortality_pressure - 0.02)
            return

        group.mortality_pressure += pressure * max(1.0, group.count ** 0.5)
        if group.mortality_pressure >= 1.0:
            loss = min(group.count, int(group.mortality_pressure))
            group.count -= loss
            group.activity_area_cm2 = self._animal_activity_area(ANIMALS[group.animal], group.count) if group.count > 0 else 0.0
            group.mortality_pressure -= loss
            group.reproduction_progress = max(0.0, group.reproduction_progress - loss * 1.5)
            group.crowding_pressure = clamp(group.crowding_pressure + pressure * 1.5, 0.0, 100.0)

    def _mark_animal_group_dead(self, group: AnimalGroup) -> None:
        group.count = 0
        group.survival_state = "dead"
        group.population_trend = "dead"
        group.growth_rate = 0.0
        group.reproduction_progress = 0.0
        group.mortality_pressure = 0.0
        group.activity_area_cm2 = 0.0
        group.movement_state = "gone"
        group.movement_reason = ""
        group.distance_moved_cm = 0.0

    def _animal_preference_score(self, definition: AnimalDefinition, env: dict[str, float]) -> float:
        scores = (
            self._range_score(env["humidity"], definition.humidity_range, 30.0),
            self._range_score(env["temperature"], definition.temperature_range, 8.0),
            self._range_score(env["water"], definition.water_range, 0.32),
            self._range_score(env["oxygen"], definition.oxygen_range, 0.30),
        )
        return min(scores)

    def _animal_food_score(self, definition: AnimalDefinition, env: dict[str, float]) -> float:
        availability = {
            "plants": env["plants"] / 180.0,
            "algae": env["algae"] / 45.0,
            "detritus": max(env["detritus"] / 0.48, env.get("leaf_litter", 0.0) * 0.74),
            "microbes": env["microbes"] / 45.0,
            "mold": env.get("mold", 0.0) * 0.90,
            "biofilm": env.get("biofilm", 0.0) * 1.08,
        }
        score = 0.0
        strongest = 0.0
        for food, weight in definition.diet_weights:
            amount = clamp(availability.get(food, 0.0))
            score += amount * weight
            strongest = max(strongest, amount * min(1.0, weight * 1.8))
        if definition.role == "decomposer":
            maintenance_floor = (
                0.12
                + clamp(env["plants"] / 85.0) * 0.20
                + clamp(env.get("leaf_litter", 0.0)) * 0.12
                + clamp(env.get("biofilm", 0.0)) * 0.10
                + clamp(env.get("mold", 0.0)) * 0.08
            )
            max_floor = 0.30 if definition.size_class == "small" else 0.38
            floor = clamp(maintenance_floor, 0.14, max_floor)
        else:
            floor = 0.18 if definition.role == "micro_consumer" else 0.08
        return clamp(max(score, strongest), floor, 1.0)

    def _apply_local_ecological_interactions(self) -> None:
        s = self.state
        if not s.animal_groups and not s.plantings:
            return

        base_env = self._life_environment()
        for group in s.animal_groups:
            if group.count <= 0 or group.survival_state == "dead":
                continue
            definition = ANIMALS[group.animal]
            env = self._local_animal_environment(group, base_env)
            activity = clamp(0.12 + group.visible_activity / 100.0) * definition.feeding_rate
            count_signal = max(1.0, group.count ** 0.5)

            if definition.detritus_processing > 0.0:
                processing = definition.detritus_processing * activity * count_signal * 0.00075
                s.detritus = max(0.0, s.detritus - processing * 0.34)
                s.leaf_litter_cover = max(0.0, s.leaf_litter_cover - processing * 0.72)

            if definition.mold_control > 0.0:
                mold_grazing = definition.mold_control * activity * count_signal * 0.00095
                s.mold_pressure = max(0.0, s.mold_pressure - mold_grazing)

            if definition.role in {"micro_consumer", "small_consumer"}:
                film_grazing = (0.30 + definition.mold_control) * activity * count_signal * 0.0011
                s.biofilm = max(0.0, s.biofilm - film_grazing)

            food_score = self._animal_food_score(definition, env)
            shortage = clamp((0.40 - food_score) / 0.40)
            if definition.plant_risk > 0.0 and shortage > 0.0:
                target = self._nearest_living_planting(group.x_percent, group.y_percent, definition.movement_range_cm * 1.8)
                if target is not None:
                    damage = definition.plant_risk * definition.feeding_rate * (0.35 + shortage) * count_signal * 0.85
                    self._mark_plant_interaction(target, damage, definition.food_source, definition.display_name)

        self._apply_visible_mold_contact()

    def _nearest_living_planting(
        self,
        x_percent: float,
        y_percent: float,
        max_distance_cm: float | None = None,
    ) -> Planting | None:
        best: tuple[float, Planting] | None = None
        for planting in self.state.plantings:
            if planting.status == "dead" or planting.survival_state == "dead" or planting.health <= 0.0:
                continue
            distance = self._distance_cm(x_percent, y_percent, planting.x_percent, planting.y_percent)
            if max_distance_cm is not None and distance > max_distance_cm:
                continue
            if best is None or distance < best[0]:
                best = (distance, planting)
        return best[1] if best is not None else None

    def _mark_plant_interaction(
        self,
        planting: Planting,
        damage_percent: float,
        food_source: str,
        animal_name: str,
    ) -> None:
        damage = max(0.0, damage_percent)
        if damage <= 0.0:
            return
        planting.visible_damage_percent = clamp(planting.visible_damage_percent + damage, 0.0, 100.0)
        planting.health = max(0.0, planting.health - damage * 0.020)
        if "root" in food_source:
            planting.root_health = max(0.0, planting.root_health - damage * 0.055)
            planting.root_tip_count = max(0, planting.root_tip_count - max(1, int(round(damage / 12.0))))
            planting.last_interaction = f"{animal_name} grazing has marked fine roots"
        elif "plant" in food_source or "tissue" in food_source:
            planting.damaged_leaf_count += max(1, int(round(damage / 18.0)))
            planting.last_interaction = f"{animal_name} has nibbled tender edges"
        else:
            planting.last_interaction = f"{animal_name} has grazed nearby films"
        self._refresh_plant_canopy_density(planting)

    def _apply_visible_mold_contact(self) -> None:
        s = self.state
        if s.mold_pressure <= 0.50 or not s.plantings:
            return
        candidates: list[tuple[float, Planting]] = []
        for planting in s.plantings:
            if planting.status == "dead" or planting.survival_state == "dead" or planting.health <= 0.0:
                continue
            local = self._local_lowland_factor(planting.x_percent, planting.y_percent)
            shelter = self._local_hardscape_effects(planting.x_percent, planting.y_percent)["shelter"]
            wood_bonus = 0.16 if planting.attached_to and any(
                item.item_id == planting.attached_to and HARDSCAPES[item.kind].category == "wood"
                for item in s.hardscape_items
            ) else 0.0
            score = s.mold_pressure * 0.55 + s.leaf_litter_cover * 0.24 + s.surface_wetness * 0.18 + local * 0.16 + shelter * 0.18 + wood_bonus
            candidates.append((score, planting))
        if not candidates:
            return
        score, target = max(candidates, key=lambda item: item[0])
        if score <= 0.70:
            return
        contact = clamp((score - 0.68) * 6.0, 0.0, 2.6)
        target.mold_contact_percent = clamp(target.mold_contact_percent + contact, 0.0, 100.0)
        target.health = max(0.0, target.health - contact * 0.010)
        if contact > 0.15:
            if contact > 1.0:
                target.damaged_leaf_count += 1
            target.last_interaction = "pale fuzz is touching lower growth"
            self._refresh_plant_canopy_density(target)

    def _animal_can_reproduce(
        self,
        definition: AnimalDefinition,
        group: AnimalGroup,
        suitability: float,
        food_score: float,
        space_score: float,
    ) -> bool:
        if group.age_ticks < 336:
            return False
        if group.count < definition.min_reproductive_count:
            return False
        if group.count >= definition.max_reasonable_count:
            return False
        if suitability < 0.65 or food_score < 0.45 or space_score < 0.45:
            return False
        return self.volume_profile()["free_container_ml"] >= definition.space_ml_per_count * max(12, group.count * 0.16)

    def _try_animal_birth(self, definition: AnimalDefinition, group: AnimalGroup) -> None:
        remaining = definition.max_reasonable_count - group.count
        if remaining <= 0:
            group.reproduction_progress = 75.0
            group.population_trend = "crowded"
            return

        addition = max(1, int(round(group.count * 0.08)))
        addition = min(addition, remaining, max(1, definition.default_count // 2))
        old_count = group.count
        old_area = group.activity_area_cm2
        group.count += addition
        group.activity_area_cm2 = self._animal_activity_area(definition, group.count)
        try:
            self._raise_if_container_volume_overflows()
        except ValueError:
            group.count = old_count
            group.activity_area_cm2 = old_area
            group.reproduction_progress = 80.0
            group.population_trend = "crowded"
            group.crowding_pressure = clamp(group.crowding_pressure + 8.0, 0.0, 100.0)
            return
        group.reproduction_progress = 0.0
        group.population_trend = "reproducing"

    def _living_state_from_score(self, score: float, health: float) -> str:
        if health < 25.0 or score < 0.18:
            return "declining"
        if score < 0.35:
            return "stressed"
        if score < 0.55:
            return "stable"
        if score < 0.78:
            return "settling"
        return "thriving"

    def _range_score(self, value: float, preferred: tuple[float, float], tolerance: float) -> float:
        low, high = preferred
        if low <= value <= high:
            return 1.0
        tolerance = max(tolerance, 1e-9)
        if value < low:
            return clamp(1.0 - (low - value) / tolerance)
        return clamp(1.0 - (value - high) / tolerance)

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
        s.liquid_water_ml = max(0.0, s.liquid_water_ml)
        s.vapor_water_ml = max(0.0, min(s.vapor_water_ml, s.container.capacity_ml * 0.08))
        s.condensation_ml = max(0.0, min(s.condensation_ml, s.container.capacity_ml * 0.05))
        s.surface_wetness = clamp(s.surface_wetness)
        s.biofilm = clamp(s.biofilm)
        s.mold_pressure = clamp(s.mold_pressure)
        s.root_zone_oxygen = clamp(s.root_zone_oxygen)
        s.leaf_litter_cover = clamp(s.leaf_litter_cover)
        s.window_light_mode = canonical_window_light_mode(s.window_light_mode)
        s.calendar_start_day_of_year = int(clamp(float(s.calendar_start_day_of_year), 1.0, 365.0))
        s.calendar_day_of_year = int(clamp(float(s.calendar_day_of_year), 1.0, 365.0))
        s.season = self._season_for_day(s.calendar_day_of_year)
        s.weather_mode = canonical_weather_mode(s.weather_mode)
        if s.weather_state not in WEATHER_PROFILES:
            s.weather_state = "clear"
        s.window_light = clamp(s.window_light)
        s.window_direct_light = clamp(s.window_direct_light)
        s.window_diffuse_light = clamp(s.window_diffuse_light)
        s.moss_lamp_light = clamp(s.moss_lamp_light)
        s.moss_lamp_intensity = clamp(s.moss_lamp_intensity)
        if s.umbrella_enabled:
            if s.umbrella_coverage_percent < UMBRELLA_MIN_COVERAGE:
                s.umbrella_coverage_percent = UMBRELLA_DEFAULT_COVERAGE
            s.umbrella_coverage_percent = clamp(
                s.umbrella_coverage_percent,
                UMBRELLA_MIN_COVERAGE,
                UMBRELLA_MAX_COVERAGE,
            )
        s.umbrella_x_percent = clamp(s.umbrella_x_percent, 0.0, 100.0)
        s.umbrella_y_percent = clamp(s.umbrella_y_percent, 0.0, 100.0)
        s.umbrella_angle_deg = self._normalize_degrees(s.umbrella_angle_deg)
        s.umbrella_tilt_deg = clamp(s.umbrella_tilt_deg, -80.0, 80.0)
        s.placement_heat_bias = max(0.0, s.placement_heat_bias)
        s.moss_lamp_start_hour = int(clamp(float(s.moss_lamp_start_hour), 0.0, float(self.config.day_length - 1)))
        s.moss_lamp_duration_hours = int(clamp(float(s.moss_lamp_duration_hours), 1.0, float(self.config.day_length)))
        for pop in ("plants", "algae", "grazers", "microbes"):
            setattr(s, pop, max(0.0, getattr(s, pop)))
        for planting in s.plantings:
            planting.root_health = clamp(planting.root_health / 100.0) * 100.0
            planting.footprint_aspect_ratio = clamp(planting.footprint_aspect_ratio, 1.0, 4.5)
            planting.visible_damage_percent = clamp(planting.visible_damage_percent, 0.0, 100.0)
            planting.mold_contact_percent = clamp(planting.mold_contact_percent, 0.0, 100.0)
            planting.stem_count = max(0, int(planting.stem_count))
            planting.leaf_count = max(0, int(planting.leaf_count))
            planting.root_anchor_count = max(0, int(planting.root_anchor_count))
            planting.damaged_leaf_count = max(0, int(planting.damaged_leaf_count))
            planting.new_growth_count = max(0, int(planting.new_growth_count))
            planting.root_tip_count = max(0, int(planting.root_tip_count))
            planting.flower_count = max(0, int(planting.flower_count))
            planting.canopy_density_percent = clamp(planting.canopy_density_percent, 0.0, 100.0)
            planting.attachment_contact_area_cm2 = max(0.0, planting.attachment_contact_area_cm2)
        for group in s.animal_groups:
            group.distance_moved_cm = max(0.0, group.distance_moved_cm)
            group.target_x_percent = clamp(group.target_x_percent, 0.0, 100.0)
            group.target_y_percent = clamp(group.target_y_percent, 0.0, 100.0)

    def _collect_events(self, events: list[str]) -> None:
        s = self.state
        profile = self.volume_profile()
        if s.oxygen < 0.22:
            events.append("O2_CRASH")
        if s.carbon_dioxide > 0.82:
            events.append("CO2_SATURATION")
        if s.water < 0.25:
            events.append("DROUGHT")
        if s.condensation_ml > 3.2:
            events.append("CONDENSATION_BEADS")
        if s.condensation_ml < 0.4 and s.surface_wetness < 0.22 and s.water < 0.42:
            events.append("GLASS_DRYING")
        if s.window_light > 0.55 and s.sun_altitude_deg > 18.0:
            events.append("WINDOW_BRIGHT_SIDE")
        if s.window_direct_light > 0.26 and s.window_direct_light > s.window_diffuse_light * 1.45:
            events.append("DIRECT_SUN_PATCH")
        if s.window_diffuse_light > 0.18 and s.window_diffuse_light > s.window_direct_light * 1.45:
            events.append("DIFFUSE_WINDOW_LIGHT")
        if s.weather_state in {"overcast", "rainy"} and s.window_light > 0.08:
            events.append("CLOUD_MUTED_LIGHT")
        if s.season == "winter" and s.hour >= 15 and s.window_light < 0.12 and s.moss_lamp_light <= 0.03:
            events.append("SHORT_WINTER_DAY")
        if s.season == "summer" and s.hour >= 18 and s.window_light > 0.14:
            events.append("LONG_SUMMER_LIGHT")
        if s.placement_heat_bias > 0.65 and (s.condensation_ml < 1.5 or s.surface_wetness < 0.45):
            events.append("WINDOW_WARM_EDGE")
        if s.moss_lamp_light > 0.16:
            events.append("MOSS_LAMP_GLOW")
        if s.moss_lamp_light > 0.34 and s.surface_wetness < 0.45:
            events.append("MOSS_LAMP_DRY_EDGE")
        if s.light > 0.40 and s.sun_altitude_deg > 12.0 and s.hardscape_items:
            events.append("SHADE_LINE_VISIBLE")
        if profile["free_water_ml"] > 5.0:
            events.append("WATER_POOLING")
        if profile["pore_capacity_ml"] > 0 and profile["water_in_pores_ml"] / profile["pore_capacity_ml"] > 0.90:
            events.append("SOIL_WATERLOGGED")
        if s.root_zone_oxygen < 0.26 and s.plantings:
            events.append("ROOT_ZONE_DULL")
        if s.surface_wetness > 0.78:
            events.append("SURFACE_GLISTENING")
        if s.algae > self._algae_carrying_capacity() * 1.35 and (s.surface_wetness > 0.35 or s.biofilm > 0.28):
            events.append("ALGAE_FILM")
        if s.biofilm > 0.58:
            events.append("BIOFILM_FILM")
        if s.mold_pressure > 0.58:
            events.append("MOLD_PATCHES")
        if s.leaf_litter_cover > 0.62:
            events.append("LITTER_MAT")
        if s.nutrients < 0.16:
            events.append("NUTRIENT_LIMIT")
        if s.detritus > 0.62:
            events.append("ROT_SPIKE")
        if s.toxicity > 0.36:
            events.append("TOXICITY_RISE")
        if (s.plantings and self.living_planting_count() == 0) or (not s.plantings and s.plants < 6.0):
            events.append("PLANT_COLLAPSE")
        if not s.animal_groups and not s.plantings and s.grazers < 0.8:
            events.append("GRAZER_LOSS")
        if self.hardscape_profile()["plantable_percent"] < 35.0:
            events.append("PLANTING_SPACE_LIMIT")
        if any(planting.offspring_potential > 0 for planting in s.plantings):
            events.append("PROPAGATION_READY")
        if any(group.crowding_pressure > 60.0 for group in s.animal_groups) or self.animal_spatial_profile()["habitat_space_score"] < 0.35:
            events.append("ANIMAL_CROWDING")
        if any(planting.population_pressure > 45.0 for planting in s.plantings):
            events.append("PLANT_SPATIAL_PRESSURE")
        if any(planting.visible_damage_percent > 18.0 for planting in s.plantings if planting.survival_state != "dead"):
            events.append("VISIBLE_PLANT_GRAZING")
        if any(planting.mold_contact_percent > 20.0 for planting in s.plantings if planting.survival_state != "dead"):
            events.append("MOLD_TOUCHING_PLANT")
        surface_ecology = self.hardscape_surface_ecology()
        if s.biofilm > 0.42 and surface_ecology["biofilm"] > 0.08:
            events.append("HARDSCAPE_FILM")
        if s.mold_pressure > 0.42 and surface_ecology["mold"] > 0.10:
            events.append("PROTECTED_SURFACE_MOLD")
        base_env = self._life_environment()
        if any(
            (local_env := self._local_life_environment(planting, base_env)).get("lowland", 0.5) > 0.82
            and local_env["aeration"] < 4.0
            for planting in s.plantings
            if planting.survival_state != "dead"
        ):
            events.append("LOW_SPOT_WET")
