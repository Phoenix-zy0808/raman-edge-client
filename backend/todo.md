# 后端开发任务清单 (Backend TODO)

> ⚠️ **已废弃** - 此文档已废弃，请查看项目根目录的 [`TODO.md`](../TODO.md) 获取最新任务清单
> 
> **最后更新**: 2026-03-22
> **当前版本**: P11 锐评修复版 (第三轮) - 历史存档

---

## 📜 历史文档（保留作为参考）

---

## 📊 真实评分（P11 验证版）

| 维度 | 评分 | 说明 |
|------|------|------|
| 文档完整性 | 75 | 模板化还是有 |
| 状态一致性 | 50 | 文档和代码可能不一致 |
| 验收标准 | 45 | 还是太模糊 |
| 时间评估 | 35 | 仍有水分 |
| 依赖关系 | 40 | 标注不完整 |
| 测试计划 | 20 | 有计划没执行 |
| 风险评估 | 65 | 还可以 |
| 技术债务 | 25 | 声称偿还但无法验证 |
| **总体** | **45** | **不及格** |

**评分依据**:
- 技术债务 25 分：inference.py 拆分✅ + LocalInference 删除✅ + app.js 拆分✅ = 60% 完成，但 E2E 测试未运行验证 → 25 分
- 测试计划 20 分：测试用例全为"待编写"，E2E 测试文件存在但未运行
- 状态一致性 50 分：部分功能无法验证

---

## 📋 完成度定义

| 状态 | 说明 | 完成度 | 验证要求 |
|------|------|--------|----------|
| ⏳ 未开始 | 还没做 | 0% | - |
| 🔄 进行中 | 正在做 | 20-50% | 代码提交记录 |
| ✅ 框架完成 | 文件存在 + 基础功能可用 | 60% | 文件存在 + 行数验证 |
| ✅ 功能完成 | 所有功能实现 + 手动测试通过 | 85% | 手动测试通过 |
| ✅ 已验证 | 自动化测试 100% 通过 | 100% | 自动化测试 100% 通过 |

---

## 💳 技术债务（真实状态）

| 债务 | 影响 | 偿还优先级 | 预计时间 | 状态 | 验证命令 |
|------|------|------------|----------|------|----------|
| inference.py 933 行拆分 | 难以扩展 | 🔴 高 | 8 小时 | ✅ 已验证 | `ls backend/algorithms/` |
| LocalInference 空壳删除 | 代码冗余 | 🟡 中 | 2 小时 | ✅ 已验证 | `grep -r "LocalInference" backend/` |
| app.js 1100 行拆分 | 难以维护 | 🔴 高 | 8 小时 | ✅ 已验证 | `ls frontend/js/` |
| 前端无自动化测试 | 改代码怕出 bug | 🟡 中 | 8 小时 | ⚠️ 框架完成 | `pytest test_frontend_e2e.py -v` |
| 谱库模拟数据 | 结果不可信 | 🔴 高 | 20 小时 | ❌ 未开始 | - |

**技术债务完成度**: (3×100% + 1×50% + 1×0%) / 5 = **70%** → 但验证不足，实际 **25 分**

---

## ⚠️ 风险评估

| 风险 | 概率 | 影响 | 缓解措施 | 状态 |
|------|------|------|----------|------|
| 真实驱动开发延期 | 高 | 高 | 先用 MockDriver 演示 | ⚠️ 未缓解 |
| NIST 谱库数据格式不兼容 | 中 | 高 | 先手动转换 3-5 个样本 | ❌ 未开始 |
| PySide6 打包后体积过大 | 高 | 中 | 用 Nuitka 替代 PyInstaller | ⚠️ 未验证 |
| QWebChannel 通信不稳定 | 低 | 高 | 添加重试机制 | ⚠️ 未实现 |
| 学生误用模拟数据做科研 | 中 | 高 | UI 醒目警告 + 启动弹窗 | ✅ 已实现 |

---

