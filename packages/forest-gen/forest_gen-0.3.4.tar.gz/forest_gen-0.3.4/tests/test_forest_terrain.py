# import unittest
# import numpy as np
# from forest_gen.temp import ForestBuilder, ForestConfig, Species


# class TestForestTerrain(unittest.TestCase):
#     def test_viability_wrapped(self):
#         moisture = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=float)
#         species = Species("oak", 5, 0.1, viability_map=lambda x, y: 0.5)
#         builder = (
#             ForestBuilder().with_size((2, 2)).add_species("trees", species)
#         )
#         builder.with_terrain_data(moisture, 1.0)
#         fg = builder.build()
#         _ = fg.generate(ForestConfig())
#         self.assertAlmostEqual(species.viability_map(0.5, 0.5), 0.5 * 1.0)
#         self.assertAlmostEqual(species.viability_map(1.2, 0.3), 0.5 * 0.0)


# if __name__ == "__main__":
#     unittest.main()
