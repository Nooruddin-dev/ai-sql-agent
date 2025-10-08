import os
from typing import List, Dict, Optional
import json
from openai import OpenAI
from helpers.errors import ProviderError
from helpers.json_utils import JsonSqlHelper

from dotenv import load_dotenv

# ✅ Load environment variables immediately when this module is imported
load_dotenv()

class OpenAICompatibleService:
    """
    Works with:
    - OpenAI cloud (default base_url)
    - DeepSeek (base_url=https://api.deepseek.com, api_key=DEEPSEEK_API_KEY)
    - Gemini via OpenAI-compatible endpoint (base_url=https://generativelanguage.googleapis.com/v1beta/openai/)  # :contentReference[oaicite:10]{index=10}
    - Ollama/local (base_url=http://localhost:11434/v1)  # :contentReference[oaicite:11]{index=11}
    """
    def __init__(self, base_url: Optional[str], api_key_env: str, model: str, timeout: int = 60, max_retries: int = 2,
                 provider_name: str = "openai"):
     
        api_key = os.getenv(api_key_env) or os.getenv("OPENAI_API_KEY")
 
        if not api_key and (base_url or "openai" in api_key_env.lower()):
            raise ProviderError(f"Missing API key in env: {api_key_env} or OPENAI_API_KEY")
        

        #self.client = OpenAI(base_url=base_url or None, api_key=api_key)
        self.client = OpenAI(
            base_url=base_url or None,
            api_key=api_key,
            timeout=timeout,
            max_retries= max_retries  # 👈 important
        )

        self.model = model
        self.timeout = timeout
        self.provider_name = provider_name

   
   
   

   
   
    def chat(self, messages: List[Dict], temperature: float = 0.0) -> str:
        # Use Chat Completions for broad OpenAI-compatibility. :contentReference[oaicite:12]{index=12}
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            timeout=self.timeout,
        )
        return resp.choices[0].message.content

    def generate_sql_json(self, messages: list, temperature: float = 0.0) -> dict:
        result = {
            "sql": None,
            "confidence": 0.0,
            "needs_clarification": True,
            "notes": "",
            "message": ""
        }

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                timeout=self.timeout,
            )
            content = resp.choices[0].message.content.strip()

            if self.provider_name == "ollama":
          
                parsed = JsonSqlHelper.safe_json_loads(content)
        
                
                if not parsed:
                    # fallback: check if raw SQL inside content
                    if "SELECT" in content.upper():
                        result.update({
                            "sql": content,
                            "confidence": 0.7,
                            "needs_clarification": False,
                            "notes": "Parsed as raw SQL from Ollama (fallback)"
                        })
                    else:
                        result["notes"] = f"Ollama output unusable: {content[:100]}..."
                    return result

                sql_value = JsonSqlHelper.clean_sql(parsed.get("sql", ""))
 


                result.update({
                    "sql": sql_value or None,
                    "confidence": float(parsed.get("confidence", 0.7)),
                    "needs_clarification": bool(parsed.get("needs_clarification", False)),
                    "notes": parsed.get("notes", "Parsed from Ollama JSON")
                })

            else:  # OpenAI/DeepSeek/Gemini
                try:
                    parsed = json.loads(content)
                    result.update({
                        "sql": parsed.get("sql"),
                        "confidence": float(parsed.get("confidence", 0.9)),
                        "needs_clarification": bool(parsed.get("needs_clarification", False)),
                        "notes": parsed.get("notes", "Parsed from OpenAI JSON")
                    })
                except Exception as e:
                    result["notes"] = f"Failed to parse LLM JSON: {e}"

        except Exception as e:
            result["notes"] = str(e)

        return result


    def markdown(self, messages: list, temperature: float = 0.0) -> str:
        """
        Generate markdown-style explanation text (for beautify node).
        Works for OpenAI, Ollama, DeepSeek, and Gemini.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                timeout=self.timeout,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"⚠️ Markdown generation failed: {str(e)}"



    

    

