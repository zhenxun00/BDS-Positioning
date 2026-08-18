# 🛰️ BDS Satellite Positioning System

基于北斗卫星导航系统的单点定位与连续定位实现

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

## 📋 项目简介

本项目实现了北斗卫星导航系统（BDS）的完整定位流程，从RINEX数据解析到最终的坐标输出。

### 🎯 核心功能

- ✅ **RINEX文件解析** - 支持RINEX 3.x格式导航电文
- ✅ **卫星位置计算** - 基于WGS-84坐标系的三维坐标计算
- ✅ **单点定位** - 最小二乘法实现2-5米定位精度
- ✅ **连续定位** - 多历元数据处理与轨迹绘制
- ✅ **GUI界面** - 交互式图形化操作界面

## 🚀 快速开始

### 环境要求

- Python 3.8+
- pandas
- numpy
- matplotlib (用于绘图)

### 安装

```bash
# 克隆项目
git clone https://github.com/zhenxun00/BDS-Positioning.git
cd BDS-Positioning

# 安装依赖
pip install pandas numpy matplotlib
```

### 运行

```bash
# 运行完整流程
python module5_gui.py

# 或单独运行各模块
python module1_rinex_parsing.py    # 模块1: 解析RINEX
python module2_satellite_position.py  # 模块2: 计算卫星位置
python module3_single_point.py     # 模块3: 单点定位
python module4_continuous.py       # 模块4: 连续定位
```

## 📁 项目结构

```
BDS-Positioning/
├── module1_rinex_parsing.py      # RINEX文件解析
├── module2_satellite_position.py # 卫星位置计算
├── module3_single_point.py       # 单点定位
├── module4_continuous.py         # 连续定位
├── module5_gui.py                # GUI界面
├── data/                         # 测试数据
│   └── test.rnx                 # RINEX测试文件
├── module1_cleaned_nav.xlsx      # 模块1输出
├── module2_sat_positions.xlsx    # 模块2输出
└── continuous_position_results.xlsx  # 模块4输出
```

## 🔧 核心算法

### 1. RINEX解析 (模块1)

解析RINEX 3.x格式的导航电文，提取卫星星历参数：

- 卫星编号 (PRN)
- 轨道半长轴 (a)
- 偏心率 (e)
- 平近点角 (M0)
- 升交点赤经 (Ω0)
- 轨道倾角 (i0)
- 近地点角距 (ω)

### 2. 卫星位置计算 (模块2)

基于开普勒轨道根数计算卫星在WGS-84坐标系中的三维位置：

```python
# 核心计算步骤
1. 计算时间差 tk = t - toe
2. 计算平均角速度 n = n0 + Δn
3. 计算平近点角 Mk = M0 + n·tk
4. 迭代求解开普勒方程: Ek = Mk + e·sin(Ek)
5. 计算真近点角 fk
6. 计算轨道平面坐标 (x, y)
7. 转换到WGS-84坐标系 (X, Y, Z)
```

### 3. 单点定位 (模块3)

使用伪距观测值进行最小二乘定位：

- 收集4+颗卫星的伪距观测值
- 建立观测方程并线性化
- 最小二乘求解接收机位置
- 典型精度：2-5米

## 📊 输出结果

| 模块 | 输出文件 | 内容 |
|------|----------|------|
| 模块1 | `module1_cleaned_nav.xlsx` | 清洗后的星历数据 |
| 模块2 | `module2_sat_positions.xlsx` | 卫星三维坐标 |
| 模块4 | `continuous_position_results.xlsx` | 连续定位轨迹 |

## 🛠️ 技术栈

- **Python** - 核心编程语言
- **NumPy** - 数值计算
- **Pandas** - 数据处理
- **Matplotlib** - 数据可视化
- **Tkinter** - GUI界面

## 📚 参考资料

- [RINEX 3.x Format Specification](https://www.unavco.org/data/data-support/flagship-datasets/rinex.html)
- [GPS Interface Specification (IS-GPS-200)](https://www.gps.gov/technical/icwg/)
- [WGS-84 Coordinate System](https://en.wikipedia.org/wiki/World_Geodetic_System)

## 📝 许可证

MIT License

## 👨‍🎓 作者

**周榆凯** - 北邮本科生

---

⭐ 如果这个项目对你有帮助，请给个star！
