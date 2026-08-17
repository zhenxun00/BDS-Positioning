# BDS Positioning - 北斗卫星导航系统定位

基于北斗卫星导航系统的单点定位与连续定位实现。

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)
![Status](https://img.shields.io/badge/Status-Completed-green?style=for-the-badge)

## 📋 项目简介

本项目实现了北斗卫星导航系统（BDS）的完整定位流程，包括：

1. **RINEX文件解析** - 解析北斗导航电文数据
2. **卫星位置计算** - 基于广播星历计算卫星三维坐标
3. **单点定位** - 使用最小二乘法进行单次定位
4. **连续定位** - 多历元连续定位与轨迹绘制
5. **GUI界面** - 可视化交互界面

## 🚀 功能模块

### 模块1: RINEX文件解析 (`module1_rinex_parsing.py`)
- 解析RINEX 3.x格式导航电文
- 提取卫星星历参数（轨道根数、时间参数等）
- 数据清洗与Excel导出

### 模块2: 卫星位置计算 (`module2_satellite_position.py`)
- 基于WGS-84坐标系
- 实现完整的卫星位置计算算法：
  - 平均角速度计算
  - 平近点角计算
  - 开普勒方程迭代求解
  - 真近点角计算
  - 轨道平面坐标计算
  - WGS-84坐标转换

### 模块3: 单点定位 (`module3_single_point.py`)
- 最小二乘法定位算法
- 误差方程建立与求解
- 接收机位置解算

### 模块4: 连续定位 (`module4_continuous.py`)
- 多历元数据处理
- 定位结果轨迹绘制
- 精度评估分析

### 模块5: GUI界面 (`module5_gui.py`)
- 图形化用户界面
- 实时定位显示
- 结果可视化

## 📁 项目结构

```
BDS-Positioning/
├── module1_rinex_parsing.py      # RINEX文件解析
├── module2_satellite_position.py # 卫星位置计算
├── module3_single_point.py       # 单点定位
├── module4_continuous.py         # 连续定位
├── module5_gui.py                # GUI界面
├── data/                         # RINEX数据文件
│   └── test.rnx
├── module1_cleaned_nav.xlsx      # 模块1输出：清洗后的星历数据
├── module2_sat_positions.xlsx    # 模块2输出：卫星位置数据
└── continuous_position_results.xlsx # 模块4输出：连续定位结果
```

## 🛠️ 环境要求

- Python 3.8+
- pandas
- numpy
- matplotlib (用于绘图)
- tkinter (GUI界面)

## 📊 算法说明

### 卫星位置计算核心算法

```
1. 计算时间差 tk
2. 计算平均角速度 n = n0 + Δn
3. 计算平近点角 Mk = M0 + n·tk
4. 迭代求解开普勒方程 Ek = Mk + e·sin(Ek)
5. 计算真近点角 fk
6. 计算轨道平面坐标 (x, y)
7. 转换到WGS-84坐标系 (X, Y, Z)
```

### 定位算法

```
1. 建立误差方程 V = A·X - L
2. 最小二乘求解 X = (A^T·A)^(-1)·A^T·L
3. 迭代直到收敛
```

## 📈 运行结果

### 模块1输出
- 成功解析卫星星历数据
- 输出 `module1_cleaned_nav.xlsx`

### 模块2输出
- 计算所有卫星三维坐标
- 输出 `module2_sat_positions.xlsx`

### 模块4输出
- 连续定位轨迹图
- 定位精度分析

## 👨‍🎓 作者

**周榆凯** - 2024210611

## 📝 实验报告

详细的实验报告和实验数据见 `周榆凯2024210611中级项目课实验报告.docx`

## 📄 License

MIT License
