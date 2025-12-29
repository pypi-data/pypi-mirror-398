from pathlib import Path
import sys

import numpy as np

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from forest_gen.terrain import Terrain, TerrainConfig
from forest_gen.travelsibilitymap import (
    TraversabilityConfig,
    TraversabilityMapBuilder,
)


def make_ramp_terrain(size: int = 4) -> Terrain:
    config = TerrainConfig(size=size, resolution=1.0)
    x_profile = np.linspace(0, 2.0, config.cols)
    heightmap = np.tile(x_profile, (config.rows, 1))
    zeros = np.zeros_like(heightmap)
    return Terrain(config, heightmap, zeros, zeros, zeros, zeros)


def test_traversability_heatmaps_change_with_parameters():
    terrain = make_ramp_terrain()
    obstacle_points = [(1.0, 1.0)]

    base_cfg = TraversabilityConfig()
    base_map = TraversabilityMapBuilder(
        terrain,
        resolution_factor=base_cfg.resolution_factor,
        max_slope_deg=base_cfg.max_slope_deg,
    )
    base_map.add_obstacle_score(
        obstacle_points,
        obstacle_influence_radius=base_cfg.obstacle_influence_radius,
        obstacle_penalty=base_cfg.obstacle_penalty,
    )
    base_score = base_map.get_score()

    steep_cfg = TraversabilityConfig(max_slope_deg=10.0)
    steep_map = TraversabilityMapBuilder(
        terrain,
        resolution_factor=steep_cfg.resolution_factor,
        max_slope_deg=steep_cfg.max_slope_deg,
    )
    steep_map.add_obstacle_score(
        obstacle_points,
        obstacle_influence_radius=steep_cfg.obstacle_influence_radius,
        obstacle_penalty=steep_cfg.obstacle_penalty,
    )
    steep_score = steep_map.get_score()

    obstacle_cfg = TraversabilityConfig(
        obstacle_influence_radius=3.0, obstacle_penalty=0.1
    )
    obstacle_map = TraversabilityMapBuilder(
        terrain,
        resolution_factor=obstacle_cfg.resolution_factor,
        max_slope_deg=obstacle_cfg.max_slope_deg,
    )
    obstacle_map.add_obstacle_score(
        obstacle_points,
        obstacle_influence_radius=obstacle_cfg.obstacle_influence_radius,
        obstacle_penalty=obstacle_cfg.obstacle_penalty,
    )
    obstacle_score = obstacle_map.get_score()

    assert not np.allclose(base_score, steep_score)
    assert not np.allclose(base_score, obstacle_score)
