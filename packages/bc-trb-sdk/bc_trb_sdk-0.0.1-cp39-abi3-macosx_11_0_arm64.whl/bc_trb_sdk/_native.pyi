"""
Type stubs for bc_trb_sdk._native

This file provides type hints for the Rust extension module.
Auto-generated from Rust code.
"""

from typing import Any, Callable, Optional
from enum import IntEnum

# ========== Enums ==========

# ========== Classes ==========

class DeviceApi:
    
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
    
    def close(self, *args, **kwargs) -> Any:
        """
        关闭设备
        """
        ...
    
    def trigger(self, *args, **kwargs) -> Any:
        """
        获取 TriggerApi
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
    

class TrbAdcValue:
    """
    ADC 读数

    DATA 结构：[adc_value_max (4), vref_mv (4), values[5] (5 * 2)] (18 bytes)
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
    
    def aud_voltage_mv(self, *args, **kwargs) -> Any:
        """
        获取 AUD 通道电压（mV）
        """
        ...
    
    def mic_voltage_mv(self, *args, **kwargs) -> Any:
        """
        获取 MIC 通道电压（mV）
        """
        ...
    
    def pd_voltage_mv(self, *args, **kwargs) -> Any:
        """
        获取 PD 通道电压（mV）
        """
        ...
    
    def value_to_mv(self, *args, **kwargs) -> Any:
        """
        将 ADC 值转换为电压（mV）
        """
        ...
    
    def vref_v(self, *args, **kwargs) -> Any:
        """
        获取参考电压（V）
        """
        ...
    

class TrbConfig:
    """
    Trigger 信号配置

    DATA 结构：[PD_enabled (1), PD_threshold (4), AUD_enabled (1), AUD_threshold (4),
               MIC_enabled (1), MIC_threshold (4)] (15 bytes)
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
    

class TrbStatus:
    """
    Trigger 信号状态

    DATA 结构：[PD_active, AUD_active, MIC_active, BTN_active] (4 bytes)
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
    

class TriggerApi:
    
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
    
    def get_adc_transfer_status(self, *args, **kwargs) -> Any:
        """
        获取 ADC 传输状态
        """
        ...
    
    def get_adc_value(self, *args, **kwargs) -> Any:
        """
        获取 ADC 值
        """
        ...
    
    def get_config(self, *args, **kwargs) -> Any:
        """
        获取配置
        """
        ...
    
    def get_status(self, *args, **kwargs) -> Any:
        """
        获取 TriggerBox 各信号激活状态
        """
        ...
    
    def set_adc_transfer(self, *args, **kwargs) -> Any:
        """
        设置 ADC 传输状态
        """
        ...
    
    def set_config(self, *args, **kwargs) -> Any:
        """
        设置配置
        """
        ...
    
    def set_signal_config(self, *args, **kwargs) -> Any:
        """
        设置单个信号配置
        """
        ...
    
    def set_signal_config_mv(self, *args, **kwargs) -> Any:
        """
        使用电压值设置信号配置
        """
        ...
    

# ========== Functions ==========

def open_bc_trb_usb(*args, **kwargs) -> Any:
    """
    打开 TriggerBox 设备（USB）

    自动查找并连接 TriggerBox 设备

    Returns:
    """
    ...
