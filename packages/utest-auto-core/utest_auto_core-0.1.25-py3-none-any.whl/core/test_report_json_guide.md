# Test Report JSON 格式说明文档

## 📋 概述

本文档详细说明了精简后的 `test-report.json` 文件格式。该JSON报告消除了数据重复，提高了数据准确性，并支持ubox和旧格式性能数据的统一处理。

## 🏗️ 整体结构

```json
{
  "report_info": {},           // 报告基本信息
  "summary": {},               // 测试汇总统计
  "device_info": {},           // 设备信息
  "test_results": [],          // 测试结果详情
  "log_data": {},              // 日志数据
  "global_monitor_result": {}  // 全局监控结果
}
```

## 📊 详细字段说明

### 1. report_info - 报告基本信息

```json
{
  "generated_at": "2024-12-01T12:00:00",  // 报告生成时间 (ISO格式)
  "timestamp": "20241201_120000",         // 时间戳标识
  "format": "json",                       // 报告格式
  "version": "2.0"                        // 报告版本号
}
```

**字段说明:**
- `generated_at`: 报告生成的具体时间，ISO 8601格式
- `timestamp`: 用于文件命名的时间戳
- `format`: 固定为"json"
- `version`: 报告格式版本，当前为2.0

### 2. summary - 测试汇总统计

```json
{
  "total_tests": 5,      // 总测试数
  "passed": 3,           // 通过数
  "failed": 1,          // 失败数
  "error": 1,           // 错误数
  "skipped": 0          // 跳过数
}
```

**字段说明:**
- `total_tests`: 执行的测试用例总数
- `passed`: 状态为"passed"的测试数
- `failed`: 状态为"failed"的测试数
- `error`: 状态为"error"的测试数
- `skipped`: 状态为"skipped"的测试数

### 3. device_info - 设备信息

```json
{
  "model": "MEIZU 18",           // 设备型号
  "version": "Android 13",       // 操作系统版本
  "serial": "test_serial_123",   // 设备序列号
  "brand": "MEIZU",              // 设备品牌
  "resolution": "1080x2400",     // 屏幕分辨率
  "dpi": 420                     // 屏幕密度
}
```

**字段说明:**
- `model`: 设备型号名称
- `version`: 操作系统版本信息
- `serial`: 设备唯一标识符
- `brand`: 设备品牌（可选）
- `resolution`: 屏幕分辨率（可选）
- `dpi`: 屏幕像素密度（可选）

### 4. test_results - 测试结果详情

测试结果数组，每个元素包含单个测试用例的详细信息：

```json
[
  {
    "test_name": "test_ubox_performance",           // 测试名称
    "status": "passed",                             // 测试状态
    "start_time": "2024-12-01T12:00:00",           // 开始时间
    "end_time": "2024-12-01T12:00:10",             // 结束时间
    "duration": 10.5,                               // 执行时长(秒)
    "error_message": null,                          // 错误信息
    "error_traceback": null,                        // 错误堆栈
    "screenshots": ["screenshot1.png"],              // 截图文件列表
    "logs": ["log1.txt"],                           // 日志文件列表
    "performance_summary": {},                       // 性能数据汇总
    "logcat_data": {},                              // Logcat数据
    "recording_data": {},                           // 录制数据
    "steps": []                                     // 测试步骤详情
  }
]
```

#### 4.1 performance_summary - 性能数据汇总

```json
{
  "data_source": "ubox_overview",    // 数据来源标识
  "metrics_count": 20,               // 指标数量
  "file_info": {                     // 性能文件信息
    "file_path": "/path/to/perf_data.json", // 性能数据文件路径
    "file_size": 1024000,            // 文件大小(字节)
    "file_exists": true               // 文件是否存在
  },
  "core_metrics": {                  // 核心性能指标
    "cpu_usage_avg": 16.3,           // 应用CPU使用率平均值(%)
    "memory_peak_mb": 1050.0,        // 内存峰值(MB)
    "fps_avg": 57.63,                // 平均FPS
    "stutter_rate_percent": 0.0,      // 卡顿率(%)
    "network_upload_total_kb": 1968.0, // 上传流量总计(KB)
    "network_download_total_kb": 1668.0, // 下载流量总计(KB)
    
    // ubox数据额外指标
    "cpu_total_avg": 38.6,           // 总CPU使用率平均值(%)
    "fps_max": 60.0,                 // 最高FPS
    "fps_min": 55.0,                 // 最低FPS
    "gpu_avg": 14.77,                // GPU使用率平均值(%)
    "big_jank_count": 0,             // 大卡顿次数
    "small_jank_count": 0            // 小卡顿次数
  }
}
```

**数据来源说明:**
- `ubox_overview`: ubox提供的丰富统计指标
- `legacy`: 旧格式性能数据
- `no_data`: 无性能数据

