"""Vector Function Architecture for function encoding and manipulation.

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
from vsax.vfa.kernels import KernelConfig, sample_kernel_basis


class VectorFunctionEncoder:
    """Vector Function Architecture for encoding functions in RKHS.

    Represents functions f(x) in a Reproducing Kernel Hilbert Space (RKHS)
    using hypervectors:
        f(x) ≈ Σ α_i * z_i^x

    where z_i are basis vectors and α_i are coefficients learned from samples.

    This enables:
        - Function approximation from samples
        - Point evaluation: f(x_query)
        - Function arithmetic: α*f + β*g
        - Function shifting: f(x - shift)
        - Function convolution: f * g

    Based on Frady et al. 2021 which demonstrates that VFA can represent
    and manipulate functions using vector symbolic operations.

    Attributes:
        model: VSAModel instance (must use ComplexHypervector).
        memory: VSAMemory for storing basis vectors.
        kernel_config: KernelConfig for basis vector sampling.
        basis_vector: The function basis vector z (sampled once).

    Example:
        >>> import jax
        >>> import jax.numpy as jnp
        >>> from vsax import create_fhrr_model, VSAMemory
        >>> from vsax.vfa import VectorFunctionEncoder, KernelConfig
        >>>
        >>> # Create VFA encoder
        >>> model = create_fhrr_model(dim=512, key=jax.random.PRNGKey(0))
        >>> memory = VSAMemory(model)
        >>> vfa = VectorFunctionEncoder(model, memory)
        >>>
        >>> # Sample a simple function
        >>> x = jnp.linspace(0, 2*jnp.pi, 20)
        >>> y = jnp.sin(x)
        >>>
        >>> # Encode the function
        >>> f_hv = vfa.encode_function_1d(x, y)
        >>>
        >>> # Evaluate at a query point
        >>> y_pred = vfa.evaluate_1d(f_hv, 1.5)

    See Also:
        - Frady et al. 2021: "Computing on Functions Using Randomized
          Vector Representations"
    """

    def __init__(
        self,
        model: VSAModel,
        memory: VSAMemory,
        kernel_config: Optional[KernelConfig] = None,
        basis_key: Optional[jax.Array] = None,
    ) -> None:
        """Initialize VectorFunctionEncoder.

        Args:
            model: VSAModel instance (must use ComplexHypervector).
            memory: VSAMemory for storing basis vectors.
            kernel_config: KernelConfig for basis sampling (default: UNIFORM).
            basis_key: Optional JAX key for basis sampling. If None, uses PRNGKey(0).

        Raises:
            TypeError: If model doesn't use ComplexHypervector.
        """
        from vsax.representations import ComplexHypervector

        if model.rep_cls != ComplexHypervector:
            raise TypeError(
                "VectorFunctionEncoder requires ComplexHypervector (FHRR) model. "
                f"Got {model.rep_cls.__name__}. "
                "Use create_fhrr_model() to create a compatible model."
            )

        self.model = model
        self.memory = memory

        # Ensure kernel_config dim matches model dim
        if kernel_config is not None:
            self.kernel_config = kernel_config
        else:
            self.kernel_config = KernelConfig(dim=model.dim)

        # Sample a single basis vector for function encoding
        key = basis_key if basis_key is not None else jax.random.PRNGKey(0)
        self.basis_vector = sample_kernel_basis(self.kernel_config, key)

    def encode_function_1d(
        self,
        x_samples: jnp.ndarray,
        y_samples: jnp.ndarray,
        regularization: float = 1e-6,
    ) -> ComplexHypervector:
        """Encode a 1D function from samples.

        Learns coefficients α such that f(x) ≈ Σ α_i * z^x_i for the sample points.
        Uses least squares to fit the coefficients.

        Args:
            x_samples: Array of x coordinates (shape: (n_samples,)).
            y_samples: Array of y values (shape: (n_samples,)).
            regularization: Regularization parameter for least squares (default: 1e-6).

        Returns:
            ComplexHypervector encoding the function.

        Raises:
            ValueError: If x_samples and y_samples have different lengths.

        Example:
            >>> # Encode sine function
            >>> x = jnp.linspace(0, 2*jnp.pi, 50)
            >>> y = jnp.sin(x)
            >>> f_hv = vfa.encode_function_1d(x, y)
        """
        if len(x_samples) != len(y_samples):
            raise ValueError(
                f"x_samples and y_samples must have same length. "
                f"Got {len(x_samples)} and {len(y_samples)}"
            )

        n_samples = len(x_samples)

        # Build design matrix: each row is z^x_i
        # Z[i] = basis_vector^x_samples[i]
        design_matrix = jnp.zeros((n_samples, self.model.dim), dtype=jnp.complex64)

        for i in range(n_samples):
            # Raise basis vector to power x_samples[i]
            powered = jnp.power(self.basis_vector, x_samples[i])
            design_matrix = design_matrix.at[i].set(powered)

        # Solve for coefficients: Z * alpha = y
        # Using regularized least squares: alpha = (Z^H Z + lambda I)^(-1) Z^H y
        ZH_Z = jnp.dot(design_matrix.conj().T, design_matrix)
        reg_term = regularization * jnp.eye(self.model.dim)
        ZH_y = jnp.dot(design_matrix.conj().T, y_samples)

        # Solve linear system
        coefficients = jnp.linalg.solve(ZH_Z + reg_term, ZH_y)

        return ComplexHypervector(coefficients)

    def evaluate_1d(
        self,
        function_hv: ComplexHypervector,
        x_query: float,
    ) -> float:
        """Evaluate encoded function at a query point.

        Computes f(x_query) = <function_hv, z^x_query> where <·,·> is inner product.

        Args:
            function_hv: Encoded function hypervector (from encode_function_1d).
            x_query: Point at which to evaluate the function.

        Returns:
            Estimated function value at x_query (real-valued).

        Example:
            >>> f_hv = vfa.encode_function_1d(x_train, y_train)
            >>> y_pred = vfa.evaluate_1d(f_hv, 1.5)
        """
        # Compute z^x_query
        query_vec = jnp.power(self.basis_vector, x_query)

        # Inner product: f(x) = <coefficients, z^x>
        result = jnp.vdot(query_vec, function_hv.vec)

        # Return real part (imaginary part should be ~0 for real functions)
        return float(jnp.real(result))

    def add_functions(
        self,
        f1: ComplexHypervector,
        f2: ComplexHypervector,
        alpha: float = 1.0,
        beta: float = 1.0,
    ) -> ComplexHypervector:
        """Compute linear combination of two functions.

        Returns h = alpha * f1 + beta * f2

        Args:
            f1: First encoded function.
            f2: Second encoded function.
            alpha: Coefficient for f1 (default: 1.0).
            beta: Coefficient for f2 (default: 1.0).

        Returns:
            Encoded function representing alpha*f1 + beta*f2.

        Example:
            >>> # Compute f + g
            >>> h = vfa.add_functions(f_hv, g_hv)
            >>> # Compute 2*f - 0.5*g
            >>> h = vfa.add_functions(f_hv, g_hv, alpha=2.0, beta=-0.5)
        """
        result = alpha * f1.vec + beta * f2.vec
        return ComplexHypervector(result)

    def shift_function(
        self,
        function_hv: ComplexHypervector,
        shift: float,
    ) -> ComplexHypervector:
        """Shift a function: f(x) -> f(x - shift).

        Uses the property: if f(x) = Σ α_i * z^x, then
        f(x - s) = Σ α_i * z^(x-s) = Σ α_i * z^(-s) * z^x = (z^(-s) ⊙ α) * z^x

        where ⊙ is element-wise multiplication.

        Args:
            function_hv: Encoded function to shift.
            shift: Amount to shift (positive shifts right).

        Returns:
            Encoded function representing f(x - shift).

        Example:
            >>> # Shift sine function to the right by π/2
            >>> x = jnp.linspace(0, 2*jnp.pi, 50)
            >>> y = jnp.sin(x)
            >>> f_hv = vfa.encode_function_1d(x, y)
            >>> shifted = vfa.shift_function(f_hv, jnp.pi/2)
            >>> # shifted should approximate cos(x)
        """
        # Compute shift factor: z^(-shift)
        shift_factor = jnp.power(self.basis_vector, -shift)

        # Apply element-wise multiplication
        result = shift_factor * function_hv.vec

        return ComplexHypervector(result)

    def convolve_functions(
        self,
        f1: ComplexHypervector,
        f2: ComplexHypervector,
    ) -> ComplexHypervector:
        """Compute convolution of two functions.

        For functions represented in VFA, convolution can be approximated
        by binding (circular convolution in frequency domain).

        Args:
            f1: First encoded function.
            f2: Second encoded function.

        Returns:
            Encoded function representing approximate convolution f1 * f2.

        Example:
            >>> # Convolve two functions
            >>> h = vfa.convolve_functions(f_hv, g_hv)

        Note:
            This is an approximation. The quality depends on the dimensionality
            and the specific functions being convolved.
        """
        # Use FHRR binding (circular convolution)
        result = self.model.opset.bind(f1.vec, f2.vec)
        return ComplexHypervector(result)

    def evaluate_batch(
        self,
        function_hv: ComplexHypervector,
        x_queries: jnp.ndarray,
    ) -> jnp.ndarray:
        """Evaluate function at multiple query points.

        Convenience function for batch evaluation.

        Args:
            function_hv: Encoded function hypervector.
            x_queries: Array of query points (shape: (n_queries,)).

        Returns:
            Array of function values (shape: (n_queries,)).

        Example:
            >>> x_test = jnp.linspace(0, 2*jnp.pi, 100)
            >>> y_pred = vfa.evaluate_batch(f_hv, x_test)
        """
        return jnp.array([self.evaluate_1d(function_hv, x) for x in x_queries])
