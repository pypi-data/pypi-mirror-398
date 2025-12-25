"""Main security analyzer coordinating all analysis components."""

from typing import Any

from clinkey_cli.security.breach import analyze_breach
from clinkey_cli.security.compliance import validate_compliance
from clinkey_cli.security.context import analyze_context
from clinkey_cli.security.dictionary import analyze_dictionary
from clinkey_cli.security.entropy import get_entropy_score
from clinkey_cli.security.patterns import analyze_patterns


class SecurityAnalyzer:
    """Coordinate all security analysis components.

    Combines entropy, pattern, dictionary, breach, context, and compliance
    analysis into a unified security assessment.

    Methods
    -------
    analyze(password: str, **options) -> dict
        Perform comprehensive security analysis.
    """

    def __init__(self):
        """Initialize security analyzer."""
        pass

    def analyze(
        self,
        password: str,
        check_breach: bool = False,
        check_dictionary: bool = True,
        check_patterns: bool = True,
    ) -> dict[str, Any]:
        """Analyze password security.

        Parameters
        ----------
        password : str
            Password to analyze.
        check_breach : bool, default False
            Check against breach databases.
        check_dictionary : bool, default True
            Check against common password dictionaries.
        check_patterns : bool, default True
            Detect security-weakening patterns.

        Returns
        -------
        dict
            Comprehensive security analysis results.
        """
        # Entropy analysis (always performed)
        entropy = get_entropy_score(password)

        # Pattern analysis (optional)
        patterns = analyze_patterns(password) if check_patterns else {}

        # Dictionary analysis (optional)
        dictionary = analyze_dictionary(password) if check_dictionary else {}

        # Breach check (async, not supported in sync method)
        breach = {}

        # Context analysis (always performed)
        context = analyze_context(password)

        # Compliance validation (always performed)
        compliance = validate_compliance(password)

        # Calculate overall strength score
        strength_score = self._calculate_strength_score(
            entropy, patterns, dictionary, breach, context
        )

        # Determine strength label
        strength_label = self._get_strength_label(strength_score)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            entropy, patterns, dictionary, breach, compliance, strength_score
        )

        return {
            "entropy": entropy,
            "patterns": patterns,
            "dictionary": dictionary,
            "breach": breach,
            "context": context,
            "compliance": compliance,
            "strength_score": strength_score,
            "strength_label": strength_label,
            "recommendations": recommendations,
        }

    async def analyze_async(
        self,
        password: str,
        check_breach: bool = False,
        check_dictionary: bool = True,
        check_patterns: bool = True,
    ) -> dict[str, Any]:
        """Analyze password security (async version with breach check).

        Parameters
        ----------
        password : str
            Password to analyze.
        check_breach : bool, default False
            Check against breach databases.
        check_dictionary : bool, default True
            Check against common password dictionaries.
        check_patterns : bool, default True
            Detect security-weakening patterns.

        Returns
        -------
        dict
            Comprehensive security analysis results.
        """
        # Entropy analysis (always performed)
        entropy = get_entropy_score(password)

        # Pattern analysis (optional)
        patterns = analyze_patterns(password) if check_patterns else {}

        # Dictionary analysis (optional)
        dictionary = analyze_dictionary(password) if check_dictionary else {}

        # Breach check (async, optional)
        breach = await analyze_breach(password) if check_breach else {}

        # Context analysis (always performed)
        context = analyze_context(password)

        # Compliance validation (always performed)
        compliance = validate_compliance(password)

        # Calculate overall strength score
        strength_score = self._calculate_strength_score(
            entropy, patterns, dictionary, breach, context
        )

        # Determine strength label
        strength_label = self._get_strength_label(strength_score)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            entropy, patterns, dictionary, breach, compliance, strength_score
        )

        return {
            "entropy": entropy,
            "patterns": patterns,
            "dictionary": dictionary,
            "breach": breach,
            "context": context,
            "compliance": compliance,
            "strength_score": strength_score,
            "strength_label": strength_label,
            "recommendations": recommendations,
        }

    def _calculate_strength_score(
        self,
        entropy: dict,
        patterns: dict,
        dictionary: dict,
        breach: dict,
        context: dict,
    ) -> int:
        """Calculate overall strength score (0-100).

        Parameters
        ----------
        entropy : dict
            Entropy analysis results.
        patterns : dict
            Pattern analysis results.
        dictionary : dict
            Dictionary analysis results.
        breach : dict
            Breach check results.
        context : dict
            Context analysis results.

        Returns
        -------
        int
            Strength score from 0 (very weak) to 100 (very strong).
        """
        # Base score from charset entropy
        charset_entropy = entropy.get("charset_entropy", 0)
        base_score = min(charset_entropy * 1.5, 100)

        # Deduct for patterns
        if patterns:
            pattern_penalty = patterns.get("entropy_reduction", 0)
            base_score -= pattern_penalty

        # Deduct for dictionary matches
        if dictionary:
            dict_penalty = dictionary.get("score_penalty", 0)
            base_score -= dict_penalty

        # Deduct for breaches
        if breach:
            breach_penalty = breach.get("score_penalty", 0)
            base_score -= breach_penalty

        # Adjust for context mixing
        if context:
            mixing_score = context.get("mixing_score", 50)
            # Boost score slightly for good mixing (max +10)
            mixing_bonus = max(0, (mixing_score - 60) / 4)
            base_score += mixing_bonus

        # Ensure score is in range [0, 100]
        return max(0, min(100, int(base_score)))

    def _get_strength_label(self, score: int) -> str:
        """Get human-readable strength label.

        Parameters
        ----------
        score : int
            Strength score 0-100.

        Returns
        -------
        str
            Strength label.
        """
        if score < 20:
            return "Very Weak"
        elif score < 40:
            return "Weak"
        elif score < 60:
            return "Moderate"
        elif score < 80:
            return "Strong"
        else:
            return "Very Strong"

    def _generate_recommendations(
        self,
        entropy: dict,
        patterns: dict,
        dictionary: dict,
        breach: dict,
        compliance: dict,
        score: int,
    ) -> list[str]:
        """Generate actionable security recommendations.

        Parameters
        ----------
        entropy : dict
            Entropy analysis.
        patterns : dict
            Pattern analysis.
        dictionary : dict
            Dictionary analysis.
        breach : dict
            Breach check.
        compliance : dict
            Compliance validation.
        score : int
            Overall strength score.

        Returns
        -------
        list[str]
            List of recommendations.
        """
        recommendations = []

        # Breach warning (highest priority)
        if breach and breach.get("is_breached"):
            count = breach.get("breach_count", 0)
            recommendations.append(
                f"⚠️  PASSWORD COMPROMISED: Found in {count:,} data breaches. Change immediately!"
            )

        # Dictionary warnings
        if dictionary and dictionary.get("is_common"):
            recommendations.append(
                "Avoid common passwords - use a password generator instead"
            )
        elif dictionary and dictionary.get("word_count", 0) > 0:
            recommendations.append(
                "Avoid dictionary words in passwords"
            )

        # Length recommendations
        length = entropy.get("length", 0)
        if length < 12:
            recommendations.append(
                f"Increase length to at least 12 characters (current: {length})"
            )
        elif length < 16:
            recommendations.append(
                f"Consider increasing length to 16+ characters (current: {length})"
            )

        # Character set recommendations
        charset_size = entropy.get("charset_size", 0)
        if charset_size < 62:
            recommendations.append(
                "Use a mix of uppercase, lowercase, digits, and symbols"
            )

        # Pattern recommendations
        if patterns and patterns.get("pattern_count", 0) > 0:
            count = patterns["pattern_count"]
            recommendations.append(
                f"Avoid predictable patterns ({count} detected)"
            )

        # Compliance recommendations
        if compliance and not compliance.get("overall_compliant"):
            nist = compliance.get("nist", {})
            owasp = compliance.get("owasp", {})

            if not nist.get("compliant"):
                recommendations.append(
                    "Does not meet NIST SP 800-63B guidelines"
                )
            if not owasp.get("compliant"):
                recommendations.append(
                    "Does not meet OWASP password recommendations"
                )

        # Overall score recommendation
        if score < 60:
            recommendations.append(
                "Consider using a password generator for stronger passwords"
            )

        return recommendations


def analyze_password(
    password: str,
    check_breach: bool = False,
    check_dictionary: bool = True,
    check_patterns: bool = True,
) -> dict[str, Any]:
    """Convenience function for password analysis.

    Parameters
    ----------
    password : str
        Password to analyze.
    check_breach : bool, default False
        Check against breach databases.
    check_dictionary : bool, default True
        Check against common password dictionaries.
    check_patterns : bool, default True
        Detect security-weakening patterns.

    Returns
    -------
    dict
        Security analysis results.

    Examples
    --------
    >>> result = analyze_password("MyPassword123")
    >>> result["strength_score"]
    45
    """
    analyzer = SecurityAnalyzer()
    return analyzer.analyze(
        password,
        check_breach=check_breach,
        check_dictionary=check_dictionary,
        check_patterns=check_patterns,
    )
