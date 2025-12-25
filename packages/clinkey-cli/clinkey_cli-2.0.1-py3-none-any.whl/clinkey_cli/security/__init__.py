"""Security analysis engine for password strength evaluation.

Provides comprehensive password analysis including entropy calculation,
pattern detection, dictionary checking, breach detection, and compliance
validation.
"""

from clinkey_cli.security.analyzer import SecurityAnalyzer, analyze_password

__all__ = ["SecurityAnalyzer", "analyze_password"]
