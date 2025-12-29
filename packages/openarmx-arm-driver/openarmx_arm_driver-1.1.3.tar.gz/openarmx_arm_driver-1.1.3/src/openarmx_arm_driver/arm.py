#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   arm.py
@Time    :   2025/12/16
@Author  :   Wei Lindong
@Version :   1.0
@Desc    :   OpenArmX 机械臂控制类 - 主要对外接口
'''

import can
import time
from typing import Optional, List, Dict, Union, Tuple

# 导入异常类
from .exceptions import (
    CANInitializationError,
    InvalidMotorIDError,
    InvalidModeError,
)

# 导入内部模块
from ._lib.motor_manager import (
    enable_motor,
    disable_motor,
    enable_all_motors,
    disable_all_motors,
    set_control_mode,
    get_motor_status_readonly,
    get_motor_basic_telemetry,
    set_motor_zero,
    set_zero_sta_parameter,
    read_motor_parameter
)

from ._lib.motor_control import (
    mit_motion_control,
    mit_motion_control_simple,
    mit_zero_position,
    mit_velocity_control,
    mit_torque_control,
    csp_motion_control,
    csp_set_speed_limits,
    csp_move_to_flowwork
)

from ._lib.motor_config_loader import MotorConfigLoader
from ._lib.log_utils import log_output
from ._lib.can_utils import (
    verify_can_interface,
    enable_can_interface
)

class Arm:
    """
    OpenArmX 机械臂控制类

    这是 openarmx_driver 包的主要对外接口，用于控制基于 Robstride 电机的机械臂。
    每条机械臂有8个电机，通过 CAN 总线进行通信。

    电机配置映射:
        - 电机 1-2: RS04 型号 (大扭矩关节)
        - 电机 3-4: RS03 型号 (中扭矩关节)
        - 电机 5-8: RS00 型号 (小扭矩关节/夹爪)

    参数:
        can_channel (str): CAN 通道名称，如 'can0', 'can1' 等
        side (str, optional): 机械臂方向
            - 'left': 左臂（默认所有电机方向反转）
            - 'right': 右臂（默认所有电机方向正常）
            - None: 不使用方向配置（所有电机方向正常）
        bustype (str): CAN 总线类型，默认 'socketcan'
        bitrate (int): CAN 总线波特率，默认 1000000 (1Mbps)
        motor_ids (List[int]): 要控制的电机ID列表，默认 [1,2,3,4,5,6,7,8]
        direction_multipliers (Dict[int, float], optional): 自定义每个电机的方向系数
            - 1.0: 正常方向
            - -1.0: 反转方向
            如果提供此参数，将覆盖 side 参数的默认配置

    示例:
        >>> # 创建右臂实例
        >>> right_arm = Arm('can0', side='right')
        >>>
        >>> # 创建左臂实例（电机方向自动反转）
        >>> left_arm = Arm('can1', side='left')
        >>>
        >>> # 自定义方向配置（只反转电机1和2）
        >>> custom_arm = Arm('can0', direction_multipliers={1: -1, 2: -1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1})
        >>>
        >>> # 使能所有电机
        >>> right_arm.enable_all()
        >>>
        >>> # 设置为 MIT 模式并移动电机
        >>> right_arm.set_mode('mit')
        >>> right_arm.move_joint_mit(motor_id=5, position=1.0, kp=20, kd=2)
        >>>
        >>> # 获取电机状态
        >>> status = right_arm.get_status(motor_id=5)
        >>> print(f"角度: {status['angle']}, 速度: {status['velocity']}")
        >>>
        >>> # 停止所有电机
        >>> right_arm.disable_all()
        >>>
        >>> # 关闭连接
        >>> right_arm.close()
    """

    def __init__(self,
                 can_channel: str,
                 side: Optional[str] = None,
                 bustype: str = 'socketcan',
                 bitrate: int = 1000000,
                 motor_ids: Optional[List[int]] = None,
                 direction_multipliers: Optional[Dict[int, float]] = None,
                 auto_enable_can: bool = True,
                 password: Optional[str] = None,
                 log=None):
        """
        初始化机械臂控制器

        参数:
            can_channel (str): CAN 通道名称，如 'can0', 'can1'
            side (str, optional): 机械臂方向 ('left', 'right', None)
            bustype (str): CAN 总线类型，默认 'socketcan'
            bitrate (int): CAN 总线波特率，默认 1000000
            motor_ids (List[int]): 要控制的电机ID列表，默认 [1,2,3,4,5,6,7,8]
            direction_multipliers (Dict[int, float], optional): 自定义方向系数
            auto_enable_can (bool): 是否自动检测并启用 CAN 接口，默认 True
            password (str, optional): sudo密码，用于自动启用CAN接口，默认 None（手动输入密码）
            log: 日志函数
        """
        self.can_channel = can_channel
        self.side = side
        self.bustype = bustype
        self.bitrate = bitrate
        self.motor_ids = motor_ids if motor_ids is not None else list(range(1, 9))
        self.log = log

        # 检测并启用 CAN 接口
        if auto_enable_can:
            self._check_and_enable_can(can_channel, bitrate, password)

        # 初始化 CAN 总线
        try:
            self.bus = can.Bus(
                channel=can_channel,
                bustype=bustype,
                bitrate=bitrate
            )
            side_info = f" ({side}臂)" if side else ""
            log_output(f"[Arm] CAN 总线 {can_channel}{side_info} 初始化成功", "SUCCESS", self.log)
        except Exception as e:
            raise CANInitializationError(
                f"CAN 总线 {can_channel} 初始化失败: {e}\n"
                f"请检查:\n"
                f"  1. CAN 接口是否存在 (ip link show {can_channel})\n"
                f"  2. CAN 接口是否已启动 (sudo ip link set {can_channel} up type can bitrate {bitrate})\n"
                f"  3. 是否有足够的权限\n"
                f"  4. CAN 驱动是否已加载 (lsmod | grep can)"
            )

        # 加载电机配置
        self.config_loader = MotorConfigLoader()

        # 设置方向系数
        self._setup_direction_multipliers(direction_multipliers)

        # 当前控制模式记录 (用于用户参考)
        self._current_mode: Dict[int, str] = {}

        log_output(f"[Arm] 机械臂初始化完成，电机ID: {self.motor_ids}", level="SUCCESS", log=log)

    def _check_and_enable_can(self, interface: str, bitrate: int = 1000000, password: Optional[str] = None):
        """
        检测并启用 CAN 接口

        参数:
            interface (str): CAN 接口名称
            bitrate (int): 波特率
            password (str, optional): sudo密码，默认 None（手动输入密码）

        异常:
            CANInitializationError: 启用失败
        """
        # 检查接口是否已经启用
        if verify_can_interface(interface):
            log_output(f"✓ {interface} 已启用", "SUCCESS", self.log)
            return

        # 尝试启用接口
        log_output(f"⚠ {interface} 未启用，正在尝试启用...", "WARNING", self.log)
        success = enable_can_interface(interface, bitrate=bitrate, verbose=False, password=password)

        if not success:
            raise CANInitializationError(
                f"无法启用 {interface}。请手动执行:\n"
                f"  sudo ip link set {interface} up type can bitrate {bitrate}"
            )

        log_output(f"✓ {interface} 启用成功", "SUCCESS", self.log)

    def _setup_direction_multipliers(self, custom_multipliers: Optional[Dict[int, float]] = None):
        """
        设置电机方向系数

        参数:
            custom_multipliers (Dict[int, float], optional): 自定义方向系数
        """
        # 如果提供了自定义方向系数，直接使用
        if custom_multipliers is not None:
            self.direction_multipliers = custom_multipliers
            log_output(f"[Arm] 使用自定义方向配置: {custom_multipliers}", "INFO", self.log)
            return

        # 根据 side 参数从配置文件加载方向系数
        if self.side in ['left', 'right']:
            # 从配置加载器获取方向系数
            self.direction_multipliers = self.config_loader.get_direction_multipliers(
                self.side, self.motor_ids
            )
            log_output(f"[Arm] {self.side}臂模式：从配置文件加载方向系数", "INFO", self.log)
            if len(self.direction_multipliers) > 0:
                # 显示方向配置摘要
                reversed_motors = [mid for mid, mult in self.direction_multipliers.items() if mult < 0]
                if reversed_motors:
                    log_output(f"[Arm] 反转电机: {reversed_motors}", "INFO", self.log)
                else:
                    log_output(f"[Arm] 所有电机方向正常", "INFO", self.log)
        else:
            # 未指定方向：所有电机方向正常
            self.direction_multipliers = {i: 1.0 for i in self.motor_ids}

    def _validate_motor_id(self, motor_id: int):
        """
        验证电机ID是否有效

        参数:
            motor_id (int): 电机ID

        抛出:
            InvalidMotorIDError: 如果电机ID无效
        """
        if motor_id not in self.motor_ids:
            raise InvalidMotorIDError(
                motor_id,
                valid_range=(min(self.motor_ids), max(self.motor_ids))
            )

    def _apply_direction(self, motor_id: int, value: float) -> float:
        """
        应用方向系数到数值

        参数:
            motor_id (int): 电机ID
            value (float): 原始数值（位置、速度或扭矩）

        返回:
            float: 应用方向系数后的数值
        """
        multiplier = self.direction_multipliers.get(motor_id, 1.0)
        return value * multiplier

    def _reverse_direction(self, motor_id: int, value: float) -> float:
        """
        反向应用方向系数（用于读取反馈值）

        参数:
            motor_id (int): 电机ID
            value (float): 反馈数值

        返回:
            float: 反向应用方向系数后的数值
        """
        multiplier = self.direction_multipliers.get(motor_id, 1.0)
        return value * multiplier  # 乘法是对称的，所以反向也是乘以相同系数

    # ==================== 基础控制方法 ====================

    def enable(self, motor_id: int, timeout: float = 1.0, verbose: bool = False) -> int:
        """
        使能指定电机

        参数:
            motor_id (int): 电机ID (1-8)
            timeout (float): 超时时间(秒)
            verbose (bool): 是否打印详细信息

        返回:
            int: 0=成功, 1=失败

        抛出:
            InvalidMotorIDError: 如果电机ID无效
        """
        self._validate_motor_id(motor_id)
        return enable_motor(self.bus, motor_id, timeout=timeout, verbose=verbose)

    def disable(self, motor_id: int, timeout: float = 1.0, verbose: bool = False) -> int:
        """
        停止指定电机

        参数:
            motor_id (int): 电机ID (1-8)
            timeout (float): 超时时间(秒)
            verbose (bool): 是否打印详细信息

        返回:
            int: 0=成功, 1=失败

        抛出:
            InvalidMotorIDError: 如果电机ID无效
        """
        self._validate_motor_id(motor_id)
        return disable_motor(self.bus, motor_id, timeout=timeout, verbose=verbose)

    def enable_all(self, verbose: bool = False) -> Dict[int, int]:
        """
        使能所有电机

        参数:
            verbose (bool): 是否打印详细信息

        返回:
            Dict[int, int]: {motor_id: state} 每个电机的状态
        """
        return enable_all_motors(self.bus, motor_ids=self.motor_ids, verbose=verbose)

    def disable_all(self, verbose: bool = False) -> Dict[int, int]:
        """
        停止所有电机

        参数:
            verbose (bool): 是否打印详细信息

        返回:
            Dict[int, int]: {motor_id: state} 每个电机的状态
        """
        return disable_all_motors(self.bus, motor_ids=self.motor_ids, verbose=verbose)

    # ==================== 模式设置 ====================

    def set_mode(self, mode: Union[str, int],
                 motor_id: Optional[int] = None,
                 timeout: float = 1.0,
                 verbose: bool = False) -> int:
        """
        设置电机控制模式

        参数:
            mode (str|int): 控制模式
                - 'mit' / 0: MIT 运控模式
                - 'csp' / 5: CSP 位置模式
                - 'pp' / 1: PP 位置模式
                - 'speed' / 2: 速度模式
                - 'current' / 3: 电流模式
            motor_id (int, optional): 电机ID，如果为 None 则设置所有电机
            timeout (float): 超时时间(秒)
            verbose (bool): 是否打印详细信息

        返回:
            int: 0=成功, 非0=失败（单个电机）或失败次数（所有电机）

        抛出:
            InvalidMotorIDError: 如果电机ID无效
            InvalidModeError: 如果控制模式无效
        """
        # 验证模式
        valid_modes = ['mit', 'pp', 'speed', 'current', 'csp', 0, 1, 2, 3, 5]
        if mode not in valid_modes:
            raise InvalidModeError(mode, valid_modes=['mit', 'pp', 'speed', 'current', 'csp'])

        if motor_id is not None:
            # 验证电机ID
            self._validate_motor_id(motor_id)

            # 设置单个电机
            state = set_control_mode(self.bus, motor_id, mode=mode,
                                    timeout=timeout, verbose=verbose)
            if state == 0:
                self._current_mode[motor_id] = str(mode)
            return state
        else:
            # 设置所有电机
            failed_count = 0
            for mid in self.motor_ids:
                state = set_control_mode(self.bus, mid, mode=mode,
                                        timeout=timeout, verbose=verbose)
                if state == 0:
                    self._current_mode[mid] = str(mode)
                else:
                    failed_count += 1
                time.sleep(0.01)
            return failed_count

    # ==================== 状态查询 ====================

    def get_status(self, motor_id: int,
                   timeout: float = 1.0,
                   verbose: bool = False) -> Optional[Dict]:
        """
        获取电机状态

        参数:
            motor_id (int): 电机ID (1-8)
            timeout (float): 超时时间(秒)
            verbose (bool): 是否打印详细信息

        返回:
            Dict 或 None: 包含 angle, velocity, torque, temperature,
                         mode_status, fault_status 等字段
        """
        state, info = get_motor_status_readonly(
            self.bus, motor_id,
            timeout=timeout, verbose=verbose
        )

        # 应用反向方向系数到反馈值
        if state == 0 and info is not None:
            if 'angle' in info:
                info['angle'] = self._reverse_direction(motor_id, info['angle'])
            if 'velocity' in info:
                info['velocity'] = self._reverse_direction(motor_id, info['velocity'])
            if 'torque' in info:
                info['torque'] = self._reverse_direction(motor_id, info['torque'])

        return info if state == 0 else None

    def get_telemetry(self, motor_id: int,
                     timeout: float = 1.0,
                     verbose: bool = False) -> Optional[Dict]:
        """
        获取电机基本遥测数据

        参数:
            motor_id (int): 电机ID (1-8)
            timeout (float): 超时时间(秒)
            verbose (bool): 是否打印详细信息

        返回:
            Dict 或 None: 包含 mech_pos, mech_vel, iqf, vbus 等字段
        """
        state, info = get_motor_basic_telemetry(
            self.bus, motor_id,
            timeout=timeout, verbose=verbose
        )

        # 应用反向方向系数到反馈值
        if state == 0 and info is not None:
            if 'mech_pos' in info:
                info['mech_pos'] = self._reverse_direction(motor_id, info['mech_pos'])
            if 'mech_vel' in info:
                info['mech_vel'] = self._reverse_direction(motor_id, info['mech_vel'])
            # iqf 和 vbus 不需要反转

        return info if state == 0 else None

    def get_all_status(self, timeout: float = 1.0, verbose: bool = False) -> Dict[int, Optional[Dict]]:
        """
        获取所有电机的状态

        参数:
            timeout (float): 超时时间(秒)
            verbose (bool): 是否打印详细信息

        返回:
            Dict[int, Dict]: {motor_id: status_dict}
        """
        results = {}
        for motor_id in self.motor_ids:
            results[motor_id] = self.get_status(motor_id, timeout=timeout, verbose=verbose)
        return results

    def show_motor_status(self, motor_id: Optional[int] = None,
                         show_header: bool = True) -> None:
        """
        显示电机状态（格式化输出）

        参数:
            motor_id (int, optional): 电机ID，如果为None则显示所有电机
            show_header (bool): 是否显示表头

        示例:
            >>> arm.show_motor_status(3)  # 显示单个电机
            >>> arm.show_motor_status()    # 显示所有电机
        """
        # 打印表头
        if show_header:
            log_output("="*120, "INFO", self.log)
            log_output("电机状态", "INFO", self.log)
            log_output("="*120, "INFO", self.log)
            log_output("ID | 角度(rad) | 速度(rad/s) | 力矩(Nm) |  温度    | 模式              | 状态", "INFO", self.log)
            log_output("-"*120, "INFO", self.log)

        # 获取状态信息
        if motor_id is not None:
            # 显示单个电机
            try:
                info = self.get_status(motor_id)
                if info:
                    self._print_single_motor_status(motor_id, info)
                else:
                    log_output(f"ID:{motor_id:2d} | ✗ 无响应 - 电机未连接或已断电", "ERROR", self.log)
            except Exception as e:
                log_output(f"ID:{motor_id:2d} | ⚠ 异常 - {str(e)}", "ERROR", self.log)
        else:
            # 显示所有电机
            for mid in self.motor_ids:
                try:
                    info = self.get_status(mid)
                    if info:
                        self._print_single_motor_status(mid, info)
                    else:
                        log_output(f"ID:{mid:2d} | ✗ 无响应", "WARNING", self.log)
                except Exception as e:
                    log_output(f"ID:{mid:2d} | ⚠ 异常 - {str(e)}", "WARNING", self.log)

        if show_header:
            log_output("="*120, "INFO", self.log)

    def _print_single_motor_status(self, motor_id: int, info: dict) -> None:
        """
        打印单个电机的状态信息（内部辅助函数）

        参数:
            motor_id (int): 电机ID
            info (dict): 状态信息字典
        """
        # 根据模式状态选择图标
        mode_status = info.get('mode_status', '未知')
        if 'Motor模式' in mode_status or '运行' in mode_status:
            mode_icon = "🟢"
        elif 'Reset模式' in mode_status or '复位' in mode_status:
            mode_icon = "🔴"
        elif 'Cali模式' in mode_status or '标定' in mode_status:
            mode_icon = "🟡"
        else:
            mode_icon = "⚪"

        # 根据故障状态选择图标
        fault_status = info.get('fault_status', '未知')
        if fault_status == "正常":
            fault_icon = "✓"
        else:
            fault_icon = "⚠"

        # 格式化输出
        log_output(f"ID:{motor_id:2d} | "
                   f"{info.get('angle', 0.0):9.3f} | "
                   f"{info.get('velocity', 0.0):11.3f} | "
                   f"{info.get('torque', 0.0):8.3f} | "
                   f"{info.get('temperature', 0.0):5.1f}°C | "
                   f"{mode_icon} {mode_status:15s} | "
                   f"{fault_icon} {fault_status}",
                   "INFO", self.log)

    # ==================== MIT 模式控制 ====================

    def move_joint_mit(self, motor_id: int,
                      position: float = 0.0,
                      velocity: float = 0.0,
                      torque: float = 0.0,
                      kp: float = 0.0,
                      kd: float = 0.0,
                      wait_response: bool = False,
                      timeout: float = 1.0,
                      verbose: bool = False) -> int:
        """
        MIT 模式运动控制

        参数:
            motor_id (int): 电机ID (1-8)
            position (float): 目标位置 (弧度)
            velocity (float): 目标速度 (弧度/秒)
            torque (float): 前馈扭矩 (牛米)
            kp (float): 位置增益
            kd (float): 速度增益
            wait_response (bool): 是否等待响应
            timeout (float): 超时时间(秒)
            verbose (bool): 是否打印详细信息

        返回:
            int: 0=成功, 1=失败

        抛出:
            InvalidMotorIDError: 如果电机ID无效
        """
        # 验证电机ID
        self._validate_motor_id(motor_id)

        # 应用方向系数
        position_cmd = self._apply_direction(motor_id, position)
        velocity_cmd = self._apply_direction(motor_id, velocity)
        torque_cmd = self._apply_direction(motor_id, torque)

        state, _, _ = mit_motion_control(
            self.bus, motor_id,
            position=position_cmd, velocity=velocity_cmd, torque=torque_cmd,
            kp=kp, kd=kd,
            wait_response=wait_response,
            timeout=timeout, verbose=verbose
        )
        return state

    def move_joint_position(self, motor_id: int,
                           position: float,
                           kp: float = 5.0,
                           kd: float = 0.5,
                           verbose: bool = False) -> int:
        """
        MIT 模式简化位置控制

        参数:
            motor_id (int): 电机ID (1-8)
            position (float): 目标位置 (弧度)
            kp (float): 位置增益
            kd (float): 速度增益
            verbose (bool): 是否打印详细信息

        返回:
            int: 0=成功, 1=失败
        """
        # 应用方向系数
        position_cmd = self._apply_direction(motor_id, position)

        return mit_motion_control_simple(
            self.bus, motor_id, position_cmd,
            kp=kp, kd=kd, verbose=verbose
        )

    def move_joint_velocity(self, motor_id: int,
                           velocity: float,
                           kd: float = 2.0,
                           verbose: bool = False) -> int:
        """
        MIT 模式速度控制

        参数:
            motor_id (int): 电机ID (1-8)
            velocity (float): 目标速度 (弧度/秒)
            kd (float): 速度增益
            verbose (bool): 是否打印详细信息

        返回:
            int: 0=成功, 1=失败
        """
        # 应用方向系数
        velocity_cmd = self._apply_direction(motor_id, velocity)

        return mit_velocity_control(
            self.bus, motor_id, velocity_cmd,
            kd=kd, verbose=verbose
        )

    def move_joint_torque(self, motor_id: int,
                         torque: float,
                         verbose: bool = False) -> int:
        """
        MIT 模式扭矩控制

        参数:
            motor_id (int): 电机ID (1-8)
            torque (float): 目标扭矩 (牛米)
            verbose (bool): 是否打印详细信息

        返回:
            int: 0=成功, 1=失败
        """
        # 应用方向系数
        torque_cmd = self._apply_direction(motor_id, torque)

        return mit_torque_control(
            self.bus, motor_id, torque_cmd,
            verbose=verbose
        )

    def home_joint(self, motor_id: int,
                  kp: float = 5.0,
                  kd: float = 0.5,
                  verbose: bool = False) -> int:
        """
        将电机移动到零位

        参数:
            motor_id (int): 电机ID (1-8)
            kp (float): 位置增益
            kd (float): 速度增益
            verbose (bool): 是否打印详细信息

        返回:
            int: 0=成功, 1=失败
        """
        return mit_zero_position(
            self.bus, motor_id,
            kp=kp, kd=kd, verbose=verbose
        )

    def home_all(self, kp: Union[float, List[float]] = 5.0, kd: Union[float, List[float]] = 0.5, verbose: bool = False) -> Dict[int, int]:
        """
        所有电机归零

        参数:
            kp (float or List[float]): 位置增益，可以是单个值（所有电机使用相同值）或列表（每个电机使用对应值）
            kd (float or List[float]): 速度增益，可以是单个值（所有电机使用相同值）或列表（每个电机使用对应值）
            verbose (bool): 是否打印详细信息

        返回:
            Dict[int, int]: {motor_id: state}

        示例:
            >>> # 所有电机使用相同的kp和kd值
            >>> arm.home_all(kp=5.0, kd=0.5)
            >>>
            >>> # 每个电机使用不同的kp和kd值
            >>> arm.home_all(kp=[5.0, 6.0, 7.0, 8.0, 5.0, 5.0, 5.0, 5.0],
            >>>              kd=[0.5, 0.6, 0.7, 0.8, 0.5, 0.5, 0.5, 0.5])
        """
        results = {}
        for i, motor_id in enumerate(self.motor_ids):
            # 根据kp和kd的类型获取对应的值
            kp_val = kp[i] if isinstance(kp, list) else kp
            kd_val = kd[i] if isinstance(kd, list) else kd
            results[motor_id] = self.home_joint(motor_id, kp=kp_val, kd=kd_val, verbose=verbose)
            time.sleep(0.01)
        return results

    # ==================== CSP 模式控制 ====================

    def move_joint_csp(self, motor_id: int,
                      position: float,
                      wait_response: bool = False,
                      timeout: float = 0.2,
                      verbose: bool = False) -> int:
        """
        CSP 模式位置控制

        参数:
            motor_id (int): 电机ID (1-8)
            position (float): 目标位置 (弧度)
            wait_response (bool): 是否等待响应
            timeout (float): 超时时间(秒)
            verbose (bool): 是否打印详细信息

        返回:
            int: 0=成功, 1=失败
        """
        # 应用方向系数
        position_cmd = self._apply_direction(motor_id, position)

        return csp_motion_control(
            self.bus, motor_id, position_cmd,
            wait_response=wait_response,
            timeout=timeout, verbose=verbose
        )

    def set_csp_limits(self, motor_id: Optional[int] = None,
                      speed_limit: Optional[float] = None,
                      current_limit: Optional[float] = None,
                      timeout: float = 0.2,
                      verbose: bool = False) -> int:
        """
        设置 CSP 模式的速度/电流限制

        参数:
            motor_id (int, optional): 电机ID (1-8)，如果为 None 则设置所有电机
            speed_limit (float, optional): 速度限制 (弧度/秒)
            current_limit (float, optional): 电流限制 (牛米)
            timeout (float): 超时时间(秒)
            verbose (bool): 是否打印详细信息

        返回:
            int: 0=成功, 非0=失败（单个电机）或失败次数（所有电机）

        示例:
            >>> # 设置单个电机的速度限制
            >>> arm.set_csp_limits(motor_id=5, speed_limit=10.0)
            >>>
            >>> # 设置所有电机的速度限制
            >>> arm.set_csp_limits(speed_limit=10.0)
        """
        if motor_id is not None:
            # 验证电机ID
            self._validate_motor_id(motor_id)

            # 设置单个电机
            return csp_set_speed_limits(
                self.bus, motor_id,
                speed_limit=speed_limit,
                current_limit=current_limit,
                timeout=timeout, verbose=verbose
            )
        else:
            # 设置所有电机
            failed_count = 0
            for mid in self.motor_ids:
                state = csp_set_speed_limits(
                    self.bus, mid,
                    speed_limit=speed_limit,
                    current_limit=current_limit,
                    timeout=timeout, verbose=verbose
                )
                if state != 0:
                    failed_count += 1
                time.sleep(0.01)
            return failed_count

    def move_to_csp(self, motor_id: int,
                   position: float,
                   speed_limit: Optional[float] = None,
                   current_limit: Optional[float] = None,
                   timeout: float = 1.0,
                   verbose: bool = False) -> int:
        """
        CSP 完整工作流程：设置模式、限制并移动到目标位置

        参数:
            motor_id (int): 电机ID (1-8)
            position (float): 目标位置 (弧度)
            speed_limit (float, optional): 速度限制 (弧度/秒)
            current_limit (float, optional): 电流限制 (牛米)
            timeout (float): 超时时间(秒)
            verbose (bool): 是否打印详细信息

        返回:
            int: 0=成功, 1=失败
        """
        # 应用方向系数
        position_cmd = self._apply_direction(motor_id, position)

        return csp_move_to_flowwork(
            self.bus, motor_id, position_cmd,
            speed_limit=speed_limit,
            current_limit=current_limit,
            timeout=timeout, verbose=verbose
        )

    # ==================== 零点设置 ====================

    def set_zero(self, motor_id: Optional[int] = None,
                timeout: float = 1.0,
                verbose: bool = False) -> int:
        """
        设置电机当前位置为零点

        参数:
            motor_id (int, optional): 电机ID (1-8)，如果为 None 则设置所有电机
            timeout (float): 超时时间(秒)
            verbose (bool): 是否打印详细信息

        返回:
            int: 0=成功, 非0=失败（单个电机）或失败次数（所有电机）

        示例:
            >>> # 设置单个电机零点
            >>> arm.set_zero(motor_id=5)
            >>>
            >>> # 设置所有电机零点
            >>> arm.set_zero()
        """
        if motor_id is not None:
            # 验证电机ID
            self._validate_motor_id(motor_id)

            # 设置单个电机
            return set_motor_zero(self.bus, motor_id, timeout=timeout, verbose=verbose)
        else:
            # 设置所有电机
            failed_count = 0
            for mid in self.motor_ids:
                state = set_motor_zero(self.bus, mid, timeout=timeout, verbose=verbose)
                if state != 0:
                    failed_count += 1
                time.sleep(0.01)
            return failed_count

    def set_zero_range(self, motor_id: Optional[int] = None,
                      zero_sta: int = 1,
                      timeout: float = 1.0,
                      verbose: bool = False) -> int:
        """
        设置零点表示范围

        参数:
            motor_id (int, optional): 电机ID (1-8)，如果为 None 则设置所有电机
            zero_sta (int): 0=范围 0~2π, 1=范围 -π~π，默认为1
            timeout (float): 超时时间(秒)
            verbose (bool): 是否打印详细信息

        返回:
            int: 0=成功, 非0=失败（单个电机）或失败次数（所有电机）

        示例:
            >>> # 设置单个电机零点范围为 -π~π
            >>> arm.set_zero_range(motor_id=5, zero_sta=1)
            >>>
            >>> # 设置所有电机零点范围为 -π~π
            >>> arm.set_zero_range(zero_sta=1)
        """
        if motor_id is not None:
            # 验证电机ID
            self._validate_motor_id(motor_id)

            # 设置单个电机
            return set_zero_sta_parameter(
                self.bus, motor_id, zero_sta,
                timeout=timeout, verbose=verbose
            )
        else:
            # 设置所有电机
            failed_count = 0
            for mid in self.motor_ids:
                state = set_zero_sta_parameter(
                    self.bus, mid, zero_sta,
                    timeout=timeout, verbose=verbose
                )
                if state != 0:
                    failed_count += 1
                time.sleep(0.01)
            return failed_count

    # ==================== 参数读取 ====================

    def read_parameter(self, motor_id: Optional[int] = None,
                      param_index: int = None,
                      timeout: float = 1.0,
                      verbose: bool = False) -> Union[Tuple[int, any], Dict[int, Tuple[int, any]]]:
        """
        读取电机参数

        参数:
            motor_id (int, optional): 电机ID (1-8)，如果为 None 则读取所有电机
            param_index (int): 参数索引 (如 0x7019)
            timeout (float): 超时时间(秒)
            verbose (bool): 是否打印详细信息

        返回:
            Tuple[int, any] 或 Dict[int, Tuple[int, any]]:
                单个电机: (state, value) state=0表示成功
                所有电机: {motor_id: (state, value)}

        示例:
            >>> # 读取单个电机参数
            >>> state, value = arm.read_parameter(motor_id=5, param_index=0x7019)
            >>>
            >>> # 读取所有电机参数
            >>> results = arm.read_parameter(param_index=0x7019)
        """
        if param_index is None:
            raise ValueError("param_index 参数不能为 None")

        if motor_id is not None:
            # 验证电机ID
            self._validate_motor_id(motor_id)

            # 读取单个电机
            return read_motor_parameter(
                self.bus, motor_id, param_index,
                timeout=timeout, verbose=verbose
            )
        else:
            # 读取所有电机
            results = {}
            for mid in self.motor_ids:
                results[mid] = read_motor_parameter(
                    self.bus, mid, param_index,
                    timeout=timeout, verbose=verbose
                )
                time.sleep(0.01)
            return results

    # ==================== 配置查询 ====================

    def get_motor_config(self, motor_id: Optional[int] = None) -> Union[Optional[Dict], Dict[int, Optional[Dict]]]:
        """
        获取电机配置参数

        参数:
            motor_id (int, optional): 电机ID (1-8)，如果为 None 则获取所有电机配置

        返回:
            Dict 或 Dict[int, Dict]:
                单个电机: 电机配置字典
                所有电机: {motor_id: 配置字典}

        示例:
            >>> # 获取单个电机配置
            >>> config = arm.get_motor_config(motor_id=5)
            >>>
            >>> # 获取所有电机配置
            >>> configs = arm.get_motor_config()
        """
        if motor_id is not None:
            # 验证电机ID
            self._validate_motor_id(motor_id)

            # 获取单个电机配置
            return self.config_loader.get_motor_config(motor_id)
        else:
            # 获取所有电机配置
            results = {}
            for mid in self.motor_ids:
                results[mid] = self.config_loader.get_motor_config(mid)
            return results

    def get_motor_limits(self, motor_id: Optional[int] = None) -> Union[Dict, Dict[int, Dict]]:
        """
        获取电机所有限制参数

        参数:
            motor_id (int, optional): 电机ID (1-8)，如果为 None 则获取所有电机限制

        返回:
            Dict 或 Dict[int, Dict]:
                单个电机: 包含 P_MIN, P_MAX, T_MIN, T_MAX 等限制参数
                所有电机: {motor_id: 限制参数字典}

        示例:
            >>> # 获取单个电机限制
            >>> limits = arm.get_motor_limits(motor_id=5)
            >>>
            >>> # 获取所有电机限制
            >>> all_limits = arm.get_motor_limits()
        """
        if motor_id is not None:
            # 验证电机ID
            self._validate_motor_id(motor_id)

            # 获取单个电机限制
            return self.config_loader.get_all_limits(motor_id)
        else:
            # 获取所有电机限制
            results = {}
            for mid in self.motor_ids:
                results[mid] = self.config_loader.get_all_limits(mid)
            return results

    # ==================== 资源管理 ====================

    def close(self):
        """关闭 CAN 总线连接"""
        if hasattr(self, 'bus') and self.bus is not None:
            self.bus.shutdown()
            log_output(f"[Arm] CAN 总线 {self.can_channel} 已关闭", "SUCCESS", self.log)

    def __enter__(self):
        """支持 with 语句"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持 with 语句自动关闭"""
        self.close()

    def __repr__(self):
        side_str = f", side='{self.side}'" if self.side else ""
        return f"Arm(can_channel='{self.can_channel}'{side_str}, motor_ids={self.motor_ids})"
