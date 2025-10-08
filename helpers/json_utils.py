import json
import ast
import re
import textwrap
import sqlparse


class JsonSqlHelper:
    @staticmethod
    def safe_json_loads(content: str) -> dict:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract the JSON object using regex
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                json_part = match.group(0)
                try:
                    return json.loads(json_part)
                except Exception as e:
                    print("⚠️ Still failed parsing extracted JSON:", e)

            # Fallback: Python dict-style parse
            try:
                return ast.literal_eval(content)
            except Exception as e2:
                print("❌ Failed to parse content:", e2)
                return {}
    
    
    @staticmethod
    def clean_sql(sql_value: str) -> str:
        """
        Extract, clean, and format SQL string.
        """
        if not sql_value:
            return ""

        # Remove triple quotes and strip
        sql_value = sql_value.replace('"""', '').replace("'''", "").strip()

        # Dedent
        sql_value = textwrap.dedent(sql_value)

        # Add semicolon if missing
        if not sql_value.endswith(";"):
            sql_value += ";"

        # Format with sqlparse
        sql_value = sqlparse.format(sql_value, reindent=True, keyword_case="upper")
        return sql_value
