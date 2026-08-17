import math
import numpy as np
import random
import pandas as pd
import os

# ====================== 全局常量定义 ======================
CLIGHT = 299792458.0  # 真空中光速，单位：m/s
a = 6378137.0  # WGS-84椭球长半轴，单位：m
f = 1 / 298.257223563  # WGS-84椭球扁率
e2 = 2 * f - f ** 2  # WGS-84椭球第一偏心率平方

# 测站真实大地坐标（北邮沙河校区实验专用精确坐标）
B_TRUE, L_TRUE, H_TRUE = 40.1575, 116.2885, 35.0
# 转换为地心直角坐标
B0, L0 = math.radians(B_TRUE), math.radians(L_TRUE)
N0 = a / math.sqrt(1 - e2 * math.sin(B0) ** 2)
X0 = (N0 + H_TRUE) * math.cos(B0) * math.cos(L0)
Y0 = (N0 + H_TRUE) * math.cos(B0) * math.sin(L0)
Z0 = (N0 * (1 - e2) + H_TRUE) * math.sin(B0)

# 固定随机种子保证结果可复现
random.seed(2026)
np.random.seed(2026)


# ====================== 坐标转换函数 ======================
def ecef2blh(X, Y, Z):
    """地心直角坐标(ECEF)转大地坐标(BLH)"""
    lon = math.atan2(Y, X)
    p = math.sqrt(X ** 2 + Y ** 2)
    lat = math.atan2(Z, p * (1 - e2))
    # 迭代求解纬度和高程（5次迭代达毫米级精度）
    for _ in range(5):
        N = a / math.sqrt(1 - e2 * math.sin(lat) ** 2)
        h = p / math.cos(lat) - N
        lat = math.atan2(Z + e2 * N * math.sin(lat), p)
    return math.degrees(lat), math.degrees(lon), h


# ====================== 北斗B1I标准伪距误差模拟 ======================
def simulate_bds_b1i_error(rho, epoch=0):
    """
    模拟北斗B1I频段的真实伪距误差（单位：米）
    符合北斗公开服务性能规范的误差量级

    参数:
        rho: 卫星到测站的几何距离真值（米）
        epoch: 历元序号（从0开始），用于模拟接收机钟差漂移

    返回:
        P: 包含所有误差的伪距观测值（米）
    """
    # 1. 接收机钟差（缓慢线性漂移+高频噪声，最主要误差源之一）
    # 基准偏移110m（约367ns）+ 每历元漂移0.15m + 8m标准差噪声
    delta_clock = 110.0 + epoch * 0.15 + random.gauss(0, 8)

    # 2. 电离层延迟（白天典型值5-15m，夜间2-8m）
    # 均值9m，标准差2.5m，符合中纬度地区白天电离层特性
    delta_iono = random.gauss(9.0, 2.5)

    # 3. 对流层延迟（天顶方向典型值2-6m）
    # 均值4.5m，标准差1.2m，符合标准大气模型
    delta_trop = random.gauss(4.5, 1.2)

    # 4. 观测噪声（接收机热噪声+多路径效应）
    # 北斗B1I伪距观测噪声典型值0.2-0.5m
    delta_noise = random.gauss(0, 0.3)

    # 合成最终伪距观测值
    P = rho + delta_clock + delta_iono + delta_trop + delta_noise
    return P


# ====================== 单历元最小二乘单点定位 ======================
def single_epoch_position(sat_df, epoch=0):
    """
    单历元最小二乘单点定位算法

    参数:
        sat_df: 包含卫星位置的DataFrame
        epoch: 历元序号（用于模拟钟差漂移）

    返回:
        成功：(x, y, z, dt_rcv, err_3D) 地心坐标、钟差、3D误差
        失败：None
    """
    # 提取所有卫星的三维位置
    sat_pos = [[row["X(m)"], row["Y(m)"], row["Z(m)"]] for _, row in sat_df.iterrows()]
    P_list = []

    # 模拟带真实误差的伪距观测值
    for Xs, Ys, Zs in sat_pos:
        rho = math.sqrt((Xs - X0) ** 2 + (Ys - Y0) ** 2 + (Zs - Z0) ** 2)
        P = simulate_bds_b1i_error(rho, epoch=epoch)
        P_list.append(P)

    # 迭代初始化（标准初始值：地心+零钟差）
    x = y = z = dt_rcv = 0.0
    max_iter = 30
    min_iter = 3  # 优化：从15改为3，符合实际工程收敛速度
    tol = 1e-9

    # 最小二乘迭代求解
    for it in range(max_iter):
        G = []  # 设计矩阵
        b = []  # 残差向量

        for i, (Xs, Ys, Zs) in enumerate(sat_pos):
            rho_calc = math.sqrt((Xs - x) ** 2 + (Ys - y) ** 2 + (Zs - z) ** 2)
            bi = P_list[i] - rho_calc - CLIGHT * dt_rcv

            # 构造方向余弦
            G.append([
                -(Xs - x) / rho_calc,
                -(Ys - y) / rho_calc,
                -(Zs - z) / rho_calc,
                CLIGHT
            ])
            b.append(bi)

        # 求解最小二乘解
        try:
            G_mat = np.array(G)
            b_mat = np.array(b)
            delta = np.linalg.inv(G_mat.T @ G_mat) @ G_mat.T @ b_mat
        except np.linalg.LinAlgError:
            # 矩阵奇异（卫星数<4或几何构型极差）
            return None

        # 更新估计值
        x += delta[0]
        y += delta[1]
        z += delta[2]
        dt_rcv += delta[3]

        # 收敛判断
        if it >= min_iter and np.linalg.norm(delta) < tol:
            break

    # 计算3D定位误差
    err_3D = math.sqrt((x - X0) ** 2 + (y - Y0) ** 2 + (z - Z0) ** 2)
    return x, y, z, dt_rcv, err_3D


# ====================== 主程序入口 ======================
if __name__ == "__main__":
    # 读取模块2生成的卫星位置文件
    file_path = os.path.join("module2_sat_positions.xlsx")
    if not os.path.exists(file_path):
        print("错误：卫星位置文件不存在，请先运行模块2")
        exit(1)

    df = pd.read_excel(file_path)

    # 获取所有唯一历元
    epochs = df["epoch"].unique()
    print(f"共读取到 {len(epochs)} 个历元的卫星数据")

    # 处理每个历元并输出结果
    for epoch_idx, epoch_time in enumerate(epochs):
        df_epoch = df[df["epoch"] == epoch_time]
        sat_count = len(df_epoch)

        if sat_count < 4:
            print(f"\n历元 {epoch_idx} ({epoch_time}): 卫星数不足4颗({sat_count}颗)，无法定位")
            continue

        pos = single_epoch_position(df_epoch, epoch=epoch_idx)
        if pos:
            x, y, z, dt, err = pos
            lat, lon, h = ecef2blh(x, y, z)

            print(f"\n===== 历元 {epoch_idx} 定位结果 =====")
            print(f"时间: {epoch_time}")
            print(f"可见卫星数: {sat_count}")
            print(f"纬度: {lat:.6f}° (真值: {B_TRUE:.6f}°)")
            print(f"经度: {lon:.6f}° (真值: {L_TRUE:.6f}°)")
            print(f"高程: {h:.3f} m (真值: {H_TRUE:.3f} m)")
            print(f"3D定位误差: {err:.3f} m")
            print(f"接收机钟差: {dt * 1e9:.3f} ns")
        else:
            print(f"\n历元 {epoch_idx} ({epoch_time}): 定位失败")