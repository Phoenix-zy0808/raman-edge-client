# 前端开发任务清单 (Frontend TODO)

> ⚠️ **已废弃** - 此文档已废弃，请查看项目根目录的 [`TODO.md`](../TODO.md) 获取最新任务清单
> 
> **最后更新**: 2026-03-27
> **当前版本**: P11 锐评重构版 (第八轮) - 历史存档

---

## 📜 历史文档（保留作为参考）

---

## 📋 P0 高优先级任务（本周内完成）

| ID | 任务 | 说明 | 预计时间 | 验收标准 | 状态 |
|----|------|------|----------|----------|------|
| P0-01 | 修复 E2E 测试超时 | TIMEOUT 3000→10000 | 0.5h | 10 项测试全部通过 | ✅ 已完成 |
| P0-02 | 集成 cache.js 到 bridge.js | SWR 缓存校准状态 | 2h | 校准状态请求减少 60% | ✅ 已完成 |
| P0-03 | 集成 theme.js 到 main.js | 8 种预设主题切换 | 2h | 主题可切换并持久化 | ✅ 已完成 |
| P0-04 | 集成 virtual-scroll.js | 日志面板虚拟滚动 | 2h | 1000+ 条日志流畅滚动 | ✅ 已完成 |
| P0-05 | 更新 todo.md 状态 | 删除评分表格 | 1h | 验证命令全部通过 | ✅ 已完成 |

---

## 📋 P1 中优先级任务（两周内完成）

| ID | 任务 | 说明 | 预计时间 | 验收标准 | 状态 |
|----|------|------|----------|----------|------|
| P1-01 | bridge.js 单元测试 | 核心通信层测试 | 8h | 覆盖率>80% | ⏳ 待开始 |
| P1-02 | 波长校准 UI 联调 | 前端按钮触发后端校准 | 4h | 校准功能完整可用 | ⏳ 待开始 |
| P1-03 | 自动曝光 UI 联调 | 开关控制自动曝光 | 4h | 自动曝光功能完整 | ⏳ 待开始 |
| P1-04 | API 响应格式测试 | 验证所有 API 返回格式 | 2h | 所有 API 返回 ApiResponse | ⏳ 待开始 |
| P1-05 | postMessage 源验证 | 指定目标源，不使用通配符 | 1h | 安全扫描通过 | ⏳ 待开始 |

---

## 📋 P2 低优先级任务（一个月内完成）

| ID | 任务 | 说明 | 预计时间 | 验收标准 | 状态 |
|----|------|------|----------|----------|------|
| P2-01 | main.js 拆分 | 拆分为 3 个模块 | 4h | app-lifecycle.js、event-bus.js | ⏳ 待开始 |
| P2-02 | 事件总线引入 | 模块间解耦 | 4h | 移除全局回调 | ⏳ 待开始 |
| P2-03 | NIST 谱库替换 | 3-5 种真实谱图 | 8h | 真实化合物谱图 | ⏳ 待开始 |
| P2-04 | 性能基准测试 | 光谱处理<50ms | 4h | 性能报告 | ⏳ 待开始 |

---

## 📁 文件结构验证

### 前端模块化验证

```
frontend/js/
├── main.js          # 511 行 - 应用入口
├── chart.js         # 389 行 - 图表渲染
├── bridge.js        # 719 行 - 后端通信（含 SWR 缓存）
├── ui.js            # 847 行 - UI 操作
├── utils.js         # 469 行 - 工具函数
├── state.js         # 277 行 - 状态管理
├── cache.js         # 346 行 - SWR 缓存
├── theme.js         # 464 行 - 主题管理
├── virtual-scroll.js# 392 行 - 虚拟滚动
├── skeleton.js      # 338 行 - 骨架屏
├── types.js         # 356 行 - 类型定义
├── peaks.js         # 383 行 - 峰值检测
├── difference.js    # 差异对比
└── live.js          # 实时数据
```

**验证命令**:
```bash
ls -la frontend/js/
python scripts/verify_status.py --frontend-modules
```

### 页面框架验证

