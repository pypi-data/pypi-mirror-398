"""
移动端AI驱动自动化测试模块

功能：
1. Android原生App自动化测试
2. iOS原生App自动化测试（后续）
3. AI驱动的元素定位（复用现有SmartLocator）
4. 多模态视觉识别支持
5. 成本优化（规则匹配优先，AI降级）

使用示例：
    from mobile_mcp.core.mobile_client import MobileClient
    
    # 连接设备
    client = MobileClient(device_id=None)
    
    # 启动App
    await client.launch_app("com.example.app")
    
    # 自然语言定位（AI自动定位）
    await client.click("登录按钮")
    await client.type_text("用户名输入框", "test@example.com")
"""

__version__ = "1.0.0"

from .core.mobile_client import MobileClient
from .core.device_manager import DeviceManager

__all__ = [
    'MobileClient',
    'DeviceManager',
]

