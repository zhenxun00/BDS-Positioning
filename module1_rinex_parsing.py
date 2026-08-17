import re
import pandas as pd
import math
from datetime import datetime
import os


def split_tokens(s):
    return [float(x) for x in re.findall(r'[+-]?\d*\.?\d+(?:[eE][+-]?\d+)?', s)]


def parse_rinex_nav(file_path=None):
    # 默认路径：data/test.rnx
    if file_path is None:
        file_path = os.path.join("data", "test.rnx")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"RINEX文件不存在: {file_path}")

    sats = []
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    start = 0
    for i, line in enumerate(lines):
        if "END OF HEADER" in line:
            start = i + 1
            break
    lines = lines[start:]
    i = 0
    while i < len(lines):
        if len(lines[i].strip()) == 0 or not lines[i].startswith("C"):
            i += 1
            continue
        try:
            block = lines[i:i + 8]
            line0 = split_tokens(block[0])
            line1 = split_tokens(block[1])
            line2 = split_tokens(block[2])
            line3 = split_tokens(block[3])
            line4 = split_tokens(block[4])
            line6 = split_tokens(block[6])
            PRN = block[0].split()[0]
            epoch = datetime(int(line0[1]), int(line0[2]), int(line0[3]),
                             int(line0[4]), int(line0[5]), int(line0[6]))
            a = line2[3] ** 2 if len(line2) > 3 else None
            e = line2[1] if len(line2) > 1 else None
            M0 = line1[3] if len(line1) > 3 else None
            dn = line1[2] if len(line1) > 2 else None
            Omega0 = line3[2] if len(line3) > 2 else None
            i0 = line4[0] if len(line4) > 0 else None
            omega = line4[2] if len(line4) > 2 else None
            toe = line3[0] if len(line3) > 0 else None
            sv_health = line6[1] if len(line6) > 1 else 0
            if sv_health != 0:
                i += 8
                continue
            sats.append({
                "PRN": PRN, "epoch": epoch, "a": a, "sqrtA": math.sqrt(a) if a else None,
                "e": e, "M0": M0, "dn": dn, "Omega0": Omega0, "i0": i0, "omega": omega,
                "toe": toe, "sv_health": sv_health
            })
        except:
            pass
        i += 8
    df = pd.DataFrame(sats)
    df = df.sort_values(["epoch", "PRN"]).reset_index(drop=True)
    df.to_excel("module1_cleaned_nav.xlsx", index=False)
    print(f"模块1完成：{len(df)}条卫星星历数据")
    return df


if __name__ == "__main__":
    parse_rinex_nav()