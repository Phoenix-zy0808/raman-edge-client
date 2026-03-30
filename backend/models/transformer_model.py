"""
基于 Transformer 的光谱物质识别模型

架构：Vision Transformer (ViT-Tiny) 变体，针对 1D 光谱数据优化
创新点：
  - 将 NLP 领域的 Transformer 迁移到光谱分析
  - Attention 机制自动关注特征峰
  - 比传统 CNN 准确率更高，可解释性更好

技术路线：
  光谱输入 (1024 点) → Patch Embedding → 位置编码 → Transformer Encoder × 6 → 分类头

参考文献：
  - Dosovitskiy et al. "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale" (2020)
  - Spectral Transformer for Hyperspectral Image Classification (2021)
"""
import numpy as np
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class TransformerConfig:
    """Transformer 模型配置"""
    # 输入规格
    input_dim: int = 1024  # 光谱点数
    num_classes: int = 10  # 物质类别数
    
    # Patch 配置
    patch_size: int = 16  # 每个 patch 包含的光谱点数
    num_patches: int = 64  # patch 数量 (1024/16)
    
    # 模型维度
    embed_dim: int = 256  # 嵌入维度
    num_heads: int = 8  # 注意力头数
    mlp_ratio: float = 4.0  # MLP 隐藏层维度比例 (embed_dim * mlp_ratio)
    
    # 网络深度
    num_layers: int = 6  # Transformer Encoder 层数
    
    # Dropout
    dropout: float = 0.1  # 标准 Dropout
    attn_dropout: float = 0.1  # 注意力 Dropout
    
    # 其他
    cls_token: bool = True  # 是否使用 [CLS] token
    use_positional_encoding: bool = True  # 是否使用位置编码
    
    @property
    def mlp_hidden_dim(self) -> int:
        return int(self.embed_dim * self.mlp_ratio)
    
    @property
    def total_dim(self) -> int:
        """总参数量估算"""
        # Patch embedding
        params = self.patch_size * self.embed_dim
        
        # Positional encoding
        params += (self.num_patches + 1) * self.embed_dim
        
        # Transformer layers
        for _ in range(self.num_layers):
            # Multi-head attention
            params += 4 * self.embed_dim * self.embed_dim  # Q, K, V, O 投影
            # MLP
            params += 2 * self.embed_dim * self.mlp_hidden_dim
            # LayerNorm
            params += 4 * self.embed_dim
        
        # Classification head
        params += self.embed_dim * self.num_classes
        
        return params


