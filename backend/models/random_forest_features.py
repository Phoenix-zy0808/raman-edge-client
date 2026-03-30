"""
随机森林特征工程模块

方案 A：随机森林 + 特征工程（小样本快速方案）

特征类别：
1. 峰位置特征（10 维）- 在已知峰位置±10 cm⁻¹范围内找最大值位置
2. 峰强度特征（10 维）- 在已知峰位置±10 cm⁻¹范围内找最大强度
3. 峰宽度特征（10 维）- 计算半高宽（FWHM）
4. 强度比特征（5 维）- 特征峰强度比值
5. 全局特征（5 维）- 曲线下面积、光谱斜率、重心、偏度、峰度

总特征数：40 维 → 特征选择 → 15-20 维

作者：P11 级全栈工程师
日期：2026-03-29
"""
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from scipy import signal
from scipy.stats import skew, kurtosis
from scipy.interpolate import interp1d
# NumPy 2.0+ 兼容性：trapz 已移至 scipy.integrate
try:
    from scipy.integrate import trapezoid as integrate_trap
except ImportError:
    integrate_trap = np.trapz
import logging

logger = logging.getLogger(__name__)


# 矿物特征峰位置（来自文献）
# 格式：{矿物名：[(峰位置 cm⁻¹, 相对强度), ...]}
MINERAL_PEAKS = {
    'diamond': [(1332, 1.0), (2664, 0.08)],
    'graphite': [(1580, 1.0), (2700, 0.5)],
    'graphene': [(1580, 1.0), (2700, 0.8), (1350, 0.3)],
    'silicon': [(520, 1.0)],
    'quartz': [(464, 1.0), (1082, 0.4), (355, 0.3), (696, 0.2)],
    'calcite': [(1086, 1.0), (713, 0.6), (282, 0.3), (1435, 0.4)],
    'corundum': [(418, 1.0), (378, 0.7), (578, 0.4), (751, 0.35)],
    'olivine': [(820, 1.0), (850, 0.8), (300, 0.4), (545, 0.25)],
    'feldspar': [(510, 1.0), (480, 0.7), (1095, 0.6), (645, 0.35)],
    'zno': [(438, 1.0), (330, 0.5), (580, 0.3)]
}

# 所有特征峰位置（用于特征提取）
ALL_PEAK_POSITIONS = []
for mineral, peaks in MINERAL_PEAKS.items():
    for pos, intensity in peaks:
        if pos not in ALL_PEAK_POSITIONS:
            ALL_PEAK_POSITIONS.append(pos)
ALL_PEAK_POSITIONS = sorted(ALL_PEAK_POSITIONS)


