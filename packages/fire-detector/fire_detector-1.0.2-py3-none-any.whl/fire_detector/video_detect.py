import os
import cv2
import torch
from torchvision import transforms
from PIL import Image
from .model_loader import load_model
from .path_utils import resolve_model_path


class VideoFireDetector:
    def __init__(self, model_path=None, threshold=0.5):
        resolved = resolve_model_path("fire_resnet18_fp16.pth", model_path)
        if not resolved:
            raise FileNotFoundError(f"模型文件不存在: {model_path or 'fire_resnet18_fp16.pth'}")
        self.model, self.device = load_model(resolved)
        self.threshold = threshold  # 火焰判定置信度阈值

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
        ])

    def predict_frame(self, frame):
        """对单帧图像进行推理"""
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        img = self.transform(image).unsqueeze(0).to(self.device)

        # 检查模型是否为半精度（FP16）
        is_fp16 = next(self.model.parameters()).dtype == torch.float16
        if is_fp16:
            img = img.half()

        with torch.no_grad():
            outputs = self.model(img)
            probabilities = torch.softmax(outputs, dim=1)
            fire_prob = probabilities[0][1].item()

        return fire_prob

    def detect_video(self, video_path):
        """遍历视频所有帧推理火焰概率"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError("无法打开视频文件：" + video_path)

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fire_frames = 0

        print(f"▶ 开始检测：{video_path}")
        print(f"📽 总帧数：{total_frames}")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            fire_prob = self.predict_frame(frame)

            if fire_prob >= self.threshold:
                fire_frames += 1
                print(f"🔥 检测到火焰 | 置信度 = {fire_prob:.4f}")
            else:
                print(f"❌ 无火焰 | 置信度 = {fire_prob:.4f}")

        cap.release()

        fire_rate = fire_frames / total_frames * 100
        print(f"======== 检测结束 ========")
        print(f"🔥 火焰帧数：{fire_frames} / {total_frames} ({fire_rate:.2f}%)")

        return {
            "total_frames": total_frames,
            "fire_frames": fire_frames,
            "fire_rate": fire_rate
        }


if __name__ == "__main__":
    # 默认模型路径无需手动传入
    detector = VideoFireDetector()
    video_path = "test_video.mp4"
    results = detector.detect_video(video_path)
    print(results)
