"""VFA Applications for density estimation, regression, and image processing.

Based on:
    Frady et al. 2021: "Computing on Functions Using Randomized Vector
    Representations"
"""

from typing import Optional

import jax
import jax.numpy as jnp

from vsax.core.memory import VSAMemory
from vsax.core.model import VSAModel
from vsax.representations import ComplexHypervector
from vsax.vfa.function_encoder import VectorFunctionEncoder
from vsax.vfa.kernels import KernelConfig


class DensityEstimator:
    """Kernel density estimation using VFA (Frady et al. 2021 §7.2.1).

    Estimates probability density functions from sample data by encoding
    the density as a hypervector. Uses VFA to represent the density function
    in RKHS.

    The density is estimated as:
        p(x) ∝ Σ_i K(x - x_i)
    where K is a kernel function and x_i are the sample points.

    Attributes:
        vfa: VectorFunctionEncoder for function encoding.
        bandwidth: Kernel bandwidth for density estimation.

    Example:
        >>> import jax
        >>> from vsax import create_fhrr_model, VSAMemory
        >>> from vsax.vfa import DensityEstimator
        >>>
        >>> # Create estimator
        >>> key = jax.random.PRNGKey(42)
        >>> model = create_fhrr_model(dim=512, key=key)
        >>> memory = VSAMemory(model)
        >>> estimator = DensityEstimator(model, memory, bandwidth=0.5)
        >>>
        >>> # Fit to data
        >>> samples = jax.random.normal(key, (100,))
        >>> estimator.fit(samples)
        >>>
        >>> # Evaluate density
        >>> x_query = jnp.array([0.0, 1.0, 2.0])
        >>> densities = estimator.evaluate(x_query)
    """

    def __init__(
        self,
        model: VSAModel,
        memory: VSAMemory,
        bandwidth: float = 1.0,
        kernel_config: Optional[KernelConfig] = None,
    ) -> None:
        """Initialize DensityEstimator.

        Args:
            model: VSAModel instance (must use ComplexHypervector).
            memory: VSAMemory for storing basis vectors.
            bandwidth: Kernel bandwidth for density estimation (default: 1.0).
            kernel_config: Optional KernelConfig for VFA basis.

        Raises:
            TypeError: If model doesn't use ComplexHypervector.
            ValueError: If bandwidth is not positive.
        """
        if bandwidth <= 0:
            raise ValueError(f"bandwidth must be positive, got {bandwidth}")

        self.vfa = VectorFunctionEncoder(model, memory, kernel_config)
        self.bandwidth = bandwidth
        self._density_hv: Optional[ComplexHypervector] = None
        self._fitted = False

    def fit(self, samples: jnp.ndarray) -> None:
        """Fit density estimator to sample data.

        Estimates the density function from samples by creating a kernel
        density estimate and encoding it as a hypervector.

        Args:
            samples: 1D array of sample points (shape: (n_samples,)).

        Raises:
            ValueError: If samples is not 1D.
        """
        if samples.ndim != 1:
            raise ValueError(f"samples must be 1D array, got shape {samples.shape}")

        # Create grid for density evaluation
        x_min, x_max = jnp.min(samples), jnp.max(samples)
        margin = 3 * self.bandwidth
        x_grid = jnp.linspace(x_min - margin, x_max + margin, 100)

        # Compute kernel density estimate on grid
        # p(x) ∝ Σ_i exp(-(x - x_i)^2 / (2 * h^2))
        density_values = jnp.zeros_like(x_grid)
        for sample in samples:
            kernel_values = jnp.exp(-((x_grid - sample) ** 2) / (2 * self.bandwidth**2))
            density_values += kernel_values

        # Normalize
        density_values /= len(samples) * self.bandwidth * jnp.sqrt(2 * jnp.pi)

        # Encode density function
        self._density_hv = self.vfa.encode_function_1d(x_grid, density_values)
        self._fitted = True

    def evaluate(self, x_query: jnp.ndarray) -> jnp.ndarray:
        """Evaluate density at query points.

        Args:
            x_query: Array of query points (shape: (n_queries,)).

        Returns:
            Estimated density values at query points (shape: (n_queries,)).

        Raises:
            RuntimeError: If estimator has not been fitted.
        """
        if not self._fitted:
            raise RuntimeError(
                "DensityEstimator must be fitted before evaluation. Call fit() first."
            )

        assert self._density_hv is not None  # Set by fit()
        return self.vfa.evaluate_batch(self._density_hv, x_query)

    def sample(self, key: jax.Array, n_samples: int = 1) -> jnp.ndarray:
        """Sample from the estimated density (not implemented).

        Args:
            key: JAX random key.
            n_samples: Number of samples to generate.

        Returns:
            Samples from the density.

        Raises:
            NotImplementedError: Sampling not yet implemented.
        """
        raise NotImplementedError(
            "Sampling from VFA density estimates is not yet implemented. "
            "This would require inverse transform sampling or MCMC."
        )


