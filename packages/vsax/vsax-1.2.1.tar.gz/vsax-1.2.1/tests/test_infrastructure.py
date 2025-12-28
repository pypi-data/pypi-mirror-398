"""Test infrastructure and basic imports."""

import pytest


def test_jax_available() -> None:
    """Test that JAX is available and importable."""
    import jax

    assert jax.__version__ is not None


def test_jax_numpy_available() -> None:
    """Test that JAX NumPy is available."""
    import jax.numpy as jnp

    # Simple test to ensure jnp works
    arr = jnp.array([1, 2, 3])
    assert arr.shape == (3,)


def test_package_imports() -> None:
    """Test that main package components can be imported."""
    import vsax
    from vsax.core import AbstractHypervector, AbstractOpSet, VSAModel

    assert vsax.__version__ == "1.2.1"
    assert AbstractHypervector is not None
    assert AbstractOpSet is not None
    assert VSAModel is not None


def test_abstract_hypervector_is_abstract() -> None:
    """Test that AbstractHypervector cannot be instantiated directly."""
    import jax.numpy as jnp

    from vsax.core import AbstractHypervector

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        AbstractHypervector(jnp.array([1.0, 2.0, 3.0]))


def test_abstract_opset_is_abstract() -> None:
    """Test that AbstractOpSet cannot be instantiated directly."""
    from vsax.core import AbstractOpSet

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        AbstractOpSet()


def test_vsa_model_creation() -> None:
    """Test VSAModel creation with mock components."""
    import jax
    import jax.numpy as jnp

    from vsax.core import AbstractHypervector, AbstractOpSet, VSAModel

    # Create minimal concrete implementations for testing
    class MockHypervector(AbstractHypervector):
        def normalize(self):
            return MockHypervector(self._vec / jnp.linalg.norm(self._vec))

    class MockOpSet(AbstractOpSet):
        def bind(self, a, b):
            return a * b

        def bundle(self, *vecs):
            return jnp.mean(jnp.stack(vecs), axis=0)

        def inverse(self, a):
            return a

    def mock_sampler(dim, n, key=None):
        if key is None:
            key = jax.random.PRNGKey(0)
        return jax.random.normal(key, shape=(n, dim))

    # Test valid model creation
    model = VSAModel(dim=512, rep_cls=MockHypervector, opset=MockOpSet(), sampler=mock_sampler)

    assert model.dim == 512
    assert model.rep_cls == MockHypervector
    assert isinstance(model.opset, MockOpSet)


def test_vsa_model_invalid_dim() -> None:
    """Test that VSAModel raises error for invalid dimensions."""
    import jax
    import jax.numpy as jnp

    from vsax.core import AbstractHypervector, AbstractOpSet, VSAModel

    class MockHypervector(AbstractHypervector):
        def normalize(self):
            return MockHypervector(self._vec / jnp.linalg.norm(self._vec))

    class MockOpSet(AbstractOpSet):
        def bind(self, a, b):
            return a * b

        def bundle(self, *vecs):
            return jnp.mean(jnp.stack(vecs), axis=0)

        def inverse(self, a):
            return a

    def mock_sampler(dim, n, key=None):
        if key is None:
            key = jax.random.PRNGKey(0)
        return jax.random.normal(key, shape=(n, dim))

    # Test invalid dimension
    with pytest.raises(ValueError, match="dim must be positive"):
        VSAModel(dim=0, rep_cls=MockHypervector, opset=MockOpSet(), sampler=mock_sampler)

    with pytest.raises(ValueError, match="dim must be positive"):
        VSAModel(dim=-100, rep_cls=MockHypervector, opset=MockOpSet(), sampler=mock_sampler)
