import pytest
from tools.sql_validator import validate_read_only

ALLOW_TABLES = {"Students", "Enrollments"}
ALLOW_COLS = {"Students": {"ID","Name"}, "Enrollments": {"StudentID","Date"}}
BLOCK_KW = {"INSERT","UPDATE","DELETE","DROP","ALTER","CREATE","MERGE"}
BLOCK_FN = {"OPENROWSET","xp_cmdshell"}

def test_select_ok():
    sql = "SELECT s.ID, s.Name FROM Students s"
    assert validate_read_only(sql, "tsql", ALLOW_TABLES, ALLOW_COLS, BLOCK_KW, BLOCK_FN, True) == sql

def test_block_update():
    with pytest.raises(Exception):
        validate_read_only("UPDATE Students SET Name='x'", "tsql", ALLOW_TABLES, ALLOW_COLS, BLOCK_KW, BLOCK_FN, True)

def test_block_unknown_table():
    with pytest.raises(Exception):
        validate_read_only("SELECT * FROM Hack", "tsql", ALLOW_TABLES, ALLOW_COLS, BLOCK_KW, BLOCK_FN, True)
