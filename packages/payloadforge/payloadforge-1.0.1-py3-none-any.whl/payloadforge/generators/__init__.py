"""
PayloadForge Generators Package

⚠️  ETHICAL USE ONLY ⚠️

This package contains payload generators for various vulnerability types.
All generators return payload strings only - they never execute anything.
"""

from payloadforge.generators.xss import XSSGenerator
from payloadforge.generators.sqli import SQLiGenerator
from payloadforge.generators.ssti import SSTIGenerator
from payloadforge.generators.cmdi import CMDiGenerator

__all__ = [
    "XSSGenerator",
    "SQLiGenerator",
    "SSTIGenerator",
    "CMDiGenerator",
]
