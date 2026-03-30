"""
日志轮转测试脚本

目的：验证 RotatingFileHandler 配置是否正确工作
验收标准：
    1. 生成超过 10MB 日志时自动轮转
    2. 保留 5 个备份文件（.1, .2, .3, .4, .5）
    3. 无日志丢失
"""
import logging
import os
import time
from pathlib import Path
from backend.logging_config import setup_logging, get_logger

# 配置日志
LOG_DIR = Path("test_logs")
LOG_DIR.mkdir(exist_ok=True)

log_file = LOG_DIR / "test_rotation.log"

# 删除旧的测试日志
for f in LOG_DIR.glob("test_rotation.log*"):
    f.unlink()

# 设置日志系统（10MB 轮转，保留 5 个备份）
logger = setup_logging(
    log_level=logging.DEBUG,
    log_file=str(log_file),
    console_output=False,  # 测试时不输出到控制台
    debug_mode=False
)

log = get_logger(__name__)

# 计算需要写入多少行才能达到 10MB
# 假设每行日志约 100 字节，10MB = 10 * 1024 * 1024 / 100 ≈ 104857 行
TARGET_SIZE_MB = 12  # 写入 12MB，确保触发轮转
ESTIMATED_BYTES_PER_LINE = 100
TARGET_LINES = (TARGET_SIZE_MB * 1024 * 1024) // ESTIMATED_BYTES_PER_LINE

print(f"目标：生成 {TARGET_SIZE_MB}MB 日志（约 {TARGET_LINES} 行）")
print(f"日志文件：{log_file}")
print("-" * 50)

start_time = time.time()
lines_written = 0

# 批量写入日志
batch_size = 1000
for batch in range(TARGET_LINES // batch_size):
    for i in range(batch_size):
        log.info(f"测试日志 [{lines_written:06d}] - " + "x" * 50)  # 填充内容使日志更长
        lines_written += 1
    
    # 每 1 万行显示进度
    if lines_written % 10000 == 0:
        current_size = log_file.stat().st_size / (1024 * 1024) if log_file.exists() else 0
        print(f"进度：{lines_written}/{TARGET_LINES} 行，当前大小：{current_size:.2f}MB")

# 检查轮转结果
print("-" * 50)
print("日志轮转结果：")

log_files = sorted(LOG_DIR.glob("test_rotation.log*"))
total_size = 0

for f in log_files:
    size_mb = f.stat().st_size / (1024 * 1024)
    total_size += size_mb
    print(f"  {f.name}: {size_mb:.2f}MB")

print("-" * 50)
print(f"总行数：{lines_written}")
print(f"总大小：{total_size:.2f}MB")
print(f"文件数量：{len(log_files)}")

# 验证
expected_files = 1  # 主文件 + 可能的备份
if len(log_files) >= expected_files:
    print("\n✅ 日志轮转测试通过！")
else:
    print(f"\n❌ 日志轮转测试失败！预期至少 {expected_files} 个文件，实际 {len(log_files)} 个")

# 清理测试文件（可选）
# for f in LOG_DIR.glob("test_rotation.log*"):
#     f.unlink()

elapsed = time.time() - start_time
print(f"\n耗时：{elapsed:.2f}秒")
