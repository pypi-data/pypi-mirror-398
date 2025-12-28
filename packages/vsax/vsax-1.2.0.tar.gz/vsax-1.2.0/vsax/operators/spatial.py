"""Pre-defined spatial operators for VSAX.

This module provides factory functions for creating common spatial relation
operators like LEFT_OF, RIGHT_OF, ABOVE, BELOW, etc.

All operators are reproducible - the same dimension will always produce the
same operator parameters for a given spatial relation.
"""

import jax.random as random

from vsax.operators.clifford import CliffordOperator
from vsax.operators.kinds import OperatorKind

# Seed constants for reproducible spatial operators
# These ensure that LEFT_OF(512) always produces the same operator
_SPATIAL_SEEDS = {
    "LEFT_OF": 1000,
    "RIGHT_OF": 1001,
    "ABOVE": 1002,
    "BELOW": 1003,
    "IN_FRONT_OF": 1004,
    "BEHIND": 1005,
    "NEAR": 1006,
    "FAR": 1007,
}


def create_left_of(dim: int) -> CliffordOperator:
    """Create LEFT_OF spatial operator.

    Represents the spatial relation "to the left of" in a horizontal layout.

    Args:
        dim: Dimensionality of the operator (must match hypervector dimension).

    Returns:
        CliffordOperator representing LEFT_OF relation.

    Example:
        >>> from vsax import create_fhrr_model, VSAMemory
        >>> from vsax.operators.spatial import create_left_of
        >>> from vsax.similarity import cosine_similarity
        >>>
        >>> model = create_fhrr_model(dim=512)
        >>> memory = VSAMemory(model)
        >>> memory.add_many(["cup", "plate"])
        >>>
        >>> # Create operator
        >>> LEFT_OF = create_left_of(512)
        >>>
        >>> # Encode: cup LEFT_OF plate
        >>> scene = model.opset.bundle(
        ...     memory["cup"].vec,
        ...     LEFT_OF.apply(memory["plate"]).vec
        ... )
        >>>
        >>> # Query: what's LEFT_OF plate?
        >>> RIGHT_OF = LEFT_OF.inverse()
        >>> answer = RIGHT_OF.apply(model.rep_cls(scene))
        >>> similarity = cosine_similarity(answer.vec, memory["cup"].vec)
        >>> print(f"Similarity to 'cup': {similarity:.3f}")
    """
    key = random.PRNGKey(_SPATIAL_SEEDS["LEFT_OF"])
    return CliffordOperator.random(
        dim=dim,
        kind=OperatorKind.SPATIAL,
        name="LEFT_OF",
        key=key,
    )


def create_right_of(dim: int) -> CliffordOperator:
    """Create RIGHT_OF spatial operator.

    Represents the spatial relation "to the right of" in a horizontal layout.

    Note:
        This is the exact inverse of LEFT_OF. For efficiency, you can also
        create it as `LEFT_OF.inverse()`.

    Args:
        dim: Dimensionality of the operator (must match hypervector dimension).

    Returns:
        CliffordOperator representing RIGHT_OF relation.

    Example:
        >>> from vsax.operators.spatial import create_left_of, create_right_of
        >>>
        >>> LEFT_OF = create_left_of(512)
        >>> RIGHT_OF = create_right_of(512)
        >>>
        >>> # Verify they are inverses
        >>> composed = LEFT_OF.compose(RIGHT_OF)
        >>> # Composed operator should be close to identity
    """
    # RIGHT_OF is the inverse of LEFT_OF
    return create_left_of(dim).inverse()


def create_above(dim: int) -> CliffordOperator:
    """Create ABOVE spatial operator.

    Represents the spatial relation "above" in a vertical layout.

    Args:
        dim: Dimensionality of the operator (must match hypervector dimension).

    Returns:
        CliffordOperator representing ABOVE relation.

    Example:
        >>> from vsax.operators.spatial import create_above
        >>>
        >>> ABOVE = create_above(512)
        >>>
        >>> # Encode: plate ABOVE table
        >>> scene = model.opset.bundle(
        ...     memory["plate"].vec,
        ...     ABOVE.apply(memory["table"]).vec
        ... )
        >>>
        >>> # Query: what's ABOVE table?
        >>> BELOW = ABOVE.inverse()
        >>> answer = BELOW.apply(model.rep_cls(scene))
    """
    key = random.PRNGKey(_SPATIAL_SEEDS["ABOVE"])
    return CliffordOperator.random(
        dim=dim,
        kind=OperatorKind.SPATIAL,
        name="ABOVE",
        key=key,
    )


def create_below(dim: int) -> CliffordOperator:
    """Create BELOW spatial operator.

    Represents the spatial relation "below" in a vertical layout.

    Note:
        This is the exact inverse of ABOVE. For efficiency, you can also
        create it as `ABOVE.inverse()`.

    Args:
        dim: Dimensionality of the operator (must match hypervector dimension).

    Returns:
        CliffordOperator representing BELOW relation.

    Example:
        >>> from vsax.operators.spatial import create_above, create_below
        >>>
        >>> ABOVE = create_above(512)
        >>> BELOW = create_below(512)
        >>>
        >>> # They are exact inverses
        >>> cup = memory["cup"]
        >>> transformed = ABOVE.apply(cup)
        >>> recovered = BELOW.apply(transformed)
        >>> # recovered ≈ cup (similarity > 0.999)
    """
    # BELOW is the inverse of ABOVE
    return create_above(dim).inverse()


