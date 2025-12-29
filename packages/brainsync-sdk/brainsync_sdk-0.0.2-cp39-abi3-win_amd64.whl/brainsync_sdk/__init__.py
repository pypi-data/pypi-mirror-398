"""
BrainSync SDK - Python bindings for EEG-CES device communication.

This package provides a Python interface to the BrainSync SDK for EEG data acquisition.

Example:
    >>> from brainsync_sdk import EegSampleRate, list_serial_ports
    >>> ports = list_serial_ports(0xCAFE, 0x4012)
    >>> print(f"Found {len(ports)} BrainSync devices")
"""

__version__ = "0.1.0"

# Import from the Rust extension module
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

    # Data types (from model/)
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

    # DeviceApi functions - Connection
    open_brainsync_ble,
    open_brainsync_ble_by_id,

    # DeviceApi functions - OTA
    get_firmware_version,
    reboot_device,
    send_ota_segment,
    start_ota,

    # DeviceApi functions - Stimulation
    arm_stimulation,
    disarm_stimulation,
    is_stimulation_armed,
    pause_stimulation,
    set_stimulation_arm,
    set_stimulation_params,
    start_stimulation,
    stimulation_go,
    stop_stimulation,

    # DeviceApi functions - EEG
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

    # DeviceApi functions - Impedance
    clear_impedance_callback,
    disable_impedance_detection_mode,
    enable_impedance_detection_mode,
    run_impedance_detection,
    set_impedance_callback,
    set_impedance_noise_type,

    # DeviceApi functions - IMU
    get_imu_params,
    set_imu_fullscale,
    set_imu_sample_rate,
    set_imu_transfer,
    subscribe_imu_data,
    unsubscribe_imu_data,

    # DeviceApi functions - Magnetometer
    get_mag_params,
    set_mag_fullscale,
    set_mag_sample_rate,
    set_mag_transfer,
    subscribe_mag_data,
    unsubscribe_mag_data,

    # DeviceApi functions - ADC
    set_adc_transfer,
    subscribe_adc_data,
    unsubscribe_adc_data,

)

# Optional BLE imports (may not be available on all platforms)
try:
    from ._native import (
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
    _BLE_AVAILABLE = True
except ImportError:
    _BLE_AVAILABLE = False

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

    # DeviceApi functions - Connection
    "open_brainsync_ble",
    "open_brainsync_ble_by_id",

    # DeviceApi functions - OTA
    "get_firmware_version",
    "reboot_device",
    "send_ota_segment",
    "start_ota",

    # DeviceApi functions - Stimulation
    "arm_stimulation",
    "disarm_stimulation",
    "is_stimulation_armed",
    "pause_stimulation",
    "set_stimulation_arm",
    "set_stimulation_params",
    "start_stimulation",
    "stimulation_go",
    "stop_stimulation",

    # DeviceApi functions - EEG
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

    # DeviceApi functions - Impedance
    "clear_impedance_callback",
    "disable_impedance_detection_mode",
    "enable_impedance_detection_mode",
    "run_impedance_detection",
    "set_impedance_callback",
    "set_impedance_noise_type",

    # DeviceApi functions - IMU
    "get_imu_params",
    "set_imu_fullscale",
    "set_imu_sample_rate",
    "set_imu_transfer",
    "subscribe_imu_data",
    "unsubscribe_imu_data",

    # DeviceApi functions - Magnetometer
    "get_mag_params",
    "set_mag_fullscale",
    "set_mag_sample_rate",
    "set_mag_transfer",
    "subscribe_mag_data",
    "unsubscribe_mag_data",

    # DeviceApi functions - ADC
    "set_adc_transfer",
    "subscribe_adc_data",
    "unsubscribe_adc_data",

]