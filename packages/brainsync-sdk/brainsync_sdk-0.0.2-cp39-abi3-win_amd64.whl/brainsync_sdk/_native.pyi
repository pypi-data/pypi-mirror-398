"""
Type stubs for brainsync_sdk._native

This file provides type hints for the Rust extension module.
Auto-generated from Rust code.
"""

from typing import Any, Callable, Optional
from enum import IntEnum

# ========== Enums ==========

# ========== Classes ==========

class AdcDataPacket:
    """
    ADC 数据包

    包含 5 个通道的 16 位 ADC 值（小端序）：
    - voltage_reference: 参考电压
    - ces_channel_1: CES 通道 1
    - ces_channel_2: CES 通道 2
    - battery_voltage: 电池电压检测
    - battery_temperature: 电池温度
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        ...
    
    def __new__(self, *args, **kwargs) -> Any:
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        ...
    
    def battery_temperature_volts(self, *args, **kwargs) -> Any:
        """
        获取电池温度电压（V）
        """
        ...
    
    def battery_voltage_volts(self, *args, **kwargs) -> Any:
        """
        获取电池电压（V）

        # Python 示例
        """
        ...
    
    def ces_channel_1_volts(self, *args, **kwargs) -> Any:
        """
        获取 CES 通道 1 电压（V）
        """
        ...
    
    def ces_channel_2_volts(self, *args, **kwargs) -> Any:
        """
        获取 CES 通道 2 电压（V）
        """
        ...
    
    def voltage_reference_volts(self, *args, **kwargs) -> Any:
        """
        获取参考电压（V）

        # Python 示例
        """
        ...
    

class DeviceInfo:
    """
    设备信息

    包含设备的基本标识信息和固件版本信息。
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        ...
    
    def __new__(self, *args, **kwargs) -> Any:
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        ...
    

class EegDataPacket:
    """
    EEG 数据包
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        ...
    
    def __new__(self, *args, **kwargs) -> Any:
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        ...
    
    def delta_time_ms(self, *args, **kwargs) -> Any:
        """
        获取采样时间差（毫秒）
        """
        ...
    
    def delta_time_us(self, *args, **kwargs) -> Any:
        """
        获取采样时间差（微秒）
        """
        ...
    
    def is_impedance_mode(self, *args, **kwargs) -> Any:
        """
        检查数据包是否来自阻抗检测模式

        通过检查 Lead-off 状态判断当前是否在进行阻抗检测
        """
        ...
    
    def to_microvolts(self, *args, **kwargs) -> Any:
        """
        将 ADC 值转换为物理量（µV）

        # 参数
        """
        ...
    
    def to_volts(self, *args, **kwargs) -> Any:
        """
        将 ADC 值转换为电压（V）

        # 参数
        """
        ...
    

class EegGain:
    """
    EEG 增益
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        ...
    
    def __new__(self, *args, **kwargs) -> Any:
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        ...
    

class EegSampleRate:
    """
    EEG 采样率
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        ...
    
    def __new__(self, *args, **kwargs) -> Any:
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        ...
    

class EegSignalType:
    """
    EEG 信号类型
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        ...
    
    def __new__(self, *args, **kwargs) -> Any:
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        ...
    

class EegStatus:
    """
    EEG 状态
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        ...
    
    def __new__(self, *args, **kwargs) -> Any:
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        ...
    

class ImpedanceData:
    """
    阻抗数据包

    包含 8 个通道的阻抗值
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        ...
    
    def __new__(self, *args, **kwargs) -> Any:
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        ...
    

class ImuDataPacket:
    """
    IMU 数据包

    包含 6 个通道的 16 位 ADC 原始值（小端序）：
    - 加速度计 X, Y, Z
    - 陀螺仪 X, Y, Z
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        ...
    
    def __new__(self, *args, **kwargs) -> Any:
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        ...
    
    def to_accel_g(self, *args, **kwargs) -> Any:
        """
        将加速度计 ADC 值转换为物理量（单位：G）

        # 参数
        """
        ...
    
    def to_gyro_dps(self, *args, **kwargs) -> Any:
        """
        将陀螺仪 ADC 值转换为物理量（单位：dps，度/秒）

        # 参数
        """
        ...
    

class ImuFullscale:
    """
    IMU 量程（加速度计）
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        ...
    
    def __new__(self, *args, **kwargs) -> Any:
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        ...
    