def create_in_front_of(dim: int) -> CliffordOperator:
    """Create IN_FRONT_OF spatial operator.

    Represents the spatial relation "in front of" in a depth layout.

    Args:
        dim: Dimensionality of the operator (must match hypervector dimension).

    Returns:
        CliffordOperator representing IN_FRONT_OF relation.

    Example:
        >>> from vsax.operators.spatial import create_in_front_of
        >>>
        >>> IN_FRONT_OF = create_in_front_of(512)
        >>>
        >>> # Encode: car IN_FRONT_OF house
        >>> scene = model.opset.bundle(
        ...     memory["car"].vec,
        ...     IN_FRONT_OF.apply(memory["house"]).vec
        ... )
    """
    key = random.PRNGKey(_SPATIAL_SEEDS["IN_FRONT_OF"])
    return CliffordOperator.random(
        dim=dim,
        kind=OperatorKind.SPATIAL,
        name="IN_FRONT_OF",
        key=key,
    )


def create_behind(dim: int) -> CliffordOperator:
    """Create BEHIND spatial operator.

    Represents the spatial relation "behind" in a depth layout.

    Note:
        This is the exact inverse of IN_FRONT_OF. For efficiency, you can also
        create it as `IN_FRONT_OF.inverse()`.

    Args:
        dim: Dimensionality of the operator (must match hypervector dimension).

    Returns:
        CliffordOperator representing BEHIND relation.

    Example:
        >>> from vsax.operators.spatial import create_in_front_of, create_behind
        >>>
        >>> IN_FRONT_OF = create_in_front_of(512)
        >>> BEHIND = create_behind(512)
        >>>
        >>> # They are exact inverses
        >>> # IN_FRONT_OF.inverse() == BEHIND
    """
    # BEHIND is the inverse of IN_FRONT_OF
    return create_in_front_of(dim).inverse()


def create_near(dim: int) -> CliffordOperator:
    """Create NEAR spatial operator.

    Represents the spatial relation "near to" (proximity).

    Args:
        dim: Dimensionality of the operator (must match hypervector dimension).

    Returns:
        CliffordOperator representing NEAR relation.

    Example:
        >>> from vsax.operators.spatial import create_near
        >>>
        >>> NEAR = create_near(512)
        >>>
        >>> # Encode: store NEAR home
        >>> scene = model.opset.bundle(
        ...     memory["store"].vec,
        ...     NEAR.apply(memory["home"]).vec
        ... )
    """
    key = random.PRNGKey(_SPATIAL_SEEDS["NEAR"])
    return CliffordOperator.random(
        dim=dim,
        kind=OperatorKind.SPATIAL,
        name="NEAR",
        key=key,
    )


def create_far(dim: int) -> CliffordOperator:
    """Create FAR spatial operator.

    Represents the spatial relation "far from" (distance).

    Note:
        This is the exact inverse of NEAR. For efficiency, you can also
        create it as `NEAR.inverse()`.

    Args:
        dim: Dimensionality of the operator (must match hypervector dimension).

    Returns:
        CliffordOperator representing FAR relation.

    Example:
        >>> from vsax.operators.spatial import create_near, create_far
        >>>
        >>> NEAR = create_near(512)
        >>> FAR = create_far(512)
        >>>
        >>> # They are exact inverses
        >>> # NEAR.inverse() == FAR
    """
    # FAR is the inverse of NEAR
    return create_near(dim).inverse()


def create_spatial_operators(dim: int) -> dict[str, CliffordOperator]:
    """Create all spatial operators at once.

    Convenience function to create all 8 spatial operators with a single call.

    Args:
        dim: Dimensionality of the operators (must match hypervector dimension).

    Returns:
        Dictionary mapping operator names to CliffordOperator instances.
        Keys: "LEFT_OF", "RIGHT_OF", "ABOVE", "BELOW", "IN_FRONT_OF",
              "BEHIND", "NEAR", "FAR"

    Example:
        >>> from vsax.operators.spatial import create_spatial_operators
        >>>
        >>> # Create all spatial operators
        >>> spatial = create_spatial_operators(512)
        >>>
        >>> # Access operators by name
        >>> LEFT_OF = spatial["LEFT_OF"]
        >>> ABOVE = spatial["ABOVE"]
        >>>
        >>> # Encode complex spatial scene
        >>> scene = model.opset.bundle(
        ...     memory["cup"].vec,
        ...     spatial["LEFT_OF"].apply(memory["plate"]).vec,
        ...     spatial["ABOVE"].apply(memory["table"]).vec
        ... )
    """
    return {
        "LEFT_OF": create_left_of(dim),
        "RIGHT_OF": create_right_of(dim),
        "ABOVE": create_above(dim),
        "BELOW": create_below(dim),
        "IN_FRONT_OF": create_in_front_of(dim),
        "BEHIND": create_behind(dim),
        "NEAR": create_near(dim),
        "FAR": create_far(dim),
    }
