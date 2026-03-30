"""
不确定性量化模块

使用 Monte Carlo Dropout 技术量化模型预测的不确定性
创新点：
  - 模型不仅给出预测，还给出置信度
  - 对于"未知物质"能说"我不知道"，而不是瞎猜
  - 科研/医疗场景刚需（医生不敢信 AI 就是因为没置信度）

技术路线：
  输入光谱 → Dropout 推理 50 次 → 预测分布 → 均值 + 方差 → 置信度

参考文献：
  - Gal, Y., & Ghahramani, Z. (2016). Dropout as a Bayesian Approximation. ICML.
  - Kendall, A., & Gal, Y. (2017). What Uncertainties Do We Need in Bayesian Deep Learning? NeurIPS.
"""
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class UncertaintyResult:
    """不确定性量化结果"""
    prediction: int  # 预测类别
    confidence: float  # 置信度（均值）
    uncertainty: float  # 不确定性（标准差）
    entropy: float  # 预测熵
    probabilities: np.ndarray  # 概率分布
    uncertainty_per_class: np.ndarray  # 每类的不确定性
    risk_level: str  # 风险等级："low", "medium", "high"
    is_reliable: bool  # 是否可信
    n_samples: int  # MC 采样次数
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'prediction': self.prediction,
            'confidence': float(self.confidence),
            'uncertainty': float(self.uncertainty),
            'entropy': float(self.entropy),
            'probabilities': self.probabilities.tolist(),
            'uncertainty_per_class': self.uncertainty_per_class.tolist(),
            'risk_level': self.risk_level,
            'is_reliable': self.is_reliable,
            'n_samples': self.n_samples,
            'confidence_interval_95': self.get_confidence_interval(0.95),
            'confidence_interval_99': self.get_confidence_interval(0.99),
        }
    
    def get_confidence_interval(self, level: float = 0.95) -> Tuple[float, float]:
        """计算置信度的置信区间"""
        z_score = 1.96 if level == 0.95 else 2.58
        lower = max(0.0, self.confidence - z_score * self.uncertainty)
        upper = min(1.0, self.confidence + z_score * self.uncertainty)
        return (float(lower), float(upper))


