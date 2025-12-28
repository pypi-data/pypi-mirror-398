"""
Tests for SQL Injection Payload Generator
"""

import pytest
from payloadforge.generators.sqli import SQLiGenerator, generate_error_based, generate_time_based


class TestSQLiGenerator:
    """Test cases for SQLiGenerator."""
    
    def test_generate_error_based_mysql(self):
        """Test MySQL error-based payloads."""
        result = SQLiGenerator.generate_error_based("mysql")
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_generate_error_based_mssql(self):
        """Test MSSQL error-based payloads."""
        result = SQLiGenerator.generate_error_based("mssql")
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_generate_error_based_postgres(self):
        """Test PostgreSQL error-based payloads."""
        result = SQLiGenerator.generate_error_based("postgres")
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_generate_error_based_with_count(self):
        """Test count parameter."""
        result = SQLiGenerator.generate_error_based("mysql", count=3)
        assert len(result) == 3
    
    def test_generate_error_based_invalid_db(self):
        """Test fallback to MySQL for invalid DB type."""
        result = SQLiGenerator.generate_error_based("invalid")
        mysql_result = SQLiGenerator.generate_error_based("mysql")
        assert result == mysql_result
    
    def test_generate_time_based_mysql(self):
        """Test MySQL time-based payloads."""
        result = SQLiGenerator.generate_time_based("mysql")
        assert isinstance(result, list)
        assert any("sleep" in p.lower() for p in result)
    
    def test_generate_time_based_mssql(self):
        """Test MSSQL time-based payloads."""
        result = SQLiGenerator.generate_time_based("mssql")
        assert isinstance(result, list)
        assert any("waitfor" in p.lower() for p in result)
    
    def test_generate_time_based_postgres(self):
        """Test PostgreSQL time-based payloads."""
        result = SQLiGenerator.generate_time_based("postgres")
        assert isinstance(result, list)
        assert any("pg_sleep" in p.lower() for p in result)
    
    def test_generate_union_based(self):
        """Test union-based payloads."""
        result = SQLiGenerator.generate_union_based("mysql")
        assert isinstance(result, list)
        assert any("union" in p.lower() for p in result)
    
    def test_generate_boolean_based(self):
        """Test boolean-based payloads."""
        result = SQLiGenerator.generate_boolean_based("mysql")
        assert isinstance(result, list)
        assert any("and" in p.lower() for p in result)
    
    def test_generate_all_returns_dict(self):
        """Test that generate_all returns all categories."""
        result = SQLiGenerator.generate_all("mysql")
        assert isinstance(result, dict)
        assert "error_based" in result
        assert "time_based" in result
        assert "union_based" in result
        assert "boolean_based" in result
    
    def test_obfuscate_case(self):
        """Test case obfuscation."""
        payloads = ["SELECT * FROM users"]
        result = SQLiGenerator.obfuscate(payloads, "case")
        # Result should have mixed case
        assert result[0] != payloads[0]
    
    def test_obfuscate_whitespace(self):
        """Test whitespace obfuscation."""
        payloads = ["SELECT * FROM users"]
        result = SQLiGenerator.obfuscate(payloads, "whitespace")
        # Result should not have regular spaces
        assert " " not in result[0] or result[0] != payloads[0]
    
    def test_convenience_functions(self):
        """Test convenience function exports."""
        assert generate_error_based() == SQLiGenerator.generate_error_based()
        assert generate_time_based() == SQLiGenerator.generate_time_based()


class TestSQLiPayloadQuality:
    """Test the quality of SQLi payloads."""
    
    def test_payloads_contain_sql_syntax(self):
        """Test that payloads contain SQL syntax."""
        result = SQLiGenerator.generate_error_based("mysql")
        sql_keywords = ["or", "and", "select", "union", "--", "#"]
        has_sql = all(
            any(kw in p.lower() for kw in sql_keywords)
            for p in result
        )
        assert has_sql
    
    def test_error_payloads_minimum_count(self):
        """Test minimum payload count."""
        for db in ["mysql", "mssql", "postgres"]:
            result = SQLiGenerator.generate_error_based(db)
            assert len(result) >= 5
    
    def test_different_dbs_have_different_payloads(self):
        """Test that different DBs have unique payloads."""
        mysql = set(SQLiGenerator.generate_time_based("mysql"))
        mssql = set(SQLiGenerator.generate_time_based("mssql"))
        # Should have some differences
        assert mysql != mssql
