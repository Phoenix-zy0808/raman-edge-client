"""
模拟拉曼光谱驱动 - 用于测试和演示
生成带有拉曼特征峰和高斯噪声的模拟数据

改进说明:
- 添加基线漂移模拟（真实设备长时间运行基线会漂）
- 添加平滑噪声（使用高斯滤波模拟真实荧光背景波动）
"""
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
from backend.driver.base import BaseDriver, DeviceState


class MockDriver(BaseDriver):
    """
    模拟拉曼光谱驱动
    
    特性:
    - 可配置设备状态（正常/异常/噪声大）
    - 可模拟连接失败场景
    - 光谱数据可复现（固定 random seed）
    - 生成带有拉曼特征峰的模拟数据
    """
    
    # 典型的拉曼位移范围 (cm^-1)
    DEFAULT_WAVENUMBER_RANGE = (200, 3200)
    DEFAULT_NUM_POINTS = 1024
    
    # 常见的拉曼特征峰位置 (cm^-1) - 可根据样品调整
    DEFAULT_RAMAN_PEAKS: List[Tuple[float, float]] = [
        (520, 0.8),    # 硅的特征峰
        (1000, 0.5),   # 苯环呼吸振动
        (1332, 0.6),   # 金刚石峰
        (1580, 0.7),   # G 峰 (石墨/碳材料)
        (2700, 0.4),   # 2D 峰
    ]
    
    def __init__(
        self,
        seed: int = 42,
        noise_level: float = 0.02,
        peak_positions: Optional[List[Tuple[float, float]]] = None,
        simulate_failure: bool = False,
        failure_rate: float = 0.1,
        baseline_drift: float = 0.01,  # 基线漂移幅度
    ):
        """
        初始化模拟驱动

        Args:
            seed: 随机种子，确保数据可复现
            noise_level: 噪声水平 (0-1)
            peak_positions: 特征峰列表 [(位置，强度), ...]
            simulate_failure: 是否模拟连接失败
            failure_rate: 失败率 (0-1)
            baseline_drift: 基线漂移幅度 (0-0.1)，模拟真实设备长时间运行基线漂移
        """
        super().__init__()
        self._seed = seed
        self._noise_level = np.clip(noise_level, 0.0, 1.0)
        self._peak_positions = peak_positions or self.DEFAULT_RAMAN_PEAKS.copy()
        self._simulate_failure = simulate_failure
        self._failure_rate = np.clip(failure_rate, 0.0, 1.0)
        self._rng = np.random.default_rng(seed)
        self._baseline_drift = np.clip(baseline_drift, 0.0, 0.1)
        self._time_counter = 0  # 用于模拟随时间变化的基线漂移

        # 设备状态
        self._device_state = DeviceState.NORMAL
        
        # 生成波长数组
        self._wavenumbers = np.linspace(
            self.DEFAULT_WAVENUMBER_RANGE[0],
            self.DEFAULT_WAVENUMBER_RANGE[1],
            self.DEFAULT_NUM_POINTS
        )
    
    @property
    def device_state(self) -> DeviceState:
        """设备状态"""
        return self._device_state
    
    @device_state.setter
    def device_state(self, state: DeviceState):
        """设置设备状态"""
        if not isinstance(state, DeviceState):
            raise TypeError(f"State must be DeviceState enum, got {type(state)}")
        self._device_state = state
    
    @property
    def peak_positions(self) -> List[Tuple[float, float]]:
        """获取特征峰配置"""
        return self._peak_positions.copy()
    
    def connect(self) -> bool:
        """连接设备"""
        if self._simulate_failure and self._rng.random() < self._failure_rate:
            self._connected = False
            return False
        self._connected = True
        # 重新初始化随机数生成器
        self._rng = np.random.default_rng(self._seed)
        return True
    
    def disconnect(self) -> None:
        """断开连接"""
        self._connected = False

    def is_connected(self) -> bool:
        """检查设备是否已连接"""
        return self._connected

    def set_params(self, **kwargs) -> None:
        """设置采集参数"""
        if 'noise_level' in kwargs:
            self._noise_level = np.clip(kwargs['noise_level'], 0.0, 1.0)
        if 'seed' in kwargs:
            self._seed = kwargs['seed']
            self._rng = np.random.default_rng(self._seed)
        if 'baseline_drift' in kwargs:
            self._baseline_drift = np.clip(kwargs['baseline_drift'], 0.0, 0.1)
        if 'integration_time' in kwargs:
            self._params['integration_time'] = int(kwargs['integration_time'])
        if 'accumulation_count' in kwargs:
            self._params['accumulation_count'] = int(kwargs['accumulation_count'])
        if 'smoothing_window' in kwargs:
            self._params['smoothing_window'] = int(kwargs['smoothing_window'])
        super().set_params(**kwargs)
    
    def get_wavelengths(self) -> np.ndarray:
        """获取波长 (拉曼位移) 数组"""
        return self._wavenumbers.copy()
    
    def read_spectrum(self) -> Optional[np.ndarray]:
        """
        读取光谱数据

        Returns:
            光谱强度数组，如果读取失败返回 None
        """
        if not self._connected:
            return None

        # 模拟设备异常
        if self._device_state == DeviceState.ERROR:
            return None

        # 根据状态调整噪声水平
        noise = self._noise_level
        if self._device_state == DeviceState.HIGH_NOISE:
            noise = self._noise_level * 5

        try:
            # 累加平均
            accumulation_count = self._params.get('accumulation_count', 1)
            spectrum_accumulated = np.zeros(len(self._wavenumbers))
            
            for i in range(accumulation_count):
                # 生成基线 (荧光背景)
                baseline = self._generate_fluorescence_background()

                # 生成拉曼特征峰
                peaks = self._generate_raman_peaks()

                # 添加噪声
                spectrum = baseline + peaks
                noise_array = self._rng.normal(0, noise, size=spectrum.shape)
                spectrum += noise_array
                
                spectrum_accumulated += spectrum
            
            # 平均
            spectrum = spectrum_accumulated / accumulation_count

            # 确保非负
            spectrum = np.maximum(spectrum, 0)

            return spectrum
        except Exception as e:
            print(f"[MockDriver] 读取光谱数据时出错：{e}")
            return None
    
    def _generate_fluorescence_background(self) -> np.ndarray:
        """
        生成荧光背景基线

        使用改进的多项式 + 指数模型模拟真实荧光背景
        改进:
        - 添加随时间变化的基线漂移
        - 添加高斯平滑噪声，模拟真实荧光背景波动
        """
        x = self._wavenumbers
        # 归一化到 0-1
        x_norm = (x - x.min()) / (x.max() - x.min())

        # 指数衰减背景 (主要成分)
        exp_component = 0.3 * np.exp(-3 * x_norm)

        # 多项式背景 (次要成分，模拟复杂荧光)
        poly_component = 0.05 * (1 - x_norm) ** 2

        # 常数基底
        base = 0.1

        # 基线漂移：使用正弦波模拟随时间缓慢变化的基线
        # 真实设备长时间运行会因温度变化、激光功率波动等产生基线漂移
        drift = self._baseline_drift * np.sin(2 * np.pi * self._time_counter / 1000)
        self._time_counter += 1  # 每次调用递增

        # 添加平滑噪声：生成随机噪声后用高斯滤波平滑
        # 模拟真实荧光背景的细微波动
        if self._baseline_drift > 0:
            random_noise = self._rng.normal(0, 0.005, size=len(x))
            # 使用累积平均实现简单平滑
            smooth_noise = np.convolve(random_noise, np.ones(50)/50, mode='same')
        else:
            smooth_noise = 0

        return exp_component + poly_component + base + drift + smooth_noise
    
    def _generate_raman_peaks(self) -> np.ndarray:
        """生成拉曼特征峰 (高斯峰)"""
        peaks = np.zeros_like(self._wavenumbers)
        
        for position, intensity in self._peak_positions:
            peak = self._gaussian_peak(
                center=position,
                amplitude=intensity,
                fwhm=30  # 半高宽 30 cm^-1
            )
            peaks += peak
        
        return peaks
    
    def _gaussian_peak(
        self,
        center: float,
        amplitude: float,
        fwhm: float
    ) -> np.ndarray:
        """
        生成高斯峰
        
        Args:
            center: 峰中心位置
            amplitude: 峰强度
            fwhm: 半高宽 (Full Width at Half Maximum)
        
        Returns:
            高斯峰数组
        """
        sigma = fwhm / (2 * np.sqrt(2 * np.log(2)))
        x = self._wavenumbers
        return amplitude * np.exp(-((x - center) ** 2) / (2 * sigma ** 2))
    
    def set_peak_positions(self, peaks: List[Tuple[float, float]]) -> None:
        """
        设置特征峰位置
        
        Args:
            peaks: 特征峰列表 [(位置，强度), ...]
        """
        self._peak_positions = peaks.copy()
    
    def reset_peak_positions(self) -> None:
        """重置为默认特征峰"""
        self._peak_positions = self.DEFAULT_RAMAN_PEAKS.copy()


if __name__ == '__main__':
    # 测试代码
    driver = MockDriver()
    driver.connect()
    
    print("波长范围:", driver.get_wavelengths().min(), "-", driver.get_wavelengths().max(), "cm^-1")
    print("数据点数:", len(driver.get_wavelengths()))
    print("设备状态:", driver.device_state.value)
    print("特征峰配置:", driver.peak_positions)
    
    spectrum = driver.read_spectrum()
    print("光谱强度范围:", spectrum.min(), "-", spectrum.max())
    
    # 测试不同状态
    driver.device_state = DeviceState.HIGH_NOISE
    noisy_spectrum = driver.read_spectrum()
    print("高噪声光谱强度范围:", noisy_spectrum.min(), "-", noisy_spectrum.max())
