"""End-to-end integration tests for Iteration 3 (VSAMemory + Factory Functions)."""

import jax
import jax.numpy as jnp

from vsax import VSAMemory, create_binary_model, create_fhrr_model, create_map_model


class TestFHRRIntegration:
    """End-to-end FHRR workflow with factory and memory."""

    def test_complete_fhrr_workflow(self):
        """Test complete FHRR workflow from model creation to operations."""
        # Create model with factory
        model = create_fhrr_model(dim=512)

        # Create memory
        memory = VSAMemory(model, key=jax.random.PRNGKey(42))

        # Add symbols
        memory.add_many(["dog", "cat", "animal", "pet"])

        # Get hypervectors
        dog = memory["dog"]
        cat = memory["cat"]
        animal = memory["animal"]

        # Bind dog + animal
        dog_is_animal = model.opset.bind(dog.vec, animal.vec)
        dog_is_animal_hv = model.rep_cls(dog_is_animal).normalize()

        # Verify properties
        assert jnp.iscomplexobj(dog_is_animal_hv.vec)
        assert jnp.allclose(jnp.abs(dog_is_animal_hv.vec), 1.0)

        # Bundle dog + cat
        pets = model.opset.bundle(dog.vec, cat.vec)
        pets_hv = model.rep_cls(pets).normalize()

        assert jnp.iscomplexobj(pets_hv.vec)
        assert jnp.allclose(jnp.abs(pets_hv.vec), 1.0)

    def test_role_filler_binding(self):
        """Test role-filler binding pattern with FHRR."""
        model = create_fhrr_model(dim=512)
        memory = VSAMemory(model, key=jax.random.PRNGKey(42))

        # Roles and fillers
        memory.add_many(["subject", "predicate", "object"])
        memory.add_many(["dog", "chases", "cat"])

        # Create sentence: "dog chases cat"
        subject_dog = model.opset.bind(memory["subject"].vec, memory["dog"].vec)
        predicate_chases = model.opset.bind(memory["predicate"].vec, memory["chases"].vec)
        object_cat = model.opset.bind(memory["object"].vec, memory["cat"].vec)

        # Bundle into sentence
        sentence = model.opset.bundle(subject_dog, predicate_chases, object_cat)
        sentence_hv = model.rep_cls(sentence).normalize()

        # Verify it's a valid hypervector
        assert jnp.iscomplexobj(sentence_hv.vec)
        assert sentence_hv.shape == (512,)
        assert jnp.allclose(jnp.abs(sentence_hv.vec), 1.0)


class TestMAPIntegration:
    """End-to-end MAP workflow with factory and memory."""

    def test_complete_map_workflow(self):
        """Test complete MAP workflow from model creation to operations."""
        # Create model with factory
        model = create_map_model(dim=512)

        # Create memory
        memory = VSAMemory(model, key=jax.random.PRNGKey(42))

        # Add features
        memory.add_many(["color", "shape", "size"])
        memory.add_many(["red", "circle", "large"])

        # Bind features
        red_color = model.opset.bind(memory["color"].vec, memory["red"].vec)
        circle_shape = model.opset.bind(memory["shape"].vec, memory["circle"].vec)

        # Bundle into object representation
        obj = model.opset.bundle(red_color, circle_shape)
        obj_hv = model.rep_cls(obj).normalize()

        # Verify properties
        assert not jnp.iscomplexobj(obj_hv.vec)
        assert obj_hv.shape == (512,)

    def test_feature_bundling(self):
        """Test bundling multiple features with MAP."""
        model = create_map_model(dim=1024)
        memory = VSAMemory(model, key=jax.random.PRNGKey(42))

        # Add color features
        colors = memory.add_many(["red", "green", "blue"])

        # Bundle all colors
        color_bundle = model.opset.bundle(*[c.vec for c in colors])
        color_bundle_hv = model.rep_cls(color_bundle).normalize()

        # Should be real-valued
        assert not jnp.iscomplexobj(color_bundle_hv.vec)
        assert color_bundle_hv.shape == (1024,)


