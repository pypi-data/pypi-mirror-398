"""
PayloadForge Obfuscation Utilities

⚠️  ETHICAL USE ONLY ⚠️

Payload obfuscation utilities for bypassing basic filters.
For authorized security testing and educational purposes only.
"""

import random
from typing import List


class SQLObfuscator:
    """SQL payload obfuscation utilities."""
    
    # SQL keywords that can have case variations
    SQL_KEYWORDS = [
        "SELECT", "UNION", "INSERT", "UPDATE", "DELETE", "DROP",
        "FROM", "WHERE", "AND", "OR", "ORDER", "BY", "LIMIT",
        "EXEC", "EXECUTE", "WAITFOR", "DELAY", "SLEEP", "BENCHMARK",
        "NULL", "TRUE", "FALSE", "LIKE", "IN", "BETWEEN",
    ]
    
    @staticmethod
    def case_flip(payload: str) -> str:
        """
        Randomly flip case of SQL keywords.
        
        Args:
            payload: SQL payload to obfuscate.
            
        Returns:
            Case-flipped payload.
        """
        result = []
        for char in payload:
            if random.random() > 0.5:
                result.append(char.upper())
            else:
                result.append(char.lower())
        return "".join(result)
    
    @staticmethod
    def alternating_case(payload: str) -> str:
        """
        Apply alternating case to payload.
        
        Args:
            payload: SQL payload to obfuscate.
            
        Returns:
            Alternating case payload.
        """
        result = []
        upper = True
        for char in payload:
            if char.isalpha():
                result.append(char.upper() if upper else char.lower())
                upper = not upper
            else:
                result.append(char)
        return "".join(result)
    
    @staticmethod
    def whitespace_bypass(payload: str) -> str:
        """
        Replace spaces with alternative whitespace characters.
        
        Args:
            payload: SQL payload.
            
        Returns:
            Payload with whitespace bypasses.
        """
        alternatives = ["/**/", "\t", "\n", "\r", "%09", "%0a", "%0d", "%20"]
        replacement = random.choice(alternatives)
        return payload.replace(" ", replacement)
    
    @staticmethod
    def inline_comments(payload: str) -> str:
        """
        Insert inline comments within SQL keywords.
        
        Args:
            payload: SQL payload.
            
        Returns:
            Payload with inline comments.
        """
        # Insert /**/ in the middle of keywords
        for keyword in SQLObfuscator.SQL_KEYWORDS:
            if keyword in payload.upper():
                # Find case-insensitive match and insert comment
                idx = payload.upper().find(keyword)
                if idx >= 0:
                    original = payload[idx:idx + len(keyword)]
                    mid = len(original) // 2
                    obfuscated = original[:mid] + "/**/" + original[mid:]
                    payload = payload[:idx] + obfuscated + payload[idx + len(keyword):]
        return payload
    
    @staticmethod
    def concat_bypass(payload: str) -> str:
        """
        Use string concatenation to bypass keyword detection.
        
        Args:
            payload: SQL payload.
            
        Returns:
            Payload with concatenation.
        """
        # MySQL concat example
        return payload.replace("SELECT", "SEL" + "/**/ECT")
    
    @staticmethod
    def hex_encode_strings(payload: str) -> str:
        """
        Encode string literals as hex values.
        
        Args:
            payload: SQL payload.
            
        Returns:
            Payload with hex-encoded strings.
        """
        import re
        
        def to_hex(match):
            content = match.group(1)
            hex_val = content.encode().hex()
            return f"0x{hex_val}"
        
        # Replace 'string' with hex
        return re.sub(r"'([^']*)'", to_hex, payload)
    
    @staticmethod
    def numeric_bypass(payload: str) -> str:
        """
        Replace numbers with expressions.
        
        Args:
            payload: SQL payload.
            
        Returns:
            Payload with numeric expressions.
        """
        # Replace common numbers
        replacements = {
            "1": "(2-1)",
            "0": "(1-1)",
            "5": "(3+2)",
        }
        for old, new in replacements.items():
            payload = payload.replace(old, new)
        return payload


