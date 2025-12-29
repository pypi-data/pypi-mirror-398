"""
Type stubs for brainsync_sdk

BrainSync SDK - Python bindings for BrainSync device communication.
"""

from typing import Callable, Dict, Any
from enum import IntEnum

# Re-export from _native (internal Rust extension module)
from ._native import (
    # Enums
    EegGain,
    EegSampleRate,
    EegSignalType,
    EegStatus,
    ImuFullscale,
    ImuSampleRate,
    LeadoffCurrent,
    LeadoffStatus,
    LeadoffType,
    LogLevel,
    MagFullscale,
    MagSampleRate,
    NoiseType,
    OtaStatus,
    ResponseResult,
    StimMode,
    StimStatus,

    # Data types
    AdcDataPacket,
    EegDataPacket,
    ImpedanceData,
    ImuDataPacket,
    MagDataPacket,
    StimPolarity,
    StimulationParams,

    # Model types
    DeviceInfo,

    # DFU types
    PyDfuProgress,
    PyDfuState,

    # Serial utilities
    find_brainsync_serial_port,
    get_brainsync_usb_pid,
    get_brainsync_usb_vid,
    get_default_baudrate,
    list_serial_ports,
    open_brainsync_serial,

    # DeviceApi - Connection
    open_brainsync_ble,
    open_brainsync_ble_by_id,

    # DeviceApi - OTA
    get_firmware_version,
    reboot_device,
    send_ota_segment,
    start_ota,

    # DeviceApi - Stimulation
    arm_stimulation,
    disarm_stimulation,
    is_stimulation_armed,
    pause_stimulation,
    set_stimulation_arm,
    set_stimulation_params,
    start_stimulation,
    stimulation_go,
    stop_stimulation,

    # DeviceApi - EEG
    disable_all_eeg_leadoff_channels,
    enable_all_eeg_leadoff_channels,
    get_eeg_loss_stats,
    get_eeg_params,
    get_eeg_sample_rate_value,
    reset_eeg_loss_stats,
    set_eeg_gain,
    set_eeg_gains,
    set_eeg_leadoff_channel_mask,
    set_eeg_leadoff_channels,
    set_eeg_leadoff_current,
    set_eeg_leadoff_type,
    set_eeg_sample_rate,
    set_eeg_signal_type,
    set_eeg_signal_types,
    set_eeg_transfer,
    subscribe_eeg_data,
    unsubscribe_eeg_data,

    # DeviceApi - Impedance
    clear_impedance_callback,
    disable_impedance_detection_mode,
    enable_impedance_detection_mode,
    run_impedance_detection,
    set_impedance_callback,
    set_impedance_noise_type,

    # DeviceApi - IMU
    get_imu_params,
    set_imu_fullscale,
    set_imu_sample_rate,
    set_imu_transfer,
    subscribe_imu_data,
    unsubscribe_imu_data,

    # DeviceApi - Magnetometer
    get_mag_params,
    set_mag_fullscale,
    set_mag_sample_rate,
    set_mag_transfer,
    subscribe_mag_data,
    unsubscribe_mag_data,

    # DeviceApi - ADC
    set_adc_transfer,
    subscribe_adc_data,
    unsubscribe_adc_data,

    # Optional BLE imports (may not be available on all platforms)
    # In type stubs, we include them directly since type checkers don't execute code
    connect_ble_device,
    get_ble_rx_char_uuid,
    get_ble_service_uuid,
    get_ble_tx_char_uuid,
    py_ble_init_adapter,
    py_ble_write_value,
    py_clear_device_discovered_callback,
    py_clear_scan_result_callback,
    py_connect_ble,
    py_disconnect_ble,
    py_is_scanning,
    py_set_adapter_state_callback,
    py_set_battery_level_callback,
    py_set_connection_state_callback,
    py_set_device_discovered_callback,
    py_set_device_info_callback,
    py_set_mtu,
    py_set_received_data_callback,
    py_set_scan_result_callback,
    py_start_scan_with_uuids,
    py_stop_scan,
    scan_and_connect,

)

__version__: str