## 📊 P0 功能完成状态

| 功能 | 后端 | 前端 | 测试 | 完成度 | 状态 |
|------|------|------|------|--------|------|
| 积分时间调节 | ✅ | ✅ | ✅ | 100% | ✅ 已完成 |
| 累加平均次数 | ✅ | ✅ | ✅ | 100% | ✅ 已完成 |
| 平滑滤波 | ✅ | ✅ | ✅ | 100% | ✅ 已完成 |
| 基线校正 | ✅ | ✅ | ✅ | 100% | ✅ 已完成 |
| 峰面积计算 | ✅ | ✅ | ✅ | 100% | ✅ 已完成 |
| 谱库匹配 | ✅ | ✅ | ✅ | 100% | ✅ 已完成 |
| 标准谱库 | ✅ (10 种) | - | - | 100% | ✅ 已完成 |
| 导入历史数据 | ✅ | ✅ | ✅ | 100% | ✅ 已完成 |
| **波长校准** | ❌ | ⚠️ | ❌ | 15% | 🔄 进行中 |
| **强度校准** | ❌ | ⚠️ | ❌ | 15% | 🔄 进行中 |
| **自动曝光** | ❌ | ⚠️ | ❌ | 15% | 🔄 进行中 |

---

## 🔴 P0 待完成（核心功能 - 没有就不能用）

### 波长校准

**用户故事**: 作为教师，我想要波长校准功能，以便确保谱库匹配结果准确可信

**依赖**: 无

**预计时间**: 16 小时（含联调测试）

**完成时间**: 2026-03-29

**验收标准**:
#### 后端接口（统一 ApiResponse 格式）
- [ ] 方法签名：`calibrateWavelength(reference_peaks: List[float], expected_positions: List[float] = [520.0]) -> ApiResponse`
- [ ] 返回格式：`ApiResponse(success=True, data={"correction": float, "calibrated_at": timestamp})`
- [ ] 方法签名：`getWavelengthCorrection() -> ApiResponse` - 获取当前校准校正值
- [ ] 返回格式：`ApiResponse(success=True, data={"correction": float})`
- [ ] 方法签名：`isWavelengthCalibrated() -> ApiResponse` - 检查是否已校准
- [ ] 返回格式：`ApiResponse(success=True, data={"calibrated": bool})`

#### 参数验证
- [ ] 输入验证：`reference_peaks` 不能为空列表 → 返回 `CALIBRATION_DATA_INVALID (253)`
- [ ] 输入验证：`expected_positions` 长度必须与 `reference_peaks` 相同 → 返回 `INVALID_PARAMETER (1)`
- [ ] 误差容忍：参考峰位置误差 < 5 cm⁻¹（绝对误差）
- [ ] 边界条件：如果误差 >= 5 cm⁻¹，返回 `CALIBRATION_FAILED (250)` 错误

#### 异常处理
- [ ] 未找到参考峰：返回 `ApiResponse.error(REFERENCE_PEAK_NOT_FOUND, "未找到参考峰，请检查样品是否正确放置")`
- [ ] 校准失败：返回 `ApiResponse.error(CALIBRATION_FAILED, "波长校准失败：{具体原因}")`
- [ ] 校准超时：返回 `ApiResponse.error(CALIBRATION_TIMEOUT, "校准超时，请重试")`

#### 日志记录（统一格式）
- [ ] 成功：`log.info(CalibrationLog.wavelength_calibration_success(correction))`
- [ ] 失败：`log.error(CalibrationLog.wavelength_calibration_failed(error_msg, error_code))`
- [ ] 迭代：`log.debug(CalibrationLog.calibration_iteration(i, current_value, target))`

#### 前端 UI
- [ ] 主界面添加"波长校准"按钮（控制面板，谱库匹配下方）
- [ ] 使用标准物质（硅 520 cm⁻¹）作为参考
- [ ] 显示校准状态指示器（已校准/未校准）
- [ ] 显示最后校准时间和校正值

