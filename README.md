# 🛰️ 北斗定位解算全流程软件系统开发

基于北斗卫星导航系统的单点定位与连续定位实现

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

## 📋 项目简介

本项目是**电子科学与技术专业中级项目课**的实验项目，实现了北斗卫星导航系统（BDS）的完整定位解算流程。

### 🎯 实验目的

1. **理论与实践结合** - 将电路设计、信号处理等专业知识转化为可编程实践
2. **掌握核心原理** - 熟练掌握RINEX格式解析、卫星位置计算、伪距单点定位解算
3. **培养工程能力** - 模块化编程、代码规范、系统调试能力
4. **为高级项目奠基** - 软件算法与工程化基础

## 🚀 功能模块

### 模块1：RINEX数据解析 (`module1_rinex_parsing.py`)

- 解析RINEX观测文件（*.obs）与导航文件（*.nav）
- 提取卫星编号、伪距观测值、信噪比、广播星历参数
- 数据预处理：剔除不健康卫星、无效观测值
- 伪距粗差初步剔除
- 按高度角筛选可见卫星
- 同一历元多卫星数据时间对齐

### 模块2：卫星位置与钟差计算 (`module2_satellite_position.py`)

- 基于广播星历计算北斗卫星在轨位置（ECEF坐标系）
- 轨道摄动修正，输出卫星X/Y/Z坐标
- 卫星钟差修正（多项式修正+相对论效应修正）
- 传播延迟修正：
  - Saastamoinen模型（对流层延迟）
  - 简化模型（电离层延迟）
- 输出最终修正后的伪距

### 模块3：单点定位解算核心算法 (`module3_single_point.py`)

- 筛选历元内可见卫星集合
- 计算PDOP、GDOP等几何精度因子
- 构建伪距定位观测方程
- **迭代最小二乘算法**求解用户位置（ECEF坐标系）
- 用户钟差计算
- ECEF坐标系与经纬高（BLH）坐标系转换
- 输出标准定位结果（经度、纬度、高程）

### 模块4：连续定位与结果分析 (`module4_continuous.py`)

- 逐历元循环解算，多历元连续定位
- 输出用户连续定位轨迹
- 存储定位结果时间序列
- 定位精度评估：
  - RMS误差
  - 均值误差
  - 最大误差
- 卫星数量、DOP值与定位精度关系分析
- 结果可视化：
  - 定位误差曲线
  - 经纬度轨迹图
  - 卫星可见数与DOP值变化曲线

### 模块5：软件系统整合与测试 (`module5_gui.py`)

- 模块化架构设计
- 完整软件系统：数据输入→预处理→解算→分析→输出
- **PyQt GUI界面**：
  - RINEX数据导入
  - 解算参数设置（迭代次数、误差阈值）
  - 定位结果实时显示
  - 定位轨迹回放
  - 误差曲线查看

## 📊 核心算法

### 1. 卫星位置计算

基于开普勒轨道根数的WGS-84坐标计算：

```
1. 计算时间差 tk = t - toe
2. 计算平均角速度 n = n0 + Δn
3. 计算平近点角 Mk = M0 + n·tk
4. 迭代求解开普勒方程: Ek = Mk + e·sin(Ek)
5. 计算真近点角 fk
6. 计算轨道平面坐标 (x, y)
7. 转换到WGS-84坐标系 (X, Y, Z)
```

### 2. 单点定位算法

基于最小二乘法的伪距定位：

```
1. 收集4+颗卫星的伪距观测值
2. 建立观测方程并线性化
3. 最小二乘求解: X = (A^T·A)^(-1)·A^T·L
4. 迭代优化提高精度
5. 输出经度、纬度、高程
```

### 3. 误差修正

- **对流层延迟**: Saastamoinen模型
- **电离层延迟**: 简化模型
- **卫星钟差**: 多项式修正 + 相对论效应

## 📁 项目结构

```
BDS-Positioning/
├── module1_rinex_parsing.py      # 模块1: RINEX数据解析
├── module2_satellite_position.py # 模块2: 卫星位置计算
├── module3_single_point.py       # 模块3: 单点定位解算
├── module4_continuous.py         # 模块4: 连续定位与分析
├── module5_gui.py                # 模块5: GUI界面
├── data/
│   └── test.rnx                  # 测试数据
├── module1_cleaned_nav.xlsx      # 模块1输出：清洗后的星历
├── module2_sat_positions.xlsx    # 模块2输出：卫星位置
└── continuous_position_results.xlsx  # 模块4输出：连续定位结果
```

## 🛠️ 技术栈

- **Python 3.8+** - 核心编程语言
- **NumPy** - 数值计算
- **Pandas** - 数据处理
- **Matplotlib** - 数据可视化
- **PyQt5** - GUI界面

## 🚀 快速开始

```bash
# 克隆项目
git clone https://github.com/zhenxun00/BDS-Positioning.git
cd BDS-Positioning

# 安装依赖
pip install pandas numpy matplotlib pyqt5

# 运行GUI界面
python module5_gui.py

# 或单独运行各模块
python module1_rinex_parsing.py
python module2_satellite_position.py
python module3_single_point.py
python module4_continuous.py
```

## 📈 测试结果

| 模块 | 功能 | 输出 |
|------|------|------|
| 模块1 | RINEX解析 | `module1_cleaned_nav.xlsx` |
| 模块2 | 卫星位置计算 | `module2_sat_positions.xlsx` |
| 模块3 | 单点定位 | 经度、纬度、高程 |
| 模块4 | 连续定位 | `continuous_position_results.xlsx` |
| 模块5 | GUI界面 | 可视化交互界面 |

## 📚 参考资料

- 《北斗卫星导航定位原理与方法》- 科学出版社
- RINEX格式规范
- 北斗卫星导航系统接口控制文件（ICD）
- GPS Interface Specification (IS-GPS-200)

## 👨‍🎓 作者

**周榆凯** - 电子科学与技术专业
- 学号：2024210611
- 北京邮电大学

## 📝 许可证

MIT License

---

⭐ 如果这个项目对你有帮助，请给个star！
