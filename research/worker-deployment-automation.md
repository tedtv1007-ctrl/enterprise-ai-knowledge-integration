# Milk-Worker 分散式節點自動化部署研究

## 1. 背景與目標
為了實現 Milk Swarm 的分散式架構，我們需要一種快速、可重複且自動化的方式在各種雲端環境（如 DigitalOcean, Vultr, AWS）部署工作節點 (Milk-Worker)。

本研究旨在設計一個基於 Docker Compose 的一鍵部署方案，整合網路互連 (Tailscale) 與節點管理 (OpenClaw)。

## 2. 架構設計

### 2.1 容器化組件
- **Tailscale (Sidecar)**: 負責建立虛擬內網，使節點能安全地與 Gateway 通訊，無需暴露公網埠。
- **OpenClaw Node**: 核心執行環境，連接至 OpenClaw Gateway。
- **Heartbeat Script**: 定期回報節點狀態至 Registry（如 Notion 或 GitHub），用於監控與自我修復。

### 2.2 自動化配置機制
- **Tailscale Auth Key**: 使用可重複使用的 Auth Key 或 Ephemeral Key，透過環境變數 `TS_AUTHKEY` 自動加入。
- **OpenClaw Gateway Token**: 透過環境變數注入，節點啟動時自動向主控端進行認證。

## 3. 部署方案實現

### 3.1 Docker Compose 模板
我們採用 `network_mode: service:tailscale` 模式，讓所有組件共用 Tailscale 的網路介面。

```yaml
version: '3.8'
services:
  tailscale:
    image: tailscale/tailscale:latest
    container_name: tailscale
    hostname: ${NODE_NAME}
    environment:
      - TS_AUTHKEY=${TS_AUTHKEY}
      - TS_STATE_DIR=/var/lib/tailscale
    volumes:
      - tailscale_data:/var/lib/tailscale
      - /dev/net/tun:/dev/net/tun
    cap_add:
      - NET_ADMIN
      - SYS_MODULE
    restart: unless-stopped

  openclaw:
    image: openclaw/openclaw:latest
    container_name: openclaw
    network_mode: service:tailscale
    environment:
      - OPENCLAW_GATEWAY_TOKEN=${OPENCLAW_GATEWAY_TOKEN}
      - OPENCLAW_GATEWAY_URL=${OPENCLAW_GATEWAY_URL}
      - OPENCLAW_NODE_NAME=${NODE_NAME}
    restart: unless-stopped

  heartbeat:
    image: alpine:latest
    container_name: heartbeat
    network_mode: service:tailscale
    depends_on:
      - tailscale
    entrypoint: ["sh", "-c", "while true; do echo \"[$(date)] Heartbeat from $NODE_NAME\"; sleep 600; done"]
    environment:
      - NODE_NAME=${NODE_NAME}
    restart: unless-stopped

volumes:
  tailscale_data:
```

### 3.2 `worker-deploy.sh` 腳本範例
此腳本支援在 Ubuntu 22.04+ 環境下一鍵安裝與配置。

```bash
#!/bin/bash
# Milk-Worker 一鍵部署腳本 (Ubuntu 22.04+)

set -e

# 1. 檢查變數
if [ -z "$TS_AUTHKEY" ] || [ -z "$OPENCLAW_GATEWAY_TOKEN" ]; then
    echo "錯誤: 請設置 TS_AUTHKEY 與 OPENCLAW_GATEWAY_TOKEN 環境變數。"
    exit 1
fi

NODE_NAME=${NODE_NAME:-"milk-worker-$(hostname)"}
GATEWAY_URL=${OPENCLAW_GATEWAY_URL:-"http://milk-gateway:8080"}

echo "開始部署 Milk-Worker 節點: $NODE_NAME"

# 2. 安裝 Docker (如果未安裝)
if ! command -v docker &> /dev/null; then
    echo "正在安裝 Docker..."
    curl -fsSL https://get.docker.com | sh
fi

# 3. 準備目錄
mkdir -p ~/milk-worker
cd ~/milk-worker

# 4. 生成 docker-compose.yml
cat <<EOF > docker-compose.yml
version: '3.8'
services:
  tailscale:
    image: tailscale/tailscale:latest
    container_name: tailscale
    hostname: $NODE_NAME
    environment:
      - TS_AUTHKEY=$TS_AUTHKEY
      - TS_STATE_DIR=/var/lib/tailscale
    volumes:
      - tailscale_data:/var/lib/tailscale
      - /dev/net/tun:/dev/net/tun
    cap_add:
      - NET_ADMIN
      - SYS_MODULE
    restart: unless-stopped

  openclaw:
    image: openclaw/openclaw:latest
    container_name: openclaw
    network_mode: service:tailscale
    environment:
      - OPENCLAW_GATEWAY_TOKEN=$OPENCLAW_GATEWAY_TOKEN
      - OPENCLAW_GATEWAY_URL=$GATEWAY_URL
      - OPENCLAW_NODE_NAME=$NODE_NAME
    restart: unless-stopped

  heartbeat:
    image: alpine:latest
    container_name: heartbeat
    network_mode: service:tailscale
    entrypoint: ["sh", "-c", "while true; do echo \"[\\\$(date)] Heartbeat from \$NODE_NAME\"; sleep 600; done"]
    environment:
      - NODE_NAME=$NODE_NAME
    restart: unless-stopped

volumes:
  tailscale_data:
EOF

# 5. 啟動服務
docker compose up -d

echo "部署完成！節點 $NODE_NAME 正在後台啟動。"
echo "請至 Tailscale 控制面板確認節點狀態。"
```

## 4. 自動化配置研究心得

1. **Tailscale 預認證 (Pre-Auth)**:
   - 使用 Tailscale 的 **Auth Keys** 可以免除手動登入。
   - 建議使用 **Ephemeral Keys**，這樣節點刪除後會自動從 Tailscale 列表中移除。
   - 在部署腳本中透過 `TS_AUTHKEY` 環境變數傳遞。

2. **OpenClaw Gateway 接入**:
   - 節點啟動時需要 `OPENCLAW_GATEWAY_TOKEN` 進行握手。
   - 透過 Docker 環境變數注入是最簡單且安全的方式，避免將密鑰寫死在鏡像中。

3. **網路安全**:
   - 透過 `network_mode: service:tailscale`，OpenClaw 節點的所有對外流量都會經過 Tailscale 隧道，實現「預設私有」。

## 5. 後續改進
- 整合 Prometheus/Grafana 進行更詳細的資源監控。
- 支援自動備份 `tailscale_data` 卷宗，避免重新認證。
- 在部署腳本中加入系統調優參數（如開啟 BBR）。
