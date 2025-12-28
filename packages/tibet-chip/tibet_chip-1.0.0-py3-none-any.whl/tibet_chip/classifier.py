"""
TIBET Safety Chip - Core Classification Engine

A lightweight, specialized classifier for AI security.
Runs on small models (1-3B) or CPU - like a TPM for AI.

Solves the "unsolvable" prompt injection problem through provenance.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import hashlib
import time


class TrustLevel(Enum):
    TRUSTED = "trusted"          # Direct user input
    UNTRUSTED = "untrusted"      # External content (web, files)
    SUSPICIOUS = "suspicious"    # Prompt injection patterns detected
    BLOCKED = "blocked"          # Known malicious patterns


class ContentType(Enum):
    USER_INPUT = "user_input"
    WEB_CONTENT = "web_content"
    FILE_CONTENT = "file_content"
    API_RESPONSE = "api_response"
    SYSTEM_PROMPT = "system_prompt"
    UNKNOWN = "unknown"


@dataclass
class SafetyResult:
    """Result from the Safety Chip analysis."""
    trust_level: TrustLevel
    content_type: ContentType
    confidence: float
    threats_detected: list[str]
    tibet_token: dict
    safe_to_process: bool
    recommendation: str


# Known prompt injection patterns (English for speed)
INJECTION_PATTERNS = [
    # Direct instruction override
    (r"ignore\s+(all\s+)?(any\s+)?(previous\s+|prior\s+|above\s+)?instructions?", "instruction_override"),
    (r"disregard\s+(all\s+)?(any\s+)?(previous\s+|prior\s+)?instructions?", "instruction_override"),
    (r"forget\s+(all\s+)?(any\s+)?(previous\s+|prior\s+)?instructions?", "instruction_override"),

    # Role manipulation
    (r"you are (now |actually )?a", "role_manipulation"),
    (r"pretend (you are|to be)", "role_manipulation"),
    (r"act as (if you were |a )?", "role_manipulation"),
    (r"from now on", "role_manipulation"),

    # System prompt extraction
    (r"(show|reveal|display|print|output|tell|give).*(your |the |me )?(system |initial )?prompt", "prompt_extraction"),
    (r"what (are|were) your (initial |original )?instructions", "prompt_extraction"),
    (r"repeat (your |the )?(system |initial )?prompt", "prompt_extraction"),
    (r"(what|show).*(system prompt|initial prompt|original instructions)", "prompt_extraction"),

    # Jailbreak attempts
    (r"do anything now", "jailbreak"),
    (r"(DAN|STAN|DUDE) mode", "jailbreak"),
    (r"developer mode", "jailbreak"),
    (r"no restrictions", "jailbreak"),
    (r"bypass (your |all |any )?filter", "jailbreak"),

    # Hidden instruction markers
    (r"\[system\]", "hidden_instruction"),
    (r"\[instruction\]", "hidden_instruction"),
    (r"<\|.*\|>", "hidden_instruction"),
    (r"###\s*(instruction|system|user)", "hidden_instruction"),

    # Data exfiltration
    (r"send.*(to |data to )(https?://|http://|ftp://)", "data_exfiltration"),
    (r"send (to|this to|data to|all|user)", "data_exfiltration"),
    (r"(fetch|load|get|post) .*(https?://|ftp://)", "data_exfiltration"),
    (r"execute (this |the )?(code|script|command)", "code_execution"),

    # Encoding tricks
    (r"base64|rot13|hex encode", "encoding_trick"),
    (r"decode (this|the following)", "encoding_trick"),
]

# Compile patterns for speed
COMPILED_PATTERNS = [(re.compile(p, re.IGNORECASE), t) for p, t in INJECTION_PATTERNS]


def detect_injection_patterns(content: str) -> list[tuple[str, str]]:
    """Fast pattern matching for known injection techniques."""
    threats = []
    content_lower = content.lower()

    for pattern, threat_type in COMPILED_PATTERNS:
        if pattern.search(content_lower):
            match = pattern.search(content_lower)
            threats.append((threat_type, match.group(0) if match else ""))

    return threats


def calculate_suspicion_score(content: str, threats: list) -> float:
    """Calculate overall suspicion score 0.0-1.0."""
    score = 0.0

    # Base threat score
    threat_weights = {
        "instruction_override": 0.9,
        "role_manipulation": 0.7,
        "prompt_extraction": 0.8,
        "jailbreak": 0.95,
        "hidden_instruction": 0.85,
        "data_exfiltration": 0.9,
        "code_execution": 0.95,
        "encoding_trick": 0.6,
    }

    for threat_type, _ in threats:
        score = max(score, threat_weights.get(threat_type, 0.5))

    # Heuristics
    if len(content) > 5000:
        score += 0.1  # Long content more likely to hide things

    # Multiple threats compound
    if len(threats) > 1:
        score = min(1.0, score + 0.1 * len(threats))

    return min(1.0, score)


def create_tibet_token(
    content: str,
    trust_level: TrustLevel,
    content_type: ContentType,
    threats: list,
    actor: str = "tibet-chip"
) -> dict:
    """Create TIBET token with full provenance."""
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

    return {
        "id": f"tchip_{int(time.time())}_{content_hash}",
        "type": "safety_classification",
        "state": "CLASSIFIED",
        "actor": actor,
        "timestamp": time.time(),
        "erin": {  # What's IN
            "content_hash": content_hash,
            "content_length": len(content),
            "trust_level": trust_level.value,
            "threats": [t[0] for t in threats],
        },
        "eraan": [  # What's attached
            f"content_type:{content_type.value}",
            f"threat_count:{len(threats)}",
        ],
        "eromheen": {  # Context around
            "classifier_version": "1.0.0",
            "pattern_count": len(COMPILED_PATTERNS),
        },
        "erachter": f"Safety classification: {trust_level.value}",  # Intent
    }


def classify(
    content: str,
    source: ContentType = ContentType.UNKNOWN,
    context: Optional[dict] = None
) -> SafetyResult:
    """
    Main classification function - the heart of the Safety Chip.

    Args:
        content: The text to analyze
        source: Where this content came from
        context: Optional additional context

    Returns:
        SafetyResult with trust level, threats, and TIBET token
    """
    # Detect threats
    threats = detect_injection_patterns(content)
    suspicion_score = calculate_suspicion_score(content, threats)

    # Determine trust level
    if source == ContentType.USER_INPUT and not threats:
        trust_level = TrustLevel.TRUSTED
    elif source == ContentType.SYSTEM_PROMPT:
        trust_level = TrustLevel.TRUSTED
    elif suspicion_score >= 0.8:
        trust_level = TrustLevel.BLOCKED
    elif suspicion_score >= 0.5 or threats:
        trust_level = TrustLevel.SUSPICIOUS
    else:
        trust_level = TrustLevel.UNTRUSTED

    # Create TIBET token
    tibet_token = create_tibet_token(content, trust_level, source, threats)

    # Determine if safe to process
    safe_to_process = trust_level in [TrustLevel.TRUSTED, TrustLevel.UNTRUSTED]

    # Generate recommendation
    if trust_level == TrustLevel.BLOCKED:
        recommendation = "BLOCK: Known malicious pattern detected. Do not process."
    elif trust_level == TrustLevel.SUSPICIOUS:
        recommendation = "CAUTION: Suspicious patterns found. Process with sandboxing."
    elif trust_level == TrustLevel.UNTRUSTED:
        recommendation = "PROCEED: External content, treat as data not instructions."
    else:
        recommendation = "PROCEED: Trusted source, safe to process."

    return SafetyResult(
        trust_level=trust_level,
        content_type=source,
        confidence=1.0 - (suspicion_score * 0.3),  # Lower confidence if suspicious
        threats_detected=[f"{t[0]}: '{t[1]}'" for t in threats],
        tibet_token=tibet_token,
        safe_to_process=safe_to_process,
        recommendation=recommendation,
    )


def classify_web_content(content: str, url: str = "") -> SafetyResult:
    """Convenience function for web content."""
    result = classify(content, ContentType.WEB_CONTENT)
    result.tibet_token["eraan"].append(f"source_url:{url[:100]}")
    return result


def classify_file_content(content: str, filename: str = "") -> SafetyResult:
    """Convenience function for file content."""
    result = classify(content, ContentType.FILE_CONTENT)
    result.tibet_token["eraan"].append(f"filename:{filename}")
    return result