class SpectrumPreprocessor:
    """光谱预处理器"""
    
    def __init__(self, wavenumber_range: Tuple[float, float] = (200, 3200),
                 num_points: int = 1024):
        """
        初始化预处理器
        
        Args:
            wavenumber_range: 波数范围 (min, max)
            num_points: 重采样点数
        """
        self.wavenumber_range = wavenumber_range
        self.num_points = num_points
        self.wavenumbers = np.linspace(wavenumber_range[0],
                                       wavenumber_range[1],
                                       num_points)
        self._log = logging.getLogger(__name__)
    
    def resample(self, spectrum: np.ndarray,
                 original_wavenumbers: np.ndarray) -> np.ndarray:
        """
        重采样到统一的波数轴
        
        Args:
            spectrum: 原始光谱
            original_wavenumbers: 原始波数轴
            
        Returns:
            重采样后的光谱
        """
        # 线性插值
        f = interp1d(original_wavenumbers, spectrum,
                     kind='linear', bounds_error=False,
                     fill_value=0.0)
        return f(self.wavenumbers)
    
    def baseline_correction(self, spectrum: np.ndarray,
                            method: str = 'iterative_poly') -> np.ndarray:
        """
        基线校正
        
        Args:
            spectrum: 原始光谱
            method: 校正方法 ('iterative_poly', 'rubberband')
            
        Returns:
            校正后的光谱
        """
        if method == 'iterative_poly':
            return self._iterative_polynomial_baseline(spectrum)
        elif method == 'rubberband':
            return self._rubberband_baseline(spectrum)
        else:
            return spectrum
    
    def _iterative_polynomial_baseline(self, spectrum: np.ndarray,
                                       order: int = 5,
                                       iterations: int = 5) -> np.ndarray:
        """迭代多项式拟合基线校正"""
        wavenumbers = self.wavenumbers
        baseline = np.zeros_like(spectrum)
        mask = np.ones(len(spectrum), dtype=bool)
        
        for i in range(iterations):
            # 用当前掩码内的点拟合多项式
            coeffs = np.polyfit(wavenumbers[mask], spectrum[mask], order)
            baseline = np.polyval(coeffs, wavenumbers)
            
            # 更新掩码：只保留低于基线的点
            mask = spectrum < baseline
        
        return spectrum - baseline
    
    def _rubberband_baseline(self, spectrum: np.ndarray) -> np.ndarray:
        """橡皮筋基线校正（凸包算法）"""
        wavenumbers = self.wavenumbers
        points = np.vstack([wavenumbers, spectrum]).T
        
        # 计算凸包
        from scipy.spatial import ConvexHull
        hull = ConvexHull(points)
        hull_indices = hull.vertices
        
        # 获取下凸包（基线）
        baseline_points = points[hull_indices]
        baseline_x = baseline_points[:, 0]
        baseline_y = baseline_points[:, 1]
        
        # 插值到完整波数轴
        baseline = np.interp(wavenumbers, baseline_x, baseline_y)
        
        return spectrum - baseline
    
    def normalize(self, spectrum: np.ndarray,
                  method: str = 'minmax') -> np.ndarray:
        """
        归一化
        
        Args:
            spectrum: 光谱
            method: 归一化方法 ('minmax', 'zscore', 'area')
            
        Returns:
            归一化后的光谱
        """
        if method == 'minmax':
            min_val = np.min(spectrum)
            max_val = np.max(spectrum)
            if max_val - min_val > 1e-10:
                return (spectrum - min_val) / (max_val - min_val)
            else:
                return spectrum
        elif method == 'zscore':
            mean = np.mean(spectrum)
            std = np.std(spectrum)
            if std > 1e-10:
                return (spectrum - mean) / std
            else:
                return spectrum
        elif method == 'area':
            area = np.trapz(spectrum, self.wavenumbers)
            if area > 1e-10:
                return spectrum / area
            else:
                return spectrum
        else:
            return spectrum
    
    def smooth(self, spectrum: np.ndarray,
               window_size: int = 11,
               polyorder: int = 2) -> np.ndarray:
        """
        Savitzky-Golay 平滑滤波
        
        Args:
            spectrum: 光谱
            window_size: 窗口大小（必须为奇数）
            polyorder: 多项式阶数
            
        Returns:
            平滑后的光谱
        """
        if window_size % 2 == 0:
            window_size += 1
        
        if window_size > len(spectrum):
            window_size = len(spectrum) if len(spectrum) % 2 == 1 else len(spectrum) - 1
        
        return signal.savgol_filter(spectrum, window_size, polyorder)
    
    def preprocess(self, spectrum: np.ndarray,
                   original_wavenumbers: Optional[np.ndarray] = None,
                   smooth_window: int = 11,
                   normalize_method: str = 'minmax') -> np.ndarray:
        """
        完整预处理流程
        
        Args:
            spectrum: 原始光谱
            original_wavenumbers: 原始波数轴（如果需要重采样）
            smooth_window: 平滑窗口大小
            normalize_method: 归一化方法
            
        Returns:
            预处理后的光谱
        """
        # 1. 重采样（如果需要）
        if original_wavenumbers is not None:
            spectrum = self.resample(spectrum, original_wavenumbers)
        
        # 2. 平滑滤波
        if smooth_window > 0:
            spectrum = self.smooth(spectrum, smooth_window)
        
        # 3. 基线校正
        spectrum = self.baseline_correction(spectrum)
        
        # 4. 归一化
        spectrum = self.normalize(spectrum, normalize_method)
        
        return spectrum


