import math
import random
from collections import Counter
from copy import deepcopy
from logging import getLogger

from opensimplex import noise2
from stripe_kit import (
    AssetInstance,
    AssetSpec,
    SceneSpec,
    TerrainInstance,
)
from trimesh import Trimesh

from forest_gen_utils.asset_dist import (
    Species,
)
from forest_gen_utils.asset_dist.grass import GrassDistributor
from forest_gen_utils.asset_dist.understory import UnderstoryDistributor
from forest_gen_utils.forest import ForestBuilder, ForestConfig
from forest_gen_utils.obstacles import ObstacleBuilder, ObstacleConfig, ObstacleSpec
from forest_gen_utils.terrain import Terrain, TerrainBuilder, TerrainConfig
from forest_gen_utils.travelsibilitymap import (
    TraversabilityConfig,
    TraversabilityMapBuilder,
)

# this is sort of a facade file for the whole module
from .assets import PlantModelFactory

logger = getLogger(__name__)

# i have heard many a voice from vile dissidents that showcase their weakness
# and complain about how convoluted this file is. As such overt comments
# have been added


# this is just a simple placeholder function that classifies the terrain,
# used for splitting the terrain into semantic classes


# Temp solution


forest_params = {
    "scene_density": 1.2,
    "simulation_years": 70,
}


grass_params = {
    "scene_density": 1.35,
    "patch_scale": 0.10,
    "hard_radius": 0.5,
    "falloff_radius": 2.0,
    "species_density": 4.28,
    "reproduction_rate": 3,
    "reproduction_radius": 3,
    "max_age": 16,
    "radius": 0.3,
    "simulation_years": 20,
}

obstacle_params = {
    "specs": [
        ("rock", 2.0, 0.55),
        ("stump", 1.2, 0.35),
        ("fallen_trunk", 1.4, 0.10),
    ],
    "density": 0.005,
    "min_distance": 1.8,
    "seed": 21,
}

understory_params = {
    "scene_density": 0.036,
    "preferred_distance": 5.0,
    "avoid_radius": 2.2,
    "falloff_radius": 11.0,
    "patch_scale": 0.12,
    "patch_threshold": 0.5,
    "species_density": 0.026,
    "reproduction_rate": 1,
    "reproduction_radius": 6.0,
    "radius": 2.6,
    "max_age": 35,
    "simulation_years": forest_params["simulation_years"],
}


def classify_terrain(x: float, y: float) -> str:
    """Classify the terrain based on the x and y coordinates.

    Args:
        x (float): The x coordinate.
        y (float): The y coordinate.

    Returns:
        str: The classification of the terrain.
    """
    if noise2(x, y) > 0:
        return "forest"
    return "plain"


GRASS_BASE_COLOR = (0.07, 0.42, 0.07)
GRASS_BASE_MATERIAL = "../forest-gen/models/materials/Ground/Mulch.mdl"


# we need this later on to properly place the trees
class HeightmapTerrain(TerrainInstance):
    """A wrapper over the TerrainInstance class, that holds the underlying
    heightmap Callable"""

    def __init__(
        self,
        mesh: list[tuple[Trimesh, list[tuple[str, str]]]],
        origin: tuple[float, float, float],
        size: tuple[float, float],
        raw: Terrain,
        traversability_cfg: TraversabilityConfig | None = None,
    ):
        """Initialize the HeightmapTerrain instance.

        Args:
            mesh (list[tuple[Trimesh, list[tuple[str, str]]]]): A list of meshes with their tags.
            origin (tuple[float, float, float]): The origin of the terrain.
            size (tuple[float, float]): The size of the terrain.
            raw (Terrain): The encapsulated logical heightmap.
        """
        super().__init__(mesh, origin, size, GRASS_BASE_COLOR)
        self.raw = raw
        self.traversability_cfg = traversability_cfg or TraversabilityConfig()
        self.traversability_map = TraversabilityMapBuilder(
            raw,
            resolution_factor=self.traversability_cfg.resolution_factor,
            max_slope_deg=self.traversability_cfg.max_slope_deg,
        )


