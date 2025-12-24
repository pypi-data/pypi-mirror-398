"""
CUDA GPU Functionality Tests
Tests GPU memory allocation, host<->device copies, and multi-GPU P2P communication
"""

import numpy as np
import time
from datetime import datetime

from ..common.cuda_interface import CUDAInterface
from ..common.models import GPUTest, P2PTest, CUDATestResult

class CUDADiagnostics:
    """
    CUDA functionality diagnostics
    Tests GPU memory, host<->device copies, and multi-GPU P2P
    """
    
    def __init__(self):
        self.cuda = None
        try:
            self.cuda = CUDAInterface()
        except Exception:
            pass
    
    def test_single_gpu(self, gpu_id: int, size_mb: int = 100) -> GPUTest:
        """Test basic GPU functionality"""
        size_bytes = size_mb * 1024 * 1024
        data = np.random.rand(size_bytes // 4).astype(np.float32)
        
        gpu_ptr = None
        try:
            self.cuda.set_device(gpu_id)
            gpu_ptr = self.cuda.malloc(size_bytes)
            self.cuda.memcpy_h2d(gpu_ptr, data, size_bytes)
            
            result = np.zeros_like(data)
            self.cuda.memcpy_d2h(result, gpu_ptr, size_bytes)
            
            success = np.allclose(data, result)
            error = None if success else "Data mismatch after copy"
            
            return GPUTest(
                gpu_id=gpu_id,
                success=success,
                error=error,
                test_size_mb=size_mb
            )
            
        except Exception as e:
            return GPUTest(
                gpu_id=gpu_id,
                success=False,
                error=str(e),
                test_size_mb=size_mb
            )
        finally:
            if gpu_ptr is not None:
                try:
                    self.cuda.free(gpu_ptr)
                except:
                    pass
    
    def test_p2p_pair(self, src_gpu: int, dst_gpu: int, size_mb: int = 100) -> P2PTest:
        """Test P2P between two GPUs with bandwidth measurement"""
        size_bytes = size_mb * 1024 * 1024
        data = np.random.rand(size_bytes // 4).astype(np.float32)
        
        gpu_ptr_src = None
        gpu_ptr_dst = None
        
        try:
            # Check P2P support
            p2p_supported = self.cuda.can_access_peer(src_gpu, dst_gpu)
            
            # Allocate on source GPU
            self.cuda.set_device(src_gpu)
            gpu_ptr_src = self.cuda.malloc(size_bytes)
            self.cuda.memcpy_h2d(gpu_ptr_src, data, size_bytes)
            
            # Allocate on destination GPU
            self.cuda.set_device(dst_gpu)
            gpu_ptr_dst = self.cuda.malloc(size_bytes)
            
            # Enable P2P if supported
            if p2p_supported:
                self.cuda.set_device(src_gpu)
                self.cuda.enable_peer_access(dst_gpu)
                self.cuda.set_device(dst_gpu)
                self.cuda.enable_peer_access(src_gpu)
            
            # Timed P2P copy
            self.cuda.set_device(src_gpu)
            start = time.time()
            self.cuda.memcpy_d2d(gpu_ptr_dst, gpu_ptr_src, size_bytes)
            self.cuda.device_synchronize()
            elapsed = time.time() - start
            
            # Verify data
            self.cuda.set_device(dst_gpu)
            verify = np.zeros_like(data)
            self.cuda.memcpy_d2h(verify, gpu_ptr_dst, size_bytes)
            
            if not np.allclose(data, verify):
                return P2PTest(
                    src_gpu=src_gpu,
                    dst_gpu=dst_gpu,
                    p2p_supported=p2p_supported,
                    success=False,
                    error="Data mismatch after P2P copy"
                )
            
            bandwidth_gbps = (size_bytes / 1e9) / elapsed
            
            return P2PTest(
                src_gpu=src_gpu,
                dst_gpu=dst_gpu,
                p2p_supported=p2p_supported,
                success=True,
                bandwidth_gbps=bandwidth_gbps
            )
            
        except Exception as e:
            return P2PTest(
                src_gpu=src_gpu,
                dst_gpu=dst_gpu,
                p2p_supported=False,
                success=False,
                error=str(e)
            )
        finally:
            if gpu_ptr_src is not None:
                try:
                    self.cuda.set_device(src_gpu)
                    self.cuda.free(gpu_ptr_src)
                except:
                    pass
            if gpu_ptr_dst is not None:
                try:
                    self.cuda.set_device(dst_gpu)
                    self.cuda.free(gpu_ptr_dst)
                except:
                    pass
    
    def run_all_tests(self) -> CUDATestResult:
        """Run comprehensive CUDA functionality tests"""
        result = CUDATestResult(
            timestamp=datetime.now(),
            cuda_available=self.cuda is not None,
            num_gpus=0
        )
        
        if not self.cuda:
            result.errors.append("CUDA not available - libcudart.so not found")
            return result
        
        try:
            result.num_gpus = self.cuda.get_device_count()
        except Exception as e:
            result.errors.append(f"Failed to get GPU count: {e}")
            return result
        
        if result.num_gpus == 0:
            result.warnings.append("No CUDA GPUs detected")
            return result
        
        # Test individual GPUs
        for gpu_id in range(result.num_gpus):
            gpu_test = self.test_single_gpu(gpu_id)
            result.individual_gpu_tests.append(gpu_test)
            if not gpu_test.success:
                result.errors.append(f"GPU {gpu_id}: {gpu_test.error}")
        
        # Test P2P between all GPU pairs
        for src in range(result.num_gpus):
            for dst in range(src + 1, result.num_gpus):
                p2p_test = self.test_p2p_pair(src, dst)
                result.p2p_tests.append(p2p_test)
                
                if not p2p_test.success:
                    result.errors.append(
                        f"P2P GPU {src} -> GPU {dst}: {p2p_test.error}"
                    )
                elif not p2p_test.p2p_supported:
                    result.warnings.append(
                        f"P2P not supported: GPU {src} -> GPU {dst}"
                    )
        
        # Check for slow P2P links
        if result.p2p_tests:
            successful_p2p = [t for t in result.p2p_tests if t.success]
            if successful_p2p:
                bandwidths = [t.bandwidth_gbps for t in successful_p2p]
                avg_bw = sum(bandwidths) / len(bandwidths)
                
                for test in successful_p2p:
                    if test.bandwidth_gbps < avg_bw * 0.5:
                        result.warnings.append(
                            f"Slow P2P link GPU {test.src_gpu} -> GPU {test.dst_gpu}: "
                            f"{test.bandwidth_gbps:.1f} GB/s (avg: {avg_bw:.1f} GB/s)"
                        )
        
        return result
    
    def format_report(self, result: CUDATestResult) -> str:
        """Format results as human-readable report"""
        lines = ["=" * 80]
        lines.append("CUDA Functionality Tests")
        lines.append(f"Timestamp: {result.timestamp}")
        lines.append("=" * 80)
        lines.append("")
        
        if not result.cuda_available:
            lines.append("ERROR: CUDA not available")
            return "\n".join(lines)
        
        lines.append(f"CUDA GPUs detected: {result.num_gpus}")
        lines.append("")
        
        # Errors
        if result.errors:
            lines.append("ERRORS:")
            for error in result.errors:
                lines.append(f"  - {error}")
            lines.append("")
        
        # Warnings
        if result.warnings:
            lines.append("WARNINGS:")
            for warning in result.warnings:
                lines.append(f"  - {warning}")
            lines.append("")
        
        # Individual GPU tests
        if result.individual_gpu_tests:
            lines.append("Individual GPU Tests:")
            for test in result.individual_gpu_tests:
                status = "✓" if test.success else "✗"
                error_msg = f" ({test.error})" if test.error else ""
                lines.append(f"  {status} GPU {test.gpu_id}{error_msg}")
            lines.append("")
        
        # P2P tests summary
        if result.p2p_tests:
            successful = sum(1 for t in result.p2p_tests if t.success)
            total = len(result.p2p_tests)
            p2p_supported = sum(1 for t in result.p2p_tests if t.p2p_supported)
            
            lines.append(f"P2P Tests: {successful}/{total} successful")
            lines.append(f"P2P Support: {p2p_supported}/{total} pairs")
            
            # Show bandwidth stats
            successful_tests = [t for t in result.p2p_tests if t.success]
            if successful_tests:
                bandwidths = [t.bandwidth_gbps for t in successful_tests]
                lines.append(f"P2P Bandwidth: {min(bandwidths):.1f} - {max(bandwidths):.1f} GB/s "
                           f"(avg: {sum(bandwidths)/len(bandwidths):.1f} GB/s)")
            lines.append("")
            
            # Detailed P2P results
            lines.append("P2P Details:")
            for test in result.p2p_tests:
                status = "✓" if test.success else "✗"
                support = "[P2P]" if test.p2p_supported else "[NO-P2P]"
                if test.success:
                    info = f"{test.bandwidth_gbps:.1f} GB/s"
                else:
                    info = test.error or "failed"
                lines.append(f"  {status} GPU {test.src_gpu} -> GPU {test.dst_gpu} {support}: {info}")
        
        return "\n".join(lines)


async def run_cuda_diagnostics():
    """Example usage"""
    from termcolor import cprint
    diagnostics = CUDADiagnostics()
    result = diagnostics.run_all_tests()
    cprint(diagnostics.format_report(result), "white")
    return result


if __name__ == "__main__":
    run_cuda_diagnostics()