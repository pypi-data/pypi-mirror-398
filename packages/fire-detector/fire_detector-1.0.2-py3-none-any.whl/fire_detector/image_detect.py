import torch
from PIL import Image
from torchvision import transforms
from .model_loader import load_model
import os
import torch.nn.functional as F
from .path_utils import resolve_model_path

class ImageDetector:
    def __init__(self, model_path=None):
        resolved = resolve_model_path("fire_resnet18_fp16.pth", model_path)
        if not resolved:
            raise FileNotFoundError(f"模型文件不存在: {model_path or 'fire_resnet18_fp16.pth'}")
        self.model, self.device = load_model(resolved)

        # 与训练一致
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
        ])

        # 类别名称（按训练集编码顺序）
        self.labels = ["fire ", "no fire"]

    def detect_image(self, img_path):
        image = Image.open(img_path).convert("RGB")
        img = self.transform(image).unsqueeze(0).to(self.device)
        if next(self.model.parameters()).dtype == torch.float16:
            img = img.half()

        with torch.no_grad():
            outputs = self.model(img)
            probs = F.softmax(outputs, dim=1)
            conf, pred = torch.max(probs, 1)

        label = self.labels[pred.item()]
        confidence = round(conf.item(), 4)

        return label, confidence
