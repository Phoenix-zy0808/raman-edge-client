"""
随机森林模型训练与评估模块

方案 A：随机森林 + 特征工程（小样本快速方案）

功能：
1. 模型训练与超参数调优
2. 交叉验证评估
3. 概率校准（Platt Scaling / Isotonic Regression）
4. 模型保存与加载

作者：P11 级全栈工程师
日期：2026-03-29
"""
import numpy as np
import pickle
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RandomForestModel:
    """随机森林分类模型"""
    
    def __init__(self, n_estimators: int = 100, max_depth: int = 10,
                 min_samples_split: int = 5, min_samples_leaf: int = 2,
                 random_state: int = 42):
        """
        初始化随机森林模型
        
        Args:
            n_estimators: 树的数量
            max_depth: 最大深度
            min_samples_split: 内部节点再划分所需最小样本数
            min_samples_leaf: 叶节点所需最小样本数
            random_state: 随机种子
        """
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.random_state = random_state
        
        self.model = None
        self.calibrated_model = None
        self.feature_names: List[str] = []
        self.class_names: List[str] = []
        self.is_trained = False
        self.is_calibrated = False
        
        self._log = logging.getLogger(__name__)
        self.training_history: Dict[str, Any] = {}
    
    def fit(self, X: np.ndarray, y: np.ndarray,
            feature_names: List[str],
            class_names: List[str],
            X_val: Optional[np.ndarray] = None,
            y_val: Optional[np.ndarray] = None) -> Dict[str, float]:
        """
        训练模型
        
        Args:
            X: 特征矩阵 [N, M]
            y: 标签 [N]
            feature_names: 特征名称列表
            class_names: 类别名称列表
            X_val: 验证集特征（可选）
            y_val: 验证集标签（可选）
            
        Returns:
            训练结果字典
        """
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        except ImportError:
            self._log.error("sklearn 未安装")
            raise ImportError("请安装 sklearn: pip install scikit-learn")
        
        self._log.info(f"开始训练随机森林...")
        self._log.info(f"训练样本数：{len(X)}, 特征数：{X.shape[1]}")
        
        self.feature_names = feature_names
        self.class_names = class_names
        
        # 初始化模型
        self.model = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            min_samples_leaf=self.min_samples_leaf,
            random_state=self.random_state,
            n_jobs=-1
        )
        
        # 训练
        self.model.fit(X, y)
        self.is_trained = True
        
        # 评估
        y_pred_train = self.model.predict(X)
        train_acc = accuracy_score(y, y_pred_train)
        
        results = {
            'train_accuracy': train_acc,
            'n_estimators': self.n_estimators,
            'max_depth': self.max_depth,
            'n_features': X.shape[1],
            'n_classes': len(class_names)
        }
        
        # 验证集评估（如果提供）
        if X_val is not None and y_val is not None:
            y_pred_val = self.model.predict(X_val)
            val_acc = accuracy_score(y_val, y_pred_val)
            val_precision = precision_score(y_val, y_pred_val, average='weighted', zero_division=0)
            val_recall = recall_score(y_val, y_pred_val, average='weighted', zero_division=0)
            val_f1 = f1_score(y_val, y_pred_val, average='weighted', zero_division=0)
            
            results.update({
                'val_accuracy': val_acc,
                'val_precision': val_precision,
                'val_recall': val_recall,
                'val_f1': val_f1
            })
            
            self._log.info(f"验证集准确率：{val_acc:.4f}")
        
        self._log.info(f"训练集准确率：{train_acc:.4f}")
        
        # 记录训练历史
        self.training_history = {
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'hyperparams': {
                'n_estimators': self.n_estimators,
                'max_depth': self.max_depth,
                'min_samples_split': self.min_samples_split,
                'min_samples_leaf': self.min_samples_leaf
            }
        }
        
        return results
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测类别"""
        if not self.is_trained:
            raise ValueError("模型未训练")
        return self.model.predict(X)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """预测概率"""
        if not self.is_trained:
            raise ValueError("模型未训练")
        return self.model.predict_proba(X)
    
    def calibrate(self, X: np.ndarray, y: np.ndarray,
                  method: str = 'isotonic', cv: int = 5) -> Dict[str, float]:
        """
        校准概率
        
        Args:
            X: 特征矩阵
            y: 标签
            method: 校准方法 ('isotonic' 或 'sigmoid')
            cv: 交叉验证折数
            
        Returns:
            校准结果
        """
        try:
            from sklearn.calibration import CalibratedClassifierCV
            from sklearn.metrics import brier_score_loss
        except ImportError:
            self._log.error("sklearn 未安装")
            raise ImportError("请安装 sklearn: pip install scikit-learn")
        
        self._log.info(f"开始校准概率（方法：{method}）...")
        
        # 校准
        self.calibrated_model = CalibratedClassifierCV(
            self.model,
            method=method,
            cv=cv
        )
        
        self.calibrated_model.fit(X, y)
        self.is_calibrated = True
        
        # 评估校准质量
        probs_calibrated = self.calibrated_model.predict_proba(X)
        y_pred_calibrated = probs_calibrated.argmax(axis=1)
        
        from sklearn.metrics import accuracy_score
        cal_acc = accuracy_score(y, y_pred_calibrated)
        
        # 计算 Brier Score（校准误差）
        # 对于多分类，计算每个类的 Brier Score 然后平均
        n_classes = len(self.class_names)
        brier_scores = []
        for c in range(n_classes):
            y_binary = (y == c).astype(int)
            probs_binary = probs_calibrated[:, c]
            brier = brier_score_loss(y_binary, probs_binary)
            brier_scores.append(brier)
        
        avg_brier = np.mean(brier_scores)
        
        results = {
            'calibration_accuracy': cal_acc,
            'avg_brier_score': avg_brier,
            'method': method,
            'cv_folds': cv
        }
        
        self._log.info(f"校准后准确率：{cal_acc:.4f}")
        self._log.info(f"平均 Brier Score: {avg_brier:.4f}")
        
        return results
    
    def predict_with_uncertainty(self, X: np.ndarray) -> List[Dict[str, Any]]:
        """
        预测并返回不确定性
        
        Args:
            X: 特征矩阵
            
        Returns:
            预测结果列表（包含不确定性信息）
        """
        if not self.is_trained:
            raise ValueError("模型未训练")
        
        # 使用校准后的模型（如果可用）
        if self.is_calibrated and self.calibrated_model is not None:
            probs = self.calibrated_model.predict_proba(X)
        else:
            probs = self.model.predict_proba(X)
        
        predictions = []
        for i in range(len(X)):
            pred = int(np.argmax(probs[i]))
            confidence = float(probs[i, pred])
            uncertainty = 1.0 - confidence
            
            # 计算熵
            from scipy.stats import entropy
            ent = entropy(probs[i])
            
            predictions.append({
                'prediction': pred,
                'class_name': self.class_names[pred] if pred < len(self.class_names) else 'unknown',
                'confidence': confidence,
                'uncertainty': uncertainty,
                'entropy': ent,
                'probabilities': probs[i].tolist()
            })
        
        return predictions
    
    def get_feature_importance(self) -> Dict[str, float]:
        """获取特征重要性"""
        if not self.is_trained:
            raise ValueError("模型未训练")
        
        importances = self.model.feature_importances_
        
        return {
            name: float(imp)
            for name, imp in zip(self.feature_names, importances)
        }
    
    def save(self, model_path: str):
        """保存模型"""
        path = Path(model_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'model': self.model,
            'calibrated_model': self.calibrated_model,
            'feature_names': self.feature_names,
            'class_names': self.class_names,
            'is_trained': self.is_trained,
            'is_calibrated': self.is_calibrated,
            'hyperparams': {
                'n_estimators': self.n_estimators,
                'max_depth': self.max_depth,
                'min_samples_split': self.min_samples_split,
                'min_samples_leaf': self.min_samples_leaf,
                'random_state': self.random_state
            },
            'training_history': self.training_history
        }
        
        with open(path, 'wb') as f:
            pickle.dump(data, f)
        
        self._log.info(f"模型已保存：{model_path}")
    
    def load(self, model_path: str):
        """加载模型"""
        path = Path(model_path)
        
        if not path.exists():
            raise FileNotFoundError(f"模型文件不存在：{model_path}")
        
        with open(path, 'rb') as f:
            data = pickle.load(f)
        
        self.model = data['model']
        self.calibrated_model = data.get('calibrated_model')
        self.feature_names = data['feature_names']
        self.class_names = data['class_names']
        self.is_trained = data['is_trained']
        self.is_calibrated = data.get('is_calibrated', False)
        
        hyperparams = data.get('hyperparams', {})
        self.n_estimators = hyperparams.get('n_estimators', 100)
        self.max_depth = hyperparams.get('max_depth', 10)
        self.min_samples_split = hyperparams.get('min_samples_split', 5)
        self.min_samples_leaf = hyperparams.get('min_samples_leaf', 2)
        self.random_state = hyperparams.get('random_state', 42)
        
        self.training_history = data.get('training_history', {})
        
        self._log.info(f"模型已加载：{model_path}")


class RandomForestTrainer:
    """随机森林训练器（支持网格搜索和交叉验证）"""
    
    def __init__(self, random_state: int = 42):
        """初始化训练器"""
        self.random_state = random_state
        self.best_model: Optional[RandomForestModel] = None
        self.best_params: Dict[str, Any] = {}
        self.cv_results: List[Dict[str, Any]] = []
        self._log = logging.getLogger(__name__)
    
    def grid_search(self, X: np.ndarray, y: np.ndarray,
                    feature_names: List[str],
                    class_names: List[str],
                    param_grid: Optional[Dict[str, List]] = None,
                    cv: int = 5) -> Dict[str, Any]:
        """
        网格搜索超参数
        
        Args:
            X: 特征矩阵
            y: 标签
            feature_names: 特征名称
            class_names: 类别名称
            param_grid: 参数网格
            cv: 交叉验证折数
            
        Returns:
            最佳参数和结果
        """
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.model_selection import GridSearchCV, cross_val_score
            from sklearn.metrics import make_scorer, accuracy_score
        except ImportError:
            self._log.error("sklearn 未安装")
            raise ImportError("请安装 sklearn: pip install scikit-learn")
        
        # 默认参数网格
        if param_grid is None:
            param_grid = {
                'n_estimators': [50, 100, 200],
                'max_depth': [5, 10, 15, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            }
        
        self._log.info(f"开始网格搜索...")
        self._log.info(f"参数组合数：{self._count_combinations(param_grid)}")
        
        # 基础模型
        rf = RandomForestClassifier(random_state=self.random_state, n_jobs=-1)
        
        # 网格搜索
        grid_search = GridSearchCV(
            rf,
            param_grid,
            cv=cv,
            scoring='accuracy',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X, y)
        
        # 保存最佳参数
        self.best_params = grid_search.best_params_
        best_score = grid_search.best_score_
        
        self._log.info(f"最佳参数：{self.best_params}")
        self._log.info(f"最佳交叉验证准确率：{best_score:.4f}")
        
        # 创建最佳模型
        self.best_model = RandomForestModel(
            n_estimators=self.best_params.get('n_estimators', 100),
            max_depth=self.best_params.get('max_depth', 10),
            min_samples_split=self.best_params.get('min_samples_split', 5),
            min_samples_leaf=self.best_params.get('min_samples_leaf', 2),
            random_state=self.random_state
        )
        
        # 用全部数据训练最佳模型
        from sklearn.model_selection import train_test_split
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, stratify=y, random_state=self.random_state
        )
        
        self.best_model.fit(X_train, y_train, feature_names, class_names, X_val, y_val)
        
        return {
            'best_params': self.best_params,
            'best_score': best_score,
            'cv_results': grid_search.cv_results_
        }
    
    def cross_validate(self, X: np.ndarray, y: np.ndarray,
                       n_folds: int = 5) -> Dict[str, float]:
        """
        交叉验证
        
        Args:
            X: 特征矩阵
            y: 标签
            n_folds: 折数
            
        Returns:
            交叉验证结果
        """
        try:
            from sklearn.model_selection import cross_val_score, StratifiedKFold
            from sklearn.ensemble import RandomForestClassifier
        except ImportError:
            self._log.error("sklearn 未安装")
            raise ImportError("请安装 sklearn: pip install scikit-learn")
        
        self._log.info(f"开始{n_folds}折交叉验证...")
        
        # 创建模型
        rf = RandomForestClassifier(
            n_estimators=self.best_params.get('n_estimators', 100),
            max_depth=self.best_params.get('max_depth', 10),
            min_samples_split=self.best_params.get('min_samples_split', 5),
            min_samples_leaf=self.best_params.get('min_samples_leaf', 2),
            random_state=self.random_state,
            n_jobs=-1
        )
        
        # 交叉验证
        cv = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=self.random_state)
        scores = cross_val_score(rf, X, y, cv=cv, scoring='accuracy')
        
        results = {
            'mean_accuracy': float(np.mean(scores)),
            'std_accuracy': float(np.std(scores)),
            'fold_scores': scores.tolist()
        }
        
        self._log.info(f"交叉验证准确率：{results['mean_accuracy']:.4f} ± {results['std_accuracy']:.4f}")
        
        self.cv_results = results
        
        return results
    
    def _count_combinations(self, param_grid: Dict[str, List]) -> int:
        """计算参数组合数"""
        import itertools
        values = param_grid.values()
        return len(list(itertools.product(*values)))


def train_random_forest(X_train: np.ndarray, y_train: np.ndarray,
                        X_val: np.ndarray, y_val: np.ndarray,
                        feature_names: List[str],
                        class_names: List[str],
                        do_grid_search: bool = True) -> RandomForestModel:
    """
    便捷函数：训练随机森林
    
    Args:
        X_train: 训练集特征
        y_train: 训练集标签
        X_val: 验证集特征
        y_val: 验证集标签
        feature_names: 特征名称
        class_names: 类别名称
        do_grid_search: 是否进行网格搜索
        
    Returns:
        训练好的模型
    """
    trainer = RandomForestTrainer(random_state=42)
    
    if do_grid_search:
        # 合并训练集和验证集进行网格搜索
        X_all = np.vstack([X_train, X_val])
        y_all = np.concatenate([y_train, y_val])
        
        trainer.grid_search(X_all, y_all, feature_names, class_names, cv=5)
        return trainer.best_model
    else:
        # 直接训练
        model = RandomForestModel(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        model.fit(X_train, y_train, feature_names, class_names, X_val, y_val)
        return model


if __name__ == '__main__':
    # 测试代码
    print("测试随机森林训练模块...")
    
    # 生成测试数据
    np.random.seed(42)
    n_samples = 200
    n_features = 40
    n_classes = 10
    
    X = np.random.randn(n_samples, n_features)
    y = np.random.randint(0, n_classes, n_samples)
    
    feature_names = [f'feature_{i}' for i in range(n_features)]
    class_names = [f'class_{i}' for i in range(n_classes)]
    
    # 划分数据集
    from sklearn.model_selection import train_test_split
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    
    # 训练模型
    model = train_random_forest(
        X_train, y_train, X_val, y_val,
        feature_names, class_names,
        do_grid_search=False  # 测试时跳过网格搜索
    )
    
    print(f"模型训练完成")
    print(f"验证集准确率：{model.training_history.get('results', {}).get('val_accuracy', 0):.4f}")
    
    # 测试预测
    predictions = model.predict_with_uncertainty(X_val[:5])
    print(f"\n测试预测（前 5 个样本）:")
    for i, pred in enumerate(predictions):
        print(f"  样本{i+1}: {pred['class_name']} (置信度：{pred['confidence']:.3f})")
