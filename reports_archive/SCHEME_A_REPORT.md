# 方案 A 实现报告 - 随机森林 + 特征工程

**版本**: P12-A 随机森林版
**最后更新**: 2026-03-29
**维护者**: P11 级全栈工程师

---

## 📋 执行摘要

成功实现**方案 A：随机森林 + 特征工程**（小样本快速方案）

所有模块已通过测试：
- ✅ 特征提取（40 维特征）
- ✅ 特征选择（降至 15-20 维）
- ✅ 模型训练（随机森林）
- ✅ 概率校准（Isotonic Regression）

**测试结果**: 4/4 测试通过 🎉

---

## 🎯 方案概述

### 核心思路
- 不用原始光谱数据（1024 维）直接训练
- 先提取有意义的特征（峰位置、强度、宽度等）
- 用随机森林分类（适合小样本、高维特征）

### 优势对比

| 维度 | 说明 |
|------|------|
| 数据需求 | 每类 10-20 个样本即可 |
| 训练时间 | <5 分钟（CPU） |
| GPU 需求 | 不需要 |
| 代码复杂度 | 低（sklearn 10 行搞定） |
| 可解释性 | 高（特征重要性） |
| 过拟合风险 | 低 |

**预期准确率**: 82-88%

---

## 📁 新增文件清单

### 后端模块

| 文件路径 | 说明 | 行数 |
|---------|------|------|
| `backend/models/random_forest_features.py` | 特征工程模块 | 665 |
| `backend/models/random_forest_model.py` | 随机森林训练模块 | 460 |
| `test_random_forest.py` | 测试脚本 | 380 |

### 配置文件

| 文件路径 | 说明 |
|---------|------|
| `requirements.txt` | 添加 scikit-learn 依赖 |
| `backend/models/__init__.py` | 导出随机森林模块 |

---

## 🏗️ 技术架构

### 特征工程流程

```
原始光谱 (1024 点)
    ↓
预处理
  - 重采样（对齐波长）
  - 基线校正（迭代多项式）
  - 平滑滤波（Savitzky-Golay）
  - 归一化（Min-Max）
    ↓
特征提取（40 维）
  - 峰位置特征（10 维）
  - 峰强度特征（10 维）
  - 峰宽度特征（10 维）
  - 强度比特征（5 维）
  - 全局特征（5 维）
    ↓
特征选择（15-20 维）
  - 方差阈值过滤
  - 相关性分析
  - 随机森林重要性
    ↓
随机森林分类
```

### 特征详细说明

#### 1. 峰位置特征（10 维）

在已知矿物特征峰位置±10 cm⁻¹范围内找最大值位置

| 特征 | 对应峰 | 矿物 |
|------|--------|------|
| peak_pos_0 | 282 cm⁻¹ | 方解石 |
| peak_pos_1 | 300 cm⁻¹ | 橄榄石 |
| peak_pos_2 | 330 cm⁻¹ | ZnO |
| peak_pos_3 | 355 cm⁻¹ | 石英 |
| peak_pos_4 | 378 cm⁻¹ | 刚玉 |
| peak_pos_5 | 418 cm⁻¹ | 刚玉 |
| peak_pos_6 | 438 cm⁻¹ | ZnO |
| peak_pos_7 | 464 cm⁻¹ | 石英 |
| peak_pos_8 | 480 cm⁻¹ | 长石 |
| peak_pos_9 | 510 cm⁻¹ | 长石 |

#### 2. 峰强度特征（10 维）

在已知特征峰位置±10 cm⁻¹范围内找最大强度（归一化后 0-1）

#### 3. 峰宽度特征（10 维）

计算半高宽（FWHM）：
- 找到峰顶强度 I_max
- 找到 I_max/2 对应的两个波长位置
- FWHM = 波长差

#### 4. 强度比特征（5 维）

计算特征峰强度比值：
- 石英 I_1082 / I_464
- 金刚石 I_1332 / I_背景
- 石墨 I_1580 / I_背景
- 方解石 I_1086 / I_713
- 刚玉 I_418 / I_背景

#### 5. 全局特征（5 维）

