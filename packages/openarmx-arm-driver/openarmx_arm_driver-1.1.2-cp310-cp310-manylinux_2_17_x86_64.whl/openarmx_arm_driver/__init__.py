#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   __init__.py
@Time    :   2025/12/16
@Author  :   Wei Lindong
@Version :   1.0
@Desc    :   OpenArmX Driver - Python SDK for OpenArmX robotic arm control
'''

# ==================== 主接口 ====================
from .arm import Arm
from .robot import Robot

# ==================== 异常系统 ====================
from .exceptions import (
    # 基础异常
    OpenArmXError,

    # CAN 通信异常
    CANError,
    CANInitializationError,
    CANTimeoutError,
    CANTransmissionError,

    # 电机异常
    MotorError,
    MotorNotEnabledError,
    MotorFaultError,
    MotorTimeoutError,
    MotorCalibrationError,

    # 配置异常
    ConfigurationError,
    InvalidMotorIDError,
    InvalidModeError,
    InvalidParameterError,
    ConfigFileError,

    # 限制异常
    LimitExceededError,
    PositionLimitError,
    VelocityLimitError,
    TorqueLimitError,
    KpLimitError,
    KdLimitError,

    # 连接异常
    ConnectionError,
    ConnectionLostError,
)

# ==================== CAN 通信层 ====================
# CAN 帧收发和数据转换
from ._lib.can_comm import (
    # 数据类型转换
    float_to_uint16,
    uint16_to_float,
    float_to_P4hex,
    P4hex_to_float,

    # CAN 帧收发
    send_extended_frame_main,
    send_extended_frame_no_wait,
    send_extended_frame_with_retry,
)

# CAN 接口管理工具
from ._lib.can_utils import (
    get_available_can_interfaces,
    get_all_can_interfaces,
    check_can_interface_type,
    verify_can_interface,
    enable_can_interface,
    disable_can_interface,
    enable_all_can_interfaces,
    disable_all_can_interfaces,
    pair_can_channels,
)

# ==================== 电机管理层 ====================
# 电机管理接口
from ._lib.motor_manager import (
    # 数据解析
    parse_motor_feedback,
    parse_control_mode_and_status,

    # 状态查询
    get_motor_status_readonly,
    get_motor_basic_telemetry,

    # 使能控制
    enable_motor,
    disable_motor,
    enable_all_motors,
    disable_all_motors,

    # 模式设置
    set_control_mode,

    # 参数读写
    read_motor_parameter,

    # 零点管理
    set_motor_zero,
    set_zero_sta_parameter,

    # CAN ID 设置
    set_motor_canid,
)

# 电机控制接口
from ._lib.motor_control import (
    # MIT 模式控制
    mit_motion_control,
    mit_motion_control_simple,
    mit_velocity_control,
    mit_torque_control,
    mit_zero_position,

    # CSP 模式控制
    csp_motion_control,
    csp_set_speed_limits,
    csp_move_to_flowwork,
)

# ==================== 配置和工具 ====================
# 配置加载器
from ._lib.motor_config_loader import MotorConfigLoader

# 日志工具
from ._lib.log_utils import (
    log_output,
    log_info,
    log_success,
    log_warning,
    log_error,
)

__version__ = '1.1.2'
__author__ = 'Wei Lindong'

__all__ = [
    # ==================== 主接口 ====================
    'Arm',
    'Robot',

    # ==================== 异常系统 ====================
    # 基础异常
    'OpenArmXError',

    # CAN 通信异常
    'CANError',
    'CANInitializationError',
    'CANTimeoutError',
    'CANTransmissionError',

    # 电机异常
    'MotorError',
    'MotorNotEnabledError',
    'MotorFaultError',
    'MotorTimeoutError',
    'MotorCalibrationError',

    # 配置异常
    'ConfigurationError',
    'InvalidMotorIDError',
    'InvalidModeError',
    'InvalidParameterError',
    'ConfigFileError',

    # 限制异常
    'LimitExceededError',
    'PositionLimitError',
    'VelocityLimitError',
    'TorqueLimitError',
    'KpLimitError',
    'KdLimitError',

    # 连接异常
    'ConnectionError',
    'ConnectionLostError',

    # ==================== CAN 通信层 ====================
    # 数据类型转换
    'float_to_uint16',
    'uint16_to_float',
    'float_to_P4hex',
    'P4hex_to_float',

    # # CAN 帧收发
    # 'send_extended_frame_main',
    # 'send_extended_frame_no_wait',
    # 'send_extended_frame_with_retry',

    # CAN 接口管理
    'get_available_can_interfaces',
    'get_all_can_interfaces',
    'check_can_interface_type',
    'verify_can_interface',
    'enable_can_interface',
    'disable_can_interface',
    'enable_all_can_interfaces',
    'disable_all_can_interfaces',
    'pair_can_channels',

    # # ==================== 电机管理层 ====================
    # # 数据解析
    # 'parse_motor_feedback',
    # 'parse_control_mode_and_status',

    # # 状态查询
    # 'get_motor_status_readonly',
    # 'get_motor_basic_telemetry',

    # # 使能控制
    # 'enable_motor',
    # 'disable_motor',
    # 'enable_all_motors',
    # 'disable_all_motors',

    # # 模式设置
    # 'set_control_mode',

    # # 参数读写
    # 'read_motor_parameter',

    # # 零点管理
    # 'set_motor_zero',
    # 'set_zero_sta_parameter',

    # # CAN ID 设置
    # 'set_motor_canid',

    # # ==================== 电机控制层 ====================
    # # MIT 模式控制
    # 'mit_motion_control',
    # 'mit_motion_control_simple',
    # 'mit_velocity_control',
    # 'mit_torque_control',
    # 'mit_zero_position',

    # # CSP 模式控制
    # 'csp_motion_control',
    # 'csp_set_speed_limits',
    # 'csp_move_to_flowwork',

    # # ==================== 配置和工具 ====================
    # # 配置加载器
    # 'MotorConfigLoader',

    # # 日志工具
    # 'log_output',
    # 'log_info',
    # 'log_success',
    # 'log_warning',
    # 'log_error',
]
