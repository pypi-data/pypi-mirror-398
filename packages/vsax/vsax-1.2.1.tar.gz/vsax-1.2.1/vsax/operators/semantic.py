"""Pre-defined semantic role operators for VSAX.

This module provides factory functions for creating common semantic role
operators like AGENT, PATIENT, THEME, INSTRUMENT, etc.

These operators enable semantic role labeling - encoding "who did what to whom"
in a sentence or event representation.

All operators are reproducible - the same dimension will always produce the
same operator parameters for a given semantic role.
"""

import jax.random as random

from vsax.operators.clifford import CliffordOperator
from vsax.operators.kinds import OperatorKind

# Seed constants for reproducible semantic operators
# These ensure that AGENT(512) always produces the same operator
_SEMANTIC_SEEDS = {
    "AGENT": 2000,
    "PATIENT": 2001,
    "THEME": 2002,
    "EXPERIENCER": 2003,
    "INSTRUMENT": 2004,
    "LOCATION": 2005,
    "GOAL": 2006,
    "SOURCE": 2007,
}


def create_agent(dim: int) -> CliffordOperator:
    """Create AGENT semantic role operator.

    Represents the semantic role of "agent" - the entity that performs an action.

    In a sentence like "dog chases cat", "dog" is the AGENT.

    Args:
        dim: Dimensionality of the operator (must match hypervector dimension).

    Returns:
        CliffordOperator representing AGENT role.

    Example:
        >>> from vsax import create_fhrr_model, VSAMemory
        >>> from vsax.operators.semantic import create_agent, create_patient
        >>> from vsax.similarity import cosine_similarity
        >>>
        >>> model = create_fhrr_model(dim=512)
        >>> memory = VSAMemory(model)
        >>> memory.add_many(["dog", "cat", "chase"])
        >>>
        >>> # Create operators
        >>> AGENT = create_agent(512)
        >>> PATIENT = create_patient(512)
        >>>
        >>> # Encode: "dog chases cat"
        >>> sentence = model.opset.bundle(
        ...     AGENT.apply(memory["dog"]).vec,
        ...     memory["chase"].vec,
        ...     PATIENT.apply(memory["cat"]).vec
        ... )
        >>>
        >>> # Query: Who is the AGENT?
        >>> who = AGENT.inverse().apply(model.rep_cls(sentence))
        >>> similarity = cosine_similarity(who.vec, memory["dog"].vec)
        >>> print(f"AGENT is 'dog': {similarity:.3f}")
    """
    key = random.PRNGKey(_SEMANTIC_SEEDS["AGENT"])
    return CliffordOperator.random(
        dim=dim,
        kind=OperatorKind.SEMANTIC,
        name="AGENT",
        key=key,
    )


def create_patient(dim: int) -> CliffordOperator:
    """Create PATIENT semantic role operator.

    Represents the semantic role of "patient" - the entity that undergoes
    or is affected by an action.

    In a sentence like "dog chases cat", "cat" is the PATIENT.

    Args:
        dim: Dimensionality of the operator (must match hypervector dimension).

    Returns:
        CliffordOperator representing PATIENT role.

    Example:
        >>> from vsax.operators.semantic import create_patient
        >>>
        >>> PATIENT = create_patient(512)
        >>>
        >>> # Encode: "dog chases cat"
        >>> sentence = model.opset.bundle(
        ...     memory["dog"].vec,
        ...     memory["chase"].vec,
        ...     PATIENT.apply(memory["cat"]).vec
        ... )
        >>>
        >>> # Query: Who is the PATIENT?
        >>> who = PATIENT.inverse().apply(model.rep_cls(sentence))
    """
    key = random.PRNGKey(_SEMANTIC_SEEDS["PATIENT"])
    return CliffordOperator.random(
        dim=dim,
        kind=OperatorKind.SEMANTIC,
        name="PATIENT",
        key=key,
    )


def create_theme(dim: int) -> CliffordOperator:
    """Create THEME semantic role operator.

    Represents the semantic role of "theme" - the entity that is moved,
    experienced, or perceived.

    In a sentence like "John gave the book to Mary", "the book" is the THEME.

    Args:
        dim: Dimensionality of the operator (must match hypervector dimension).

    Returns:
        CliffordOperator representing THEME role.

    Example:
        >>> from vsax.operators.semantic import create_agent, create_theme, create_goal
        >>>
        >>> AGENT = create_agent(512)
        >>> THEME = create_theme(512)
        >>> GOAL = create_goal(512)
        >>>
        >>> memory.add_many(["John", "book", "Mary", "give"])
        >>>
        >>> # Encode: "John gave the book to Mary"
        >>> sentence = model.opset.bundle(
        ...     AGENT.apply(memory["John"]).vec,
        ...     memory["give"].vec,
        ...     THEME.apply(memory["book"]).vec,
        ...     GOAL.apply(memory["Mary"]).vec
        ... )
        >>>
        >>> # Query: What was given? (THEME)
        >>> what = THEME.inverse().apply(model.rep_cls(sentence))
    """
    key = random.PRNGKey(_SEMANTIC_SEEDS["THEME"])
    return CliffordOperator.random(
        dim=dim,
        kind=OperatorKind.SEMANTIC,
        name="THEME",
        key=key,
    )


