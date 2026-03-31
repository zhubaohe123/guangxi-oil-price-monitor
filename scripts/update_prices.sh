#!/bin/bash
# 从汽车之家获取真实油价并更新数据库
# 在宿主机运行（Docker容器无法访问汽车之家）

DATA_DIR="/vol2/@apphome/trim.openclaw/data/workspace/guangxi-oil-price-monitor/data"
DB="$DATA_DIR/oil_prices.db"
TODAY=$(date +%Y-%m-%d)

# 用curl从汽车之家抓取
HTML=$(curl -s -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  "https://www.autohome.com.cn/oil/450000.html" --max-time 15 2>/dev/null)

if [ -z "$HTML" ]; then
  echo "[$(date)] 无法访问汽车之家，跳过更新"
  exit 0
fi

# 提取价格
P92=$(echo "$HTML" | grep -oP '92号汽油为\K\d+\.?\d*')
P95=$(echo "$HTML" | grep -oP '95号汽油为\K\d+\.?\d*')
P0=$(echo "$HTML" | grep -oP '0号柴油为\K\d+\.?\d*')

if [ -z "$P92" ] || [ -z "$P95" ] || [ -z "$P0" ]; then
  echo "[$(date)] 无法解析价格数据"
  exit 0
fi

echo "[$(date)] 汽车之家油价: 92号=$P92  95号=$P95  0号柴油=$P0"

# 更新数据库
REGIONS="南宁 柳州 桂林 梧州 北海 防城港 钦州 贵港 玉林 百色 贺州 河池 来宾 崇左"
for R in $REGIONS; do
  sqlite3 "$DB" "INSERT OR REPLACE INTO oil_prices (region, date, gasoline_92, gasoline_95, diesel_0, source) VALUES ('$R', '$TODAY', $P92, $P95, $P0, '汽车之家(定时)');"
done

echo "[$(date)] 已更新14个地区的油价数据"