class UncertaintyQuantifier:
    """
    不确定性量化器
    
    使用 Monte Carlo Dropout 技术：
    1. 在推理时保持 Dropout 激活
    2. 进行多次前向传播（默认 50 次）
    3. 计算预测的均值和方差
    4. 评估预测可靠性
    """
    
    # 风险等级阈值
    HIGH_CONFIDENCE_THRESHOLD = 0.8  # 置信度>80% 为高置信度
    LOW_CONFIDENCE_THRESHOLD = 0.5   # 置信度<50% 为低置信度
    HIGH_UNCERTAINTY_THRESHOLD = 0.15  # 不确定性>15% 为高不确定性
    HIGH_ENTROPY_THRESHOLD = 2.0  # 熵>2.0 为高熵（对于 10 类别，最大熵约 2.3）
    
    def __init__(
        self,
        model: Any,
        n_samples: int = 50,
        dropout_rate: float = 0.1
    ):
        """
        初始化不确定性量化器
        
        Args:
            model: 支持 predict_with_uncertainty 方法的模型
            n_samples: Monte Carlo 采样次数
            dropout_rate: Dropout 率
        """
        self.model = model
        self.n_samples = n_samples
        self.dropout_rate = dropout_rate
        self._log = logging.getLogger(__name__)
        
        # 校准数据（用于可靠性评估）
        self._calibration_data: Dict[str, List] = {
            'confidence': [],
            'accuracy': []
        }
    
    def predict(
        self,
        spectrum: np.ndarray,
        class_names: Optional[List[str]] = None
    ) -> UncertaintyResult:
        """
        进行不确定性量化预测

        Args:
            spectrum: 输入光谱
            class_names: 类别名称列表

        Returns:
            UncertaintyResult 对象
        """
        if not hasattr(self.model, 'predict_with_uncertainty'):
            raise ValueError("模型必须支持 predict_with_uncertainty 方法")

        # 获取不确定性预测
        result_dict = self.model.predict_with_uncertainty(
            spectrum,
            n_samples=self.n_samples,
            dropout_rate=self.dropout_rate
        )
        
        # 检查是否有错误
        if 'error' in result_dict:
            # 模型未加载，返回默认结果
            return UncertaintyResult(
                prediction=0,
                confidence=0.0,
                uncertainty=0.0,
                entropy=0.0,
                probabilities=np.zeros(self.model.config.num_classes if hasattr(self.model, 'config') else 10),
                uncertainty_per_class=np.zeros(self.model.config.num_classes if hasattr(self.model, 'config') else 10),
                risk_level='high',
                is_reliable=False,
                n_samples=self.n_samples
            )

        # 提取结果
        prediction = result_dict['prediction']
        confidence = result_dict['confidence']
        uncertainty = result_dict['uncertainty']
        entropy = result_dict.get('entropy', 0.0)
        probabilities = np.array(result_dict['probabilities'])
        uncertainty_per_class = np.array(result_dict.get('uncertainty_per_class', np.zeros_like(probabilities)))

        # 评估风险等级
        risk_level = self._evaluate_risk_level(confidence, uncertainty, entropy)
        is_reliable = risk_level == 'low'

        result = UncertaintyResult(
            prediction=prediction,
            confidence=confidence,
            uncertainty=uncertainty,
            entropy=entropy,
            probabilities=probabilities,
            uncertainty_per_class=uncertainty_per_class,
            risk_level=risk_level,
            is_reliable=is_reliable,
            n_samples=self.n_samples
        )

        self._log.info(
            f"[UncertaintyQuantifier] 预测：{prediction}, "
            f"置信度：{confidence:.3f}±{uncertainty:.3f}, "
            f"风险等级：{risk_level}"
        )

        return result
    
    def _evaluate_risk_level(
        self,
        confidence: float,
        uncertainty: float,
        entropy: float
    ) -> str:
        """
        评估预测风险等级
        
        Args:
            confidence: 置信度
            uncertainty: 不确定性
            entropy: 预测熵
            
        Returns:
            风险等级："low", "medium", "high"
        """
        # 高风险条件
        high_risk_conditions = [
            confidence < self.LOW_CONFIDENCE_THRESHOLD,
            uncertainty > self.HIGH_UNCERTAINTY_THRESHOLD,
            entropy > self.HIGH_ENTROPY_THRESHOLD
        ]
        
        # 低风险条件
        low_risk_conditions = [
            confidence >= self.HIGH_CONFIDENCE_THRESHOLD,
            uncertainty <= self.HIGH_UNCERTAINTY_THRESHOLD / 2,
            entropy <= self.HIGH_ENTROPY_THRESHOLD / 2
        ]
        
        if sum(high_risk_conditions) >= 2:
            return 'high'
        elif sum(low_risk_conditions) >= 2:
            return 'low'
        else:
            return 'medium'
    
    def calibrate(
        self,
        spectra: List[np.ndarray],
        true_labels: List[int]
    ) -> Dict[str, float]:
        """
        校准不确定性估计
        
        通过分析预测置信度与实际准确率的关系，评估不确定性量化的可靠性
        
        Args:
            spectra: 光谱样本列表
            true_labels: 真实标签列表
            
        Returns:
            校准结果
        """
        if len(spectra) != len(true_labels):
            raise ValueError("样本数和标签数必须一致")
        
        predictions = []
        confidences = []
        accuracies = []
        
        # 对每个样本进行预测
        for spectrum, true_label in zip(spectra, true_labels):
            result = self.predict(spectrum)
            pred_correct = (result.prediction == true_label)
            
            predictions.append(result.prediction)
            confidences.append(result.confidence)
            accuracies.append(pred_correct)
        
        # 计算校准统计量
        confidences = np.array(confidences)
        accuracies = np.array(accuracies)
        
        # 分箱分析
        bins = [0.0, 0.3, 0.5, 0.7, 0.9, 1.0]
        bin_stats = []
        
        for i in range(len(bins) - 1):
            mask = (confidences >= bins[i]) & (confidences < bins[i + 1])
            if np.sum(mask) > 0:
                bin_conf = np.mean(confidences[mask])
                bin_acc = np.mean(accuracies[mask])
                bin_stats.append({
                    'bin': f'{bins[i]:.1f}-{bins[i+1]:.1f}',
                    'count': int(np.sum(mask)),
                    'avg_confidence': float(bin_conf),
                    'accuracy': float(bin_acc),
                    'gap': float(abs(bin_acc - bin_conf))
                })
        
        # 计算 ECE (Expected Calibration Error)
        ece = 0.0
        total = len(confidences)
        for stat in bin_stats:
            weight = stat['count'] / total
            ece += weight * stat['gap']
        
        calibration_result = {
            'ece': float(ece),
            'accuracy': float(np.mean(accuracies)),
            'avg_confidence': float(np.mean(confidences)),
            'correlation': float(np.corrcoef(confidences, accuracies)[0, 1]) if len(confidences) > 1 else 0.0,
            'bin_stats': bin_stats,
            'n_samples': len(spectra)
        }
        
        self._log.info(
            f"[UncertaintyQuantifier] 校准完成：ECE={ece:.4f}, "
            f"准确率={calibration_result['accuracy']:.3f}, "
            f"相关性={calibration_result['correlation']:.3f}"
        )
        
        return calibration_result
    
    def detect_outlier(
        self,
        spectrum: np.ndarray,
        threshold: float = 0.5
    ) -> Tuple[bool, float]:
        """
        检测异常样本（未知物质）
        
        如果模型对某个样本的预测不确定性很高，可能是未知物质
        
        Args:
            spectrum: 输入光谱
            threshold: 不确定性阈值
            
        Returns:
            (是否异常，异常分数)
        """
        result = self.predict(spectrum)
        
        # 异常分数：综合考虑低置信度和高不确定性
        outlier_score = (1 - result.confidence) * 0.5 + result.uncertainty * 0.5
        
        is_outlier = outlier_score > threshold
        
        self._log.info(
            f"[UncertaintyQuantifier] 异常检测：分数={outlier_score:.3f}, "
            f"阈值={threshold}, 结果={'异常' if is_outlier else '正常'}"
        )
        
        return is_outlier, outlier_score
    
    def get_reliability_diagram_data(
        self,
        spectra: List[np.ndarray],
        true_labels: List[int],
        n_bins: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取可靠性图数据（用于可视化）
        
        Args:
            spectra: 光谱样本列表
            true_labels: 真实标签列表
            n_bins: 分箱数量
            
        Returns:
            可靠性图数据
        """
        predictions = []
        confidences = []
        
        for spectrum in spectra:
            result = self.predict(spectrum)
            predictions.append(result.prediction)
            confidences.append(result.confidence)
        
        confidences = np.array(confidences)
        correct = np.array(predictions) == np.array(true_labels)
        
        bin_edges = np.linspace(0, 1, n_bins + 1)
        diagram_data = []
        
        for i in range(n_bins):
            mask = (confidences >= bin_edges[i]) & (confidences < bin_edges[i + 1])
            if np.sum(mask) > 0:
                bin_conf = np.mean(confidences[mask])
                bin_acc = np.mean(correct[mask])
                bin_count = int(np.sum(mask))
            else:
                bin_conf = (bin_edges[i] + bin_edges[i + 1]) / 2
                bin_acc = 0.0
                bin_count = 0
            
            diagram_data.append({
                'confidence': float(bin_conf),
                'accuracy': float(bin_acc),
                'count': bin_count,
                'gap': float(abs(bin_acc - bin_conf))
            })
        
        return diagram_data


class ConfidenceCalibrator:
    """
    置信度校准器
    
    使用温度缩放（Temperature Scaling）校准预测置信度
    使置信度更接近真实准确率
    """
    
    def __init__(self):
        self.temperature: float = 1.0
        self._is_calibrated: bool = False
        self._log = logging.getLogger(__name__)
    
    def fit(
        self,
        logits: np.ndarray,
        labels: np.ndarray,
        lr: float = 0.01,
        n_iterations: int = 100
    ) -> float:
        """
        拟合温度参数
        
        Args:
            logits: 模型输出的 logits [n_samples, n_classes]
            labels: 真实标签 [n_samples]
            lr: 学习率
            n_iterations: 迭代次数
            
        Returns:
            最优温度参数
        """
        n_samples = len(labels)
        
        # 梯度下降优化温度
        for iteration in range(n_iterations):
            # 应用温度缩放
            scaled_logits = logits / self.temperature
            probs = self._softmax(scaled_logits, axis=1)
            
            # 计算负对数似然损失
            correct_probs = probs[np.arange(n_samples), labels]
            loss = -np.mean(np.log(correct_probs + 1e-10))
            
            # 计算梯度
            grad = self._compute_temperature_gradient(logits, labels, self.temperature)
            
            # 更新温度
            self.temperature -= lr * grad
            self.temperature = max(0.1, min(5.0, self.temperature))  # 裁剪
        
        self._is_calibrated = True
        self._log.info(f"[ConfidenceCalibrator] 校准完成：温度={self.temperature:.3f}")
        return self.temperature
    
    def calibrate(self, probs: np.ndarray) -> np.ndarray:
        """
        校准概率
        
        Args:
            probs: 原始概率
            
        Returns:
            校准后的概率
        """
        if not self._is_calibrated:
            self._log.warning("[ConfidenceCalibrator] 未校准，返回原始概率")
            return probs
        
        # 逆温度缩放（简化版本）
        # 实际应用中需要更复杂的校准方法
        calibrated = probs ** (1 / self.temperature)
        calibrated = calibrated / np.sum(calibrated, axis=-1, keepdims=True)
        return calibrated
    
    def _softmax(self, x: np.ndarray, axis: int = -1) -> np.ndarray:
        exp_x = np.exp(x - np.max(x, axis=axis, keepdims=True))
        return exp_x / np.sum(exp_x, axis=axis, keepdims=True)
    
    def _compute_temperature_gradient(
        self,
        logits: np.ndarray,
        labels: np.ndarray,
        temperature: float
    ) -> float:
        """计算温度参数的梯度"""
        n_samples = len(labels)
        scaled_logits = logits / temperature
        probs = self._softmax(scaled_logits, axis=1)
        
        # 梯度计算
        grad = 0.0
        for i in range(n_samples):
            correct_class = labels[i]
            grad += (probs[i, correct_class] - 1) * logits[i, correct_class]
            for j in range(logits.shape[1]):
                if j != correct_class:
                    grad += probs[i, j] * logits[i, j]
        
        return grad / (n_samples * temperature ** 2)