def create_experiencer(dim: int) -> CliffordOperator:
    """Create EXPERIENCER semantic role operator.

    Represents the semantic role of "experiencer" - the entity that experiences
    a mental or emotional state.

    In a sentence like "Mary loves music", "Mary" is the EXPERIENCER.

    Args:
        dim: Dimensionality of the operator (must match hypervector dimension).

    Returns:
        CliffordOperator representing EXPERIENCER role.

    Example:
        >>> from vsax.operators.semantic import create_experiencer, create_theme
        >>>
        >>> EXPERIENCER = create_experiencer(512)
        >>> THEME = create_theme(512)
        >>>
        >>> memory.add_many(["Mary", "music", "love"])
        >>>
        >>> # Encode: "Mary loves music"
        >>> sentence = model.opset.bundle(
        ...     EXPERIENCER.apply(memory["Mary"]).vec,
        ...     memory["love"].vec,
        ...     THEME.apply(memory["music"]).vec
        ... )
        >>>
        >>> # Query: Who experiences the feeling?
        >>> who = EXPERIENCER.inverse().apply(model.rep_cls(sentence))
    """
    key = random.PRNGKey(_SEMANTIC_SEEDS["EXPERIENCER"])
    return CliffordOperator.random(
        dim=dim,
        kind=OperatorKind.SEMANTIC,
        name="EXPERIENCER",
        key=key,
    )


def create_instrument(dim: int) -> CliffordOperator:
    """Create INSTRUMENT semantic role operator.

    Represents the semantic role of "instrument" - the tool or means by which
    an action is performed.

    In a sentence like "John cut the bread with a knife", "knife" is the INSTRUMENT.

    Args:
        dim: Dimensionality of the operator (must match hypervector dimension).

    Returns:
        CliffordOperator representing INSTRUMENT role.

    Example:
        >>> from vsax.operators.semantic import create_agent, create_patient, create_instrument
        >>>
        >>> AGENT = create_agent(512)
        >>> PATIENT = create_patient(512)
        >>> INSTRUMENT = create_instrument(512)
        >>>
        >>> memory.add_many(["John", "bread", "knife", "cut"])
        >>>
        >>> # Encode: "John cut the bread with a knife"
        >>> sentence = model.opset.bundle(
        ...     AGENT.apply(memory["John"]).vec,
        ...     memory["cut"].vec,
        ...     PATIENT.apply(memory["bread"]).vec,
        ...     INSTRUMENT.apply(memory["knife"]).vec
        ... )
        >>>
        >>> # Query: What was used as instrument?
        >>> what = INSTRUMENT.inverse().apply(model.rep_cls(sentence))
    """
    key = random.PRNGKey(_SEMANTIC_SEEDS["INSTRUMENT"])
    return CliffordOperator.random(
        dim=dim,
        kind=OperatorKind.SEMANTIC,
        name="INSTRUMENT",
        key=key,
    )


def create_location(dim: int) -> CliffordOperator:
    """Create LOCATION semantic role operator.

    Represents the semantic role of "location" - the place where an action
    or state occurs.

    In a sentence like "John ate in the restaurant", "restaurant" is the LOCATION.

    Args:
        dim: Dimensionality of the operator (must match hypervector dimension).

    Returns:
        CliffordOperator representing LOCATION role.

    Example:
        >>> from vsax.operators.semantic import create_agent, create_location
        >>>
        >>> AGENT = create_agent(512)
        >>> LOCATION = create_location(512)
        >>>
        >>> memory.add_many(["John", "restaurant", "eat"])
        >>>
        >>> # Encode: "John ate in the restaurant"
        >>> sentence = model.opset.bundle(
        ...     AGENT.apply(memory["John"]).vec,
        ...     memory["eat"].vec,
        ...     LOCATION.apply(memory["restaurant"]).vec
        ... )
        >>>
        >>> # Query: Where did the action occur?
        >>> where = LOCATION.inverse().apply(model.rep_cls(sentence))
    """
    key = random.PRNGKey(_SEMANTIC_SEEDS["LOCATION"])
    return CliffordOperator.random(
        dim=dim,
        kind=OperatorKind.SEMANTIC,
        name="LOCATION",
        key=key,
    )


