import os
from datetime import datetime
import cuda.bindings.driver as cuda
import cuda.bindings.runtime as cudart


# 由相对路径补全完整文件路径：文件夹由本py文件决定。
def file_path_complete(filename):
    r'''
    Get the absolute path for the file inside this repo.
    '''
    dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(dir, filename)


def datetime_string():
    '''
    按照“月日年_时分秒”格式化当前时间
    '''
    ct = datetime.now()
    fmt_time = ct.strftime('%m%d%Y_%H%M%S')

    return fmt_time

# 读取CUDA核心数


def get_cuda_core_count():
    # Get device
    cuda.cuInit(0)
    err, device = cuda.cuDeviceGet(0)
    if err != cuda.CUresult.CUDA_SUCCESS:
        raise RuntimeError("Failed to get CUDA device.")

    # Retrieve SM count

    err, sm_count = cuda.cuDeviceGetAttribute(
        cuda.CUdevice_attribute.CU_DEVICE_ATTRIBUTE_MULTIPROCESSOR_COUNT, device)
    if err != cuda.CUresult.CUDA_SUCCESS:
        raise RuntimeError("Failed to get SM count.")

    # Retrieve Compute Capability Major version
    err, major = cuda.cuDeviceGetAttribute(
        cuda.CUdevice_attribute.CU_DEVICE_ATTRIBUTE_COMPUTE_CAPABILITY_MAJOR, device)
    if err != cuda.CUresult.CUDA_SUCCESS:
        raise RuntimeError("Failed to get Compute Capability.")

    err, minor = cuda.cuDeviceGetAttribute(
        cuda.CUdevice_attribute.CU_DEVICE_ATTRIBUTE_COMPUTE_CAPABILITY_MINOR, device)
    if err != cuda.CUresult.CUDA_SUCCESS:
        raise RuntimeError("Failed to get Compute Capability.")

    # CUDA cores per SM lookup table
    cores_per_sm_dict = {
        2: 32,  # Fermi
        3: 192,  # Kepler
        5: 128,  # Maxwell
        6: 64,  # Pascal
        7: 64,  # Volta & Turing (7.0) | 128 for Turing (7.5)
        8: 64,  # Ampere (8.0) | 128 for 8.6+
        9: 128,  # Hopper & Ada
        12: 128  # Blackwell
    }

    if major != 8:
        cores_per_sm = cores_per_sm_dict.get(
            major, 64)  # Default to 64 if unknown
    elif minor < 6:
        cores_per_sm = 64
    else:
        cores_per_sm = 128

    total_cores = sm_count * cores_per_sm

    return total_cores, sm_count, major, minor
