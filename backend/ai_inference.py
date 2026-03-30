"""
AI 推理模块 - P12 新版

集成：
  - Transformer 物质识别模型
  - MC Dropout 不确定性量化
  - 可解释性分析
  - 随机森林 + 特征工程（方案 A）

使用方式:
    from backend.ai_inference import AIInference

    ai = AIInference()
    ai.load_model("models/transformer_minerals.npz")

    # 预测
    result = ai.predict(spectrum)

    # 带不确定性的预测
    result = ai.predict_with_uncertainty(spectrum)

    # 可解释性分析
    result = ai.explain(spectrum)
"""
import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import time
from pathlib import Path

# P12-A 新增：导入随机森林模块
try:
    from backend.models import (
        SpectrumPreprocessor,
        FeatureExtractor,
        FeatureSelector,
        RandomForestModel,
        extract_mineral_features
    )
    RF_AVAILABLE = True
except ImportError as e:
    RF_AVAILABLE = False

logger = logging.getLogger(__name__)


class AIInference:
    """
    AI 推理类
    
    集成 Transformer 模型、不确定性量化和可解释性分析
    """
    
    # 矿物/宝石类别（与 model_config.json 一致）
    CLASS_NAMES = [
        "diamond",      # 金刚石
        "graphite",     # 石墨
        "graphene",     # 石墨烯
        "silicon",      # 硅
        "quartz",       # 石英
        "calcite",      # 方解石
        "corundum",     # 刚玉
        "olivine",      # 橄榄石
        "feldspar",     # 长石
        "zno"           # 氧化锌
    ]
    
    # 中文名称映射
    CLASS_NAMES_ZH = {
        "diamond": "金刚石 (Diamond)",
        "graphite": "石墨 (Graphite)",
        "graphene": "石墨烯 (Graphene)",
        "silicon": "硅 (Silicon)",
        "quartz": "石英 (Quartz)",
        "calcite": "方解石 (Calcite)",
        "corundum": "刚玉 (Corundum)",
        "olivine": "橄榄石 (Olivine)",
        "feldspar": "长石 (Feldspar)",
        "zno": "氧化锌 (ZnO)"
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化 AI 推理

        Args:
            config_path: 配置文件路径
        """
        self._model = None  # Transformer 模型
        self._rf_model = None  # 随机森林模型（方案 A）
        self._uncertainty_quantifier = None
        self._explainability_analyzer = None
        self._is_loaded = False
        self._is_rf_loaded = False  # 随机森林是否已加载
        self._log = logging.getLogger(__name__)
        self._config = {}

        # 预处理和特征提取器（用于随机森林）
        self._preprocessor = None
        self._feature_extractor = None
        self._feature_selector = None

        # 加载配置
        if config_path is None:
            config_path = Path(__file__).parent / "model_config.json"

        try:
            import json
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            self._log.info(f"[AIInference] 配置加载成功：{config_path}")
        except Exception as e:
            self._log.warning(f"[AIInference] 配置加载失败：{e}，使用默认配置")
            self._config = {
                "wavenumber_range": [200, 3200],
                "num_points": 1024,
                "class_labels": self.CLASS_NAMES
            }
    
    def load_model(self, model_path: str) -> bool:
        """
        加载模型
        
        Args:
            model_path: 模型文件路径
            
        Returns:
            是否加载成功
        """
        try:
            # 检查是否可用
            if not self._check_availability():
                self._log.warning("[AIInference] AI 模型模块不可用，使用 MockInference")
                return False
            
            from backend.models.transformer_model import create_transformer_model
            from backend.models.uncertainty import UncertaintyQuantifier
            from backend.models.explainability import ExplainabilityAnalyzer
            
            # 创建模型
            self._model = create_transformer_model(
                num_classes=len(self.CLASS_NAMES),
                input_dim=self._config.get('num_points', 1024),
                model_size='tiny'
            )
            
            # 加载权重
            self._model.load_model(model_path)
            
            # 创建不确定性量化器
            uncertainty_config = self._config.get('uncertainty', {})
            self._uncertainty_quantifier = UncertaintyQuantifier(
                self._model,
                n_samples=uncertainty_config.get('n_samples', 50),
                dropout_rate=uncertainty_config.get('dropout_rate', 0.1)
            )
            
            # 创建可解释性分析器
            self._explainability_analyzer = ExplainabilityAnalyzer(
                self._model,
                class_names=self.CLASS_NAMES,
                wavenumbers=np.linspace(
                    self._config['wavenumber_range'][0],
                    self._config['wavenumber_range'][1],
                    self._config['num_points']
                )
            )
            
            self._is_loaded = True
            self._log.info(f"[AIInference] 模型加载成功：{model_path}")
            return True
            
        except Exception as e:
            self._log.error(f"[AIInference] 模型加载失败：{e}")
            return False
    
    def _check_availability(self) -> bool:
        """检查 AI 模型模块是否可用"""
        try:
            from backend.models.transformer_model import SpectralTransformer
            return True
        except ImportError:
            return False
    
    @property
    def is_loaded(self) -> bool:
        return self._is_loaded
    
    def predict(
        self,
        spectrum: np.ndarray,
        return_probs: bool = True
    ) -> Dict[str, Any]:
        """
        预测物质类别
        
        Args:
            spectrum: 输入光谱
            return_probs: 是否返回概率分布
            
        Returns:
            预测结果字典
        """
        if not self._is_loaded:
            return {
                'success': False,
                'error': 'Model not loaded',
                'prediction': -1,
                'confidence': 0.0
            }
        
        start_time = time.time()
        
        # 预测
        prediction, confidence, metadata = self._model.predict(spectrum, return_probs)
        
        inference_time = time.time() - start_time
        
        result = {
            'success': True,
            'prediction': prediction,
            'class_name': self.CLASS_NAMES[prediction] if prediction < len(self.CLASS_NAMES) else 'unknown',
            'class_name_zh': self.CLASS_NAMES_ZH.get(
                self.CLASS_NAMES[prediction] if prediction < len(self.CLASS_NAMES) else 'unknown',
                '未知'
            ),
            'confidence': confidence,
            'inference_time_ms': inference_time * 1000,
            'metadata': metadata
        }
        
        return result
    
    def predict_with_uncertainty(
        self,
        spectrum: np.ndarray
    ) -> Dict[str, Any]:
        """
        带不确定性量化的预测
        
        Args:
            spectrum: 输入光谱
            
        Returns:
            预测结果字典（包含不确定性信息）
        """
        if not self._is_loaded:
            return {
                'success': False,
                'error': 'Model not loaded',
                'prediction': -1,
                'confidence': 0.0,
                'uncertainty': 0.0
            }
        
        start_time = time.time()
        
        # 不确定性量化预测
        uncertainty_result = self._uncertainty_quantifier.predict(spectrum)
        
        inference_time = time.time() - start_time
        
        # 转换为字典
        result_dict = uncertainty_result.to_dict()
        
        result = {
            'success': True,
            'prediction': uncertainty_result.prediction,
            'class_name': self.CLASS_NAMES[uncertainty_result.prediction] if uncertainty_result.prediction < len(self.CLASS_NAMES) else 'unknown',
            'class_name_zh': self.CLASS_NAMES_ZH.get(
                self.CLASS_NAMES[uncertainty_result.prediction] if uncertainty_result.prediction < len(self.CLASS_NAMES) else 'unknown',
                '未知'
            ),
            'confidence': uncertainty_result.confidence,
            'uncertainty': uncertainty_result.uncertainty,
            'entropy': uncertainty_result.entropy,
            'risk_level': uncertainty_result.risk_level,
            'is_reliable': uncertainty_result.is_reliable,
            'confidence_interval_95': result_dict['confidence_interval_95'],
            'inference_time_ms': inference_time * 1000,
            'probabilities': result_dict['probabilities'],
            'uncertainty_per_class': result_dict['uncertainty_per_class']
        }
        
        self._log.info(
            f"[AIInference] 预测：{result['class_name']}, "
            f"置信度：{result['confidence']:.3f}±{result['uncertainty']:.3f}, "
            f"风险等级：{result['risk_level']}"
        )
        
        return result
    
    def explain(
        self,
        spectrum: np.ndarray,
        method: str = 'attention',
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        可解释性分析
        
        Args:
            spectrum: 输入光谱
            method: 解释方法 ('attention', 'gradient', 'occlusion', 'shap')
            top_k: 返回前 k 个重要特征
            
        Returns:
            解释结果字典
        """
        if not self._is_loaded:
            return {
                'success': False,
                'error': 'Model not loaded'
            }
        
        start_time = time.time()
        
        # 可解释性分析
        explain_result = self._explainability_analyzer.explain(
            spectrum, method=method, top_k=top_k
        )
        
        inference_time = time.time() - start_time
        
        # 生成热力图数据
        heatmap_data = self._explainability_analyzer.visualize_heatmap(
            spectrum, explain_result.feature_importance
        )
        
        result = {
            'success': True,
            'prediction': explain_result.prediction,
            'class_name': self.CLASS_NAMES[explain_result.prediction] if explain_result.prediction < len(self.CLASS_NAMES) else 'unknown',
            'class_name_zh': self.CLASS_NAMES_ZH.get(
                self.CLASS_NAMES[explain_result.prediction] if explain_result.prediction < len(self.CLASS_NAMES) else 'unknown',
                '未知'
            ),
            'confidence': explain_result.confidence,
            'decision_basis': explain_result.decision_basis,
            'top_contributions': [fc.to_dict() for fc in explain_result.top_contributions],
            'feature_importance': heatmap_data,
            'inference_time_ms': inference_time * 1000
        }
        
        self._log.info(
            f"[AIInference] 解释生成：{result['class_name']}, "
            f"特征数：{len(result['top_contributions'])}"
        )
        
        return result
    
    def full_analysis(
        self,
        spectrum: np.ndarray,
        include_uncertainty: bool = True,
        include_explainability: bool = True
    ) -> Dict[str, Any]:
        """
        完整分析（预测 + 不确定性 + 可解释性）
        
        Args:
            spectrum: 输入光谱
            include_uncertainty: 是否包含不确定性量化
            include_explainability: 是否包含可解释性分析
            
        Returns:
            完整分析结果
        """
        if not self._is_loaded:
            return {
                'success': False,
                'error': 'Model not loaded'
            }
        
        start_time = time.time()
        
        result = {
            'success': True,
            'analysis_time_ms': 0
        }
        
        # 基础预测
        pred_result = self.predict(spectrum)
        result.update(pred_result)
        
        # 不确定性量化
        if include_uncertainty:
            unc_result = self.predict_with_uncertainty(spectrum)
            result['uncertainty'] = {
                'uncertainty': unc_result['uncertainty'],
                'entropy': unc_result['entropy'],
                'risk_level': unc_result['risk_level'],
                'is_reliable': unc_result['is_reliable'],
                'confidence_interval_95': unc_result['confidence_interval_95'],
                'probabilities': unc_result['probabilities']
            }
        
        # 可解释性分析
        if include_explainability:
            exp_result = self.explain(spectrum)
            result['explainability'] = {
                'decision_basis': exp_result['decision_basis'],
                'top_contributions': exp_result['top_contributions'],
                'feature_importance': exp_result['feature_importance']
            }
        
        result['analysis_time_ms'] = (time.time() - start_time) * 1000
        
        self._log.info(
            f"[AIInference] 完整分析完成，耗时：{result['analysis_time_ms']:.1f}ms"
        )
        
        return result
    
    def detect_outlier(
        self,
        spectrum: np.ndarray,
        threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        检测异常样本（未知物质）
        
        Args:
            spectrum: 输入光谱
            threshold: 不确定性阈值
            
        Returns:
            异常检测结果
        """
        if not self._is_loaded:
            return {
                'success': False,
                'error': 'Model not loaded'
            }
        
        is_outlier, outlier_score = self._uncertainty_quantifier.detect_outlier(
            spectrum, threshold
        )
        
        result = {
            'success': True,
            'is_outlier': is_outlier,
            'outlier_score': outlier_score,
            'threshold': threshold,
            'message': '检测到未知物质' if is_outlier else '样本正常'
        }
        
        self._log.info(
            f"[AIInference] 异常检测：分数={outlier_score:.3f}, 结果={'异常' if is_outlier else '正常'}"
        )
        
        return result
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        if not self._is_loaded and not self._is_rf_loaded:
            return {'loaded': False}

        info = {
            'transformer_loaded': self._is_loaded,
            'random_forest_loaded': self._is_rf_loaded
        }

        if self._is_loaded and self._model is not None:
            info.update({
                'model_type': 'SpectralTransformer',
                'model_size': 'tiny',
                'num_classes': len(self.CLASS_NAMES),
                'input_dim': self._config.get('num_points', 1024),
                'wavenumber_range': self._config.get('wavenumber_range', [200, 3200]),
            })

        if self._is_rf_loaded and self._rf_model is not None:
            info.update({
                'rf_model_type': 'RandomForest',
                'rf_n_estimators': self._rf_model.n_estimators,
                'rf_n_features': len(self._rf_model.feature_names),
                'rf_n_classes': len(self._rf_model.class_names)
            })

        info['config'] = self._config

        return info

    # ========== P12-A 随机森林方法 ==========

    def load_random_forest(self, model_path: str) -> bool:
        """
        加载随机森林模型

        Args:
            model_path: 模型文件路径 (.pkl)

        Returns:
            是否加载成功
        """
        if not RF_AVAILABLE:
            self._log.warning("[AIInference] 随机森林模块不可用")
            return False

        try:
            from backend.models import RandomForestModel

            self._rf_model = RandomForestModel()
            self._rf_model.load(model_path)

            # 初始化预处理和特征提取器
            self._preprocessor = SpectrumPreprocessor(
                wavenumber_range=self._config.get('wavenumber_range', [200, 3200]),
                num_points=self._config.get('num_points', 1024)
            )
            self._feature_extractor = FeatureExtractor(self._preprocessor)

            self._is_rf_loaded = True
            self._log.info(f"[AIInference] 随机森林模型已加载：{model_path}")
            return True

        except Exception as e:
            self._log.error(f"[AIInference] 随机森林模型加载失败：{e}")
            return False

    def predict_rf(self, spectrum: np.ndarray) -> Dict[str, Any]:
        """
        随机森林预测

        Args:
            spectrum: 输入光谱

        Returns:
            预测结果
        """
        if not self._is_rf_loaded:
            return {
                'success': False,
                'error': '随机森林模型未加载',
                'prediction': -1,
                'confidence': 0.0
            }

        start_time = time.time()

        try:
            # 预处理
            spectrum_processed = self._preprocessor.preprocess(spectrum)

            # 特征提取
            features = self._feature_extractor.extract_all_features(spectrum_processed)
            features_array = np.array(features).reshape(1, -1)

            # 预测
            prediction = self._rf_model.predict(features_array)[0]
            probs = self._rf_model.predict_proba(features_array)[0]
            confidence = float(np.max(probs))

            inference_time = time.time() - start_time

            result = {
                'success': True,
                'prediction': int(prediction),
                'class_name': self._rf_model.class_names[prediction] if prediction < len(self._rf_model.class_names) else 'unknown',
                'class_name_zh': self.CLASS_NAMES_ZH.get(
                    self._rf_model.class_names[prediction] if prediction < len(self._rf_model.class_names) else 'unknown',
                    '未知'
                ),
                'confidence': confidence,
                'probabilities': probs.tolist(),
                'inference_time_ms': inference_time * 1000
            }

            return result

        except Exception as e:
            self._log.error(f"[AIInference] 随机森林预测失败：{e}")
            return {
                'success': False,
                'error': str(e)
            }

    def predict_rf_with_uncertainty(self, spectrum: np.ndarray) -> Dict[str, Any]:
        """
        随机森林预测（带不确定性）

        Args:
            spectrum: 输入光谱

        Returns:
            预测结果（包含不确定性信息）
        """
        if not self._is_rf_loaded:
            return {
                'success': False,
                'error': '随机森林模型未加载',
                'prediction': -1,
                'confidence': 0.0,
                'uncertainty': 0.0
            }

        start_time = time.time()

        try:
            # 预处理
            spectrum_processed = self._preprocessor.preprocess(spectrum)

            # 特征提取
            features = self._feature_extractor.extract_all_features(spectrum_processed)
            features_array = np.array(features).reshape(1, -1)

            # 预测（带不确定性）
            results = self._rf_model.predict_with_uncertainty(features_array)
            result = results[0]

            inference_time = time.time() - start_time

            result['success'] = True
            result['class_name'] = self._rf_model.class_names[result['prediction']] if result['prediction'] < len(self._rf_model.class_names) else 'unknown'
            result['class_name_zh'] = self.CLASS_NAMES_ZH.get(
                self._rf_model.class_names[result['prediction']] if result['prediction'] < len(self._rf_model.class_names) else 'unknown',
                '未知'
            )
            result['inference_time_ms'] = inference_time * 1000

            return result

        except Exception as e:
            self._log.error(f"[AIInference] 随机森林预测失败：{e}")
            return {
                'success': False,
                'error': str(e)
            }

    def explain_rf(self, spectrum: np.ndarray, top_k: int = 5) -> Dict[str, Any]:
        """
        随机森林可解释性分析

        Args:
            spectrum: 输入光谱
            top_k: 返回前 k 个重要特征

        Returns:
            解释结果
        """
        if not self._is_rf_loaded:
            return {
                'success': False,
                'error': '随机森林模型未加载'
            }

        start_time = time.time()

        try:
            # 预处理
            spectrum_processed = self._preprocessor.preprocess(spectrum)

            # 特征提取
            features = self._feature_extractor.extract_all_features(spectrum_processed)
            features_array = np.array(features).reshape(1, -1)

            # 预测
            prediction = self._rf_model.predict(features_array)[0]
            probs = self._rf_model.predict_proba(features_array)[0]
            confidence = float(np.max(probs))

            # 获取特征重要性
            importances = self._rf_model.get_feature_importance()

            # 排序
            sorted_features = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:top_k]

            # 生成决策依据
            class_name = self._rf_model.class_names[prediction] if prediction < len(self._rf_model.class_names) else 'unknown'
            decision_basis = f"基于 {len(importances)} 个特征的随机森林分类，预测为 {class_name}，置信度 {confidence*100:.1f}%。"

            inference_time = time.time() - start_time

            result = {
                'success': True,
                'prediction': int(prediction),
                'class_name': class_name,
                'class_name_zh': self.CLASS_NAMES_ZH.get(class_name, '未知'),
                'confidence': confidence,
                'decision_basis': decision_basis,
                'top_contributions': [
                    {
                        'position': 0,  # 随机森林特征不是基于波数位置
                        'contribution': imp,
                        'intensity': 0,
                        'assignment': name
                    }
                    for name, imp in sorted_features
                ],
                'feature_importance': importances,
                'inference_time_ms': inference_time * 1000
            }

            return result

        except Exception as e:
            self._log.error(f"[AIInference] 随机森林解释失败：{e}")
            return {
                'success': False,
                'error': str(e)
            }
