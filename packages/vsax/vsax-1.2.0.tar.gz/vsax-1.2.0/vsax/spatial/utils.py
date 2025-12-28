"""Utility functions for Spatial Semantic Pointers."""

from typing import Any

import jax.numpy as jnp

from vsax.representations import ComplexHypervector
from vsax.similarity import cosine_similarity
from vsax.spatial.ssp import SpatialSemanticPointers


def create_spatial_scene(
    ssp: SpatialSemanticPointers,
    objects_and_locations: dict[str, list[float]],
) -> ComplexHypervector:
    """Create a scene by bundling multiple object-location bindings.

    Convenience function that:
    1. Binds each object to its location: Object_i ⊗ S(x_i, y_i)
    2. Bundles all bindings into a single scene hypervector

    Args:
        ssp: SpatialSemanticPointers instance.
        objects_and_locations: Dictionary mapping object names to coordinates.
            Example: {"apple": [1.0, 2.0], "banana": [3.0, 4.0]}

    Returns:
        Scene hypervector containing all object-location pairs.

    Raises:
        ValueError: If objects_and_locations is empty.
        KeyError: If any object name is not in ssp.memory.

    Example:
        >>> scene = create_spatial_scene(ssp, {
        ...     "apple": [1.0, 2.0],
        ...     "banana": [3.0, 4.0],
        ...     "cherry": [5.0, 1.0]
        ... })
        >>> # Query: what's at (1.0, 2.0)?
        >>> result = ssp.query_location(scene, [1.0, 2.0])
    """
    if not objects_and_locations:
        raise ValueError("objects_and_locations cannot be empty")

    # Bind each object to its location
    bindings = []
    for obj_name, coords in objects_and_locations.items():
        binding = ssp.bind_object_location(obj_name, coords)
        bindings.append(binding.vec)

    # Bundle all bindings
    scene_vec = ssp.model.opset.bundle(*bindings)
    return ComplexHypervector(scene_vec)


def similarity_map_2d(
    ssp: SpatialSemanticPointers,
    query_hv: ComplexHypervector,
    x_range: tuple[float, float],
    y_range: tuple[float, float],
    resolution: int = 50,
) -> tuple[jnp.ndarray, jnp.ndarray, jnp.ndarray]:
    """Generate 2D similarity heatmap for visualization.

    Computes similarity between query_hv and encoded locations across a 2D grid.
    Useful for visualizing "where" an object is located, or what regions match
    a given hypervector.

    Args:
        ssp: SpatialSemanticPointers instance (must be 2D).
        query_hv: Query hypervector to compare against locations.
        x_range: (min_x, max_x) range for grid.
        y_range: (min_y, max_y) range for grid.
        resolution: Number of grid points per axis (default: 50).

    Returns:
        Tuple of (X, Y, similarities):
            - X: 2D meshgrid of x coordinates (resolution x resolution)
            - Y: 2D meshgrid of y coordinates (resolution x resolution)
            - similarities: 2D array of similarity values (resolution x resolution)

    Raises:
        ValueError: If ssp is not 2D (num_axes != 2).

    Example:
        >>> # Create scene with apple at (3.5, 2.1)
        >>> scene = ssp.bind_object_location("apple", [3.5, 2.1])
        >>> # Query where apple is
        >>> apple_location = ssp.query_object(scene, "apple")
        >>> # Generate heatmap
        >>> X, Y, sims = similarity_map_2d(
        ...     ssp, apple_location,
        ...     x_range=(0, 5), y_range=(0, 5), resolution=50
        ... )
        >>> # Peak should be near (3.5, 2.1)
    """
    if ssp.config.num_axes != 2:
        raise ValueError(
            f"similarity_map_2d only works with 2D SSP. Got num_axes={ssp.config.num_axes}"
        )

    # Create grid
    x = jnp.linspace(x_range[0], x_range[1], resolution)
    y = jnp.linspace(y_range[0], y_range[1], resolution)
    X, Y = jnp.meshgrid(x, y)

    # Compute similarities
    similarities = jnp.zeros((resolution, resolution))

    for i in range(resolution):
        for j in range(resolution):
            loc = ssp.encode_location([X[i, j].item(), Y[i, j].item()])
            sim = cosine_similarity(query_hv.vec, loc.vec)
            similarities = similarities.at[i, j].set(sim)

    return X, Y, similarities