| 特征 | 说明 | 公式 |
|------|------|------|
| 曲线下面积 | 积分强度 | ∫spectrum dx |
| 光谱斜率 | 线性拟合斜率 | polyfit(x, y, 1)[0] |
| 光谱重心 | 强度加权平均波长 | Σ(x*I) / ΣI |
| 光谱偏度 | 三阶矩 | skew(spectrum) |
| 光谱峰度 | 四阶矩 | kurtosis(spectrum) |

---

## 🧪 测试结果

### 测试命令
```bash
python test_random_forest.py
```

### 测试结果

```
============================================================
测试结果汇总
============================================================
  feature_extraction: ✅ 通过
  feature_selection: ✅ 通过
  model_training: ✅ 通过
  model_calibration: ✅ 通过

总计：4/4 测试通过
🎉 所有测试通过！
```

### 详细测试数据

#### 特征提取测试
- 输入：石英合成光谱（1024 点）
- 输出：40 维特征向量
- 特征名称匹配：100%

#### 特征选择测试
- 初始特征数：40
- 方差过滤后：~30
- 相关性过滤后：~25
- RF 重要性选择后：19

#### 模型训练测试
- 数据集：5 类矿物 × 30 样本 = 150 样本
- 训练集：120 样本
- 验证集：30 样本
- **训练集准确率：100%**
- **验证集准确率：100%**

#### 预测测试（5 个样本）
```
样本 1: corundum (置信度：0.947, 不确定性：0.053)
样本 2: corundum (置信度：0.949, 不确定性：0.051)
样本 3: diamond (置信度：0.865, 不确定性：0.135)
样本 4: corundum (置信度：0.981, 不确定性：0.019)
样本 5: calcite (置信度：0.916, 不确定性：0.084)
```

#### 特征重要性（Top-5）
```
peak_pos_0: 0.1536  (282 cm⁻¹ - 方解石)
peak_pos_2: 0.1464  (330 cm⁻¹ - ZnO)
peak_pos_1: 0.1420  (300 cm⁻¹ - 橄榄石)
peak_pos_3: 0.1144  (355 cm⁻¹ - 石英)
peak_pos_4: 0.0988  (378 cm⁻¹ - 刚玉)
```

#### 概率校准测试
- 校准前 Brier Score: ~0.05
- 校准后 Brier Score: 0.0000
- 校准方法：Isotonic Regression（5 折交叉验证）

---

## 📊 对比实验设计

### 实验 1：特征选择效果对比

| 特征数 | 准确率 | 说明 |
|--------|--------|------|
| 40（全部） | 待测试 | 未选择 |
| 20（Top-K） | 待测试 | RF 重要性 |
| 15（方差 + 相关性） | 待测试 | 过滤方法 |

### 实验 2：不同模型对比

| 模型 | 准确率 | 训练时间 | 说明 |
|------|--------|----------|------|
| 随机森林 | 100% | <1 分钟 | 本方案 |
| SVM | 待测试 | - | RBF 核 |
| KNN | 待测试 | - | K=5 |
| 逻辑回归 | 待测试 | - | - |

### 实验 3：样本数量影响

| 样本数/类 | 准确率 | 说明 |
|-----------|--------|------|
| 10 | 待测试 | 最小样本 |
| 20 | 待测试 | 推荐样本 |
| 30 | 100% | 当前测试 |
| 50 | 待测试 | 充足样本 |

---

## 🔧 使用方法

### 1. 特征提取

```python
from backend.models import extract_mineral_features

# 输入光谱
spectrum = [...]  # 1024 点
wavenumbers = np.linspace(200, 3200, 1024)

# 提取特征
features, feature_names = extract_mineral_features(spectrum, wavenumbers)

print(f"特征数：{len(features)}")
print(f"特征名称：{feature_names}")
```

### 2. 模型训练

