#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   test.py
@Time    :   2025/12/24 13:09:56
@Author  :   Wei Lindong 
@Version :   1.0
@Desc    :   None
'''

import sys
import os

# 添加 src 目录到 Python 路径
# tests/ 和 src/ 是同级目录，需要先回到父目录再进入 src
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
src_dir = os.path.join(parent_dir, 'src')
sys.path.insert(0, src_dir)

# 导入 Arm 类和异常

from openarmx_arm_driver import Robot, get_available_can_interfaces, pair_can_channels



if __name__ == "__main__":
    robot = Robot(right_can_channel='can0', left_can_channel='can1')
    print('----------------------------------------------------------------------------------------------------------')
    resutl = robot.get_all_status()
    for arm, value in resutl.items():
        print(f"{arm} 状态:")
        for motor_id, status in value.items():
            print(f"  电机 {motor_id}: {status['angle']}")