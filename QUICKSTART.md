# 快速开始指南

本指南帮助你快速启动拉曼光谱边缘客户端的前后端服务。

## 目录

1. [环境检查](#环境检查)
2. [安装依赖](#安装依赖)
3. [启动方式](#启动方式)
4. [常见问题](#常见问题)

---

## 环境检查

### Python 环境

```bash
# 检查 Python 版本（要求 3.9+）
python --version

# 检查是否在虚拟环境中
# Windows: 查看命令行前是否有 (.venv)
# 或运行：
python -c "import sys; print('虚拟环境:', sys.prefix)"
```

### Node.js 环境（可选，仅前端开发需要）

```bash
# 检查 Node.js 版本（要求 16+）
node --version

# 检查 npm 版本
npm --version
```

---

## 安装依赖

### 1. 激活虚拟环境

```bash
# Windows (PowerShell 或 CMD)
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

激活成功后，命令行前应该显示 `(.venv)`。

### 2. 安装 Python 依赖

```bash
# 在项目根目录执行
pip install -r requirements.txt
```

这将安装：
- PySide6 (GUI 框架)
- NumPy (科学计算)
- SciPy (科学计算)
- pytest (测试框架)
- playwright (E2E 测试)

### 3. 安装 Node.js 依赖（可选）

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 可选：安装文件监听（开发模式）
npm install chokidar
```

---

## 启动方式

### 方式一：一键启动（推荐）

同时启动前端开发服务器和后端应用。

```bash
# 激活虚拟环境后执行
python scripts/start_all.py
```

**选项:**
```bash
# 仅启动后端（PySide6 内嵌前端）
python scripts/start_all.py --backend-only

# 仅启动前端（HTTP 服务器）
python scripts/start_all.py --frontend-only

# 指定前端端口
python scripts/start_all.py --frontend-port 3000

# 调试模式
python scripts/start_all.py --debug

# 生产模式
python scripts/start_all.py --prod
```

### 方式二：分别启动

**启动后端:**
```bash
# 开发模式
python scripts/start_backend.py

# 调试模式
python scripts/start_backend.py --debug

# 生产模式（禁用日志）
python scripts/start_backend.py --prod
```

**启动前端:**
```bash
# 使用 node
node scripts/start_frontend.js

# 使用 npm
cd frontend && npm run dev

# 指定端口
node scripts/start_frontend.js --port 3000
```

### 方式三：传统启动

```bash
# 直接运行主程序
python run.py
```

---

## 命令行工具

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

---

## 运行测试

```bash
# 算法测试（15 项，100% 通过）
python test_algorithms.py

# 完整测试套件
python test_all.py

# E2E 测试
python -m pytest test_frontend_e2e.py -v

# 单元测试（前端）
cd frontend && npm test
```

---

## 常见问题

### Q1: PySide6 安装失败

**问题:** `pip install PySide6` 失败

**解决:**
```bash
# 升级 pip
python -m pip install --upgrade pip

# 使用清华镜像源
pip install PySide6 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q2: 端口被占用

**问题:** `端口 8080 已被占用`

**解决:**
```bash
# 使用其他端口
node scripts/start_frontend.js --port 3000

# 或查找并关闭占用端口的进程
# Windows:
netstat -ano | findstr :8080
taskkill /PID <PID> /F

# Linux/Mac:
lsof -i :8080
kill -9 <PID>
```

### Q3: Node.js 未安装

**问题:** `node: command not found`

**解决:**
1. 访问 https://nodejs.org/ 下载安装
2. 或使用 nvm (Node Version Manager):
   ```bash
   # Windows (使用 scoop)
   scoop install nodejs

   # Linux/Mac (使用 nvm)
   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
   nvm install 18
   ```

### Q4: 虚拟环境未激活

**问题:** `警告：未使用虚拟环境`

**解决:**
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

如果 `.venv` 不存在：
```bash
# 创建虚拟环境
python -m venv .venv

# 然后激活
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

### Q5: 前端页面无法加载

**问题:** 访问 `http://localhost:8080` 显示空白

**解决:**
1. 检查前端服务器是否启动
2. 检查浏览器控制台是否有错误
3. 尝试清除浏览器缓存
4. 使用无痕模式打开

---

## 快速参考

| 命令 | 说明 |
|------|------|
| `python scripts/start_all.py` | 一键启动前后端 |
| `python scripts/start_backend.py` | 仅启动后端 |
| `node scripts/start_frontend.js` | 仅启动前端 |
| `python run.py` | 传统启动方式 |
| `python cli.py --help` | 命令行工具帮助 |
| `python test_algorithms.py` | 运行算法测试 |

---

## 获取帮助

如有问题，请查看：
- [README.md](README.md) - 项目说明
- [backend/todo.md](backend/todo.md) - 后端任务清单
- [frontend/todo.md](frontend/todo.md) - 前端任务清单