**文件信息说明:**
- `file_path`: 性能数据文件的完整路径
- `file_size`: 文件大小（字节）
- `file_exists`: 文件是否存在（生成报告时检查）

#### 4.2 steps - 测试步骤详情

```json
[
  {
    "step_name": "启动应用",                    // 步骤名称
    "status": "passed",                       // 步骤状态
    "start_time": "2024-12-01T12:00:00",      // 开始时间
    "end_time": "2024-12-01T12:00:05",       // 结束时间
    "duration": 5.0,                          // 执行时长(秒)
    "error_message": null,                     // 错误信息
    "error_traceback": null,                  // 错误堆栈
    "screenshots": ["step1_screenshot.png"],   // 步骤截图
    "logs": ["step1_log.txt"],                // 步骤日志
    "description": "启动目标应用并等待加载完成"  // 步骤描述
  }
]
```

### 5. log_data - 日志数据

```json
{
  "logcat_files": ["logcat1.txt", "logcat2.txt"],  // Logcat文件列表
  "system_logs": ["system1.log"],                  // 系统日志文件
  "app_logs": ["app1.log"],                        // 应用日志文件
  "total_log_size": 1024000                        // 总日志大小(字节)
}
```

### 6. global_monitor_result - 全局监控结果

```json
{
  "monitor_status": "completed",     // 监控状态
  "monitor_duration": 300,           // 监控时长(秒)
  "data_points": 1500,               // 数据点数量
  "monitor_files": [                 // 监控文件列表
    "perf_data.json",
    "system_monitor.log"
  ],
  "errors": []                       // 监控错误列表
}
```

## 🔧 数据来源说明

### ubox数据 (data_source: "ubox_overview")

ubox提供的丰富性能统计指标，包含以下详细信息：

**CPU指标:**
- `cpu_usage_avg`: 应用CPU使用率平均值
- `cpu_total_avg`: 总CPU使用率平均值
- `cpu_usage_max`: 应用CPU使用率峰值
- `cpu_total_max`: 总CPU使用率峰值

**内存指标:**
- `memory_peak_mb`: 内存峰值(MB)
- `memory_avg_mb`: 内存平均值(MB)
- `swap_memory_avg`: 交换内存平均值(MB)
- `virtual_memory_avg`: 虚拟内存平均值(MB)

**FPS指标:**
- `fps_avg`: 平均FPS
- `fps_max`: 最高FPS
- `fps_min`: 最低FPS
- `fps_p50`: FPS-P50值

**卡顿指标:**
- `stutter_rate_percent`: 卡顿率(%)
- `big_jank_count`: 大卡顿次数
- `small_jank_count`: 小卡顿次数
- `jank_total`: 总卡顿次数

**GPU指标:**
- `gpu_avg`: GPU使用率平均值(%)

**网络指标:**
- `network_upload_total_kb`: 上传流量总计(KB)
- `network_download_total_kb`: 下载流量总计(KB)
- `net_up_avg`: 平均上传速度(KB/s)
- `net_down_avg`: 平均下载速度(KB/s)

**温度指标:**
- `cpu_temp_avg`: CPU温度平均值(°C)
- `cpu_temp_max`: CPU温度峰值(°C)
- `battery_temp_avg`: 电池温度平均值(°C)
- `battery_temp_max`: 电池温度峰值(°C)

**功耗指标:**
- `power_avg`: 平均功耗(mW)
- `voltage_avg`: 平均电压(mV)
- `current_avg`: 平均电流(mA)

**帧时间指标:**
- `frame_time_avg`: 平均帧时间(ms)
- `frame_time_peak`: 峰值帧时间(ms)

### 旧格式数据 (data_source: "legacy")

兼容旧版本性能数据格式，包含基本指标：
- `cpu_usage_avg`: CPU使用率平均值
- `memory_peak_mb`: 内存峰值
- `fps_avg`: 平均FPS
- `stutter_rate_percent`: 卡顿率
- `network_upload_total_kb`: 上传流量
- `network_download_total_kb`: 下载流量

## 📈 优化特性

### 1. 数据去重
- 消除了性能数据在多个地方的重复存储
- 精简了数据结构，减少文件大小约60-70%

### 2. 数据准确性
- 统一了数据计算逻辑
- 确保数值计算的正确性
- 支持多种数据来源的统一处理

### 3. 结构清晰
- 分层显示核心指标和扩展指标
- 清楚标识数据来源
- 便于理解和解析

### 4. 扩展性
- 支持ubox的丰富指标
- 保持对旧格式数据的兼容性
- 易于添加新的性能指标

## 🚀 使用示例

### Python解析示例

