# 文件: marvinbo/__init__.py

# 1. 暴露版本号
__version__ = "0.2.0"  # 既然加了新功能，我们可以假装升级了版本

# 2. 从 basic_math 模块导入基础函数
# 这里的 . 代表“当前目录”
from .math import square, cube

# 3. 尝试导入 GPU 模块
# 使用 try-except 是为了防止用户没有显卡驱动时报错，保证基础功能可用
try:
    from .gpu_ops import vector_add_gpu
    GPU_AVAILABLE = True
except ImportError as e:
    GPU_AVAILABLE = False
    # 如果导入失败，定义一个报错的替身函数
    def vector_add_gpu(*args, **kwargs):
        raise RuntimeError(
            f"无法使用 GPU 功能。请确保已安装 CUDA 环境和 Numba 库。\n详细错误: {e}"
        )

# 4. 定义对外暴露的列表 (可选，但推荐)
# 当用户使用 from marvinbo import * 时，只会导入这些
__all__ = [
    "square", 
    "cube", 
    "vector_add_gpu", 
    "GPU_AVAILABLE"
]