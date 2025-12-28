"""Spatial Semantic Pointers for continuous spatial representation.

Based on:
    Komer et al. 2019: "A neural representation of continuous space using
    fractional binding"
"""

from dataclasses import dataclass
from typing import Optional

import jax.numpy as jnp

from vsax.core.memory import VSAMemory
from vsax.core.model import VSAModel
from vsax.encoders import FractionalPowerEncoder
from vsax.representations import ComplexHypervector
from vsax.similarity import cosine_similarity


@dataclass
class SSPConfig:
    """Configuration for Spatial Semantic Pointers.

    Attributes:
        dim: Dimensionality of hypervectors (e.g., 512, 1024).
        num_axes: Number of spatial dimensions (1D, 2D, 3D, etc.).
        scale: Optional scaling factor for spatial coordinates.
        axis_names: Optional custom names for axes (defaults to ["x", "y", "z", ...]).
    """

    dim: int = 512
    num_axes: int = 2
    scale: Optional[float] = None
    axis_names: Optional[list[str]] = None

    def __post_init__(self) -> None:
        """Set default axis names if not provided."""
        if self.axis_names is None:
            # Default axis names: x, y, z, w, v, u, ...
            default_names = ["x", "y", "z", "w", "v", "u"]
            if self.num_axes <= len(default_names):
                self.axis_names = default_names[: self.num_axes]
            else:
                # For higher dimensions, use axis_0, axis_1, ...
                self.axis_names = [f"axis_{i}" for i in range(self.num_axes)]
        elif len(self.axis_names) != self.num_axes:
            raise ValueError(
                f"axis_names length ({len(self.axis_names)}) must match num_axes ({self.num_axes})"
            )


