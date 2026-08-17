import sys, os
import pandas as pd
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QFileDialog, QGridLayout, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# 导入前面四个模块的核心函数
from module1_rinex_parsing import parse_rinex_nav
from module2_satellite_position import compute_satellite_positions
from module3_single_point import single_epoch_position, ecef2blh
from module4_continuous import compute_pdop

# ✅ 修复1：全局设置Matplotlib中文显示（解决PyQt嵌入图表中文方块问题）
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


# ---------------- 后台计算线程 ----------------
class ContinuousThread(QThread):
    finished = pyqtSignal(pd.DataFrame)

    def __init__(self, df_sat):
        super().__init__()
        self.df_sat = df_sat

    def run(self):
        df_sat = self.df_sat.copy()
        df_sat["epoch"] = pd.to_datetime(df_sat["epoch"])
        results = []

        # 北邮沙河校区实验专用精确坐标
        ref_lat, ref_lon = 40.1575, 116.2885

        for t in df_sat["epoch"].unique():
            df_epoch = df_sat[df_sat["epoch"] == t]
            if len(df_epoch) < 4: continue
            pos = single_epoch_position(df_epoch)
            if not pos: continue
            x, y, z, _, err3d = pos
            lat, lon, h = ecef2blh(x, y, z)
            results.append({
                "epoch": t,
                "纬度": lat,
                "经度": lon,
                "高程": h,
                "3D误差": err3d,
                "卫星数": len(df_epoch),
                "PDOP": compute_pdop(df_epoch)
            })

        df_out = pd.DataFrame(results)
        df_out["纬度_smooth"] = df_out["纬度"].rolling(5, min_periods=1).mean()
        df_out["经度_smooth"] = df_out["经度"].rolling(5, min_periods=1).mean()
        df_out["PDOP_smooth"] = df_out["PDOP"].rolling(5, min_periods=1).mean()

        self.finished.emit(df_out)