class ImuSampleRate:
    """
    IMU 采样率
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        ...
    
    def __new__(self, *args, **kwargs) -> Any:
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        ...
    

class LeadoffCurrent:
    """
    Lead-off 检测电流
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        ...
    
    def __new__(self, *args, **kwargs) -> Any:
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        ...
    

class LeadoffStatus:
    """
    Lead-off 状态
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        ...
    
    def __new__(self, *args, **kwargs) -> Any:
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        ...
    

class LeadoffType:
    """
    Lead-off 检测类型
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        ...
    
    def __new__(self, *args, **kwargs) -> Any:
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        ...
    

class LogLevel:
    
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        ...
    
    def __new__(self, *args, **kwargs) -> Any:
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        ...
    

class MagDataPacket:
    """
    磁力计数据包

    包含 3 个通道的 16 位 ADC 原始值（小端序）：
    - 磁场 X, Y, Z
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        ...
    
    def __new__(self, *args, **kwargs) -> Any:
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        ...
    
    def to_gauss(self, *args, **kwargs) -> Any:
        """
        将磁力计 ADC 值转换为物理量（单位：Gauss）

        # 参数
        """
        ...
    

class MagFullscale:
    """
    磁力计量程
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        ...
    
    def __new__(self, *args, **kwargs) -> Any:
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        ...
    

class MagSampleRate:
    """
    磁力计采样率
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        ...
    
    def __new__(self, *args, **kwargs) -> Any:
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        ...
    

class NoiseType:
    """
    环境噪声类型
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        ...
    
    def __new__(self, *args, **kwargs) -> Any:
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        ...
    

class OtaStatus:
    """
    OTA 状态
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        ...
    
    def __new__(self, *args, **kwargs) -> Any:
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        ...
    

class PyDfuProgress:
    """
    Python-facing DFU progress information (simplified from DfuProgress)
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        ...
    
    def __new__(self, *args, **kwargs) -> Any:
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        ...
    

class PyDfuState:
    """
    Python-facing DFU state enum
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        ...
    
    def __new__(self, *args, **kwargs) -> Any:
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        ...
    

class ResponseResult:
    """
    命令响应结果
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        ...
    
    def __new__(self, *args, **kwargs) -> Any:
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        ...
    

class StimMode:
    """
    电刺激模式

    # 模式说明

    - **TDCS**: 直流电刺激 (Transcranial Direct Current Stimulation)
      - 恒定直流电刺激
      - 分为正向 (DC_POS) 和反向 (DC_NEG)

    - **TACS**: 交流电刺激 (Transcranial Alternating Current Stimulation)
      - 正弦波交流电刺激
      - 频率范围: 0.1-100Hz
      - 波形: s = I * sin(2*pi*f*t)

    - **TIS**: 时域干涉刺激 (Temporal Interference Stimulation)
      - 使用 2 个高频 tACS 产生干涉包络
      - 示例: CH1=1000Hz, CH2=1010Hz → 干涉包络=10Hz
      - 频率设定范围: 1000Hz-1100Hz (100Hz 范围的包络)

    - **Blank**: 不刺激
      - ramp_up_ms = 0, hold_ms = 0, ramp_down_ms = 0
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        ...
    
    def __new__(self, *args, **kwargs) -> Any:
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        ...
    

class StimPolarity:
    """
    电刺激极性

    用于标识电极的极性配置

    # 说明

    - **Anode (阳极/正极)**: 电流流出的电极
    - **Cathode (阴极/负极)**: 电流流入的电极

    # 硬件配置

    设备支持 2 个刺激通道，每个通道需要配置一对电极（阳极和阴极）：
    - Channel 0: 电极 0 (阳极) ←→ 电极 1 (阴极)
    - Channel 1: 电极 2 (阳极) ←→ 电极 3 (阴极)

    # 示例

    ```ignore
    // Channel 0 配置
    let electrode_config = vec![
        ("CP4", 0, 0, StimPolarity::Anode),    // CP4 作为阳极
        ("CP2", 1, 0, StimPolarity::Cathode),  // CP2 作为阴极
    ];
    ```
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        ...
    
    def __new__(self, *args, **kwargs) -> Any:
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        ...
    

