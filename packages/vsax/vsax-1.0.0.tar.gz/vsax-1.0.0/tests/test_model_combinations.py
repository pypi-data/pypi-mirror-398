"""Integration tests for all VSA model combinations."""

import jax
import jax.numpy as jnp
import pytest

from vsax.core.model import VSAModel
from vsax.ops import BinaryOperations, FHRROperations, MAPOperations
from vsax.representations import BinaryHypervector, ComplexHypervector, RealHypervector
from vsax.sampling import sample_binary_random, sample_complex_random, sample_random


class TestFHRRModel:
    """Integration tests for FHRR model (ComplexHypervector + FHRROperations)."""

    @pytest.fixture
    def fhrr_model(self):
        """Create FHRR VSAModel."""
        return VSAModel(
            dim=512,
            rep_cls=ComplexHypervector,
            opset=FHRROperations(),
            sampler=sample_complex_random,
        )

    def test_fhrr_model_creation(self, fhrr_model):
        """Test FHRR model can be created."""
        assert fhrr_model.dim == 512
        assert fhrr_model.rep_cls == ComplexHypervector
        assert isinstance(fhrr_model.opset, FHRROperations)

    def test_fhrr_sampling_and_wrapping(self, fhrr_model):
        """Test sampling and wrapping with FHRR model."""
        key = jax.random.PRNGKey(42)
        vectors = fhrr_model.sampler(dim=fhrr_model.dim, n=5, key=key)

        # Wrap in representation
        hvs = [fhrr_model.rep_cls(vec) for vec in vectors]

        for hv in hvs:
            assert isinstance(hv, ComplexHypervector)
            assert hv.shape == (fhrr_model.dim,)
            assert jnp.iscomplexobj(hv.vec)

    def test_fhrr_bind_and_unbind(self, fhrr_model):
        """Test bind and unbind workflow with FHRR model."""
        key = jax.random.PRNGKey(42)
        vectors = fhrr_model.sampler(dim=fhrr_model.dim, n=2, key=key)

        a = fhrr_model.rep_cls(vectors[0]).normalize()
        b = fhrr_model.rep_cls(vectors[1]).normalize()

        # Bind
        bound = fhrr_model.opset.bind(a.vec, b.vec)
        bound_hv = fhrr_model.rep_cls(bound).normalize()

        # Unbind
        inv_b = fhrr_model.opset.inverse(b.vec)
        unbound = fhrr_model.opset.bind(bound_hv.vec, inv_b)
        unbound_hv = fhrr_model.rep_cls(unbound).normalize()

        # Verify the unbind operation produces valid output
        assert unbound_hv.shape == a.shape
        assert jnp.iscomplexobj(unbound_hv.vec)
        assert jnp.allclose(jnp.abs(unbound_hv.vec), 1.0)  # Unit magnitude

    def test_fhrr_bundle(self, fhrr_model):
        """Test bundling with FHRR model."""
        key = jax.random.PRNGKey(42)
        vectors = fhrr_model.sampler(dim=fhrr_model.dim, n=3, key=key)

        hvs = [fhrr_model.rep_cls(vec).normalize() for vec in vectors]

        # Bundle
        bundled = fhrr_model.opset.bundle(*[hv.vec for hv in hvs])
        bundled_hv = fhrr_model.rep_cls(bundled)

        # Should be complex and unit magnitude
        assert jnp.iscomplexobj(bundled_hv.vec)
        assert jnp.allclose(jnp.abs(bundled_hv.vec), 1.0)


class TestMAPModel:
    """Integration tests for MAP model (RealHypervector + MAPOperations)."""

    @pytest.fixture
    def map_model(self):
        """Create MAP VSAModel."""
        return VSAModel(
            dim=512,
            rep_cls=RealHypervector,
            opset=MAPOperations(),
            sampler=sample_random,
        )

    def test_map_model_creation(self, map_model):
        """Test MAP model can be created."""
        assert map_model.dim == 512
        assert map_model.rep_cls == RealHypervector
        assert isinstance(map_model.opset, MAPOperations)

    def test_map_sampling_and_wrapping(self, map_model):
        """Test sampling and wrapping with MAP model."""
        key = jax.random.PRNGKey(42)
        vectors = map_model.sampler(dim=map_model.dim, n=5, key=key)

        # Wrap in representation
        hvs = [map_model.rep_cls(vec) for vec in vectors]

        for hv in hvs:
            assert isinstance(hv, RealHypervector)
            assert hv.shape == (map_model.dim,)
            assert not jnp.iscomplexobj(hv.vec)

    def test_map_bind_and_unbind(self, map_model):
        """Test bind and unbind workflow with MAP model."""
        key = jax.random.PRNGKey(42)
        vectors = map_model.sampler(dim=map_model.dim, n=2, key=key)

        a = map_model.rep_cls(vectors[0]).normalize()
        b = map_model.rep_cls(vectors[1]).normalize()

        # Bind
        bound = map_model.opset.bind(a.vec, b.vec)
        bound_hv = map_model.rep_cls(bound).normalize()

        # Unbind (approximate)
        inv_b = map_model.opset.inverse(b.vec)
        unbound = map_model.opset.bind(bound_hv.vec, inv_b)
        unbound_hv = map_model.rep_cls(unbound).normalize()

        # Check similarity to original (approximate unbinding)
        similarity = jnp.dot(a.vec, unbound_hv.vec)
        assert similarity > 0.5  # MAP unbinding is approximate

    def test_map_bundle(self, map_model):
        """Test bundling with MAP model."""
        key = jax.random.PRNGKey(42)
        vectors = map_model.sampler(dim=map_model.dim, n=3, key=key)

        hvs = [map_model.rep_cls(vec).normalize() for vec in vectors]

        # Bundle
        bundled = map_model.opset.bundle(*[hv.vec for hv in hvs])
        bundled_hv = map_model.rep_cls(bundled)

        # Should be real-valued
        assert not jnp.iscomplexobj(bundled_hv.vec)


