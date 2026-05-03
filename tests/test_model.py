import unittest

from terrarium.model import SimulationConfig, Terrarium, TerrariumState


class TerrariumModelTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