class StimStatus:
    """
    电刺激状态
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        ...
    
    def __new__(self, *args, **kwargs) -> Any:
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        ...
    

class StimulationParams:
    """
    电刺激参数（小端序，19 bytes）

    协议: [chan (1), mode (1), freq_hz_10x (2), current_ua (2), ramp_up_ms (4), hold_ms (4), ramp_down_ms (4), label_id (1)]

    # 参数说明

    - **chan**: 通道号 (0-based)，支持双通道独立控制
    - **mode**: 刺激模式
      - 0x00 = OFF (关闭)
      - 0x01 = SINE (正弦波，用于 tACS/TIS)
      - 0x02 = SQUARE (方波，保留)
      - 0x03 = DC_POS (正向直流，用于 tDCS)
      - 0x04 = DC_NEG (反向直流，用于 tDCS)
      - 0xFF = QUERY (查询)
    - **freq_hz_10x**: 频率，单位 0.1Hz (100mHz)
      - 步长: 0.1Hz
      - 范围: 0.1Hz - 6553.5Hz
      - 示例: 1000 = 100Hz, 10000 = 1000Hz
      - tACS 常用: 0.1-100Hz
      - TIS 常用: 1000-1100Hz
    - **current_ua**: 电流强度，单位微安 (µA)
      - 步长: 1µA
      - 范围: 0 - 4000µA
      - 两通道独立调整
    - **ramp_up_ms**: Ramp Up 时长，单位毫秒 (ms)
      - 步长: 1ms
      - 两通道同步设置
      - Blank 模式: 设为 0
    - **hold_ms**: 持续输出时长，单位毫秒 (ms)
      - 步长: 1ms (通常以秒为单位设置)
      - 两通道同步设置
      - Sham 模式: 设为 0 (Ramp Up 后立即 Ramp Down)
      - Blank 模式: 设为 0
    - **ramp_down_ms**: Ramp Down 时长，单位毫秒 (ms)
      - 步长: 1ms
      - 两通道同步设置
      - Blank 模式: 设为 0
    - **label_id**: 标签 ID，用于在 EEG 数据中标记刺激事件

    # 典型配置示例

    ## tDCS (直流电刺激)
    ```ignore
    StimulationParams {
        chan: 0,
        mode: 0x03,           // DC_POS (正向)
        freq_hz_10x: 0,       // 直流无频率
        current_ua: 2000,     // 2000µA = 2mA
        ramp_up_ms: 30000,    // 30秒
        hold_ms: 1200000,     // 20分钟
        ramp_down_ms: 30000,  // 30秒
        label_id: 1,
    }
    ```

    ## tACS (交流电刺激)
    ```ignore
    StimulationParams {
        chan: 0,
        mode: 0x01,           // SINE
        freq_hz_10x: 100,     // 10Hz
        current_ua: 1500,     // 1500µA = 1.5mA
        ramp_up_ms: 10000,    // 10秒
        hold_ms: 600000,      // 10分钟
        ramp_down_ms: 10000,  // 10秒
        label_id: 2,
    }
    ```

    ## TIS (时域干涉刺激)
    ```ignore
    // 通道 1: 1000Hz
    StimulationParams {
        chan: 0,
        mode: 0x01,           // SINE
        freq_hz_10x: 10000,   // 1000Hz
        current_ua: 2000,     // 2000µA
        ramp_up_ms: 5000,     // 5秒
        hold_ms: 300000,      // 5分钟
        ramp_down_ms: 5000,   // 5秒
        label_id: 3,
    }
    // 通道 2: 1010Hz (产生 10Hz 包络)
    StimulationParams {
        chan: 1,
        mode: 0x01,           // SINE
        freq_hz_10x: 10100,   // 1010Hz
        current_ua: 2000,     // 2000µA
        ramp_up_ms: 5000,     // 5秒
        hold_ms: 300000,      // 5分钟
        ramp_down_ms: 5000,   // 5秒
        label_id: 3,
    }
    ```

    ## Sham (假刺激)
    ```ignore
    StimulationParams {
        chan: 0,
        mode: 0x01,           // SINE
        freq_hz_10x: 100,     // 10Hz
        current_ua: 1500,     // 1500µA
        ramp_up_ms: 10000,    // 10秒
        hold_ms: 0,           // 0 (立即 Ramp Down)
        ramp_down_ms: 10000,  // 10秒
        label_id: 4,
    }
    ```

    ## Blank (不刺激)
    ```ignore
    StimulationParams {
        chan: 0,
        mode: 0x00,           // OFF
        freq_hz_10x: 0,
        current_ua: 0,
        ramp_up_ms: 0,        // 0
        hold_ms: 0,           // 0
        ramp_down_ms: 0,      // 0
        label_id: 0,
    }
    ```
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        ...
    
    def __new__(self, *args, **kwargs) -> Any:
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        ...
    

