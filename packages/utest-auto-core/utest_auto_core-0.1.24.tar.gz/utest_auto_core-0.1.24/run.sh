#!/bin/bash

cd "$(dirname "$0")"
set -x

# 创建虚拟环境
uv venv --python 3.10.12
source .venv/bin/activate

# 安装依赖
uv pip install -U -r requirements.txt --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 获取参数
jobid=${1}        # 任务ID
serials=${2}      # 设备序列号
osType=${3}       # 操作系统类型 (android/ios/hm)
appName=${4}      # 应用包名
authcode=${5}     # 设备认证码

# 获取第6个参数及以后的所有参数（资源信息）
# 使用 shift 跳过前5个参数，剩余的都是资源信息
shift 5
resource_args=("$@")  # 将所有剩余参数保存到数组中

# 清理垃圾进程
ps -ef | grep 'uv run start_test.py' | grep ''$serials'' | awk '{print "kill -9 " $2}' | sh

# 更新配置文件中的任务参数
echo "更新配置文件中的任务参数..."
# 将资源参数数组展开传递给 update_config.py
uv run update_config.py "${jobid}" "${serials}" "${osType}" "${appName}" "${authcode}" "${resource_args[@]}"

# 执行测试框架（从配置文件读取参数）
uv run start_test.py > u2at_${jobid}_${serials}.log
test_res=$?

# 根据测试结果设置返回码
if [ "$test_res" -eq "0" ]; then
    echo "ResultCode:0:0:"
elif [ "$test_res" -eq "17" ]; then
    echo "ResultCode:17:8:"
elif [ "$test_res" -eq "18" ]; then
    echo "ResultCode:18:8:"
elif [ "$test_res" -eq "2" ]; then
    echo "ResultCode:2:8:"
elif [ "$test_res" -eq "3" ]; then
    echo "ResultCode:3:8:"
else
    echo "ResultCode:$test_res:0:"
fi

ps -ef | grep 'uv run start_test.py' | grep ''$serials'' | awk '{print "kill -9 " $2}' | sh

# 清理环境
rm -rf .venv
