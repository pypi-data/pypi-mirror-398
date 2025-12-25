'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2025-07-24 12:51:45 +0200
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-09-28 08:18:07 +0200
FilePath     : utils_tensorflow.py
Description  :

Copyright (c) 2025 by everyone, All Rights Reserved.
'''

import subprocess
import re
import os
from typing import Optional, Tuple
import pandas as pd

from analysis_tool.utils.utils_logging import get_logger

logger = get_logger(__name__, auto_setup_rich_logging=True)


def find_best_available_gpu(min_free_memory_mb: int = 1000) -> Optional[int]:
    """
    Find the GPU with the most available memory.

    Args:
        min_free_memory_mb: Minimum free memory required in MB

    Returns:
        GPU ID with most free memory, or None if no suitable GPU found
    """
    try:
        # Run nvidia-smi to get GPU memory info
        result = subprocess.run(['nvidia-smi', '--query-gpu=index,memory.free,memory.total', '--format=csv,noheader,nounits'], capture_output=True, text=True, check=True)

        # Collect GPU data in a list first
        gpu_data = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                parts = line.split(', ')
                gpu_id = int(parts[0])
                free_memory = int(parts[1])
                total_memory = int(parts[2])
                used_memory = total_memory - free_memory
                usage_percent = (used_memory / total_memory) * 100

                gpu_data.append(
                    {
                        'gpu_id': gpu_id,
                        'free_memory_mb': free_memory,
                        'used_memory_mb': used_memory,
                        'total_memory_mb': total_memory,
                        'usage_percent': round(usage_percent, 1),
                        'free_memory_gb': round(free_memory / 1024, 1),
                        'total_memory_gb': round(total_memory / 1024, 1),
                    }
                )

        # Create DataFrame from the list
        gpu_info = pd.DataFrame(gpu_data)

        if gpu_info.empty:
            logger.error("No GPUs found")
            return None

        # Display GPU information in table format
        print("\n======== GPU Memory Information ========")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', None)

        # Create a nice display DataFrame
        display_df = gpu_info[['gpu_id', 'free_memory_gb', 'total_memory_gb', 'usage_percent']].copy()
        display_df.columns = ['GPU ID', 'Free (GB)', 'Total (GB)', 'Usage (%)']
        print(display_df.to_string(index=False, float_format='%.1f'))
        print("=" * 40)

        # Filter GPUs with sufficient free memory
        suitable_gpus = gpu_info[gpu_info['free_memory_mb'] >= min_free_memory_mb]

        if suitable_gpus.empty:
            logger.warning(f"No GPU found with at least {min_free_memory_mb}MB ({min_free_memory_mb/1024:.1f}GB) free memory")
            return None

        # Select GPU with most free memory
        best_gpu_idx = suitable_gpus['free_memory_mb'].idxmax()
        best_gpu = suitable_gpus.loc[best_gpu_idx]

        gpu_id = int(best_gpu['gpu_id'])
        free_mem_mb = best_gpu['free_memory_mb']
        free_mem_gb = best_gpu['free_memory_gb']
        total_mem_gb = best_gpu['total_memory_gb']

        logger.info(f"\nSelected GPU {gpu_id}: {free_mem_gb:.1f}GB free / {total_mem_gb:.1f}GB total")
        return gpu_id

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.error(f"Error checking GPU status: {e}")
        return None


def _configure_tensorflow_memory_growth(gpus, memory_requirement_mb: int):
    """Configure TensorFlow with memory growth."""
    if 'tf' not in globals():
        import tensorflow as tf

    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)
    logger.info("Enabled TensorFlow GPU memory growth")


def _configure_tensorflow_memory_occupancy(gpus, memory_requirement_mb: int):
    """Configure TensorFlow with fully occupy the specified GPU memory."""
    if 'tf' not in globals():
        import tensorflow as tf

    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, False)
    logger.info("Enabled TensorFlow GPU memory occupancy")


def _configure_tensorflow_memory_limit(gpus, memory_requirement_mb: int, additional_buffer_mb: int = 2000):
    """Configure TensorFlow with fixed memory limit."""
    if 'tf' not in globals():
        import tensorflow as tf

    try:
        selected_gpu = gpus[0]  # First GPU (since we set CUDA_VISIBLE_DEVICES)
        memory_limit_mb = memory_requirement_mb + additional_buffer_mb

        tf.config.experimental.set_virtual_device_configuration(selected_gpu, [tf.config.experimental.VirtualDeviceConfiguration(memory_limit=memory_limit_mb)])
        logger.info(
            f"Set GPU memory limit to {memory_limit_mb}MB ({memory_limit_mb/1024:.1f}GB) with {additional_buffer_mb}MB ({additional_buffer_mb/1024:.1f}GB) additional buffer for operations included"
        )

    except RuntimeError as e:
        if "Virtual devices cannot be modified" in str(e):
            logger.warning("TensorFlow already initialized, using default memory configuration")
        else:
            raise e


def _check_cuda_availability() -> bool:
    """
    Check if CUDA is available on the system.

    Returns:
        True if CUDA is available, False otherwise
    """
    try:
        # Try nvidia-smi command first
        subprocess.run(['nvidia-smi'], capture_output=True, check=True, timeout=10)
        logger.debug("CUDA available: nvidia-smi command successful")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        logger.debug("CUDA not available: nvidia-smi command failed or not found")
        return False


def setup_optimal_backend(backend: str = 'tensorflow', memory_requirement_mb: int = 2000, memory_strategy: str = 'growth', device: str = 'auto') -> str:
    """
    Setup optimal backend configuration based on available resources.

    Args:
        backend: Preferred backend ('tensorflow', 'jax', 'numpy')
        memory_requirement_mb: Minimum GPU memory required in MB
        memory_strategy:    'growth' for memory growth,
                            'occupancy' for fully occupy the specified GPU memory,
                            'limit' for fixed limit
        device: Device to use ('gpu', 'cpu', 'auto').
                'auto' defaults to 'gpu' for tensorflow/jax, 'cpu' for numpy

    Returns:
        The backend that was actually configured
    """

    available_memory_strategy = ['growth', 'occupancy', 'limit']
    available_devices = ['gpu', 'cpu', 'auto']

    assert memory_strategy in available_memory_strategy, f"Invalid memory strategy: {memory_strategy}. Available strategies: {available_memory_strategy}"
    assert device in available_devices, f"Invalid device: {device}. Available devices: {available_devices}"

    # Handle 'auto' device selection
    if device == 'auto':
        if backend in ['tensorflow', 'jax']:
            device = 'gpu'
        else:  # numpy backend
            device = 'cpu'

    # Handle explicit CPU request
    if device == 'cpu':
        os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # Force CPU
        logger.info(f"Using {backend} backend (CPU) - explicitly requested")
        return backend

    # Handle GPU request
    if device == 'gpu':
        if backend == 'numpy':
            logger.warning("NumPy backend requested with GPU device, but NumPy is CPU-only. Using CPU.")
            os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # Force CPU
            return backend

        if backend in ['tensorflow', 'jax']:
            # Check if CUDA is available first
            cuda_available = _check_cuda_availability()
            if not cuda_available:
                logger.warning(f"CUDA not available for {backend}, falling back to CPU")
                os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # Force CPU
                return backend

            # Try to find suitable GPU
            best_gpu_id = find_best_available_gpu(memory_requirement_mb)

            if best_gpu_id is not None:
                # Configure to use the selected GPU
                os.environ['CUDA_VISIBLE_DEVICES'] = str(best_gpu_id)
                logger.info(f"Using {backend} backend with GPU {best_gpu_id}")

                if backend == 'tensorflow':
                    try:
                        if 'tf' not in globals():
                            import tensorflow as tf

                        if gpus := tf.config.experimental.list_physical_devices('GPU'):
                            # Apply memory configuration strategy
                            if memory_strategy == 'growth':
                                _configure_tensorflow_memory_growth(gpus, memory_requirement_mb)
                            elif memory_strategy == 'occupancy':
                                _configure_tensorflow_memory_occupancy(gpus, memory_requirement_mb)
                            elif memory_strategy == 'limit':
                                _configure_tensorflow_memory_limit(gpus, memory_requirement_mb)
                            else:
                                raise ValueError(f"Unknown memory strategy: {memory_strategy}")

                    except ImportError:
                        logger.warning("TensorFlow not available, falling back to numpy")
                        return 'numpy'
                    except Exception as e:
                        logger.error(f"Error configuring TensorFlow: {e}")
                        return 'numpy'

                return backend
            else:
                # No suitable GPU found, fall back to CPU
                logger.warning(f"No suitable GPU found for {backend}, falling back to CPU")
                os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # Force CPU
                return backend

    # Default case (shouldn't reach here with current logic)
    logger.info(f"Using {backend} backend")
    return backend


if __name__ == "__main__":
    preferred_backend = 'tensorflow'

    # Choose your strategy:
    # Option 1: Direct call with strategy parameter
    backend = setup_optimal_backend(backend=preferred_backend, memory_requirement_mb=20000, memory_strategy='growth')  # or 'growth'

    # Option 2: Use convenience functions
    # backend = setup_optimal_backend_by_memory_growth(preferred_backend, 20000)
    # backend = setup_optimal_backend_by_reserving_memory(preferred_backend, 20000)

    logger.info(f"Final backend: {backend}")

    from time import sleep

    sleep(5)
