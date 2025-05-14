
#!/bin/bash
# 获取当前日期时间
timestamp=$(date +"%Y%m%d_%H%M%S")
# 定义日志文件名
log_file="terminal_${timestamp}_running_log.log"
# 使用script命令记录完整终端会话
echo "Starting terminal session logging to ${log_file}"
echo "To exit logging session, type 'exit' or press Ctrl-D"
script -a "${log_file}"