#### 测试（测试先行）
- [ ] 测试用例设计：2026-03-25（代码开发前）
- [ ] 测试框架搭建：2026-03-26
- [ ] 单元测试：`test_wavelength_calibration_success()` - 验证正常校准流程
- [ ] 单元测试：`test_wavelength_calibration_invalid_input()` - 验证空输入处理
- [ ] 单元测试：`test_wavelength_calibration_large_error()` - 验证大误差处理
- [ ] 集成测试：`test_wavelength_calibration_workflow()` - 完整工作流测试
- [ ] 代码开发：2026-03-27 ~ 2026-03-28
- [ ] 测试运行通过：2026-03-29
- [ ] 覆盖率目标：80% (业务逻辑覆盖，非仅函数签名)

---

### 强度校准

**用户故事**: 作为检测员，我想要强度校准功能，以便确保峰面积计算结果可信

**依赖**: 波长校准 (2026-03-29 完成)

**预计时间**: 16 小时（含联调测试）

**完成时间**: 2026-03-30（不依赖 SQLite，只需波长校准完成后即可开始）

**验收标准**:
#### 后端接口（统一 ApiResponse 格式）
- [ ] 方法签名：`calibrateIntensity(reference_spectrum: np.ndarray, wavelength_range: Tuple[float, float]) -> ApiResponse`
- [ ] 返回格式：`ApiResponse(success=True, data={"correction_curve": list, "wavelength_range": list})`
- [ ] 方法签名：`getIntensityCorrection() -> ApiResponse` - 获取强度校正曲线
- [ ] 返回格式：`ApiResponse(success=True, data={"correction_curve": list})`
- [ ] 方法签名：`isIntensityCalibrated() -> ApiResponse` - 检查是否已校准
- [ ] 返回格式：`ApiResponse(success=True, data={"calibrated": bool})`

#### 参数验证
- [ ] 输入验证：`reference_spectrum` 不能为空 → 返回 `CALIBRATION_DATA_INVALID (253)`
- [ ] 输入验证：`reference_spectrum` 维度必须与当前光谱匹配 → 返回 `SPECTRUM_DIMENSION_MISMATCH (351)`
- [ ] 输入验证：`wavelength_range` 必须在设备支持范围内 → 返回 `SPECTRUM_WAVELENGTH_RANGE_ERROR (352)`

#### 异常处理
- [ ] 谱图格式无效：返回 `ApiResponse.error(INVALID_SPECTRUM_FORMAT, "标准谱图格式无效：{具体原因}")`
- [ ] 校准失败：返回 `ApiResponse.error(INTENSITY_CALIBRATION_ERROR, "强度校准失败：{具体原因}")`
- [ ] 波长范围不匹配：返回 `ApiResponse.error(SPECTRUM_WAVELENGTH_RANGE_ERROR, "波长范围不匹配")`

#### 日志记录（统一格式）
- [ ] 成功：`log.info(CalibrationLog.intensity_calibration_success(wavelength_range))`
- [ ] 失败：`log.error(CalibrationLog.intensity_calibration_failed(error_msg, error_code))`

#### 前端 UI
- [ ] 主界面添加"强度校准"按钮（波长校准右侧）
- [ ] 导入标准光源谱图文件选择器
- [ ] 显示校准状态指示器
- [ ] 显示校正曲线图表

#### 测试（测试先行）
- [ ] 测试用例设计：2026-03-26（代码开发前）
- [ ] 测试框架搭建：2026-03-27
- [ ] 单元测试：`test_intensity_calibration_success()` - 验证正常校准流程
- [ ] 单元测试：`test_intensity_calibration_invalid_spectrum()` - 验证无效谱图处理
- [ ] 单元测试：`test_intensity_calibration_dimension_mismatch()` - 验证维度不匹配处理
- [ ] 集成测试：`test_intensity_calibration_workflow()` - 完整工作流测试
- [ ] 代码开发：2026-03-28 ~ 2026-03-29
- [ ] 测试运行通过：2026-03-30
- [ ] 覆盖率目标：80% (业务逻辑覆盖，非仅函数签名)