class FeatureExtractor:
    """特征提取器"""
    
    def __init__(self, preprocessor: Optional[SpectrumPreprocessor] = None):
        """
        初始化特征提取器
        
        Args:
            preprocessor: 预处理器实例
        """
        self.preprocessor = preprocessor or SpectrumPreprocessor()
        self.wavenumbers = self.preprocessor.wavenumbers
        self.feature_names: List[str] = []
        self._log = logging.getLogger(__name__)
    
    def extract_all_features(self, spectrum: np.ndarray) -> np.ndarray:
        """
        提取所有特征
        
        Args:
            spectrum: 预处理后的光谱
            
        Returns:
            特征向量
        """
        features = []
        self.feature_names = []
        
        # 1. 峰位置特征（10 维）
        peak_pos_features = self._extract_peak_positions(spectrum)
        features.extend(peak_pos_features)
        self.feature_names.extend([f'peak_pos_{i}' for i in range(len(peak_pos_features))])
        
        # 2. 峰强度特征（10 维）
        peak_int_features = self._extract_peak_intensities(spectrum)
        features.extend(peak_int_features)
        self.feature_names.extend([f'peak_int_{i}' for i in range(len(peak_int_features))])
        
        # 3. 峰宽度特征（10 维）
        peak_width_features = self._extract_peak_widths(spectrum)
        features.extend(peak_width_features)
        self.feature_names.extend([f'peak_width_{i}' for i in range(len(peak_width_features))])
        
        # 4. 强度比特征（5 维）
        ratio_features = self._extract_intensity_ratios(spectrum)
        features.extend(ratio_features)
        self.feature_names.extend([f'intensity_ratio_{i}' for i in range(len(ratio_features))])
        
        # 5. 全局特征（5 维）
        global_features = self._extract_global_features(spectrum)
        features.extend(global_features)
        self.feature_names.extend([f'global_{i}' for i in range(len(global_features))])
        
        return np.array(features)
    
    def _extract_peak_positions(self, spectrum: np.ndarray,
                                search_range: float = 10) -> List[float]:
        """
        提取峰位置特征
        
        在已知特征峰位置±search_range 范围内找最大值位置
        """
        features = []
        
        for peak_pos in ALL_PEAK_POSITIONS[:10]:  # 只用前 10 个峰
            # 定义搜索范围
            min_idx = np.searchsorted(self.wavenumbers, peak_pos - search_range)
            max_idx = np.searchsorted(self.wavenumbers, peak_pos + search_range)
            
            if min_idx >= len(spectrum) or max_idx <= 0:
                features.append(peak_pos)  # 超出范围，用理论值
                continue
            
            min_idx = max(0, min_idx)
            max_idx = min(len(spectrum), max_idx)
            
            # 找最大值位置
            region = spectrum[min_idx:max_idx]
            if len(region) > 0:
                max_local_idx = np.argmax(region)
                actual_pos = self.wavenumbers[min_idx + max_local_idx]
                features.append(actual_pos)
            else:
                features.append(peak_pos)
        
        return features
    
    def _extract_peak_intensities(self, spectrum: np.ndarray,
                                  search_range: float = 10) -> List[float]:
        """
        提取峰强度特征
        
        在已知特征峰位置±search_range 范围内找最大强度
        """
        features = []
        
        for peak_pos in ALL_PEAK_POSITIONS[:10]:
            # 定义搜索范围
            min_idx = np.searchsorted(self.wavenumbers, peak_pos - search_range)
            max_idx = np.searchsorted(self.wavenumbers, peak_pos + search_range)
            
            if min_idx >= len(spectrum) or max_idx <= 0:
                features.append(0.0)
                continue
            
            min_idx = max(0, min_idx)
            max_idx = min(len(spectrum), max_idx)
            
            # 找最大强度
            region = spectrum[min_idx:max_idx]
            if len(region) > 0:
                max_intensity = np.max(region)
                features.append(max_intensity)
            else:
                features.append(0.0)
        
        return features
    
    def _extract_peak_widths(self, spectrum: np.ndarray,
                             search_range: float = 10) -> List[float]:
        """
        提取峰宽度特征（半高宽 FWHM）
        """
        features = []
        
        for peak_pos in ALL_PEAK_POSITIONS[:10]:
            # 定义搜索范围
            min_idx = np.searchsorted(self.wavenumbers, peak_pos - search_range)
            max_idx = np.searchsorted(self.wavenumbers, peak_pos + search_range)
            
            if min_idx >= len(spectrum) or max_idx <= 0:
                features.append(20.0)  # 默认宽度
                continue
            
            min_idx = max(0, min_idx)
            max_idx = min(len(spectrum), max_idx)
            
            region = spectrum[min_idx:max_idx]
            region_wavenumbers = self.wavenumbers[min_idx:max_idx]
            
            if len(region) < 3:
                features.append(20.0)
                continue
            
            # 找峰顶
            max_idx_local = np.argmax(region)
            max_intensity = region[max_idx_local]
            half_max = max_intensity / 2
            
            # 找半高宽
            left_idx = np.where(region[:max_idx_local] <= half_max)[0]
            right_idx = np.where(region[max_idx_local:] <= half_max)[0]
            
            if len(left_idx) > 0 and len(right_idx) > 0:
                left_wavenumber = region_wavenumbers[left_idx[-1]]
                right_wavenumber = region_wavenumbers[max_idx_local + right_idx[0]]
                fwhm = right_wavenumber - left_wavenumber
                features.append(fwhm)
            else:
                features.append(20.0)
        
        return features
    
    def _extract_intensity_ratios(self, spectrum: np.ndarray) -> List[float]:
        """
        提取强度比特征
        
        计算特征峰强度比值
        """
        features = []
        
        # 定义强度比：使用主要矿物的特征峰
        ratios = [
            ('quartz', 0, 1),      # I_1082 / I_464
            ('diamond', 0, 1),     # I_1332 / I_背景
            ('graphite', 0, 1),    # I_1580 / I_背景
            ('calcite', 0, 1),     # I_1086 / I_713
            ('corundum', 0, 1),    # I_418 / I_背景
        ]
        
        # 获取所有峰强度
        intensities = self._extract_peak_intensities(spectrum)
        
        # 计算背景强度（用光谱均值）
        background_intensity = np.mean(spectrum) + 0.01
        
        for mineral, idx1, idx2 in ratios:
            if idx1 < len(intensities) and idx2 < len(intensities):
                int1 = intensities[idx1]
                int2 = intensities[idx2] if idx2 < len(intensities) else background_intensity
                
                if int2 > 0.01:
                    ratio = int1 / int2
                else:
                    ratio = int1 / background_intensity
                
                features.append(min(10.0, ratio))  # 限制最大值
            else:
                features.append(1.0)
        
        return features
    
    def _extract_global_features(self, spectrum: np.ndarray) -> List[float]:
        """
        提取全局特征
        
        1. 曲线下面积（积分强度）
        2. 光谱斜率（线性拟合斜率）
        3. 光谱重心（强度加权平均波长）
        4. 光谱偏度（三阶矩）
        5. 光谱峰度（四阶矩）
        """
        features = []
        
        # 1. 曲线下面积
        area = integrate_trap(spectrum, self.wavenumbers)
        features.append(area)
        
        # 2. 光谱斜率
        coeffs = np.polyfit(self.wavenumbers, spectrum, 1)
        slope = coeffs[0]
        features.append(slope)
        
        # 3. 光谱重心
        total_intensity = np.sum(spectrum)
        if total_intensity > 1e-10:
            centroid = np.sum(self.wavenumbers * spectrum) / total_intensity
        else:
            centroid = np.mean(self.wavenumbers)
        features.append(centroid)
        
        # 4. 光谱偏度
        if np.std(spectrum) > 1e-10:
            spectrum_skew = skew(spectrum)
        else:
            spectrum_skew = 0.0
        features.append(spectrum_skew)
        
        # 5. 光谱峰度
        if np.std(spectrum) > 1e-10:
            spectrum_kurt = kurtosis(spectrum)
        else:
            spectrum_kurt = 0.0
        features.append(spectrum_kurt)
        
        return features


