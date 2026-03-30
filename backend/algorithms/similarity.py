"""
相似度计算算法模块

提供余弦相似度、相关系数等光谱相似度计算方法
"""
import numpy as np
from typing import Union
import logging

logger = logging.getLogger(__name__)


def cosine_similarity(
    spectrum1: np.ndarray,
    spectrum2: np.ndarray
) -> float:
    """
    计算两个光谱的余弦相似度

    Args:
        spectrum1: 光谱 1
        spectrum2: 光谱 2

    Returns:
        余弦相似度 (0-1)
    """
    if len(spectrum1) != len(spectrum2):
        logger.error("光谱长度不匹配")
        return 0.0
    
    if len(spectrum1) == 0:
        return 0.0
    
    # 计算余弦相似度
    dot_product = np.dot(spectrum1, spectrum2)
    norm1 = np.linalg.norm(spectrum1)
    norm2 = np.linalg.norm(spectrum2)
    
    if norm1 < 1e-10 or norm2 < 1e-10:
        return 0.0
    
    similarity = dot_product / (norm1 * norm2)
    
    # 确保在 [0, 1] 范围内
    similarity = float(np.clip(similarity, 0.0, 1.0))
    
    logger.debug(f"余弦相似度：{similarity:.4f}")
    return similarity


def correlation_coefficient(
    spectrum1: np.ndarray,
    spectrum2: np.ndarray
) -> float:
    """
    计算两个光谱的皮尔逊相关系数

    Args:
        spectrum1: 光谱 1
        spectrum2: 光谱 2

    Returns:
        相关系数 (-1 到 1)
    """
    if len(spectrum1) != len(spectrum2):
        logger.error("光谱长度不匹配")
        return 0.0
    
    if len(spectrum1) == 0:
        return 0.0
    
    # 计算均值
    mean1 = np.mean(spectrum1)
    mean2 = np.mean(spectrum2)
    
    # 中心化
    centered1 = spectrum1 - mean1
    centered2 = spectrum2 - mean2
    
    # 计算相关系数
    numerator = np.sum(centered1 * centered2)
    denominator = np.sqrt(np.sum(centered1**2) * np.sum(centered2**2))
    
    if denominator < 1e-10:
        return 0.0
    
    correlation = numerator / denominator
    
    logger.debug(f"皮尔逊相关系数：{correlation:.4f}")
    return float(correlation)


def euclidean_distance(
    spectrum1: np.ndarray,
    spectrum2: np.ndarray
) -> float:
    """
    计算两个光谱的欧几里得距离

    Args:
        spectrum1: 光谱 1
        spectrum2: 光谱 2

    Returns:
        欧几里得距离
    """
    if len(spectrum1) != len(spectrum2):
        logger.error("光谱长度不匹配")
        return float('inf')
    
    distance = float(np.linalg.norm(spectrum1 - spectrum2))
    logger.debug(f"欧几里得距离：{distance:.4f}")
    return distance


def spectral_angle_mapper(
    spectrum1: np.ndarray,
    spectrum2: np.ndarray
) -> float:
    """
    计算光谱角制图 (SAM) 角度

    Args:
        spectrum1: 光谱 1
        spectrum2: 光谱 2

    Returns:
        光谱角度 (弧度)
    """
    if len(spectrum1) != len(spectrum2):
        logger.error("光谱长度不匹配")
        return float('inf')
    
    dot_product = np.dot(spectrum1, spectrum2)
    norm1 = np.linalg.norm(spectrum1)
    norm2 = np.linalg.norm(spectrum2)
    
    if norm1 < 1e-10 or norm2 < 1e-10:
        return float('inf')
    
    # 计算角度
    cos_angle = dot_product / (norm1 * norm2)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    angle = np.arccos(cos_angle)
    
    logger.debug(f"SAM 角度：{np.degrees(angle):.2f}°")
    return float(angle)


def calculate_similarity(
    spectrum1: np.ndarray,
    spectrum2: np.ndarray,
    method: str = 'cosine'
) -> float:
    """
    计算光谱相似度统一接口

    Args:
        spectrum1: 光谱 1
        spectrum2: 光谱 2
        method: 计算方法 ('cosine', 'correlation', 'euclidean', 'sam')

    Returns:
        相似度值 (对于距离类方法，转换为 0-1 范围)
    """
    if method == 'cosine':
        return cosine_similarity(spectrum1, spectrum2)
    elif method == 'correlation':
        return correlation_coefficient(spectrum1, spectrum2)
    elif method == 'euclidean':
        # 将距离转换为相似度
        distance = euclidean_distance(spectrum1, spectrum2)
        return 1.0 / (1.0 + distance)
    elif method == 'sam':
        # 将角度转换为相似度
        angle = spectral_angle_mapper(spectrum1, spectrum2)
        if np.isinf(angle):
            return 0.0
        return 1.0 - (angle / np.pi)
    else:
        logger.warning(f"未知相似度计算方法：{method}，使用余弦相似度")
        return cosine_similarity(spectrum1, spectrum2)
