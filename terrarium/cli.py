from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

from .model import SimulationConfig, Terrarium, TerrariumState
from .render import render_dashboard, render_log_line


POOLS = {"water", "nutrients", "oxygen", "carbon_dioxide", "detritus", "toxicity", "temperature", "light_intensity"}
POPS = {"plants", "algae", "grazers", "microbes"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="terrarium",
        description="Closed terrarium ecosystem simulator.",
    )
    add_initial_state_args(parser)

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
    config = SimulationConfig(light_intensity=max(0.0, min(1.0, args.light)))
    state = TerrariumState(
        water=max(0.0, min(1.0, args.water)),
        nutrients=max(0.0, min(1.0, args.nutrients)),
        plants=max(0.0, args.plants),
        algae=max(0.0, args.algae),
        grazers=max(0.0, args.grazers),
        microbes=max(0.0, args.microbes),
        seed=args.seed,
    )
    return Terrarium(state=state, config=config, seed=args.seed)


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


def command_shell(args: argparse.Namespace) -> int:
    if args.load:
        sim = Terrarium.from_json(args.load.read_text(encoding="utf-8"))
    else:
        sim = make_sim(args)

    print("Terrarium CLI shell. Type 'help' for commands.")
    print(render_dashboard(sim))
    while True:
        try:
            raw = input("terrarium> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not raw:
            continue

        parts = raw.split()
        command = parts[0].lower()
        try:
            if command in {"quit", "exit", "q"}:
                return 0
            if command in {"help", "h", "?"}:
                print_help()
            elif command in {"status", "s"}:
                print(render_dashboard(sim))
            elif command == "step":
                ticks = int(parts[1]) if len(parts) > 1 else 1
                sim.run(ticks)
                print(render_dashboard(sim))
            elif command == "run":
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
                sim.set_pool(name, float(parts[2]))
                print(render_dashboard(sim, compact=True))
            elif command == "add":
                if len(parts) != 3:
                    raise ValueError("usage: add <population> <amount>")
                name = normalize_name(parts[1])
                if name not in POPS:
                    raise ValueError(f"population must be one of: {', '.join(sorted(POPS))}")
                sim.add_population(name, float(parts[2]))
                print(render_dashboard(sim, compact=True))
            elif command == "save":
                if len(parts) != 2:
                    raise ValueError("usage: save <path>")
                Path(parts[1]).write_text(sim.state.to_json() + "\n", encoding="utf-8")
                print(f"saved {parts[1]}")
            else:
                print(f"unknown command: {command}")
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
    return 0


def normalize_name(name: str) -> str:
    return name.lower().replace("-", "_")


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
                "  save <path>            save current state JSON",
                "  quit                   exit",
            ]
        )
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        return command_run(args)
    return command_shell(args)
