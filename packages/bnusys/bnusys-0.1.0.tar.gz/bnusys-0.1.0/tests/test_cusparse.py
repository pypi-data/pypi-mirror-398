import numpy as np
import scipy.sparse as sp
from bnusys.sparse_ops import spmv_csr_cuda

def test_spmv():
    print("=== 测试 cuSPARSE SpMV ===")
    
    # 1. 制造一个稀疏矩阵 (10x10, 密度 20%)
    rows, cols = 10, 10
    density = 0.2
    # 使用 scipy 生成随机 CSR 矩阵作为 Ground Truth
    sparse_matrix = sp.random(rows, cols, density=density, format='csr', dtype=np.float32)
    
    # 提取 CSR 三要素
    row_offsets = sparse_matrix.indptr
    col_indices = sparse_matrix.indices
    values      = sparse_matrix.data
    
    print(f"矩阵形状: {rows}x{cols}, 非零元素: {len(values)}")

    # 2. 制造向量 X
    x_vec = np.random.random(cols).astype(np.float32)

    # 3. CPU 结果 (Scipy 计算)
    y_cpu = sparse_matrix.dot(x_vec)
    print("CPU 计算完成")

    # 4. GPU 结果 (bnusys + cuSPARSE)
    y_gpu = spmv_csr_cuda(row_offsets, col_indices, values, x_vec, shape=(rows, cols))
    print("GPU 计算完成")

    # 5. 验证
    if np.allclose(y_cpu, y_gpu, atol=1e-5):
        print("✅ 成功！CPU 与 cuSPARSE 结果一致！")
        print(f"CPU: {y_cpu[:3]}...")
        print(f"GPU: {y_gpu[:3]}...")
    else:
        print("❌ 失败！结果不一致。")

if __name__ == "__main__":
    test_spmv()