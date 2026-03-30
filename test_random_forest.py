"""
随机森林模型测试脚本

测试方案 A（随机森林 + 特征工程）的所有功能：
1. 特征提取
2. 模型训练
3. 不确定性量化
4. 可解释性分析

使用方法:
    python test_random_forest.py
"""
import sys
import numpy as np
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

def generate_synthetic_spectrum(mineral_name: str,
                                wavenumbers: np.ndarray,
                                noise_level: float = 0.02,
                                seed: int = None) -> np.ndarray:
    """
    生成合成矿物光谱（用于测试）
    
    Args:
        mineral_name: 矿物名称
        wavenumbers: 波数轴
        noise_level: 噪声水平
        seed: 随机种子
        
    Returns:
        合成光谱
    """
    if seed is not None:
        np.random.seed(seed)
    
    from backend.models.random_forest_features import MINERAL_PEAKS
    
    spectrum = np.zeros_like(wavenumbers)
    
    if mineral_name in MINERAL_PEAKS:
        for peak_pos, relative_intensity in MINERAL_PEAKS[mineral_name]:
            # 用高斯峰模拟
            peak = relative_intensity * np.exp(-(wavenumbers - peak_pos) ** 2 / (2 * 15 ** 2))
            spectrum += peak
    
    # 添加基线
    baseline = 0.1 * np.exp(-wavenumbers / 1000)
    spectrum += baseline
    
    # 添加噪声
    spectrum += np.random.normal(0, noise_level, len(wavenumbers))
    
    # 归一化
    spectrum = spectrum / np.max(spectrum)
    
    return spectrum


