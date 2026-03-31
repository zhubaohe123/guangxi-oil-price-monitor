#!/usr/bin/env python3
"""
从汽车之家获取广西真实油价并更新数据库
在宿主机运行，每日定时执行
"""
import re
import subprocess
import sqlite3
from datetime import date

DB_PATH = "/vol2/@apphome/trim.openclaw/data/workspace/guangxi-oil-price-monitor/data/oil_prices.db"
REGIONS = ["南宁","柳州","桂林","梧州","北海","防城港","钦州","贵港","玉林","百色","贺州","河池","来宾","崇左"]

def fetch_and_update():
    today = date.today().isoformat()
    
    # 抓取汽车之家
    r = subprocess.run(
        ["curl", "-s", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
         "https://www.autohome.com.cn/oil/450000.html", "--max-time", "15"],
        capture_output=True
    )
    html = r.stdout.decode("utf-8", errors="replace")
    
    # 解析价格（兼容不同编码和换行）
    m92 = re.search(r'92.{0,15}汽油.{0,10}(\d+\.\d+)', html)
    m95 = re.search(r'95.{0,15}汽油.{0,10}(\d+\.\d+)', html)
    m0  = re.search(r'0.{0,15}柴油.{0,10}(\d+\.\d+)', html)
    
    if not (m92 and m95 and m0):
        print(f"[{today}] 无法解析油价数据")
        return False
    
    p92, p95, p0 = float(m92.group(1)), float(m95.group(1)), float(m0.group(1))
    print(f"[{today}] 汽车之家油价: 92号={p92}  95号={p95}  0号={p0}")
    
    # 写入数据库
    conn = sqlite3.connect(DB_PATH)
    for r in REGIONS:
        conn.execute(
            "INSERT OR REPLACE INTO oil_prices (region, date, gasoline_92, gasoline_95, diesel_0, source) VALUES (?,?,?,?,?,?)",
            (r, today, p92, p95, p0, "汽车之家(定时)")
        )
    conn.commit()
    conn.close()
    print(f"[{today}] 已更新{len(REGIONS)}个地区")
    return True

if __name__ == "__main__":
    fetch_and_update()
