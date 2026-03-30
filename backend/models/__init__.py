"""
AI 模型模块

提供 Transformer 物质识别模型、不确定性量化、可解释性分析、随机森林等功能
"""
from .transformer_model import (
    SpectralTransformer,
    TransformerConfig,
    create_transformer_model,
)
from .uncertainty import UncertaintyQuantifier
from .explainability import ExplainabilityAnalyzer

# 方案 A：随机森林模块
from .random_forest_features import (
    SpectrumPreprocessor,
    FeatureExtractor,
    FeatureSelector,
    extract_mineral_features,
    MINERAL_PEAKS,
)
from .random_forest_model import (
    RandomForestModel,
    RandomForestTrainer,
    train_random_forest,
)

__all__ = [
    # Transformer
    "SpectralTransformer",
    "TransformerConfig",
    "create_transformer_model",
    "UncertaintyQuantifier",
    "ExplainabilityAnalyzer",
    
    # 随机森林
    "SpectrumPreprocessor",
    "FeatureExtractor",
    "FeatureSelector",
    "extract_mineral_features",
    "MINERAL_PEAKS",
    "RandomForestModel",
    "RandomForestTrainer",
    "train_random_forest",
]
