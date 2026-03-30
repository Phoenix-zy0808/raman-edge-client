"""
拉曼光谱仪驱动基类接口
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from enum import Enum
import numpy as np


class DeviceState(Enum):
    """设备状态枚举"""
    NORMAL = 'normal'          # 正常
    HIGH_NOISE = 'high_noise'  # 高噪声
    ERROR = 'error'            # 异常


class BaseDriver(ABC):
    """光谱仪驱动基类"""

    def __init__(self):
        self._connected = False
        self._params: Dict[str, Any] = {
            'integration_time': 100,      # 积分时间 (ms)
            'accumulation_count': 1,      # 累加平均次数
            'smoothing_window': 0,        # 平滑窗口大小 (点数)
        }
    
    @property
    def connected(self) -> bool:
        """设备连接状态"""
        return self._connected
    
    @property
    def params(self) -> Dict[str, Any]:
        """当前参数配置"""
        return self._params
    
    @abstractmethod
    def connect(self) -> bool:
        """连接设备"""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """断开连接"""
        pass
    
    @abstractmethod
    def read_spectrum(self) -> Optional[np.ndarray]:
        """读取光谱数据，返回强度数组"""
        pass
    
    @abstractmethod
    def get_wavelengths(self) -> np.ndarray:
        """获取波长数组"""
        pass
    
    def set_params(self, **kwargs) -> None:
        """设置采集参数"""
        self._params.update(kwargs)
