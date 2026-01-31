# APISIX 網關架構與服務路由 (Milk 整理)

根據現有 Wiki 紀錄，系統採用 APISIX 作為統一入口，管理容器間的流量與路由。

## 1. 流量入口配置
- **HTTP**: 9080
- **HTTPS**: 9443
- **Admin API**: 9180
- **Dashboard**: 9000

## 2. 服務路由清單 (Upstream Services)
| 服務名稱 | 內部埠號 | 外部域名 (*.it205.ski.ad) |
| :--- | :--- | :--- |
| Wiki.js | 3000 | wikijs.it205 |
| Mattermost | 8065 | mattermost.it205 |
| Ollama | 11434 | ollama.it205 |
| AnythingLLM | 3001 | anythingllm.it205 |
| Elasticsearch | 9200 | elasticsearch.it205 |
| Kibana | 5601 | kibana.it205 |
| Logstash | 5044 | logstash.it205 |
| APM Server | 8200 | apm-server.it205 |

## 3. 基礎設施支撐
- **配置存儲**: Etcd (2379)
- **監控數據**: Prometheus (9090)
- **數據視覺化**: Grafana (3000)

## 4. 下一步優化方向
- 整合 APISIX 的 Auth 插件，確保 LLM 與 RAG 資源的存取安全性。
- 研究如何透過 APISIX 限流 (Rate Limiting) 保護 Ollama 推理資源。
