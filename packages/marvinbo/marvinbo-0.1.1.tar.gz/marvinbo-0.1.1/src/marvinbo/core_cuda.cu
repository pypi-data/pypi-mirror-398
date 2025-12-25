#include <cuda_runtime.h>
#include <stdio.h>

// --------------------------------------------------------
// 1. Kernel 函数：这是真正在 GPU 显卡上跑的代码
//    就像是一群微小的工人，每个人只负责计算一个数
// --------------------------------------------------------
__global__ void vector_add_kernel(const float* a, const float* b, float* c, int n) {
    // 计算当前线程的全局 ID
    int idx = blockDim.x * blockIdx.x + threadIdx.x;

    // 防止线程数多于数据量时发生越界
    if (idx < n) {
        c[idx] = a[idx] + b[idx];
    }
}

// --------------------------------------------------------
// 2. Host 函数：这是在 CPU 上跑的“包工头”
//    负责分配内存、搬运数据、指挥 GPU 启动
//    必须加 extern "C" __declspec(dllexport) 才能被 Python 找到
// --------------------------------------------------------
extern "C" {
    __declspec(dllexport) void launch_vector_add(float* h_a, float* h_b, float* h_c, int n) {
        float *d_a, *d_b, *d_c;
        size_t size = n * sizeof(float);

        // A. 在显卡上申请显存 (Malloc)
        cudaMalloc((void**)&d_a, size);
        cudaMalloc((void**)&d_b, size);
        cudaMalloc((void**)&d_c, size);

        // B. 把数据从 CPU 搬运到 GPU (Host -> Device)
        cudaMemcpy(d_a, h_a, size, cudaMemcpyHostToDevice);
        cudaMemcpy(d_b, h_b, size, cudaMemcpyHostToDevice);

        // C. 计算网格大小 (Grid Size)
        int threadsPerBlock = 256;
        int blocksPerGrid = (n + threadsPerBlock - 1) / threadsPerBlock;

        // D. 启动核函数！(Launch Kernel)
        vector_add_kernel<<<blocksPerGrid, threadsPerBlock>>>(d_a, d_b, d_c, n);

        // E. 把计算结果搬回 CPU (Device -> Host)
        cudaMemcpy(h_c, d_c, size, cudaMemcpyDeviceToHost);

        // F. 释放显存，防止内存泄漏
        cudaFree(d_a);
        cudaFree(d_b);
        cudaFree(d_c);
    }
}