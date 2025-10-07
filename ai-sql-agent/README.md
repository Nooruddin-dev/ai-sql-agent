# AI SQL Agent (Read-Only, Production-Grade)

## Quick Start

### 1. Create Virtual Environment
Go to the folder where you cloned the project and run:
```bash
python3 -m venv ar_ai_agent
```

Or run below one for latest python version env according to your version.
```bash
python3.11 -m venv ar_ai_agent
```

Activate the environment:

```bash
source ar_ai_agent/bin/activate
```

(Windows PowerShell:  
```powershell
.r_ai_agent\Scripts\activate
```)

---

### 2. Install Requirements
The project includes a `requirements.txt` file. Install dependencies by running:
```bash
pip install -r requirements.txt
```

---

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and set your API key(s).

---

### 4. Edit Configuration
Update `config/config.yaml`:

- Set `llm.provider` to one of:  
  `openai`, `deepseek`, `gemini-openai`, `ollama`.
- For non-OpenAI providers, set `llm.base_url` accordingly:
  - **DeepSeek**: `https://api.deepseek.com`
  - **Gemini (compat)**: `https://generativelanguage.googleapis.com/v1beta/openai/`
  - **Ollama local**: `http://localhost:11434/v1`
- Update `database.odbc_connect` with your SQL Server connection string, including **ApplicationIntent=ReadOnly** (and listener for read-only routing).

---

### 5. Database Schema
Place your exported DB schema JSON file at:
```
schema/database_schema.json
```

---

### 6. Run the Server
Start the API service:
```bash
uvicorn main:app --reload --port 8900
```

---

## Why this is Safe
- **Read-only enforced at 3 layers:**
  1. Connection string uses `ApplicationIntent=ReadOnly` for SQL Server AG routing/enforcement.  
  2. **SQLGlot** AST validation ensures only `SELECT` / `WITH … SELECT` queries are executed.  
  3. Block-list of keywords and stored procedures prevents dangerous paths.
- **Pagination**: all queries wrapped with `ORDER BY 1 OFFSET … FETCH …` for bounded and fast responses.

---

## Provider Switching
This project uses a **single OpenAI-compatible client**, so you can switch providers via config only (no code changes).  

Supported Providers:
- **OpenAI**  
- **DeepSeek** (OpenAI-compatible endpoint)  
- **Gemini** (OpenAI-compatible endpoint)  
- **Ollama** (local OpenAI-compatible API)  

---
