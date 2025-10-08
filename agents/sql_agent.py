from typing import TypedDict, Optional
import pandas as pd
from langgraph.graph import StateGraph, END
from services.llm.factory import make_llm
from tools.schema_loader import load_schema, extract_allowlists
from tools.sql_validator import validate_read_only
from tools.sql_executor import MsSqlExecutor
from tools.prompt_builders import build_sql_generation_messages, build_beautify_messages
from helpers.config import load_config
from helpers.formatting import to_markdown
from helpers.errors import ClarificationNeeded, ValidationError, ExecutionError
from db.session import SessionLocal
from db.models import ChatMessage
from tools.schema_retriever import SchemaRetriever
from openai import RateLimitError, APIStatusError

class AgentState(TypedDict):
    session_id: str
    user_query: str
    sql: Optional[str]
    df: Optional[pd.DataFrame]
    explanation_md: Optional[str]
    needs_clarification: bool


cfg = load_config()
schema_json = load_schema(cfg.schema["path"])

# NEW retriever setup
retriever = None
if cfg.retriever.get("enabled", False):
    retriever = SchemaRetriever(
        schema_json,
        persist_path=cfg.retriever["persist_path"],
        top_k=cfg.retriever["top_k"]
    )

# still keep allow-lists for validation
ALLOW_TABLES, ALLOW_COLS = extract_allowlists(schema_json)

llm = make_llm()
executor = MsSqlExecutor(cfg.database["odbc_connect"], timeout=cfg.limits["query_timeout_seconds"])


def node_generate_sql(state: AgentState) -> AgentState:
    """Generate SQL with conversation context."""
    
    print("⚙️ node_generate_sql() called")

    # Load last few messages for context
    history_messages = []
    if cfg.chat_history.get("enabled", False):
        with SessionLocal() as s:
            rows = (
                s.query(ChatMessage)
                .filter(ChatMessage.session_id == state["session_id"])
                .order_by(ChatMessage.id.desc())
                .limit(5)
                .all()
            )
            history_messages = [{"role": r.role, "content": r.content}
                                for r in reversed(rows)]

    # Build base messages
    base_msgs = build_sql_generation_messages(state["user_query"], schema_json, retriever)

    # Merge history before system+user prompts
    msgs = history_messages + base_msgs
    #print(f"🧠 Injected {len(history_messages)} previous messages into prompt: ", history_messages)
    print(f"🧠 Injected LLM msg input: ", msgs)

    mock_enabled = str(cfg.mock_flow.get("enabled", "0")) == "1"
    if mock_enabled:
        out = {
            "sql": "SELECT PaymentId, Amount, Status, TransactionDate FROM epay.Payments WHERE Status = 3 AND TransactionDate >= DATEADD(DAY, -60, GETDATE())",
            "confidence": 0.95,
            "needs_clarification": False,
            "notes": "Mock SQL generated (payments schema example).",
            "message": ""
        }
    else:
        out = llm.generate_sql_json(msgs, temperature=cfg.llm["temperature"])

    print("🤖 LLM output:", out)
    if out.get("needs_clarification"):
        raise ClarificationNeeded(out.get("notes") or "Need clarification.")

    state["sql"] = out["sql"]
    return state




def node_validate(state: AgentState) -> AgentState:
    print("running node_validate() before: ")
    sql = state["sql"] or ""
    validate_read_only(
        sql=sql,
        dialect=cfg.schema["dialect"],
        allow_tables=ALLOW_TABLES,
        allow_cols=ALLOW_COLS,
        block_keywords=set(k.upper() for k in cfg.security["block_keywords"]),
        block_functions=set(cfg.security["block_functions"]),
        allow_ctes=cfg.security["allow_ctes"],
    )
    return state