class FeatureSelector:
    """特征选择器"""
    
    def __init__(self, variance_threshold: float = 0.01,
                 correlation_threshold: float = 0.9,
                 top_k: int = 20):
        """
        初始化特征选择器
        
        Args:
            variance_threshold: 方差阈值（删除方差<阈值的特征）
            correlation_threshold: 相关性阈值（删除|r|>阈值的特征）
            top_k: 保留 Top-K 特征（基于随机森林重要性）
        """
        self.variance_threshold = variance_threshold
        self.correlation_threshold = correlation_threshold
        self.top_k = top_k
        self.selected_indices: Optional[np.ndarray] = None
        self.feature_names: List[str] = []
        self._log = logging.getLogger(__name__)
    
    def select(self, X: np.ndarray, y: np.ndarray,
               feature_names: List[str]) -> np.ndarray:
        """
        执行特征选择
        
        Args:
            X: 特征矩阵 [N, M]
            y: 标签 [N]
            feature_names: 特征名称列表
            
        Returns:
            选择后的特征矩阵 [N, K]
        """
        self.feature_names = feature_names.copy()
        n_samples, n_features = X.shape
        
        self._log.info(f"初始特征数：{n_features}")
        
        # 1. 方差阈值过滤
        X_filtered = self._variance_threshold_filter(X)
        self._log.info(f"方差过滤后特征数：{X_filtered.shape[1]}")
        
        # 2. 相关性过滤
        X_filtered = self._correlation_filter(X_filtered)
        self._log.info(f"相关性过滤后特征数：{X_filtered.shape[1]}")
        
        # 3. 基于随机森林重要性的 Top-K 选择
        X_selected = self._random_forest_selection(X_filtered, y)
        self._log.info(f"RF 重要性选择后特征数：{X_selected.shape[1]}")
        
        return X_selected
    
    def _variance_threshold_filter(self, X: np.ndarray) -> np.ndarray:
        """方差阈值过滤"""
        variances = np.var(X, axis=0)
        mask = variances > self.variance_threshold
        
        self.selected_indices = np.where(mask)[0]
        self.feature_names = [self.feature_names[i] for i in range(len(self.feature_names)) if mask[i]]
        
        return X[:, mask]
    
    def _correlation_filter(self, X: np.ndarray) -> np.ndarray:
        """相关性过滤（删除高度相关的特征）"""
        n_features = X.shape[1]
        
        if n_features < 2:
            return X
        
        # 计算相关系数矩阵
        corr_matrix = np.corrcoef(X.T)
        
        # 标记要删除的特征
        to_remove = set()
        for i in range(n_features):
            if i in to_remove:
                continue
            for j in range(i + 1, n_features):
                if j in to_remove:
                    continue
                if abs(corr_matrix[i, j]) > self.correlation_threshold:
                    # 删除方差较小的那个
                    var_i = np.var(X[:, i])
                    var_j = np.var(X[:, j])
                    if var_i < var_j:
                        to_remove.add(i)
                    else:
                        to_remove.add(j)
        
        # 保留未被标记的特征
        mask = np.array([i not in to_remove for i in range(n_features)])
        
        self.selected_indices = self.selected_indices[mask] if self.selected_indices is not None else np.where(mask)[0]
        self.feature_names = [self.feature_names[i] for i in range(len(self.feature_names)) if mask[i]]
        
        return X[:, mask]
    
    def _random_forest_selection(self, X: np.ndarray, y: np.ndarray) -> np.ndarray:
        """基于随机森林重要性的 Top-K 选择"""
        try:
            from sklearn.ensemble import RandomForestClassifier
            
            # 训练随机森林
            rf = RandomForestClassifier(
                n_estimators=100,
                max_depth=5,
                random_state=42,
                n_jobs=-1
            )
            rf.fit(X, y)
            
            # 获取特征重要性
            importances = rf.feature_importances_
            
            # 选择 Top-K
            top_k = min(self.top_k, X.shape[1])
            top_indices = np.argsort(importances)[::-1][:top_k]
            
            self.selected_indices = self.selected_indices[top_indices] if self.selected_indices is not None else top_indices
            self.feature_names = [self.feature_names[i] for i in range(len(self.feature_names)) if i in top_indices]
            
            return X[:, top_indices]
        
        except ImportError:
            self._log.warning("sklearn 未安装，跳过 RF 特征选择")
            return X