def plot_ssp_2d_scene(
    ssp: SpatialSemanticPointers,
    scene: ComplexHypervector,
    object_names: list[str],
    x_range: tuple[float, float] = (0, 5),
    y_range: tuple[float, float] = (0, 5),
    resolution: int = 30,
    figsize: tuple[int, int] = (12, 4),
) -> Any:  # matplotlib.figure.Figure when matplotlib is installed
    """Plot 2D scene showing where each object is located.

    Creates a figure with subplots showing similarity heatmaps for each object.
    Requires matplotlib.

    Args:
        ssp: SpatialSemanticPointers instance (must be 2D).
        scene: Scene hypervector containing object-location bindings.
        object_names: List of object names to visualize.
        x_range: (min_x, max_x) for plot (default: (0, 5)).
        y_range: (min_y, max_y) for plot (default: (0, 5)).
        resolution: Grid resolution (default: 30).
        figsize: Figure size (default: (12, 4)).

    Returns:
        Matplotlib Figure object.

    Raises:
        ImportError: If matplotlib is not installed.
        ValueError: If ssp is not 2D.
        KeyError: If any object name is not in ssp.memory.

    Example:
        >>> import matplotlib.pyplot as plt
        >>> scene = create_spatial_scene(ssp, {
        ...     "apple": [1.0, 2.0],
        ...     "banana": [3.0, 4.0]
        ... })
        >>> fig = plot_ssp_2d_scene(ssp, scene, ["apple", "banana"])
        >>> plt.show()
    """
    try:
        import matplotlib.pyplot as plt  # type: ignore[import-not-found]
    except ImportError:
        raise ImportError(
            "matplotlib is required for plotting. Install with: pip install matplotlib"
        )

    if ssp.config.num_axes != 2:
        raise ValueError(
            f"plot_ssp_2d_scene only works with 2D SSP. Got num_axes={ssp.config.num_axes}"
        )

    n_objects = len(object_names)
    fig, axes = plt.subplots(1, n_objects, figsize=figsize)

    # Handle single object case
    if n_objects == 1:
        axes = [axes]

    for idx, obj_name in enumerate(object_names):
        # Query where this object is
        location_hv = ssp.query_object(scene, obj_name)

        # Generate similarity map
        X, Y, sims = similarity_map_2d(ssp, location_hv, x_range, y_range, resolution)

        # Plot heatmap
        ax = axes[idx]
        im = ax.contourf(X, Y, sims, levels=20, cmap="viridis")
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_title(f"Location of '{obj_name}'")
        ax.set_aspect("equal")
        plt.colorbar(im, ax=ax, label="Similarity")

    plt.tight_layout()
    return fig


def region_query(
    ssp: SpatialSemanticPointers,
    scene: ComplexHypervector,
    object_names: list[str],
    center: list[float],
    radius: float,
    resolution: int = 20,
) -> dict[str, float]:
    """Find which objects are within a spatial region.

    Searches a circular region (2D) or spherical region (3D) around a center point
    and returns objects with high similarity to locations in that region.

    Args:
        ssp: SpatialSemanticPointers instance.
        scene: Scene hypervector.
        object_names: List of candidate object names to check.
        center: Center coordinates of the search region.
        radius: Radius of the search region.
        resolution: Number of sample points to check in the region (default: 20).

    Returns:
        Dictionary mapping object names to maximum similarity scores.
        Higher scores indicate the object is likely in the region.

    Raises:
        ValueError: If center length doesn't match num_axes.
        KeyError: If any object name is not in ssp.memory.

    Example:
        >>> scene = create_spatial_scene(ssp, {
        ...     "apple": [1.0, 1.0],
        ...     "banana": [3.0, 3.0],
        ...     "cherry": [5.0, 5.0]
        ... })
        >>> # Search region around (3.0, 3.0) with radius 0.5
        >>> results = region_query(
        ...     ssp, scene, ["apple", "banana", "cherry"],
        ...     center=[3.0, 3.0], radius=0.5
        ... )
        >>> # results["banana"] should be highest
    """
    if len(center) != ssp.config.num_axes:
        raise ValueError(f"center must have {ssp.config.num_axes} coordinates, got {len(center)}")

    # Sample points in the region
    if ssp.config.num_axes == 2:
        # 2D: sample points in a circle
        angles = jnp.linspace(0, 2 * jnp.pi, resolution)
        radii = jnp.linspace(0, radius, max(resolution // 4, 1))

        sample_points = []
        for r in radii:
            for angle in angles:
                x = center[0] + r * jnp.cos(angle)
                y = center[1] + r * jnp.sin(angle)
                sample_points.append([x.item(), y.item()])
    elif ssp.config.num_axes == 3:
        # 3D: sample points in a sphere (simplified uniform sampling)
        phi = jnp.linspace(0, jnp.pi, resolution)
        theta = jnp.linspace(0, 2 * jnp.pi, resolution)
        radii = jnp.linspace(0, radius, max(resolution // 4, 1))

        sample_points = []
        for r in radii:
            for p in phi:
                for t in theta:
                    x = center[0] + r * jnp.sin(p) * jnp.cos(t)
                    y = center[1] + r * jnp.sin(p) * jnp.sin(t)
                    z = center[2] + r * jnp.cos(p)
                    sample_points.append([x.item(), y.item(), z.item()])
    else:
        # Higher dimensions: sample along axes and diagonals
        sample_points = []
        for _ in range(resolution * ssp.config.num_axes):
            offset = jnp.random.uniform(-radius, radius, ssp.config.num_axes)
            point = [center[i] + offset[i].item() for i in range(ssp.config.num_axes)]
            sample_points.append(point)

    # For each object, compute max similarity to sampled locations
    results = {}
    for obj_name in object_names:
        location_hv = ssp.query_object(scene, obj_name)
        max_sim = -jnp.inf

        for point in sample_points:
            point_hv = ssp.encode_location(point)
            sim = cosine_similarity(location_hv.vec, point_hv.vec)
            max_sim = max(max_sim, sim)

        results[obj_name] = float(max_sim)

    return results
