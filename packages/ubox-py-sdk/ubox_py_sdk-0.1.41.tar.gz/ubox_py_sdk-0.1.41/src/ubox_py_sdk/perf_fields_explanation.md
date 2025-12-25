# SaveDataWrapper 处理后的JSON数据结构说明

## 概述
`SaveDataWrapper.process_json_file()` 方法处理原始性能数据后，会生成一个结构化的JSON文件，包含原始数据、统计指标和分类指标。

## 性能指标概念说明

### FPS相关指标
- **Fps**: 1秒内游戏界面或应用界面真实平均刷新次数，俗称帧率/FPS
- **Jank**: 1秒内卡顿次数，表示在1秒钟内发生的卡顿事件的数量。卡顿通常是由于渲染、计算或其他性能问题导致的应用程序或游戏运行不流畅的现象
- **BigJank**: 大卡顿次数，表示在一定时间段内发生的严重卡顿事件的数量。大卡顿通常会导致用户明显感受到的性能下降
- **SmallJank**: 微小卡顿次数，表示在一定时间段内发生的微小卡顿事件的数量
- **Stutter**: 卡顿率，表示卡顿事件在总帧数中所占的百分比。较高的卡顿率意味着应用程序或游戏的性能较差
- **FrameTime**: FrameTime生成每一帧图形所需的时间，用于衡量渲染性能和游戏流畅度

### CPU相关指标
- **TotalUsage**: 总使用率，表示某个资源（如CPU、GPU或内存）的使用量占其总容量的百分比
- **AppUsage**: 应用使用率，表示应用程序占用某个资源（如CPU、GPU或内存）的使用量占其总容量的百分比

### 内存相关指标
- **Memory**: 指FootPrint，注：OOM与FootPrint有关，与系统、机型无关。只与RAM有关，如1G内存机器。FootPrint超过650MB，引发OOM
- **SwapMemory**: 一般压缩会占用CPU的资源，同时相应会导致FPS降低
- **VirtualMemory**: VSS Memory，虚拟耗用内存
- **XCodeMemory**: XCode Debug gauges统计方式即XCode Memory
- **RealMemory**: Xcode Instrument统计方式即Real Memory，实际占用物理内存
- **AvailableMemory**: 整机可用剩余内存

### 网络相关指标
- **UpSpeed**: 上行速度，表示应用程序或设备每秒发送数据的速度，单位为KB/s（千字节/秒）
- **DownSpeed**: 下行速度，表示应用程序或设备每秒接收数据的速度，单位为KB/s（千字节/秒）

### 温度相关指标
- **BatteryTemperature**: 整机电池温度
- **CpuTemperature**: 整机CPU温度

### 功耗相关指标
- **Current**: 整机实时电流
- **Voltage**: 整机实时电压
- **Power**: 整机实时耗能
- **BatLevel**: 整机电池电量百分比

### GPU相关指标
- **GpuUsage**: 整机GPU使用率

- **Device**: 整机GPU使用率
- **Render**: 渲染器利用率（像素着色处理阶段，若占比高，说明是PS阶段出现瓶颈，shader过于复杂或纹理大小、采样复杂等）
- **Tiler**: Tiler利用率（顶点着色处理阶段，若占比高，说明是VS阶段出现瓶颈，顶点数太多等原因）

## 数据结构

### 1. 基础信息字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `AbsDataStartTime` | number | 数据采集开始时间戳（毫秒） |
| `AppDisplayName` | string | 应用显示名称 |
| `AppVersion` | string | 应用版本号 |
| `AppPackageName` | string | 应用包名 |
| `DeviceModel` | string | 设备型号 |
| `OSType` | string | 操作系统类型（ANDROID/IOS） |
| `OSVersion` | string | 操作系统版本 |

### 2. DataList - 原始数据列表

包含每个时间点的详细性能数据，每个数据项包含：

#### CommonFPS - 通用FPS数据

| 字段名 | 类型 | 说明 | 单位 |
|--------|------|------|------|
| `Fps` | number | 当前帧率 | 帧/秒 |
| `Jank` | number | 卡顿次数 | 次 |
| `BigJank` | number | 大卡顿次数 | 次 |
| `SmallJank` | number | 小卡顿次数 | 次 |
| `Stutter` | number | 卡顿率 | % |