def extract_mineral_features(spectrum: np.ndarray,
                             wavenumbers: Optional[np.ndarray] = None,
                             do_preprocess: bool = True) -> Tuple[np.ndarray, List[str]]:
    """
    便捷函数：提取矿物特征
    
    Args:
        spectrum: 原始光谱
        wavenumbers: 波数轴
        do_preprocess: 是否进行预处理
        
    Returns:
        (特征向量，特征名称列表)
    """
    preprocessor = SpectrumPreprocessor()
    extractor = FeatureExtractor(preprocessor)
    
    if do_preprocess and wavenumbers is not None:
        # 预处理
        spectrum_processed = preprocessor.preprocess(spectrum, wavenumbers)
    elif do_preprocess:
        spectrum_processed = preprocessor.preprocess(spectrum)
    else:
        spectrum_processed = spectrum
    
    # 提取特征
    features = extractor.extract_all_features(spectrum_processed)
    
    return features, extractor.feature_names


if __name__ == '__main__':
    # 测试代码
    print("测试特征工程模块...")
    
    # 生成测试光谱（模拟石英）
    wavenumbers = np.linspace(200, 3200, 1024)
    spectrum = np.exp(-(wavenumbers - 464) ** 2 / (2 * 15 ** 2)) + \
               0.4 * np.exp(-(wavenumbers - 1082) ** 2 / (2 * 20 ** 2)) + \
               np.random.normal(0, 0.02, 1024)
    
    # 提取特征
    features, names = extract_mineral_features(spectrum, wavenumbers)
    
    print(f"特征数：{len(features)}")
    print(f"特征名称：{names[:10]}...")
    print(f"前 10 个特征值：{features[:10]}")
