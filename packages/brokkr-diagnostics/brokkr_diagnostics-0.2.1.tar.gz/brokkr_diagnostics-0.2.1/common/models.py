
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

cudaSuccess = 0
cudaMemcpyHostToDevice = 1
cudaMemcpyDeviceToHost = 2
cudaMemcpyDeviceToDevice = 3


@dataclass
class GPUTest:
    """Result of testing a single GPU"""
    gpu_id: int
    success: bool
    error: Optional[str] = None
    test_size_mb: int = 0


@dataclass
class P2PTest:
    """Result of P2P test between two GPUs"""
    src_gpu: int
    dst_gpu: int
    p2p_supported: bool
    success: bool
    bandwidth_gbps: float = 0.0
    error: Optional[str] = None


@dataclass
class CUDATestResult:
    """Results from CUDA functionality tests"""
    timestamp: datetime
    cuda_available: bool
    num_gpus: int
    individual_gpu_tests: List[GPUTest] = field(default_factory=list)
    p2p_tests: List[P2PTest] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