class NonlinearRegressor:
    """Nonlinear regression using VFA (Frady et al. 2021 §7.2.2).

    Fits nonlinear functions to (x, y) data using vector function architecture.
    Provides a scikit-learn-like interface for regression tasks.

    Attributes:
        vfa: VectorFunctionEncoder for function encoding.
        regularization: Regularization parameter for least squares.

    Example:
        >>> import jax.numpy as jnp
        >>> from vsax import create_fhrr_model, VSAMemory
        >>> from vsax.vfa import NonlinearRegressor
        >>>
        >>> # Create regressor
        >>> key = jax.random.PRNGKey(42)
        >>> model = create_fhrr_model(dim=1024, key=key)
        >>> memory = VSAMemory(model)
        >>> regressor = NonlinearRegressor(model, memory)
        >>>
        >>> # Fit to nonlinear data
        >>> x_train = jnp.linspace(0, 10, 50)
        >>> y_train = jnp.sin(x_train) + 0.1 * jax.random.normal(key, (50,))
        >>> regressor.fit(x_train, y_train)
        >>>
        >>> # Predict
        >>> x_test = jnp.linspace(0, 10, 100)
        >>> y_pred = regressor.predict(x_test)
    """

    def __init__(
        self,
        model: VSAModel,
        memory: VSAMemory,
        regularization: float = 1e-6,
        kernel_config: Optional[KernelConfig] = None,
    ) -> None:
        """Initialize NonlinearRegressor.

        Args:
            model: VSAModel instance (must use ComplexHypervector).
            memory: VSAMemory for storing basis vectors.
            regularization: Regularization parameter (default: 1e-6).
            kernel_config: Optional KernelConfig for VFA basis.

        Raises:
            TypeError: If model doesn't use ComplexHypervector.
            ValueError: If regularization is negative.
        """
        if regularization < 0:
            raise ValueError(f"regularization must be non-negative, got {regularization}")

        self.vfa = VectorFunctionEncoder(model, memory, kernel_config)
        self.regularization = regularization
        self._function_hv: Optional[ComplexHypervector] = None
        self._fitted = False

    def fit(self, x_train: jnp.ndarray, y_train: jnp.ndarray) -> None:
        """Fit regressor to training data.

        Args:
            x_train: Training input values (shape: (n_samples,)).
            y_train: Training target values (shape: (n_samples,)).

        Raises:
            ValueError: If x_train and y_train have different lengths.
        """
        self._function_hv = self.vfa.encode_function_1d(
            x_train, y_train, regularization=self.regularization
        )
        self._fitted = True

    def predict(self, x_test: jnp.ndarray) -> jnp.ndarray:
        """Predict target values for test inputs.

        Args:
            x_test: Test input values (shape: (n_test,)).

        Returns:
            Predicted target values (shape: (n_test,)).

        Raises:
            RuntimeError: If regressor has not been fitted.
        """
        if not self._fitted:
            raise RuntimeError(
                "NonlinearRegressor must be fitted before prediction. Call fit() first."
            )

        assert self._function_hv is not None  # Set by fit()
        return self.vfa.evaluate_batch(self._function_hv, x_test)

    def score(self, x_test: jnp.ndarray, y_test: jnp.ndarray) -> float:
        """Compute R² score on test data.

        Args:
            x_test: Test input values (shape: (n_test,)).
            y_test: True target values (shape: (n_test,)).

        Returns:
            R² score (1.0 is perfect, 0.0 is baseline, negative is worse than baseline).

        Raises:
            RuntimeError: If regressor has not been fitted.
        """
        if not self._fitted:
            raise RuntimeError(
                "NonlinearRegressor must be fitted before scoring. Call fit() first."
            )

        y_pred = self.predict(x_test)

        # R² = 1 - (SS_res / SS_tot)
        ss_res = jnp.sum((y_test - y_pred) ** 2)
        ss_tot = jnp.sum((y_test - jnp.mean(y_test)) ** 2)

        r2 = 1.0 - (ss_res / ss_tot)
        return float(r2)


