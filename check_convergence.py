# 设置收敛标准，根据你的计算需要调整这些值
from pathlib import Path
import re
def get_converge(incar: Path ='./INCAR'):
    with open(incar, "r") as incar_file:
        lines =  incar_file.readlines()
    for line in lines:
        if re.search('EDIFF', line):
            EDIFF = float(line.split()[2])
        elif re.search('EDIFFG', line):
            EDIFFG = float(line.split()[2])
    return EDIFF, EDIFFG

# with open(("./INCAR"), 'r') as f:
#     print(f.readlines()[3])
print(get_converge("./INCAR"))
# energy_convergence = 1e-5  # 能量收敛标准
# position_conv erg ence = 0.01  # 原子位置收敛标准
# force_convergence = 0.01  # 力收敛标准
#
# # 打开 OUTCAR 文件
# with open("OUTCAR", "r") as outcar_file:
#     lines = outcar_file.readlines()
#
# # 寻找最后一步的信息
# for i in range(len(lines) - 1, 0, -1):
#     line = lines[i].strip()
#     if "energy without entropy=" in line:
#         energy_line = line
#         break
#
# for i in range(len(lines) - 1, 0, -1):
#     line = lines[i].strip()
#     if "POSITION" in line:
#         position_lines = lines[i:]
#         break
#
# for i in range(len(lines) - 1, 0, -1):
#     line = lines[i].strip()
#     if "FORCES:" in line:
#         force_lines = lines[i:]
#         break
#
# # 提取能量值
# energy = float(energy_line.split("=")[1].split()[0])
#
# # 检查原子位置变化是否满足收敛标准
# positions_converged = all(float(line.split()[-1]) < position_convergence for line in position_lines[1:])
#
# # 检查力是否满足收敛标准
# forces_converged = all(float(line.split()[-1]) < force_convergence for line in force_lines[1:])
#
# # 判断结构优化是否结束
# if energy < energy_convergence and positions_converged and forces_converged:
#     print("结构优化已经结束。")
# else:
#     print("结构优化尚未结束。")
#
