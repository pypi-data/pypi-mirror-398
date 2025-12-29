from setuptools import setup, find_packages

with open("README.rst", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    # 基本信息
    name="emeralx",
    version="0.9.1",
    author="modaochangyang",
    author_email="1602422136@qq.com",
    description="A library for making simple 2D games",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    
    packages=find_packages(),
    
    # Python版本要求
    python_requires=">=3.7",
    
    # 依赖
    install_requires=[
        'pygame>=2.5.0',          # 用于图形、声音、事件处理
        'pywin32>=306',           # Windows API调用（GetMonitorInfo等）
        'numpy>=1.24.0',          # 图像处理（numpy数组操作）
        'Pillow>=10.0.0',         # GIF动画处理（Image.open等）
        'pygame-freetype>=1.0.0', # 字体渲染（部分系统可能需要）
    ],
    
    # 分类器
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    
    # 许可证
    license="MIT",
    
    # 关键词
    keywords="emeralx",
    
    # 包含数据文件
    include_package_data=True,
    package_data={
        "emeralx": ["resources/*.png","resources/*.ttf"],
    }
)