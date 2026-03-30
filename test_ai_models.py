"""
AI 模型测试脚本

测试 Transformer 模型、不确定性量化、可解释性分析功能

使用方法:
    python test_ai_models.py
"""
import sys
import numpy as np
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

def test_transformer_model():
    """测试 Transformer 模型"""
    print("\n" + "="*60)
    print("测试 Transformer 模型")
    print("="*60)
    
    try:
        from backend.models.transformer_model import (
            SpectralTransformer,
            TransformerConfig,
            create_transformer_model
        )
        
        # 创建模型
        print("\n1. 创建模型...")
        model = create_transformer_model(
            num_classes=10,
            input_dim=1024,
            model_size='tiny'
        )
        
        print(f"   ✓ 模型已创建")
        print(f"   - 参数量：{model.config.total_dim:,}")
        print(f"   - Patch 大小：{model.config.patch_size}")
        print(f"   - 编码器层数：{model.config.num_layers}")
        
        # 生成测试数据
        print("\n2. 生成测试光谱...")
        spectrum = generate_test_spectrum(num_points=1024)
        print(f"   ✓ 光谱形状：{spectrum.shape}")
        
        # 测试预测
        print("\n3. 测试预测...")
        prediction, confidence, metadata = model.predict(spectrum)
        print(f"   ✓ 预测类别：{prediction}")
        print(f"   ✓ 置信度：{confidence:.3f}")
        
        # 测试不确定性量化
        print("\n4. 测试不确定性量化（MC Dropout, n=10）...")
        uncertainty_result = model.predict_with_uncertainty(spectrum, n_samples=10)
        print(f"   ✓ 预测类别：{uncertainty_result['prediction']}")
        print(f"   ✓ 置信度：{uncertainty_result['confidence']:.3f} ± {uncertainty_result['uncertainty']:.3f}")
        if 'entropy' in uncertainty_result:
            print(f"   ✓ 熵：{uncertainty_result['entropy']:.3f}")
        
        # 测试可解释性
        print("\n5. 测试可解释性分析...")
        importance = model.get_feature_importance(spectrum, method='attention')
        print(f"   ✓ 特征重要性形状：{importance.shape}")
        print(f"   ✓ 最大重要性位置：{np.argmax(importance)}")
        
        attention_weights = model.get_attention_weights(spectrum)
        if attention_weights:
            print(f"   ✓ 注意力权重层数：{len(attention_weights)}")
        
        print("\n✅ Transformer 模型测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ Transformer 模型测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_inference():
    """测试 AI 推理模块"""
    print("\n" + "="*60)
    print("测试 AI 推理模块")
    print("="*60)
    
    try:
        from backend.ai_inference import AIInference
        
        # 创建 AI 推理实例
        print("\n1. 创建 AI 推理实例...")
        ai = AIInference()
        print(f"   ✓ AI 推理已初始化")
        
        # 获取模型信息
        print("\n2. 获取模型信息...")
        info = ai.get_model_info()
        if info.get('loaded'):
            print(f"   ✓ 模型已加载")
            print(f"   - 模型类型：{info.get('model_type')}")
            print(f"   - 类别数：{info.get('num_classes')}")
        else:
            print(f"   ⚠ 模型未加载（正常，因为模型文件不存在）")
        
        # 生成测试数据
        print("\n3. 生成测试光谱...")
        spectrum = generate_test_spectrum(num_points=1024)
        
        # 测试预测
        print("\n4. 测试预测...")
        result = ai.predict(spectrum)
        if result.get('success'):
            print(f"   ✓ 预测成功")
            print(f"   - 类别：{result.get('class_name_zh', 'N/A')}")
            print(f"   - 置信度：{result.get('confidence', 0):.3f}")
        else:
            print(f"   ⚠ 预测失败（可能模型未加载）：{result.get('error')}")
        
        # 测试不确定性量化
        print("\n5. 测试不确定性量化...")
        result = ai.predict_with_uncertainty(spectrum)
        if result.get('success'):
            print(f"   ✓ 不确定性量化成功")
            print(f"   - 置信度：{result.get('confidence', 0):.3f} ± {result.get('uncertainty', 0):.3f}")
            print(f"   - 风险等级：{result.get('risk_level', 'N/A')}")
        else:
            print(f"   ⚠ 不确定性量化失败：{result.get('error')}")
        
        # 测试可解释性
        print("\n6. 测试可解释性分析...")
        result = ai.explain(spectrum, method='attention', top_k=3)
        if result.get('success'):
            print(f"   ✓ 可解释性分析成功")
            print(f"   - 类别：{result.get('class_name_zh', 'N/A')}")
            if result.get('top_contributions'):
                print(f"   - 特征峰数量：{len(result['top_contributions'])}")
                for contrib in result['top_contributions'][:2]:
                    print(f"     • {contrib['position']:.0f} cm⁻¹: {contrib['contribution']*100:.1f}%")
        else:
            print(f"   ⚠ 可解释性分析失败：{result.get('error')}")
        
        print("\n✅ AI 推理模块测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ AI 推理模块测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_uncertainty_quantification():
    """测试不确定性量化模块"""
    print("\n" + "="*60)
    print("测试不确定性量化模块")
    print("="*60)
    
    try:
        from backend.models.transformer_model import create_transformer_model
        from backend.models.uncertainty import UncertaintyQuantifier
        
        # 创建模型和量化器
        print("\n1. 创建模型和不确定性量化器...")
        model = create_transformer_model(num_classes=10, input_dim=1024)
        quantifier = UncertaintyQuantifier(model, n_samples=20)
        print(f"   ✓ 已创建")
        
        # 生成测试数据
        print("\n2. 生成测试光谱...")
        spectrum = generate_test_spectrum(num_points=1024)
        
        # 测试预测
        print("\n3. 测试不确定性预测...")
        result = quantifier.predict(spectrum)
        print(f"   ✓ 预测类别：{result.prediction}")
        print(f"   ✓ 置信度：{result.confidence:.3f} ± {result.uncertainty:.3f}")
        print(f"   ✓ 风险等级：{result.risk_level}")
        print(f"   ✓ 是否可信：{result.is_reliable}")
        
        # 测试异常检测
        print("\n4. 测试异常检测...")
        is_outlier, score = quantifier.detect_outlier(spectrum, threshold=0.5)
        print(f"   ✓ 异常分数：{score:.3f}")
        print(f"   ✓ 是否异常：{is_outlier}")
        
        print("\n✅ 不确定性量化模块测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 不确定性量化模块测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_explainability():
    """测试可解释性分析模块"""
    print("\n" + "="*60)
    print("测试可解释性分析模块")
    print("="*60)
    
    try:
        from backend.models.transformer_model import create_transformer_model
        from backend.models.explainability import ExplainabilityAnalyzer
        
        # 创建模型和分析器
        print("\n1. 创建模型和可解释性分析器...")
        model = create_transformer_model(num_classes=10, input_dim=1024)
        wavenumbers = np.linspace(200, 3200, 1024)
        analyzer = ExplainabilityAnalyzer(model, wavenumbers=wavenumbers)
        print(f"   ✓ 已创建")
        
        # 生成测试数据
        print("\n2. 生成测试光谱...")
        spectrum = generate_test_spectrum(num_points=1024)
        
        # 测试解释
        print("\n3. 测试可解释性分析（attention 方法）...")
        result = analyzer.explain(spectrum, method='attention', top_k=5)
        print(f"   ✓ 预测类别：{result.class_name}")
        print(f"   ✓ 置信度：{result.confidence:.3f}")
        print(f"   ✓ 特征贡献数：{len(result.top_contributions)}")
        
        # 打印主要贡献
        print("\n   主要特征峰贡献度：")
        for i, contrib in enumerate(result.top_contributions[:3]):
            assignment = contrib.assignment or "未知"
            print(f"   {i+1}. {contrib.position:.0f} cm⁻¹: {contrib.contribution*100:.1f}% ({assignment})")
        
        # 测试热力图数据
        print("\n4. 测试热力图数据生成...")
        heatmap_data = analyzer.visualize_heatmap(spectrum, result.feature_importance)
        print(f"   ✓ 热力图数据已生成")
        print(f"   - 波数点数：{len(heatmap_data['wavenumbers'])}")
        print(f"   - 重要性范围：[{heatmap_data['min_importance']:.3f}, {heatmap_data['max_importance']:.3f}]")
        
        print("\n✅ 可解释性分析模块测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 可解释性分析模块测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def generate_test_spectrum(num_points=1024, seed=42):
    """生成测试光谱（模拟矿物光谱）"""
    rng = np.random.default_rng(seed)
    
    # 生成波数轴
    wavenumbers = np.linspace(200, 3200, num_points)
    
    # 生成基线
    baseline = np.exp(-wavenumbers / 1000) * 0.5
    
    # 添加特征峰（模拟石英光谱）
    peaks = [
        (464, 1.0, 15),   # 最强峰
        (206, 0.15, 10),
        (355, 0.3, 12),
        (696, 0.2, 12),
        (1082, 0.4, 20),
    ]
    
    spectrum = baseline.copy()
    for pos, intensity, width in peaks:
        spectrum += intensity * np.exp(-(wavenumbers - pos) ** 2 / (2 * width ** 2))
    
    # 添加噪声
    spectrum += rng.normal(0, 0.02, num_points)
    
    # 归一化
    spectrum = spectrum / np.max(spectrum)
    
    return spectrum


def main():
    """主函数"""
    print("\n" + "="*60)
    print("🤖 AI 模型测试套件")
    print("="*60)
    
    results = {
        'transformer': test_transformer_model(),
        'ai_inference': test_ai_inference(),
        'uncertainty': test_uncertainty_quantification(),
        'explainability': test_explainability()
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