# ---------------- GUI ----------------
class BeidouGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("北斗定位解算系统")
        self.setGeometry(100, 100, 1200, 700)

        layout = QGridLayout()
        self.setLayout(layout)

        # ---------------- 标签 ----------------
        self.label = QLabel("请选择RINEX导航文件")
        layout.addWidget(self.label, 0, 0, 1, 3)

        # ---------------- 按钮 ----------------
        self.btn_load = QPushButton("导入RINEX文件")
        self.btn_load.clicked.connect(self.load_file)
        layout.addWidget(self.btn_load, 1, 0)

        self.btn_single = QPushButton("单点定位")
        self.btn_single.clicked.connect(self.run_single)
        layout.addWidget(self.btn_single, 1, 1)

        self.btn_continuous = QPushButton("连续定位")
        self.btn_continuous.clicked.connect(self.run_continuous)
        layout.addWidget(self.btn_continuous, 1, 2)

        # ---------------- 三个绘图画布 ----------------
        self.canvas_trajectory = FigureCanvas(Figure(figsize=(5, 4)))
        self.canvas_error = FigureCanvas(Figure(figsize=(5, 4)))
        self.canvas_pdop = FigureCanvas(Figure(figsize=(5, 4)))

        layout.addWidget(self.canvas_trajectory, 2, 0)
        layout.addWidget(self.canvas_error, 2, 1)
        layout.addWidget(self.canvas_pdop, 2, 2)

        # 默认文件
        self.rinex_file = os.path.join("data", "test.rnx")
        self.thread = None

    def load_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "选择RINEX导航文件", "", "RINEX Files (*.rnx *.nav *.cmb)")
        if file:
            self.rinex_file = file
            self.label.setText(f"已选择文件: {file}")

    def run_single(self):
        try:
            df_nav = parse_rinex_nav(self.rinex_file)
            df_pos = compute_satellite_positions(df_nav)
            df_epoch = df_pos[df_pos["epoch"] == df_pos["epoch"].iloc[0]]
            pos = single_epoch_position(df_epoch)
            if pos:
                x, y, z, _, err = pos
                lat, lon, h = ecef2blh(x, y, z)
                QMessageBox.information(self, "单点定位结果",
                                        f"纬度:{lat:.6f}\n经度:{lon:.6f}\n高程:{h:.3f} m\n3D误差:{err:.3f} m")
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))

    def run_continuous(self):
        try:
            df_nav = parse_rinex_nav(self.rinex_file)
            df_pos = compute_satellite_positions(df_nav)
            self.btn_continuous.setEnabled(False)
            self.label.setText("正在进行连续定位，请稍候...")

            self.thread = ContinuousThread(df_pos)
            self.thread.finished.connect(self.update_charts)
            self.thread.start()
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))
            self.btn_continuous.setEnabled(True)

    def update_charts(self, df_out):
        try:
            # ---------- 轨迹 ----------
            ax = self.canvas_trajectory.figure.subplots()
            ax.clear()
            ax.plot(df_out["经度_smooth"], df_out["纬度_smooth"], 'b.-', label="平滑轨迹")
            ax.plot(df_out["经度"], df_out["纬度"], 'r.-', alpha=0.5, label="原始轨迹")
            ax.scatter(df_out["经度"].iloc[0], df_out["纬度"].iloc[0], c='g', s=80, marker='o', label='起点')
            ax.scatter(df_out["经度"].iloc[-1], df_out["纬度"].iloc[-1], c='k', s=80, marker='X', label='终点')
            # ✅ 修复2：统一参考点坐标
            ax.scatter(116.2885, 40.1575, c='purple', s=120, marker='*', label='北邮沙河校区(真值)')

            lon_margin = (df_out["经度"].max() - df_out["经度"].min()) * 0.1
            lat_margin = (df_out["纬度"].max() - df_out["纬度"].min()) * 0.1
            ax.set_xlim(df_out["经度"].min() - lon_margin, df_out["经度"].max() + lon_margin)
            ax.set_ylim(df_out["纬度"].min() - lat_margin, df_out["纬度"].max() + lat_margin)

            # ✅ 修复3：关闭科学计数法，显示完整6位小数经纬度
            ax.xaxis.set_major_formatter(plt.FormatStrFormatter('%.6f'))
            ax.yaxis.set_major_formatter(plt.FormatStrFormatter('%.6f'))

            ax.set_xlabel("经度(°)");
            ax.set_ylabel("纬度(°)")
            ax.set_title("连续定位轨迹")
            ax.grid(True)
            ax.legend()
            self.canvas_trajectory.draw()

            # ---------- 3D误差 ----------
            ax = self.canvas_error.figure.subplots()
            ax.clear()
            ax.plot(df_out["epoch"], df_out["3D误差"], 'b.-', label="3D误差")
            ax.axhline(1, color='gray', linestyle='--', label="1米参考线")
            ax.axhline(2, color='gray', linestyle='-.', label="2米参考线")
            ax.axhline(df_out["3D误差"].mean(), color='purple', linestyle=':', label="平均误差")
            ax.set_xlabel("历元");
            ax.set_ylabel("3D误差 (米)")
            ax.set_title("3D误差随时间变化")
            ax.grid(True)
            ax.legend()
            self.canvas_error.draw()

            # ---------- 卫星数 + PDOP ----------
            ax1 = self.canvas_pdop.figure.subplots()
            ax1.clear()
            ax1.plot(df_out["epoch"], df_out["卫星数"], 'g.-', label="卫星数")
            ax1.set_xlabel("历元");
            ax1.set_ylabel("卫星数", color='g')
            ax2 = ax1.twinx()
            ax2.plot(df_out["epoch"], df_out["PDOP_smooth"], 'r.-', label="PDOP(平滑)")
            ax2.set_ylabel("PDOP", color='r')
            ax1.set_title("卫星数与PDOP变化")
            ax1.grid(True)
            ax1.legend(loc="upper left")
            ax2.legend(loc="upper right")
            self.canvas_pdop.draw()
        finally:
            self.btn_continuous.setEnabled(True)
            self.label.setText("连续定位完成")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = BeidouGUI()
    gui.show()
    sys.exit(app.exec_())