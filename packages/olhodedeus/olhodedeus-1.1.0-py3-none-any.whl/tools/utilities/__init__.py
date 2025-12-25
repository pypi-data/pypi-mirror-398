"""
Utilities - Ferramentas Utilitárias
Parte do toolkit Olho de Deus
"""

from .encoding_hub import (
    EncodingResult,
    Base64Encoder,
    Base32Encoder,
    Base16Encoder,
    URLEncoder,
    HTMLEncoder,
    HexEncoder,
    BinaryEncoder,
    OctalEncoder,
    ASCIIEncoder,
    ROT13Encoder,
    UnicodeEncoder,
    JSONEncoder,
    MorseEncoder,
    EncodingHub,
    interactive_menu as encoding_menu
)

from .hash_identifier import (
    HashInfo,
    HashMatch,
    HashDatabase,
    HashIdentifier,
    HashGenerator,
    HashAnalyzer,
    interactive_menu as hash_menu
)

from .regex_builder import (
    RegexMatch,
    RegexTest,
    RegexPatternLibrary,
    RegexBuilder,
    RegexTester,
    interactive_menu as regex_menu
)

from .wordlist_generator import (
    WordlistConfig,
    LeetSpeakConverter,
    CasePermutator,
    SuffixAppender,
    PatternGenerator,
    CombinationGenerator,
    WordlistGenerator,
    interactive_menu as wordlist_menu
)

from .password_policy import (
    PolicyRule,
    PasswordAnalysis,
    CommonPatterns,
    EntropyCalculator,
    PasswordPolicy,
    PasswordAnalyzer,
    PasswordGenerator,
    interactive_menu as password_menu
)

__all__ = [
    # Encoding Hub
    "EncodingResult",
    "Base64Encoder",
    "Base32Encoder",
    "Base16Encoder",
    "URLEncoder",
    "HTMLEncoder",
    "HexEncoder",
    "BinaryEncoder",
    "OctalEncoder",
    "ASCIIEncoder",
    "ROT13Encoder",
    "UnicodeEncoder",
    "JSONEncoder",
    "MorseEncoder",
    "EncodingHub",
    "encoding_menu",
    
    # Hash Identifier
    "HashInfo",
    "HashMatch",
    "HashDatabase",
    "HashIdentifier",
    "HashGenerator",
    "HashAnalyzer",
    "hash_menu",
    
    # Regex Builder
    "RegexMatch",
    "RegexTest",
    "RegexPatternLibrary",
    "RegexBuilder",
    "RegexTester",
    "regex_menu",
    
    # Wordlist Generator
    "WordlistConfig",
    "LeetSpeakConverter",
    "CasePermutator",
    "SuffixAppender",
    "PatternGenerator",
    "CombinationGenerator",
    "WordlistGenerator",
    "wordlist_menu",
    
    # Password Policy
    "PolicyRule",
    "PasswordAnalysis",
    "CommonPatterns",
    "EntropyCalculator",
    "PasswordPolicy",
    "PasswordAnalyzer",
    "PasswordGenerator",
    "password_menu",
]
