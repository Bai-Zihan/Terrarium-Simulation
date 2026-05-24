import io
import json
import os
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from terrarium.cli import (
    build_parser,
    command_shell,
    handle_bottle_command,
    handle_container_command,
    handle_hardscape_command,
    handle_moisten_command,
    handle_animal_command,
    handle_placement_command,
    handle_plant_command,
    handle_seal_command,
    handle_spray_command,
    handle_space_command,
    handle_substrate_command,
    has_crafting_content,
    make_followup_sim,
    SurvivalManager,
    parse_height,
    parse_ml,
    parse_count,
    parse_percent,
    parse_substrate_mix,
    split_command_batch,
    render_shell_home,
    print_hardscape_catalog,
    print_animal_catalog,
    print_container_catalog,
    print_plant_catalog,
    print_substrate_catalog,
)
from terrarium.model import Terrarium


class CliParserTests(unittest.TestCase):
    def test_no_subcommand_starts_shell_mode(self) -> None:
        args = build_parser().parse_args([])

        self.assertIsNone(args.command)

    def test_no_subcommand_can_open_shell_home(self) -> None:
        with TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            inputs = iter(["quit"])
            output = io.StringIO()

            with (
                patch.dict(os.environ, {"TERRARIUM_HOME": temp_dir}),
                patch("builtins.input", lambda prompt="": next(inputs)),
                redirect_stdout(output),
            ):
                exit_code = command_shell(build_parser().parse_args([]))

        self.assertEqual(exit_code, 0)
        text = output.getvalue()
        self.assertIn("TERRARIUM", text)
        self.assertIn("BOTTLES running 0/0", text)
        self.assertIn("make [name] starts a new bottle", text)

    def test_command_batch_splits_semicolons_and_lines(self) -> None:
        commands = split_command_batch(
            """
            # starter recipe
            container set tiny_vial; substrate add drainage 1cm leca=100
            moisten 8ml

            spray 2; seal
            """
        )

        self.assertEqual(
            commands,
            [
                "container set tiny_vial",
                "substrate add drainage 1cm leca=100",
                "moisten 8ml",
                "spray 2",
                "seal",
            ],
        )

    def test_shell_source_queues_recipe_commands(self) -> None:
        with TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            recipe = Path(temp_dir) / "recipe.txt"
            recipe.write_text("make; container set tiny_vial; moisten 5ml\n", encoding="utf-8")
            inputs = iter([f"source {recipe}", "quit"])
            output = io.StringIO()

            with (
                patch.dict(os.environ, {"TERRARIUM_HOME": temp_dir}),
                patch("builtins.input", lambda prompt="": next(inputs)),
                redirect_stdout(output),
            ):
                exit_code = command_shell(build_parser().parse_args(["shell"]))

        text = output.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("queued 3 command(s)", text)
        self.assertIn("Started a new open terrarium", text)
        self.assertIn("selected container tiny_vial", text)
        self.assertIn("moistened soil with 5.0 ml", text)

    def test_shell_mesh_alias_places_screen_layer(self) -> None:
        with TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            inputs = iter(["make", "mesh", "quit"])
            output = io.StringIO()

            with (
                patch.dict(os.environ, {"TERRARIUM_HOME": temp_dir}),
                patch("builtins.input", lambda prompt="": next(inputs)),
                redirect_stdout(output),
            ):
                exit_code = command_shell(build_parser().parse_args([]))

        text = output.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("placed mesh screen layer", text)

    def test_complex_recipe_can_be_pasted_and_sealed(self) -> None:
        recipe = """
        make complex_bottle
        container set wide_jar
        placement window east
        placement face 90
        placement lamp 230 0.22 schedule 18-22
        substrate add drainage 1.8cm leca=60,pumice=40 slope_x=0.4 slope_y=-0.2
        substrate add purification 0.6cm activated_charcoal=100
        mesh
        substrate add soil 4.2cm peat_moss=45,compost=20,sphagnum_moss=20,perlite=15 slope_x=1.1 slope_y=-0.6
        substrate add amendment 0.8cm akadama=45,kanuma=25,perlite=30 slope_x=0.8 slope_y=-0.4
        moisten 85ml
        spray 8
        hardscape place driftwood 14% center arch x=48 y=54 angle=35 tilt=18
        hardscape place slate 9% east leaning_west x=70 y=48 angle=115 tilt=24
        hardscape place river_stone 5% northwest flat x=28 y=68 angle=20
        plant add cushion_moss 5% hardscape:H01:groove
        plant add rabbit_foot_fern 4% hardscape:H01:side
        plant add fittonia_mini 5% surface x=18 y=30
        plant add mini_masdevallia 4% hardscape:H02:side
        plant add sheet_moss 6% surface x=55 y=25
        placement umbrella 120% south leaning_north
        animal add springtail 35 soil x=42 y=48
        animal add dwarf_white_isopod 6 leaf_litter x=55 y=58
        space status
        seal
        """
        with TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            inputs = iter([recipe, "quit"])
            output = io.StringIO()

            with (
                patch.dict(os.environ, {"TERRARIUM_HOME": temp_dir}),
                patch("builtins.input", lambda prompt="": next(inputs)),
                redirect_stdout(output),
            ):
                exit_code = command_shell(build_parser().parse_args([]))

        text = output.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertNotIn("Nothing changed", text)
        self.assertIn("planted P05 Sheet moss", text)
        self.assertIn("added A02 Dwarf white isopod x6", text)
        self.assertIn("Auto-survival started as B01", text)

    def test_sealed_bottles_are_persisted_and_loaded_on_next_shell(self) -> None:
        with TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            first_inputs = iter(
                [
                    "make saved_bottle",
                    "plant add fittonia_mini 5%",
                    "animal add springtail 30 soil",
                    "seal",
                    "quit",
                ]
            )
            first_output = io.StringIO()

            with (
                patch.dict(os.environ, {"TERRARIUM_HOME": temp_dir}),
                patch("builtins.input", lambda prompt="": next(first_inputs)),
                redirect_stdout(first_output),
            ):
                first_exit = command_shell(build_parser().parse_args([]))

            second_inputs = iter(["bottles", "quit"])
            second_output = io.StringIO()
            with (
                patch.dict(os.environ, {"TERRARIUM_HOME": temp_dir}),
                patch("builtins.input", lambda prompt="": next(second_inputs)),
                redirect_stdout(second_output),
            ):
                second_exit = command_shell(build_parser().parse_args([]))

        self.assertEqual(first_exit, 0)
        self.assertEqual(second_exit, 0)
        self.assertIn("Auto-survival started as B01", first_output.getvalue())
        text = second_output.getvalue()
        self.assertIn("Loaded 1 saved terrarium(s)", text)
        self.assertIn("B01 saved_bottle running", text)
        self.assertIn("make [name] starts a new bottle", text)

    def test_standalone_bottle_saves_are_imported_then_persisted(self) -> None:
        with TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            home_dir = Path(temp_dir) / "home"
            import_dir = Path(temp_dir) / "imports"
            import_dir.mkdir()
            sim = Terrarium(seed=7)
            sim.add_planting("fittonia_mini", 5.0)
            sim.add_animals("springtail", 30)
            sim.seal()
            (import_dir / "legacy_bottle.json").write_text(sim.state.to_json() + "\n", encoding="utf-8")

            first_inputs = iter(["bottles", "pause B01", "quit"])
            first_output = io.StringIO()
            env = {"TERRARIUM_HOME": str(home_dir), "TERRARIUM_IMPORT_DIR": str(import_dir)}
            with (
                patch.dict(os.environ, env),
                patch("builtins.input", lambda prompt="": next(first_inputs)),
                redirect_stdout(first_output),
            ):
                first_exit = command_shell(build_parser().parse_args([]))

            second_inputs = iter(["bottles", "wake B01", "discard B01", "bottles", "quit"])
            second_output = io.StringIO()
            with (
                patch.dict(os.environ, env),
                patch("builtins.input", lambda prompt="": next(second_inputs)),
                redirect_stdout(second_output),
            ):
                second_exit = command_shell(build_parser().parse_args([]))

            third_inputs = iter(["bottles", "quit"])
            third_output = io.StringIO()
            with (
                patch.dict(os.environ, env),
                patch("builtins.input", lambda prompt="": next(third_inputs)),
                redirect_stdout(third_output),
            ):
                third_exit = command_shell(build_parser().parse_args([]))

        self.assertEqual(first_exit, 0)
        self.assertEqual(second_exit, 0)
        self.assertEqual(third_exit, 0)
        first_text = first_output.getvalue()
        self.assertIn("Imported 1 standalone bottle save(s)", first_text)
        self.assertIn("B01 legacy_bottle running", first_text)
        self.assertIn("B01 is now paused", first_text)
        second_text = second_output.getvalue()
        self.assertIn("Loaded 1 saved terrarium(s)", second_text)
        self.assertNotIn("Imported 1 standalone bottle save(s)", second_text)
        self.assertIn("B01 legacy_bottle paused", second_text)
        self.assertIn("B01 is now running", second_text)
        self.assertIn("B01 legacy_bottle removed from the bottle list", second_text)
        self.assertIn("BOTTLES running 0/0", second_text)
        third_text = third_output.getvalue()
        self.assertNotIn("Imported 1 standalone bottle save(s)", third_text)
        self.assertIn("BOTTLES running 0/0", third_text)

    def test_exported_managed_bottle_is_not_imported_as_duplicate(self) -> None:
        with TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            home_dir = Path(temp_dir) / "home"
            import_dir = Path(temp_dir) / "imports"
            import_dir.mkdir()
            export_path = import_dir / "again.json"
            env = {"TERRARIUM_HOME": str(home_dir), "TERRARIUM_IMPORT_DIR": str(import_dir)}

            first_inputs = iter(["make stable", "plant add fittonia_mini 5%", "seal", "quit"])
            first_output = io.StringIO()
            with (
                patch.dict(os.environ, env),
                patch("builtins.input", lambda prompt="": next(first_inputs)),
                redirect_stdout(first_output),
            ):
                first_exit = command_shell(build_parser().parse_args([]))

            second_inputs = iter([f"save {export_path}", "quit"])
            second_output = io.StringIO()
            with (
                patch.dict(os.environ, env),
                patch("builtins.input", lambda prompt="": next(second_inputs)),
                redirect_stdout(second_output),
            ):
                second_exit = command_shell(build_parser().parse_args([]))

            third_inputs = iter(["bottles", "quit"])
            third_output = io.StringIO()
            with (
                patch.dict(os.environ, env),
                patch("builtins.input", lambda prompt="": next(third_inputs)),
                redirect_stdout(third_output),
            ):
                third_exit = command_shell(build_parser().parse_args([]))

        self.assertEqual(first_exit, 0)
        self.assertEqual(second_exit, 0)
        self.assertEqual(third_exit, 0)
        self.assertIn("saved", second_output.getvalue())
        third_text = third_output.getvalue()
        self.assertIn("Loaded 1 saved terrarium(s)", third_text)
        self.assertNotIn("Imported 1 standalone bottle save(s)", third_text)
        self.assertIn("BOTTLES running 1/1", third_text)
        self.assertNotIn("B02", third_text)

    def test_duplicate_saved_bottle_entries_are_collapsed_on_load(self) -> None:
        with TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            home_dir = Path(temp_dir) / "home"
            import_dir = Path(temp_dir) / "imports"
            home_dir.mkdir()
            import_dir.mkdir()
            export_path = import_dir / "again.json"
            sim = Terrarium(seed=7)
            sim.add_planting("fittonia_mini", 5.0)
            sim.seal()
            state = json.loads(sim.state.to_json())
            export_path.write_text(sim.state.to_json() + "\n", encoding="utf-8")
            game_state = {
                "version": 1,
                "deleted_sources": [],
                "bottles": [
                    {"name": "stable_umbrella_test", "running": True, "source": "", "state": state},
                    {
                        "name": "again",
                        "running": True,
                        "source": str(export_path.resolve()),
                        "state": state,
                    },
                ],
            }
            (home_dir / "game.json").write_text(json.dumps(game_state), encoding="utf-8")
            env = {"TERRARIUM_HOME": str(home_dir), "TERRARIUM_IMPORT_DIR": str(import_dir)}
            inputs = iter(["bottles", "quit"])
            output = io.StringIO()
            with (
                patch.dict(os.environ, env),
                patch("builtins.input", lambda prompt="": next(inputs)),
                redirect_stdout(output),
            ):
                exit_code = command_shell(build_parser().parse_args([]))

        self.assertEqual(exit_code, 0)
        text = output.getvalue()
        self.assertIn("Loaded 1 saved terrarium(s)", text)
        self.assertNotIn("Imported 1 standalone bottle save(s)", text)
        self.assertIn("BOTTLES running 1/1", text)
        self.assertIn("B01 stable_umbrella_test", text)
        self.assertNotIn("B02", text)

    def test_shell_home_draws_small_terminal_interface(self) -> None:
        sim = Terrarium(seed=1)
        home = render_shell_home(sim, SurvivalManager())

        self.assertIn("TERRARIUM", home)
        self.assertIn("closed ecosystem terminal game", home)
        self.assertIn("quick:", home)
        self.assertIn("status opens the full dashboard", home)
        self.assertIn("/       \\", home)

    def test_shell_home_lists_multiple_bottles_without_cutting_stability(self) -> None:
        manager = SurvivalManager()
        first = Terrarium(seed=1)
        first.add_planting("fittonia_mini", 5.0)
        first.seal()
        second = Terrarium(seed=2)
        second.add_planting("cushion_moss", 5.0)
        second.seal()
        manager.register(first, "complex_test_with_a_name_that_needs_shortening")
        manager.register(second, "test_bottle")

        with patch("terrarium.cli.get_terminal_size", return_value=os.terminal_size((88, 24))):
            home = render_shell_home(None, manager)

        self.assertIn("BOTTLES running 2/2", home)
        self.assertRegex(home, r"B01 .*stability \d{3}/100")
        self.assertRegex(home, r"B02 .*stability \d{3}/100")
        self.assertNotIn("/10 ", home)

    def test_seed_can_appear_before_subcommand(self) -> None:
        args = build_parser().parse_args(["--seed", "42", "run", "--ticks", "2"])

        self.assertEqual(args.seed, 42)
        self.assertEqual(args.command, "run")

    def test_seed_can_appear_after_subcommand(self) -> None:
        args = build_parser().parse_args(["run", "--ticks", "2", "--seed", "42"])

        self.assertEqual(args.seed, 42)
        self.assertEqual(args.command, "run")

    def test_container_option_can_appear_after_subcommand(self) -> None:
        args = build_parser().parse_args(["shell", "--container", "horizontal_jar"])

        self.assertEqual(args.container, "horizontal_jar")

    def test_container_command_selects_before_crafting(self) -> None:
        sim = Terrarium(seed=1)
        output = io.StringIO()

        with redirect_stdout(output):
            handle_container_command(sim, ["set", "tiny_vial"])

        text = output.getvalue()
        self.assertIn("selected container tiny_vial", text)
        self.assertEqual(sim.state.container.capacity_ml, 150.0)

    def test_container_command_guides_after_crafting_started(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_substrate("soil", 1.0, {"peat_moss": 100})
        output = io.StringIO()

        with redirect_stdout(output):
            handle_container_command(sim, ["set", "wide_jar"])

        text = output.getvalue()
        self.assertIn("Nothing changed", text)
        self.assertIn("Choose the container first", text)

    def test_container_catalog_lists_horizontal_and_tiny_options(self) -> None:
        output = io.StringIO()

        with redirect_stdout(output):
            print_container_catalog()

        text = output.getvalue()
        self.assertIn("tiny_vial", text)
        self.assertIn("horizontal_jar", text)

    def test_substrate_height_accepts_percent_of_container(self) -> None:
        self.assertAlmostEqual(parse_height("10%", 16.7), 1.67)

    def test_substrate_mix_accepts_percent_entries(self) -> None:
        mix = parse_substrate_mix("peat-moss=50, compost=30%, perlite=20")

        self.assertEqual(mix["peat_moss"], 50)
        self.assertEqual(mix["compost"], 30)
        self.assertEqual(mix["perlite"], 20)

    def test_percent_parser_accepts_optional_percent_symbol(self) -> None:
        self.assertEqual(parse_percent("8%"), 8.0)
        self.assertEqual(parse_percent("8"), 8.0)

    def test_ml_parser_accepts_optional_ml_suffix(self) -> None:
        self.assertEqual(parse_ml("30ml"), 30.0)
        self.assertEqual(parse_ml("30"), 30.0)

    def test_count_parser_accepts_whole_numbers(self) -> None:
        self.assertEqual(parse_count("5"), 5)

    def test_substrate_command_allows_arbitrary_order(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_substrate("soil", 2.0, {"peat_moss": 100})
        output = io.StringIO()

        with redirect_stdout(output):
            handle_substrate_command(sim, ["add", "purification", "1cm", "activated_charcoal=100"])

        text = output.getvalue()
        self.assertIn("added 1.00 cm to purification", text)
        self.assertEqual([layer.layer_kind for layer in sim.state.substrate_layers], ["soil", "purification"])

    def test_substrate_command_accepts_slope_option(self) -> None:
        sim = Terrarium(seed=1)
        output = io.StringIO()

        with redirect_stdout(output):
            handle_substrate_command(sim, ["add", "soil", "4cm", "peat_moss=100", "slope=0.6,-0.2"])

        text = output.getvalue()
        self.assertIn("slope +0.60,-0.20cm", text)
        self.assertAlmostEqual(sim.state.substrate_layers[0].slope_x_cm, 0.6)
        self.assertAlmostEqual(sim.state.substrate_layers[0].slope_y_cm, -0.2)

    def test_substrate_command_accepts_named_slope_axes_after_mixture(self) -> None:
        sim = Terrarium(seed=1)
        output = io.StringIO()

        with redirect_stdout(output):
            handle_substrate_command(
                sim,
                [
                    "add",
                    "soil",
                    "4.2cm",
                    "peat_moss=45,compost=20,sphagnum_moss=20,perlite=15",
                    "slope_x=1.1",
                    "slope_y=-0.6",
                ],
            )

        text = output.getvalue()
        self.assertIn("added 4.20 cm to soil", text)
        self.assertAlmostEqual(sim.state.substrate_layers[0].slope_x_cm, 1.1)
        self.assertAlmostEqual(sim.state.substrate_layers[0].slope_y_cm, -0.6)

    def test_substrate_command_reports_bad_mix_as_retry_hint(self) -> None:
        sim = Terrarium(seed=1)
        output = io.StringIO()

        with redirect_stdout(output):
            handle_substrate_command(sim, ["add", "drainage", "2cm", "leca=70,pumice=20"])

        text = output.getvalue()
        self.assertIn("Nothing changed", text)
        self.assertIn("add up to 100", text)
        self.assertEqual(sim.state.substrate_layers, [])

    def test_substrate_catalog_does_not_list_chemistry_for_materials(self) -> None:
        output = io.StringIO()

        with redirect_stdout(output):
            print_substrate_catalog()

        text = output.getvalue()
        self.assertIn("water_ret=", text)
        self.assertIn("aeration=", text)
        self.assertNotIn("pH=", text)
        self.assertNotIn("nutrients=", text)

    def test_substrate_mesh_command_can_start_stack(self) -> None:
        sim = Terrarium(seed=1)
        output = io.StringIO()

        with redirect_stdout(output):
            handle_substrate_command(sim, ["mesh"])

        text = output.getvalue()
        self.assertIn("placed mesh screen layer", text)
        self.assertTrue(sim.state.mesh_barrier)
        self.assertEqual(sim.mesh_layer_count(), 1)

    def test_substrate_mesh_command_installs_barrier(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_substrate("drainage", 2.0, {"leca": 100})
        output = io.StringIO()

        with redirect_stdout(output):
            handle_substrate_command(sim, ["mesh"])

        text = output.getvalue()
        self.assertIn("placed mesh screen layer", text)
        self.assertTrue(sim.state.mesh_barrier)

    def test_hardscape_command_places_and_picks_item(self) -> None:
        sim = Terrarium(seed=1)
        output = io.StringIO()

        with redirect_stdout(output):
            handle_hardscape_command(sim, ["place", "river_stone", "8%", "edge", "flat", "x=50", "y=70"])
            handle_hardscape_command(sim, ["pick", "H01"])

        text = output.getvalue()
        self.assertIn("placed H01", text)
        self.assertIn("xyz 50.0,70.0", text)
        self.assertIn("picked H01", text)
        self.assertEqual(sim.state.hardscape_items, [])

    def test_hardscape_command_accepts_angle_and_tilt(self) -> None:
        sim = Terrarium(seed=1)
        output = io.StringIO()

        with redirect_stdout(output):
            handle_hardscape_command(sim, ["place", "slate", "10%", "center", "flat", "angle=120", "tilt=22"])

        text = output.getvalue()
        self.assertIn("angle 120", text)
        self.assertIn("tilt +22", text)
        self.assertAlmostEqual(sim.state.hardscape_items[0].rotation_deg, 120.0)
        self.assertAlmostEqual(sim.state.hardscape_items[0].tilt_deg, 22.0)

    def test_hardscape_command_guides_player_without_raising(self) -> None:
        sim = Terrarium(seed=1)
        output = io.StringIO()

        with redirect_stdout(output):
            handle_hardscape_command(sim, ["place", "river_stone", "40%", "edge"])

        text = output.getvalue()
        self.assertIn("Nothing changed", text)
        self.assertIn("suggested range", text)
        self.assertEqual(sim.state.hardscape_items, [])

    def test_hardscape_catalog_lists_shapes_and_effects(self) -> None:
        output = io.StringIO()

        with redirect_stdout(output):
            print_hardscape_catalog()

        text = output.getvalue()
        self.assertIn("shape", text)
        self.assertIn("block=", text)
        self.assertIn("moisture_edge=", text)

    def test_placement_command_sets_window_face_and_lamp(self) -> None:
        sim = Terrarium(seed=1)
        output = io.StringIO()

        with redirect_stdout(output):
            handle_placement_command(sim, ["window", "east"])
            handle_placement_command(sim, ["face", "135"])
            handle_placement_command(sim, ["lamp", "45", "35%", "schedule", "7-19"])

        text = output.getvalue()
        self.assertIn("set window to east-facing", text)
        self.assertIn("face toward window 135.0deg", text)
        self.assertIn("set moss lamp to 45.0deg", text)
        self.assertEqual(sim.state.window_direction, "east")
        self.assertAlmostEqual(sim.state.window_facing_deg, 135.0)
        self.assertTrue(sim.state.moss_lamp_enabled)
        self.assertAlmostEqual(sim.state.moss_lamp_intensity, 0.35)
        self.assertEqual(sim.state.moss_lamp_start_hour, 7)
        self.assertEqual(sim.state.moss_lamp_duration_hours, 12)

    def test_placement_command_updates_lamp_schedule_and_timer(self) -> None:
        sim = Terrarium(seed=1)
        output = io.StringIO()

        with redirect_stdout(output):
            handle_placement_command(sim, ["lamp", "45", "0.30"])
            handle_placement_command(sim, ["lamp", "schedule", "20-8"])
            handle_placement_command(sim, ["lamp", "timer", "10h"])

        text = output.getvalue()
        self.assertIn("set moss lamp schedule to 20:00 for 12h", text)
        self.assertIn("set moss lamp timer to 10h", text)
        self.assertEqual(sim.state.moss_lamp_start_hour, 20)
        self.assertEqual(sim.state.moss_lamp_duration_hours, 10)

    def test_placement_command_sets_shade_umbrella(self) -> None:
        sim = Terrarium(seed=1)
        output = io.StringIO()

        with redirect_stdout(output):
            handle_placement_command(sim, ["umbrella", "120%", "south", "leaning_north", "x=50", "y=70", "angle=180", "tilt=20"])

        text = output.getvalue()
        self.assertIn("set shade umbrella area 120.0%", text)
        self.assertIn("shade umbrella area 120%", text)
        self.assertTrue(sim.state.umbrella_enabled)
        self.assertEqual(sim.state.umbrella_coverage_percent, 120.0)
        self.assertEqual(sim.state.hardscape_items, [])

    def test_placement_command_turns_umbrella_off(self) -> None:
        sim = Terrarium(seed=1)
        sim.set_umbrella(120.0, x_percent=50.0, y_percent=70.0)
        output = io.StringIO()

        with redirect_stdout(output):
            handle_placement_command(sim, ["umbrella", "off"])

        text = output.getvalue()
        self.assertIn("turned shade umbrella off", text)
        self.assertFalse(sim.state.umbrella_enabled)

    def test_placement_command_guides_bad_input_without_raising(self) -> None:
        sim = Terrarium(seed=1)
        output = io.StringIO()

        with redirect_stdout(output):
            handle_placement_command(sim, ["window", "up"])
            handle_placement_command(sim, ["umbrella", "laser"])
            handle_placement_command(sim, ["lamp", "30", "2.0"])

        text = output.getvalue()
        self.assertIn("Nothing changed", text)
        self.assertIn("north, east, south, or west", text)
        self.assertIn("unknown umbrella option", text)
        self.assertFalse(sim.state.moss_lamp_enabled)

    def test_season_and_weather_are_not_player_commands(self) -> None:
        sim = Terrarium(seed=1)
        output = io.StringIO()

        with redirect_stdout(output):
            handle_placement_command(sim, ["season", "winter"])
            handle_placement_command(sim, ["weather", "clear"])

        text = output.getvalue()
        self.assertIn("unknown placement action", text)
        self.assertNotEqual(sim.state.season, "winter")
        self.assertEqual(sim.state.weather_mode, "variable")

    def test_plant_command_adds_prunes_and_removes(self) -> None:
        sim = Terrarium(seed=1)
        output = io.StringIO()

        with redirect_stdout(output):
            handle_plant_command(sim, ["add", "fittonia_mini", "5%", "soil", "x=50", "y=40"])
            handle_plant_command(sim, ["prune", "P01", "roots", "20%"])
            handle_plant_command(sim, ["remove", "P01"])

        text = output.getvalue()
        self.assertIn("planted P01", text)
        self.assertIn("xyz 50.0,40.0", text)
        self.assertIn("pruned P01 roots", text)
        self.assertIn("removed P01", text)
        self.assertEqual(sim.state.plantings, [])

    def test_plant_command_auto_mounts_moss_by_coordinate(self) -> None:
        sim = Terrarium(seed=1)
        sim.place_hardscape("driftwood", 12.0, x_percent=35.0, y_percent=55.0)
        output = io.StringIO()

        with redirect_stdout(output):
            handle_plant_command(sim, ["add", "cushion_moss", "6%", "x=35", "y=55"])

        text = output.getvalue()
        self.assertIn("hardscape:H01", text)
        self.assertEqual(sim.state.plantings[0].attached_to, "H01")

    def test_plant_command_guides_player_without_raising(self) -> None:
        sim = Terrarium(seed=1)
        output = io.StringIO()

        with redirect_stdout(output):
            handle_plant_command(sim, ["add", "fittonia_mini", "1%"])

        text = output.getvalue()
        self.assertIn("Nothing changed", text)
        self.assertIn("larger area", text)
        self.assertEqual(sim.state.plantings, [])

    def test_plant_catalog_mentions_survival_is_not_a_gate(self) -> None:
        output = io.StringIO()

        with redirect_stdout(output):
            print_plant_catalog("fittonia")

        text = output.getvalue()
        self.assertIn("minimum area", text)
        self.assertIn("fittonia_mini", text)

    def test_plant_growth_command_reports_life_details(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_planting("fittonia_mini", 5.0)
        output = io.StringIO()

        with redirect_stdout(output):
            handle_plant_command(sim, ["growth"])

        text = output.getvalue()
        self.assertIn("PLANT GROWTH", text)
        self.assertIn("Mini fittonia", text)
        self.assertIn("health", text)
        self.assertIn("light note", text)
        self.assertIn("growth_rate", text)
        self.assertIn("repro", text)

    def test_animal_command_adds_and_removes_group(self) -> None:
        sim = Terrarium(seed=1)
        output = io.StringIO()

        with redirect_stdout(output):
            handle_animal_command(sim, ["add", "springtail", "30", "soil", "x=30", "y=50"])
            handle_animal_command(sim, ["remove", "A01"])

        text = output.getvalue()
        self.assertIn("added A01", text)
        self.assertIn("xyz 30.0,50.0", text)
        self.assertIn("removed A01", text)
        self.assertEqual(sim.state.animal_groups, [])

    def test_animal_command_guides_player_without_raising(self) -> None:
        sim = Terrarium(seed=1)
        output = io.StringIO()

        with redirect_stdout(output):
            handle_animal_command(sim, ["add", "springtail", "1"])

        text = output.getvalue()
        self.assertIn("Nothing changed", text)
        self.assertIn("minimum", text)
        self.assertEqual(sim.state.animal_groups, [])

    def test_animal_catalog_mentions_predators_are_future_plan(self) -> None:
        output = io.StringIO()

        with redirect_stdout(output):
            print_animal_catalog("decomposer")

        text = output.getvalue()
        self.assertIn("Predators", text)
        self.assertIn("springtail", text)

    def test_moisten_command_uses_milliliters(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_substrate("soil", 3.0, {"peat_moss": 100})
        output = io.StringIO()

        with redirect_stdout(output):
            handle_moisten_command(sim, ["30ml"])

        text = output.getvalue()
        self.assertIn("moistened soil with 30.0 ml", text)
        self.assertEqual(sim.state.soil_moistened_ml, 30.0)

    def test_moisten_command_does_not_require_soil(self) -> None:
        sim = Terrarium(seed=1)
        output = io.StringIO()

        with redirect_stdout(output):
            handle_moisten_command(sim, ["soil", "30ml"])

        text = output.getvalue()
        self.assertIn("moistened soil with 30.0 ml", text)
        self.assertEqual(sim.state.soil_moistened_ml, 30.0)

    def test_spray_command_uses_count(self) -> None:
        sim = Terrarium(seed=1)
        output = io.StringIO()

        with redirect_stdout(output):
            handle_spray_command(sim, ["5"])

        text = output.getvalue()
        self.assertIn("sprayed 5 time(s)", text)
        self.assertAlmostEqual(sim.state.sprayed_ml, 4.0)
        self.assertEqual(sim.state.spray_count, 5)

    def test_spray_command_guides_bad_count(self) -> None:
        sim = Terrarium(seed=1)
        output = io.StringIO()

        with redirect_stdout(output):
            handle_spray_command(sim, ["half"])

        text = output.getvalue()
        self.assertIn("Nothing changed", text)
        self.assertIn("whole number", text)

    def test_seal_command_finishes_crafting_and_reports_summary(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_substrate("soil", 2.0, {"peat_moss": 100})
        sim.add_planting("fittonia_mini", 5.0)
        output = io.StringIO()

        with redirect_stdout(output):
            handle_seal_command(sim, [])

        text = output.getvalue()
        self.assertTrue(sim.state.sealed)
        self.assertIn("SEALED TERRARIUM", text)
        self.assertIn("living", text)

    def test_sealed_crafting_command_guides_player_without_changing_state(self) -> None:
        sim = Terrarium(seed=1)
        sim.seal()
        output = io.StringIO()

        with redirect_stdout(output):
            handle_spray_command(sim, ["5"])
            handle_plant_command(sim, ["add", "fittonia_mini"])

        text = output.getvalue()
        self.assertIn("Nothing changed", text)
        self.assertIn("sealed", text)
        self.assertEqual(sim.state.sprayed_ml, 0.0)
        self.assertEqual(sim.state.plantings, [])

    def test_survival_manager_tracks_and_pauses_sealed_bottles(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_planting("fittonia_mini", 5.0)
        sim.seal()
        manager = SurvivalManager()

        bottle = manager.register(sim)
        manager.pause(bottle.bottle_id)
        text = manager.render_list()

        self.assertEqual(bottle.bottle_id, "B01")
        self.assertFalse(bottle.running)
        self.assertIn("B01", text)
        self.assertIn("paused", text)

    def test_survival_manager_removes_bottle_from_list(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_planting("fittonia_mini", 5.0)
        sim.seal()
        manager = SurvivalManager()
        bottle = manager.register(sim, "old_bottle")

        removed = manager.remove(bottle.bottle_id)
        text = manager.render_list()

        self.assertEqual(removed.bottle_id, "B01")
        self.assertFalse(removed.running)
        self.assertIn("empty", text)
        with self.assertRaises(ValueError):
            manager.get("B01")

    def test_bottle_remove_command_discards_bottle_without_throwing(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_planting("fittonia_mini", 5.0)
        sim.seal()
        manager = SurvivalManager()
        manager.register(sim, "old_bottle")
        output = io.StringIO()

        with redirect_stdout(output):
            handle_bottle_command(manager, ["remove", "B01"])
            handle_bottle_command(manager, ["remove", "B01"])

        text = output.getvalue()
        self.assertIn("B01 old_bottle removed from the bottle list", text)
        self.assertIn("Nothing changed", text)
        self.assertIn("unknown bottle id", text)
        self.assertIn("empty", manager.render_list())

    def test_survival_manager_generates_landmark_messages(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_planting("fittonia_mini", 5.0)
        sim.seal()
        manager = SurvivalManager()
        bottle = manager.register(sim)
        sim.state.events = ["O2_CRASH"]

        messages = manager._messages_for_step(bottle)

        self.assertTrue(any("survival day" in message for message in messages))
        self.assertTrue(any("sluggish near the surface" in message for message in messages))

    def test_survival_manager_reports_visible_water_cycle_evidence(self) -> None:
        sim = Terrarium(seed=1)
        sim.seal()
        manager = SurvivalManager()
        bottle = manager.register(sim)
        sim.state.events = ["CONDENSATION_BEADS", "SOIL_WATERLOGGED", "GLASS_DRYING"]

        messages = manager._messages_for_step(bottle)

        text = "\n".join(messages)
        self.assertIn("beads of water collect on the glass", text)
        self.assertIn("root zone looks glassy", text)
        self.assertIn("glass is nearly dry", text)
        self.assertNotIn("oxygen", text.lower())
        self.assertNotIn("carbon", text.lower())

    def test_survival_manager_reports_plant_and_animal_life_changes(self) -> None:
        sim = Terrarium(seed=1)
        planting = sim.add_planting("fittonia_mini", 5.0)
        group = sim.add_animals("springtail", 30)
        sim.seal()
        manager = SurvivalManager()
        bottle = manager.register(sim)
        planting.growth_stage = "growing"
        planting.survival_state = "stable"
        planting.reproduction_progress = 26.0
        group.count = 32
        group.population_trend = "growing"

        messages = manager._messages_for_step(bottle)

        text = "\n".join(messages)
        self.assertIn("fresh tips are visible", text)
        self.assertIn("new growth points", text)
        self.assertIn("new tiny young", text)

    def test_daily_summary_reports_visible_growth_without_internal_numbers(self) -> None:
        sim = Terrarium(seed=1)
        planting = sim.add_planting("fittonia_mini", 5.0)
        group = sim.add_animals("springtail", 30)
        sim.seal()
        manager = SurvivalManager()
        bottle = manager.register(sim)
        sim.state.tick = 24
        planting.growth_stage = "reproductive"
        planting.reproduction_progress = 76.0
        planting.new_growth_count = 4
        group.population_trend = "reproducing"
        group.visible_activity = 72.0

        messages = manager._messages_for_step(bottle)

        daily_messages = [message for message in messages if " - DAILY: " in message]
        self.assertEqual(1, len(daily_messages))
        daily = daily_messages[0]
        self.assertIn("plant changes:", daily)
        self.assertIn("new growth points", daily)
        self.assertIn("animal changes:", daily)
        self.assertIn("tiny young", daily)
        self.assertNotIn("growth_rate", daily)
        self.assertNotIn("repro", daily)
        self.assertNotIn("%", daily)

    def test_daily_summary_lists_every_living_group_without_more_stub(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_planting("fittonia_mini", 5.0, "surface", 35.0, 36.0)
        sim.add_planting("fittonia_white", 5.0, "surface", 58.0, 38.0)
        dead_planting = sim.add_planting("cushion_moss", 7.0, "surface", 45.0, 68.0)
        sim.add_animals("springtail", 30, "soil", 48.0, 52.0)
        dead_group = sim.add_animals("dwarf_white_isopod", 6, "leaf_litter", 56.0, 56.0)
        sim.seal()
        manager = SurvivalManager()
        bottle = manager.register(sim)
        sim.state.tick = 24
        dead_planting.survival_state = "dead"
        dead_planting.status = "dead"
        dead_group.count = 0
        dead_group.survival_state = "dead"

        messages = manager._messages_for_step(bottle)

        daily_messages = [message for message in messages if " - DAILY: " in message]
        self.assertEqual(1, len(daily_messages))
        daily = daily_messages[0]
        self.assertIn("Mini fittonia", daily)
        self.assertIn("White nerve plant", daily)
        self.assertIn("Cushion moss", daily)
        self.assertIn("Springtail colony", daily)
        self.assertIn("Dwarf white isopod", daily)
        self.assertIn("no living tissue remains", daily)
        self.assertIn("no visible movement remains", daily)
        self.assertNotIn("+", daily)
        self.assertNotIn("more plantings", daily)
        self.assertNotIn("more groups", daily)

    def test_survival_manager_life_state_messages_are_descriptive_and_cooled(self) -> None:
        sim = Terrarium(seed=1)
        planting = sim.add_planting("fittonia_mini", 5.0)
        sim.seal()
        manager = SurvivalManager()
        bottle = manager.register(sim)
        planting.survival_state = "stressed"
        planting.growth_rate = 0.004

        first = manager._messages_for_step(bottle)
        planting.survival_state = "stable"
        sim.state.tick += 1
        second = manager._messages_for_step(bottle)

        self.assertTrue(any("Mini fittonia" in message and "leaves" in message for message in first))
        self.assertFalse(any("Mini fittonia" in message and "health" in message for message in first))
        self.assertFalse(any("Mini fittonia" in message and "leaves" in message for message in second))

    def test_survival_report_variants_reduce_repetition_without_personifying(self) -> None:
        sim = Terrarium(seed=1)
        planting = sim.add_planting("fittonia_mini", 5.0)
        planting.survival_state = "stressed"
        sim.seal()
        manager = SurvivalManager()
        bottle = manager.register(sim)
        prefix = "[B01] survival day 1 01:00"

        first = manager._plant_state_message(bottle, prefix, planting)
        second = manager._plant_state_message(bottle, prefix, planting)
        event_first = manager._event_message(bottle, "CONDENSATION_BEADS")
        event_second = manager._event_message(bottle, "CONDENSATION_BEADS")

        self.assertNotEqual(first, second)
        self.assertNotEqual(event_first, event_second)
        self.assertIn("FLORA", first)
        report_text = "\n".join([first, second, event_first, event_second])
        self.assertNotIn(" is now ", report_text)
        self.assertNotIn("wants", report_text)
        self.assertNotIn("feels", report_text)

    def test_bottle_plants_command_reports_managed_bottle_growth(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_planting("fittonia_mini", 5.0)
        sim.seal()
        manager = SurvivalManager()
        bottle = manager.register(sim)
        output = io.StringIO()

        with redirect_stdout(output):
            handle_bottle_command(manager, ["plants", bottle.bottle_id])

        text = output.getvalue()
        self.assertIn("PLANT GROWTH", text)
        self.assertIn("Mini fittonia", text)

    def test_survival_manager_stops_dead_bottle(self) -> None:
        sim = Terrarium(seed=1)
        planting = sim.add_planting("fittonia_mini", 5.0)
        sim.seal()
        manager = SurvivalManager()
        bottle = manager.register(sim)
        planting.status = "dead"
        planting.survival_state = "dead"
        planting.health = 0.0

        messages = manager._death_messages_if_needed(bottle)

        self.assertTrue(bottle.dead)
        self.assertFalse(bottle.running)
        self.assertTrue(any("terrarium died" in message for message in messages))
        with self.assertRaises(ValueError):
            manager.resume(bottle.bottle_id)

    def test_loaded_sealed_bottle_can_be_observed_without_new_open_craft(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_planting("fittonia_mini", 5.0)
        sim.seal()
        manager = SurvivalManager()

        bottle = manager.register(sim)

        self.assertTrue(sim.state.sealed)
        self.assertIn("B01", manager.render_list())
        self.assertFalse(has_crafting_content(make_followup_sim(build_parser().parse_args(["shell"]), 1)))
        self.assertEqual(bottle.bottle_id, "B01")

    def test_space_command_reports_volume_budget(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_substrate("soil", 3.0, {"peat_moss": 100})
        output = io.StringIO()

        with redirect_stdout(output):
            handle_space_command(sim, ["status"])

        text = output.getvalue()
        self.assertIn("SPACE used", text)
        self.assertIn("layers", text)
        self.assertIn("open_air", text)


if __name__ == "__main__":
    unittest.main()
