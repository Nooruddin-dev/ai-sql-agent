from tools.prompt_builders import build_sql_generation_messages

def test_prompt_build():
    schema = {"DatabaseSchema":[{"TableName":"Students","Columns":[{"ColumnName":"ID"},{"ColumnName":"Name"}]}]}
    msgs = build_sql_generation_messages("Show students", schema)
    assert any("ONLY SELECT" in m["content"] for m in msgs if m["role"]=="system")