def node_execute(state: AgentState) -> AgentState:
   
    mock_enabled = str(cfg.mock_flow.get("enabled", "0")) == "1"

    # 👇 if you have no DB credentials, skip actual execution, and use below dummy data
    if mock_enabled: 

        data = [
            {"PaymentId": "FDF3C5CD-D0D2-4C9D-A5FB-092FA1E3DA0C", "Amount": 50.000, "Status": 3, "TransactionDate": "2025-09-08 22:07:57.223"},
            {"PaymentId": "99B198E0-6F8C-43BB-9664-0FE94606E141", "Amount": 50.000, "Status": 3, "TransactionDate": "2025-09-08 12:31:13.650"},
            {"PaymentId": "B987FAD6-E080-42A8-A21F-100FD2B9CEC7", "Amount": 50.000, "Status": 3, "TransactionDate": "2025-08-31 12:56:41.313"},
            {"PaymentId": "99CBB87B-8F8F-48D9-8C2E-16858FEEAA05", "Amount": 5.000, "Status": 3, "TransactionDate": "2025-09-14 11:26:21.433"},
            {"PaymentId": "139FE071-4340-46F3-AC4C-23E9696D4D89", "Amount": 50.000, "Status": 3, "TransactionDate": "2025-08-18 10:06:59.187"},
            {"PaymentId": "D0F0A3B2-D41D-47D9-953A-2A56CB664736", "Amount": 5.000, "Status": 3, "TransactionDate": "2025-09-09 12:02:01.690"},
            {"PaymentId": "91CD0A36-D5DB-4198-8539-2A7494F02DBF", "Amount": 50.000, "Status": 3, "TransactionDate": "2025-09-02 11:17:09.727"},
            {"PaymentId": "3850BD50-1840-47D7-9207-381740C1AA23", "Amount": 50.000, "Status": 3, "TransactionDate": "2025-09-17 17:24:51.047"},
            {"PaymentId": "1BD79AC7-FA46-48FD-AFB8-3E61FACD22F1", "Amount": 5.000, "Status": 3, "TransactionDate": "2025-09-10 09:49:26.857"},
            {"PaymentId": "9262A1D2-B695-436C-AE13-3E7A227497B9", "Amount": 50.000, "Status": 3, "TransactionDate": "2025-09-01 10:09:54.507"},
        ]

        df = pd.DataFrame(data)
        state["df"] = df
       
        return state
    
     # Fallback: try real execution (if credentials available)
    page_size = cfg.limits["default_page_size"]
    df = executor.run_select(state["sql"], page=1, page_size=page_size, hard_cap=cfg.limits["hard_row_cap"])
    state["df"] = df
    return state

def node_beautify(state: AgentState) -> AgentState:
    print("🤖 Generating SQL explanation...")
    df = state.get("df")

    # handle None or invalid cases
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        df = pd.DataFrame()

    table_md = to_markdown(df)
    msgs = build_beautify_messages(state["user_query"], state["sql"], table_md)
    md = llm.markdown(msgs, temperature=0.0)
    state["explanation_md"] = md
    print("🤖 SQL explanation:\n", md)
    return state

def node_end(state: AgentState) -> AgentState:
    return state

graph = StateGraph(AgentState)
graph.add_node("generate_sql", node_generate_sql)
graph.add_node("validate", node_validate)
graph.add_node("execute", node_execute)
graph.add_node("beautify", node_beautify)
graph.add_edge("generate_sql", "validate")
graph.add_edge("validate", "execute")
graph.add_edge("execute", "beautify")
graph.add_edge("beautify", END)
graph.set_entry_point("generate_sql")
app_graph = graph.compile()

def persist_message(session_id: str, role: str, content: str, provider: str = None, model: str = None):
    if not cfg.chat_history["enabled"]:
        return
    with SessionLocal() as s:
        s.add(ChatMessage(session_id=session_id, role=role, content=content, provider=provider, model=model))
        s.commit()

def run_agent(session_id: str, user_query: str) -> dict:
    """Main orchestrator for the SQL AI Agent."""
    try:
        # 💾 Persist user query
        persist_message(session_id, "user", user_query,
                        provider=cfg.llm["provider"], model=cfg.llm["model"])

        # Create agent state
        initial_state = AgentState(
            session_id=session_id,
            user_query=user_query,
            sql=None,
            df=None,
            explanation_md=None,
            needs_clarification=False
        )

        # Execute the state graph
        final_state = app_graph.invoke(initial_state)

        # Extract results
        md = final_state.get("explanation_md") or "No result."
        sql = final_state.get("sql") or ""

        # 💾 Save assistant reply
        persist_message(session_id, "assistant", md,
                        provider=cfg.llm["provider"], model=cfg.llm["model"])

        # ✅ Response
        return {
            "ok": True,
            "sql": sql,
            "markdown": md,
            "session_id": session_id
        }

    except ClarificationNeeded as ce:
        msg = f"I need a bit more detail to run a safe query: {ce}"
        persist_message(session_id, "assistant", msg)
        return {"ok": False, "needs_clarification": True, "message": msg}

    except ValidationError as ve:
        msg = f"Query blocked by safety validator: {ve}"
        persist_message(session_id, "assistant", msg)
        return {"ok": False, "error": msg}

    except ExecutionError as ee:
        msg = f"Execution error: {ee}"
        persist_message(session_id, "assistant", msg)
        return {"ok": False, "error": msg}

    except Exception as e:
        msg = f"Unexpected error: {e}"
        persist_message(session_id, "assistant", msg)
        return {"ok": False, "error": msg}