class ForestGenSpec(SceneSpec):
    """A specification for generating a forest scene."""

    def __init__(
        self,
        size: int = 256,
        margin: int = 10,
        traversability_cfg: TraversabilityConfig | None = None,
    ):
        """Initialize the forest generation specification.

        Args:
            size (int): The size of the terrain.
            robot (AssetBaseCfg | None): The robot configuration.
        """

        # here the assets are hooked up to the scene
        super().__init__(
            size=(size, size),
            palette=[PlantSpec(origin_margin=margin)],
        )
        self.side = size
        self.origin = (
            random.randint(margin, size - margin),
            random.randint(margin, size - margin),
        )
        self.traversability_cfg = traversability_cfg or TraversabilityConfig()

    def generate(self) -> HeightmapTerrain:
        # please note how we return a custom subclass that holds extra data,
        # so that the hooked up asset classes can depend on that extra data

        generator = (
            TerrainBuilder()
            .with_noise("fractal")
            .with_microrelief(True)
            .with_moisture_model({})
            .build()
        )
        terrain_cfg = TerrainConfig(
            size=self.side,
            resolution=0.25,
            scale=4.0,
            octaves=2,
            height_scale=2,
            apply_microrelief=True,
        )
        terrain = generator.generate(terrain_cfg)

        return HeightmapTerrain(
            terrain.to_meshes(classify_terrain),
            (self.origin[0], self.origin[1], terrain(*self.origin) + 1.0),
            self.size,
            terrain,
            self.traversability_cfg,
        )


