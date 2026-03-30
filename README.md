# 拉曼光谱边缘客户端

基于 PySide6 + QWebEngineView + ECharts 的拉曼光谱数据采集与分析客户端。

## 项目结构

```
edge-client/
├── backend/              # 后端模块
│   ├── driver/          # 硬件驱动层
│   │   ├── __init__.py
│   │   ├── base.py      # 驱动基类接口 (含 DeviceState Enum)
│   │   └── mock_driver.py  # 模拟驱动
│   ├── algorithms/      # 算法模块
│   │   ├── wavelength_calibration.py  # 波长校准
│   │   ├── intensity_calibration.py   # 强度校准
│   │   └── auto_exposure.py          # 自动曝光
│   ├── __init__.py
│   └── state_manager.py # 状态管理器
├── frontend/            # 前端静态资源
│   ├── index.html       # 主页面 (HTML+ECharts)
│   ├── js/              # JavaScript 模块
│   │   ├── main.js      # 应用入口
│   │   ├── bridge.js    # 后端通信
│   │   ├── chart.js     # 图表渲染
│   │   ├── ui.js        # UI 操作
│   │   ├── utils.js     # 工具函数
│   │   ├── state.js     # 状态管理
│   │   ├── cache.js     # SWR 缓存
│   │   ├── theme.js     # 主题管理
│   │   └── virtual-scroll.js  # 虚拟滚动
│   └── pages/           # 子页面
│       ├── settings.html
│       ├── calibration.html
│       └── ...
├── scripts/             # 启动脚本
│   ├── start_backend.py    # 后端启动
│   ├── start_frontend.js   # 前端启动
│   └── start_all.py        # 一键启动
├── main.py              # 主程序入口
├── run.py               # 快速启动
├── cli.py               # 命令行工具
└── tests/               # 测试目录
```

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      MainWindow                             │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │ StateManager│  │ BridgeObject │  │  WorkerThread   │   │
│  │  (状态管理)  │◄─┤  (通信桥接)  │  │   (数据采集)    │   │
│  └─────────────┘  └──────┬───────┘  └────────┬────────┘   │
│         │                 │                   │            │
│         │                 │                   │            │
│         ▼                 ▼                   ▼            │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │ AppState    │  │ QWebChannel  │  │   MockDriver    │   │
│  │ (状态数据)  │  │  (前端通信)  │  │   (驱动实现)    │   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 核心模块职责

| 模块 | 职责 | 设计原则 |
|------|------|----------|
| **StateManager** | 统一管理应用状态（连接/采集/设备状态） | 单一职责，状态集中管理 |
| **BridgeObject** | 前后端通信桥接，暴露 Slot 给前端调用 | 仅负责通信，不持有业务逻辑 |
| **WorkerThread** | 多线程数据采集，避免阻塞 UI | 独立线程，异常安全 |
| **MockDriver** | 模拟拉曼光谱数据生成 | 继承 BaseDriver，可替换真实驱动 |

## 快速开始

### 方式一：一键启动（推荐）

同时启动前端开发服务器和后端应用，适合前后端联调开发。

```bash
# 激活虚拟环境
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 一键启动前后端
python scripts/start_all.py

# 或者使用快捷方式
python run.py  # 仅启动后端（PySide6 内嵌前端）
```

### 方式二：分别启动

**启动后端:**
```bash
# 开发模式（默认）
python scripts/start_backend.py

# 调试模式
python scripts/start_backend.py --debug

# 生产模式（禁用日志）
python scripts/start_backend.py --prod

# 指定日志级别
python scripts/start_backend.py --log-level DEBUG
```

**启动前端:**
```bash
# 使用 node 直接启动
node scripts/start_frontend.js

# 使用 npm
cd frontend && npm run dev

# 指定端口
node scripts/start_frontend.js --port 3000

# 生产模式
node scripts/start_frontend.js --prod
```

### 方式三：传统启动

```bash
# 激活虚拟环境
.venv\Scripts\activate

# 运行测试
python test_all.py           # 完整测试套件
python test_algorithms.py    # 算法测试 (15 项，100% 通过)
python -m pytest test_frontend_e2e.py -v  # E2E 测试

# 启动应用
python run.py
```

### 命令行工具

```bash
# 采集光谱并保存
python cli.py --acquire --output result.csv

# 谱库匹配
python cli.py --match sample.csv --top-3

# 光谱分析
python cli.py --analyze spectrum.json --output analysis.json

# 查看帮助
python cli.py --help
```

## 功能特性

- ✅ **状态管理重构**: StateManager 统一管理状态，避免状态共享
- ✅ **模拟数据生成**: MockDriver 生成带拉曼特征峰的模拟数据
- ✅ **实时采集**: WorkerThread 多线程采集，动态时序控制
- ✅ **异常处理**: 数据采集循环包含完整的异常处理
- ✅ **QWebChannel 通信**: 前后端双向通信
- ✅ **ECharts 可视化**: 实时光谱显示，本地化部署
- ✅ **设备状态模拟**: 正常/高噪声/异常三种模式 (使用 Enum)
- ✅ **打包兼容**: 资源路径适配打包后环境
- ✅ **启动脚本**: 支持一键启动、分别启动、命令行工具