# ========== Functions ==========

def abort_dfu(*args, **kwargs) -> Any:
    ...

def arm_stimulation(*args, **kwargs) -> Any:
    """
    Arm stimulation (enable high voltage circuit)

    Args:
      handle: DeviceApi handle from open_brainsync_serial
    """
    ...

def clear_impedance_callback(*args, **kwargs) -> Any:
    """
    Clear impedance detection callback and disable detector

    Args:
      handle: DeviceApi handle from open_brainsync_serial or open_brainsync_ble
    """
    ...

def connect_ble_device(*args, **kwargs) -> Any:
    """
    Connect to BLE device directly by device ID (without scanning)

    **Level: Recommended** - High-level API for connecting to a known BLE device.

    This function connects to a BLE device using its device ID and returns
    """
    ...

def disable_all_eeg_leadoff_channels(*args, **kwargs) -> Any:
    """
    Disable all EEG leadoff channels

    Args:
      handle: DeviceApi handle from open_brainsync_serial
    """
    ...

def disable_impedance_detection_mode(*args, **kwargs) -> Any:
    """
    Disable impedance detection mode and restore normal EEG configuration

    Args:
      handle: DeviceApi handle from open_brainsync_serial or open_brainsync_ble
    """
    ...

def disarm_stimulation(*args, **kwargs) -> Any:
    """
    Disarm stimulation (disable high voltage circuit)

    Args:
      handle: DeviceApi handle from open_brainsync_serial
    """
    ...

def enable_all_eeg_leadoff_channels(*args, **kwargs) -> Any:
    """
    Enable all EEG leadoff channels

    Args:
      handle: DeviceApi handle from open_brainsync_serial
    """
    ...

def enable_impedance_detection_mode(*args, **kwargs) -> Any:
    """
    Enable impedance detection mode (one-click configuration)

    This configures EEG parameters for impedance measurement:
    - Sample rate: 250Hz
    - Gain: 24x
    """
    ...

def find_brainsync_serial_port(*args, **kwargs) -> Any:
    """
    Find BrainSync device serial port

    **Level: Utility** - Auto-discover the first available BrainSync serial port.
    """
    ...

def get_ble_rx_char_uuid(*args, **kwargs) -> Any:
    """
    Get BrainSync RX characteristic UUID

    **Level: Utility** - Returns the BLE RX characteristic UUID for BrainSync devices.
    """
    ...

def get_ble_service_uuid(*args, **kwargs) -> Any:
    """
    Get BrainSync service UUID

    **Level: Utility** - Returns the BLE service UUID for BrainSync devices.
    """
    ...