#### CommonGPUUsage - GPU使用情况

**Android设备：**

| 字段名 | 类型 | 说明 | 单位 |
|--------|------|------|------|
| `GpuUsage` | number | GPU使用率 | % |

**iOS设备：**

| 字段名 | 类型 | 说明 | 单位 |
|--------|------|------|------|
| `Tiler` | number | Tiler GPU使用率 | % |
| `Render` | number | 渲染GPU使用率 | % |
| `Device` | number | 设备GPU使用率 | % |

#### CpuUsage - CPU使用情况

| 字段名 | 类型 | 说明 | 单位 |
|--------|------|------|------|
| `AppUsage` | number | 应用CPU使用率 | % |
| `TotalUsage` | number | 总CPU使用率 | % |

#### MemoryUsage - 内存使用情况
| 字段名 | 类型 | 说明 | 单位 |
|--------|------|------|------|
| `Memory` | number | 内存使用量 | MB |
| `SwapMemory` | number | 交换内存使用量（Android） | MB |
| `VirtualMemory` | number | 虚拟内存使用量 | MB |

#### NetworkUsage - 网络使用情况
| 字段名 | 类型 | 说明 | 单位 |
|--------|------|------|------|
| `UpSpeed` | number | 上传速度 | KB/s |
| `DownSpeed` | number | 下载速度 | KB/s |

#### Temperature - 温度情况
| 字段名 | 类型 | 说明 | 单位 |
|--------|------|------|------|
| `BatteryTemperature` | number | 电池温度 | ℃ |
| `CpuTemperature` | number | CPU温度（仅Android） | ℃ |

#### Power - 功耗情况
| 字段名 | 类型 | 说明 | 单位 |
|--------|------|------|------|
| `Power` | number | 功耗 | mW |
| `Voltage` | number | 电压 | mV |
| `Current` | number | 电流 | mA |

#### FrameTime - 帧时间数据
| 字段名 | 类型 | 说明 | 单位 |
|--------|------|------|------|
| `FrameTimeData` | array | 帧时间数据列表 | - |
| `FrameTimeData[].Time` | number | 帧的时间戳 | 毫秒 |
| `FrameTimeData[].FrameTime` | number | 单帧渲染时间 | 毫秒 |

### 3. Overview - 性能指标概览

`Overview.ALL` 包含所有性能指标的汇总，每个指标包含：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `Name` | string | 指标名称 |
| `Value` | number | 指标值 |
| `Unit` | string | 单位 |
| `Key` | string | 指标分类键 |

### 4. 分类指标

#### Fps - FPS相关指标（16个）
| 指标名称 | 说明 | 单位 |
|----------|------|------|
| Avg(FPS) | 平均帧率 | 帧/s |
| FPS>=18 | FPS大于等于18帧的百分比 | % |
| FPS>=25 | FPS大于等于25帧的百分比 | % |
| Max(FPS) | 最大FPS | 帧/s |
| Min(FPS) | 最小FPS | 帧/s |
| Jank | 总卡顿次数 | 次 |
| Big Jank | 大卡顿次数 | 次 |
| Small Jank | 小卡顿次数 | 次 |
| Jank[/10min] | 每10分钟的卡顿次数 | 次 |
| Big Jank[/10min] | 每10分钟的大卡顿次数 | 次 |
| Small Jank[/10min] | 每10分钟的小卡顿次数 | 次 |
| Stutter | 卡顿率 | % |
| Avg(FTime)[ms] | 平均帧时间 | 毫秒 |
| Peak(FTime) | 峰值帧时间 | 毫秒 |
| FTime>=100ms[%] | 帧时间大于等于100ms的百分比 | % |
| P50(FPS) | FPS的50分位数 | 帧/s |

