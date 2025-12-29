# BrainSync SDK Python Package

Python bindings for BrainSync SDK - EEG data acquisition and device control.

## 📦 安装

```bash
# 从源码构建
cd sdk
maturin develop --features python

# 或使用 pip 安装（如果已发布）
pip install brainsync-sdk
```

## 🚀 快速开始

### Serial 连接

```python
import asyncio
from brainsync_sdk import (
    open_brainsync_serial,
    get_firmware_version,
    set_eeg_transfer,
)

async def main():
    # 打开设备（自动发现串口）
    device = await open_brainsync_serial()
    
    # 获取固件版本
    version = await get_firmware_version(device)
    print(f"固件版本: {version}")
    
    # 开始 EEG 数据流
    await set_eeg_transfer(device, True)

asyncio.run(main())
```

### BLE 连接

```python
import asyncio
from brainsync_sdk import (
    open_brainsync_ble,
    get_firmware_version,
    set_eeg_transfer,
)

async def main():
    # 通过设备名称连接
    device = await open_brainsync_ble("BRSC1")
    
    # 使用相同的 API
    version = await get_firmware_version(device)
    print(f"固件版本: {version}")
    
    # 开始 EEG 数据流
    await set_eeg_transfer(device, True)

asyncio.run(main())
```

## 📁 文件说明

```
brainsync_sdk/
├── __init__.py          # Python 包入口（导出所有 API）
├── __init__.pyi         # 类型提示（主模块）
├── _native.abi3.so      # Rust 扩展模块（编译后生成）
└── _native.pyi          # 类型提示（扩展模块）
```

## 🔧 主要功能

### DeviceApi - 统一设备接口

**连接函数：**
- `open_brainsync_serial()` - Serial 连接（自动发现）
- `open_brainsync_ble(device_name)` - BLE 按名称连接
- `open_brainsync_ble_by_id(device_id)` - BLE 按 ID 连接

**设备控制：**
- `get_firmware_version(handle)` - 获取固件版本
- `get_arm_status(handle)` - 获取电刺激状态
- `get_eeg_params(handle)` - 获取 EEG 参数
- `set_eeg_sample_rate(handle, rate)` - 设置采样率
- `set_eeg_gain(handle, gain)` - 设置增益
- `set_eeg_signal_type(handle, signal_type)` - 设置信号类型
- `set_eeg_transfer(handle, enable)` - 开始/停止 EEG 数据流
- `get_eeg_loss_stats(handle)` - 获取丢包统计
- `reset_eeg_loss_stats(handle)` - 重置丢包统计
- `get_imu_params(handle)` - 获取 IMU 参数
- `set_imu_transfer(handle, enable)` - 开始/停止 IMU 数据流
- `set_adc_transfer(handle, enable)` - 开始/停止 ADC 数据流

### 数据类型

**枚举：**
- `EegSampleRate` - EEG 采样率（125Hz, 250Hz, 500Hz, 1000Hz）
- `EegGain` - EEG 增益（1, 2, 4, 6, 8, 12, 24）
- `EegSignalType` - 信号类型（Normal, TestSignal, ShortCircuit）
- `ImuSampleRate`, `ImuFullscale` - IMU 参数
- `MagSampleRate`, `MagFullscale` - 磁力计参数

**数据包：**
- `EegDataPacket` - EEG 数据包
- `ImuDataPacket` - IMU 数据包
- `AdcDataPacket` - ADC 数据包
- `MagDataPacket` - 磁力计数据包

**DFU：**
- `PyDfuState` - DFU 状态枚举
- `PyDfuProgress` - DFU 进度信息

## 💡 类型提示

`.pyi` 文件为 IDE 提供完整的类型信息：

- ✅ **代码补全**：自动提示可用的函数和参数
- ✅ **类型检查**：mypy 或 Pylance 检查类型错误
- ✅ **文档提示**：悬停显示函数文档和参数说明
- ✅ **参数提示**：输入时显示参数类型和说明

## 🛠️ 开发说明

### 构建 Python 绑定

```bash
# 开发模式（Serial 支持）
cd sdk
maturin develop --features python

# 包含 BLE 支持
maturin develop --features "python ble"

# 生产构建
maturin build --release --features python
```

### 更新类型提示

类型提示文件直接在此目录中维护：

```bash
# 方式 1: 手动编辑（推荐）
vim __init__.py      # Python 包入口
vim __init__.pyi     # 主模块类型提示
vim _native.pyi      # Rust 扩展模块类型提示

# 方式 2: 使用 stub_gen 自动生成（可选）
cd sdk
cargo run --bin stub_gen --features "stub_gen python"

# 检查生成的文件
git diff

# 重新构建 Python 包
maturin develop --features python
```

**注意**：类型提示文件已被 Git 管理，直接编辑即可。构建系统不会覆盖这些文件。

### 运行示例

```bash
# Serial 示例
python examples/python/serial_example.py

# BLE DeviceApi 示例
python examples/python/ble_device_api_example.py

# DFU 示例
python examples/python/serial_dfu.py
python examples/python/ble_dfu.py
```

### 类型检查

```bash
# 使用 mypy 进行类型检查
pip install mypy
mypy examples/python/serial_example.py
```

## 📚 更多信息

- **示例代码**：[examples/python/](../../examples/python/)
- **示例文档**：[examples/python/README.md](../../examples/python/README.md)
- **API 文档**：查看 `.pyi` 文件中的类型定义和文档字符串
- **Rust 源码**：[src/python/](../../src/python/)

## 🔗 相关链接

- [BrainSync SDK 主文档](../../../README.md)
- [Rust 示例](../../examples/)
- [协议文档](../../../docs/)
