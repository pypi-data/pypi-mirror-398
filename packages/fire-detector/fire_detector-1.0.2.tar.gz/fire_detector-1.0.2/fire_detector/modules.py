import torch
import torch.nn as nn

class PartialConv2d(nn.Module):
    """Partial Convolution (PConv) 实现"""
    def __init__(self, in_channels, kernel_size=3, stride=1, padding=1):
        super(PartialConv2d, self).__init__()
        # 只对部分通道进行卷积
        self.partial_channels = max(1, in_channels // 4)  # 论文中设置为1/4
        self.conv = nn.Conv2d(
            self.partial_channels, self.partial_channels,
            kernel_size=kernel_size, stride=stride, 
            padding=padding, bias=False
        )
        self.bn = nn.BatchNorm2d(self.partial_channels)
        self.activation = nn.ReLU(inplace=True)
        
    def forward(self, x):
        # 只对前partial_channels个通道进行卷积
        partial_x = x[:, :self.partial_channels, :, :].contiguous()
        partial_x = self.conv(partial_x)
        partial_x = self.bn(partial_x)
        partial_x = self.activation(partial_x)
        
        # 将处理后的部分通道与原始通道合并
        result = torch.cat([partial_x, x[:, self.partial_channels:, :, :].contiguous()], dim=1)
        return result

class FasterNetBlock(nn.Module):
    """FasterNet Block 模块"""
    def __init__(self, in_channels, out_channels, expansion=2):
        super(FasterNetBlock, self).__init__()
        
        # 扩展通道数
        hidden_channels = int(in_channels * expansion)
        
        # PConv层
        self.pconv = PartialConv2d(in_channels, kernel_size=3, stride=1, padding=1)
        
        # 第一个PWConv (1x1卷积)
        self.pwconv1 = nn.Conv2d(in_channels, hidden_channels, kernel_size=1, bias=False)
        self.bn1 = nn.BatchNorm2d(hidden_channels)
        self.act1 = nn.ReLU(inplace=True)
        
        # 第二个PWConv (1x1卷积)
        self.pwconv2 = nn.Conv2d(hidden_channels, out_channels, kernel_size=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)
        
        #  shortcut连接
        self.use_shortcut = (in_channels == out_channels)
        if not self.use_shortcut:
            self.shortcut = nn.Conv2d(in_channels, out_channels, kernel_size=1, bias=False)
            self.shortcut_bn = nn.BatchNorm2d(out_channels)
            
    def forward(self, x):
        identity = x
        
        # PConv
        x = self.pconv(x)
        
        # 第一个PWConv
        x = self.pwconv1(x)
        x = self.bn1(x)
        x = self.act1(x)
        
        # 第二个PWConv
        x = self.pwconv2(x)
        x = self.bn2(x)
        
        # Shortcut连接
        if self.use_shortcut:
            x = x + identity
        else:
            identity = self.shortcut(identity)
            identity = self.shortcut_bn(identity)
            x = x + identity
            
        return x

class FasterNetC2f(nn.Module):
    """
    使用 FasterNetBlock 替换 C2f 的包装类
    用于劫持 Ultralytics 的 C2f 模块，以便利用 parse_model 的自动通道计算功能
    优化: 当 c1 != c2 时使用 1x1 卷积过渡，减少参数量
    """
    def __init__(self, c1, c2, n=1, shortcut=False, g=1, e=0.5):
        super().__init__()
        self.c1 = c1
        self.c2 = c2
        self.blocks = nn.ModuleList()
        
        # 转换层: 如果输入输出通道不同，使用1x1卷积调整
        if c1 != c2:
            self.transition = nn.Sequential(
                nn.Conv2d(c1, c2, kernel_size=1, stride=1, bias=False),
                nn.BatchNorm2d(c2),
                nn.ReLU(inplace=True)
            )
        else:
            self.transition = None
            
        # 堆叠 n 个 FasterNetBlock (保持通道数 c2 -> c2)
        for _ in range(n):
            self.blocks.append(FasterNetBlock(c2, c2))
            
    def forward(self, x):
        if self.transition:
            x = self.transition(x)
        for block in self.blocks:
            x = block(x)
        return x
