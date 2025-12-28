"""GraphEncoder for encoding graph structures into hypervectors."""

from vsax.core.base import AbstractHypervector
from vsax.encoders.base import AbstractEncoder


class GraphEncoder(AbstractEncoder):
    """Encoder for graph structures using edge binding.

    Encodes graphs by representing each edge as a binding of source, relation,
    and target, then bundling all edges together.

    Graphs are represented as edge lists: [(source, relation, target), ...]

    All node and relation names must be symbols that exist in memory.

    Attributes:
        model: The VSAModel instance defining the VSA algebra.
        memory: The VSAMemory instance for accessing basis hypervectors.

    Example:
        >>> from vsax import create_fhrr_model, VSAMemory
        >>> from vsax.encoders import GraphEncoder
        >>> model = create_fhrr_model(dim=512)
        >>> memory = VSAMemory(model)
        >>> memory.add_many(["Alice", "Bob", "knows", "likes"])
        >>> encoder = GraphEncoder(model, memory)
        >>> # Alice knows Bob, Alice likes Bob
        >>> graph_hv = encoder.encode([
        ...     ("Alice", "knows", "Bob"),
        ...     ("Alice", "likes", "Bob")
        ... ])
    """

    def encode(self, edges: list[tuple[str, str, str]]) -> AbstractHypervector:
        """Encode a graph as a list of edges.

        Args:
            edges: List of (source, relation, target) tuples.
                   All names must be symbols in memory.

        Returns:
            The encoded hypervector representing the graph.

        Raises:
            KeyError: If any node or relation is not in memory.
            ValueError: If the edge list is empty.

        Example:
            >>> encoder = GraphEncoder(model, memory)
            >>> graph_hv = encoder.encode([
            ...     ("Alice", "knows", "Bob"),
            ...     ("Bob", "likes", "Alice")
            ... ])
        """
        if len(edges) == 0:
            raise ValueError("Cannot encode empty graph (no edges)")

        # Encode each edge and collect results
        edge_encodings = []
        for source, relation, target in edges:
            source_hv = self.memory[source]
            relation_hv = self.memory[relation]
            target_hv = self.memory[target]

            # Encode edge as bind(source, bind(relation, target))
            rel_target = self.model.opset.bind(relation_hv.vec, target_hv.vec)
            edge_encoding = self.model.opset.bind(source_hv.vec, rel_target)
            edge_encodings.append(edge_encoding)

        # Bundle all edges together
        result = self.model.opset.bundle(*edge_encodings)

        return self.model.rep_cls(result)