class SpatialSemanticPointers:
    """Spatial Semantic Pointers for continuous spatial representation.

    Encodes continuous spatial locations using fractional power encoding:
        S(x, y) = X^x ⊗ Y^y

    This enables:
        - Encoding arbitrary spatial coordinates
        - Binding objects to locations
        - Querying "what is at location (x, y)?"
        - Querying "where is object O?"
        - Shifting entire scenes by a displacement vector
        - Decoding approximate locations from encoded vectors

    Based on Komer et al. 2019 which demonstrates that SSPs can represent
    continuous spatial relationships in a compositional, distributed manner.

    Attributes:
        model: VSAModel instance (must use ComplexHypervector/FHRR).
        memory: VSAMemory for storing axis basis vectors and named objects.
        config: SSPConfig with spatial configuration.
        encoder: FractionalPowerEncoder for encoding spatial coordinates.

    Example:
        >>> import jax
        >>> from vsax import create_fhrr_model, VSAMemory
        >>> from vsax.spatial import SpatialSemanticPointers, SSPConfig
        >>>
        >>> # Create 2D spatial representation
        >>> model = create_fhrr_model(dim=512, key=jax.random.PRNGKey(0))
        >>> memory = VSAMemory(model)
        >>> config = SSPConfig(dim=512, num_axes=2)  # 2D space
        >>> ssp = SpatialSemanticPointers(model, memory, config)
        >>>
        >>> # Encode a location
        >>> location = ssp.encode_location([3.5, 2.1])  # (x=3.5, y=2.1)
        >>>
        >>> # Bind object to location
        >>> memory.add("apple")
        >>> scene = ssp.bind_object_location("apple", [3.5, 2.1])
        >>>
        >>> # Query: what is at location (3.5, 2.1)?
        >>> result = ssp.query_location(scene, [3.5, 2.1])
        >>> # result should be similar to apple hypervector

    See Also:
        - :class:`~vsax.encoders.FractionalPowerEncoder`: Underlying encoder
        - Komer et al. 2019: "A neural representation of continuous space using
          fractional binding"
    """

    def __init__(
        self,
        model: VSAModel,
        memory: VSAMemory,
        config: Optional[SSPConfig] = None,
    ) -> None:
        """Initialize Spatial Semantic Pointers.

        Args:
            model: VSAModel instance (must use ComplexHypervector).
            memory: VSAMemory for basis vectors and objects.
            config: SSPConfig, defaults to 2D (512-dim) if not provided.

        Raises:
            TypeError: If model doesn't use ComplexHypervector.
        """
        self.model = model
        self.memory = memory
        self.config = config if config is not None else SSPConfig()

        # axis_names is always set by SSPConfig.__post_init__
        assert self.config.axis_names is not None

        # Create FractionalPowerEncoder
        self.encoder = FractionalPowerEncoder(model, memory, scale=self.config.scale)

        # Initialize axis basis vectors in memory
        for axis_name in self.config.axis_names:
            if axis_name not in memory:
                memory.add(axis_name)

    def encode_location(self, coordinates: list[float]) -> ComplexHypervector:
        """Encode a spatial location as a hypervector.

        For 2D: S(x, y) = X^x ⊗ Y^y
        For 3D: S(x, y, z) = X^x ⊗ Y^y ⊗ Z^z

        Args:
            coordinates: List of coordinate values, one per axis.

        Returns:
            ComplexHypervector representing the spatial location.

        Raises:
            ValueError: If coordinates length doesn't match num_axes.

        Example:
            >>> location = ssp.encode_location([3.5, 2.1])  # 2D point
            >>> location3d = ssp.encode_location([1.0, 2.0, 3.0])  # 3D point
        """
        if len(coordinates) != self.config.num_axes:
            raise ValueError(f"Expected {self.config.num_axes} coordinates, got {len(coordinates)}")

        assert self.config.axis_names is not None  # Always set in __init__
        return self.encoder.encode_multi(self.config.axis_names, coordinates)

    def bind_object_location(
        self, object_name: str, coordinates: list[float]
    ) -> ComplexHypervector:
        """Bind an object to a spatial location.

        Creates: Object ⊗ S(x, y) = Object ⊗ X^x ⊗ Y^y

        Args:
            object_name: Name of object in memory.
            coordinates: Spatial coordinates for the object.

        Returns:
            ComplexHypervector representing object-at-location.

        Raises:
            KeyError: If object_name not in memory.
            ValueError: If coordinates length doesn't match num_axes.

        Example:
            >>> memory.add("apple")
            >>> apple_at_pos = ssp.bind_object_location("apple", [3.5, 2.1])
        """
        # Get object hypervector
        object_hv = self.memory[object_name]

        # Encode location
        location_hv = self.encode_location(coordinates)

        # Bind object to location
        result_vec = self.model.opset.bind(object_hv.vec, location_hv.vec)

        return ComplexHypervector(result_vec)

    def query_location(
        self, scene: ComplexHypervector, coordinates: list[float]
    ) -> ComplexHypervector:
        """Query what object is at a given location in the scene.

        For scene containing Object ⊗ S(x, y), querying at (x, y) returns
        a vector similar to Object.

        Args:
            scene: Scene hypervector (typically a bundle of object-location pairs).
            coordinates: Location to query.

        Returns:
            ComplexHypervector representing the object at that location.

        Raises:
            ValueError: If coordinates length doesn't match num_axes.

        Example:
            >>> # Create scene with apple at (3.5, 2.1)
            >>> scene = ssp.bind_object_location("apple", [3.5, 2.1])
            >>> # Query: what's at (3.5, 2.1)?
            >>> result = ssp.query_location(scene, [3.5, 2.1])
            >>> # result should be similar to memory["apple"]
        """
        # Encode query location
        location_hv = self.encode_location(coordinates)

        # Unbind: Scene ⊗ S(x,y)^(-1) ≈ Object
        inv_location = self.model.opset.inverse(location_hv.vec)
        result_vec = self.model.opset.bind(scene.vec, inv_location)

        return ComplexHypervector(result_vec)

    def query_object(self, scene: ComplexHypervector, object_name: str) -> ComplexHypervector:
        """Query where an object is located in the scene.

        For scene containing Object ⊗ S(x, y), querying for Object returns
        a vector similar to S(x, y).

        Args:
            scene: Scene hypervector.
            object_name: Name of object to locate.

        Returns:
            ComplexHypervector representing the location of the object.

        Raises:
            KeyError: If object_name not in memory.

        Example:
            >>> scene = ssp.bind_object_location("apple", [3.5, 2.1])
            >>> # Query: where is the apple?
            >>> location_hv = ssp.query_object(scene, "apple")
            >>> # location_hv should be similar to ssp.encode_location([3.5, 2.1])
        """
        # Get object hypervector
        object_hv = self.memory[object_name]

        # Unbind: Scene ⊗ Object^(-1) ≈ S(x,y)
        inv_object = self.model.opset.inverse(object_hv.vec)
        result_vec = self.model.opset.bind(scene.vec, inv_object)

        return ComplexHypervector(result_vec)

    def shift_scene(self, scene: ComplexHypervector, offset: list[float]) -> ComplexHypervector:
        """Shift all objects in a scene by a displacement vector.

        For scene S containing objects at various locations, shift by (dx, dy)
        moves all objects by that offset.

        This works because: (Object ⊗ X^x ⊗ Y^y) ⊗ (X^dx ⊗ Y^dy) =
                             Object ⊗ X^(x+dx) ⊗ Y^(y+dy)

        Args:
            scene: Scene hypervector to shift.
            offset: Displacement vector, one value per axis.

        Returns:
            Shifted scene hypervector.

        Raises:
            ValueError: If offset length doesn't match num_axes.

        Example:
            >>> # Apple at (3.5, 2.1)
            >>> scene = ssp.bind_object_location("apple", [3.5, 2.1])
            >>> # Shift scene by (1.0, -0.5)
            >>> shifted = ssp.shift_scene(scene, [1.0, -0.5])
            >>> # Now apple is at (4.5, 1.6)
        """
        if len(offset) != self.config.num_axes:
            raise ValueError(f"Expected {self.config.num_axes} offset values, got {len(offset)}")

        # Encode displacement as a location
        displacement_hv = self.encode_location(offset)

        # Bind displacement to scene
        result_vec = self.model.opset.bind(scene.vec, displacement_hv.vec)

        return ComplexHypervector(result_vec)

    def decode_location(
        self,
        location_hv: ComplexHypervector,
        search_range: list[tuple[float, float]],
        resolution: int = 20,
    ) -> list[float]:
        """Decode approximate coordinates from a location hypervector.

        Uses grid search to find coordinates that best match the encoded location.

        Args:
            location_hv: Encoded location hypervector to decode.
            search_range: List of (min, max) tuples, one per axis.
            resolution: Number of grid points to sample per axis (default: 20).

        Returns:
            List of decoded coordinates (approximate).

        Raises:
            ValueError: If search_range length doesn't match num_axes.

        Example:
            >>> location_hv = ssp.encode_location([3.5, 2.1])
            >>> decoded = ssp.decode_location(
            ...     location_hv,
            ...     search_range=[(0.0, 5.0), (0.0, 5.0)],
            ...     resolution=50
            ... )
            >>> # decoded should be close to [3.5, 2.1]
        """
        if len(search_range) != self.config.num_axes:
            raise ValueError(
                f"Expected {self.config.num_axes} search ranges, got {len(search_range)}"
            )

        # Create grid of candidate coordinates
        grids = [jnp.linspace(min_val, max_val, resolution) for min_val, max_val in search_range]

        # Generate all combinations using meshgrid
        mesh = jnp.meshgrid(*grids, indexing="ij")
        # Flatten and stack to get all candidate points
        candidates = jnp.stack([g.flatten() for g in mesh], axis=1)

        # Encode all candidate locations and compute similarities
        best_similarity = -jnp.inf
        best_coords = None

        for candidate in candidates:
            candidate_hv = self.encode_location(candidate.tolist())
            similarity = cosine_similarity(location_hv.vec, candidate_hv.vec)

            if similarity > best_similarity:
                best_similarity = similarity
                best_coords = candidate

        assert best_coords is not None  # At least one candidate should exist
        result: list[float] = best_coords.tolist()
        return result