def get_ble_tx_char_uuid(*args, **kwargs) -> Any:
    """
    Get BrainSync TX characteristic UUID

    **Level: Utility** - Returns the BLE TX characteristic UUID for BrainSync devices.
    """
    ...

def get_brainsync_usb_pid(*args, **kwargs) -> Any:
    """
    Get BrainSync USB PID

    **Level: Utility** - Returns the USB Product ID for BrainSync devices.
    """
    ...

def get_brainsync_usb_vid(*args, **kwargs) -> Any:
    """
    Get BrainSync USB VID

    **Level: Utility** - Returns the USB Vendor ID for BrainSync devices.
    """
    ...

def get_default_baudrate(*args, **kwargs) -> Any:
    """
    Get default baudrate

    **Level: Utility** - Returns the default serial baudrate for BrainSync devices.
    """
    ...

def get_eeg_loss_stats(*args, **kwargs) -> Any:
    """
    Get EEG loss statistics

    Args:
      handle: DeviceApi handle from open_brainsync_serial

    """
    ...

def get_eeg_params(*args, **kwargs) -> Any:
    """
    Get EEG parameters

    Args:
      handle: DeviceApi handle from open_brainsync_serial

    """
    ...

def get_eeg_sample_rate_value(*args, **kwargs) -> Any:
    """
    获取 EEG 采样率的实际数值（Hz）

    # 参数

    - `sample_rate`: EegSampleRate 枚举值
    """
    ...

def get_firmware_version(*args, **kwargs) -> Any:
    """
    Get firmware version

    Args:
      handle: DeviceApi handle from open_brainsync_serial or open_brainsync_ble

    """
    ...

def get_imu_params(*args, **kwargs) -> Any:
    """
    Get IMU parameters

    Args:
      handle: DeviceApi handle from open_brainsync_serial

    """
    ...

def get_mag_params(*args, **kwargs) -> Any:
    """
    Get magnetometer parameters

    Args:
      handle: DeviceApi handle from open_brainsync_serial

    """
    ...

def is_stimulation_armed(*args, **kwargs) -> Any:
    """
    Get stimulation arm status

    Args:
      handle: DeviceApi handle from open_brainsync_serial

    """
    ...

def list_serial_ports(*args, **kwargs) -> Any:
    """
    List available serial ports with VID/PID filter

    **Level: Utility** - List serial ports matching specific USB VID/PID.
    """
    ...

def open_brainsync_ble(*args, **kwargs) -> Any:
    """
    Open BrainSync device via BLE by name and return DeviceApi handle (async version)

    This function scans for and connects to an BrainSync device via BLE by device name,
    then returns a DeviceApi handle for device operations.

    """
    ...

def open_brainsync_ble_by_id(*args, **kwargs) -> Any:
    """
    Open BrainSync device via BLE by device ID and return DeviceApi handle (async version)

    This function directly connects to an BrainSync device via BLE using its device ID,
    then returns a DeviceApi handle for device operations.

    """
    ...

def open_brainsync_serial(*args, **kwargs) -> Any:
    """
    Open BrainSync device and return DeviceApi handle (async version)

    This function opens an BrainSync device and returns a DeviceApi handle that can be used
    for all device operations including configuration, data streaming, and OTA updates.

    """
    ...

def pause_stimulation(*args, **kwargs) -> Any:
    """
    Pause stimulation

    Args:
      handle: DeviceApi handle from open_brainsync_serial
    """
    ...

def py_ble_init_adapter(*args, **kwargs) -> Any:
    """
    Initialize BLE adapter

    **Level: Advanced** - For custom BLE workflows. Most users should use `scan_and_connect()` instead.
    """
    ...

def py_ble_write_value(*args, **kwargs) -> Any:
    """
    Write value to BLE device

    **Level: Advanced** - Low-level BLE write operation. Most users should use high-level device APIs.
    """
    ...

def py_clear_device_discovered_callback(*args, **kwargs) -> Any:
    """
    Clear device discovered callback

    **Level: Advanced** - Clear the device discovered callback.
    """
    ...

