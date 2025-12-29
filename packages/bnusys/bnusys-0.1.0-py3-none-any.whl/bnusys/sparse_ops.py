import ctypes
import os
import numpy as np


def add_cuda_to_dll_path():
    # 1. 尝试从环境变量获取 CUDA 路径
    cuda_path = os.environ.get('CUDA_PATH')
    
    if cuda_path:
        bin_path = os.path.join(cuda_path, 'bin')
        if os.path.exists(bin_path):
            print(f"DEBUG: 正在添加 CUDA 搜索路径: {bin_path}")
            # Python 3.8+ 必须使用 add_dll_directory
            if hasattr(os, 'add_dll_directory'):
                os.add_dll_directory(bin_path)
            # 为了兼容性，也加到 PATH 里
            os.environ['PATH'] = bin_path + os.pathsep + os.environ['PATH']
    else:
        print("WARNING: 未找到 CUDA_PATH 环境变量，可能会导致 DLL 加载失败。")

# 执行添加路径操作
add_cuda_to_dll_path()

# 1. 加载 DLL
curr_dir = os.path.dirname(os.path.abspath(__file__))
dll_path = os.path.join(curr_dir, "lib_bnusys.dll")

try:
    # Windows 下使用 CDLL 加载
    _lib = ctypes.CDLL(dll_path)
except FileNotFoundError:
    raise RuntimeError(f"未找到库文件: {dll_path}")
except OSError as e:
    # 这里的 e 通常就是 "找不到指定模块"
    raise RuntimeError(
        f"加载库失败: {e}\n"
        f"提示: 请检查是否安装了 CUDA Toolkit，且环境变量 CUDA_PATH 设置正确。\n"
        f"缺失的可能是: cusparse64_xx.dll 或 cudart64_xx.dll"
    )

# 2. 定义函数参数类型
# void run_spmv_csr(int rows, int cols, int nnz, int* offsets, int* cols, float* vals, float* x, float* y)
_lib.run_spmv_csr.argtypes = [
    ctypes.c_int, ctypes.c_int, ctypes.c_int,
    ctypes.POINTER(ctypes.c_int),   # row_offsets
    ctypes.POINTER(ctypes.c_int),   # col_indices
    ctypes.POINTER(ctypes.c_float), # values
    ctypes.POINTER(ctypes.c_float), # x
    ctypes.POINTER(ctypes.c_float)  # y
]
_lib.run_spmv_csr.restype = None

# 3. 封装给用户调用的函数
def spmv_csr_cuda(row_offsets, col_indices, values, x_vec, shape):
    """
    调用 CUDA cuSPARSE 执行稀疏矩阵乘向量
    A (shape) * x = y
    """
    rows, cols = shape
    nnz = len(values)

    # 确保数据类型正确 (C++ 那边极其严格)
    # 索引必须是 int32，数值必须是 float32
    h_offsets = np.ascontiguousarray(row_offsets, dtype=np.int32)
    h_columns = np.ascontiguousarray(col_indices, dtype=np.int32)
    h_values  = np.ascontiguousarray(values, dtype=np.float32)
    h_x       = np.ascontiguousarray(x_vec, dtype=np.float32)
    
    # 准备输出容器
    h_y = np.zeros(rows, dtype=np.float32)

    # 获取指针
    ptr_offsets = h_offsets.ctypes.data_as(ctypes.POINTER(ctypes.c_int))
    ptr_columns = h_columns.ctypes.data_as(ctypes.POINTER(ctypes.c_int))
    ptr_values  = h_values.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    ptr_x       = h_x.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    ptr_y       = h_y.ctypes.data_as(ctypes.POINTER(ctypes.c_float))

    # 调用 C++
    _lib.run_spmv_csr(
        rows, cols, nnz,
        ptr_offsets, ptr_columns, ptr_values,
        ptr_x, ptr_y
    )

    return h_y