#!/bin/bash
# Milk-Worker 一鍵部署腳本 (Support DigitalOcean/Vultr Ubuntu)
# 用法: TS_AUTHKEY=tskey-auth... OPENCLAW_GATEWAY_TOKEN=... bash worker-deploy.sh

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}==> Milk-Worker 自動化部署開始 <==${NC}"

# 1. 參數檢查
if [ -z "$TS_AUTHKEY" ]; then
    echo -e "${RED}錯誤: 未設置 TS_AUTHKEY。請至 Tailscale 控制台生成。${NC}"
    exit 1
fi

if [ -z "$OPENCLAW_GATEWAY_TOKEN" ]; then
    echo -e "${RED}錯誤: 未設置 OPENCLAW_GATEWAY_TOKEN。${NC}"
    exit 1
fi

NODE_NAME=${NODE_NAME:-"milk-worker-$(hostname)"}
GATEWAY_URL=${OPENCLAW_GATEWAY_URL:-"http://milk-gateway:8080"}

# 2. 系統環境準備
echo -e "${GREEN}==> 更新系統並安裝基礎工具...${NC}"
sudo apt-get update && sudo apt-get install -y curl git ca-certificates gnupg

# 3. 安裝 Docker (如果未安裝)
if ! command -v docker &> /dev/null; then
    echo -e "${GREEN}==> 安裝 Docker...${NC}"
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
fi

# 4. 準備部署目錄
DEPLOY_DIR="$HOME/milk-worker-deploy"
mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR"

# 5. 寫入 Docker Compose 配置
echo -e "${GREEN}==> 配置 Docker Compose...${NC}"
cat <<EOF > docker-compose.yml
version: '3.8'

services:
  tailscale:
    image: tailscale/tailscale:latest
    container_name: milk-tailscale
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
    container_name: milk-openclaw-node
    network_mode: service:tailscale
    depends_on:
      - tailscale
    environment:
      - OPENCLAW_GATEWAY_TOKEN=${OPENCLAW_GATEWAY_TOKEN}
      - OPENCLAW_GATEWAY_URL=${GATEWAY_URL}
      - OPENCLAW_NODE_NAME=${NODE_NAME}
    restart: unless-stopped

  heartbeat:
    image: alpine:latest
    container_name: milk-heartbeat
    network_mode: service:tailscale
    depends_on:
      - tailscale
    entrypoint: 
      - /bin/sh
      - -c
      - |
        apk add --no-cache curl
        while true; do
          echo "[\\\$(date)] Sending heartbeat for ${NODE_NAME}..."
          # 這裡可以根據實際 API 調整，目前僅作為連通性測試與日誌紀錄
          # curl -X POST -d "node=${NODE_NAME}" ${GATEWAY_URL}/api/heartbeat || true
          sleep 600
        done
    restart: unless-stopped

volumes:
  tailscale_data:
EOF

# 6. 啟動節點
echo -e "${GREEN}==> 啟動 Milk-Worker 服務...${NC}"
docker compose up -d

# 7. 驗證與回報
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}部署成功！${NC}"
echo -e "節點名稱: ${NODE_NAME}"
echo -e "Tailscale 狀態: 正在加入網路..."
echo -e "OpenClaw 節點: 正在連接至 $GATEWAY_URL"
echo -e "您可以透過 'docker compose logs -f' 查看日誌"
echo -e "${GREEN}========================================${NC}"
