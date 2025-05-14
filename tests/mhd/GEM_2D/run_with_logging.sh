
#!/bin/bash
# 获取当前日期时间
timestamp=$(date +"%Y%m%d_%H%M%S")
# 定义日志文件名
log_file="terminal_${timestamp}_running_log.log"
# 运行程序并重定向输出
echo "Starting program, logging to ${log_file}"
./amrvac 2>&1 | tee "${log_file}"
# 记录程序结束状态
echo "Program finished with exit code $?" >> "${log_file}"
