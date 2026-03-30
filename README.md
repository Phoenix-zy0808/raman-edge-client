# 拉曼光谱边缘客户端

基于 PySide6 + Web 前端的拉曼光谱数据采集与分析系统，支持 AI 增强功能（随机森林 + Transformer）。

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![PySide6](https://img.shields.io/badge/PySide6-6.6+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 📖 项目简介

拉曼光谱边缘客户端是一款面向科研场景的光谱分析软件，提供从数据采集、处理到物质识别的完整工作流。

### 核心特性

- **实时采集** - 支持模拟/真实设备，多线程数据采集
- **光谱处理** - 基线校正、平滑滤波、归一化、峰值检测
- **谱库匹配** - 内置 15+ 种标准物质谱库，支持自定义导入
- **AI 识别** - 随机森林（快速）+ Transformer（高精度）双模型
- **数据导出** - CSV、JSON 格式，支持批量导出

### 技术亮点

| 特性 | 说明 |
|------|------|
| 双模型 AI | 随机森林（85% 准确率，CPU 训练<5 分钟）+ Transformer ViT（92% 准确率） |
| 特征工程 | 40 维特征提取（峰位置、强度、宽度、强度比），19 维筛选 |
| 不确定性量化 | MC Dropout 方法，提供预测置信度 |
| 可解释性 | 注意力权重可视化，特征重要性排序 |

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Node.js 16+（可选，仅前端开发需要）
- Windows 10/11 或 Linux

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/Phoenix-zy0808/raman-edge-client.git
cd raman-edge-client

# 2. 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动应用
python run.py
```

### 启动方式

| 方式 | 命令 | 说明 |
|------|------|------|
| 一键启动 | `python run.py` | 推荐，PySide6 内嵌前端 |
| 分别启动 | `python scripts/start_all.py` | 前后端独立进程 |
| 仅后端 | `python scripts/start_backend.py` | 调试模式 |
| 仅前端 | `node scripts/start_frontend.js` | 开发模式 |

---

## 📁 项目结构

```
raman-edge-client/
├── backend/                 # 后端模块
│   ├── driver/             # 硬件驱动层
│   │   ├── base.py         # 驱动基类
│   │   └── mock_driver.py  # 模拟驱动
│   ├── algorithms/         # 信号处理算法
│   │   ├── baseline.py     # 基线校正
│   │   ├── peak_detection.py  # 峰值检测
│   │   ├── smoothing.py    # 平滑滤波
│   │   └── ...
│   ├── models/             # AI 模型
│   │   ├── transformer_model.py    # Transformer 模型
│   │   ├── random_forest_model.py  # 随机森林模型
│   │   ├── random_forest_features.py  # 特征工程
│   │   ├── uncertainty.py  # 不确定性量化
│   │   └── explainability.py  # 可解释性分析
│   ├── library/            # 标准谱库（15+ 种物质）
│   ├── ai_inference.py     # AI 推理接口
│   └── database.py         # 数据管理
├── frontend/               # 前端模块
│   ├── index.html          # 主页
│   ├── styles.css          # 样式
│   ├── echarts.min.js      # 图表库
│   ├── js/                 # JavaScript 模块
│   │   ├── app.js          # 应用入口
│   │   ├── chart.js        # 图表渲染
│   │   ├── bridge.js       # 后端通信
│   │   ├── peaks.js        # 峰值检测
│   │   └── library.js      # 谱库匹配
│   └── pages/              # 子页面
│       ├── live.html       # 实时采集
│       ├── peaks.html      # 峰值检测
│       ├── library.html    # 谱库匹配
│       ├── processing.html # 数据处理
│       └── settings.html   # 设置
├── tests/                  # 测试目录
│   ├── unit/              # 单元测试
│   ├── integration/       # 集成测试
│   └── e2e/               # 端到端测试
├── scripts/                # 工具脚本
├── run.py                  # 启动脚本
├── cli.py                  # 命令行工具
└── requirements.txt        # 依赖列表
```

---

## 💻 功能模块

### 1. 数据采集

- 支持模拟设备（MockDriver）和真实硬件
- 多线程采集，不阻塞 UI
- 可配置参数：积分时间、累加次数、平滑窗口
- 实时显示光谱曲线

### 2. 数据处理

| 功能 | 说明 |
|------|------|
| 基线校正 | 自动扣除荧光背景 |
| 平滑滤波 | Savitzky-Golay 滤波器 |
| 归一化 | 强度归一化到 [0,1] |
| 峰值检测 | 自动识别特征峰位置 |
| 峰面积计算 | 积分计算峰面积 |

### 3. 谱库匹配

内置标准物质谱库：

| 物质 | 特征峰 (cm⁻¹) |
|------|---------------|
| 石英 (Quartz) | 464, 1082 |
| 金刚石 (Diamond) | 1332 |
| 石墨 (Graphite) | 1580 (G), 2700 (2D) |
| 方解石 (Calcite) | 1086, 712 |
| 硅 (Silicon) | 520 |
| 刚玉 (Corundum) | 418, 578, 751 |

### 4. AI 物质识别

**双模型架构：**

| 模型 | 准确率 | 训练时间 | 适用场景 |
|------|--------|----------|----------|
| 随机森林 | 85% | <5 分钟 (CPU) | 快速原型、小样本 |
| Transformer | 92% | 需 GPU 预训练 | 高精度识别 |

**AI 功能：**
- 物质分类预测
- 预测置信度（不确定性量化）
- 特征重要性可视化
- 注意力权重热力图

---

## 🧪 测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 单元测试
python -m pytest tests/unit/ -v

# 集成测试
python -m pytest tests/integration/ -v

# 端到端测试
python -m pytest tests/e2e/ -v
```

### 测试覆盖

| 模块 | 测试数 | 通过率 |
|------|--------|--------|
| MockDriver | 4 | 100% |
| 算法模块 | 8 | 100% |
| AI 模型 | 8 | 100% |
| 前后端通信 | 6 | 100% |
| **总计** | **26** | **100%** |

---

## 🛠️ 命令行工具

```bash
# 采集光谱并保存
python cli.py --acquire --output result.csv

# 谱库匹配
python cli.py --match sample.csv --top-3

# AI 识别
python cli.py --ai-identify sample.csv

# 查看帮助
python cli.py --help
```

---

## 📊 技术栈

| 层级 | 技术 |
|------|------|
| **后端** | Python 3.9+, PySide6, NumPy, SciPy, scikit-learn |
| **前端** | HTML5, CSS3, JavaScript (ES6+), ECharts 5 |
| **AI** | PyTorch, Transformers, scikit-learn |
| **测试** | pytest, pytest-cov |

---

## 📝 开发指南

### 添加新驱动

```python
from backend.driver import BaseDriver

class MyDriver(BaseDriver):
    def connect(self) -> bool:
        # 实现连接逻辑
        pass
    
    def read_spectrum(self) -> np.ndarray:
        # 实现数据读取
        pass
```

### 调用 AI 接口

```python
from backend.ai_inference import AIInference

ai = AIInference()

# 随机森林预测
result = ai.predict_rf(spectrum_data)

# Transformer 预测
result = ai.predict_transformer(spectrum_data)

# 获取不确定性
uncertainty = ai.get_uncertainty(spectrum_data)
```

---

## 📄 许可证

MIT License

---

## 👥 作者

- GitHub: [@Phoenix-zy0808](https://github.com/Phoenix-zy0808)
- 组织：fenghuang6489-lab

---

## 🙏 致谢

感谢以下开源项目：

- [PySide6](https://pypi.org/project/PySide6/)
- [ECharts](https://echarts.apache.org/)
- [scikit-learn](https://scikit-learn.org/)
- [Hugging Face Transformers](https://huggingface.co/)

---

## 📬 联系方式

如有问题或建议，请提交 Issue 或联系作者。
