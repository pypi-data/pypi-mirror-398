import time
import numpy as np
import marvinbo  # 导入你的库

def run_test():
    # 1. 生成大规模数据
    # 如果数据量太小（比如只有几千个），GPU 传输数据的耗时会超过计算耗时，反而比 CPU 慢
    # 这里我们用 1000 万个数据
    N = 10_000_000
    print(f"正在生成 {N} 个随机浮点数...")
    
    # 使用 numpy 生成随机数
    a = np.random.random(N).astype(np.float32)
    b = np.random.random(N).astype(np.float32)

    print("-" * 30)
    
    # 2. 测试 CPU (Numpy) 速度
    print("正在运行 CPU 计算 (Numpy)...")
    start_cpu = time.time()
    res_cpu = a + b
    end_cpu = time.time()
    cpu_time = end_cpu - start_cpu
    print(f"CPU 耗时: {cpu_time:.5f} 秒")

    print("-" * 30)

    # 3. 测试 GPU (marvin0624) 速度
    # 第一次运行通常包含编译时间 (JIT Compile)，可能会慢，所以我们往往跑两次
    print("正在预热 GPU (首次运行包含编译时间)...")
    marvinbo.vector_add_gpu(a[:100].copy(), b[:100].copy()) # 小数据预热

    print("正在运行 GPU 计算 (marvinbo)...")
    start_gpu = time.time()
    res_gpu = marvinbo.vector_add_gpu(a, b)
    end_gpu = time.time()
    gpu_time = end_gpu - start_gpu
    print(f"GPU 耗时: {gpu_time:.5f} 秒")
    
    print("-" * 30)

    # 4. 验证结果正确性
    # 浮点数计算会有微小误差，使用 allclose 判断是否足够接近
    is_correct = np.allclose(res_cpu, res_gpu, atol=1e-5)
    if is_correct:
        print(f"✅ 结果验证通过！加速比: {cpu_time / gpu_time:.2f}x")
    else:
        print("❌ 结果验证失败！")

if __name__ == "__main__":
    run_test()

print('测试结束')