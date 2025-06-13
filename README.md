# 智能求職助手 Smart Job Application Assistant

[繁體中文](#繁體中文說明) | [English](#english-description)

## 繁體中文說明

### 功能簡介
這是一個智能求職助手應用程式，幫助您管理個人簡歷並自動生成求職文件。主要功能包括：

1. 個人資料管理
   - 編輯和保存個人基本資料
   - 管理工作經驗
   - 管理教育背景
   - 自動生成當日日期的 JSON 格式簡歷

2. 智能求職文件生成
   - 貼上職位描述自動分析
   - 使用 Google Gemini AI 生成：
     - 針對職位優化的簡歷
     - 英文求職信
     - 中文求職信
   - 自動保存所有文件（PDF 和 Markdown 格式）

### 安裝說明

1. 系統要求
   ```
   Python 3.9 或以上（由於 google-generativeai 套件的要求）
   pip 或 Conda（Python 包管理器）
   wkhtmltopdf（PDF 生成工具）
   ```

2. 安裝 wkhtmltopdf
   - Windows：從 https://wkhtmltopdf.org/downloads.html 下載安裝
   - macOS：`brew install wkhtmltopdf`
   - Linux：`sudo apt-get install wkhtmltopdf`

3. 選擇安裝方式：

   使用 pip：
   ```bash
   pip install -r requirements.txt
   ```

   或使用 Conda：
   ```bash
   # 創建新的 Conda 環境（使用 Python 3.9 或更高版本）
   conda create -n jobhunter python=3.9
   
   # 啟動環境
   conda activate jobhunter
   
   # 安裝依賴包
   conda install -c conda-forge flask=3.0.2
   conda install -c conda-forge python-dotenv=1.0.1
   conda install -c conda-forge markdown2=2.4.12
   pip install google-generativeai==0.3.2
   pip install pdfkit==1.0.0
   pip install sqlite3worker==1.1.7
   pip install flask-sqlalchemy==3.1.1
   ```

4. 設置環境變數
   - 創建 `.env` 檔案
   - 添加 Google Gemini API 金鑰：
     ```
     GOOGLE_API_KEY=your_api_key_here
     ```

### 使用說明

1. 啟動應用程式
   
   如果使用 pip：
   ```bash
   python app.py
   ```

   如果使用 Conda：
   ```bash
   conda activate jobhunter
   python app.py
   ```

2. 訪問網頁界面
   - 打開瀏覽器訪問：`http://localhost:5000`

3. 個人資料管理
   - 點擊「個人資料」頁面
   - 填寫或更新您的資料
   - 點擊「保存資料」按鈕

4. 生成求職文件
   - 點擊「職位申請」頁面
   - 貼上完整職位描述
   - 點擊「生成申請文件」
   - 等待系統生成文件
   - 下載生成的 PDF 文件

### 注意事項
- 首次使用時，如果有 `cv.json` 檔案，系統會自動導入資料
- 所有生成的文件都保存在 `output` 目錄下
- 文件名格式：`公司名_職位名_時間戳`

---

## English Description

### Features
This is a smart job application assistant that helps you manage your CV and automatically generate job application documents. Main features include:

1. Personal Information Management
   - Edit and save personal information
   - Manage work experience
   - Manage educational background
   - Auto-generate JSON format CV with current date

2. Smart Job Application Document Generation
   - Analyze job descriptions automatically
   - Use Google Gemini AI to generate:
     - Position-optimized CV
     - English cover letter
     - Chinese cover letter
   - Auto-save all documents (PDF and Markdown formats)

### Installation

1. System Requirements
   ```
   Python 3.9 or above (required by google-generativeai package)
   pip or Conda (Python package manager)
   wkhtmltopdf (PDF generation tool)
   ```

2. Install wkhtmltopdf
   - Windows: Download from https://wkhtmltopdf.org/downloads.html
   - macOS: `brew install wkhtmltopdf`
   - Linux: `sudo apt-get install wkhtmltopdf`

3. Choose Installation Method:

   Using pip:
   ```bash
   pip install -r requirements.txt
   ```

   Or using Conda:
   ```bash
   # Create new Conda environment (using Python 3.9 or above)
   conda create -n jobhunter python=3.9
   
   # Activate environment
   conda activate jobhunter
   
   # Install dependencies
   pip install uv
   uv pip install flask python-dotenv markdown2 google-generativeai pdfkit sqlite3worker flask-sqlalchemy
   ```

4. Set Environment Variables
   - Create `.env` file
   - Add Google Gemini API key:
     ```
     GOOGLE_API_KEY=your_api_key_here
     ```

### Usage Instructions

1. Start the Application
   
   If using pip:
   ```bash
   python app.py
   ```

   If using Conda:
   ```bash
   conda activate jobhunter
   python app.py
   ```

2. Access Web Interface
   - Open browser and visit: `http://localhost:5000`

3. Personal Information Management
   - Click on "Personal Information" page
   - Fill in or update your information
   - Click "Save Data" button

4. Generate Job Application Documents
   - Click on "Job Application" page
   - Paste complete job description
   - Click "Generate Application Documents"
   - Wait for system to generate documents
   - Download generated PDF files

### Notes
- If `cv.json` exists when first using the system, data will be automatically imported
- All generated documents are saved in the `output` directory
- File naming format: `company_name_position_timestamp` 