class JSObfuscator:
    """JavaScript payload obfuscation utilities."""
    
    @staticmethod
    def string_from_charcode(text: str) -> str:
        """
        Convert string to String.fromCharCode.
        
        Args:
            text: Text to convert.
            
        Returns:
            fromCharCode representation.
        """
        codes = ",".join(str(ord(c)) for c in text)
        return f"String.fromCharCode({codes})"
    
    @staticmethod
    def atob_encode(text: str) -> str:
        """
        Encode using atob (base64).
        
        Args:
            text: Text to encode.
            
        Returns:
            atob wrapped payload.
        """
        import base64
        encoded = base64.b64encode(text.encode()).decode()
        return f"atob('{encoded}')"
    
    @staticmethod
    def eval_wrap(payload: str) -> str:
        """
        Wrap payload in eval.
        
        Args:
            payload: JavaScript payload.
            
        Returns:
            eval-wrapped payload.
        """
        codes = ",".join(str(ord(c)) for c in payload)
        return f"eval(String.fromCharCode({codes}))"
    
    @staticmethod
    def constructor_exec(payload: str) -> str:
        """
        Use Function constructor for execution.
        
        Args:
            payload: JavaScript code.
            
        Returns:
            Function constructor payload.
        """
        return f"[].constructor.constructor('{payload}')()"
    
    @staticmethod
    def template_literal(text: str) -> str:
        """
        Convert to template literal format.
        
        Args:
            text: Text to convert.
            
        Returns:
            Template literal format.
        """
        return f"`{text}`"
    
    @staticmethod
    def unicode_escape(text: str) -> str:
        """
        Convert to Unicode escape sequences.
        
        Args:
            text: Text to convert.
            
        Returns:
            Unicode escaped string.
        """
        return "".join(f"\\u{ord(c):04x}" for c in text)
    
    @staticmethod
    def octal_escape(text: str) -> str:
        """
        Convert to octal escape sequences.
        
        Args:
            text: Text to convert.
            
        Returns:
            Octal escaped string.
        """
        return "".join(f"\\{ord(c):03o}" for c in text if ord(c) < 256)
    
    @staticmethod
    def jsfuck_style(char: str) -> str:
        """
        Get JSFuck-style representation for common characters.
        
        Args:
            char: Single character.
            
        Returns:
            JSFuck-style representation.
        """
        # Simplified JSFuck mappings
        mappings = {
            "a": "(![]+[])[+!+[]]",
            "e": "(!![]+[])[+!+[]+!+[]+!+[]]",
            "l": "(![]+[])[!+[]+!+[]]",
            "r": "(!![]+[])[+!+[]]",
            "t": "(!![]+[])[+[]]",
        }
        return mappings.get(char, f"'{char}'")


class HTMLObfuscator:
    """HTML payload obfuscation utilities."""
    
    @staticmethod
    def tag_case_variation(html: str) -> str:
        """
        Apply random case to HTML tags.
        
        Args:
            html: HTML content.
            
        Returns:
            HTML with randomized tag cases.
        """
        import re
        
        def randomize_tag(match):
            tag = match.group(1)
            return "<" + "".join(
                c.upper() if random.random() > 0.5 else c.lower()
                for c in tag
            )
        
        return re.sub(r"<([a-zA-Z]+)", randomize_tag, html)
    
    @staticmethod
    def add_extra_whitespace(html: str) -> str:
        """
        Add extra whitespace in tags.
        
        Args:
            html: HTML content.
            
        Returns:
            HTML with extra whitespace.
        """
        import re
        return re.sub(r"<(\w+)", r"< \1", html)
    
    @staticmethod
    def newline_in_tags(html: str) -> str:
        """
        Add newlines within HTML tags.
        
        Args:
            html: HTML content.
            
        Returns:
            HTML with newlines in tags.
        """
        import re
        return re.sub(r"<(\w+)\s", r"<\1\n", html)
