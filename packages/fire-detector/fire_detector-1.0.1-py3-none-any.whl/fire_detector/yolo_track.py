import os
import cv2
import sys
from ultralytics import YOLO

# 添加项目根目录到 sys.path 以便导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

from fire_detector.path_utils import resolve_model_path

class YoloVideoTracker:
    """
    使用 YOLOv8 + ByteTrack 进行视频火焰/烟雾追踪
    """
    def __init__(self, model_path=None, swap_labels=True):
        # 默认使用精度较高的 yolov8s_fire_smoke.pt
        default_model = "yolov8s_fire_smoke.pt"
        
        # 尝试解析模型路径
        self.model_path = resolve_model_path(default_model, model_path)
        
        if not self.model_path:
            # 如果找不到特定模型，尝试找通用的 yolov8s.pt
            print(f"Warning: Could not find {default_model}, trying generic yolov8s.pt")
            self.model_path = resolve_model_path("yolov8s.pt", None)
            
        if not self.model_path:
            raise FileNotFoundError(f"无法找到模型文件: {model_path or default_model}")
            
        print(f"Loading model from: {self.model_path}")
        self.model = YOLO(self.model_path)
        
        # 修正类别映射 (Fix class mapping)
        if hasattr(self.model, 'names') and len(self.model.names) >= 2:
            print(f"Original model names: {self.model.names}")
            
            # 如果用户指定了 swap_labels，或者检测到潜在问题
            # (之前的自动检测可能失效，因为元数据可能也是 0:fire, 1:smoke，但模型行为反了)
            if swap_labels:
                print("Force swapping labels: 0 <-> 1")
                new_names = dict(self.model.names)
                # 交换 0 和 1 的标签
                name0 = new_names.get(0, 'class0')
                name1 = new_names.get(1, 'class1')
                new_names[0] = name1
                new_names[1] = name0
                
                # 应用更改
                if hasattr(self.model.model, 'names'):
                    self.model.model.names = new_names
                
                # 尝试更新 wrapper 的 names (如果有 setter)
                try:
                    self.model.names = new_names
                except AttributeError:
                    print("Warning: Cannot set model.names directly (read-only property), relying on model.model.names")
                
                print(f"New model names (internal): {self.model.model.names}")


        
    def track_video(self, video_path, output_path=None, conf=0.25, iou=0.5, show=True):
        """
        追踪视频中的火焰和烟雾
        
        Args:
            video_path: 输入视频路径
            output_path: 输出视频路径 (可选，如果不填则自动生成)
            conf: 置信度阈值
            iou: NMS 阈值
            show: 是否实时显示
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
            
        print(f"Start tracking video: {video_path}")
        print(f"Using tracker: ByteTrack")
        
        # 使用 ultralytics 内置的 track 方法
        # tracker="bytetrack.yaml" 是默认支持的配置
        results = self.model.track(
            source=video_path,
            conf=conf,
            iou=iou,
            tracker="bytetrack.yaml",
            show=show,
            save=True,
            project="runs/track1",
            name="fire_smoke_tracking",
            exist_ok=True,
            persist=True # 保持轨迹ID
        )
        
        print("\nTracking completed.")
        # 获取保存的路径
        if hasattr(results[0], 'save_dir'):
             save_dir = results[0].save_dir
             print(f"Results saved to: {save_dir}")
             
             # 尝试查找生成的 AVI 文件并转换为 MP4
             for file in os.listdir(save_dir):
                 if file.endswith(".avi"):
                     avi_path = os.path.join(save_dir, file)
                     mp4_path = os.path.splitext(avi_path)[0] + ".mp4"
                     self.convert_avi_to_mp4(avi_path, mp4_path)
                     print(f"Converted to MP4: {mp4_path}")

    def convert_avi_to_mp4(self, input_path, output_path):
        """
        使用 OpenCV 将 AVI 转换为 MP4 (H.264)
        """
        try:
            cap = cv2.VideoCapture(input_path)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            # 使用 mp4v 或 avc1 编码
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            print(f"Converting {os.path.basename(input_path)} to MP4...")
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                out.write(frame)
                
            cap.release()
            out.release()
            
        except Exception as e:
            print(f"Failed to convert video: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="YOLOv8 Video Tracking with ByteTrack")
    parser.add_argument("--video", type=str, required=True, help="Path to input video")
    parser.add_argument("--model", type=str, default=None, help="Path to model file (optional)")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument("--iou", type=float, default=0.5, help="IOU threshold")
    parser.add_argument("--no-show", action="store_true", help="Don't show video window")
    parser.add_argument("--no-swap", action="store_true", help="Disable label swapping (use original model labels)")
    
    args = parser.parse_args()
    
    try:
        tracker = YoloVideoTracker(model_path=args.model, swap_labels=not args.no_swap)
        tracker.track_video(
            video_path=args.video,
            conf=args.conf,
            iou=args.iou,
            show=not args.no_show
        )
    except Exception as e:
        print(f"Error: {e}")
