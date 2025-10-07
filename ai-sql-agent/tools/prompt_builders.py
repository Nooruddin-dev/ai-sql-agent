import json
from typing import Dict, List

# def build_sql_generation_messages(user_query: str, schema_json: Dict) -> List[Dict]:
#     schema_excerpt = json.dumps(schema_json["DatabaseSchema"][:50])

#     system = (
#         "You are a senior data analyst for a Ministry of Education system.\n"
#         "Task: Convert the user request into a **single, safe T-SQL SELECT** query for Microsoft SQL Server.\n"
#         "Follow rules strictly:\n"
#         "1) ONLY SELECT / WITH CTEs leading to SELECT. No INSERT/UPDATE/DELETE/MERGE/TRUNCATE/DDL/EXEC.\n"
#         "2) Use only tables/columns present in the provided schema.\n"
#         "3) Prefer explicit JOINs; qualify columns (t.col) to avoid ambiguity.\n"
#         "4) If the user asks for total records in a table, always return COUNT(*).\n"
#         "5) Only ask for clarification if NO table can be mapped at all.\n"
#         "6) Respond in JSON with keys: {\"sql\": string, \"confidence\": 0..1, \"needs_clarification\": boolean, \"notes\": string}."
#     )

#     schema_msg = f"Schema (partial): {schema_excerpt}"
#     user = f"User request: {user_query}"

#     return [
#         {"role": "system", "content": system},
#         {"role": "system", "content": schema_msg},
#         {"role": "user", "content": user},
#     ]

def build_sql_generation_messages(user_query: str, schema_json: Dict, retriever=None) -> List[Dict]:
    if retriever:
     
        matches = retriever.query(user_query)

    
        
        schema_excerpt = json.dumps(matches, indent=2)
    else:
        schema_excerpt = json.dumps(schema_json["DatabaseSchema"][:50])

    system = (
    "You are a SQL code generator for a Ministry of Education database.\n"
    "Your ONLY job is to return one valid JSON object with a safe T-SQL SELECT query.\n\n"
    "❌ Forbidden:\n"
    "- Using world knowledge (e.g., MIT, Harvard, rankings).\n"
    "- Providing explanations, text, or markdown outside of JSON.\n"
    "- Returning answers unrelated to the provided schema.\n\n"
    "✅ Required:\n"
    "- Use ONLY the provided schema excerpt.\n"
    "- If no relevant table exists, return sql=null, needs_clarification=true, and explain why in notes.\n"
    "- Always include all 5 keys: sql, confidence, needs_clarification, notes, message.\n"
    "- SQL must be a single-line string (use \\n for newlines).\n\n"
    f"Schema excerpt:\n{schema_excerpt}\n\n"
    "⚠️ STRICT OUTPUT FORMAT:\n"
    "{\n"
    "  \"sql\": string or null,\n"
    "  \"confidence\": float (0..1),\n"
    "  \"needs_clarification\": boolean,\n"
    "  \"notes\": string,\n"
    "  \"message\": string\n"
    "}\n"
    "Output JSON ONLY. No text, no markdown, no extra words."
)


    user = f"User request: {user_query}"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]



def build_beautify_messages(user_query: str, sql: str, preview_markdown: str) -> List[Dict]:
    system = (
        "You are a senior data analyst and presenter. Produce a clear, accurate, user-friendly summary.\n"
        "Requirements:\n"
        "- Explain what the query returns in simple business language.\n"
        "- Show a clean markdown table of the preview (already provided as markdown).\n"
        "- Mention filters/date ranges, grouping, and any caveats.\n"
        "- If appropriate, propose 1-2 follow-up questions.\n"
        "Return markdown only."
    )
    user = (
        f"Original request: {user_query}\n\n"
        f"SQL used:\n```\n{sql}\n```\n\n"
        f"Preview:\n{preview_markdown}\n"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
