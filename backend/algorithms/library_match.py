"""
谱库匹配算法模块

提供光谱库匹配功能，返回 Top K 匹配结果
"""
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging
import json

from .similarity import calculate_similarity

logger = logging.getLogger(__name__)


@dataclass
class LibraryMatchResult:
    """谱库匹配结果"""
    substance_id: str
    substance_name: str
    cas_number: str
    similarity: float
    rank: int
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.substance_id,
            "name": self.substance_name,
            "cas": self.cas_number,
            "similarity": self.similarity,
            "rank": self.rank,
            "description": self.description
        }


class SpectralLibrary:
    """光谱库管理类"""
    
    def __init__(self, library_path: Optional[str] = None):
        """
        初始化光谱库
        
        Args:
            library_path: 谱库目录路径
        """
        if library_path is None:
            # 默认路径
            library_path = Path(__file__).parent.parent / "library"
        
        self.library_path = Path(library_path)
        self.spectra: Dict[str, Dict[str, Any]] = {}
        self.index: Dict[str, str] = {}  # id -> name 映射
        
        self._load_index()
    
    def _load_index(self) -> None:
        """加载谱库索引"""
        index_file = self.library_path / "index.json"
        
        if not index_file.exists():
            logger.warning(f"谱库索引文件不存在：{index_file}")
            return
        
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for substance in data.get("substances", []):
                substance_id = substance.get("id")
                substance_name = substance.get("name")
                if substance_id:
                    self.index[substance_id] = substance_name or substance_id
            
            logger.info(f"加载谱库索引：{len(self.index)} 种物质")
            
        except Exception as e:
            logger.error(f"加载谱库索引失败：{e}")
    
    def load_spectrum(self, substance_id: str) -> Optional[Dict[str, Any]]:
        """
        加载指定物质的谱图数据
        
        Args:
            substance_id: 物质 ID
            
        Returns:
            谱图数据字典
        """
        if substance_id in self.spectra:
            return self.spectra[substance_id]
        
        spectrum_file = self.library_path / f"{substance_id}.json"
        
        if not spectrum_file.exists():
            logger.warning(f"谱图文件不存在：{spectrum_file}")
            return None
        
        try:
            with open(spectrum_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.spectra[substance_id] = data
            logger.debug(f"加载谱图：{substance_id}")
            return data
            
        except Exception as e:
            logger.error(f"加载谱图失败：{e}")
            return None
    
    def get_all_substance_ids(self) -> List[str]:
        """获取所有物质 ID"""
        return list(self.index.keys())


def match_library(
    spectrum: np.ndarray,
    wavenumbers: np.ndarray,
    library_path: Optional[str] = None,
    top_k: int = 5,
    similarity_method: str = 'cosine'
) -> List[LibraryMatchResult]:
    """
    谱库匹配
    
    将输入光谱与谱库中的标准谱图进行匹配，返回 Top K 匹配结果
    
    Args:
        spectrum: 输入光谱强度数据
        wavenumbers: 拉曼位移数组
        library_path: 谱库目录路径
        top_k: 返回前 K 个匹配结果
        similarity_method: 相似度计算方法
        
    Returns:
        谱库匹配结果列表
    """
    library = SpectralLibrary(library_path)
    results: List[LibraryMatchResult] = []
    
    # 获取所有物质 ID
    substance_ids = library.get_all_substance_ids()
    
    if len(substance_ids) == 0:
        logger.warning("谱库为空")
        return []
    
    # 对每种物质进行匹配
    for substance_id in substance_ids:
        spectrum_data = library.load_spectrum(substance_id)
        
        if spectrum_data is None:
            continue
        
        # 获取标准谱图
        reference_spectrum = spectrum_data.get("spectrum", None)
        
        # 如果没有完整谱图，使用峰值生成模拟谱图
        if reference_spectrum is None:
            reference_spectrum = _generate_spectrum_from_peaks(
                spectrum_data.get("peaks", []),
                wavenumbers
            )
        
        if reference_spectrum is None or len(reference_spectrum) != len(spectrum):
            logger.debug(f"跳过物质 {substance_id}：谱图不匹配")
            continue
        
        # 计算相似度
        similarity = calculate_similarity(
            spectrum,
            reference_spectrum,
            method=similarity_method
        )
        
        # 创建匹配结果
        result = LibraryMatchResult(
            substance_id=substance_id,
            substance_name=spectrum_data.get("name", substance_id),
            cas_number=spectrum_data.get("cas", "N/A"),
            similarity=similarity,
            rank=0,  # 稍后排序
            description=spectrum_data.get("description", "")
        )
        
        results.append(result)
    
    # 按相似度排序
    results.sort(key=lambda x: x.similarity, reverse=True)
    
    # 设置排名并返回 Top K
    for i, result in enumerate(results[:top_k]):
        result.rank = i + 1
    
    logger.info(f"谱库匹配完成：Top {top_k}, 最佳匹配={results[0].substance_name if results else 'N/A'} "
                f"(相似度={results[0].similarity:.3f} if results else 0)")
    
    return results[:top_k]


def _generate_spectrum_from_peaks(
    peaks: List[Dict[str, Any]],
    wavenumbers: np.ndarray
) -> Optional[np.ndarray]:
    """
    从峰值数据生成模拟谱图
    
    Args:
        peaks: 峰值列表 [{"position": x, "intensity": y, "width": w}, ...]
        wavenumbers: 波长数组
        
    Returns:
        生成的谱图数据
    """
    if not peaks or len(wavenumbers) == 0:
        return None
    
    spectrum = np.zeros(len(wavenumbers))
    
    for peak in peaks:
        position = peak.get("position", 0)
        intensity = peak.get("intensity", 1.0)
        width = peak.get("width", 20)
        
        # 高斯峰模拟
        if width <= 0:
            width = 20
        
        gaussian = intensity * np.exp(-((wavenumbers - position) ** 2) / (2 * width ** 2))
        spectrum += gaussian
    
    # 添加少量噪声
    noise = np.random.normal(0, 0.01, len(spectrum))
    spectrum += noise
    
    # 确保非负
    spectrum = np.maximum(spectrum, 0)
    
    return spectrum


def format_match_results(results: List[LibraryMatchResult]) -> List[Dict[str, Any]]:
    """
    格式化匹配结果为字典列表
    
    Args:
        results: 匹配结果列表
        
    Returns:
        字典格式的匹配结果
    """
    return [result.to_dict() for result in results]