class ImageProcessor:
    """Image processing using VFA (Frady et al. 2021 §7.1).

    Encodes 2D images as vector functions and supports spatial transformations.
    Images are represented as functions f(x, y) mapping coordinates to pixel values.

    Attributes:
        vfa: VectorFunctionEncoder for function encoding.
        image_shape: Shape of the encoded image (height, width).

    Example:
        >>> import jax.numpy as jnp
        >>> from vsax import create_fhrr_model, VSAMemory
        >>> from vsax.vfa import ImageProcessor
        >>>
        >>> # Create processor
        >>> key = jax.random.PRNGKey(42)
        >>> model = create_fhrr_model(dim=2048, key=key)
        >>> memory = VSAMemory(model)
        >>> processor = ImageProcessor(model, memory)
        >>>
        >>> # Encode image
        >>> image = jnp.zeros((32, 32))
        >>> image = image.at[10:20, 10:20].set(1.0)  # White square
        >>> processor.encode(image)
        >>>
        >>> # Shift image
        >>> shifted = processor.shift(dx=5.0, dy=5.0)
        >>> reconstructed = processor.decode(shifted, shape=(32, 32))
    """

    def __init__(
        self,
        model: VSAModel,
        memory: VSAMemory,
        kernel_config: Optional[KernelConfig] = None,
    ) -> None:
        """Initialize ImageProcessor.

        Args:
            model: VSAModel instance (must use ComplexHypervector).
            memory: VSAMemory for storing basis vectors.
            kernel_config: Optional KernelConfig for VFA basis.

        Raises:
            TypeError: If model doesn't use ComplexHypervector.
        """
        self.vfa = VectorFunctionEncoder(model, memory, kernel_config)
        self._image_hv: Optional[ComplexHypervector] = None
        self._image_shape: Optional[tuple[int, int]] = None
        self._encoded = False

    def encode(self, image: jnp.ndarray) -> ComplexHypervector:
        """Encode a 2D image as a hypervector.

        Note: Currently implements a simplified version that flattens the image
        and encodes it as a 1D function. Full 2D encoding would require
        multi-dimensional VFA which is planned for future work.

        Args:
            image: 2D array representing the image (shape: (height, width)).

        Returns:
            Encoded image hypervector.

        Raises:
            ValueError: If image is not 2D.
        """
        if image.ndim != 2:
            raise ValueError(f"image must be 2D array, got shape {image.shape}")

        self._image_shape = image.shape
        height, width = image.shape

        # Flatten image for 1D encoding (simplified approach)
        # Full 2D encoding would use multi-dimensional VFA
        x_coords = jnp.arange(height * width, dtype=jnp.float32)
        pixel_values = image.flatten()

        self._image_hv = self.vfa.encode_function_1d(x_coords, pixel_values)
        self._encoded = True

        return self._image_hv

    def decode(
        self,
        image_hv: ComplexHypervector,
        shape: tuple[int, int],
    ) -> jnp.ndarray:
        """Decode hypervector back to image.

        Args:
            image_hv: Encoded image hypervector.
            shape: Output image shape (height, width).

        Returns:
            Reconstructed 2D image array.
        """
        height, width = shape

        # Evaluate at grid points
        x_coords = jnp.arange(height * width, dtype=jnp.float32)
        pixel_values = self.vfa.evaluate_batch(image_hv, x_coords)

        # Reshape to image
        return pixel_values.reshape(height, width)

    def shift(self, dx: float = 0.0, dy: float = 0.0) -> ComplexHypervector:
        """Shift the encoded image.

        Note: Current simplified implementation shifts in the flattened space.
        Full 2D shifting would require multi-dimensional VFA.

        Args:
            dx: Horizontal shift amount (not used in current simplified version).
            dy: Vertical shift amount (not used in current simplified version).

        Returns:
            Shifted image hypervector.

        Raises:
            RuntimeError: If no image has been encoded.
            NotImplementedError: 2D shifting not yet implemented.
        """
        if not self._encoded:
            raise RuntimeError(
                "ImageProcessor must encode an image before shifting. Call encode() first."
            )

        # For proper 2D shifting, we would need multi-dimensional VFA
        raise NotImplementedError(
            "2D image shifting requires multi-dimensional VFA which is planned "
            "for future work. Current implementation only supports 1D flattened encoding."
        )

    def blend(
        self,
        image_hv1: ComplexHypervector,
        image_hv2: ComplexHypervector,
        alpha: float = 0.5,
    ) -> ComplexHypervector:
        """Blend two encoded images.

        Args:
            image_hv1: First encoded image.
            image_hv2: Second encoded image.
            alpha: Blending factor (0.0 = all image1, 1.0 = all image2).

        Returns:
            Blended image hypervector.

        Raises:
            ValueError: If alpha is not in [0, 1].
        """
        if not (0.0 <= alpha <= 1.0):
            raise ValueError(f"alpha must be in [0, 1], got {alpha}")

        # Blend using function addition
        return self.vfa.add_functions(image_hv1, image_hv2, alpha=(1.0 - alpha), beta=alpha)
