"""
提供检测方式的统一入口：
1️⃣ detect_image(img_path): 静态图像检测 (ResNet18)
2️⃣ detect_video(video_path): 简单视频检测 (逐帧)
3️⃣ detect_yolo(img_path): YOLO 目标检测 (火焰/烟雾检测)
4️⃣ track_video(video_path): YOLO 视频追踪 (ByteTrack)
"""

from .image_detect import ImageDetector 
from .video_detect import VideoFireDetector
from .YoloDetector import YoloDetector
from .yolo_track import YoloVideoTracker


class FireDetector:
    def __init__(self,
                 static_model_path=None,
                 threshold=0.5,
                 yolo_model_variant="full",
                 yolo_model_path=None):
        """
        🔹统一管理所有模型与接口
        
        参数:
            threshold: 检测阈值
            yolo_model_variant: YOLO 模型变体 ('light' 或 'full')
            yolo_model_path: 自定义 YOLO 模型路径 (可选)
        """
        # 静态检测器 (ResNet18)
        self.static_detector = ImageDetector(static_model_path)

        # 简单视频检测器（逐帧）
        self.video_detector = VideoFireDetector(static_model_path, threshold)

        # YOLO 目标检测器
        self.yolo_detector = YoloDetector(
            model_variant=yolo_model_variant,
            model_path=yolo_model_path
        )

        # YOLO 视频追踪器
        self.tracker = YoloVideoTracker(
            model_path=yolo_model_path
        )

    # ==================================================
    # 1️⃣ 静态图像检测 (ResNet18)
    # ==================================================
    def detect_image(self, img_path):
        """
        输入一张图片 → 返回火焰/无火焰 + 置信度 (ResNet18)
        """
        return self.static_detector.detect_image(img_path)

    # ==================================================
    # 2️⃣ 逐帧视频检测
    # ==================================================
    def detect_video(self, video_path):
        """
        输入视频 → 遍历所有帧 → 输出火焰统计信息
        """
        return self.video_detector.detect_video(video_path)

    # ==================================================
    # 3️⃣ YOLO 目标检测 (火焰/烟雾检测)
    # ==================================================
    def detect_yolo(self, img_path, conf=0.25, iou=0.5):
        """
        YOLOv8 火焰/烟雾目标检测
        返回检测框、类别和置信度
        
        参数:
            img_path: 图片路径
            conf: 置信度阈值 (默认 0.25)
            iou: NMS 阈值 (默认 0.5)
            
        返回:
            list of dict: [{'class': 'fire', 'conf': 0.87, 'box':[x1,y1,x2,y2]}, ...]
        """
        return self.yolo_detector.detect_image(img_path, conf=conf, iou=iou)

    # ==================================================
    # 4️⃣ YOLO 视频追踪 (ByteTrack)
    # ==================================================
    def track_video(self, video_path, output_path=None, conf=0.25, iou=0.5, show=True):
        """
        使用 YOLOv8 + ByteTrack 追踪视频中的火焰和烟雾
        
        参数:
            video_path: 输入视频路径
            output_path: 输出视频路径 (可选)
            conf: 置信度阈值
            iou: NMS 阈值
            show: 是否实时显示
        """
        return self.tracker.track_video(video_path, output_path, conf, iou, show)

    def detect_yolo_batch(self, img_paths, conf=0.25, iou=0.5):
        """
        批量 YOLO 检测
        
        参数:
            img_paths: 图片路径列表
            conf: 置信度阈值
            iou: NMS 阈值
            
        返回:
            dict: {img_path: detections}
        """
        return self.yolo_detector.detect_batch(img_paths, conf=conf, iou=iou)

    def get_yolo_model_info(self):
        """
        获取 YOLO 模型信息
        """
        return {
            "model_variant": self.yolo_detector.model_variant if hasattr(self.yolo_detector, 'model_variant') else "full",
            "labels": self.yolo_detector.labels,
            "model_path": self.yolo_detector.model_path if hasattr(self.yolo_detector, 'model_path') else "default"
        }


__all__ = ["FireDetector", "YoloDetector"]