def py_clear_scan_result_callback(*args, **kwargs) -> Any:
    """
    Clear scan result callback

    **Level: Advanced** - Clear the scan result callback.
    """
    ...

def py_connect_ble(*args, **kwargs) -> Any:
    """
    Connect to BLE device

    **Level: Advanced** - For custom BLE workflows. Most users should use `connect_ble_device()` instead.
    """
    ...

def py_disconnect_ble(*args, **kwargs) -> Any:
    """
    Disconnect from BLE device

    **Level: Advanced** - For custom BLE workflows.
    """
    ...

def py_is_scanning(*args, **kwargs) -> Any:
    """
    Check if scanning

    **Level: Advanced** - Query BLE scanning state.
    """
    ...

def py_set_adapter_state_callback(*args, **kwargs) -> Any:
    """
    Set adapter state callback

    **Level: Advanced** - For monitoring BLE adapter state changes.
    """
    ...

def py_set_battery_level_callback(*args, **kwargs) -> Any:
    """
    Set battery level callback

    **Level: Advanced** - For monitoring device battery level.
    """
    ...

def py_set_connection_state_callback(*args, **kwargs) -> Any:
    """
    Set connection state callback

    **Level: Advanced** - For monitoring BLE connection state changes.
    """
    ...

def py_set_device_discovered_callback(*args, **kwargs) -> Any:
    """
    Set device discovered callback

    **Level: Advanced** - For custom BLE device discovery handling.
    """
    ...

def py_set_device_info_callback(*args, **kwargs) -> Any:
    """
    Set device info callback

    **Level: Advanced** - For receiving device information updates.
    """
    ...

def py_set_mtu(*args, **kwargs) -> Any:
    """
    Set MTU size

    **Level: Advanced** - Configure BLE MTU size for custom scenarios.
    """
    ...

def py_set_received_data_callback(*args, **kwargs) -> Any:
    """
    Set received data callback

    **Level: Advanced** - For custom BLE data reception handling.
    """
    ...

def py_set_scan_result_callback(*args, **kwargs) -> Any:
    """
    Set scan result callback

    **Level: Advanced** - For custom BLE scan result handling.
    """
    ...

def py_start_scan_with_uuids(*args, **kwargs) -> Any:
    """
    Start BLE scan with service UUIDs

    **Level: Advanced** - For custom BLE workflows. Most users should use `scan_and_connect()` instead.
    """
    ...

def py_stop_scan(*args, **kwargs) -> Any:
    """
    Stop BLE scan

    **Level: Advanced** - For custom BLE workflows.
    """
    ...

def reboot_device(*args, **kwargs) -> Any:
    """
    Reboot device

    Args:
      handle: DeviceApi handle from open_brainsync_serial
    """
    ...

def reset_eeg_loss_stats(*args, **kwargs) -> Any:
    """
    Reset EEG loss statistics

    Args:
      handle: DeviceApi handle from open_brainsync_serial
    """
    ...

def run_impedance_detection(*args, **kwargs) -> Any:
    """
    Run impedance detection for specified seconds (convenience helper)

    This is equivalent to:
    - set_eeg_transfer(True)
    - sleep(duration_secs)
    """
    ...

def scan_and_connect(*args, **kwargs) -> Any:
    """
    Scan and connect to BrainSync BLE device using unified API (async version)

    **Level: Recommended** - High-level API for scanning and connecting to BLE devices.

    This is the unified API that matches Rust's `scan_and_connect()`.
    """
    ...

def send_ota_segment(*args, **kwargs) -> Any:
    """
    Send OTA firmware segment

    Args:
      handle: DeviceApi handle from open_brainsync_serial
      offset: Data offset (u32)
    """
    ...

def set_adc_transfer(*args, **kwargs) -> Any:
    """
    Set ADC transfer (start/stop data streaming)

    Args:
      handle: DeviceApi handle from open_brainsync_serial
      enable: True to start streaming, False to stop
    """
    ...

