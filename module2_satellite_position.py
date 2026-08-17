import math
import pandas as pd
import os
from module1_rinex_parsing import parse_rinex_nav

# WGS-84地球引力常数（国际标准值，绝对不可修改）
GM = 3.986004418e14  # 单位：m³/s²
# GPS一周的秒数
WEEK_SECONDS = 604800.0


def compute_satellite_positions(df_nav=None, obs_time=None):
    """
    基于广播星历计算卫星在指定时刻的三维地心直角坐标(WGS-84)

    参数:
        df_nav: 模块1解析得到的星历DataFrame，为None时自动读取Excel文件
        obs_time: 观测时刻(datetime对象)，为None时默认使用星历参考时刻(toe)

    返回:
        df_pos: 包含卫星位置的DataFrame
    """
    # 输入处理
    if df_nav is None:
        # 默认读取模块1生成的清洗星历文件
        nav_path = os.path.join("module1_cleaned_nav.xlsx")
        if not os.path.exists(nav_path):
            raise FileNotFoundError(f"星历文件不存在，请先运行模块1: {nav_path}")
        df_nav = pd.read_excel(nav_path)

    sats = []
    total = len(df_nav)
    success = 0

    for idx, row in df_nav.iterrows():
        try:
            # 提取星历参数
            PRN = row["PRN"]
            sqrtA = row["sqrtA"]
            e = row["e"]
            M0 = row["M0"]
            dn = row["dn"]
            i0 = row["i0"]
            omega = row["omega"]
            Omega0 = row["Omega0"]
            toe = row["toe"]
            epoch = row["epoch"]

            # 参数完整性检查
            if any(pd.isna([sqrtA, e, M0, dn, i0, omega, Omega0, toe])):
                print(f"警告：卫星{PRN}在{epoch}的星历参数缺失，跳过")
                continue

            # ====================== 步骤1：计算时间差tk ======================
            if obs_time is None:
                # 默认使用星历参考时刻
                tk = 0.0
            else:
                # 计算观测时刻与toe的时间差（秒）
                # 注意：这里简化处理，实际应使用GPS周内秒计算
                # 完整实现需要将datetime转换为GPS周和周内秒
                delta = obs_time - epoch
                tk = delta.total_seconds()

            # GPS周跳处理：时间差超过半周时修正
            if tk > WEEK_SECONDS / 2:
                tk -= WEEK_SECONDS
            elif tk < -WEEK_SECONDS / 2:
                tk += WEEK_SECONDS

            # ====================== 步骤2：计算平均角速度 ======================
            A = sqrtA ** 2  # 轨道半长轴（m）
            n0 = math.sqrt(GM / A ** 3)  # ✅ 修正：分母加三次方
            n = n0 + dn  # 改正后的平均角速度（rad/s）

            # ====================== 步骤3：计算平近点角 ======================
            Mk = M0 + n * tk  # 观测时刻的平近点角（rad）

            # ====================== 步骤4：迭代求解开普勒方程 ======================
            Ek = Mk  # 初始值设为平近点角
            # 迭代求解，精度达到1e-12 rad时提前退出
            for _ in range(5):
                Ek_new = Mk + e * math.sin(Ek)
                if abs(Ek_new - Ek) < 1e-12:
                    break
                Ek = Ek_new

            # ====================== 步骤5：计算真近点角 ======================
            sinEk = math.sin(Ek)
            cosEk = math.cos(Ek)
            fk = math.atan2(math.sqrt(1 - e ** 2) * sinEk, cosEk - e)

            # ====================== 步骤6：计算轨道平面内坐标 ======================
            phi = fk + omega  # 升交距角（rad）
            r = A * (1 - e * cosEk)  # 卫星到地心的距离（m）

            x_orbit = r * math.cos(phi)  # 轨道平面x坐标
            y_orbit = r * math.sin(phi)  # 轨道平面y坐标

            # ====================== 步骤7：转换到WGS-84地心直角坐标系 ======================
            cosOmega = math.cos(Omega0)
            sinOmega = math.sin(Omega0)
            cosi = math.cos(i0)
            sini = math.sin(i0)

            # ✅ 修正：完整的三维坐标旋转公式
            X = x_orbit * cosOmega - y_orbit * cosi * sinOmega
            Y = x_orbit * sinOmega + y_orbit * cosi * cosOmega
            Z = y_orbit * sini

            # 存储结果
            sats.append({
                "PRN": PRN,
                "X(m)": X,
                "Y(m)": Y,
                "Z(m)": Z,
                "epoch": epoch,
                "toe": toe,
                "tk": tk
            })
            success += 1

        except Exception as e:
            print(f"错误：计算卫星{row.get('PRN', '未知')}位置失败: {str(e)}")
            continue

    # 结果整理与导出
    df_pos = pd.DataFrame(sats)
    df_pos.to_excel("module2_sat_positions.xlsx", index=False)
    print(f"模块2完成：共{total}条星历，成功计算{success}颗卫星位置")

    return df_pos


if __name__ == "__main__":
    # 自动运行完整流程：解析RINEX → 计算卫星位置
    df_nav = parse_rinex_nav()
    df_pos = compute_satellite_positions(df_nav)

    # 可选：计算指定时刻的卫星位置
    # from datetime import datetime
    # obs_time = datetime(2026, 5, 18, 12, 30, 0)
    # df_pos = compute_satellite_positions(df_nav, obs_time=obs_time)