def create_goal(dim: int) -> CliffordOperator:
    """Create GOAL semantic role operator.

    Represents the semantic role of "goal" - the endpoint or recipient of
    a motion or transfer.

    In a sentence like "John went to Paris", "Paris" is the GOAL.

    Args:
        dim: Dimensionality of the operator (must match hypervector dimension).

    Returns:
        CliffordOperator representing GOAL role.

    Example:
        >>> from vsax.operators.semantic import create_agent, create_goal
        >>>
        >>> AGENT = create_agent(512)
        >>> GOAL = create_goal(512)
        >>>
        >>> memory.add_many(["John", "Paris", "go"])
        >>>
        >>> # Encode: "John went to Paris"
        >>> sentence = model.opset.bundle(
        ...     AGENT.apply(memory["John"]).vec,
        ...     memory["go"].vec,
        ...     GOAL.apply(memory["Paris"]).vec
        ... )
        >>>
        >>> # Query: Where did John go? (destination)
        >>> where = GOAL.inverse().apply(model.rep_cls(sentence))
    """
    key = random.PRNGKey(_SEMANTIC_SEEDS["GOAL"])
    return CliffordOperator.random(
        dim=dim,
        kind=OperatorKind.SEMANTIC,
        name="GOAL",
        key=key,
    )


def create_source(dim: int) -> CliffordOperator:
    """Create SOURCE semantic role operator.

    Represents the semantic role of "source" - the starting point of a motion
    or transfer.

    In a sentence like "John came from Boston", "Boston" is the SOURCE.

    Args:
        dim: Dimensionality of the operator (must match hypervector dimension).

    Returns:
        CliffordOperator representing SOURCE role.

    Example:
        >>> from vsax.operators.semantic import create_agent, create_source, create_goal
        >>>
        >>> AGENT = create_agent(512)
        >>> SOURCE = create_source(512)
        >>> GOAL = create_goal(512)
        >>>
        >>> memory.add_many(["John", "Boston", "Paris", "travel"])
        >>>
        >>> # Encode: "John traveled from Boston to Paris"
        >>> sentence = model.opset.bundle(
        ...     AGENT.apply(memory["John"]).vec,
        ...     memory["travel"].vec,
        ...     SOURCE.apply(memory["Boston"]).vec,
        ...     GOAL.apply(memory["Paris"]).vec
        ... )
        >>>
        >>> # Query: Where did John come from?
        >>> where = SOURCE.inverse().apply(model.rep_cls(sentence))
    """
    key = random.PRNGKey(_SEMANTIC_SEEDS["SOURCE"])
    return CliffordOperator.random(
        dim=dim,
        kind=OperatorKind.SEMANTIC,
        name="SOURCE",
        key=key,
    )


def create_semantic_operators(dim: int) -> dict[str, CliffordOperator]:
    """Create all semantic role operators at once.

    Convenience function to create all 8 semantic operators with a single call.

    Args:
        dim: Dimensionality of the operators (must match hypervector dimension).

    Returns:
        Dictionary mapping operator names to CliffordOperator instances.
        Keys: "AGENT", "PATIENT", "THEME", "EXPERIENCER", "INSTRUMENT",
              "LOCATION", "GOAL", "SOURCE"

    Example:
        >>> from vsax.operators.semantic import create_semantic_operators
        >>>
        >>> # Create all semantic operators
        >>> semantic = create_semantic_operators(512)
        >>>
        >>> # Access operators by name
        >>> AGENT = semantic["AGENT"]
        >>> PATIENT = semantic["PATIENT"]
        >>>
        >>> # Encode complex event with multiple roles
        >>> event = model.opset.bundle(
        ...     semantic["AGENT"].apply(memory["John"]).vec,
        ...     memory["cut"].vec,
        ...     semantic["PATIENT"].apply(memory["bread"]).vec,
        ...     semantic["INSTRUMENT"].apply(memory["knife"]).vec,
        ...     semantic["LOCATION"].apply(memory["kitchen"]).vec
        ... )
    """
    return {
        "AGENT": create_agent(dim),
        "PATIENT": create_patient(dim),
        "THEME": create_theme(dim),
        "EXPERIENCER": create_experiencer(dim),
        "INSTRUMENT": create_instrument(dim),
        "LOCATION": create_location(dim),
        "GOAL": create_goal(dim),
        "SOURCE": create_source(dim),
    }
