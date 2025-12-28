# fire_detector/YoloDetector.py
import os
import numpy as np
from ultralytics import YOLO
from .path_utils import resolve_model_path

class YoloDetector:
    """
    YOLOv8 火焰/烟雾检测器
    支持两个模型变体：
      - 'light' : light_yolov8_flame.pt (轻量，适合边缘设备)
      - 'full'  : yolov8s_fire_smoke.pt (精度高)
    """
    def __init__(self, model_variant="full", model_path=None, swap_labels=True):
        self.model_variant = model_variant
        default_name = "light_yolov8_flame.pt" if model_variant == "light" else "yolov8s_fire_smoke.pt"
        resolved = resolve_model_path(default_name, model_path)
        if not resolved:
            raise FileNotFoundError(f"模型文件不存在: {model_path or default_name}")
        self.model_path = resolved
        self.model = YOLO(self.model_path)
        
        # 修正类别映射 (Fix class mapping)
        # 如果用户遇到 smoke/fire 标签反转的问题，启用 swap_labels
        if swap_labels and hasattr(self.model, 'names') and len(self.model.names) >= 2:
            print(f"Original YoloDetector model names: {self.model.names}")
            print("Swapping labels in YoloDetector: 0 <-> 1")
            
            new_names = dict(self.model.names)
            name0 = new_names.get(0, 'class0')
            name1 = new_names.get(1, 'class1')
            new_names[0] = name1
            new_names[1] = name0
            
            # 更新模型内部映射
            if hasattr(self.model.model, 'names'):
                self.model.model.names = new_names
            try:
                self.model.names = new_names
            except AttributeError:
                pass
            print(f"New YoloDetector model names: {self.model.names}")

        # 动态获取标签列表，不再硬编码
        if hasattr(self.model, 'names'):
            # 确保按 id 排序
            self.labels = [self.model.names[i] for i in sorted(self.model.names.keys())]
        else:
            self.labels = ["fire", "smoke"] # Fallback


    def detect_image(self, img_path, conf=0.25, iou=0.5):
        """
        对单张图像进行火焰/烟雾检测
        :param img_path: 图片路径
        :param conf: 置信度阈值
        :param iou: NMS 阈值
        :return: list of dict [{'class': 'fire', 'conf': 0.87, 'box':[x1,y1,x2,y2]}, ...]
        """
        if not os.path.exists(img_path):
            raise FileNotFoundError(f"图像文件不存在: {img_path}")
        
        results = self.model(img_path, conf=conf, iou=iou)
        detections = []
        
        if len(results) > 0:
            r = results[0]
            boxes = r.boxes
            for i in range(len(boxes)):
                cls_id = int(boxes.cls[i].item())
                score = float(boxes.conf[i].item())
                xyxy = boxes.xyxy[i].cpu().numpy().tolist()  # [x1, y1, x2, y2]
                label = self.labels[cls_id] if cls_id < len(self.labels) else f"class_{cls_id}"
                detections.append({
                    "class": label,
                    "conf": round(score, 4),
                    "box": xyxy
                })
        return detections

    def detect_batch(self, img_paths, conf=0.25, iou=0.5):
        """
        批量图像检测
        :param img_paths: 图片路径列表
        :return: dict {img_path: detections}
        """
        results_dict = {}
        for path in img_paths:
            results_dict[path] = self.detect_image(path, conf=conf, iou=iou)
        return results_dict