class TestBinaryIntegration:
    """End-to-end Binary workflow with factory and memory."""

    def test_complete_binary_workflow(self):
        """Test complete Binary workflow from model creation to operations."""
        # Create model with factory
        model = create_binary_model(dim=1000, bipolar=True)

        # Create memory
        memory = VSAMemory(model, key=jax.random.PRNGKey(42))

        # Add concepts
        memory.add_many(["concept_a", "concept_b", "concept_c"])

        # Get hypervectors
        a = memory["concept_a"]
        b = memory["concept_b"]

        # Bind (XOR)
        bound = model.opset.bind(a.vec, b.vec)
        bound_hv = model.rep_cls(bound, bipolar=True)

        # Verify bipolar
        assert jnp.all(jnp.isin(bound_hv.vec, jnp.array([-1, 1])))

        # Unbind (self-inverse property)
        unbound = model.opset.bind(bound_hv.vec, b.vec)
        unbound_hv = model.rep_cls(unbound, bipolar=True)

        # Should recover original
        assert jnp.array_equal(unbound_hv.vec, a.vec)

    def test_exact_unbinding(self):
        """Test exact unbinding property of Binary VSA."""
        model = create_binary_model(dim=2000, bipolar=True)
        memory = VSAMemory(model, key=jax.random.PRNGKey(42))

        # Add symbols
        a = memory.add("symbol_a")
        b = memory.add("symbol_b")

        # Bind
        c = model.opset.bind(a.vec, b.vec)

        # Unbind with b to recover a
        recovered_a = model.opset.bind(c, b.vec)

        # Should be exactly equal (self-inverse property)
        assert jnp.array_equal(recovered_a, a.vec)

        # Unbind with a to recover b
        recovered_b = model.opset.bind(c, a.vec)

        # Should be exactly equal
        assert jnp.array_equal(recovered_b, b.vec)


class TestCrossModelComparison:
    """Compare workflows across different models."""

    def test_same_workflow_all_models(self):
        """Test that same high-level workflow works for all models."""
        key = jax.random.PRNGKey(42)

        # Create all three models
        fhrr = create_fhrr_model(dim=512)
        map_model = create_map_model(dim=512)
        binary = create_binary_model(dim=1000, bipolar=True)

        # Same workflow for each
        for model in [fhrr, map_model, binary]:
            memory = VSAMemory(model, key=key)

            # Add symbols
            memory.add_many(["a", "b", "c"])

            # Verify all symbols present
            assert "a" in memory
            assert "b" in memory
            assert "c" in memory
            assert len(memory) == 3

            # Get hypervectors
            a = memory["a"]
            b = memory["b"]

            # Bind operation
            bound = model.opset.bind(a.vec, b.vec)
            assert bound.shape == a.vec.shape

            # Bundle operation
            bundled = model.opset.bundle(a.vec, b.vec)
            assert bundled.shape == a.vec.shape

    def test_memory_isolation(self):
        """Test that memories from different models don't interfere."""
        fhrr_memory = VSAMemory(create_fhrr_model(dim=512), key=jax.random.PRNGKey(42))
        map_memory = VSAMemory(create_map_model(dim=512), key=jax.random.PRNGKey(42))

        # Add same symbol to both
        fhrr_hv = fhrr_memory.add("symbol")
        map_hv = map_memory.add("symbol")

        # Should have different types
        assert jnp.iscomplexobj(fhrr_hv.vec)
        assert not jnp.iscomplexobj(map_hv.vec)

        # Memories are independent
        assert len(fhrr_memory) == 1
        assert len(map_memory) == 1
        fhrr_memory.clear()
        assert len(fhrr_memory) == 0
        assert len(map_memory) == 1  # Unchanged


class TestFactoryDefaults:
    """Test that factory defaults make sense for real use."""

    def test_fhrr_default_dimension_sufficient(self):
        """Test FHRR default dimension (512) is sufficient."""
        model = create_fhrr_model()  # Uses default dim=512
        memory = VSAMemory(model, key=jax.random.PRNGKey(42))

        # Can represent many concepts
        concepts = [f"concept_{i}" for i in range(100)]
        memory.add_many(concepts)

        assert len(memory) == 100

    def test_binary_default_dimension_appropriate(self):
        """Test Binary default dimension (10000) is appropriate."""
        model = create_binary_model()  # Uses default dim=10000
        memory = VSAMemory(model, key=jax.random.PRNGKey(42))

        # Binary typically needs higher dim
        assert model.dim == 10000

        # Can still create and use symbols
        a = memory.add("a")
        b = memory.add("b")

        bound = model.opset.bind(a.vec, b.vec)
        assert bound.shape == (10000,)
