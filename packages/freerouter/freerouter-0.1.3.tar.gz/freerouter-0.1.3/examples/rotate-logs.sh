#!/bin/bash
# FreeRouter 简易日志轮转脚本
#
# 使用方法：
# 1. chmod +x rotate-logs.sh
# 2. ./rotate-logs.sh
# 3. 或添加到 crontab: 0 0 * * * /path/to/rotate-logs.sh

# 配置
LOG_DIR="$HOME/.config/freerouter"
LOG_FILE="$LOG_DIR/freerouter.log"
KEEP_DAYS=7
MAX_SIZE_MB=100

# 检查日志文件是否存在
if [ ! -f "$LOG_FILE" ]; then
    echo "日志文件不存在: $LOG_FILE"
    exit 0
fi

# 获取文件大小（MB）
FILE_SIZE=$(du -m "$LOG_FILE" | cut -f1)

# 检查是否需要轮转
if [ "$FILE_SIZE" -lt "$MAX_SIZE_MB" ]; then
    echo "日志文件大小 ${FILE_SIZE}MB，未达到轮转阈值 ${MAX_SIZE_MB}MB"
    exit 0
fi

echo "开始轮转日志..."

# 生成时间戳
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$LOG_DIR/freerouter.log.${TIMESTAMP}"

# 复制并清空当前日志
cp "$LOG_FILE" "$BACKUP_FILE"
echo "" > "$LOG_FILE"

# 压缩备份
gzip "$BACKUP_FILE"
echo "✓ 已创建备份: freerouter.log.${TIMESTAMP}.gz"

# 删除超过 N 天的旧日志
find "$LOG_DIR" -name "freerouter.log.*.gz" -type f -mtime +$KEEP_DAYS -delete
echo "✓ 已删除超过 ${KEEP_DAYS} 天的旧日志"

# 显示当前日志文件
echo ""
echo "当前日志文件："
ls -lh "$LOG_DIR"/freerouter.log*

echo ""
echo "日志轮转完成！"
