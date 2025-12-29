# 文件: bnusys/__init__.py

# 1. 暴露版本号
__version__ = "0.1.0"

# 2. 尝试导入 GPU 模块 (包含向量加法 和 稀疏矩阵乘法)
# 使用 try-except 是为了防止用户没有显卡驱动或缺少 DLL 时报错
try:
    # 导入向量加法 (来自 gpu_ops.py)
    from .gpu_ops import vector_add_gpu
    
    # [新增] 导入稀疏矩阵乘法 (来自 sparse_ops.py)
    from .sparse_ops import spmv_csr_cuda
    
    GPU_AVAILABLE = True

except ImportError as e:
    GPU_AVAILABLE = False
    
    # 定义报错的替身函数，告诉用户缺了什么
    def vector_add_gpu(*args, **kwargs):
        raise RuntimeError(error_msg(e))

    def spmv_csr_cuda(*args, **kwargs):
        raise RuntimeError(error_msg(e))

def error_msg(e):
    return (
        f"无法加载 GPU 模块。\n"
        f"原因: {e}\n"
        f"提示: 请确保已安装 NVIDIA CUDA Toolkit，并且环境变量 PATH 包含 bin 目录。"
    )

# 3. 定义对外暴露的列表
# 当用户使用 from bnusys import * 时，只会导入这些
__all__ = [
    "vector_add_gpu", 
    "spmv_csr_cuda",  # <--- 新增这个
    "GPU_AVAILABLE",
    "__version__"
]