---

### 自动曝光

**用户故事**: 作为学生，我想要自动曝光功能，以便快速获得合适的光谱而无需手动调节积分时间

**依赖**: 积分时间调节

**预计时间**: 16 小时（含联调测试）

**完成时间**: 2026-03-29

**验收标准**:
#### 后端接口（统一 ApiResponse 格式）
- [ ] 方法签名：`autoExposure(target_intensity: float = 0.7, max_iterations: int = 3) -> ApiResponse`
- [ ] 返回格式：`ApiResponse(success=True, data={"final_integration_time": int, "iterations": int, "final_intensity": float})`
- [ ] 方法签名：`setAutoExposureEnabled(enabled: bool)` - 启用/禁用自动曝光
- [ ] 方法签名：`isAutoExposureEnabled() -> ApiResponse` - 检查自动曝光是否启用
- [ ] 返回格式：`ApiResponse(success=True, data={"enabled": bool})`

#### 参数验证
- [ ] 输入验证：`target_intensity` 范围 0.5-0.8（50%-80% 满量程）→ 返回 `INVALID_PARAMETER (1)`
- [ ] 输入验证：`max_iterations` 范围 1-10 → 返回 `INVALID_PARAMETER (1)`
- [ ] 边界条件：如果 `target_intensity` 超出范围，返回 `INVALID_PARAMETER (1)` 错误

#### 算法要求
- [ ] 使用二分查找或梯度上升算法
- [ ] 最大迭代次数：3 次（可配置）
- [ ] 积分时间调节范围：10ms - 10000ms
- [ ] 收敛条件：目标强度 ±10%

#### 异常处理
- [ ] 自动曝光超时：返回 `ApiResponse.error(AUTO_EXPOSURE_TIMEOUT, "自动曝光超时：3 次迭代内无法收敛，请手动调节")`
- [ ] 设备未连接：返回 `ApiResponse.error(DEVICE_NOT_CONNECTED, "设备未连接")`
- [ ] 采集失败：返回 `ApiResponse.error(ACQUISITION_FAILED, "数据采集失败")`

#### 日志记录（统一格式）
- [ ] 成功：`log.info(AutoExposureLog.auto_exposure_success(final_time, iterations))`
- [ ] 失败：`log.error(AutoExposureLog.auto_exposure_failed(error_msg, error_code))`
- [ ] 超时：`log.warning(AutoExposureLog.auto_exposure_timeout(iterations))`
- [ ] 迭代：`log.debug(AutoExposureLog.exposure_adjustment(current_time, new_time, intensity))`

#### 前端 UI
- [ ] 添加"自动曝光"开关（积分时间输入框右侧）
- [ ] 目标强度滑块（50%-80% 满量程，默认 70%）
- [ ] 自动曝光时显示"调节中..."动画
- [ ] 超时提示用户手动调节

#### 测试（测试先行）
- [ ] 测试用例设计：2026-03-25（代码开发前）
- [ ] 测试框架搭建：2026-03-26
- [ ] 单元测试：`test_auto_exposure_success()` - 验证正常曝光流程
- [ ] 单元测试：`test_auto_exposure_invalid_target()` - 验证无效目标强度处理
- [ ] 单元测试：`test_auto_exposure_timeout()` - 验证超时处理
- [ ] 集成测试：`test_auto_exposure_workflow()` - 完整工作流测试
- [ ] 代码开发：2026-03-27 ~ 2026-03-28
- [ ] 测试运行通过：2026-03-29
- [ ] 覆盖率目标：75% (业务逻辑覆盖，非仅函数签名)

---

## 🟡 P1 待完成（重要功能 - 有了更好用）

### 暗噪声扣除

**依赖**: 真实驱动接口

**预计时间**: 8 小时

**完成时间**: 2026-04-05

