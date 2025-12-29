# import unittest
# from forest_gen.temp import SimulationState, Plant, Species, Simulation
# from math import dist


# class TestSimulationState(unittest.TestCase):

#     species_a = Species("a", 5, 0.02, radius=2.0)
#     species_b = Species("b", 4, 0.05)

#     def test_iter(self):
#         init = (
#             Plant((0, 0), self.species_a, 0),
#             Plant((1, 1), self.species_b, 0),
#         )
#         state = SimulationState(init, (10, 10))
#         for el in init:
#             self.assertIn(el, state)
#         state = SimulationState(init, (20, 20))
#         for el in init:
#             self.assertIn(el, state)

#     def test_find_nearby(self):
#         init = (
#             Plant((0, 0), self.species_a, 0),
#             Plant((1, 1), self.species_b, 0),
#             Plant((10, 10), self.species_a, 0),
#         )
#         state = SimulationState(init, (10, 10))
#         self.assertIn(init[1], state.get_nearby(init[0]))
#         self.assertNotIn(init[2], state.get_nearby(init[0]))
#         state = SimulationState(init, (20, 20))
#         self.assertIn(init[1], state.get_nearby(init[0]))
#         self.assertNotIn(init[2], state.get_nearby(init[0]))

#     def test_auto_find_nearby(self):
#         size = 10
#         for size in range(1, 50):
#             spec = Species("spec", 5, 2, radius=float(size))
#             init = (Plant((i, i), spec, 0) for i in range(size))
#             state = SimulationState(init, (size, size))
#             for el in init:
#                 self.assertIn(el, state.get_nearby(el))

#     def test_init_state(self):
#         state = Simulation(
#             (100, 100), {"trees": {self.species_a, self.species_b}}
#         ).new_state(1.0)
#         not_empty = False
#         for i, a in enumerate(state):
#             not_empty = True
#             for j, b in enumerate(state):
#                 if i == j:
#                     continue
#                 self.assertGreaterEqual(
#                     dist(a.coords, b.coords), a.species.radius
#                 )
#         self.assertTrue(not_empty)

#     def test_post_sim_state(self):
#         state = Simulation(
#             (100, 100), {"trees": {self.species_a, self.species_b}}
#         ).new_state(1.0)
#         state.run_state(5)
#         not_empty = False
#         for i, a in enumerate(state):
#             not_empty = True
#             for j, b in enumerate(state):
#                 if i == j:
#                     continue
#                 self.assertGreaterEqual(
#                     dist(a.coords, b.coords), a.species.radius
#                 )
#         self.assertTrue(not_empty)

#     def test_reproduction_limit(self):
#         species = Species(
#             "fast",
#             3,
#             0.1,
#             reproduction_rate=3,
#             reproduction_radius=5.0,
#             radius=1.0,
#         )
#         init = [Plant((float(i), 0.0), species, 0) for i in range(5)]
#         state = SimulationState(init, (50, 10))
#         max_pop = state.grid_width * state.grid_height
#         state.run_state(10, max_population=max_pop)
#         self.assertGreater(len(state), len(init))
#         self.assertLessEqual(len(state), max_pop)


# if __name__ == "__main__":
#     unittest.main()
