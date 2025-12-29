# OpenArmX Driver

> **Developed by Chengdu Changshu Robotics Co., Ltd.**

Python SDK for OpenArmX robotic arm control via CAN bus. 

## Installation

```bash
pip install openarmx-driver
```

## Quick Start

### Single Arm Control

```python
from openarmx_driver import Arm

# Create right arm instance
arm = Arm('can0', side='right')

# Enable motors
arm.enable_all()

# Set to MIT mode
arm.set_mode('mit')

# Move joint
arm.move_joint_mit(motor_id=1, position=0.5, kp=10.0, kd=1.0)

# Check status
arm.show_motor_status()

# Stop
arm.disable_all()
```

### Dual Arm Control

```python
from openarmx_driver import Robot

# Create dual-arm robot
robot = Robot(left_can_channel='can0', right_can_channel='can1')

# Enable all motors
robot.enable_all()

# Set mode
robot.set_mode_all('mit')

# Symmetrical motion of left and right arms
robot.move_joints_mit(
    left_positions=[0.1, 0.2, 0.3, 0, 0, 0, 0],
    right_positions=[0.1, 0.2, 0.3, 0, 0, 0, 0],
    kp=10.0, kd=1.0
)

# Check status
robot.show_all_status()

# Stop
robot.disable_all()
```

## Supported Control Modes

- **MIT Mode**: Hybrid position/velocity/torque control (with PD gains)


## License

This project is licensed under the OpenArmX Research and Education License.
Commercial use requires a separate license.

---

## 📞 Contact Us

### Chengdu Changshu Robotics Co., Ltd.

| Contact | Information |
|---------|-------------|
| 📧 Email | openarmrobot@gmail.com |
| 📱 Phone/WeChat | +86-17746530375 |
| 🌐 Website | https://openarmx.com/ |
| 📍 Address | No.11 Xinye 8th Street, West Zone, Tianjin Economic-Technological Development Area, Huacheng Machinery Factory |
| 👤 Contact Person | Mr. Wang |

---

**Copyright © 2025 Chengdu Changshu Robotics Co., Ltd. All Rights Reserved.**
