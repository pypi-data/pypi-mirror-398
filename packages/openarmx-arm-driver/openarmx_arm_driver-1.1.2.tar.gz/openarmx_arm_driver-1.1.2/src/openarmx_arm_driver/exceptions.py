#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   exceptions.py
@Time    :   2025/12/16
@Author  :   Wei Lindong
@Version :   1.0
@Desc    :   OpenArmX Driver 异常类定义
             定义了所有可能抛出的自定义异常
'''


# ==================== 基础异常类 ====================

class OpenArmXError(Exception):
    """
    OpenArmX 驱动的基础异常类

    所有自定义异常都继承自此类，便于统一捕获和处理。

    示例:
        >>> try:
        >>>     arm.enable(motor_id=5)
        >>> except OpenArmXError as e:
        >>>     print(f"OpenArmX 错误: {e}")
    """
    pass


# ==================== CAN 通信相关异常 ====================

class CANError(OpenArmXError):
    """
    CAN 总线错误基类

    所有与 CAN 总线通信相关的异常都继承自此类。
    """
    pass


class CANInitializationError(CANError):
    """
    CAN 总线初始化失败异常

    当 CAN 总线无法初始化时抛出此异常。
    可能的原因：
    - CAN 接口不存在（如 can0 未配置）
    - 权限不足
    - 驱动未加载
    - 硬件故障

    示例:
        >>> try:
        >>>     arm = Arm('can9')  # can9 不存在
        >>> except CANInitializationError as e:
        >>>     print(f"CAN 初始化失败: {e}")
    """
    pass


class CANTimeoutError(CANError):
    """
    CAN 通信超时异常

    当 CAN 消息发送后在指定时间内未收到响应时抛出此异常。
    可能的原因：
    - 电机未连接或断电
    - CAN 总线故障
    - 电机ID配置错误
    - 网络拥堵

    参数:
        motor_id (int): 超时的电机ID
        timeout (float): 超时时间（秒）
    """
    def __init__(self, motor_id=None, timeout=None, message=None):
        if message is None:
            msg_parts = ["CAN 通信超时"]
            if motor_id is not None:
                msg_parts.append(f"电机ID: {motor_id}")
            if timeout is not None:
                msg_parts.append(f"超时: {timeout}s")
            message = " - ".join(msg_parts)
        super().__init__(message)
        self.motor_id = motor_id
        self.timeout = timeout


class CANTransmissionError(CANError):
    """
    CAN 消息发送失败异常

    当 CAN 消息无法发送到总线时抛出此异常。
    可能的原因：
    - CAN 总线错误
    - 总线关闭状态
    - 硬件故障
    """
    pass


# ==================== 电机相关异常 ====================

class MotorError(OpenArmXError):
    """
    电机错误基类

    所有与电机控制和状态相关的异常都继承自此类。
    """
    pass


class MotorNotEnabledError(MotorError):
    """
    电机未使能异常

    当尝试控制未使能的电机时抛出此异常。

    参数:
        motor_id (int): 未使能的电机ID

    示例:
        >>> # 在未使能的情况下尝试移动电机
        >>> arm.move_joint_position(motor_id=5, position=1.0)
        >>> # 抛出 MotorNotEnabledError
    """
    def __init__(self, motor_id, message=None):
        if message is None:
            message = f"电机 {motor_id} 未使能，请先调用 enable() 方法"
        super().__init__(message)
        self.motor_id = motor_id


class MotorFaultError(MotorError):
    """
    电机故障异常

    当电机报告故障状态时抛出此异常。

    参数:
        motor_id (int): 故障的电机ID
        fault_code (int): 故障代码
        fault_description (str): 故障描述

    故障类型：
        - 欠压故障 (bit 0)
        - 驱动故障 (bit 1)
        - 过温 (bit 2)
        - 磁编码故障 (bit 3)
        - 堵转过载故障 (bit 4)
        - 未标定 (bit 5)
    """
    def __init__(self, motor_id, fault_code=None, fault_description=None):
        msg_parts = [f"电机 {motor_id} 故障"]
        if fault_code is not None:
            msg_parts.append(f"故障代码: 0x{fault_code:02X}")
        if fault_description:
            msg_parts.append(f"描述: {fault_description}")
        message = " - ".join(msg_parts)
        super().__init__(message)
        self.motor_id = motor_id
        self.fault_code = fault_code
        self.fault_description = fault_description


class MotorTimeoutError(MotorError):
    """
    电机响应超时异常

    当电机在指定时间内未响应命令时抛出此异常。

    参数:
        motor_id (int): 超时的电机ID
        command (str): 超时的命令类型
        timeout (float): 超时时间（秒）
    """
    def __init__(self, motor_id, command=None, timeout=None):
        msg_parts = [f"电机 {motor_id} 响应超时"]
        if command:
            msg_parts.append(f"命令: {command}")
        if timeout is not None:
            msg_parts.append(f"超时: {timeout}s")
        message = " - ".join(msg_parts)
        super().__init__(message)
        self.motor_id = motor_id
        self.command = command
        self.timeout = timeout


class MotorCalibrationError(MotorError):
    """
    电机未标定异常

    当电机未完成标定就尝试使用时抛出此异常。

    参数:
        motor_id (int): 未标定的电机ID
    """
    def __init__(self, motor_id, message=None):
        if message is None:
            message = f"电机 {motor_id} 未标定，请先进行标定"
        super().__init__(message)
        self.motor_id = motor_id


# ==================== 配置相关异常 ====================

class ConfigurationError(OpenArmXError):
    """
    配置错误基类

    所有与配置相关的异常都继承自此类。
    """
    pass


class InvalidMotorIDError(ConfigurationError):
    """
    无效的电机ID异常

    当使用的电机ID不在有效范围内时抛出此异常。

    参数:
        motor_id: 无效的电机ID
        valid_range (tuple): 有效的ID范围，如 (1, 8)
    """
    def __init__(self, motor_id, valid_range=(1, 8)):
        message = f"无效的电机ID: {motor_id}，有效范围: {valid_range[0]}-{valid_range[1]}"
        super().__init__(message)
        self.motor_id = motor_id
        self.valid_range = valid_range


class InvalidModeError(ConfigurationError):
    """
    无效的控制模式异常

    当指定的控制模式不支持时抛出此异常。

    参数:
        mode: 无效的控制模式
        valid_modes (list): 有效的控制模式列表
    """
    def __init__(self, mode, valid_modes=None):
        if valid_modes is None:
            valid_modes = ['mit', 'csp', 'pp', 'speed', 'current']
        message = f"无效的控制模式: {mode}，有效模式: {valid_modes}"
        super().__init__(message)
        self.mode = mode
        self.valid_modes = valid_modes


class InvalidParameterError(ConfigurationError):
    """
    无效的参数异常

    当参数值不在有效范围内或格式错误时抛出此异常。

    参数:
        param_name (str): 参数名称
        param_value: 参数值
        reason (str): 无效的原因
    """
    def __init__(self, param_name, param_value, reason=None):
        msg_parts = [f"无效的参数 {param_name}: {param_value}"]
        if reason:
            msg_parts.append(f"原因: {reason}")
        message = " - ".join(msg_parts)
        super().__init__(message)
        self.param_name = param_name
        self.param_value = param_value
        self.reason = reason


class ConfigFileError(ConfigurationError):
    """
    配置文件错误异常

    当配置文件加载或解析失败时抛出此异常。

    参数:
        config_file (str): 配置文件路径
        reason (str): 错误原因
    """
    def __init__(self, config_file, reason=None):
        msg_parts = [f"配置文件错误: {config_file}"]
        if reason:
            msg_parts.append(f"原因: {reason}")
        message = " - ".join(msg_parts)
        super().__init__(message)
        self.config_file = config_file
        self.reason = reason


# ==================== 限制相关异常 ====================

class LimitExceededError(OpenArmXError):
    """
    超出限制基类

    所有与参数限制相关的异常都继承自此类。
    """
    pass


class PositionLimitError(LimitExceededError):
    """
    位置超限异常

    当设置的位置超出电机允许范围时抛出此异常。

    参数:
        motor_id (int): 电机ID
        position (float): 设置的位置值
        min_limit (float): 最小限制
        max_limit (float): 最大限制
    """
    def __init__(self, motor_id, position, min_limit, max_limit):
        message = (
            f"电机 {motor_id} 位置超限: {position:.3f} rad "
            f"(允许范围: {min_limit:.3f} ~ {max_limit:.3f} rad)"
        )
        super().__init__(message)
        self.motor_id = motor_id
        self.position = position
        self.min_limit = min_limit
        self.max_limit = max_limit


class VelocityLimitError(LimitExceededError):
    """
    速度超限异常

    当设置的速度超出电机允许范围时抛出此异常。

    参数:
        motor_id (int): 电机ID
        velocity (float): 设置的速度值
        min_limit (float): 最小限制
        max_limit (float): 最大限制
    """
    def __init__(self, motor_id, velocity, min_limit, max_limit):
        message = (
            f"电机 {motor_id} 速度超限: {velocity:.3f} rad/s "
            f"(允许范围: {min_limit:.3f} ~ {max_limit:.3f} rad/s)"
        )
        super().__init__(message)
        self.motor_id = motor_id
        self.velocity = velocity
        self.min_limit = min_limit
        self.max_limit = max_limit


class TorqueLimitError(LimitExceededError):
    """
    扭矩超限异常

    当设置的扭矩超出电机允许范围时抛出此异常。

    参数:
        motor_id (int): 电机ID
        torque (float): 设置的扭矩值
        min_limit (float): 最小限制
        max_limit (float): 最大限制
    """
    def __init__(self, motor_id, torque, min_limit, max_limit):
        message = (
            f"电机 {motor_id} 扭矩超限: {torque:.3f} Nm "
            f"(允许范围: {min_limit:.3f} ~ {max_limit:.3f} Nm)"
        )
        super().__init__(message)
        self.motor_id = motor_id
        self.torque = torque
        self.min_limit = min_limit
        self.max_limit = max_limit


class KpLimitError(LimitExceededError):
    """
    KP增益超限异常

    当设置的KP增益超出允许范围时抛出此异常。

    参数:
        motor_id (int): 电机ID
        kp (float): 设置的KP值
        min_limit (float): 最小限制
        max_limit (float): 最大限制
    """
    def __init__(self, motor_id, kp, min_limit, max_limit):
        message = (
            f"电机 {motor_id} KP增益超限: {kp:.3f} "
            f"(允许范围: {min_limit:.3f} ~ {max_limit:.3f})"
        )
        super().__init__(message)
        self.motor_id = motor_id
        self.kp = kp
        self.min_limit = min_limit
        self.max_limit = max_limit


class KdLimitError(LimitExceededError):
    """
    KD增益超限异常

    当设置的KD增益超出允许范围时抛出此异常。

    参数:
        motor_id (int): 电机ID
        kd (float): 设置的KD值
        min_limit (float): 最小限制
        max_limit (float): 最大限制
    """
    def __init__(self, motor_id, kd, min_limit, max_limit):
        message = (
            f"电机 {motor_id} KD增益超限: {kd:.3f} "
            f"(允许范围: {min_limit:.3f} ~ {max_limit:.3f})"
        )
        super().__init__(message)
        self.motor_id = motor_id
        self.kd = kd
        self.min_limit = min_limit
        self.max_limit = max_limit


# ==================== 连接相关异常 ====================

class ConnectionError(OpenArmXError):
    """
    连接错误异常

    当与硬件的连接出现问题时抛出此异常。
    """
    pass


class ConnectionLostError(ConnectionError):
    """
    连接丢失异常

    当与电机或CAN总线的连接丢失时抛出此异常。

    参数:
        device (str): 丢失连接的设备描述
    """
    def __init__(self, device=None):
        message = "连接丢失"
        if device:
            message += f": {device}"
        super().__init__(message)
        self.device = device


# ==================== 异常导出 ====================

__all__ = [
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
]
