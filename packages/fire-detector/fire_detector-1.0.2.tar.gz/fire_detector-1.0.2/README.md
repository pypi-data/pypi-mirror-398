# fire_detector —— 火灾/烟雾检测包

基于深度学习的火灾与烟雾检测，提供统一易用的 Python API。

⭐️ **主入口 (Main Entry)**

本文档仅包含项目简介。详细文档请查阅 [docs/](docs/) 目录：

- 📥 [安装与环境 (Install)](docs/INSTALL.md)
- 🚀 [快速开始 (Quick Start)](docs/QUICKSTART.md)
- 📖 [API 文档 (API Reference)](docs/API.md)
- 🧠 [模型说明 (Models)](docs/MODELS.md)
- 🏋️ [训练指南 (Training)](docs/TRAINING.md)
- ❓ [常见问题 (FAQ)](docs/FAQ.md)

---

## 功能特性

- **YOLOv8 目标检测**: 同时检测火焰与烟雾位置 (基于轻量化 YOLOv8)
- **视频追踪**: 基于 YOLOv8 + ByteTrack 的实时目标追踪
- **图像/视频分类**: 基于 ResNet18 的快速二分类筛查
- **开箱即用**: 内置预训练模型权重，安装即用

## 快速预览

```python
from fire_detector import FireDetector

# 初始化 (自动加载内置模型)
detector = FireDetector()

# 1. 检测图片
results = detector.detect_yolo("assets/test.jpg")
print(results)

# 2. 追踪视频
detector.track_video("assets/test_video.mp4", show=True)
```

## 更新日志 (Changelog)

### [1.0.2] - 2025-12-25

- �️ **移除**: 删除了 `full` (yolov8s) 模型，统一使用轻量化 `light` 模型以减小包体积。
- ⚡ **优化**: 默认模型切换为轻量级版本，保持了相近的检测性能。
- �🔄 **变更**: 默认关闭了 YOLO 标签自动交换功能。现在假设模型训练时标签顺序正确 (0:smoke, 1:fire)。
- ✨ **新增**: `detect_yolo` 接口支持 `output_path` 参数，可直接保存检测结果图片。

### [1.0.1] - 2025-12-24

- ✨ **新增**: 集成 YOLOv8 + ByteTrack 视频追踪模块
- ⚡ **优化**: 改进轻量化 YOLO 训练脚本 (FasterNet 模块劫持)
- 🗑️ **移除**: 删除了过时的 CNN+LSTM 及二阶段检测模块
- 🐛 **修复**: 修正了模型类别标签映射问题

---

© 2025 Fire Detector Project.
