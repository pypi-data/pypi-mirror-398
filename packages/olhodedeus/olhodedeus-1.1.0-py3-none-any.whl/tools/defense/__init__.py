#!/usr/bin/env python3
"""
Defense Tools - Ferramentas de defesa e análise de segurança
Parte do toolkit Olho de Deus
"""

from .malware_analyzer import (
    MalwareAnalyzer,
    FileTypeDetector,
    StringExtractor,
    EntropyCalculator,
    interactive_menu as malware_analyzer_menu
)

from .log_analyzer import (
    LogAnalyzer,
    LogParser,
    SecurityDetector,
    interactive_menu as log_analyzer_menu
)

from .network_traffic import (
    TrafficAnalyzer,
    PcapParser,
    NetstatParser,
    ProtocolDB,
    interactive_menu as network_traffic_menu
)

from .ransomware_db import (
    RansomwareDatabase,
    RansomwareDetector,
    interactive_menu as ransomware_db_menu
)

from .firewall_generator import (
    FirewallGenerator,
    FirewallRule,
    IPTablesGenerator,
    WindowsFirewallGenerator,
    UFWGenerator,
    PfGenerator,
    interactive_menu as firewall_generator_menu
)

__all__ = [
    # Malware Analyzer
    'MalwareAnalyzer',
    'FileTypeDetector',
    'StringExtractor',
    'EntropyCalculator',
    'malware_analyzer_menu',
    
    # Log Analyzer
    'LogAnalyzer',
    'LogParser',
    'SecurityDetector',
    'log_analyzer_menu',
    
    # Network Traffic
    'TrafficAnalyzer',
    'PcapParser',
    'NetstatParser',
    'ProtocolDB',
    'network_traffic_menu',
    
    # Ransomware DB
    'RansomwareDatabase',
    'RansomwareDetector',
    'ransomware_db_menu',
    
    # Firewall Generator
    'FirewallGenerator',
    'FirewallRule',
    'IPTablesGenerator',
    'WindowsFirewallGenerator',
    'UFWGenerator',
    'PfGenerator',
    'firewall_generator_menu',
]
