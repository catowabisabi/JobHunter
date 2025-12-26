# 智能求職助手 Smart Job Application Assistant

[繁體中文說明](#繁體中文說明) | [English Description](#english-description)

---

## 繁體中文說明

### 專案簡介
智能求職助手協助整理個人履歷資料、管理求職流程並透過 Google Gemini 與 OpenAI 模型自動生成履歷、求職信與 PDF 檔案。新版部署流程以 TrueNAS SCALE + Docker 為核心，方便集中管理與備份。

### TrueNAS SCALE 部署流程
1. **準備資料集**：在 TrueNAS SCALE 建立兩個目錄或資料集，分別存放 `instance`（SQLite 與使用者上傳資料）及 `output`（匯出檔案）。記錄它們的完整路徑，例如 `/mnt/tank/apps/jobhunter/instance` 與 `/mnt/tank/apps/jobhunter/output`。
2. **放置專案檔案**：將此專案資料夾（含 [Dockerfile](Dockerfile)、[docker-compose.yml](docker-compose.yml)、[requirements.txt](requirements.txt)）上傳到 TrueNAS SCALE 可存取的路徑，例如 `/mnt/tank/apps/jobhunter/app`。
3. **建立環境變數檔**：在專案根目錄建立 `.env`，內容可參考下列範例：
   ```bash
   GOOGLE_API_KEY=your-google-api-key
   GEMINI_MODEL=gemini-1.5-pro
   OPENAI_API_KEY=your-openai-api-key
   CHATGPT_MODEL=gpt-4o-mini
   API_KEY=replace-with-request-key
   SECRET_KEY=replace-with-flask-secret
   ```
4. **調整掛載路徑**：在 [docker-compose.yml](docker-compose.yml) 設定以下環境變數（可寫入 `.env` 或在 TrueNAS UI 輸入）：
   ```bash
   JOBHUNTER_INSTANCE_PATH=/mnt/tank/apps/jobhunter/instance
   JOBHUNTER_OUTPUT_PATH=/mnt/tank/apps/jobhunter/output
   ```
   若未提供，Compose 會 fallback 到容器內的預設 `./instance` 與 `./output`。
5. **建置與啟動容器**：在 TrueNAS SCALE Shell 或自動化任務執行：
   ```bash
   cd /mnt/tank/apps/jobhunter/app
   docker compose up -d --build
   ```
6. **驗證服務**：瀏覽 `http://<TrueNAS-IP>:5001/login`，首次登入預設帳號 `admin` 密碼 `Love2025`（建議立即變更）。

### 重要設定
- `WKHTMLTOPDF_PATH` 已在容器內預設為 `/usr/bin/wkhtmltopdf`，若自行部署於其他環境，可透過環境變數覆寫。
- `JOBHUNTER_INSTANCE_PATH` 與 `JOBHUNTER_OUTPUT_PATH` 決定資料持久化位置，請務必對應至 TrueNAS 的 ZFS 資料集。
- 若需設定 HTTPS 或反向代理，可在 TrueNAS SCALE 內再建立 Traefik/Nginx 容器。

### 手動開發環境（可選）
仍可於本地環境使用 `python -m venv` 或 Conda 建立虛擬環境並執行：
```bash
pip install -r requirements.txt
python app_04.py
```
若要產生 PDF，請自行安裝 wkhtmltopdf 並設定 `WKHTMLTOPDF_PATH`。

### 疑難排解
- **PDF 轉檔失敗**：確認 `wkhtmltopdf` 是否存在，並檢查 `.env` 裡的 `WKHTMLTOPDF_PATH`。
- **AI 呼叫失敗**：檢查 `.env` 中的 API Key 是否有效、配額是否足夠。
- **資料未保存**：確認 TrueNAS 掛載路徑對容器具備讀寫權限。

---

## English Description

### Overview
The Smart Job Application Assistant manages résumé data, guides job applications, and leverages Google Gemini plus OpenAI models to produce tailored résumés, cover letters, and PDFs. The recommended deployment now targets TrueNAS SCALE with Docker for easy maintenance and backups.

### Deploying on TrueNAS SCALE
1. **Prepare datasets**: Create two TrueNAS datasets or directories for persistent storage: one for `instance` (SQLite database and uploads) and another for `output` (generated documents). Record their absolute paths, such as `/mnt/tank/apps/jobhunter/instance` and `/mnt/tank/apps/jobhunter/output`.
2. **Upload project files**: Copy the repository (including [Dockerfile](Dockerfile), [docker-compose.yml](docker-compose.yml), and [requirements.txt](requirements.txt)) to a location accessible by TrueNAS, for example `/mnt/tank/apps/jobhunter/app`.
3. **Create the environment file**: Inside the project folder add a `.env` file using the template below:
   ```bash
   GOOGLE_API_KEY=your-google-api-key
   GEMINI_MODEL=gemini-1.5-pro
   OPENAI_API_KEY=your-openai-api-key
   CHATGPT_MODEL=gpt-4o-mini
   API_KEY=replace-with-request-key
   SECRET_KEY=replace-with-flask-secret
   ```
4. **Configure volume bindings**: Define the following variables (either in `.env` or via the TrueNAS UI) so Docker mounts the datasets correctly:
   ```bash
   JOBHUNTER_INSTANCE_PATH=/mnt/tank/apps/jobhunter/instance
   JOBHUNTER_OUTPUT_PATH=/mnt/tank/apps/jobhunter/output
   ```
   Without these values the compose file falls back to relative paths inside the container.
5. **Build and start the stack**: From the TrueNAS SCALE shell execute:
   ```bash
   cd /mnt/tank/apps/jobhunter/app
   docker compose up -d --build
   ```
6. **Confirm the service**: Visit `http://<truenas-ip>:5001/login`. The default credentials are `admin` / `Love2025`; change them immediately after signing in.

### Key configuration notes
- `WKHTMLTOPDF_PATH` defaults to `/usr/bin/wkhtmltopdf` inside the container. Override it via environment variable if your platform stores the binary elsewhere.
- `JOBHUNTER_INSTANCE_PATH` and `JOBHUNTER_OUTPUT_PATH` control persistence. Always point them to ZFS datasets so backups and snapshots work as expected.
- For TLS or reverse proxy, pair this service with Traefik or Nginx within TrueNAS SCALE.

### Optional local development
You can still run the project directly on a workstation:
```bash
pip install -r requirements.txt
python app_04.py
```
Install wkhtmltopdf manually and export `WKHTMLTOPDF_PATH` if you need PDF generation outside the container.

### Troubleshooting
- **PDF rendering errors**: ensure `wkhtmltopdf` is installed and the `WKHTMLTOPDF_PATH` variable points to the binary.
- **AI request failures**: verify the API keys saved in `.env` and confirm you have remaining quota.
- **Missing data**: double-check that the mounted dataset paths grant read/write permissions to the container user.