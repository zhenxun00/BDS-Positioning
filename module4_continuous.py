import pandas as pd
import matplotlib

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np
import os
from module3_single_point import single_epoch_position, ecef2blh

# ---------------- 中文字体设置 ----------------
plt.rcParams['font.sans-serif'] = ['SimHei']  # 中文显示
plt.rcParams['axes.unicode_minus'] = False  # 负号正常显示


# ---------------- PDOP计算 ----------------
def compute_pdop(sat_df):
    sat_pos = [[row["X(m)"], row["Y(m)"], row["Z(m)"]] for _, row in sat_df.iterrows()]
    x = y = z = 0.0
    G = []
    for Xs, Ys, Zs in sat_pos:
        rho = np.sqrt((Xs - x) ** 2 + (Ys - y) ** 2 + (Zs - z) ** 2)
        G.append([-(Xs - x) / rho, -(Ys - y) / rho, -(Zs - z) / rho, 1.0])
    G = np.array(G)
    try:
        Q = np.linalg.inv(G.T @ G)
        PDOP = np.sqrt(np.trace(Q[0:3, 0:3]))
    except:
        PDOP = np.nan
    return PDOP


# ---------------- 连续定位 ----------------
def continuous_positioning_with_reference(df_sat=None):
    if df_sat is None:
        df_sat = pd.read_excel(os.path.join("module2_sat_positions.xlsx"))

    df_sat["epoch"] = pd.to_datetime(df_sat["epoch"])
    epochs = df_sat["epoch"].unique()
    results = []

    # ---------------- 北邮沙河校区参考点 ----------------
    ref_lat = 40.1575
    ref_lon = 116.2885
    ref_h = 35

    for t in epochs:
        df_epoch = df_sat[df_sat["epoch"] == t]
        if len(df_epoch) < 4:
            continue
        pos = single_epoch_position(df_epoch)
        if not pos:
            continue
        x, y, z, _, err3d = pos
        lat, lon, h = ecef2blh(x, y, z)  # 转 WGS84
        visible_sat = len(df_epoch)
        pdop = compute_pdop(df_epoch)
        results.append({
            "epoch": t,
            "纬度": lat,
            "经度": lon,
            "高程": h,
            "3D误差": err3d,
            "卫星数": visible_sat,
            "PDOP": pdop
        })

    df_out = pd.DataFrame(results)
    df_out.to_excel("continuous_position_results.xlsx", index=False)

    # 平滑轨迹和平滑PDOP
    df_out["纬度_smooth"] = df_out["纬度"].rolling(5, min_periods=1).mean()
    df_out["经度_smooth"] = df_out["经度"].rolling(5, min_periods=1).mean()
    df_out["PDOP_smooth"] = df_out["PDOP"].rolling(5, min_periods=1).mean()

    # ---------------- 图1：轨迹 ----------------
    plt.figure(figsize=(10, 8))

    # 使用平滑后的经纬度绘图，避免数据挤在一起
    plt.plot(df_out["经度_smooth"], df_out["纬度_smooth"], 'b.-', label="平滑轨迹", linewidth=2)
    plt.plot(df_out["经度"], df_out["纬度"], 'r.-', alpha=0.4, label="原始轨迹", linewidth=1)

    # 起点/终点
    plt.scatter(df_out["经度"].iloc[0], df_out["纬度"].iloc[0], c='g', s=120, marker='o', edgecolors='k', label='起点')
    plt.scatter(df_out["经度"].iloc[-1], df_out["纬度"].iloc[-1], c='k', s=120, marker='X', label='终点')

    # 北邮参考点（更醒目）
    plt.scatter(ref_lon, ref_lat, c='purple', s=200, marker='*', edgecolors='gold', linewidth=2,
                label='北邮沙河校区(真值)')

    # ✅ 修复：计算显示范围时同时考虑参考点
    all_lons = np.concatenate([df_out["经度"], [ref_lon]])
    all_lats = np.concatenate([df_out["纬度"], [ref_lat]])

    lon_margin = (all_lons.max() - all_lons.min()) * 0.2  # 增加边距到20%
    lat_margin = (all_lats.max() - all_lats.min()) * 0.2

    plt.xlim(all_lons.min() - lon_margin, all_lons.max() + lon_margin)
    plt.ylim(all_lats.min() - lat_margin, all_lats.max() + lat_margin)

    # ✅ 关闭科学计数法，显示完整经纬度
    plt.gca().xaxis.set_major_formatter(plt.FormatStrFormatter('%.6f'))
    plt.gca().yaxis.set_major_formatter(plt.FormatStrFormatter('%.6f'))

    plt.xlabel("经度(°)", fontsize=12)
    plt.ylabel("纬度(°)", fontsize=12)
    plt.title("北斗三连续定位轨迹与真实位置对比", fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.7)

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show(block=True)

    # ---------------- 图2：3D误差 ----------------
    plt.figure(figsize=(10, 6))
    plt.plot(df_out["epoch"], df_out["3D误差"], 'b.-', label="3D误差", linewidth=1.5)
    plt.axhline(y=1, color='gray', linestyle='--', label="1米参考线")
    plt.axhline(y=5, color='gray', linestyle='-.', label="5米参考线")
    plt.axhline(y=df_out["3D误差"].mean(), color='purple', linestyle=':', linewidth=2,
                label=f"平均误差: {df_out['3D误差'].mean():.2f}m")
    plt.xlabel("时间", fontsize=12)
    plt.ylabel("3D定位误差 (米)", fontsize=12)
    plt.title("3D定位误差随时间变化", fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show(block=True)

    # ---------------- 图3：卫星数 + PDOP ----------------
    plt.figure(figsize=(10, 6))
    ax1 = plt.gca()
    ax1.plot(df_out["epoch"], df_out["卫星数"], 'g.-', label="可见卫星数", linewidth=1.5)
    ax1.set_ylabel("可见卫星数", color='g', fontsize=12)
    ax1.set_xlabel("时间", fontsize=12)
    ax1.tick_params(axis='y', labelcolor='g')

    ax2 = ax1.twinx()
    ax2.plot(df_out["epoch"], df_out["PDOP_smooth"], 'r.-', label="PDOP(平滑)", linewidth=1.5)
    ax2.set_ylabel("PDOP", color='r', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='r')

    plt.title("可见卫星数与PDOP变化", fontsize=14, fontweight='bold')
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.legend(loc="upper left", fontsize=11)
    ax2.legend(loc="upper right", fontsize=11)

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show(block=True)

    # ---------------- 统计信息输出 ----------------
    print("=" * 60)
    print("北斗B1I连续定位结果统计")
    print("=" * 60)
    print(f"总有效历元数: {len(df_out)}")
    print(f"平均3D误差: {df_out['3D误差'].mean():.3f} m")
    print(f"3D误差RMS: {np.sqrt(np.mean(df_out['3D误差'] ** 2)):.3f} m")
    print(f"最大3D误差: {df_out['3D误差'].max():.3f} m")
    print(f"最小3D误差: {df_out['3D误差'].min():.3f} m")
    print(f"平均可见卫星数: {df_out['卫星数'].mean():.1f} 颗")
    print(f"平均PDOP: {df_out['PDOP'].mean():.3f}")
    print(
        f"平均平面偏移: {np.sqrt((df_out['经度'].mean() - ref_lon) ** 2 + (df_out['纬度'].mean() - ref_lat) ** 2) * 111000:.3f} m")
    print(f"平均高程偏移: {abs(df_out['高程'].mean() - ref_h):.3f} m")
    print("=" * 60)

    return df_out


if __name__ == "__main__":
    continuous_positioning_with_reference()