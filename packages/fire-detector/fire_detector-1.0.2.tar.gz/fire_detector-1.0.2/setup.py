from setuptools import setup, find_packages

setup(
    name="fire_detector",
    version="1.0.2",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "fire_detector": [
            "models/*.pth",
            "models/*.pt",
        ],
    },
    install_requires=[
        "torch",
        "torchvision",
        "Pillow",
        "ultralytics",  # 添加 ultralytics 作为依赖，用于 YOLOv8
    ],
    author="WS",
    description="Deep Learning Fire Detection ",
    python_requires=">=3.8",
)