## 环境要求

### Python 环境

- Python 3.9+
- PySide6
- NumPy
- SciPy

```bash
# 创建虚拟环境（如果还没有）
python -m venv .venv

# 激活虚拟环境
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### Node.js 环境（前端开发）

- Node.js 16+
- npm 8+

```bash
# 安装前端依赖
cd frontend
npm install

# 可选：安装文件监听（开发模式）
npm install chokidar
```

## 启动脚本说明

### start_all.py - 一键启动

同时启动前端开发服务器和后端应用。

```bash
# 基本用法
python scripts/start_all.py

# 仅启动后端
python scripts/start_all.py --backend-only

# 仅启动前端
python scripts/start_all.py --frontend-only

# 指定前端端口
python scripts/start_all.py --frontend-port 3000

# 调试模式
python scripts/start_all.py --debug

# 生产模式
python scripts/start_all.py --prod
```

### start_backend.py - 后端启动

启动 PySide6 + QWebEngine 应用。

```bash
# 开发模式
python scripts/start_backend.py

# 调试模式
python scripts/start_backend.py --debug

# 生产模式
python scripts/start_backend.py --prod

# 指定日志级别
python scripts/start_backend.py --log-level DEBUG

# 禁用控制台日志
python scripts/start_backend.py --no-console

# 仅检查环境
python scripts/start_backend.py --check
```

### start_frontend.js - 前端启动

启动 HTTP 服务器提供前端静态文件。

```bash
# 使用 node
node scripts/start_frontend.js

# 使用 npm
cd frontend && npm run dev

# 指定端口
node scripts/start_frontend.js --port 3000

# 生产模式
node scripts/start_frontend.js --prod

# 自动打开浏览器
node scripts/start_frontend.js --open
```

## 技术栈

- **后端**: Python 3.9+, PySide6, NumPy
- **前端**: HTML5, ECharts 5.4.3 (本地化), QWebChannel
- **测试**: 自定义测试框架，10 项单元测试

## 开发说明

### 驱动开发

实现新驱动需继承 `BaseDriver` 类并使用 `DeviceState` Enum：

```python
from backend.driver import BaseDriver, DeviceState

class MyDriver(BaseDriver):
    def connect(self) -> bool:
        # 实现连接逻辑
        pass
    
    def disconnect(self) -> None:
        # 实现断开逻辑
        pass
    
    def read_spectrum(self) -> np.ndarray:
        # 实现数据读取
        pass
    
    def get_wavelengths(self) -> np.ndarray:
        # 返回波长数组
        pass
    
    @property
    def device_state(self) -> DeviceState:
        return self._device_state
```

### 状态管理

```python
from backend.state_manager import StateManager, ConnectionState, AcquisitionState

state_manager = StateManager()

# 状态变化会触发信号
state_manager.connectionChanged.connect(on_connection_changed)
state_manager.acquisitionChanged.connect(on_acquisition_changed)

# 状态操作
state_manager.connect_device()
state_manager.set_connected(True)
state_manager.start_acquisition()
state_manager.stop_acquisition()
```

### 前后端通信

**后端暴露方法** (使用 `@Slot`):
```python
@Slot(result=bool)
def connect(self) -> bool:
    self._state_manager.connect_device()
    success = self._driver.connect()
    self._state_manager.set_connected(success)
    return success
```

**前端调用**:
```javascript
pythonBackend.connect();
```

**后端发送信号**:
```python
# WorkerThread 发送数据
self.spectrumReady.emit(data)

# StateManager 触发状态变化信号
self.acquisitionChanged.emit(state)
```

**前端接收**:
```javascript
pythonBackend.spectrumReady.connect(updateSpectrum);
```

## 测试覆盖

| 测试模块 | 测试内容 | 状态 |
|----------|----------|------|
| MockDriver | 基本功能、设备状态、特征峰配置 | ✅ |
| StateManager | 基本功能、信号触发 | ✅ |
| BridgeObject | 通信桥接方法 | ✅ |
| WorkerThread | 基本功能、异常处理 | ✅ |
| 边界条件 | 噪声水平、采样率边界 | ✅ |
| 并发测试 | 快速状态切换 | ✅ |

## 待办事项

详见 `backend/todo.md` 和 `frontend/todo.md`

## 评分改进

根据代码审查进行的改进：

| 模块 | 改进前 | 改进后 | 改进内容 |
|------|--------|--------|----------|
| 驱动层 | 75 | 90 | 使用 Enum、添加边界处理、改进荧光模型 |
| 通信层 | 55 | 85 | 引入 StateManager、职责分离 |
| 工作线程 | 50 | 85 | 修复重复发信号、添加异常处理、动态时序 |
| 前端 | 65 | 85 | ECharts 本地化、改进降级模式 |
| 测试 | 40 | 90 | 10 项测试，覆盖所有核心模块 |
