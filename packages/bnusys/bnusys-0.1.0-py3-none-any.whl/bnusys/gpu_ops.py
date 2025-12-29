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


# 1. 定位 DLL 文件的路径
#    __file__ 表示当前 py 文件的路径，我们在同级目录下找 .dll
curr_dir = os.path.dirname(os.path.abspath(__file__))
dll_path = os.path.join(curr_dir, "lib_bnusys.dll")

# 2. 加载 DLL
try:
    # Windows 下使用 CDLL 加载
    _lib = ctypes.CDLL(dll_path)
except FileNotFoundError:
    raise RuntimeError(f"未找到 CUDA 库文件: {dll_path}。请先运行 nvcc 编译 core_cuda.cu！")
except OSError as e:
    raise RuntimeError(f"加载 CUDA 库失败，可能是缺少依赖 (如 cudart.dll)。错误: {e}")

# 3. 配置函数的参数类型 (必须与 C++ 代码严格对应)
#    C++: void launch_vector_add(float* a, float* b, float* c, int n)
_lib.launch_vector_add.argtypes = [
    ctypes.POINTER(ctypes.c_float), # float*
    ctypes.POINTER(ctypes.c_float), # float*
    ctypes.POINTER(ctypes.c_float), # float*
    ctypes.c_int                    # int
]
_lib.launch_vector_add.restype = None  # void 返回空

# 4. 封装成 Python 友好的函数
def vector_add_gpu(a_list, b_list):
    """
    使用 C++ 原生 CUDA 实现的向量加法
    """
    # 强制转换为 float32 类型的 numpy 数组 (因为 C++ 里是 float)
    a = np.array(a_list, dtype=np.float32)
    b = np.array(b_list, dtype=np.float32)
    
    if a.size != b.size:
        raise ValueError("输入数组大小必须一致")
    
    n = a.size
    # 准备一个全 0 的数组来接收结果
    c = np.zeros(n, dtype=np.float32)

    # 获取 numpy 数组的底层内存指针
    a_ptr = a.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    b_ptr = b.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    c_ptr = c.ctypes.data_as(ctypes.POINTER(ctypes.c_float))

    # 调用 C++ 函数
    _lib.launch_vector_add(a_ptr, b_ptr, c_ptr, n)

    return c