```python
import json

# 读取JSON报告
with open('test_report_20241201_120000.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

# 获取基本信息
print(f"报告版本: {report['report_info']['version']}")
print(f"总测试数: {report['summary']['total_tests']}")
print(f"通过数: {report['summary']['passed']}")

# 遍历测试结果
for test_result in report['test_results']:
    test_name = test_result['test_name']
    status = test_result['status']
    perf_data = test_result['performance_summary']
    
    print(f"测试: {test_name}, 状态: {status}")
    print(f"数据来源: {perf_data['data_source']}")
    
    # 显示文件信息
    file_info = perf_data['file_info']
    if file_info['file_path']:
        print(f"性能文件: {file_info['file_path']}")
        print(f"文件大小: {file_info['file_size']} 字节")
        print(f"文件存在: {file_info['file_exists']}")
    
    core_metrics = perf_data['core_metrics']
    print(f"CPU: {core_metrics['cpu_usage_avg']:.2f}%")
    print(f"FPS: {core_metrics['fps_avg']:.2f}")
    
    # 如果是ubox数据，显示额外指标
    if perf_data['data_source'] == 'ubox_overview':
        print(f"GPU: {core_metrics['gpu_avg']:.2f}%")
        print(f"大卡顿: {core_metrics['big_jank_count']}次")
```

### JavaScript解析示例

```javascript
// 读取JSON报告
const fs = require('fs');
const report = JSON.parse(fs.readFileSync('test_report_20241201_120000.json', 'utf8'));

// 获取基本信息
console.log(`报告版本: ${report.report_info.version}`);
console.log(`总测试数: ${report.summary.total_tests}`);
console.log(`通过数: ${report.summary.passed}`);

// 遍历测试结果
report.test_results.forEach(testResult => {
    const testName = testResult.test_name;
    const status = testResult.status;
    const perfData = testResult.performance_summary;
    
    console.log(`测试: ${testName}, 状态: ${status}`);
    console.log(`数据来源: ${perfData.data_source}`);
    
    // 显示文件信息
    const fileInfo = perfData.file_info;
    if (fileInfo.file_path) {
        console.log(`性能文件: ${fileInfo.file_path}`);
        console.log(`文件大小: ${fileInfo.file_size} 字节`);
        console.log(`文件存在: ${fileInfo.file_exists}`);
    }
    
    const coreMetrics = perfData.core_metrics;
    console.log(`CPU: ${coreMetrics.cpu_usage_avg.toFixed(2)}%`);
    console.log(`FPS: ${coreMetrics.fps_avg.toFixed(2)}`);
    
    // 如果是ubox数据，显示额外指标
    if (perfData.data_source === 'ubox_overview') {
        console.log(`GPU: ${coreMetrics.gpu_avg.toFixed(2)}%`);
        console.log(`大卡顿: ${coreMetrics.big_jank_count}次`);
    }
});
```

### 性能数据统计示例

```python
import json

def analyze_performance_data(report_file):
    """分析性能数据统计"""
    with open(report_file, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    # 收集所有性能数据
    all_cpu = []
    all_fps = []
    all_memory = []
    ubox_tests = 0
    legacy_tests = 0
    
    for test_result in report['test_results']:
        perf_data = test_result['performance_summary']
        if perf_data['data_source'] != 'no_data':
            core_metrics = perf_data['core_metrics']
            
            all_cpu.append(core_metrics['cpu_usage_avg'])
            all_fps.append(core_metrics['fps_avg'])
            all_memory.append(core_metrics['memory_peak_mb'])
            
            if perf_data['data_source'] == 'ubox_overview':
                ubox_tests += 1
            else:
                legacy_tests += 1
    
    # 计算统计值
    if all_cpu:
        print(f"性能数据统计:")
        print(f"  总测试数: {len(all_cpu)}")
        print(f"  ubox测试: {ubox_tests}")
        print(f"  旧格式测试: {legacy_tests}")
        print(f"  CPU使用率: 平均{sum(all_cpu)/len(all_cpu):.2f}%, 最高{max(all_cpu):.2f}%")
        print(f"  FPS: 平均{sum(all_fps)/len(all_fps):.2f}, 最高{max(all_fps):.2f}")
        print(f"  内存峰值: 平均{sum(all_memory)/len(all_memory):.2f}MB, 最高{max(all_memory):.2f}MB")

# 使用示例
analyze_performance_data('test_report_20241201_120000.json')
```

## 📝 注意事项

1. **文件编码**: JSON文件使用UTF-8编码
2. **时间格式**: 所有时间字段使用ISO 8601格式
3. **数值精度**: 浮点数保留2位小数
4. **空值处理**: 使用`null`表示空值，不使用空字符串
5. **数组索引**: 数组索引从0开始
6. **文件路径**: 相对路径相对于报告文件所在目录
7. **性能数据**: 所有性能数据都在 `test_results` 中，无需额外的全局汇总

## 🔄 版本历史

- **v2.0**: 精简数据结构，消除重复，支持ubox数据，移除全局性能汇总
- **v1.0**: 初始版本，基础JSON报告格式

---

*最后更新: 2024-12-01*