#### CpuUsage - CPU使用率相关指标（10个）
| 指标名称 | 说明 | 单位 |
|----------|------|------|
| Avg(AppCPU) | 平均应用CPU使用率 | % |
| AppCPU<=60% | 应用CPU使用率小于等于60%的百分比 | % |
| AppCPU<=80% | 应用CPU使用率小于等于80%的百分比 | % |
| Peak(AppCPU) | 峰值应用CPU使用率 | % |
| P50(AppCPU) | 应用CPU使用率的50分位数 | % |
| Avg(TotalCPU) | 平均总CPU使用率 | % |
| TotalCPU<=60% | 总CPU使用率小于等于60%的百分比 | % |
| TotalCPU<=80% | 总CPU使用率小于等于80%的百分比 | % |
| Peak(TotalCPU) | 峰值总CPU使用率 | % |
| P50(TotalCPU) | 总CPU使用率的50分位数 | % |

#### MemoryUsage - 内存使用相关指标（7个）
| 指标名称 | 说明 | 单位 |
|----------|------|------|
| Avg(Memory) | 平均内存使用量 | MB |
| Avg(SwapMemory) | 平均交换内存使用量 | MB |
| Avg(VirtualMemory) | 平均虚拟内存使用量 | MB |
| Peak(Memory) | 峰值内存使用量 | MB |
| Peak(SwapMemory) | 峰值交换内存使用量 | MB |
| Peak(VirtualMemory) | 峰值虚拟内存使用量 | MB |
| P50(Memory) | 内存使用量的50分位数 | MB |

#### NetworkUsage - 网络使用相关指标（6个）
| 指标名称 | 说明 | 单位 |
|----------|------|------|
| Avg(Send)[KB/s] | 平均上传速度 | KB/s |
| Avg(Recv)[KB/s] | 平均下载速度 | KB/s |
| Sum(Send)[KB] | 总上传数据量 | KB |
| Sum(Recv)[KB] | 总下载数据量 | KB |
| Send[KB/10min] | 每10分钟上传数据量 | KB |
| Recv[KB/10min] | 每10分钟下载数据量 | KB |

#### Temperature - 温度相关指标
**Android设备（6个）：**

| 指标名称 | 说明 | 单位 |
|----------|------|------|
| Avg(BatteryTemp) | 平均电池温度 | ℃ |
| Max(BatteryTemp) | 最大电池温度 | ℃ |
| P50(BatteryTemp) | 电池温度的50分位数 | ℃ |
| Avg(CPUTemp) | 平均CPU温度 | ℃ |
| Max(CPUTemp) | 最大CPU温度 | ℃ |
| P50(CPUTemp) | CPU温度的50分位数 | ℃ |

**iOS设备（3个）：**

| 指标名称 | 说明 | 单位 |
|----------|------|------|
| Avg(BatteryTemp) | 平均电池温度 | ℃ |
| Max(BatteryTemp) | 最大电池温度 | ℃ |
| P50(BatteryTemp) | 电池温度的50分位数 | ℃ |

#### GpuUsage - GPU使用相关指标
**Android设备（1个）：**

| 指标名称 | 说明 | 单位 |
|----------|------|------|
| Avg(GPUUsage) | 平均GPU使用率 | % |

**iOS设备（3个）：**

| 指标名称 | 说明 | 单位 |
|----------|------|------|
| Avg(Render) | 平均渲染GPU使用率 | % |
| Avg(Device) | 平均设备GPU使用率 | % |
| Avg(Tiler) | 平均Tiler GPU使用率 | % |

#### Power - 功耗相关指标（5个）

| 指标名称 | 说明 | 单位 |
|----------|------|------|
| Avg(Power) | 平均功耗 | mW |
| P50(Power) | 功耗的50分位数 | mW |
| Sum(Battery) | 总电量消耗 | mWh |
| Avg(Voltage) | 平均电压 | mV |
| Avg(Current) | 平均电流 | mA |

## 注意事项

1. **设备差异**：Android和iOS设备的数据结构和指标略有不同
2. **分位数计算**：P50表示50分位数（中位数）
3. **时间单位**：时间相关数据统一使用毫秒
4. **百分比计算**：范围统计（如FPS>=18）表示满足条件的样本占总样本的百分比
5. **数据完整性**：某些指标可能为0或空值，表示该设备不支持该指标
6. **电量计算**：Sum(Battery) = 平均电流 × 平均电压 × 时间 / 1000 / 1000 / 3600（转换为mWh）