__all__ = [
    # Enums
    "EegGain",
    "EegSampleRate",
    "EegSignalType",
    "EegStatus",
    "ImuFullscale",
    "ImuSampleRate",
    "LeadoffCurrent",
    "LeadoffStatus",
    "LeadoffType",
    "LogLevel",
    "MagFullscale",
    "MagSampleRate",
    "NoiseType",
    "OtaStatus",
    "ResponseResult",
    "StimMode",
    "StimStatus",

    # Data types
    "AdcDataPacket",
    "EegDataPacket",
    "ImpedanceData",
    "ImuDataPacket",
    "MagDataPacket",
    "StimPolarity",
    "StimulationParams",

    # Model types
    "DeviceInfo",

    # DFU types
    "PyDfuProgress",
    "PyDfuState",

    # Serial utilities
    "find_brainsync_serial_port",
    "get_brainsync_usb_pid",
    "get_brainsync_usb_vid",
    "get_default_baudrate",
    "list_serial_ports",
    "open_brainsync_serial",

    # DeviceApi - Connection
    "open_brainsync_ble",
    "open_brainsync_ble_by_id",

    # DeviceApi - OTA
    "get_firmware_version",
    "reboot_device",
    "send_ota_segment",
    "start_ota",

    # DeviceApi - Stimulation
    "arm_stimulation",
    "disarm_stimulation",
    "is_stimulation_armed",
    "pause_stimulation",
    "set_stimulation_arm",
    "set_stimulation_params",
    "start_stimulation",
    "stimulation_go",
    "stop_stimulation",

    # DeviceApi - EEG
    "disable_all_eeg_leadoff_channels",
    "enable_all_eeg_leadoff_channels",
    "get_eeg_loss_stats",
    "get_eeg_params",
    "get_eeg_sample_rate_value",
    "reset_eeg_loss_stats",
    "set_eeg_gain",
    "set_eeg_gains",
    "set_eeg_leadoff_channel_mask",
    "set_eeg_leadoff_channels",
    "set_eeg_leadoff_current",
    "set_eeg_leadoff_type",
    "set_eeg_sample_rate",
    "set_eeg_signal_type",
    "set_eeg_signal_types",
    "set_eeg_transfer",
    "subscribe_eeg_data",
    "unsubscribe_eeg_data",

    # DeviceApi - Impedance
    "clear_impedance_callback",
    "disable_impedance_detection_mode",
    "enable_impedance_detection_mode",
    "run_impedance_detection",
    "set_impedance_callback",
    "set_impedance_noise_type",

    # DeviceApi - IMU
    "get_imu_params",
    "set_imu_fullscale",
    "set_imu_sample_rate",
    "set_imu_transfer",
    "subscribe_imu_data",
    "unsubscribe_imu_data",

    # DeviceApi - Magnetometer
    "get_mag_params",
    "set_mag_fullscale",
    "set_mag_sample_rate",
    "set_mag_transfer",
    "subscribe_mag_data",
    "unsubscribe_mag_data",

    # DeviceApi - ADC
    "set_adc_transfer",
    "subscribe_adc_data",
    "unsubscribe_adc_data",

]

# ========== Custom Type Annotations ==========
# This file contains manually maintained type annotations that provide
# more detailed type information than auto-generated stubs.
#
# These annotations will be appended to the auto-generated __init__.pyi

from typing import List, Callable, Dict, Any

# ========== EEG Data Subscription ==========

async def subscribe_eeg_data(
    handle: int,
    batch_size: int,
    callback: Callable[[List[EegDataPacket]], None]
) -> None:
    """
    Subscribe to EEG data stream with batch callback.
    
    This function subscribes to EEG data with batch processing to reduce
    the overhead of Rust-to-Python callback invocations. The callback will
    be triggered when the buffer reaches the specified batch size.
    
    Args:
        handle: DeviceApi handle from open_brainsync_serial or open_brainsync_ble
        batch_size: Number of packets to buffer before callback (must be multiple of 500)
        callback: Python callable that accepts a list of EegDataPacket
    
    Raises:
        ValueError: If batch_size is not a multiple of 500 or is 0
        RuntimeError: If subscription fails
    
    Example:
        ```python
        from typing import List
        
        def on_eeg_batch(packets: List[EegDataPacket]) -> None:
            print(f"Received {len(packets)} EEG packets")
            for packet in packets:
                print(f"  seq: {packet.seq_num}, ch0: {packet.channel_data[0]}")
        
        device = await open_brainsync_serial()
        await subscribe_eeg_data(device, 500, on_eeg_batch)
        await set_eeg_transfer(device, True)
        ```
    """
    ...

async def unsubscribe_eeg_data(handle: int) -> None:
    """
    Unsubscribe from EEG data stream.
    
    Args:
        handle: DeviceApi handle from open_brainsync_serial or open_brainsync_ble
    
    Example:
        ```python
        await unsubscribe_eeg_data(device)
        ```
    """
    ...

async def get_eeg_loss_stats(handle: int) -> Dict[str, Any]:
    """
    Get EEG packet loss statistics.
    
    Args:
        handle: DeviceApi handle from open_brainsync_serial or open_brainsync_ble
    
    Returns:
        Dictionary with loss statistics:
        - total_received (int): Total number of packets received
        - total_lost (int): Total number of packets lost
        - loss_rate (float): Packet loss rate in percentage (0-100)
    
    Note:
        The loss_rate is already in percentage form (0-100), not a ratio (0-1).
        Do not multiply by 100 again.
    
    Example:
        ```python
        stats = await get_eeg_loss_stats(device)
        print(f"Received: {stats['total_received']}")
        print(f"Lost: {stats['total_lost']}")
        print(f"Loss rate: {stats['loss_rate']:.4f}%")  # Already in percentage
        
        # Calculate total expected packets
        total_expected = stats['total_received'] + stats['total_lost']
        ```
    """
    ...

async def reset_eeg_loss_stats(handle: int) -> None:
    """
    Reset EEG packet loss statistics.
    
    Args:
        handle: DeviceApi handle from open_brainsync_serial or open_brainsync_ble
    
    Example:
        ```python
        # Reset statistics before starting data collection
        await reset_eeg_loss_stats(device)
        await set_eeg_transfer(device, True)
        ```
    """
    ...