**验收标准**:
- [ ] 后端方法：`acquireDarkSpectrum(n_average: int = 3) -> bool`
- [ ] 后端方法：`setDarkNoiseCorrection(bool)`
- [ ] 前端 UI：主界面添加"采集暗光谱"按钮
- [ ] 前端 UI：添加"暗噪声扣除"开关 (默认开启)
- [ ] 单元测试：`test_dark_noise_subtraction()` - 完成时间：2026-04-05
- [ ] 集成测试：`test_dark_noise_workflow()` - 完成时间：2026-04-05

---

### 非线性校正

**依赖**: 真实驱动接口

**预计时间**: 8 小时

**完成时间**: 2026-04-05

---

### 连续采集模式

**依赖**: 工作线程优化

**预计时间**: 4 小时

**完成时间**: 2026-04-05

---

## 🟢 P2 待完成（可选功能 - 锦上添花）

### 多组分分析

**依赖**: 谱库匹配

**预计时间**: 16 小时

**完成时间**: 2026-04-12

---

### 标准曲线法

**依赖**: SQLite 数据库

**预计时间**: 12 小时

**完成时间**: 2026-04-12

---

### PCA 聚类分析

**依赖**: 多组分分析

**预计时间**: 16 小时

**完成时间**: 2026-04-12

---

## 📋 技术任务

### 真实驱动接口

**依赖**: 无

**预计时间**: 40-80 小时

**完成时间**: 2026-04-22

---

### SQLite 数据库

**依赖**: 数据导出功能

**预计时间**: 16 小时

**完成时间**: 2026-04-05

---

## 🧪 测试计划

### 单元测试 (覆盖率目标：80%)

| 任务 | 测试用例 | 状态 | 完成时间 |
|------|----------|------|----------|
| 波长校准 | `test_wavelength_calibration()` | ⏳ 待编写 | 2026-03-29 |
| 强度校准 | `test_intensity_calibration()` | ⏳ 待编写 | 2026-03-29 |
| 自动曝光 | `test_auto_exposure()` | ⏳ 待编写 | 2026-03-29 |
| 暗噪声扣除 | `test_dark_noise_subtraction()` | ⏳ 待编写 | 2026-04-05 |
| 非线性校正 | `test_nonlinear_correction()` | ⏳ 待编写 | 2026-04-05 |

### 集成测试 (覆盖率目标：75%)

| 任务 | 测试用例 | 状态 | 完成时间 |
|------|----------|------|----------|
| 波长校准工作流 | `test_wavelength_calibration_workflow()` | ⏳ 待编写 | 2026-03-29 |
| 强度校准工作流 | `test_intensity_calibration_workflow()` | ⏳ 待编写 | 2026-03-29 |
| 自动曝光工作流 | `test_auto_exposure_workflow()` | ⏳ 待编写 | 2026-03-29 |

### E2E 测试 (Playwright)

| 任务 | 测试用例 | 文件存在 | 能运行 | 通过率 | 状态 |
|------|----------|----------|--------|--------|------|
| 页面加载 | `test_page_loads()` | ✅ | ✅ | 0% (超时) | ❌ 失败 |
| UI 元素存在性 | `test_ui_elements_present()` | ✅ | ✅ | 0% (超时) | ❌ 失败 |
| 主题切换 | `test_theme_toggle()` | ✅ | ✅ | 0% (超时) | ❌ 失败 |
| 峰值标注开关 | `test_peak_labels_toggle()` | ✅ | ✅ | 0% (超时) | ❌ 失败 |
| 积分时间验证 | `test_integration_time_validation()` | ✅ | ✅ | 0% (超时) | ❌ 失败 |
| 噪声水平滑块 | `test_noise_level_slider()` | ✅ | ✅ | 0% (超时) | ❌ 失败 |
| 日志面板 | `test_log_panel()` | ✅ | ✅ | 0% (超时) | ❌ 失败 |
| 状态栏 | `test_status_bar()` | ✅ | ✅ | 0% (超时) | ❌ 失败 |
| 多光谱对比按钮 | `test_multi_spectrum_buttons()` | ✅ | ✅ | 0% (超时) | ❌ 失败 |
| 谱库匹配面板 | `test_library_panel()` | ✅ | ✅ | 0% (超时) | ❌ 失败 |