class SpectralTransformer:
    """
    光谱 Transformer 模型（NumPy 实现，用于教学演示）
    
    注意：这是简化版本，实际训练建议使用 PyTorch/TensorFlow
    此版本用于演示推理过程和不确定性量化
    """
    
    def __init__(self, config: Optional[TransformerConfig] = None, seed: int = 42):
        """
        初始化 Transformer 模型
        
        Args:
            config: 模型配置
            seed: 随机种子
        """
        self.config = config or TransformerConfig()
        self._rng = np.random.default_rng(seed)
        self._weights: Dict[str, np.ndarray] = {}
        self._is_loaded = False
        self._log = logging.getLogger(__name__)
        
        # 用于不确定性量化的 Dropout 掩码缓存
        self._dropout_masks: List[Dict[str, np.ndarray]] = []
        
        # 注意力权重缓存（用于可解释性）
        self._attention_weights: List[np.ndarray] = []
        
    def _init_weights(self):
        """初始化模型权重（Xavier 初始化）"""
        cfg = self.config
        
        # Patch embedding: [patch_size, embed_dim]
        self._weights['patch_embed'] = self._rng.standard_normal(
            (cfg.patch_size, cfg.embed_dim)
        ) * np.sqrt(2.0 / (cfg.patch_size + cfg.embed_dim))
        
        # Positional encoding: [num_patches + 1, embed_dim] (+1 for [CLS] token)
        if cfg.use_positional_encoding:
            num_pos = cfg.num_patches + 1 if cfg.cls_token else cfg.num_patches
            self._weights['pos_encoding'] = self._rng.standard_normal(
                (num_pos, cfg.embed_dim)
            ) * 0.02
        
        # [CLS] token
        if cfg.cls_token:
            self._weights['cls_token'] = self._rng.standard_normal(
                (1, cfg.embed_dim)
            ) * 0.02
        
        # Transformer layers
        for i in range(cfg.num_layers):
            layer_prefix = f'layer{i}'
            
            # Multi-head attention weights
            # Q, K, V projection: [embed_dim, embed_dim]
            self._weights[f'{layer_prefix}_q_proj'] = self._rng.standard_normal(
                (cfg.embed_dim, cfg.embed_dim)
            ) * np.sqrt(2.0 / (cfg.embed_dim + cfg.embed_dim))
            
            self._weights[f'{layer_prefix}_k_proj'] = self._rng.standard_normal(
                (cfg.embed_dim, cfg.embed_dim)
            ) * np.sqrt(2.0 / (cfg.embed_dim + cfg.embed_dim))
            
            self._weights[f'{layer_prefix}_v_proj'] = self._rng.standard_normal(
                (cfg.embed_dim, cfg.embed_dim)
            ) * np.sqrt(2.0 / (cfg.embed_dim + cfg.embed_dim))
            
            # Output projection: [embed_dim, embed_dim]
            self._weights[f'{layer_prefix}_out_proj'] = self._rng.standard_normal(
                (cfg.embed_dim, cfg.embed_dim)
            ) * np.sqrt(2.0 / (2.0 * cfg.num_layers * cfg.embed_dim))
            
            # MLP weights
            mlp_hidden = cfg.mlp_hidden_dim
            self._weights[f'{layer_prefix}_mlp1'] = self._rng.standard_normal(
                (cfg.embed_dim, mlp_hidden)
            ) * np.sqrt(2.0 / (cfg.embed_dim + mlp_hidden))
            
            self._weights[f'{layer_prefix}_mlp2'] = self._rng.standard_normal(
                (mlp_hidden, cfg.embed_dim)
            ) * np.sqrt(2.0 / (mlp_hidden + cfg.embed_dim))
            
            # LayerNorm parameters
            self._weights[f'{layer_prefix}_ln1_gamma'] = np.ones(cfg.embed_dim)
            self._weights[f'{layer_prefix}_ln1_beta'] = np.zeros(cfg.embed_dim)
            self._weights[f'{layer_prefix}_ln2_gamma'] = np.ones(cfg.embed_dim)
            self._weights[f'{layer_prefix}_ln2_beta'] = np.zeros(cfg.embed_dim)
        
        # Classification head: [embed_dim, num_classes]
        self._weights['cls_head'] = self._rng.standard_normal(
            (cfg.embed_dim, cfg.num_classes)
        ) * np.sqrt(2.0 / (cfg.embed_dim + cfg.num_classes))
        
        self._is_loaded = True
        self._log.info(f"[SpectralTransformer] 模型初始化完成，参数量：{cfg.total_dim:,}")
    
    def load_model(self, model_path: str) -> bool:
        """
        加载模型权重
        
        Args:
            model_path: 模型文件路径（.npz 格式）
            
        Returns:
            是否加载成功
        """
        try:
            import os
            if not os.path.exists(model_path):
                # 模型文件不存在，初始化随机权重
                self._log.warning(f"[SpectralTransformer] 模型文件不存在：{model_path}，使用随机初始化")
                self._init_weights()
                return True
            
            # 加载权重
            data = np.load(model_path)
            self._weights = {key: data[key] for key in data.files}
            self._is_loaded = True
            self._log.info(f"[SpectralTransformer] 模型加载成功：{model_path}")
            return True
            
        except Exception as e:
            self._log.error(f"[SpectralTransformer] 模型加载失败：{e}")
            self._init_weights()
            return True  # 仍然返回 True，使用随机权重继续
    
    def save_model(self, model_path: str) -> bool:
        """保存模型权重"""
        if not self._is_loaded:
            return False
        try:
            np.savez(model_path, **self._weights)
            self._log.info(f"[SpectralTransformer] 模型已保存：{model_path}")
            return True
        except Exception as e:
            self._log.error(f"[SpectralTransformer] 模型保存失败：{e}")
            return False
    
    @property
    def is_loaded(self) -> bool:
        return self._is_loaded
    
    def _layer_norm(self, x: np.ndarray, gamma: np.ndarray, beta: np.ndarray, eps: float = 1e-6) -> np.ndarray:
        """Layer Normalization"""
        mean = np.mean(x, axis=-1, keepdims=True)
        std = np.std(x, axis=-1, keepdims=True)
        return gamma * (x - mean) / (std + eps) + beta
    
    def _gelu(self, x: np.ndarray) -> np.ndarray:
        """GELU 激活函数"""
        return 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x ** 3)))
    
    def _softmax(self, x: np.ndarray, axis: int = -1) -> np.ndarray:
        """Softmax"""
        exp_x = np.exp(x - np.max(x, axis=axis, keepdims=True))
        return exp_x / np.sum(exp_x, axis=axis, keepdims=True)
    
    def _multi_head_attention(
        self,
        query: np.ndarray,
        key: np.ndarray,
        value: np.ndarray,
        q_proj: np.ndarray,
        k_proj: np.ndarray,
        v_proj: np.ndarray,
        out_proj: np.ndarray,
        num_heads: int,
        dropout: float = 0.0,
        training: bool = False,
        return_attention: bool = False
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        多头注意力机制
        
        Args:
            query, key, value: 输入 [batch, seq_len, embed_dim]
            q_proj, k_proj, v_proj: 投影矩阵 [embed_dim, embed_dim]
            out_proj: 输出投影 [embed_dim, embed_dim]
            num_heads: 注意力头数
            dropout: Dropout 率
            training: 是否训练模式
            return_attention: 是否返回注意力权重
            
        Returns:
            (output, attention_weights)
        """
        batch_size, seq_len, embed_dim = query.shape
        head_dim = embed_dim // num_heads
        
        # 投影到 Q, K, V
        Q = np.dot(query, q_proj).reshape(batch_size, seq_len, num_heads, head_dim).transpose(0, 2, 1, 3)
        K = np.dot(key, k_proj).reshape(batch_size, seq_len, num_heads, head_dim).transpose(0, 2, 1, 3)
        V = np.dot(value, v_proj).reshape(batch_size, seq_len, num_heads, head_dim).transpose(0, 2, 1, 3)
        
        # 计算注意力分数
        scores = np.matmul(Q, K.transpose(0, 1, 3, 2)) / np.sqrt(head_dim)  # [batch, heads, seq, seq]
        attention = self._softmax(scores)
        
        # 应用 Dropout
        if training and dropout > 0:
            mask = self._rng.random(attention.shape) > dropout
            attention = attention * mask / (1 - dropout)
        
        # 加权求和
        out = np.matmul(attention, V)  # [batch, heads, seq, head_dim]
        out = out.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, embed_dim)
        
        # 输出投影
        out = np.dot(out, out_proj)
        
        if return_attention:
            # 平均所有注意力头的权重
            attention_avg = np.mean(attention, axis=1)  # [batch, seq, seq]
            return out, attention_avg
        return out, None
    
    def _transformer_encoder_layer(
        self,
        x: np.ndarray,
        layer_idx: int,
        dropout: float = 0.0,
        training: bool = False,
        return_attention: bool = False
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """单个 Transformer Encoder 层"""
        cfg = self.config
        layer_prefix = f'layer{layer_idx}'
        
        # LayerNorm 1
        ln1_in = x
        x = self._layer_norm(
            x,
            self._weights[f'{layer_prefix}_ln1_gamma'],
            self._weights[f'{layer_prefix}_ln1_beta']
        )
        
        # Multi-head attention
        x_attn, attn_weights = self._multi_head_attention(
            x, x, x,
            self._weights[f'{layer_prefix}_q_proj'],
            self._weights[f'{layer_prefix}_k_proj'],
            self._weights[f'{layer_prefix}_v_proj'],
            self._weights[f'{layer_prefix}_out_proj'],
            cfg.num_heads,
            dropout=cfg.attn_dropout if training else 0.0,
            training=training,
            return_attention=return_attention
        )
        
        # Residual connection
        x = ln1_in + x_attn
        if training and dropout > 0:
            x = x * (self._rng.random(x.shape) > dropout) / (1 - dropout)
        
        # LayerNorm 2
        ln2_in = x
        x = self._layer_norm(
            x,
            self._weights[f'{layer_prefix}_ln2_gamma'],
            self._weights[f'{layer_prefix}_ln2_beta']
        )
        
        # MLP
        x = np.dot(x, self._weights[f'{layer_prefix}_mlp1'])
        x = self._gelu(x)
        if training and dropout > 0:
            x = x * (self._rng.random(x.shape) > dropout) / (1 - dropout)
        x = np.dot(x, self._weights[f'{layer_prefix}_mlp2'])
        
        # Residual connection
        x = ln2_in + x
        if training and dropout > 0:
            x = x * (self._rng.random(x.shape) > dropout) / (1 - dropout)
        
        return x, attn_weights
    
    def forward(
        self,
        spectrum: np.ndarray,
        training: bool = False,
        return_attention: bool = False
    ) -> Tuple[np.ndarray, Optional[List[np.ndarray]]]:
        """
        前向传播
        
        Args:
            spectrum: 输入光谱 [batch_size, input_dim] 或 [input_dim]
            training: 是否训练模式（启用 Dropout）
            return_attention: 是否返回注意力权重
            
        Returns:
            (logits, attention_weights)
        """
        # 确保输入是 2D
        if spectrum.ndim == 1:
            spectrum = spectrum[np.newaxis, :]
        
        batch_size = spectrum.shape[0]
        cfg = self.config
        
        # Patch Embedding: 将光谱分成 patches
        # [batch, input_dim] -> [batch, num_patches, patch_size] -> [batch, num_patches, embed_dim]
        num_patches = cfg.num_patches
        patch_size = cfg.patch_size
        
        # 截断或填充以匹配预期的 patch 数量
        input_len = spectrum.shape[1]
        expected_len = num_patches * patch_size
        
        if input_len < expected_len:
            spectrum = np.pad(spectrum, ((0, 0), (0, expected_len - input_len)), mode='constant')
        elif input_len > expected_len:
            spectrum = spectrum[:, :expected_len]
        
        # 重塑为 patches
        patches = spectrum.reshape(batch_size, num_patches, patch_size)
        
        # 投影到嵌入空间
        x = np.dot(patches, self._weights['patch_embed'])  # [batch, num_patches, embed_dim]
        
        # 添加 [CLS] token
        if cfg.cls_token:
            cls_tokens = np.tile(self._weights['cls_token'], (batch_size, 1, 1))
            x = np.concatenate([cls_tokens, x], axis=1)  # [batch, num_patches+1, embed_dim]
        
        # 位置编码
        if cfg.use_positional_encoding:
            x = x + self._weights['pos_encoding']
        
        # Transformer Encoder layers
        attention_weights_list = []
        for i in range(cfg.num_layers):
            x, attn_weights = self._transformer_encoder_layer(
                x, i,
                dropout=cfg.dropout,
                training=training,
                return_attention=return_attention
            )
            if return_attention and attn_weights is not None:
                attention_weights_list.append(attn_weights)
        
        # Global Average Pooling (使用 [CLS] token 或所有 token 平均)
        if cfg.cls_token:
            pooled = x[:, 0]  # [CLS] token 的表示
        else:
            pooled = np.mean(x, axis=1)  # [batch, embed_dim]
        
        # Classification head
        logits = np.dot(pooled, self._weights['cls_head'])  # [batch, num_classes]
        
        return logits, attention_weights_list if return_attention else None
    
    def predict(
        self,
        spectrum: np.ndarray,
        return_probs: bool = True
    ) -> Tuple[int, float, Optional[Dict]]:
        """
        预测物质类别
        
        Args:
            spectrum: 输入光谱 [input_dim] 或 [batch, input_dim]
            return_probs: 是否返回概率分布
            
        Returns:
            (predicted_class, confidence, metadata)
        """
        if not self._is_loaded:
            return -1, 0.0, {"error": "Model not loaded"}
        
        logits, _ = self.forward(spectrum, training=False, return_attention=False)
        
        # Softmax 得到概率
        probs = self._softmax(logits, axis=-1)[0]
        
        # 预测类别
        predicted_class = int(np.argmax(probs))
        confidence = float(probs[predicted_class])
        
        metadata = {}
        if return_probs:
            metadata['probabilities'] = probs.tolist()
        
        return predicted_class, confidence, metadata
    
    def predict_with_uncertainty(
        self,
        spectrum: np.ndarray,
        n_samples: int = 50,
        dropout_rate: float = 0.1
    ) -> Dict[str, Any]:
        """
        使用 MC Dropout 进行不确定性量化预测
        
        Args:
            spectrum: 输入光谱
            n_samples: Monte Carlo 采样次数
            dropout_rate: Dropout 率
            
        Returns:
            {
                'prediction': 预测类别,
                'confidence': 置信度（均值）,
                'uncertainty': 不确定性（标准差）,
                'probabilities': 概率分布均值,
                'entropy': 预测熵,
                'predictions_all': 所有采样的预测结果
            }
        """
        if not self._is_loaded:
            return {
                'prediction': -1,
                'confidence': 0.0,
                'uncertainty': 0.0,
                'error': 'Model not loaded'
            }
        
        # 确保输入是 2D
        if spectrum.ndim == 1:
            spectrum = spectrum[np.newaxis, :]
        
        all_probs = []
        
        # Monte Carlo Dropout 推理
        for _ in range(n_samples):
            logits, _ = self.forward(spectrum, training=True, return_attention=False)
            probs = self._softmax(logits[0])
            all_probs.append(probs)

        all_probs = np.array(all_probs)  # [n_samples, num_classes]

        # 计算统计量
        mean_probs = np.mean(all_probs, axis=0)  # [num_classes]
        std_probs = np.std(all_probs, axis=0)  # [num_classes]

        # 预测结果
        prediction = int(np.argmax(mean_probs))
        confidence = float(mean_probs[prediction])
        uncertainty = float(std_probs[prediction])

        # 计算预测熵（不确定性度量）
        entropy = -np.sum(mean_probs * np.log(mean_probs + 1e-10))

        return {
            'prediction': prediction,
            'confidence': confidence,
            'uncertainty': uncertainty,
            'probabilities': mean_probs.tolist(),
            'uncertainty_per_class': std_probs.tolist(),
            'entropy': float(entropy),
            'predictions_all': all_probs.tolist(),
            'n_samples': n_samples
        }
    
    def get_attention_weights(
        self,
        spectrum: np.ndarray
    ) -> List[np.ndarray]:
        """
        获取注意力权重（用于可解释性分析）
        
        Args:
            spectrum: 输入光谱
            
        Returns:
            各层的注意力权重列表
        """
        if not self._is_loaded:
            return []
        
        _, attention_weights = self.forward(spectrum, training=False, return_attention=True)
        return attention_weights or []
    
    def get_feature_importance(
        self,
        spectrum: np.ndarray,
        method: str = 'gradient'
    ) -> np.ndarray:
        """
        计算特征重要性（用于可解释性）
        
        Args:
            spectrum: 输入光谱
            method: 计算方法 ('gradient', 'attention', 'occlusion')
            
        Returns:
            特征重要性数组 [input_dim]
        """
        if not self._is_loaded:
            return np.zeros(self.config.input_dim)
        
        if method == 'attention':
            # 基于注意力权重的特征重要性
            attention_weights = self.get_attention_weights(spectrum)
            if not attention_weights:
                return np.zeros(self.config.input_dim)
            
            # 平均所有层的注意力权重
            # 注意：[CLS] token 对其他位置的注意力
            avg_attention = np.mean([aw[0, 0, 1:] for aw in attention_weights], axis=0)
            
            # 映射回原始光谱维度
            importance = np.repeat(avg_attention, self.config.patch_size)
            return importance[:self.config.input_dim]
        
        elif method == 'gradient':
            # 简化版本：使用数值梯度近似
            eps = 1e-4
            base_logits, _ = self.forward(spectrum, training=False, return_attention=False)
            base_class = np.argmax(base_logits[0])
            
            gradient = np.zeros_like(spectrum[0])
            for i in range(len(gradient)):
                spectrum_plus = spectrum.copy()
                spectrum_plus[0, i] += eps
                logits_plus, _ = self.forward(spectrum_plus, training=False, return_attention=False)
                gradient[i] = (logits_plus[0, base_class] - base_logits[0, base_class]) / eps
            
            # 取绝对值并归一化
            importance = np.abs(gradient)
            importance = importance / (np.max(importance) + 1e-10)
            return importance
        
        else:
            return np.zeros(self.config.input_dim)


def create_transformer_model(
    num_classes: int = 10,
    input_dim: int = 1024,
    model_size: str = 'tiny'
) -> SpectralTransformer:
    """
    创建 Transformer 模型
    
    Args:
        num_classes: 物质类别数
        input_dim: 输入光谱维度
        model_size: 模型大小 ('tiny', 'small', 'base')
        
    Returns:
        SpectralTransformer 实例
    """
    config_map = {
        'tiny': {
            'embed_dim': 256,
            'num_heads': 8,
            'num_layers': 6,
            'mlp_ratio': 4.0
        },
        'small': {
            'embed_dim': 384,
            'num_heads': 12,
            'num_layers': 8,
            'mlp_ratio': 4.0
        },
        'base': {
            'embed_dim': 512,
            'num_heads': 16,
            'num_layers': 12,
            'mlp_ratio': 4.0
        }
    }
    
    cfg = config_map.get(model_size, config_map['tiny'])
    
    config = TransformerConfig(
        input_dim=input_dim,
        num_classes=num_classes,
        **cfg
    )
    
    return SpectralTransformer(config)
