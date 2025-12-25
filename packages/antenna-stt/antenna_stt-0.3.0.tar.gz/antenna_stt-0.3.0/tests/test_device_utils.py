"""Tests for device utility functions."""

import pytest
import antenna


class TestDeviceAvailability:
    """Test device availability check functions."""

    def test_is_cuda_available_returns_bool(self):
        """is_cuda_available should return a boolean."""
        result = antenna.is_cuda_available()
        assert isinstance(result, bool)

    def test_cuda_device_count_returns_int(self):
        """cuda_device_count should return a non-negative integer."""
        result = antenna.cuda_device_count()
        assert isinstance(result, int)
        assert result >= 0

    def test_is_metal_available_returns_bool(self):
        """is_metal_available should return a boolean."""
        result = antenna.is_metal_available()
        assert isinstance(result, bool)

    def test_metal_device_count_returns_int(self):
        """metal_device_count should return a non-negative integer."""
        result = antenna.metal_device_count()
        assert isinstance(result, int)
        assert result >= 0

    def test_is_gpu_available_returns_bool(self):
        """is_gpu_available should return a boolean."""
        result = antenna.is_gpu_available()
        assert isinstance(result, bool)

    def test_is_gpu_available_matches_cuda_or_metal(self):
        """is_gpu_available should be True if either CUDA or Metal is available."""
        gpu = antenna.is_gpu_available()
        cuda = antenna.is_cuda_available()
        metal = antenna.is_metal_available()
        assert gpu == (cuda or metal)


class TestOnnxBackendAvailability:
    """Test ONNX backend availability check functions."""

    def test_is_onnx_available_returns_bool(self):
        """is_onnx_available should return a boolean."""
        result = antenna.is_onnx_available()
        assert isinstance(result, bool)

    def test_is_onnx_cuda_available_returns_bool(self):
        """is_onnx_cuda_available should return a boolean."""
        result = antenna.is_onnx_cuda_available()
        assert isinstance(result, bool)

    def test_is_onnx_tensorrt_available_returns_bool(self):
        """is_onnx_tensorrt_available should return a boolean."""
        result = antenna.is_onnx_tensorrt_available()
        assert isinstance(result, bool)

    def test_tensorrt_implies_cuda(self):
        """TensorRT availability implies ONNX CUDA availability."""
        tensorrt = antenna.is_onnx_tensorrt_available()
        cuda = antenna.is_onnx_cuda_available()
        if tensorrt:
            assert cuda, "TensorRT available implies CUDA should be available"


class TestDeviceConsistency:
    """Test device availability consistency."""

    def test_cuda_count_zero_when_unavailable(self):
        """If CUDA is not available, device count should be 0."""
        if not antenna.is_cuda_available():
            assert antenna.cuda_device_count() == 0

    def test_metal_count_zero_when_unavailable(self):
        """If Metal is not available, device count should be 0."""
        if not antenna.is_metal_available():
            assert antenna.metal_device_count() == 0

    def test_cuda_count_positive_when_available(self):
        """If CUDA is available, device count should be positive."""
        if antenna.is_cuda_available():
            assert antenna.cuda_device_count() > 0

    def test_metal_count_positive_when_available(self):
        """If Metal is available, device count should be positive."""
        if antenna.is_metal_available():
            assert antenna.metal_device_count() > 0


class TestExportsPresent:
    """Test that all device functions are properly exported."""

    @pytest.mark.parametrize("func_name", [
        "is_cuda_available",
        "cuda_device_count",
        "is_metal_available",
        "metal_device_count",
        "is_gpu_available",
        "is_onnx_available",
        "is_onnx_cuda_available",
        "is_onnx_tensorrt_available",
    ])
    def test_function_exported(self, func_name):
        """All device utility functions should be exported."""
        assert hasattr(antenna, func_name)
        func = getattr(antenna, func_name)
        assert callable(func)

    @pytest.mark.parametrize("func_name", [
        "is_cuda_available",
        "cuda_device_count",
        "is_metal_available",
        "metal_device_count",
        "is_gpu_available",
        "is_onnx_available",
        "is_onnx_cuda_available",
        "is_onnx_tensorrt_available",
    ])
    def test_function_in_all(self, func_name):
        """All device utility functions should be in __all__."""
        assert func_name in antenna.__all__