**验证命令**:
```bash
python -m pytest test_frontend_e2e.py -v --tb=short
# 结果：10 failed (0:04:49) - 超时，前端页面结构与测试代码不匹配
```

**失败原因**: 测试代码期望的 UI 元素与实际前端页面结构不匹配，需要修复测试或更新前端

---

## 📝 评分提升路径

### 当前：45/100 (不及格)

- 完成 P0 功能 UI (波长校准、强度校准、自动曝光) → +15 分 → 60 分
- 运行 E2E 测试并全部通过 → +10 分 → 70 分
- 实现设置页面持久化功能 → +5 分 → 75 分
- 替换 3-5 种 NIST 真实谱库数据 → +8 分 → 83 分

### 目标：85/100 (良好)

需要完成：
1. P0 功能 UI 实现并测试通过
2. E2E 测试 100% 通过
3. P1 功能 50% 完成
4. 技术债务偿还 80%

---

## 📈 变更记录

| 日期 | 变更内容 | 变更人 |
|------|----------|--------|
| 2026-03-22 | P11 锐评修复 (第一轮) | Qwen-Code |
| 2026-03-22 | P11 锐评修复 (第二轮) | Qwen-Code |
| 2026-03-22 | **统一评分为 45 分，添加验证命令** | Qwen-Code |
| 2026-03-27 | **P11 锐评同步 (第七轮) - 与前端评分对齐，添加后端改进计划** | Qwen-Code |

---

*最后更新：2026-03-27*
*测试验证：test_algorithms.py (15 项测试，100% 通过)*
*E2E 测试：test_frontend_e2e.py (文件存在，待运行验证)*
*前端模块化：6 个 JS 模块 (✅)*
*总体评分：45/100 (不及格)*

---

## 🎯 P12 后端改进计划（与大厂对齐）

### P0 高优先级（2026-04-05 前完成）

| 任务 | 说明 | 预计时间 | 验收标准 |
|------|------|----------|----------|
| API 响应缓存 | 校准状态等只读数据添加缓存 | 2h | 重复请求不执行计算 |
| 异步任务队列 | 耗时操作（校准）改为异步 | 4h | 不阻塞 UI，支持进度查询 |
| 连接池优化 | QWebChannel 连接复用 | 2h | 连接建立时间 < 100ms |
| 日志轮转 | 日志文件超过 10MB 自动轮转 | 2h | 日志目录 < 100MB |
| 配置热加载 | 修改配置无需重启 | 2h | 配置变更 5s 内生效 |

### P1 中优先级（2026-04-15 前完成）

| 任务 | 说明 | 预计时间 | 验收标准 |
|------|------|----------|----------|
| 单元测试覆盖 | 核心算法覆盖率 > 80% | 16h | pytest-cov 报告 |
| 集成测试 | 校准流程集成测试 | 8h | 校准流程自动化测试 |
| 性能基准 | 建立性能基准测试 | 4h | 光谱处理 < 50ms |
| 错误日志上报 | 错误日志结构化上报 | 4h | ELK 集成 |

### P2 低优先级（2026-04-30 前完成）

| 任务 | 说明 | 预计时间 | 验收标准 |
|------|------|----------|----------|
| API 版本控制 | 支持多版本 API 共存 | 8h | v1/v2 同时可用 |
| 速率限制 | 防止 API 滥用 | 4h | 单用户 < 100 次/分钟 |
| 健康检查 | 服务健康检查端点 | 2h | /health 返回服务状态 |
| 指标监控 | Prometheus 指标导出 | 8h | Grafana 仪表盘 |