```python
from backend.models import (
    SpectrumPreprocessor,
    FeatureExtractor,
    FeatureSelector,
    train_random_forest
)

# 准备数据
X = [...]  # 光谱列表
y = [...]  # 标签列表
minerals = ['quartz', 'calcite', 'diamond', ...]

# 特征提取和选择
preprocessor = SpectrumPreprocessor()
extractor = FeatureExtractor()
selector = FeatureSelector(top_k=20)

X_features = []
for spectrum in X:
    spectrum_processed = preprocessor.preprocess(spectrum, wavenumbers)
    features = extractor.extract_all_features(spectrum_processed)
    X_features.append(features)

X_features = np.array(X_features)
X_selected = selector.select(X_features, y, extractor.feature_names)

# 训练模型
from sklearn.model_selection import train_test_split
X_train, X_val, y_train, y_val = train_test_split(
    X_selected, y, test_size=0.2, stratify=y, random_state=42
)

model = train_random_forest(
    X_train, y_train, X_val, y_val,
    selector.feature_names, minerals,
    do_grid_search=True  # 启用网格搜索
)
```

### 3. 模型预测

```python
# 基础预测
prediction = model.predict(X_test)

# 带不确定性的预测
results = model.predict_with_uncertainty(X_test)
for result in results:
    print(f"类别：{result['class_name']}")
    print(f"置信度：{result['confidence']:.3f}")
    print(f"不确定性：{result['uncertainty']:.3f}")
    print(f"熵：{result['entropy']:.3f}")
```

### 4. 概率校准

```python
# 校准概率
cal_results = model.calibrate(X_train, y_train, method='isotonic', cv=5)

print(f"校准后准确率：{cal_results['calibration_accuracy']:.4f}")
print(f"Brier Score: {cal_results['avg_brier_score']:.4f}")
```

### 5. 特征重要性

```python
importances = model.get_feature_importance()

# 打印 Top-10
top_features = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:10]
for name, imp in top_features:
    print(f"{name}: {imp:.4f}")
```

### 6. 模型保存与加载

```python
# 保存
model.save('models/random_forest_minerals.pkl')

# 加载
model.load('models/random_forest_minerals.pkl')
```

---

## 🎯 下一步工作

### 高优先级（P0）

1. **真实数据训练**
   - 下载 RRUFF 矿物光谱数据
   - 每类矿物 20-50 个样本
   - 重新训练模型

2. **超参数调优**
   - 网格搜索最佳参数
   - 5 折交叉验证
   - 记录最佳模型

3. **对比实验**
   - 完成方案中的对比实验表格
   - 收集准确率数据

### 中优先级（P1）

1. **后端集成**
   - 在 `ai_inference.py` 中添加随机森林支持
   - 统一预测接口

2. **前端集成**
   - 添加模型选择下拉框
   - 显示特征重要性图表

3. **文档完善**
   - API 文档
   - 训练指南

---

## ⚠️ 注意事项

### 数据需求
- 每类矿物至少需要 10-20 个样本
- 建议使用 RRUFF 标准谱库数据
- 当前使用合成光谱测试，准确率为 100%（过拟合）

### 特征工程
- 特征峰位置来自文献，可能与实测数据有偏差
- 需要根据真实数据调整特征峰位置
- 基线校正参数可能需要调优

### 模型训练
- 随机森林容易在训练集上过拟合
- 务必使用交叉验证评估
- 概率校准推荐使用 Isotonic Regression

---

## 📝 变更记录

| 日期 | 变更内容 | 变更人 |
|------|----------|--------|
| 2026-03-29 | 方案 A 实现 - 特征工程、模型训练、概率校准 | P11 |
| 2026-03-29 | 测试脚本创建，4/4 测试通过 | P11 |
| 2026-03-29 | requirements.txt 更新 | P11 |

---

## 📚 参考文献

1. Breiman, L. (2001). Random Forests. Machine Learning, 45(1), 5-32.
2. Pedregosa, F., et al. (2011). Scikit-learn: Machine Learning in Python. JMLR.
3. Gunasekaran, S., et al. (2006). Spectrochimica Acta Part A, 65, 212-221.（矿物拉曼光谱）
4. RRUFF Project: https://rruff.info/

---

*最后更新：2026-03-29*
*当前版本：P12-A 随机森林版*
*测试状态：4/4 测试通过 ✅*
*准确率：100%（合成数据，待真实数据验证）*
