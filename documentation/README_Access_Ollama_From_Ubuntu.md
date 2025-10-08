# 🦙 Ollama on Windows + WSL (Ubuntu) Setup Guide

This guide explains how to run **Ollama on Windows** and access it from **Ubuntu (WSL)**.  
Follow these steps if you want to integrate local Ollama models with your Linux tools and scripts.

---

## 📥 1. Install Ollama (Windows)
- Download the latest Windows build from [ollama.com/download](https://ollama.com/download).
- Install with the default path:
  ```
  C:\Users\<YourUser>\AppData\Local\Programs\Ollama\ollama.exe
  ```

---

## ✅ 2. Verify Ollama is Working
Open **PowerShell** and run:

```powershell
ollama list
```

You should see your installed models (`llama3`, etc.).

---

## 🔄 3. Expose Ollama to WSL Using Port Proxy
By default, Ollama only binds to `127.0.0.1` (localhost).  
To make it accessible from WSL, set up a port proxy:

Run in **Administrator PowerShell**:

```powershell
netsh interface portproxy add v4tov4 listenport=11434 listenaddress=0.0.0.0 connectport=11434 connectaddress=127.0.0.1
```

Verify the rule:

```powershell
netsh interface portproxy show all
```

Expected output:

```
0.0.0.0:11434   →   127.0.0.1:11434
```

---

## 🌐 4. Find Your Windows IP
In **PowerShell**, run:

```powershell
ipconfig
```

Look under your **Ethernet/Wi-Fi adapter** for `IPv4 Address`.  
Example:
```
10.20.20.97
```

---

## 🐧 5. Test from WSL (Ubuntu)
In your **Ubuntu terminal**, run:

```bash
curl http://<Windows-IP>:11434/api/tags
```

Example:

```bash
curl http://10.20.20.97:11434/api/tags
```

✅ You should receive JSON listing installed models.

---

## 💬 6. Run a Chat Request
From **Ubuntu (WSL)**:

```bash
curl -X POST "http://10.20.20.97:11434/v1/chat/completions"   -H "Content-Type: application/json"   -d '{
    "model": "llama3",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful assistant."
      },
      {
        "role": "user",
        "content": "List top 5 Oman cities, comma separated, short summary please."
      }
    ],
    "temperature": 0.7
  }'
```

Expected response (example):

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "Muscat, Nizwa, Sohar, Salalah, Seeb — five major cities in Oman known for their history, trade, and culture."
      }
    }
  ]
}
```

---

## 🧹 7. Remove Port Proxy (Optional)
If you no longer need forwarding, remove the rule:

```powershell
netsh interface portproxy delete v4tov4 listenport=11434 listenaddress=0.0.0.0
```

---

## ⚡ Notes
- Always run `netsh` commands in **Administrator PowerShell**.
- Windows Ollama does **not yet support `--host`**, so portproxy is required.
- In WSL, always connect via your **Windows IP** (e.g., `10.20.20.97`).

---

## 🎯 Summary
With this setup:
- Ollama runs on **Windows**.  
- WSL (Ubuntu) connects to it via Windows IP.  
- Port forwarding ensures smooth integration between environments.

Enjoy running Llama locally 🚀
