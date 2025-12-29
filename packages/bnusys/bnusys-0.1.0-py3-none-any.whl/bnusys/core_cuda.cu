#include <cuda_runtime.h>
#include <cusparse.h>
#include <stdio.h>

// 宏定义用于检查 CUDA 错误
#define CHECK_CUDA(func) { \
    cudaError_t status = (func); \
    if (status != cudaSuccess) { \
        printf("CUDA API failed at line %d with error: %s (%d)\n", \
               __LINE__, cudaGetErrorString(status), status); \
        return; \
    } \
}

// 宏定义用于检查 CUSPARSE 错误
#define CHECK_CUSPARSE(func) { \
    cusparseStatus_t status = (func); \
    if (status != CUSPARSE_STATUS_SUCCESS) { \
        printf("CUSPARSE API failed at line %d with error: %d\n", \
               __LINE__, status); \
        return; \
    } \
}

// Part 2: 向量加法 Kernel

__global__ void vector_add_kernel(const float* a, const float* b, float* c, int n) {
    int idx = blockDim.x * blockIdx.x + threadIdx.x;
    if (idx < n) {
        c[idx] = a[idx] + b[idx];
    }
}

extern "C" {

    // 功能 A: 向量加法接口 (找回这个函数！)
    // ========================================================
    __declspec(dllexport) void launch_vector_add(float* h_a, float* h_b, float* h_c, int n) {
        float *d_a, *d_b, *d_c;
        size_t size = n * sizeof(float);

        cudaMalloc((void**)&d_a, size);
        cudaMalloc((void**)&d_b, size);
        cudaMalloc((void**)&d_c, size);

        cudaMemcpy(d_a, h_a, size, cudaMemcpyHostToDevice);
        cudaMemcpy(d_b, h_b, size, cudaMemcpyHostToDevice);

        int threadsPerBlock = 256;
        int blocksPerGrid = (n + threadsPerBlock - 1) / threadsPerBlock;

        vector_add_kernel<<<blocksPerGrid, threadsPerBlock>>>(d_a, d_b, d_c, n);

        cudaMemcpy(h_c, d_c, size, cudaMemcpyDeviceToHost);

        cudaFree(d_a);
        cudaFree(d_b);
        cudaFree(d_c);
    }


    // 功能 B: cuSPARSE 稀疏矩阵乘法接口 (新功能)
    // ------------------------------------------------------------
    // 函数：cusparse_spmv_csr
    // 功能：计算 y = alpha * A * x + beta * y
    // 输入：
    //   rows: 矩阵行数
    //   cols: 矩阵列数
    //   nnz:  非零元素个数
    //   h_csr_offsets: CSR 行偏移数组 (大小 rows + 1)
    //   h_csr_columns: CSR 列索引数组 (大小 nnz)
    //   h_csr_values:  CSR 数值数组   (大小 nnz)
    //   h_x:           输入向量 x     (大小 cols)
    //   h_y:           输出向量 y     (大小 rows)
    // ------------------------------------------------------------
    __declspec(dllexport) void run_spmv_csr(
        int rows, int cols, int nnz,
        int* h_csr_offsets, int* h_csr_columns, float* h_csr_values,
        float* h_x, float* h_y
    ) {
        // 1. 定义变量
        cusparseHandle_t     handle = NULL;
        cusparseSpMatDescr_t matA;
        cusparseDnVecDescr_t vecX, vecY;
        void* dBuffer    = NULL;
        size_t               bufferSize = 0;
        
        // 并在 GPU 上申请内存
        int   *d_csr_offsets, *d_csr_columns;
        float *d_csr_values, *d_x, *d_y;
        float alpha = 1.0f;
        float beta  = 0.0f;

        // 2. 初始化 cuSPARSE
        CHECK_CUSPARSE(cusparseCreate(&handle));

        // 3. 申请显存 (Device Memory)
        CHECK_CUDA(cudaMalloc((void**)&d_csr_offsets, (rows + 1) * sizeof(int)));
        CHECK_CUDA(cudaMalloc((void**)&d_csr_columns, nnz * sizeof(int)));
        CHECK_CUDA(cudaMalloc((void**)&d_csr_values,  nnz * sizeof(float)));
        CHECK_CUDA(cudaMalloc((void**)&d_x,           cols * sizeof(float)));
        CHECK_CUDA(cudaMalloc((void**)&d_y,           rows * sizeof(float)));

        // 4. 数据搬运 (Host -> Device)
        CHECK_CUDA(cudaMemcpy(d_csr_offsets, h_csr_offsets, (rows + 1) * sizeof(int), cudaMemcpyHostToDevice));
        CHECK_CUDA(cudaMemcpy(d_csr_columns, h_csr_columns, nnz * sizeof(int), cudaMemcpyHostToDevice));
        CHECK_CUDA(cudaMemcpy(d_csr_values,  h_csr_values,  nnz * sizeof(float), cudaMemcpyHostToDevice));
        CHECK_CUDA(cudaMemcpy(d_x,           h_x,           cols * sizeof(float), cudaMemcpyHostToDevice));
        // y 不需要搬运初始值，因为我们设 beta = 0

        // 5. 创建描述符 (Descriptors)
        // 创建稀疏矩阵 A (CSR 格式)
        CHECK_CUSPARSE(cusparseCreateCsr(&matA, rows, cols, nnz,
                                         d_csr_offsets, d_csr_columns, d_csr_values,
                                         CUSPARSE_INDEX_32I, CUSPARSE_INDEX_32I,
                                         CUSPARSE_INDEX_BASE_ZERO, CUDA_R_32F));
        
        // 创建稠密向量 X 和 Y
        CHECK_CUSPARSE(cusparseCreateDnVec(&vecX, cols, d_x, CUDA_R_32F));
        CHECK_CUSPARSE(cusparseCreateDnVec(&vecY, rows, d_y, CUDA_R_32F));

        // 6. 询问 cuSPARSE 需要多大的外部缓存 (Buffer)
        CHECK_CUSPARSE(cusparseSpMV_bufferSize(
                                handle, CUSPARSE_OPERATION_NON_TRANSPOSE,
                                &alpha, matA, vecX, &beta, vecY, CUDA_R_32F,
                                CUSPARSE_SPMV_ALG_DEFAULT, &bufferSize));
        
        CHECK_CUDA(cudaMalloc(&dBuffer, bufferSize));

        // 7. 执行 SpMV 计算 (A * x -> y)
        CHECK_CUSPARSE(cusparseSpMV(handle, CUSPARSE_OPERATION_NON_TRANSPOSE,
                                    &alpha, matA, vecX, &beta, vecY, CUDA_R_32F,
                                    CUSPARSE_SPMV_ALG_DEFAULT, dBuffer));

        // 8. 搬回结果 (Device -> Host)
        CHECK_CUDA(cudaMemcpy(h_y, d_y, rows * sizeof(float), cudaMemcpyDeviceToHost));

        // 9. 资源清理 (切记！)
        CHECK_CUSPARSE(cusparseDestroySpMat(matA));
        CHECK_CUSPARSE(cusparseDestroyDnVec(vecX));
        CHECK_CUSPARSE(cusparseDestroyDnVec(vecY));
        CHECK_CUSPARSE(cusparseDestroy(handle));
        
        CHECK_CUDA(cudaFree(dBuffer));
        CHECK_CUDA(cudaFree(d_csr_offsets));
        CHECK_CUDA(cudaFree(d_csr_columns));
        CHECK_CUDA(cudaFree(d_csr_values));
        CHECK_CUDA(cudaFree(d_x));
        CHECK_CUDA(cudaFree(d_y));
    }
}