def set_eeg_gain(*args, **kwargs) -> Any:
    """
    Set EEG gain

    Args:
      handle: DeviceApi handle from open_brainsync_serial
      gain: EegGain enum value
    """
    ...

def set_eeg_gains(*args, **kwargs) -> Any:
    """
    Set EEG gains for each channel

    Args:
      handle: DeviceApi handle from open_brainsync_serial
      gains: List of 8 EegGain enum values
    """
    ...

def set_eeg_leadoff_channel_mask(*args, **kwargs) -> Any:
    """
    Set EEG leadoff channel mask

    Args:
      handle: DeviceApi handle from open_brainsync_serial
      mask: 8-bit mask (bit 0 = channel 1, bit 7 = channel 8)
    """
    ...

def set_eeg_leadoff_channels(*args, **kwargs) -> Any:
    """
    Set EEG leadoff channels (using boolean array)

    Args:
      handle: DeviceApi handle from open_brainsync_serial
      channels: List of 8 booleans (channels[0] = channel 1, channels[7] = channel 8)
    """
    ...

def set_eeg_leadoff_current(*args, **kwargs) -> Any:
    """
    Set EEG leadoff current

    Args:
      handle: DeviceApi handle from open_brainsync_serial
      current: LeadoffCurrent enum value
    """
    ...

def set_eeg_leadoff_type(*args, **kwargs) -> Any:
    """
    Set EEG leadoff type

    Args:
      handle: DeviceApi handle from open_brainsync_serial
      leadoff_type: LeadoffType enum value
    """
    ...

def set_eeg_sample_rate(*args, **kwargs) -> Any:
    """
    Set EEG sample rate

    Args:
      handle: DeviceApi handle from open_brainsync_serial
      sample_rate: EegSampleRate enum value
    """
    ...

def set_eeg_signal_type(*args, **kwargs) -> Any:
    """
    Set EEG signal type

    Args:
      handle: DeviceApi handle from open_brainsync_serial
      signal_type: EegSignalType enum value
    """
    ...

def set_eeg_signal_types(*args, **kwargs) -> Any:
    """
    Set EEG signal types for each channel

    Args:
      handle: DeviceApi handle from open_brainsync_serial
      signal_types: List of 8 EegSignalType enum values
    """
    ...

def set_eeg_transfer(*args, **kwargs) -> Any:
    """
    Set EEG transfer (start/stop data streaming)

    Args:
      handle: DeviceApi handle from open_brainsync_serial
      enable: True to start streaming, False to stop
    """
    ...

def set_impedance_callback(*args, **kwargs) -> Any:
    """
    Set impedance detection callback

    Args:
      handle: DeviceApi handle from open_brainsync_serial or open_brainsync_ble
      callback: Python callable that accepts an ImpedanceData object
    """
    ...

def set_impedance_noise_type(*args, **kwargs) -> Any:
    """
    Set impedance detection noise type (50Hz/60Hz/Both)

    Args:
      handle: DeviceApi handle from open_brainsync_serial or open_brainsync_ble
      noise_type: NoiseType enum value
    """
    ...

def set_imu_fullscale(*args, **kwargs) -> Any:
    """
    Set IMU fullscale

    Args:
      handle: DeviceApi handle from open_brainsync_serial
      fullscale: ImuFullscale enum value
    """
    ...

def set_imu_sample_rate(*args, **kwargs) -> Any:
    """
    Set IMU sample rate

    Args:
      handle: DeviceApi handle from open_brainsync_serial
      sample_rate: ImuSampleRate enum value
    """
    ...

def set_imu_transfer(*args, **kwargs) -> Any:
    """
    Set IMU transfer (start/stop data streaming)

    Args:
      handle: DeviceApi handle from open_brainsync_serial
      enable: True to start streaming, False to stop
    """
    ...

def set_mag_fullscale(*args, **kwargs) -> Any:
    """
    Set magnetometer fullscale

    Args:
      handle: DeviceApi handle from open_brainsync_serial
      fullscale: MagFullscale enum value
    """
    ...

