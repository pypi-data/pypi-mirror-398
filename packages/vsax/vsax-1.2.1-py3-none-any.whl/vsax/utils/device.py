"""Device management utilities for GPU/CPU control.

This module provides utilities for managing JAX devices (GPU/CPU),
checking device availability, and benchmarking operations.
"""

import time
from typing import Any, Callable, Optional, Union

import jax
import jax.numpy as jnp


def get_device_info() -> dict[str, object]:
    """Get information about available JAX devices.

    Returns:
        Dictionary containing:
        - 'devices': List of all available devices
        - 'default_backend': Default backend name (cpu, gpu, tpu)
        - 'device_count': Number of available devices
        - 'gpu_available': Whether GPU is available
    """
    devices = jax.devices()
    default_backend = jax.default_backend()

    return {
        "devices": devices,
        "default_backend": default_backend,
        "device_count": len(devices),
        "gpu_available": any(d.platform == "gpu" for d in devices),
    }


def print_device_info() -> None:
    """Print detailed information about available JAX devices."""
    info = get_device_info()
    devices: Any = info["devices"]  # Type is list of jax.Device

    print("=" * 60)
    print("JAX Device Information")
    print("=" * 60)
    print(f"Default backend: {info['default_backend']}")
    print(f"Device count: {info['device_count']}")
    print(f"GPU available: {info['gpu_available']}")
    print("\nAvailable devices:")
    for i, device in enumerate(devices):
        print(f"  [{i}] {device}")
    print("=" * 60)


def ensure_gpu() -> bool:
    """Check if GPU is available and warn if not.

    Returns:
        True if GPU is available, False otherwise
    """
    info = get_device_info()

    if not info["gpu_available"]:
        print("⚠️  WARNING: GPU not available, using CPU")
        print("   For GPU support, install JAX with GPU:")
        print("   pip install jax[cuda12]")
        return False

    print(f"✓ GPU available: {info['devices']}")
    return True


def get_array_device(array: jnp.ndarray) -> str:
    """Get the device where an array is stored.

    Args:
        array: JAX array

    Returns:
        String representation of the device (e.g., 'cuda:0', 'cpu:0')
    """
    return str(array.devices().pop())


def benchmark_operation(
    operation: Callable[[], jnp.ndarray],
    n_iterations: int = 10,
    warmup: int = 3,
    device: Optional[str] = None,
) -> dict[str, Union[float, str]]:
    """Benchmark an operation on a specific device.

    Args:
        operation: Function that performs the operation (takes no args, returns array)
        n_iterations: Number of iterations to average over
        warmup: Number of warmup iterations before timing
        device: Device to use ('cpu', 'gpu', or None for default)

    Returns:
        Dictionary containing:
        - 'mean_time': Mean execution time in seconds
        - 'std_time': Standard deviation of execution time
        - 'device': Device used
        - 'throughput': Operations per second
    """
    # Select device
    if device is not None:
        if device.lower() == "cpu":
            target_device = jax.devices("cpu")[0]
        elif device.lower() == "gpu":
            gpu_devices = [d for d in jax.devices() if d.platform == "gpu"]
            if not gpu_devices:
                raise ValueError("No GPU available")
            target_device = gpu_devices[0]
        else:
            raise ValueError(f"Unknown device: {device}")
    else:
        target_device = jax.devices()[0]

    # Run warmup iterations
    with jax.default_device(target_device):
        for _ in range(warmup):
            result = operation()
            result.block_until_ready()  # Ensure computation completes

    # Time iterations
    times = []
    with jax.default_device(target_device):
        for _ in range(n_iterations):
            start = time.perf_counter()
            result = operation()
            result.block_until_ready()  # Ensure computation completes
            end = time.perf_counter()
            times.append(end - start)

    mean_time = jnp.mean(jnp.array(times))
    std_time = jnp.std(jnp.array(times))

    return {
        "mean_time": float(mean_time),
        "std_time": float(std_time),
        "device": str(target_device),
        "throughput": 1.0 / float(mean_time),
    }


def compare_devices(
    operation: Callable[[], jnp.ndarray],
    n_iterations: int = 10,
) -> dict[str, Union[dict[str, Union[float, str]], float]]:
    """Compare operation performance on CPU vs GPU.

    Args:
        operation: Function that performs the operation
        n_iterations: Number of iterations to average over

    Returns:
        Dictionary with 'cpu' and 'gpu' benchmark results, and optional 'speedup' float
    """
    results: dict[str, Union[dict[str, Union[float, str]], float]] = {}

    # Benchmark CPU
    print("Benchmarking on CPU...")
    results["cpu"] = benchmark_operation(operation, n_iterations, device="cpu")

    # Benchmark GPU if available
    info = get_device_info()
    if info["gpu_available"]:
        print("Benchmarking on GPU...")
        results["gpu"] = benchmark_operation(operation, n_iterations, device="gpu")

        # Calculate speedup
        cpu_result = results["cpu"]
        gpu_result = results["gpu"]
        assert isinstance(cpu_result, dict) and isinstance(gpu_result, dict)
        cpu_time = cpu_result["mean_time"]
        gpu_time = gpu_result["mean_time"]
        assert isinstance(cpu_time, float) and isinstance(gpu_time, float)
        speedup = cpu_time / gpu_time
        results["speedup"] = speedup
        print(f"\n✓ GPU speedup: {speedup:.2f}x faster")
    else:
        print("⚠️  GPU not available, skipping GPU benchmark")

    return results


def print_benchmark_results(results: dict[str, Union[dict[str, Union[float, str]], float]]) -> None:
    """Pretty-print benchmark results.

    Args:
        results: Results from benchmark_operation or compare_devices
    """
    print("\n" + "=" * 60)
    print("Benchmark Results")
    print("=" * 60)

    for device_name, metrics in results.items():
        if device_name == "speedup":
            continue

        assert isinstance(metrics, dict)
        device_str = metrics["device"]
        mean_time = metrics["mean_time"]
        std_time = metrics["std_time"]
        throughput = metrics["throughput"]
        assert isinstance(mean_time, float)
        assert isinstance(std_time, float)
        assert isinstance(throughput, float)

        print(f"\n{device_name.upper()}:")
        print(f"  Device: {device_str}")
        print(f"  Mean time: {mean_time * 1000:.2f} ms")
        print(f"  Std time: {std_time * 1000:.2f} ms")
        print(f"  Throughput: {throughput:.2f} ops/sec")

    if "speedup" in results:
        speedup = results["speedup"]
        assert isinstance(speedup, float)
        print(f"\nSpeedup: {speedup:.2f}x (GPU vs CPU)")

    print("=" * 60)
