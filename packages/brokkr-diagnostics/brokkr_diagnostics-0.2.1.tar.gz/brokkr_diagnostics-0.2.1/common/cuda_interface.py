import ctypes
from .models import *




class CUDAInterface:
    """CUDA runtime interface via ctypes"""
    
    def __init__(self):
        try:
            self.cuda = ctypes.CDLL("libcudart.so")
        except OSError:
            raise RuntimeError("libcudart.so not found - CUDA not available")
        
    def check_error(self, result, operation="CUDA operation"):
        if result != cudaSuccess:
            raise RuntimeError(f"{operation} failed with error code {result}")
    
    def get_device_count(self):
        """Get number of GPUs"""
        count = ctypes.c_int()
        result = self.cuda.cudaGetDeviceCount(ctypes.byref(count))
        self.check_error(result, "cudaGetDeviceCount")
        return count.value
    
    def set_device(self, device_id):
        """Set active GPU"""
        result = self.cuda.cudaSetDevice(device_id)
        self.check_error(result, f"cudaSetDevice({device_id})")
    
    def malloc(self, size_bytes):
        """Allocate GPU memory"""
        ptr = ctypes.c_void_p()
        result = self.cuda.cudaMalloc(ctypes.byref(ptr), size_bytes)
        self.check_error(result, f"cudaMalloc({size_bytes} bytes)")
        return ptr.value
    
    def free(self, gpu_ptr):
        """Free GPU memory"""
        result = self.cuda.cudaFree(ctypes.c_void_p(gpu_ptr))
        self.check_error(result, "cudaFree")
    
    def memcpy_h2d(self, dst_gpu, src_host, size_bytes):
        """Copy host to device"""
        result = self.cuda.cudaMemcpy(
            ctypes.c_void_p(dst_gpu),
            src_host.ctypes.data_as(ctypes.c_void_p),
            size_bytes,
            cudaMemcpyHostToDevice
        )
        self.check_error(result, "cudaMemcpy H2D")
    
    def memcpy_d2h(self, dst_host, src_gpu, size_bytes):
        """Copy device to host"""
        result = self.cuda.cudaMemcpy(
            dst_host.ctypes.data_as(ctypes.c_void_p),
            ctypes.c_void_p(src_gpu),
            size_bytes,
            cudaMemcpyDeviceToHost
        )
        self.check_error(result, "cudaMemcpy D2H")
    
    def memcpy_d2d(self, dst_gpu, src_gpu, size_bytes):
        """Copy device to device (peer copy)"""
        result = self.cuda.cudaMemcpy(
            ctypes.c_void_p(dst_gpu),
            ctypes.c_void_p(src_gpu),
            size_bytes,
            cudaMemcpyDeviceToDevice
        )
        self.check_error(result, "cudaMemcpy D2D")
    
    def enable_peer_access(self, peer_device):
        """Enable P2P access to another GPU"""
        result = self.cuda.cudaDeviceEnablePeerAccess(peer_device, 0)
        if result != cudaSuccess and result != 4:  # 4 = already enabled
            self.check_error(result, f"cudaDeviceEnablePeerAccess({peer_device})")
    
    def can_access_peer(self, device, peer_device):
        """Check if P2P is possible"""
        can_access = ctypes.c_int()
        result = self.cuda.cudaDeviceCanAccessPeer(
            ctypes.byref(can_access),
            device,
            peer_device
        )
        self.check_error(result, "cudaDeviceCanAccessPeer")
        return can_access.value == 1
    
    def device_synchronize(self):
        """Wait for GPU to finish"""
        result = self.cuda.cudaDeviceSynchronize()
        self.check_error(result, "cudaDeviceSynchronize")

