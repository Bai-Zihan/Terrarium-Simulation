import json
import unittest
from pathlib import Path

from terrarium.model import ANIMALS, CONTAINERS, HARDSCAPES, PLANTS, SimulationConfig, Terrarium, TerrariumState, soil_layer_stats, substrate_layer_stats

FIXTURES_DIR = Path(__file__).with_name("fixtures")


class TerrariumModelTests(unittest.TestCase):
    def _build_complex_recipe(self) -> Terrarium:
        sim = Terrarium(config=SimulationConfig(noise=0.0), seed=1)
        sim.set_container("wide_jar")
        sim.set_window("east")
        sim.set_window_facing(90)
        sim.set_window_light_mode("mixed")
        sim.set_moss_lamp(230, 0.22)
        sim.set_moss_lamp_schedule(18, 4)
        sim.add_substrate("drainage", 1.8, {"leca": 60, "pumice": 40}, slope_x_cm=0.4, slope_y_cm=-0.2)
        sim.add_substrate("purification", 0.6, {"activated_charcoal": 100})
        sim.install_mesh_barrier()
        sim.add_substrate(
            "soil",
            4.2,
            {"peat_moss": 45, "compost": 20, "sphagnum_moss": 20, "perlite": 15},
            slope_x_cm=1.1,
            slope_y_cm=-0.6,
        )
        sim.add_substrate(
            "amendment",
            0.8,
            {"akadama": 45, "kanuma": 25, "perlite": 30},
            slope_x_cm=0.8,
            slope_y_cm=-0.4,
        )
        sim.moisten_soil(85)
        sim.spray(8)
        sim.place_hardscape("driftwood", 14, "center", "arch", x_percent=48, y_percent=54, angle_deg=35, tilt_deg=18)
        sim.place_hardscape("slate", 9, "east", "leaning_west", x_percent=70, y_percent=48, angle_deg=115, tilt_deg=24)
        sim.place_hardscape("river_stone", 5, "northwest", "flat", x_percent=28, y_percent=68, angle_deg=20)
        sim.add_planting("cushion_moss", 5, "hardscape:H01:groove")
        sim.add_planting("rabbit_foot_fern", 4, "hardscape:H01:side")
        sim.add_planting("fittonia_mini", 5, "surface", 18, 30)
        sim.add_planting("masdevallia_mini", 4, "hardscape:H02:side")
        sim.add_planting("sheet_moss", 6, "surface", 55, 25)
        sim.add_animals("springtail", 35, "soil", 42, 48)
        sim.add_animals("dwarf_white_isopod", 6, "leaf_litter", 55, 58)
        sim.seal()
        return sim

    def _build_balanced_fittonia_recipe(self) -> Terrarium:
        sim = Terrarium(config=SimulationConfig(noise=0.0), seed=11)
        sim.set_container("standard_1l")
        sim.set_window("east")
        sim.set_window_facing(90)
        sim.set_window_light_mode("mixed")
        sim.set_moss_lamp(220, 0.18)
        sim.set_moss_lamp_schedule(18, 3)
        sim.add_substrate("drainage", 1.8, {"leca": 70, "pumice": 30}, slope_x_cm=0.4)
        sim.install_mesh_barrier()
        sim.add_substrate(
            "soil",
            4.0,
            {"peat_moss": 45, "compost": 25, "sphagnum_moss": 15, "perlite": 15},
            slope_x_cm=0.7,
            slope_y_cm=-0.3,
        )
        sim.moisten_soil(70)
        sim.spray(5)
        sim.place_hardscape("river_stone", 8, "edge", "flat", x_percent=78, y_percent=45)
        sim.add_planting("fittonia_mini", 5, "surface", 35, 45)
        sim.add_planting("fittonia_white", 5, "surface", 58, 48)
        sim.add_planting("cushion_moss", 8, "surface", 45, 70)
        sim.add_animals("springtail", 32, "soil", 48, 52)
        sim.add_animals("dwarf_white_isopod", 8, "leaf_litter", 55, 58)
        sim.seal()
        return sim

    def _build_stable_umbrella_recipe(self) -> Terrarium:
        sim = Terrarium(config=SimulationConfig(noise=0.0), seed=1)
        sim.set_container("wide_jar")
        sim.set_window("east")
        sim.set_window_facing(90)
        sim.set_umbrella(125, "center", "leaning_west")
        sim.set_moss_lamp(230, 0.18)
        sim.set_moss_lamp_schedule(18, 3)
        sim.add_substrate("drainage", 1.6, {"leca": 70, "pumice": 30}, slope_x_cm=0.2, slope_y_cm=-0.1)
        sim.install_mesh_barrier()
        sim.add_substrate(
            "soil",
            4.0,
            {"peat_moss": 45, "compost": 20, "sphagnum_moss": 20, "perlite": 15},
            slope_x_cm=0.5,
            slope_y_cm=-0.2,
        )
        sim.add_substrate("amendment", 0.5, {"akadama": 50, "perlite": 30, "kanuma": 20}, slope_x_cm=0.3, slope_y_cm=-0.1)
        sim.moisten_soil(72)
        sim.spray(5)
        sim.place_hardscape("driftwood", 10, "center", "arch", x_percent=48, y_percent=55, angle_deg=35, tilt_deg=14)
        sim.add_planting("cushion_moss", 7, "surface", 45, 68)
        sim.add_planting("sheet_moss", 5, "hardscape:H01:groove")
        sim.add_planting("fittonia_mini", 5, "surface", 35, 36)
        sim.add_planting("fittonia_white", 5, "surface", 58, 38)
        sim.add_animals("springtail", 32, "soil", 48, 52)
        sim.add_animals("dwarf_white_isopod", 6, "leaf_litter", 56, 56)
        sim.seal()
        return sim

    def _build_carnivorous_bog_recipe(self) -> Terrarium:
        sim = Terrarium(config=SimulationConfig(noise=0.0), seed=13)
        sim.set_container("wide_jar")
        sim.set_window("south")
        sim.set_window_light_mode("direct")
        sim.set_moss_lamp(160, 0.26)
        sim.set_moss_lamp_schedule(8, 10)
        sim.add_substrate("drainage", 1.1, {"pumice": 100})
        sim.install_mesh_barrier()
        sim.add_substrate("soil", 3.0, {"sphagnum_moss": 70, "perlite": 30}, slope_x_cm=-0.5)
        sim.moisten_soil(95)
        sim.spray(6)
        sim.add_planting("drosera_spatulata", 5, "surface", 35, 45)
        sim.add_planting("pinguicula_esseriana", 4, "surface", 55, 48)
        sim.add_planting("utricularia_sandersonii", 7, "surface", 45, 68)
        sim.add_animals("springtail", 25, "soil", 48, 58)
        sim.seal()
        return sim

    def _build_tiny_crowded_vial_recipe(self) -> Terrarium:
        sim = Terrarium(config=SimulationConfig(noise=0.0), seed=17)
        sim.set_container("tiny_vial")
        sim.set_window("east")
        sim.set_window_light_mode("mixed")
        sim.add_substrate("drainage", 0.8, {"leca": 100})
        sim.install_mesh_barrier()
        sim.add_substrate("soil", 1.6, {"peat_moss": 50, "compost": 25, "perlite": 25})
        sim.moisten_soil(20)
        sim.spray(3)
        sim.add_planting("fittonia_mini", 5, "surface", 45, 45)
        sim.add_planting("cushion_moss", 8, "surface", 55, 60)
        sim.add_animals("springtail", 20, "soil")
        sim.seal()
        return sim

    def test_same_seed_is_deterministic(self) -> None:
        left = Terrarium(seed=42)
        right = Terrarium(seed=42)

        for _ in range(72):
            left.step()
            right.step()

        self.assertEqual(left.state.to_json(), right.state.to_json())

    def test_resource_pools_stay_bounded(self) -> None:
        sim = Terrarium(seed=7)

        sim.run(500)

        for name in ("water", "nutrients", "oxygen", "carbon_dioxide", "detritus", "toxicity"):
            value = getattr(sim.state, name)
            self.assertGreaterEqual(value, 0.0, name)
            self.assertLessEqual(value, 1.0, name)

    def test_dark_terrarium_loses_plant_biomass(self) -> None:
        config = SimulationConfig(light_intensity=0.0, noise=0.0)
        state = TerrariumState(plants=80.0, grazers=0.0, algae=0.0, microbes=12.0)
        sim = Terrarium(state=state, config=config, seed=3)

        sim.run(240)

        self.assertLess(sim.state.plants, 80.0)

    def test_container_can_be_selected_before_crafting(self) -> None:
        sim = Terrarium(seed=1)

        selected = sim.set_container("tiny_vial")

        self.assertEqual(selected.key, "tiny_vial")
        self.assertEqual(sim.state.container.capacity_ml, 150.0)
        self.assertLess(sim.state.container.height_cm, CONTAINERS["standard_1l"].spec().height_cm)

    def test_container_selection_is_locked_after_physical_contents(self) -> None:
        sim = Terrarium(seed=1)
        sim.moisten_soil(5.0)

        with self.assertRaises(ValueError):
            sim.set_container("wide_jar")

    def test_horizontal_container_uses_rectangular_coordinates(self) -> None:
        sim = Terrarium(seed=1)
        sim.set_container("horizontal_jar")

        planting = sim.add_planting("cushion_moss", 6.0, "surface", 95.0, 95.0)

        self.assertEqual(sim.state.container.footprint_shape, "rect")
        self.assertAlmostEqual(planting.x_percent, 95.0)
        self.assertAlmostEqual(planting.y_percent, 95.0)

    def test_substrate_layers_can_be_added_in_any_order(self) -> None:
        sim = Terrarium(seed=1)

        sim.add_substrate("soil", 4.0, {"peat_moss": 60, "compost": 40})
        sim.add_substrate("drainage", 2.0, {"leca": 70, "pumice": 30})
        sim.add_substrate("purification", 1.0, {"activated_charcoal": 100})

        self.assertEqual([layer.layer_kind for layer in sim.state.substrate_layers], ["soil", "drainage", "purification"])

    def test_repeated_substrate_layer_stays_separate(self) -> None:
        sim = Terrarium(seed=1)

        sim.add_substrate("drainage", 1.0, {"leca": 100})
        sim.add_substrate("drainage", 1.5, {"pumice": 100})

        self.assertEqual(len(sim.state.substrate_layers), 2)
        self.assertEqual(sim.state.substrate_layers[0].height_cm, 1.0)
        self.assertEqual(sim.state.substrate_layers[1].height_cm, 1.5)

    def test_dig_only_removes_current_top_substrate_layer(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_substrate("soil", 3.0, {"peat_moss": 70, "perlite": 30})
        sim.add_substrate("amendment", 1.0, {"akadama": 100})

        removed = sim.dig_substrate(0.4)

        self.assertEqual(removed.layer_kind, "amendment")
        self.assertAlmostEqual(sim.state.substrate_layers[-1].height_cm, 0.6)
        with self.assertRaises(ValueError):
            sim.dig_substrate(0.7)

    def test_substrate_state_round_trips_through_json(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_substrate("drainage", 2.0, {"leca": 50, "volcanic_rock": 50})
        sim.install_mesh_barrier()

        loaded = Terrarium.from_json(sim.state.to_json())

        self.assertEqual(len(loaded.state.substrate_layers), 2)
        self.assertEqual(loaded.state.substrate_layers[0].portions[1].substrate, "volcanic_rock")
        self.assertEqual(loaded.state.substrate_layers[1].layer_kind, "mesh")
        self.assertTrue(loaded.state.mesh_barrier)

    def test_mesh_barrier_is_recorded_as_a_layer(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_substrate("drainage", 2.0, {"leca": 100})

        sim.install_mesh_barrier()

        self.assertTrue(sim.state.mesh_barrier)
        self.assertEqual(sim.mesh_layer_count(), 1)
        self.assertEqual(sim.state.substrate_layers[-1].layer_kind, "mesh")

    def test_mesh_barrier_can_be_added_after_soil(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_substrate("soil", 3.0, {"peat_moss": 100})

        sim.install_mesh_barrier()

        self.assertEqual([layer.layer_kind for layer in sim.state.substrate_layers], ["soil", "mesh"])

    def test_lower_substrate_can_be_added_after_mesh(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_substrate("drainage", 2.0, {"leca": 100})
        sim.install_mesh_barrier()

        sim.add_substrate("purification", 1.0, {"activated_charcoal": 100})

        self.assertEqual([layer.layer_kind for layer in sim.state.substrate_layers], ["drainage", "mesh", "purification"])

    def test_multiple_mesh_layers_are_allowed(self) -> None:
        sim = Terrarium(seed=1)

        sim.install_mesh_barrier()
        sim.install_mesh_barrier()

        self.assertEqual(sim.mesh_layer_count(), 2)

    def test_moisten_uses_milliliters_without_requiring_soil(self) -> None:
        sim = Terrarium(seed=1)
        before = sim.state.water

        sim.moisten_soil(30.0)

        self.assertEqual(sim.state.soil_moistened_ml, 30.0)
        self.assertGreater(sim.state.water, before)

    def test_spray_uses_assumed_ml_per_pump(self) -> None:
        sim = Terrarium(seed=1)
        before = sim.state.water

        added = sim.spray(5)

        self.assertAlmostEqual(added, 4.0)
        self.assertEqual(sim.state.spray_count, 5)
        self.assertAlmostEqual(sim.state.sprayed_ml, 4.0)
        self.assertGreater(sim.state.water, before)

    def test_volume_profile_tracks_layers_water_air_and_objects(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_substrate("soil", 3.0, {"peat_moss": 100})
        sim.moisten_soil(30.0)
        sim.spray(5)
        sim.place_hardscape("river_stone", 8.0)
        sim.add_planting("fittonia_mini", 5.0)

        profile = sim.volume_profile()

        self.assertGreater(profile["layer_volume_ml"], 0.0)
        self.assertGreater(profile["pore_capacity_ml"], 0.0)
        self.assertEqual(profile["water_added_ml"], 34.0)
        self.assertEqual(profile["spray_count"], 5.0)
        self.assertIn("vapor_water_ml", profile)
        self.assertIn("condensation_ml", profile)
        self.assertIn("surface_wetness", profile)
        self.assertGreater(profile["hardscape_volume_ml"], 0.0)
        self.assertGreater(profile["plant_root_volume_ml"], 0.0)
        self.assertGreater(profile["total_air_ml"], 0.0)

    def test_water_cycle_moves_water_between_visible_pools(self) -> None:
        config = SimulationConfig(light_intensity=0.0, noise=0.0)
        sim = Terrarium(config=config, seed=1)
        sim.add_substrate("soil", 3.0, {"peat_moss": 100})
        sim.moisten_soil(35.0)
        sim.spray(10)

        before_condensation = sim.state.condensation_ml
        sim.step()

        self.assertTrue(sim.state.water_cycle_initialized)
        self.assertGreaterEqual(sim.state.condensation_ml, before_condensation)
        self.assertGreaterEqual(sim.state.vapor_water_ml, 0.0)
        self.assertGreaterEqual(sim.state.surface_wetness, 0.0)

    def test_air_volume_and_waterlogging_affect_carbon_cycle(self) -> None:
        compact = Terrarium(seed=1)
        open_air = Terrarium(seed=1)
        compact.add_substrate("soil", 8.0, {"peat_moss": 100})
        compact.moisten_soil(260.0)
        open_air.moisten_soil(20.0)

        compact.step()
        open_air.step()

        self.assertNotEqual(compact.state.carbon_dioxide, open_air.state.carbon_dioxide)
        self.assertLess(compact._substrate_aeration_score(), 5.0)

    def test_volume_boundary_blocks_obvious_overfill(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_substrate("soil", 16.7, {"peat_moss": 100})

        with self.assertRaises(ValueError):
            sim.place_hardscape("ceramic_figure", 12.0)

    def test_substrate_stats_are_physical_not_soil_chemistry(self) -> None:
        sim = Terrarium(seed=1)
        layer = sim.add_substrate("drainage", 2.0, {"leca": 100})

        stats = substrate_layer_stats(layer)
        soil_stats = soil_layer_stats(layer)

        self.assertEqual(set(stats), {"water_retention", "aeration"})
        self.assertIsNone(soil_stats["ph"])
        self.assertIsNone(soil_stats["nutrients"])

    def test_soil_layer_has_root_zone_chemistry(self) -> None:
        sim = Terrarium(seed=1)
        layer = sim.add_substrate("soil", 4.0, {"peat_moss": 50, "compost": 30, "perlite": 20})

        stats = soil_layer_stats(layer)

        self.assertAlmostEqual(stats["ph"], 5.0625)
        self.assertAlmostEqual(stats["nutrients"], 6.0)

    def test_hardscape_reduces_plantable_area(self) -> None:
        sim = Terrarium(seed=1)

        sim.place_hardscape("slate", 20.0, "center", "flat")

        profile = sim.hardscape_profile()
        self.assertEqual(profile["coverage_percent"], 20.0)
        self.assertLess(profile["plantable_percent"], 100.0)
        self.assertGreater(profile["evaporation_shield"], 0.0)

    def test_hardscape_can_be_picked_by_id(self) -> None:
        sim = Terrarium(seed=1)
        item = sim.place_hardscape("river_stone", 8.0)

        removed = sim.pick_hardscape(item.item_id)

        self.assertEqual(removed.kind, "river_stone")
        self.assertEqual(sim.state.hardscape_items, [])

    def test_hardscape_total_coverage_is_capped(self) -> None:
        sim = Terrarium(seed=1)
        sim.place_hardscape("gravel_patch", 30.0)
        sim.place_hardscape("driftwood", 24.0)
        sim.place_hardscape("slate", 22.0)

        with self.assertRaises(ValueError):
            sim.place_hardscape("river_stone", 16.0)

    def test_explicit_hardscape_core_collision_is_rejected(self) -> None:
        sim = Terrarium(seed=1)
        sim.place_hardscape("river_stone", 10.0, x_percent=50.0, y_percent=50.0)

        with self.assertRaisesRegex(ValueError, "hardscape collision"):
            sim.place_hardscape("slate", 10.0, x_percent=50.0, y_percent=50.0)

    def test_hardscape_state_round_trips_through_json(self) -> None:
        sim = Terrarium(seed=1)
        sim.place_hardscape("driftwood", 12.0, "west", "leaning_east", 35.0, 55.0)

        loaded = Terrarium.from_json(sim.state.to_json())

        self.assertEqual(len(loaded.state.hardscape_items), 1)
        self.assertEqual(loaded.state.hardscape_items[0].position, "west")
        self.assertEqual(loaded.state.hardscape_items[0].orientation, "leaning_east")
        self.assertEqual(loaded.state.hardscape_items[0].x_percent, 35.0)
        self.assertEqual(loaded.state.hardscape_items[0].y_percent, 55.0)

    def test_substrate_slope_changes_surface_height_by_coordinate(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_substrate("soil", 4.0, {"peat_moss": 100}, slope_x_cm=1.0, slope_y_cm=-0.5)

        east = sim.substrate_surface_height_cm(80.0, 50.0)
        west = sim.substrate_surface_height_cm(20.0, 50.0)
        north = sim.substrate_surface_height_cm(50.0, 80.0)
        south = sim.substrate_surface_height_cm(50.0, 20.0)

        self.assertGreater(east, west)
        self.assertLess(north, south)

    def test_local_environment_uses_slope_and_hardscape_microclimate(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_substrate("soil", 4.0, {"peat_moss": 100}, slope_x_cm=1.2)
        sim.moisten_soil(40.0)
        base = sim._life_environment()
        low = sim.add_planting("sheet_moss", 6.0, "surface", 20.0, 50.0)
        high = sim.add_planting("sheet_moss", 6.0, "surface", 80.0, 50.0)

        low_env = sim._local_life_environment(low, base)
        high_env = sim._local_life_environment(high, base)

        self.assertGreater(low_env["water"], high_env["water"])
        self.assertGreater(low_env["humidity"], high_env["humidity"])

    def test_local_hardscape_shade_reduces_nearby_light(self) -> None:
        sim = Terrarium(state=TerrariumState(light=1.0), seed=1)
        sim.place_hardscape("driftwood", 12.0, x_percent=35.0, y_percent=55.0)
        near = sim.add_planting("cushion_moss", 6.0, "surface", 35.0, 55.0)
        far = sim.add_planting("cushion_moss", 6.0, "surface", 75.0, 50.0)
        base = sim._life_environment()

        self.assertLess(sim._local_life_environment(near, base)["light"], sim._local_life_environment(far, base)["light"])

    def test_oriented_hardscape_collision_uses_ellipse_direction(self) -> None:
        sim = Terrarium(seed=1)
        sim.place_hardscape("driftwood", 12.0, x_percent=50.0, y_percent=50.0, angle_deg=0.0, tilt_deg=0.0)

        with self.assertRaisesRegex(ValueError, "hardscape collision"):
            sim.place_hardscape("pebble", 1.0, x_percent=70.0, y_percent=50.0)

        side_item = sim.place_hardscape("pebble", 1.0, x_percent=50.0, y_percent=70.0)

        self.assertEqual(side_item.item_id, "H03")

    def test_hardscape_irregular_geometry_varies_boundary_by_angle(self) -> None:
        sim = Terrarium(seed=1)
        item = sim.place_hardscape("lava_rock", 10.0, x_percent=50.0, y_percent=50.0, angle_deg=0.0)

        left = sim._hardscape_support_radius_cm(item, 30.0)
        right = sim._hardscape_support_radius_cm(item, 330.0)

        self.assertEqual(HARDSCAPES[item.kind].geometry_profile, "porous_lobed")
        self.assertNotAlmostEqual(left, right, places=3)

    def test_pseudo3d_scene_exposes_projected_primitives_for_future_ui(self) -> None:
        sim = Terrarium(seed=1)
        hardscape = sim.place_hardscape("driftwood", 12.0, x_percent=42.0, y_percent=55.0, angle_deg=35.0)
        sim.add_planting("cushion_moss", 4.0, f"hardscape:{hardscape.item_id}:groove")
        sim.add_animals("springtail", 30, f"hardscape:{hardscape.item_id}:underside")

        scene = sim.pseudo3d_scene(view_angle_deg=35.0)
        ids = {primitive["id"] for primitive in scene}

        self.assertIn(hardscape.item_id, ids)
        self.assertIn("P01", ids)
        self.assertIn("A01", ids)
        self.assertTrue(all("bbox" in primitive and "depth_key" in primitive for primitive in scene))
        self.assertEqual([primitive["depth_key"] for primitive in scene], sorted(primitive["depth_key"] for primitive in scene))

    def test_hardscape_contact_patch_reports_surface_normal_and_area(self) -> None:
        sim = Terrarium(seed=1)
        item = sim.place_hardscape("driftwood", 12.0, x_percent=50.0, y_percent=50.0, angle_deg=0.0)

        patch = sim.hardscape_contact_patch(item.item_id, "groove")

        self.assertEqual(patch["surface"], "groove")
        self.assertIn(patch["feature"], HARDSCAPES[item.kind].surface_features)
        self.assertGreater(patch["contact_area_cm2"], 0.0)
        self.assertIn("normal_deg", patch)
        self.assertGreater(patch["attachment_support"], 0.0)
        self.assertGreater(patch["mold_bias"], 0.0)

    def test_hardscape_surface_microclimate_changes_attached_plant_environment(self) -> None:
        sim = Terrarium(
            state=TerrariumState(light=0.80, water=0.55, oxygen=0.65, carbon_dioxide=0.45),
            config=SimulationConfig(noise=0.0),
            seed=1,
        )
        item = sim.place_hardscape("driftwood", 12.0, x_percent=50.0, y_percent=50.0, angle_deg=0.0)
        top = sim.add_planting("cushion_moss", 4.0, f"hardscape:{item.item_id}:top")
        groove = sim.add_planting("cushion_moss", 4.0, f"hardscape:{item.item_id}:groove")
        base = sim._life_environment()

        top_env = sim._local_life_environment(top, base)
        groove_env = sim._local_life_environment(groove, base)

        self.assertGreater(groove_env["water"], top_env["water"])
        self.assertGreater(groove_env["humidity"], top_env["humidity"])
        self.assertGreater(groove_env["attachment_support"], top_env["attachment_support"])
        self.assertGreater(groove_env["surface_mold_bias"], top_env["surface_mold_bias"])
        self.assertLess(groove_env["aeration"], top_env["aeration"])

    def test_hardscape_surface_ecology_can_raise_visible_film_and_mold(self) -> None:
        def after_tick(with_hardscape: bool) -> tuple[float, float]:
            state = TerrariumState(
                water=0.95,
                oxygen=0.65,
                detritus=0.75,
                algae=60.0,
                microbes=70.0,
                surface_wetness=0.85,
                condensation_ml=5.0,
                liquid_water_ml=60.0,
                biofilm=0.10,
                mold_pressure=0.10,
                water_cycle_initialized=True,
            )
            sim = Terrarium(state=state, config=SimulationConfig(noise=0.0), seed=1)
            if with_hardscape:
                sim.place_hardscape("driftwood", 20.0, x_percent=50.0, y_percent=50.0)
            sim._advance_visible_ecology(0.0, 0.0)
            return sim.state.biofilm, sim.state.mold_pressure

        plain_biofilm, plain_mold = after_tick(False)
        hardscape_biofilm, hardscape_mold = after_tick(True)

        self.assertGreater(hardscape_biofilm, plain_biofilm)
        self.assertGreater(hardscape_mold, plain_mold)

    def test_hardscape_surface_attachment_sets_orientation(self) -> None:
        sim = Terrarium(seed=1)
        item = sim.place_hardscape("driftwood", 12.0, x_percent=50.0, y_percent=50.0, angle_deg=0.0)

        planting = sim.add_planting("cushion_moss", 4.0, f"hardscape:{item.item_id}:groove")

        self.assertEqual(planting.site, f"hardscape:{item.item_id}:groove")
        self.assertEqual(planting.attached_to, item.item_id)
        self.assertEqual(planting.attachment_surface, "groove")
        self.assertIn(planting.attachment_feature, HARDSCAPES[item.kind].surface_features)
        self.assertLess(planting.pitch_deg, 20.0)
        self.assertEqual(planting.lean_reason, "following_groove")

    def test_attached_planting_has_directional_footprint_shape(self) -> None:
        sim = Terrarium(seed=1)
        item = sim.place_hardscape("driftwood", 12.0, x_percent=50.0, y_percent=50.0, angle_deg=0.0)

        planting = sim.add_planting("cushion_moss", 4.0, f"hardscape:{item.item_id}:groove")
        along = sim._plant_support_radius_cm(planting, item.rotation_deg)
        across = sim._plant_support_radius_cm(planting, item.rotation_deg + 90.0)

        self.assertEqual(planting.shape_state, "tracking_groove")
        self.assertGreater(planting.footprint_aspect_ratio, 2.0)
        self.assertGreater(along, across)

    def test_coordinate_planting_auto_mounts_on_side_surface(self) -> None:
        sim = Terrarium(seed=1)
        item = sim.place_hardscape("driftwood", 12.0, x_percent=50.0, y_percent=50.0, angle_deg=0.0)
        x_percent, y_percent = sim._default_surface_xy(item, "side")

        planting = sim.add_planting("rabbit_foot_fern", 4.0, "surface", x_percent, y_percent)

        self.assertEqual(planting.site, f"hardscape:{item.item_id}:side")
        self.assertEqual(planting.attachment_surface, "side")
        self.assertLess(planting.pitch_deg, 50.0)

    def test_plant_structure_initializes_and_changes_with_growth(self) -> None:
        sim = Terrarium(
            state=TerrariumState(water=0.80, nutrients=0.75, oxygen=0.70, carbon_dioxide=0.50, plants=80.0),
            config=SimulationConfig(noise=0.0),
            seed=1,
        )
        planting = sim.add_planting("fittonia_mini", 5.0, "surface", 50.0, 50.0)
        initial_leaves = planting.leaf_count
        initial_stems = planting.stem_count

        sim.run(72)

        self.assertGreater(initial_leaves, 0)
        self.assertGreater(initial_stems, 0)
        self.assertGreaterEqual(planting.leaf_count, initial_leaves)
        self.assertGreaterEqual(planting.stem_count, initial_stems)
        self.assertGreaterEqual(planting.new_growth_count, 0)
        self.assertGreater(planting.root_tip_count, 0)
        self.assertGreater(planting.canopy_density_percent, 0.0)

    def test_visible_plant_structure_tracks_damage_and_contact_area(self) -> None:
        sim = Terrarium(seed=1)
        item = sim.place_hardscape("driftwood", 12.0, x_percent=50.0, y_percent=50.0, angle_deg=0.0)
        planting = sim.add_planting("rabbit_foot_fern", 4.0, f"hardscape:{item.item_id}:side")
        before_density = planting.canopy_density_percent

        sim._mark_plant_interaction(planting, 30.0, "soft plant tissue", "Tiny slug")

        self.assertGreater(planting.attachment_contact_area_cm2, 0.0)
        self.assertGreater(planting.damaged_leaf_count, 0)
        self.assertLess(planting.canopy_density_percent, before_density)

    def test_sun_direction_and_altitude_change_through_day(self) -> None:
        sim = Terrarium(config=SimulationConfig(noise=0.0), seed=1)

        sim.run(7)
        morning = (sim.state.light, sim.current_light_compass_deg(), sim.state.sun_altitude_deg)
        sim.run(5)
        noon = (sim.state.light, sim.current_light_compass_deg(), sim.state.sun_altitude_deg)
        sim.run(5)
        evening = (sim.state.light, sim.current_light_compass_deg(), sim.state.sun_altitude_deg)

        self.assertGreater(morning[0], 0.0)
        self.assertLess(morning[1], noon[1])
        self.assertGreater(evening[1], noon[1])
        self.assertGreater(noon[2], morning[2])
        self.assertGreater(noon[2], evening[2])

    def test_window_direction_changes_daily_light_profile(self) -> None:
        east = Terrarium(config=SimulationConfig(noise=0.0, light_intensity=1.0), seed=1)
        east.set_window("east")
        east.run(8)
        east_morning = east.state.light
        east.run(8)
        east_evening = east.state.light

        west = Terrarium(config=SimulationConfig(noise=0.0, light_intensity=1.0), seed=1)
        west.set_window("west")
        west.run(8)
        west_morning = west.state.light
        west.run(8)
        west_evening = west.state.light

        self.assertGreater(east_morning, east_evening)
        self.assertGreater(west_evening, west_morning)

    def test_window_facing_sets_local_light_source_angle(self) -> None:
        sim = Terrarium(config=SimulationConfig(noise=0.0, light_intensity=1.0), seed=1)
        sim.set_window("south")
        sim.set_window_facing(45.0)

        sim.run(12)

        self.assertAlmostEqual(sim.current_light_compass_deg(), 45.0, delta=1.0)
        self.assertAlmostEqual(sim.state.sun_altitude_deg, 68.0, delta=0.1)

    def test_moss_lamp_adds_light_and_round_trips(self) -> None:
        base = Terrarium(config=SimulationConfig(noise=0.0, light_intensity=0.35), seed=1)
        base.set_window("north")
        base.run(12)

        lit = Terrarium(config=SimulationConfig(noise=0.0, light_intensity=0.35), seed=1)
        lit.set_window("north")
        lit.set_moss_lamp(270.0, 0.40)
        lit.run(12)
        loaded = Terrarium.from_json(lit.state.to_json())

        self.assertGreater(lit.state.light, base.state.light)
        self.assertTrue(loaded.state.moss_lamp_enabled)
        self.assertAlmostEqual(loaded.state.moss_lamp_angle_deg, 270.0)
        self.assertEqual(loaded.state.window_direction, "north")

    def test_moss_lamp_schedule_controls_active_hours(self) -> None:
        sim = Terrarium(config=SimulationConfig(noise=0.0), seed=1)
        sim.set_moss_lamp(45.0, 0.40)
        sim.set_moss_lamp_schedule(20, 4)

        sim.run(12)
        midday_lamp = sim.state.moss_lamp_light
        sim.run(8)
        evening_lamp = sim.state.moss_lamp_light
        loaded = Terrarium.from_json(sim.state.to_json())

        self.assertEqual(midday_lamp, 0.0)
        self.assertAlmostEqual(evening_lamp, 0.40)
        self.assertEqual(loaded.state.moss_lamp_start_hour, 20)
        self.assertEqual(loaded.state.moss_lamp_duration_hours, 4)

    def test_window_exposure_splits_direct_and_diffuse_light(self) -> None:
        direct = Terrarium(config=SimulationConfig(noise=0.0, light_intensity=1.0), seed=1)
        direct.set_window("south")
        direct.set_window_light_mode("direct")
        direct.run(12)

        diffuse = Terrarium(config=SimulationConfig(noise=0.0, light_intensity=1.0), seed=1)
        diffuse.set_window("south")
        diffuse.set_window_light_mode("diffuse")
        diffuse.run(12)

        self.assertGreater(direct.state.window_direct_light, direct.state.window_diffuse_light)
        self.assertGreater(diffuse.state.window_diffuse_light, diffuse.state.window_direct_light)
        self.assertIn("DIRECT_SUN_PATCH", direct.state.events)
        self.assertIn("DIFFUSE_WINDOW_LIGHT", diffuse.state.events)

    def test_shade_umbrella_softens_window_light_without_blocking_soil(self) -> None:
        base = Terrarium(config=SimulationConfig(noise=0.0, light_intensity=1.0), seed=1)
        base.set_window("south")
        base.run(12)

        shaded = Terrarium(config=SimulationConfig(noise=0.0, light_intensity=1.0), seed=1)
        shaded.set_window("south")
        shaded.set_umbrella(120.0, "south", "leaning_north", 50.0, 70.0, 180.0, 20.0)
        shaded.run(12)
        hardscape = shaded.hardscape_profile()

        self.assertTrue(shaded.state.umbrella_enabled)
        self.assertEqual(float(hardscape["blocked_percent"]), 0.0)
        self.assertLess(shaded.state.window_direct_light, base.state.window_direct_light)
        self.assertLess(shaded.state.placement_heat_bias, base.state.placement_heat_bias)
        self.assertLess(shaded._life_environment()["light"], base._life_environment()["light"])

    def test_legacy_mini_umbrella_save_becomes_external_shade(self) -> None:
        payload = Terrarium(seed=1).snapshot().to_json()
        data = json.loads(payload)
        data["hardscape_items"] = [
            {
                "item_id": "H01",
                "kind": "mini_umbrella",
                "coverage_percent": 8.0,
                "position": "south",
                "orientation": "leaning_north",
                "rotation_deg": 180.0,
                "tilt_deg": 20.0,
                "x_percent": 50.0,
                "y_percent": 70.0,
                "z_base_cm": 0.0,
                "z_top_cm": 4.0,
            }
        ]

        loaded = Terrarium.from_json(json.dumps(data))

        self.assertTrue(loaded.state.umbrella_enabled)
        self.assertEqual(loaded.state.umbrella_coverage_percent, 120.0)
        self.assertEqual(loaded.state.hardscape_items, [])

    def test_season_changes_day_length_and_window_strength(self) -> None:
        summer = Terrarium(
            state=TerrariumState(calendar_start_day_of_year=172, weather_mode="clear"),
            config=SimulationConfig(noise=0.0, light_intensity=1.0),
            seed=1,
        )
        summer.set_window("south")
        summer.run(18)

        winter = Terrarium(
            state=TerrariumState(calendar_start_day_of_year=355, weather_mode="clear"),
            config=SimulationConfig(noise=0.0, light_intensity=1.0),
            seed=1,
        )
        winter.set_window("south")
        winter.run(18)

        self.assertEqual(summer.state.season, "summer")
        self.assertEqual(winter.state.season, "winter")
        self.assertGreater(summer.state.window_light, winter.state.window_light)

        summer.set_window("west")
        summer.run(24)
        self.assertIn("LONG_SUMMER_LIGHT", summer.state.events)

    def test_season_advances_automatically_with_simulated_calendar(self) -> None:
        sim = Terrarium(
            state=TerrariumState(calendar_start_day_of_year=151),
            config=SimulationConfig(noise=0.0),
            seed=1,
        )

        sim.run(24)

        self.assertEqual(sim.state.calendar_day_of_year, 152)
        self.assertEqual(sim.state.season, "summer")

    def test_weather_is_auto_variable_and_saved(self) -> None:
        overcast = Terrarium(
            state=TerrariumState(weather_mode="overcast"),
            config=SimulationConfig(noise=0.0, light_intensity=1.0),
            seed=1,
        )
        overcast.set_window("south")
        overcast.run(12)

        clear = Terrarium(
            state=TerrariumState(weather_mode="clear"),
            config=SimulationConfig(noise=0.0, light_intensity=1.0),
            seed=1,
        )
        clear.set_window("south")
        clear.run(12)

        variable = Terrarium(config=SimulationConfig(noise=0.0, light_intensity=1.0), seed=4)
        variable.run(12)
        loaded = Terrarium.from_json(variable.state.to_json())

        self.assertLess(overcast.state.window_light, clear.state.window_light)
        self.assertIn("CLOUD_MUTED_LIGHT", overcast.state.events)
        self.assertEqual(loaded.state.weather_mode, "variable")
        self.assertEqual(loaded.state.weather_state, variable.state.weather_state)

    def test_placement_heat_bias_distinguishes_west_afternoon_and_lamp_heat(self) -> None:
        west = Terrarium(config=SimulationConfig(noise=0.0, light_intensity=1.0), seed=1)
        west.set_window("west")
        west.run(16)

        east = Terrarium(config=SimulationConfig(noise=0.0, light_intensity=1.0), seed=1)
        east.set_window("east")
        east.run(16)

        lit = Terrarium(config=SimulationConfig(noise=0.0, light_intensity=0.0), seed=1)
        lit.set_moss_lamp(0.0, 0.50)
        lit.set_moss_lamp_schedule(0, 24)
        lit.run(1)

        self.assertGreater(west.state.placement_heat_bias, east.state.placement_heat_bias)
        self.assertGreater(lit.state.placement_heat_bias, 0.0)

    def test_visible_light_events_and_plant_light_observation(self) -> None:
        state = TerrariumState(water=0.05, surface_wetness=0.10, water_cycle_initialized=True)
        sim = Terrarium(state=state, config=SimulationConfig(noise=0.0, light_intensity=0.0), seed=1)
        sim.set_moss_lamp(45.0, 0.50)
        sim.set_moss_lamp_schedule(0, 24)
        planting = sim.add_planting("cushion_moss", 6.0)
        sim.state.surface_wetness = 0.20

        sim.step()

        self.assertIn("MOSS_LAMP_GLOW", sim.state.events)
        self.assertIn("MOSS_LAMP_DRY_EDGE", sim.state.events)
        self.assertIn("moss lamp", sim.plant_light_observation(planting))

    def test_planting_only_checks_minimum_area(self) -> None:
        sim = Terrarium(seed=1)

        planting = sim.add_planting("reindeer_lichen", 3.0, "soil")

        self.assertEqual(planting.plant, "reindeer_lichen")
        self.assertEqual(planting.site, "soil")
        self.assertEqual(sim.planted_area_percent(), 3.0)

    def test_planting_rejects_area_below_plant_minimum(self) -> None:
        sim = Terrarium(seed=1)

        with self.assertRaises(ValueError):
            sim.add_planting("fittonia_mini", 1.0)

    def test_planting_uses_hardscape_plantable_area(self) -> None:
        sim = Terrarium(seed=1)
        sim.place_hardscape("gravel_patch", 30.0)
        sim.place_hardscape("slate", 22.0)

        sim.add_planting("sheet_moss", 35.0)

        with self.assertRaises(ValueError):
            sim.add_planting("ficus_pumila_minima", 30.0)

    def test_planting_can_target_existing_hardscape(self) -> None:
        sim = Terrarium(seed=1)
        item = sim.place_hardscape("driftwood", 12.0)

        planting = sim.add_planting("rabbit_foot_fern", 4.0, item.item_id)

        self.assertEqual(planting.site, "hardscape:H01")
        self.assertEqual(planting.z_cm, item.z_top_cm)

    def test_planting_rejects_missing_hardscape_target(self) -> None:
        sim = Terrarium(seed=1)

        with self.assertRaises(ValueError):
            sim.add_planting("rabbit_foot_fern", 4.0, "hardscape:H99")

    def test_coordinate_planting_auto_mounts_epiphyte_on_hardscape(self) -> None:
        sim = Terrarium(seed=1)
        item = sim.place_hardscape("driftwood", 12.0, x_percent=35.0, y_percent=55.0)

        planting = sim.add_planting("cushion_moss", 6.0, "surface", 35.0, 55.0)

        self.assertEqual(planting.site, f"hardscape:{item.item_id}")
        self.assertEqual(planting.attached_to, item.item_id)
        self.assertAlmostEqual(planting.x_percent, 35.0)
        self.assertAlmostEqual(planting.y_percent, 55.0)
        self.assertGreater(planting.footprint_cm2, 0.0)
        self.assertGreater(planting.height_cm, 0.0)

    def test_soil_plant_rejects_root_collision_with_hardscape(self) -> None:
        sim = Terrarium(seed=1)
        sim.place_hardscape("river_stone", 10.0, x_percent=50.0, y_percent=50.0)

        with self.assertRaisesRegex(ValueError, "root zone collides"):
            sim.add_planting("fittonia_mini", 5.0, "surface", 50.0, 50.0)

    def test_planting_collision_rejects_severe_overlap(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_planting("fittonia_mini", 5.0, "surface", 35.0, 50.0)

        with self.assertRaisesRegex(ValueError, "overlaps"):
            sim.add_planting("fittonia_white", 5.0, "surface", 35.0, 50.0)

    def test_hardscape_rejects_collision_with_existing_planting(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_planting("fittonia_mini", 5.0, "surface", 50.0, 50.0)

        with self.assertRaisesRegex(ValueError, "planting P01"):
            sim.place_hardscape("river_stone", 10.0, x_percent=50.0, y_percent=50.0)

    def test_root_prune_records_crafting_effects(self) -> None:
        sim = Terrarium(seed=1)
        planting = sim.add_planting("fittonia_mini", 5.0)
        planting.reproduction_progress = 20.0

        pruned = sim.prune_roots(planting.planting_id, 20.0)

        self.assertLess(pruned.root_mass_percent, 100.0)
        self.assertEqual(pruned.root_pruned_percent, 20.0)
        self.assertGreater(pruned.prune_stress, 0.0)
        self.assertLess(pruned.reproduction_progress, 20.0)
        self.assertEqual(pruned.status, "recovering")

    def test_planting_has_life_growth_and_reproduction_state(self) -> None:
        sim = Terrarium(seed=1)
        planting = sim.add_planting("sheet_moss", 20.0)

        sim.run(10)

        self.assertGreater(PLANTS[planting.plant].reproduction_rate, 0.0)
        self.assertGreater(planting.age_ticks, 0)
        self.assertIn(planting.survival_state, {"declining", "stressed", "stable", "settling", "thriving"})
        self.assertGreaterEqual(planting.growth_rate, 0.0)
        self.assertGreaterEqual(planting.reproduction_progress, 0.0)

    def test_planting_footprint_expands_during_good_growth(self) -> None:
        state = TerrariumState(nutrients=0.2, carbon_dioxide=0.55, oxygen=0.65)
        sim = Terrarium(state=state, config=SimulationConfig(light_intensity=0.35, noise=0.0), seed=1)
        sim.add_substrate("soil", 3.5, {"sphagnum_moss": 70, "perlite": 30})
        sim.moisten_soil(120.0)
        sim.spray(20)
        planting = sim.add_planting("sheet_moss", 6.0, "surface", 30.0, 50.0)
        before = planting.footprint_cm2

        sim.run(72)

        self.assertGreater(planting.footprint_cm2, before)
        self.assertGreater(planting.area_percent, 6.0)

    def test_growth_overlap_adds_population_pressure_without_expanding(self) -> None:
        state = TerrariumState(water=0.9, nutrients=0.8, carbon_dioxide=0.55, oxygen=0.65)
        sim = Terrarium(state=state, config=SimulationConfig(light_intensity=0.9, noise=0.0), seed=1)
        planting = sim.add_planting("fittonia_mini", 5.0, "surface", 35.0, 50.0)
        neighbor = sim.add_planting("fittonia_white", 5.0, "surface", 65.0, 50.0)
        neighbor.footprint_cm2 *= 2.2
        before_pressure = planting.population_pressure

        sim.run(48)

        self.assertGreaterEqual(planting.population_pressure, before_pressure)

    def test_planting_can_die_under_harsh_conditions(self) -> None:
        state = TerrariumState(water=0.0, nutrients=0.0, oxygen=0.0, carbon_dioxide=1.0, toxicity=1.0)
        sim = Terrarium(state=state, config=SimulationConfig(light_intensity=0.0, noise=0.0), seed=1)
        planting = sim.add_planting("fittonia_mini", 5.0)
        planting.health = 0.1

        sim.step()

        self.assertEqual(planting.status, "dead")
        self.assertEqual(planting.survival_state, "dead")
        self.assertEqual(sim.living_planting_count(), 0)

    def test_plant_reproduction_records_potential_without_adding_commanded_plant(self) -> None:
        sim = Terrarium(seed=1)
        planting = sim.add_planting("sheet_moss", 24.0)
        definition = PLANTS[planting.plant]
        planting.age_ticks = definition.min_reproductive_age_ticks
        planting.reproduction_progress = 99.99

        sim.step()

        self.assertGreaterEqual(planting.offspring_potential, 0)
        self.assertEqual(len(sim.state.plantings), 1)

    def test_animal_group_can_be_added_and_removed(self) -> None:
        sim = Terrarium(seed=1)

        group = sim.add_animals("springtail", 30, "soil")

        self.assertEqual(group.group_id, "A01")
        self.assertEqual(group.animal, "springtail")
        self.assertEqual(group.count, 30)
        self.assertEqual(sim.animal_count_total(), 30)
        removed = sim.remove_animal_group("A01")
        self.assertEqual(removed.animal, "springtail")
        self.assertEqual(sim.state.animal_groups, [])

    def test_animal_count_has_strict_container_bounds(self) -> None:
        sim = Terrarium(seed=1)

        with self.assertRaises(ValueError):
            sim.add_animals("springtail", 1)
        with self.assertRaises(ValueError):
            sim.add_animals("micro_snail", ANIMALS["micro_snail"].max_reasonable_count + 1)

    def test_animal_volume_is_part_of_container_budget(self) -> None:
        sim = Terrarium(seed=1)

        sim.add_animals("dwarf_white_isopod", 8)
        profile = sim.volume_profile()

        self.assertGreater(profile["animal_volume_ml"], 0.0)
        self.assertGreater(profile["animal_activity_area_cm2"], 0.0)
        self.assertGreaterEqual(profile["entity_volume_ml"], profile["animal_volume_ml"])

    def test_animal_group_can_use_specific_hardscape_surface(self) -> None:
        sim = Terrarium(seed=1)
        item = sim.place_hardscape("driftwood", 12.0, x_percent=50.0, y_percent=50.0)

        group = sim.add_animals("springtail", 30, f"hardscape:{item.item_id}:underside")

        self.assertEqual(group.site, f"hardscape:{item.item_id}:underside")
        self.assertEqual(group.attached_to, item.item_id)
        self.assertEqual(group.attachment_surface, "underside")
        self.assertEqual(group.microhabitat, "under hardscape")
        self.assertLess(group.z_cm, item.z_top_cm)

    def test_animal_group_tracks_coordinates_and_habitat_space(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_substrate("soil", 3.0, {"peat_moss": 70, "perlite": 30})

        group = sim.add_animals("springtail", 30, "soil", 25.0, 50.0)
        profile = sim.animal_spatial_profile()

        self.assertAlmostEqual(group.x_percent, 25.0)
        self.assertAlmostEqual(group.y_percent, 50.0)
        self.assertGreater(group.activity_area_cm2, 0.0)
        self.assertGreater(profile["habitat_area_cm2"], 0.0)

    def test_animal_local_space_drops_when_groups_overlap(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_substrate("soil", 2.0, {"peat_moss": 100})
        first = sim.add_animals("springtail", 300, "soil", 50.0, 50.0)
        sim.add_animals("soil_mite", 300, "soil", 50.0, 50.0)

        env = sim._local_animal_environment(first, sim._life_environment())

        self.assertLess(env["animal_space"], 1.0)
        self.assertGreater(env["local_animal_overlap"], 0.0)

    def test_animal_microhabitat_updates_from_local_conditions(self) -> None:
        state = TerrariumState(water=0.10, oxygen=0.62, detritus=0.30)
        sim = Terrarium(state=state, config=SimulationConfig(noise=0.0), seed=1)
        sim.add_substrate("soil", 2.0, {"peat_moss": 100})
        group = sim.add_animals("springtail", 30, "soil", 50.0, 50.0)

        sim.step()

        self.assertIn(group.microhabitat, {"searching damp edges", "soil pore network", "near air pockets"})
        self.assertGreaterEqual(group.shelter_use, 0.0)
        self.assertGreaterEqual(group.visible_activity, 0.0)

    def test_animal_group_moves_toward_better_local_habitat(self) -> None:
        state = TerrariumState(water=0.36, oxygen=0.62, detritus=0.75, leaf_litter_cover=0.70)
        sim = Terrarium(state=state, config=SimulationConfig(noise=0.0), seed=1)
        sim.add_substrate("soil", 2.0, {"peat_moss": 100}, slope_x_cm=3.0)
        group = sim.add_animals("springtail", 30, "soil", 80.0, 50.0)
        before = (group.x_percent, group.y_percent)

        sim.step()

        self.assertNotEqual((group.x_percent, group.y_percent), before)
        self.assertGreater(group.distance_moved_cm, 0.0)
        self.assertIn(group.movement_state, {"relocating", "settled"})
        self.assertTrue(group.movement_reason)

    def test_hardscape_animal_movement_stays_on_attachment_surface(self) -> None:
        sim = Terrarium(seed=1)
        item = sim.place_hardscape("driftwood", 12.0, x_percent=50.0, y_percent=50.0)
        group = sim.add_animals("springtail", 30, f"hardscape:{item.item_id}:groove")

        sim.run(3)

        self.assertEqual(group.attached_to, item.item_id)
        self.assertTrue(group.site.startswith(f"hardscape:{item.item_id}"))
        self.assertIn(group.attachment_surface, HARDSCAPES[item.kind].attach_surfaces)

    def test_hardscape_surface_microclimate_changes_animal_habitat(self) -> None:
        sim = Terrarium(
            state=TerrariumState(water=0.45, oxygen=0.62, detritus=0.55, biofilm=0.20, mold_pressure=0.20),
            config=SimulationConfig(noise=0.0),
            seed=1,
        )
        item = sim.place_hardscape("driftwood", 12.0, x_percent=50.0, y_percent=50.0)
        top = sim.add_animals("springtail", 30, f"hardscape:{item.item_id}:top")
        groove = sim.add_animals("springtail", 30, f"hardscape:{item.item_id}:groove")
        base = sim._life_environment()

        top_env = sim._local_animal_environment(top, base)
        groove_env = sim._local_animal_environment(groove, base)

        self.assertGreater(groove_env["water"], top_env["water"])
        self.assertGreater(groove_env["local_shelter"], top_env["local_shelter"])
        self.assertGreater(groove_env["biofilm"], top_env["biofilm"])
        self.assertGreater(groove_env["mold"], top_env["mold"])

    def test_animal_reproduction_is_slow_and_space_gated(self) -> None:
        sim = Terrarium(seed=1)
        group = sim.add_animals("springtail", 30)

        sim.run(50)

        self.assertEqual(group.count, 30)
        self.assertLess(group.reproduction_progress, 100.0)

    def test_animal_group_can_go_extinct_under_harsh_conditions(self) -> None:
        state = TerrariumState(water=0.0, oxygen=0.0, carbon_dioxide=1.0, toxicity=1.0, detritus=0.0, algae=0.0, microbes=0.0, plants=0.0)
        sim = Terrarium(state=state, config=SimulationConfig(light_intensity=0.0, noise=0.0), seed=1)
        group = sim.add_animals("micro_snail", 1)
        group.mortality_pressure = 0.99

        sim.step()

        self.assertEqual(group.count, 0)
        self.assertEqual(group.survival_state, "dead")
        self.assertEqual(sim.living_animal_count(), 0)

    def test_all_explicit_life_dead_requires_all_plants_and_animals_dead(self) -> None:
        sim = Terrarium(seed=1)
        planting = sim.add_planting("fittonia_mini", 5.0)
        group = sim.add_animals("micro_snail", 1)

        planting.health = 0.0
        planting.status = "dead"
        planting.survival_state = "dead"
        self.assertFalse(sim.all_explicit_life_dead())

        group.count = 0
        group.survival_state = "dead"
        self.assertTrue(sim.all_explicit_life_dead())

    def test_animal_state_round_trips_through_json(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_animals("dwarf_white_isopod", 8, "leaf_litter", 40.0, 60.0)
        sim.run(2)

        loaded = Terrarium.from_json(sim.state.to_json())

        self.assertEqual(len(loaded.state.animal_groups), 1)
        self.assertEqual(loaded.state.animal_groups[0].animal, "dwarf_white_isopod")
        self.assertEqual(loaded.state.animal_groups[0].site, "leaf_litter")
        self.assertAlmostEqual(loaded.state.animal_groups[0].x_percent, 40.0)
        self.assertGreater(loaded.state.animal_groups[0].activity_area_cm2, 0.0)
        self.assertGreater(loaded.state.animal_groups[0].age_ticks, 0)

    def test_visible_ecology_tracks_biofilm_mold_litter_and_root_oxygen(self) -> None:
        state = TerrariumState(
            water=0.95,
            oxygen=0.60,
            detritus=0.90,
            algae=80.0,
            microbes=80.0,
            surface_wetness=0.95,
            condensation_ml=6.0,
            liquid_water_ml=95.0,
            leaf_litter_cover=0.01,
            water_cycle_initialized=True,
        )
        sim = Terrarium(state=state, config=SimulationConfig(noise=0.0), seed=1)
        sim.add_substrate("soil", 4.0, {"peat_moss": 100})
        planting = sim.add_planting("fittonia_mini", 5.0, "surface", 70.0, 50.0)
        before = (sim.state.biofilm, sim.state.mold_pressure, sim.state.leaf_litter_cover, sim.state.root_zone_oxygen)

        sim.run(12)

        self.assertGreater(sim.state.biofilm, before[0])
        self.assertGreater(sim.state.mold_pressure, before[1])
        self.assertGreater(sim.state.leaf_litter_cover, before[2])
        self.assertLess(sim.state.root_zone_oxygen, before[3])
        self.assertLessEqual(planting.root_health, 100.0)

    def test_decomposer_activity_reduces_visible_mold_and_litter(self) -> None:
        state = TerrariumState(water=0.88, detritus=0.85, mold_pressure=0.80, leaf_litter_cover=0.75)
        sim = Terrarium(state=state, config=SimulationConfig(noise=0.0), seed=1)
        sim.add_animals("springtail", 120, "leaf_litter", 50.0, 50.0)
        before = (sim.state.mold_pressure, sim.state.leaf_litter_cover)

        for _ in range(6):
            sim._apply_local_ecological_interactions()

        self.assertLess(sim.state.mold_pressure, before[0])
        self.assertLess(sim.state.leaf_litter_cover, before[1])

    def test_legacy_bloom_fixture_is_damped_by_current_model(self) -> None:
        payload = (FIXTURES_DIR / "legacy_bloom_bottle.json").read_text(encoding="utf-8")
        sim = Terrarium.from_json(payload)
        sim.config.noise = 0.0
        before_algae = sim.state.algae
        before_litter = sim.state.leaf_litter_cover

        sim.run(24)

        self.assertLess(sim.state.algae, before_algae * 0.90)
        self.assertTrue(all(planting.death_processed for planting in sim.state.plantings))
        self.assertGreater(sim.state.leaf_litter_cover, before_litter)
        self.assertGreater(sim.state.nutrients, 0.0)
        self.assertIn("PLANT_COLLAPSE", sim.state.events)
        self.assertIn("ALGAE_FILM", sim.state.events)
        self.assertTrue({"O2_CRASH", "CO2_SATURATION", "ROT_SPIKE"} & set(sim.state.events))
        group = sim.state.animal_groups[0]
        if group.count > 0:
            self.assertIn(group.survival_state, {"declining", "stressed"})
            self.assertEqual(group.population_trend, "stalled")

    def test_under_minimum_colony_is_not_reported_as_thriving(self) -> None:
        state = TerrariumState(water=0.86, oxygen=0.82, detritus=0.55, microbes=80.0)
        sim = Terrarium(state=state, config=SimulationConfig(noise=0.0), seed=1)
        group = sim.add_animals("springtail", 5, "soil")
        group.count = 1
        group.survival_state = "thriving"
        group.population_trend = "growing"

        sim.step()

        self.assertIn(group.survival_state, {"declining", "stressed"})
        self.assertEqual(group.population_trend, "stalled")
        self.assertLess(group.growth_rate, ANIMALS["springtail"].base_growth_rate * 0.30)

    def test_food_shortage_can_leave_visible_consumer_marks_on_plants(self) -> None:
        state = TerrariumState(
            water=0.86,
            algae=0.0,
            detritus=0.0,
            plants=5.0,
            biofilm=0.0,
            microbes=2.0,
        )
        sim = Terrarium(state=state, config=SimulationConfig(noise=0.0), seed=1)
        planting = sim.add_planting("fittonia_mini", 5.0, "surface", 50.0, 50.0)
        sim.add_animals("tiny_slug", 1, "surface", 50.0, 50.0)

        sim._apply_local_ecological_interactions()

        self.assertGreater(planting.visible_damage_percent, 0.0)
        self.assertIn("nibbled", planting.last_interaction)

    def test_mold_pressure_can_touch_lower_growth_visibly(self) -> None:
        state = TerrariumState(
            water=0.95,
            surface_wetness=0.95,
            mold_pressure=0.86,
            leaf_litter_cover=0.80,
        )
        sim = Terrarium(state=state, config=SimulationConfig(noise=0.0), seed=1)
        planting = sim.add_planting("cushion_moss", 6.0, "surface", 50.0, 50.0)

        sim._apply_local_ecological_interactions()

        self.assertGreater(planting.mold_contact_percent, 0.0)
        self.assertIn("fuzz", planting.last_interaction)

    def test_seal_records_crafting_completion_and_blocks_more_crafting(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_substrate("soil", 2.0, {"peat_moss": 100})
        sim.add_planting("fittonia_mini", 5.0)

        sim.seal()

        self.assertTrue(sim.state.sealed)
        self.assertEqual(sim.state.sealed_tick, sim.state.tick)
        with self.assertRaises(ValueError):
            sim.add_substrate("drainage", 1.0, {"leca": 100})
        with self.assertRaises(ValueError):
            sim.add_planting("sheet_moss", 10.0)
        with self.assertRaises(ValueError):
            sim.spray(1)

    def test_seal_syncs_abstract_biomass_to_crafted_contents(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_substrate("soil", 3.0, {"peat_moss": 60, "compost": 40})
        sim.moisten_soil(40.0)
        sim.add_planting("fittonia_mini", 5.0)
        sim.add_animals("springtail", 30)

        sim.seal()

        self.assertLess(sim.state.plants, 20.0)
        self.assertLess(sim.state.algae, 18.0)
        self.assertLess(sim.state.grazers, 2.0)
        self.assertGreater(sim.state.microbes, 8.0)

    def test_complex_recipe_survives_first_ten_days_after_seal(self) -> None:
        sim = self._build_complex_recipe()

        sim.run(240)

        self.assertGreaterEqual(sim.living_planting_count(), 5)
        self.assertGreaterEqual(sim.living_animal_count(), 35)
        self.assertGreaterEqual(sim.stability_score(), 65)
        self.assertGreater(sim.state.oxygen, 0.30)
        self.assertLess(sim.state.carbon_dioxide, 0.70)
        self.assertGreater(sim.state.water, 0.38)
        self.assertNotIn("GRAZER_LOSS", sim.state.events)

    def test_stable_umbrella_recipe_remains_observable_for_three_months(self) -> None:
        sim = self._build_stable_umbrella_recipe()

        sim.run(2160)

        self.assertGreaterEqual(sim.living_planting_count(), 3)
        self.assertGreaterEqual(sim.living_animal_count(), 30)
        self.assertGreaterEqual(sim.stability_score(), 60)
        self.assertNotIn("O2_CRASH", sim.state.events)

    def test_balanced_fittonia_recipe_uses_nutrients_without_rot_bloom(self) -> None:
        sim = self._build_balanced_fittonia_recipe()

        sim.run(720)

        self.assertEqual(sim.living_planting_count(), 3)
        self.assertEqual(sim.living_animal_count(), 40)
        self.assertGreaterEqual(sim.stability_score(), 75)
        self.assertLess(sim.state.nutrients, 0.40)
        self.assertLess(sim.state.detritus, 0.35)
        self.assertNotIn("ROT_SPIKE", sim.state.events)

    def test_carnivorous_bog_keeps_wet_specialists_alive(self) -> None:
        sim = self._build_carnivorous_bog_recipe()

        sim.run(720)

        self.assertEqual(sim.living_planting_count(), 3)
        self.assertGreaterEqual(sim.stability_score(), 65)
        self.assertGreater(sim.state.water, 0.55)
        self.assertLess(sim.state.nutrients, 0.30)
        self.assertNotIn("ROT_SPIKE", sim.state.events)

    def test_tiny_crowded_vial_becomes_gas_limited(self) -> None:
        sim = self._build_tiny_crowded_vial_recipe()

        sim.run(336)

        self.assertLess(sim.stability_score(), 70)
        self.assertTrue({"O2_CRASH", "CO2_SATURATION"} & set(sim.state.events))
        self.assertLess(sim.living_animal_count(), 20)

    def test_plant_resource_traits_change_photosynthesis_and_nutrient_use(self) -> None:
        def prepared(plant: str) -> Terrarium:
            sim = Terrarium(config=SimulationConfig(noise=0.0), seed=1)
            sim.add_substrate("soil", 3.0, {"peat_moss": 60, "compost": 40})
            sim.moisten_soil(50.0)
            sim.add_planting(plant, 8.0)
            sim.seal()
            sim.state.plants = 30.0
            sim.state.water = 0.72
            sim.state.nutrients = 0.58
            sim.state.carbon_dioxide = 0.42
            sim.state.tick = 8
            return sim

        fittonia = prepared("fittonia_mini")
        moss = prepared("cushion_moss")

        fittonia.step()
        moss.step()

        self.assertGreater(PLANTS["fittonia_mini"].nutrient_demand, PLANTS["cushion_moss"].nutrient_demand)
        self.assertGreater(fittonia.state.flux.photosynthesis, moss.state.flux.photosynthesis)
        self.assertLess(fittonia.state.nutrients, moss.state.nutrients)

    def test_animal_resource_traits_change_diet_and_feeding_rate(self) -> None:
        def prepared(animal: str, count: int) -> Terrarium:
            state = TerrariumState(
                water=0.82,
                oxygen=0.70,
                carbon_dioxide=0.42,
                detritus=0.85,
                algae=70.0,
                plants=90.0,
                microbes=60.0,
                biofilm=0.75,
                mold_pressure=0.70,
                leaf_litter_cover=0.72,
                grazers=5.0,
            )
            sim = Terrarium(state=state, config=SimulationConfig(noise=0.0), seed=1)
            group = sim.add_animals(animal, count)
            group.visible_activity = 80.0
            sim.state.tick = 8
            return sim

        springtail = prepared("springtail", 30)
        isopod = prepared("dwarf_white_isopod", 6)

        springtail_profile = springtail._animal_resource_profile()
        isopod_profile = isopod._animal_resource_profile()
        springtail.step()
        isopod.step()

        self.assertGreater(springtail_profile["diet"]["detritus"], springtail_profile["diet"]["plants"])
        self.assertGreater(isopod_profile["feeding_rate"], springtail_profile["feeding_rate"])
        self.assertGreater(isopod.state.flux.grazing, springtail.state.flux.grazing)

    def test_sealed_state_round_trips_through_json(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_animals("springtail", 30)
        sim.seal()

        loaded = Terrarium.from_json(sim.state.to_json())

        self.assertTrue(loaded.state.sealed)
        self.assertEqual(loaded.state.sealed_tick, 0)
        self.assertEqual(len(loaded.state.animal_groups), 1)

    def test_planting_state_round_trips_through_json(self) -> None:
        sim = Terrarium(seed=1)
        sim.add_planting("fittonia_mini", 5.0, "surface")
        sim.prune_roots("P01", 10.0)
        sim.run(2)

        loaded = Terrarium.from_json(sim.state.to_json())

        self.assertEqual(len(loaded.state.plantings), 1)
        self.assertEqual(loaded.state.plantings[0].plant, "fittonia_mini")
        self.assertEqual(loaded.state.plantings[0].root_pruned_percent, 10.0)
        self.assertGreater(loaded.state.plantings[0].age_ticks, 0)


if __name__ == "__main__":
    unittest.main()