class PlantSpec(AssetSpec):
    """Specification for generating all plant assets in a forest scene. One Spec to rule them all."""

    def __init__(
        self,
        sim_duration: int = 10,
        scene_density: float = 1.0,
        origin_margin: float = 10.0,
    ):
        """Construct a PlantSpec.

        Args:
            sim_duration (int, optional): The duration in years of the simulation used for tree position generation. Defaults to 10.
            scene_density (float, optional): Global density multiplier applied to the generated scene. Defaults to 1.0.
            origin_margin (float, optional): The margin around the origin for generating assets. Defaults to 10.0.
        """
        super().__init__("all")
        self.forest_cfg = ForestConfig(scene_density, sim_duration)
        self.origin_margin = origin_margin

    def generate(self, terrain: HeightmapTerrain) -> list[AssetInstance]:
        """Generate a list of instances based on the given terrain.

        Args:
            terrain (HeightmapTerrain): The terrain instance on which to generate.

        Returns:
            list[AssetInstance]: A list of generated grass asset instances.
        """

        # List for all assets
        asset_list = []

        # create factory for assets
        model_factory = PlantModelFactory()

        forest = (
            ForestBuilder()
            .with_size(terrain.size)
            .with_terrain(terrain.raw)
            .add_species("trees", Species("Pine", 10, 0.005, radius=2.0))
            .build()
        )

        # do the trees simulation
        logger.debug("Starting Tree simulation")
        state = forest.generate(self.forest_cfg)
        tree_positions = [plant.coords for plant in state]

        logger.debug("Tree simulation finished")

        origin_2d = (terrain.origin[0], terrain.origin[1])
        # then we create the tree instances
        obstacles: list[tuple[float, float]] = []

        for i, plant in enumerate(state):
            if math.dist(plant.coords, origin_2d) > self.origin_margin:

                obstacles.append(plant.coords)

                asset_list.append(
                    self.create_instance(
                        f"{plant.species.name}_{i}",
                        model_factory.get_usdz_model_by_name(
                            plant.species.name, random.randint(1, 3)
                        ),
                        (
                            plant.coords[0],
                            plant.coords[1],
                            terrain.raw(*plant.coords),
                        ),
                        (0.0, 0.0, 0.0, 0.0),
                        {"color": "green", "species": plant.species.name},
                    )
                )

        if obstacles:
            terrain.traversability_map.add_obstacle_score(
                obstacles,
                obstacle_influence_radius=terrain.traversability_cfg.obstacle_influence_radius,
                obstacle_penalty=terrain.traversability_cfg.obstacle_penalty,
            )

        # do the grass simulation
        logger.debug("Generating grass")

        # old grass distr when we hoped for terrain mesh textures
        #
        # unfiltered_grass = grass_points(
        #     int(terrain.size[0]), int(terrain.size[1]), 0.5
        # )
        # grass = remove_grass_near_tree(
        #     unfiltered_grass, [plant.coords for plant in state]
        # )

        grass_generator = GrassDistributor(
            terrain.raw,
            tree_positions,
            patch_scale=grass_params["patch_scale"],
            hard_radius=grass_params["hard_radius"],
            falloff_radius=grass_params["falloff_radius"],
            max_age=grass_params["max_age"],
            species_density=grass_params["species_density"],
            reproduction_rate=grass_params["reproduction_rate"],
            reproduction_radius=grass_params["reproduction_radius"],
            radius=grass_params["radius"],
        )
        grass_state = grass_generator.generate(
            ForestConfig(scene_density=grass_params["scene_density"], years=0)
        )
        grass_states = []
        for _ in range(grass_params["simulation_years"]):
            grass_state.run_state(1)
            grass_states.append(deepcopy(grass_state))

        final_grass_state = grass_states[-1] if grass_states else grass_state
        logger.debug("Grass generation finished")

        for i, plant in enumerate(final_grass_state):
            # Skip grass near the origin
            # if math.dist(plant.coords, origin_2d) <= self.origin_margin:
            #     continue

            asset_list.append(
                self.create_instance(
                    f"Grass_{i}",
                    model_factory.get_usdz_model_by_name("Grass", 1),
                    (
                        plant.coords[0],
                        plant.coords[1],
                        terrain.raw(*plant.coords) - 0.1,
                    ),
                    (0.0, 0.0, 0.0, 0.0),  # for glb (0.70711, 0.70711, 0.0, 0.0),
                    {"color": "blue", "species": "Grass"},
                )
            )

        # Do the understory simulation
        logger.debug("Generating understory")

        understory_generator = UnderstoryDistributor(
            terrain.raw,
            tree_positions,
            preferred_distance=understory_params["preferred_distance"],
            avoid_radius=understory_params["avoid_radius"],
            falloff_radius=understory_params["falloff_radius"],
            patch_scale=understory_params["patch_scale"],
            patch_threshold=understory_params["patch_threshold"],
            species_density=understory_params["species_density"],
            reproduction_rate=understory_params["reproduction_rate"],
            reproduction_radius=understory_params["reproduction_radius"],
            radius=understory_params["radius"],
            max_age=understory_params["max_age"],
        )

        understory_state = understory_generator.generate(
            ForestConfig(scene_density=understory_params["scene_density"], years=0)
        )

        understory_states = []
        for _ in range(understory_params["simulation_years"]):
            understory_state.run_state(1)
            understory_states.append(deepcopy(understory_state))

        final_understory_state = (
            understory_states[-1] if understory_states else understory_state
        )

        logger.debug("Finished generating understory")

        for i, plant in enumerate(final_understory_state):
            asset_list.append(
                self.create_instance(
                    f"Bush_{i}",
                    model_factory.get_usdz_model_by_name("Bush", 1),
                    (plant.coords[0], plant.coords[1], terrain.raw(*plant.coords)),
                    (0.0, 0.0, 0.0, 0.0),
                    {"color": "purple", "species": "Bush"},
                )
            )

        # Do the obstacle simulation
        logger.debug("Generating obstacles")

        obstacle_builder = (
            ObstacleBuilder()
            .with_specs(
                tuple(
                    ObstacleSpec(name, radius=radius, weight=weight)
                    for name, radius, weight in obstacle_params["specs"]
                )
            )
            .with_seed(obstacle_params["seed"])
        )
        obstacle_generator = obstacle_builder.build()
        obstacle_config = ObstacleConfig(
            size=terrain.size,
            density=obstacle_params["density"],
            min_distance=obstacle_params["min_distance"],
        )

        logger.debug("Finished generating obstacles")

        for i, obs in enumerate(obstacle_generator.generate(obstacle_config)):
            asset_list.append(
                self.create_instance(
                    f"Rock_{i}",
                    model_factory.get_usdz_model_by_name(
                        "Rock", random.randint(1, 7), 1.5
                    ),
                    (obs.coords[0], obs.coords[1], terrain.raw(*obs.coords)),
                    (0.0, 0.0, 0.0, 0.0),
                    {"color": "red", "species": "obstacle"},
                )
            )

        logger.debug(
            f"{dict(Counter(ass.name.split('_', 1)[0] for ass in asset_list))}"
        )
        return asset_list