def set_mag_sample_rate(*args, **kwargs) -> Any:
    """
    Set magnetometer sample rate

    Args:
      handle: DeviceApi handle from open_brainsync_serial
      sample_rate: MagSampleRate enum value
    """
    ...

def set_mag_transfer(*args, **kwargs) -> Any:
    """
    Set magnetometer transfer (start/stop data streaming)

    Args:
      handle: DeviceApi handle from open_brainsync_serial
      enable: True to start streaming, False to stop
    """
    ...

def set_stimulation_arm(*args, **kwargs) -> Any:
    """
    Set stimulation arm status

    Args:
      handle: DeviceApi handle from open_brainsync_serial
      armed: True to arm (enable high voltage), False to disarm
    """
    ...

def set_stimulation_params(*args, **kwargs) -> Any:
    """
    Set stimulation parameters

    Args:
      handle: DeviceApi handle from open_brainsync_serial
      chan: Channel number (0 or 1)
    """
    ...

def start_dfu(*args, **kwargs) -> Any:
    """
    Start DFU (Device Firmware Update) process
    """
    ...

def start_ota(*args, **kwargs) -> Any:
    """
    Start OTA firmware update

    Args:
      handle: DeviceApi handle from open_brainsync_serial
      file_size: Firmware file size in bytes (u32)
    """
    ...

def start_stimulation(*args, **kwargs) -> Any:
    """
    Start stimulation

    Args:
      handle: DeviceApi handle from open_brainsync_serial
    """
    ...

def stimulation_go(*args, **kwargs) -> Any:
    """
    Control stimulation (go command)

    Args:
      handle: DeviceApi handle from open_brainsync_serial
      channel_mask: Channel bitmask (bit0=CH0, bit1=CH1, e.g., 0x03=both channels)
    """
    ...

def stop_stimulation(*args, **kwargs) -> Any:
    """
    Stop stimulation

    Args:
      handle: DeviceApi handle from open_brainsync_serial
    """
    ...

def subscribe_adc_data(*args, **kwargs) -> Any:
    """
    Subscribe to ADC data stream with batch callback

    Args:
      handle: DeviceApi handle from open_brainsync_serial or open_brainsync_ble
      batch_size: Number of packets to buffer before callback
    """
    ...

def subscribe_eeg_data(*args, **kwargs) -> Any:
    """
    Subscribe to EEG data stream with batch callback

    This function subscribes to EEG data with batch processing to reduce
    the overhead of Rust-to-Python callback invocations. The callback will
    be triggered when the buffer reaches the specified batch size.
    """
    ...

def subscribe_imu_data(*args, **kwargs) -> Any:
    """
    Subscribe to IMU data stream with batch callback

    Args:
      handle: DeviceApi handle from open_brainsync_serial or open_brainsync_ble
      batch_size: Number of packets to buffer before callback
    """
    ...

def subscribe_mag_data(*args, **kwargs) -> Any:
    """
    Subscribe to magnetometer data stream with batch callback

    Args:
      handle: DeviceApi handle from open_brainsync_serial or open_brainsync_ble
      batch_size: Number of packets to buffer before callback
    """
    ...

def unsubscribe_adc_data(*args, **kwargs) -> Any:
    """
    Unsubscribe from ADC data stream

    Args:
      handle: DeviceApi handle from open_brainsync_serial or open_brainsync_ble
    """
    ...

def unsubscribe_eeg_data(*args, **kwargs) -> Any:
    """
    Unsubscribe from EEG data stream

    Args:
      handle: DeviceApi handle from open_brainsync_serial or open_brainsync_ble
    """
    ...

def unsubscribe_imu_data(*args, **kwargs) -> Any:
    """
    Unsubscribe from IMU data stream

    Args:
      handle: DeviceApi handle from open_brainsync_serial or open_brainsync_ble
    """
    ...

def unsubscribe_mag_data(*args, **kwargs) -> Any:
    """
    Unsubscribe from magnetometer data stream

    Args:
      handle: DeviceApi handle from open_brainsync_serial or open_brainsync_ble
    """
    ...
