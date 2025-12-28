"""Operator kinds and metadata for semantic typing."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class OperatorKind(Enum):
    """Semantic types for operators.

    Operator kinds provide semantic metadata inspired by Clifford algebra grades.
    They help categorize operators by their intended use and transformation type.

    Attributes:
        RELATION: Semantic or abstract relations (e.g., graph edges, roles).
        TRANSFORM: Geometric transformations (e.g., rotations, reflections).
        LOGICAL: Logical operations and constraints.
        SPATIAL: Spatial relations (e.g., LEFT_OF, ABOVE, NEAR).
        TEMPORAL: Temporal relations and sequences.
        SEMANTIC: Semantic roles (e.g., AGENT, PATIENT, THEME).
        GENERAL: General-purpose operators without specific semantics.

    Example:
        >>> from vsax.operators import OperatorKind, CliffordOperator
        >>> import jax
        >>>
        >>> op = CliffordOperator.random(
        ...     dim=512,
        ...     kind=OperatorKind.SPATIAL,
        ...     name="LEFT_OF",
        ...     key=jax.random.PRNGKey(0)
        ... )
        >>> print(op.metadata.kind)
        OperatorKind.SPATIAL
    """

    RELATION = "relation"
    TRANSFORM = "transform"
    LOGICAL = "logical"
    SPATIAL = "spatial"
    TEMPORAL = "temporal"
    SEMANTIC = "semantic"
    GENERAL = "general"


@dataclass(frozen=True)
class OperatorMetadata:
    """Optional metadata for operators.

    Provides semantic information about an operator, including its kind,
    name, description, and properties. This metadata helps with debugging,
    visualization, and understanding operator compositions.

    Attributes:
        kind: Semantic type of the operator.
        name: Human-readable name for the operator.
        description: Optional detailed description of what the operator does.
        invertible: Whether the operator has an exact inverse (default: True).
        commutative: Whether the operator commutes with others (default: False).

    Example:
        >>> from vsax.operators import OperatorMetadata, OperatorKind
        >>>
        >>> metadata = OperatorMetadata(
        ...     kind=OperatorKind.SPATIAL,
        ...     name="LEFT_OF",
        ...     description="Spatial relation: object A is left of object B",
        ...     invertible=True,
        ...     commutative=False
        ... )
        >>> print(metadata.name)
        LEFT_OF
    """

    kind: OperatorKind
    name: str
    description: Optional[str] = None
    invertible: bool = True
    commutative: bool = False
