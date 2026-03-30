# 拉曼光谱边缘客户端 - 项目架构文档

**版本**: P12 重构版
**最后更新**: 2026-03-28
**维护者**: P11 级全栈工程师

---

## 📋 目录

1. [项目概述](#项目概述)
2. [技术栈](#技术栈)
3. [系统架构](#系统架构)
4. [目录结构](#目录结构)
5. [核心模块](#核心模块)
6. [数据流](#数据流)
7. [测试架构](#测试架构)
8. [部署架构](#部署架构)
9. [开发指南](#开发指南)

---

## 项目概述

### 项目名称
拉曼光谱边缘客户端（Raman Spectroscopy Edge Client）

### 项目定位
基于 PySide6 + QWebEngineView + ECharts 的拉曼光谱数据采集与分析客户端，支持边缘计算场景。

### 目标用户
- 高校教师：拉曼光谱教学演示
- 科研人员：快速光谱分析
- 检测员：现场物质检测

### 核心功能
| 功能 | 状态 | 说明 |
|------|------|------|
| 数据采集 | ✅ | 支持积分时间、累加平均调节 |
| 平滑滤波 | ✅ | Savitzky-Golay、移动平均 |
| 基线校正 | ✅ | 多项式拟合、airPLS |
| 峰值检测 | ✅ | 自动寻峰、峰面积计算 |
| 谱库匹配 | ✅ | 10 种标准物质谱库 |
| 波长校准 | 🔄 | P0 待完成 |
| 强度校准 | 🔄 | P0 待完成 |
| 自动曝光 | 🔄 | P0 待完成 |

---

## 技术栈

### 后端技术

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.9+ | 主要编程语言 |
| PySide6 | 6.6+ | Qt6 Python 绑定 |
| QWebEngineView | 6.6+ | 内嵌 Chromium 浏览器 |
| QWebChannel | 6.6+ | 前后端通信桥接 |
| NumPy | 1.24+ | 数值计算 |
| SciPy | 1.10+ | 科学计算算法 |

### 前端技术

| 技术 | 版本 | 用途 |
|------|------|------|
| HTML5 | - | 页面结构 |
| CSS3 | - | 样式设计 |
| JavaScript | ES6+ | 交互逻辑 |
| ECharts | 5.4.3 | 图表可视化 |
| QWebChannel.js | 6.6+ | 后端通信 |

### 测试工具

| 工具 | 版本 | 用途 |
|------|------|------|
| pytest | 7.4+ | Python 测试框架 |
| Playwright | 1.40+ | E2E 测试框架 |
| pytest-cov | 4.1+ | 覆盖率统计 |

---

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        MainWindow (PySide6)                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    QWebEngineView                         │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │              Frontend (HTML/JS/ECharts)             │  │  │
│  │  │  - index.html                                       │  │  │
│  │  │  - js/main.js                                       │  │  │
│  │  │  - js/bridge.js                                     │  │  │
│  │  │  - js/chart.js                                      │  │  │
│  │  │  - js/ui.js                                         │  │  │
│  │  │  - js/state.js                                      │  │  │
│  │  │  - js/cache.js                                      │  │  │
│  │  │  - js/theme.js                                      │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └─────────────────────┬─────────────────────────────────────┘  │
│                        │ QWebChannel                             │
│  ┌─────────────────────▼─────────────────────────────────────┐  │
│  │                   BridgeObject                             │  │
│  │  @Slot connect() -> bool                                   │  │
│  │  @Slot startAcquisition() -> bool                          │  │
│  │  @Slot stopAcquisition()                                   │  │
│  │  @Signal connected()                                       │  │
│  │  @Signal spectrumReady(data)                               │  │
│  └────────────┬──────────────────────────────────────────────┘  │
│               │                                                  │
│  ┌────────────▼──────────────────────────────────────────────┐  │
│  │                   StateManager                             │  │
│  │  - connection: ConnectionState                             │  │
│  │  - acquisition: AcquisitionState                           │  │
│  │  - noise_level: float                                      │  │
│  │  @Signal connectionChanged(state)                          │  │
│  │  @Signal acquisitionChanged(state)                         │  │
│  └────────────┬──────────────────────────────────────────────┘  │
│               │                                                  │
│  ┌────────────▼──────────────────────────────────────────────┐  │
│  │                    MockDriver                              │  │
│  │  - connect() -> bool                                       │  │
│  │  - read_spectrum() -> np.ndarray                           │  │
│  │  - get_wavelengths() -> np.ndarray                         │  │
│  │  - device_state: DeviceState (Enum)                        │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                  WorkerThread (QThread)                    │  │
│  │  - acquiring: bool                                         │  │
│  │  - sample_rate: float                                      │  │
│  │  @Signal spectrumReady(data)                               │  │
│  │  @Signal errorOccurred(msg)                                │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 模块职责

| 模块 | 职责 | 设计原则 |
|------|------|----------|
| **MainWindow** | 应用主窗口，整合所有组件 | 组合模式 |
| **QWebEngineView** | 内嵌浏览器，渲染前端页面 | 前后端分离 |
| **BridgeObject** | 前后端通信桥接，暴露 Slot 给前端 | 单一职责 |
| **StateManager** | 统一管理应用状态（连接/采集/设备） | 状态集中管理 |
| **WorkerThread** | 多线程数据采集，避免阻塞 UI | 独立线程，异常安全 |
| **MockDriver** | 模拟拉曼光谱数据生成 | 继承 BaseDriver，可替换 |

---

## 目录结构

```
edge-client/
├── backend/                    # 后端模块
│   ├── __init__.py
│   ├── algorithms/             # 算法模块
│   │   ├── __init__.py
│   │   ├── smoothing.py        # 平滑滤波
│   │   ├── baseline.py         # 基线校正
│   │   ├── peak_detection.py   # 峰值检测
│   │   ├── similarity.py       # 相似度计算
│   │   ├── library_match.py    # 谱库匹配
│   │   ├── wavelength_calibration.py  # 波长校准
│   │   ├── intensity_calibration.py   # 强度校准
│   │   └── auto_exposure.py    # 自动曝光
│   ├── driver/                 # 硬件驱动层
│   │   ├── __init__.py
│   │   ├── base.py             # 驱动基类接口
│   │   └── mock_driver.py      # 模拟驱动
│   ├── library/                # 标准谱库
│   │   ├── __init__.py
│   │   └── [物质谱图文件.json]
│   ├── services/               # 服务层（预留）
│   │   └── __init__.py
│   ├── database.py             # 数据库（预留）
│   ├── error_handler.py        # 错误处理
│   ├── inference.py            # 推理模块
│   ├── logging_config.py       # 日志配置
│   ├── model_config.json       # 模型配置
│   ├── report_generator.py     # 报告生成
│   ├── state_manager.py        # 状态管理器
│   └── todo.md                 # 后端任务清单
│
├── frontend/                   # 前端模块
│   ├── index.html              # 主页面
│   ├── styles.css              # 全局样式
│   ├── echarts.min.js          # ECharts 库
│   ├── qwebchannel.js          # QWebChannel 库
│   ├── package.json            # Node.js 配置
│   ├── vitest.config.js        # Vitest 配置
│   ├── js/                     # JavaScript 模块
│   │   ├── main.js             # 应用入口
│   │   ├── bridge.js           # 后端通信
│   │   ├── chart.js            # 图表渲染
│   │   ├── ui.js               # UI 操作
│   │   ├── utils.js            # 工具函数
│   │   ├── state.js            # 状态管理
│   │   ├── cache.js            # SWR 缓存
│   │   ├── theme.js            # 主题管理
│   │   ├── virtual-scroll.js   # 虚拟滚动
│   │   ├── skeleton.js         # 骨架屏
│   │   ├── types.js            # 类型定义
│   │   ├── peaks.js            # 峰值检测
│   │   ├── difference.js       # 差异对比
│   │   └── live.js             # 实时数据
│   ├── pages/                  # 子页面
│   │   ├── settings.html       # 设置页面
│   │   ├── calibration.html    # 校准页面
│   │   ├── library.html        # 谱库匹配
│   │   ├── history.html        # 历史记录
│   │   ├── report.html         # 报告生成
│   │   └── about.html          # 关于页面
│   ├── tests/                  # 前端测试
│   │   └── [测试文件]
│   └── todo.md                 # 前端任务清单
│
├── tests/                      # 测试套件
│   ├── __init__.py
│   ├── conftest.py             # 测试配置
│   ├── unit/                   # 单元测试
│   │   └── test_algorithms.py
│   ├── integration/            # 集成测试
│   │   └── test_core.py
│   ├── e2e/                    # E2E 测试
│   │   └── test_frontend.py
│   └── fixtures/               # 测试夹具
│
├── scripts/                    # 启动脚本
│   ├── start_all.py            # 一键启动
│   ├── start_backend.py        # 后端启动
│   └── start_frontend.js       # 前端启动
│
├── logs/                       # 日志目录（自动生成）
├── dist/                       # 打包输出（自动生成）
├── build/                      # 构建中间文件（自动生成）
│
├── main.py                     # 主程序入口
├── run.py                      # 快速启动
├── cli.py                      # 命令行工具
├── requirements.txt            # Python 依赖
├── README.md                   # 项目说明
├── ARCHITECTURE.md             # 架构文档（本文件）
├── RECONSTRUCTION_REPORT.md    # 重构总报告
└── PROJECT_STATUS.md           # 项目状态
```

---

## 核心模块

### 1. StateManager（状态管理器）

**职责**: 统一管理应用状态，避免状态共享

**状态类型**:
```python
class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"

class AcquisitionState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    STOPPING = "stopping"
```

**核心方法**:
```python
class StateManager(QObject):
    connectionChanged = Signal(object)  # 连接状态变化信号
    acquisitionChanged = Signal(object)  # 采集状态变化信号

    def connect_device(self) -> None
    def disconnect_device(self) -> None
    def set_connected(self, connected: bool) -> None
    def start_acquisition(self) -> bool
    def stop_acquisition(self) -> None
```

### 2. BridgeObject（通信桥接）

**职责**: 前后端通信桥接，暴露 Slot 给前端调用

**核心方法**:
```python
class BridgeObject(QObject):
    @Slot(result=bool)
    def connect(self) -> bool

    @Slot()
    def disconnect(self) -> None

    @Slot(result=bool)
    def startAcquisition(self) -> bool

    @Slot()
    def stopAcquisition(self) -> None

    @Signal
    def connected(self)

    @Signal
    def spectrumReady(self, data)
```

### 3. WorkerThread（工作线程）

**职责**: 多线程数据采集，避免阻塞 UI

**核心属性**:
```python
class WorkerThread(QThread):
    acquiring: bool = False  # 是否正在采集
    sample_rate: float = 10.0  # 采样率 (Hz)

    spectrumReady = Signal(object)  # 光谱数据就绪信号
    errorOccurred = Signal(str)  # 错误发生信号
```

### 4. MockDriver（模拟驱动）

**职责**: 模拟拉曼光谱数据生成

**核心方法**:
```python
class MockDriver(BaseDriver):
    def connect(self) -> bool
    def disconnect(self) -> None
    def read_spectrum(self) -> Optional[np.ndarray]
    def get_wavelengths(self) -> np.ndarray

    @property
    def device_state(self) -> DeviceState
    @device_state.setter
    def device_state(self, state: DeviceState)
```

---

## 数据流

### 数据采集流程

```
1. 用户点击"开始采集"按钮
   ↓
2. Frontend (main.js) 调用 bridge.startAcquisition()
   ↓
3. BridgeObject.startAcquisition() → StateManager.start_acquisition()
   ↓
4. WorkerThread.acquiring = True → 开始采集循环
   ↓
5. WorkerThread 调用 driver.read_spectrum()
   ↓
6. MockDriver 生成模拟光谱数据
   ↓
7. WorkerThread.spectrumReady.emit(data)
   ↓
8. BridgeObject 接收信号 → 通过 QWebChannel 发送前端
   ↓
9. Frontend (chart.js) 接收数据 → ECharts 更新图表
```

### 状态变化流程

```
1. 用户点击"连接设备"按钮
   ↓
2. Frontend 调用 bridge.connect()
   ↓
3. BridgeObject.connect() → driver.connect()
   ↓
4. StateManager.set_connected(True)
   ↓
5. StateManager.connectionChanged.emit(CONNECTED)
   ↓
6. BridgeObject.connected.emit()
   ↓
7. Frontend 接收信号 → 更新 UI 状态
```

---

## 测试架构

### 测试分类

| 类型 | 位置 | 说明 | 运行命令 |
|------|------|------|----------|
| 单元测试 | tests/unit/ | 测试单个函数/类 | `pytest tests/unit/ -v` |
| 集成测试 | tests/integration/ | 测试模块间交互 | `pytest tests/integration/ -v` |
| E2E 测试 | tests/e2e/ | 测试完整用户流程 | `pytest tests/e2e/ -v` |

### 测试覆盖率

**目标覆盖率**:
- 单元测试：80%+
- 集成测试：75%+
- E2E 测试：100% UI 覆盖

**运行覆盖率**:
```bash
pytest tests/ --cov=backend --cov=frontend --cov-report=html
```

---

## 部署架构

### 开发环境

```
┌─────────────┐     ┌─────────────┐
│  前端开发   │     │  后端开发   │
│   服务器    │     │  PySide6    │
│  (8080)     │◄───►│   (内嵌)    │
└─────────────┘     └─────────────┘
```

**启动命令**:
```bash
# 一键启动
python scripts/start_all.py

# 分别启动
python scripts/start_backend.py
node scripts/start_frontend.js
```

### 生产环境

```
┌─────────────────────────────────┐
│      PySide6 应用窗口           │
│  ┌───────────────────────────┐  │
│  │   QWebEngineView          │  │
│  │   (内嵌前端，无服务器)    │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

**打包命令**:
```bash
pyinstaller main.spec
```

---

## 开发指南

### 新增算法模块

1. 在 `backend/algorithms/` 创建新文件
2. 实现统一接口：
```python
def process_spectrum(spectrum: np.ndarray, **kwargs) -> np.ndarray:
    """处理光谱"""
    pass
```
3. 添加单元测试：`tests/unit/test_algorithms.py`
4. 更新文档

### 新增前端页面

1. 在 `frontend/pages/` 创建 HTML 文件
2. 引入必要的 JS 模块
3. 实现页面逻辑
4. 添加导航链接
5. 测试页面加载

### 新增测试用例

1. 确定测试类型（unit/integration/e2e）
2. 在对应目录创建测试文件
3. 遵循命名规范：`test_*.py`
4. 使用 pytest 装饰器：`@pytest.mark.*`
5. 运行测试验证

### 代码规范

**Python**:
- 遵循 PEP 8
- 类型注解必需
- 文档字符串完整
- 日志记录规范

**JavaScript**:
- 使用 ES6 模块
- 避免全局变量
- 事件监听器清理
- 错误处理完整

---

*文档最后更新：2026-03-28*
*维护者：P11 级全栈工程师*
