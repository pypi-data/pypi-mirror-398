"""Spatial representations using Semantic Pointers.

This module provides Spatial Semantic Pointers (SSP) for encoding continuous
spatial locations and scenes using fractional power encoding.
"""

from vsax.spatial.ssp import SpatialSemanticPointers, SSPConfig
from vsax.spatial.utils import (
    create_spatial_scene,
    plot_ssp_2d_scene,
    region_query,
    similarity_map_2d,
)

__all__ = [
    "SpatialSemanticPointers",
    "SSPConfig",
    "create_spatial_scene",
    "similarity_map_2d",
    "plot_ssp_2d_scene",
    "region_query",
]
