#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   test_one_motor_CSP.py
@Time    :   2025/12/24
@Author  :   Wei Lindong
@Version :   1.0
@Desc    :   测试单电机 CSP 模式控制
             CSP (Cyclic Synchronous Position) 模式是一种位置控制模式
             特点：平滑轨迹、可设置速度/电流限制
'''

import sys
import os
import time

# 添加 src 目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
src_dir = os.path.join(parent_dir, 'src')
sys.path.insert(0, src_dir)

from openarmx_arm_driver import Robot




if __name__ == "__main__":
    print("="*60)
    print("测试单电机")
    print("="*60)

    side = 'right'  # 测试电机所在机械臂侧 'right' 或 'left'
    motor_id = 1
    position = 0.3  # 电机运动目标位置

    # Robot 会自动检测并启用 CAN 接口
    # 如果 can0 或 can1 未启用，会自动尝试启用
    with Robot(right_can_channel='can0', left_can_channel='can1') as robot:

        # 设置为 MIT 模式
        robot.set_mode_all('csp')

        # 使能所有电机
        robot.enable_all()

        robot.set_csp_limits_all(speed_limit=1.0)

        # 单电机运动
        robot.move_one_joint_csp(arm=side, 
                                 motor_id=motor_id, 
                                 position=0.3)
        time.sleep(3)

        # 回到零位
        robot.move_one_joint_csp(arm=side, 
                                 motor_id=motor_id, 
                                 position=0.0)
        time.sleep(2)

        # 停止所有电机
        robot.disable_all()

        robot.shutdown()
