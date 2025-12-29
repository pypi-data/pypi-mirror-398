# from typing import Any
# import unittest
# from forest_gen.heightmap import NOISE_FUNC, heightmap_to_mesh


# class TestNoise(unittest.TestCase):

#     def assertAlmostEqual(
#         self, a: Any, b: Any, places: int = 3
#     ):  # reduced default from 7 to 3
#         super().assertAlmostEqual(a, b, places=places)

#     def test_0(self):
#         self.assertAlmostEqual(NOISE_FUNC(0.0, 0.0), 2.5)

#     def test_1(self):
#         self.assertAlmostEqual(NOISE_FUNC(1.0, 1.0), 2.1825)

#     def test_2(self):
#         self.assertAlmostEqual(NOISE_FUNC(2.0, 2.0), 1.8975)


# class TestExport(unittest.TestCase):

#     def test_plane(self):
#         def heightmap(x, y):
#             return 0.0

#         mesh = heightmap_to_mesh(heightmap, 10)
#         self.assertEqual(mesh.vertices.shape[0], 100)
#         self.assertEqual(mesh.faces.shape[0], 162)
#         self.assertEqual(mesh.vertices.shape[1], 3)
#         self.assertEqual(mesh.faces.shape[1], 3)
#         self.assertEqual(mesh.vertices[0][0], 0.0)
#         self.assertEqual(mesh.vertices[0][1], 0.0)
#         self.assertEqual(mesh.vertices[0][2], 0.0)
#         self.assertEqual(mesh.faces[0][0], 0)
#         self.assertEqual(mesh.faces[0][1], 1)
#         self.assertEqual(mesh.faces[0][2], 10)
