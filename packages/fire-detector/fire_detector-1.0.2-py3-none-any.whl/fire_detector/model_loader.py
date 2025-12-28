import torch
import torch.nn as nn
from torchvision import models
import os

def load_model(model_path):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # 先读取权重判断精度
    state = torch.load(model_path, map_location="cpu")
    any_tensor = None
    for v in state.values():
        if isinstance(v, torch.Tensor):
            any_tensor = v
            break
    is_fp16 = (any_tensor is not None and any_tensor.dtype == torch.float16) or (
        os.path.basename(model_path).endswith("_fp16.pth")
    )

    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    model.fc = nn.Linear(model.fc.in_features, 2)

    if is_fp16:
        model = model.half()

    model.load_state_dict(state)
    model = model.to(device)

    # CPU 上半精度不稳定，推理统一转回 float
    if device.type == "cpu":
        model = model.float()

    model.eval()
    return model, device