class TestBinaryModel:
    """Integration tests for Binary model (BinaryHypervector + BinaryOperations)."""

    @pytest.fixture
    def binary_model(self):
        """Create Binary VSAModel."""
        return VSAModel(
            dim=512,
            rep_cls=BinaryHypervector,
            opset=BinaryOperations(),
            sampler=sample_binary_random,
        )

    def test_binary_model_creation(self, binary_model):
        """Test Binary model can be created."""
        assert binary_model.dim == 512
        assert binary_model.rep_cls == BinaryHypervector
        assert isinstance(binary_model.opset, BinaryOperations)

    def test_binary_sampling_and_wrapping(self, binary_model):
        """Test sampling and wrapping with Binary model."""
        key = jax.random.PRNGKey(42)
        vectors = binary_model.sampler(dim=binary_model.dim, n=5, key=key, bipolar=True)

        # Wrap in representation
        hvs = [binary_model.rep_cls(vec, bipolar=True) for vec in vectors]

        for hv in hvs:
            assert isinstance(hv, BinaryHypervector)
            assert hv.shape == (binary_model.dim,)
            assert jnp.all(jnp.isin(hv.vec, jnp.array([-1, 1])))

    def test_binary_bind_and_unbind(self, binary_model):
        """Test bind and unbind workflow with Binary model."""
        key = jax.random.PRNGKey(42)
        vectors = binary_model.sampler(dim=binary_model.dim, n=2, key=key, bipolar=True)

        a = binary_model.rep_cls(vectors[0], bipolar=True)
        b = binary_model.rep_cls(vectors[1], bipolar=True)

        # Bind
        bound = binary_model.opset.bind(a.vec, b.vec)
        bound_hv = binary_model.rep_cls(bound, bipolar=True)

        # Unbind (self-inverse)
        unbound = binary_model.opset.bind(bound_hv.vec, b.vec)
        unbound_hv = binary_model.rep_cls(unbound, bipolar=True)

        # Should recover exactly
        assert jnp.array_equal(unbound_hv.vec, a.vec)

    def test_binary_bundle(self, binary_model):
        """Test bundling with Binary model."""
        key = jax.random.PRNGKey(42)
        vectors = binary_model.sampler(dim=binary_model.dim, n=3, key=key, bipolar=True)

        hvs = [binary_model.rep_cls(vec, bipolar=True) for vec in vectors]

        # Bundle
        bundled = binary_model.opset.bundle(*[hv.vec for hv in hvs])
        bundled_hv = binary_model.rep_cls(bundled, bipolar=True)

        # Should be bipolar
        assert jnp.all(jnp.isin(bundled_hv.vec, jnp.array([-1, 1])))


class TestModelComparison:
    """Cross-model comparison tests."""

    def test_all_models_have_same_interface(self):
        """Test that all models follow the same interface."""
        fhrr = VSAModel(
            dim=512,
            rep_cls=ComplexHypervector,
            opset=FHRROperations(),
            sampler=sample_complex_random,
        )
        map_model = VSAModel(
            dim=512,
            rep_cls=RealHypervector,
            opset=MAPOperations(),
            sampler=sample_random,
        )
        binary = VSAModel(
            dim=512,
            rep_cls=BinaryHypervector,
            opset=BinaryOperations(),
            sampler=sample_binary_random,
        )

        for model in [fhrr, map_model, binary]:
            assert hasattr(model, "dim")
            assert hasattr(model, "rep_cls")
            assert hasattr(model, "opset")
            assert hasattr(model, "sampler")

            # Check opset has required methods
            assert hasattr(model.opset, "bind")
            assert hasattr(model.opset, "bundle")
            assert hasattr(model.opset, "inverse")
            assert hasattr(model.opset, "permute")

    def test_different_dimensions(self):
        """Test creating models with different dimensions."""
        for dim in [128, 256, 512, 1024]:
            fhrr = VSAModel(
                dim=dim,
                rep_cls=ComplexHypervector,
                opset=FHRROperations(),
                sampler=sample_complex_random,
            )
            assert fhrr.dim == dim

            key = jax.random.PRNGKey(42)
            vectors = fhrr.sampler(dim=dim, n=1, key=key)
            assert vectors.shape == (1, dim)

    def test_model_immutability(self):
        """Test that models are immutable."""
        model = VSAModel(
            dim=512,
            rep_cls=ComplexHypervector,
            opset=FHRROperations(),
            sampler=sample_complex_random,
        )

        # dataclass frozen raises FrozenInstanceError or AttributeError
        with pytest.raises(Exception):
            model.dim = 1024