def test_feature_extraction():
    """测试特征提取"""
    print("\n" + "="*60)
    print("测试特征提取")
    print("="*60)
    
    try:
        from backend.models import (
            SpectrumPreprocessor,
            FeatureExtractor,
            extract_mineral_features,
            MINERAL_PEAKS
        )
        
        # 生成测试光谱（石英）
        print("\n1. 生成测试光谱（石英）...")
        wavenumbers = np.linspace(200, 3200, 1024)
        spectrum = generate_synthetic_spectrum('quartz', wavenumbers, noise_level=0.02, seed=42)
        print(f"   ✓ 光谱形状：{spectrum.shape}")
        
        # 预处理
        print("\n2. 光谱预处理...")
        preprocessor = SpectrumPreprocessor()
        spectrum_processed = preprocessor.preprocess(spectrum, wavenumbers)
        print(f"   ✓ 预处理完成")
        
        # 提取特征
        print("\n3. 提取特征...")
        extractor = FeatureExtractor()
        features = extractor.extract_all_features(spectrum_processed)
        print(f"   ✓ 特征数：{len(features)}")
        print(f"   ✓ 特征名称（前 10 个）：{extractor.feature_names[:10]}")
        
        # 测试便捷函数
        print("\n4. 测试便捷函数...")
        features2, names2 = extract_mineral_features(spectrum, wavenumbers)
        print(f"   ✓ 特征数：{len(features2)}")
        print(f"   ✓ 特征名称匹配：{names2 == extractor.feature_names}")
        
        print("\n✅ 特征提取测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 特征提取测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_feature_selection():
    """测试特征选择"""
    print("\n" + "="*60)
    print("测试特征选择")
    print("="*60)
    
    try:
        from backend.models import (
            SpectrumPreprocessor,
            FeatureExtractor,
            FeatureSelector
        )
        
        # 生成多个样本
        print("\n1. 生成多个矿物样本...")
        wavenumbers = np.linspace(200, 3200, 1024)
        minerals = ['quartz', 'calcite', 'diamond', 'corundum']
        
        X = []
        y = []
        
        for i, mineral in enumerate(minerals):
            for j in range(20):  # 每类 20 个样本
                spectrum = generate_synthetic_spectrum(mineral, wavenumbers, noise_level=0.03, seed=i*100+j)
                X.append(spectrum)
                y.append(i)
        
        X = np.array(X)
        y = np.array(y)
        
        print(f"   ✓ 样本数：{len(X)}, 类别数：{len(minerals)}")
        
        # 预处理和特征提取
        print("\n2. 批量特征提取...")
        preprocessor = SpectrumPreprocessor()
        extractor = FeatureExtractor()
        
        features_list = []
        for spectrum in X:
            spectrum_processed = preprocessor.preprocess(spectrum, wavenumbers)
            features = extractor.extract_all_features(spectrum_processed)
            features_list.append(features)
        
        X_features = np.array(features_list)
        print(f"   ✓ 特征矩阵形状：{X_features.shape}")
        
        # 特征选择
        print("\n3. 特征选择...")
        selector = FeatureSelector(variance_threshold=0.001, correlation_threshold=0.95, top_k=20)
        X_selected = selector.select(X_features, y, extractor.feature_names)
        print(f"   ✓ 选择后特征数：{X_selected.shape[1]}")
        print(f"   ✓ 选择的特征：{selector.feature_names[:10]}...")
        
        print("\n✅ 特征选择测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 特征选择测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_training():
    """测试模型训练"""
    print("\n" + "="*60)
    print("测试模型训练")
    print("="*60)
    
    try:
        from backend.models import (
            SpectrumPreprocessor,
            FeatureExtractor,
            FeatureSelector,
            RandomForestModel,
            train_random_forest
        )
        
        # 生成训练数据
        print("\n1. 生成训练数据...")
        wavenumbers = np.linspace(200, 3200, 1024)
        minerals = ['quartz', 'calcite', 'diamond', 'corundum', 'olivine']
        
        X = []
        y = []
        
        for i, mineral in enumerate(minerals):
            for j in range(30):  # 每类 30 个样本
                spectrum = generate_synthetic_spectrum(mineral, wavenumbers, noise_level=0.03, seed=i*100+j)
                X.append(spectrum)
                y.append(i)
        
        X = np.array(X)
        y = np.array(y)
        
        print(f"   ✓ 样本数：{len(X)}, 类别数：{len(minerals)}")
        
        # 特征提取
        print("\n2. 特征提取...")
        preprocessor = SpectrumPreprocessor()
        extractor = FeatureExtractor()
        selector = FeatureSelector(top_k=20)
        
        features_list = []
        for spectrum in X:
            spectrum_processed = preprocessor.preprocess(spectrum, wavenumbers)
            features = extractor.extract_all_features(spectrum_processed)
            features_list.append(features)
        
        X_features = np.array(features_list)
        X_selected = selector.select(X_features, y, extractor.feature_names)
        
        print(f"   ✓ 特征矩阵形状：{X_selected.shape}")
        
        # 划分数据集
        print("\n3. 划分数据集...")
        from sklearn.model_selection import train_test_split
        X_train, X_val, y_train, y_val = train_test_split(
            X_selected, y, test_size=0.2, stratify=y, random_state=42
        )
        print(f"   ✓ 训练集：{len(X_train)}, 验证集：{len(X_val)}")
        
        # 训练模型
        print("\n4. 训练随机森林模型...")
        model = train_random_forest(
            X_train, y_train, X_val, y_val,
            selector.feature_names, minerals,
            do_grid_search=False  # 测试时跳过网格搜索
        )
        
        results = model.training_history.get('results', {})
        print(f"   ✓ 训练集准确率：{results.get('train_accuracy', 0):.4f}")
        print(f"   ✓ 验证集准确率：{results.get('val_accuracy', 0):.4f}")
        
        # 测试预测
        print("\n5. 测试预测...")
        predictions = model.predict_with_uncertainty(X_val[:5])
        for i, pred in enumerate(predictions):
            print(f"   样本{i+1}: {pred['class_name']} (置信度：{pred['confidence']:.3f}, 不确定性：{pred['uncertainty']:.3f})")
        
        # 测试特征重要性
        print("\n6. 获取特征重要性...")
        importances = model.get_feature_importance()
        top_features = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:5]
        print("   Top-5 特征:")
        for name, imp in top_features:
            print(f"     {name}: {imp:.4f}")
        
        print("\n✅ 模型训练测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 模型训练测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_calibration():
    """测试概率校准"""
    print("\n" + "="*60)
    print("测试概率校准")
    print("="*60)
    
    try:
        from backend.models import (
            SpectrumPreprocessor,
            FeatureExtractor,
            FeatureSelector,
            RandomForestModel
        )
        from sklearn.model_selection import train_test_split
        
        # 生成数据
        print("\n1. 生成数据...")
        wavenumbers = np.linspace(200, 3200, 1024)
        minerals = ['quartz', 'calcite', 'diamond', 'corundum']
        
        X = []
        y = []
        for i, mineral in enumerate(minerals):
            for j in range(40):
                spectrum = generate_synthetic_spectrum(mineral, wavenumbers, noise_level=0.03, seed=i*100+j)
                X.append(spectrum)
                y.append(i)
        
        X = np.array(X)
        y = np.array(y)
        
        # 特征提取
        print("\n2. 特征提取...")
        preprocessor = SpectrumPreprocessor()
        extractor = FeatureExtractor()
        selector = FeatureSelector(top_k=15)
        
        features_list = []
        for spectrum in X:
            spectrum_processed = preprocessor.preprocess(spectrum, wavenumbers)
            features = extractor.extract_all_features(spectrum_processed)
            features_list.append(features)
        
        X_features = np.array(features_list)
        X_selected = selector.select(X_features, y, extractor.feature_names)
        
        # 划分数据集
        X_train, X_test, y_train, y_test = train_test_split(
            X_selected, y, test_size=0.3, stratify=y, random_state=42
        )
        
        # 训练模型
        print("\n3. 训练模型...")
        model = RandomForestModel(n_estimators=100, max_depth=10)
        model.fit(X_train, y_train, selector.feature_names, minerals)
        
        # 概率校准
        print("\n4. 概率校准...")
        cal_results = model.calibrate(X_train, y_train, method='isotonic', cv=5)
        print(f"   ✓ 校准后准确率：{cal_results['calibration_accuracy']:.4f}")
        print(f"   ✓ Brier Score: {cal_results['avg_brier_score']:.4f}")
        
        # 比较校准前后的不确定性
        print("\n5. 比较校准前后...")
        print("   校准前:")
        preds_before = model.model.predict_proba(X_test[:5])
        for i in range(5):
            pred = np.argmax(preds_before[i])
            conf = preds_before[i, pred]
            print(f"     样本{i+1}: 类别{pred}, 置信度{conf:.3f}")
        
        print("   校准后:")
        preds_after = model.predict_with_uncertainty(X_test[:5])
        for i, pred in enumerate(preds_after):
            print(f"     样本{i+1}: {pred['class_name']}, 置信度{pred['confidence']:.3f}, 熵{pred['entropy']:.3f}")
        
        print("\n✅ 概率校准测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 概率校准测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "="*60)
    print("🌲 随机森林模型测试套件（方案 A）")
    print("="*60)
    
    results = {
        'feature_extraction': test_feature_extraction(),
        'feature_selection': test_feature_selection(),
        'model_training': test_model_training(),
        'model_calibration': test_model_calibration()
    }
    
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    print(f"\n总计：{total_passed}/{total_tests} 测试通过")
    
    if total_passed == total_tests:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查错误信息")
        return 1


if __name__ == '__main__':
    sys.exit(main())