```
frontend/
├── index.html       # 主页面
└── pages/
    ├── settings.html    # 设置页面（持久化）
    ├── calibration.html # 校准页面（波长/强度校准）
    ├── library.html     # 谱库匹配
    ├── history.html     # 历史记录
    ├── report.html      # 报告生成
    └── about.html       # 关于页面
```

**验证命令**:
```bash
ls -la frontend/ frontend/pages/
python scripts/verify_status.py --frontend-pages
```

---

## 🧪 测试状态

### E2E 测试 (Playwright)

| 测试项 | 状态 | 说明 |
|--------|------|------|
| test_page_loads | ✅ 通过 | 页面加载验证 |
| test_ui_elements_present | ✅ 通过 | UI 元素存在性 |
| test_theme_toggle_button_exists | ✅ 通过 | 主题切换按钮 |
| test_peak_labels_button_exists | ✅ 通过 | 峰值标注按钮 |
| test_integration_time_input_exists | ✅ 通过 | 积分时间输入 |
| test_noise_level_slider_exists | ✅ 通过 | 噪声水平滑块 |
| test_log_panel_exists | ✅ 通过 | 日志面板 |
| test_status_bar_exists | ✅ 通过 | 状态栏 |
| test_multi_spectrum_button_exists | ✅ 通过 | 多光谱对比按钮 |
| test_library_panel_exists | ✅ 通过 | 谱库匹配面板 |

**运行命令**:
```bash
python -m pytest test_frontend_e2e.py -v
```

### 单元测试 (Vitest)

| 模块 | 测试文件 | 覆盖率目标 | 状态 |
|------|----------|------------|------|
| bridge.js | test_bridge.test.js | 80% | ⏳ 待开始 |
| state.js | test_state.test.js | 90% | ⏳ 待开始 |
| types.js | test_types.test.js | 80% | ⏳ 待开始 |
| utils.js | test_utils.test.js | 75% | ⏳ 待开始 |
| cache.js | test_cache.test.js | 85% | ⏳ 待开始 |
| theme.js | test_theme.test.js | 70% | ⏳ 待开始 |

**运行命令**:
```bash
npm test
```

---

## 💳 技术债务清单

| 债务 | 影响 | 优先级 | 状态 | 验证命令 |
|------|------|--------|------|----------|
| 全局回调耦合 | 难以维护 | 🔴 高 | ⏳ 待解决 | 检查 main.js bindGlobalCallbacks |
| 无单元测试 | 质量无保障 | 🔴 高 | ⏳ 待解决 | npm test |
| postMessage 通配符 | 安全隐患 | 🟡 中 | ⏳ 待解决 | 检查 postMessage 调用 |
| 无电路断路器 | 稳定性差 | 🟡 中 | ⏳ 待解决 | 检查 bridge.js 重试机制 |
| 无焦点管理 | A11y 不合规 | 🟡 中 | ⏳ 待解决 | 检查对话框焦点陷阱 |

---

## 📈 变更记录

| 日期 | 变更内容 | 变更人 |
|------|----------|--------|
| 2026-03-27 | P11 锐评重构 (第八轮) - 删除评分表格，改为纯任务清单 | Qwen-Code |
| 2026-03-27 | 修复 E2E 测试超时 (TIMEOUT 3000→10000) | Qwen-Code |
| 2026-03-27 | 验证 E2E 测试 10 项全部通过 | Qwen-Code |

---

## 🔧 验证脚本

运行以下命令验证文档与代码状态一致：

```bash
# 1. 验证所有状态
python scripts/verify_status.py --all

# 2. 验证前端模块
python scripts/verify_status.py --frontend-modules

# 3. 验证技术债务状态
python scripts/verify_status.py --tech-debt

# 4. 验证文件行数
python scripts/verify_status.py --file-lines

# 5. 验证 E2E 测试
python -m pytest test_frontend_e2e.py -v
```

---

*最后更新：2026-03-27*
*前端模块化：12 个 JS 模块 (✅)*
*页面功能：settings.html、calibration.html 功能实现 (✅)*
*状态管理：state.js 统一管理 (✅)*
*SWR 缓存：bridge.js 集成 (✅)*
*主题管理：theme.js 集成 (✅)*
*虚拟滚动：virtual-scroll.js 集成 (✅)*
*E2E 测试：10/10 通过 (✅)*
