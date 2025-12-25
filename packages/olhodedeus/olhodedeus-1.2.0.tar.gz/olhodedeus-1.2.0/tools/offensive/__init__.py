#!/usr/bin/env python3
"""
Offensive Security Tools - __init__.py
"""

from .payload_generator import PayloadGenerator, XSSPayloads, SQLiPayloads, SSTIPayloads, LFIPayloads
from .exploit_db import ExploitDBClient, NVDClient, VulnerabilityScanner
from .web_fuzzer import WebFuzzer, WordlistManager
from .waf_detector import WAFDetector, WAFBypass, WAFDatabase
from .c2_lite import C2Server, PayloadGenerator as C2PayloadGenerator

__all__ = [
    'PayloadGenerator',
    'XSSPayloads',
    'SQLiPayloads', 
    'SSTIPayloads',
    'LFIPayloads',
    'ExploitDBClient',
    'NVDClient',
    'VulnerabilityScanner',
    'WebFuzzer',
    'WordlistManager',
    'WAFDetector',
    'WAFBypass',
    'WAFDatabase',
    'C2Server',
    'C2PayloadGenerator'
]
