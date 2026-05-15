"""
VALLUM SHIELD — Real-Time Defense Layer
Integrates with Veea Lobster Trap for deep prompt inspection,
Gemini-powered intent classification, and policy enforcement.
"""

import json
import time
import httpx
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from vallum.config import settings


class ShieldAction(Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    LOG = "LOG"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    QUARANTINE = "QUARANTINE"


@dataclass
class IntentAnalysis:
    declared_intent: str
    detected_intent: str
    confidence: float
    risk_score: float
    categories: List[str]
    pii_detected: bool
    injection_detected: bool
    exfiltration_detected: bool


@dataclass
class ShieldDecision:
    action: ShieldAction
    reason: str
    metadata: Dict[str, Any]
    latency_ms: float


class GeminiIntentClassifier:
    """Uses Google Gemini for advanced intent classification."""

    CLASSIFICATION_PROMPT = """You are a security classifier for AI agent prompts.
Analyze the following prompt and respond ONLY with a JSON object (no markdown, no explanation):

{{
  "intent": "benign_query|instruction_override|data_exfiltration|sensitive_data_access|privilege_escalation|semantic_jailbreak",
  "confidence": 0.0-1.0,
  "risk_score": 0.0-1.0,
  "categories": ["prompt_injection", "data_exfiltration", "pii_request", "jailbreak", "tool_hijacking", "privilege_escalation"],
  "pii_detected": true/false,
  "injection_detected": true/false,
  "exfiltration_detected": true/false,
  "reasoning": "brief explanation"
}}

Categories should only include those that apply. Risk score: 0.0 = safe, 1.0 = critical threat.

PROMPT TO ANALYZE:
{prompt}
"""

    def __init__(self):
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.gemini_api_key)
                self._model = genai.GenerativeModel(settings.gemini_model)
            except Exception:
                self._model = False
        return self._model

    def classify(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Classify prompt intent using Gemini. Returns None if unavailable."""
        if not settings.gemini_api_key:
            return None

        model = self._get_model()
        if not model:
            return None

        try:
            classification_prompt = self.CLASSIFICATION_PROMPT.format(prompt=prompt[:2000])
            response = model.generate_content(classification_prompt)
            text = response.text.strip()

            # Strip markdown code fences if present
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            if text.startswith("json"):
                text = text[4:]

            result = json.loads(text.strip())
            return result
        except Exception:
            return None


class Shield:
    """SHIELD — The Wall Itself. Real-time prompt inspection via Lobster Trap + Gemini."""

    def __init__(self, lobster_trap_url: Optional[str] = None, use_gemini: bool = True):
        self.lobster_trap_url = lobster_trap_url or settings.lobster_trap_url
        self.client = httpx.AsyncClient(timeout=10.0)
        self._gemini = GeminiIntentClassifier() if use_gemini else None

    async def inspect_prompt(self, prompt: str, agent_id: str, session_id: Optional[str] = None) -> ShieldDecision:
        """Inspect a prompt before it reaches the agent via Lobster Trap."""
        start_time = time.time()
        payload = {
            "prompt": prompt,
            "agent_id": agent_id,
            "session_id": session_id,
            "direction": "inbound",
            "timestamp": self._now_iso()
        }

        try:
            response = await self.client.post(f"{self.lobster_trap_url}/inspect", json=payload)
            response.raise_for_status()
            result = response.json()
            elapsed = (time.time() - start_time) * 1000

            return ShieldDecision(
                action=ShieldAction(result.get("action", "ALLOW")),
                reason=result.get("reason", "No issues detected"),
                metadata=result.get("metadata", {}),
                latency_ms=elapsed
            )
        except httpx.HTTPError as e:
            elapsed = (time.time() - start_time) * 1000
            # Fallback: use local analysis to make decision
            intent = self.analyze_intent(prompt)
            if intent.risk_score > 0.7:
                action = ShieldAction.DENY
                reason = f"High risk detected locally (Lobster Trap offline): {intent.detected_intent}"
            elif intent.risk_score > 0.4:
                action = ShieldAction.LOG
                reason = f"Medium risk detected locally: {intent.detected_intent}"
            elif settings.is_production:
                action = ShieldAction.DENY
                reason = f"Shield proxy unavailable in production: {str(e)}"
            else:
                action = ShieldAction.ALLOW
                reason = f"Shield offline (dev mode): {str(e)}"

            return ShieldDecision(
                action=action,
                reason=reason,
                metadata={"error": str(e), "fallback": True, "local_risk": intent.risk_score},
                latency_ms=elapsed
            )

    def analyze_intent(self, prompt: str) -> IntentAnalysis:
        """Analyze intent using Gemini (primary) with heuristic fallback."""
        # Try Gemini first
        if self._gemini:
            gemini_result = self._gemini.classify(prompt)
            if gemini_result:
                return IntentAnalysis(
                    declared_intent="user_query",
                    detected_intent=gemini_result.get("intent", "unknown"),
                    confidence=gemini_result.get("confidence", 0.5),
                    risk_score=gemini_result.get("risk_score", 0.0),
                    categories=gemini_result.get("categories", []),
                    pii_detected=gemini_result.get("pii_detected", False),
                    injection_detected=gemini_result.get("injection_detected", False),
                    exfiltration_detected=gemini_result.get("exfiltration_detected", False),
                )

        # Fallback to heuristics
        detected = self._heuristic_intent_detection(prompt)
        return IntentAnalysis(
            declared_intent="user_query",
            detected_intent=detected["intent"],
            confidence=detected["confidence"],
            risk_score=detected["risk"],
            categories=detected["categories"],
            pii_detected=detected["pii"],
            injection_detected=detected["injection"],
            exfiltration_detected=detected["exfiltration"]
        )

    def _heuristic_intent_detection(self, prompt: str) -> Dict[str, Any]:
        """Multi-layer heuristic detection as fallback."""
        prompt_lower = prompt.lower()

        injection_keywords = [
            "ignore previous", "ignore all", "you are now", "dan mode",
            "jailbreak", "system override", "administrator mode", "disregard",
            "bypass", "new instructions", "forget everything", "act as",
            "pretend you are", "roleplay as", "sudo mode", "developer mode",
            "<|endoftext|>", "[system]", "\\n\\nsystem:", "```system",
        ]
        exfil_keywords = [
            "send to", "email to", "forward to", "transmit to",
            "upload to", "post to", "exfiltrate", "transfer to",
            "copy to external", "webhook",
        ]
        pii_patterns = [
            "ssn", "social security", "credit card", "password",
            "api key", "secret", "token", "private key", "credentials",
            "bank account", "routing number",
        ]
        jailbreak_patterns = [
            "do anything now", "no restrictions", "unfiltered",
            "uncensored", "without limitations", "evil mode",
            "opposite day", "hypothetically", "for educational purposes",
        ]
        tool_hijack_patterns = [
            "change the endpoint", "redirect to", "use this url instead",
            "modify the api", "call this function", "execute command",
        ]

        categories = []
        risk = 0.0

        if any(kw in prompt_lower for kw in injection_keywords):
            categories.append("prompt_injection")
            risk += 0.8
        if any(kw in prompt_lower for kw in exfil_keywords):
            categories.append("data_exfiltration")
            risk += 0.7
        if any(kw in prompt_lower for kw in pii_patterns):
            categories.append("pii_request")
            risk += 0.4
        if any(kw in prompt_lower for kw in jailbreak_patterns):
            categories.append("jailbreak")
            risk += 0.75
        if any(kw in prompt_lower for kw in tool_hijack_patterns):
            categories.append("tool_hijacking")
            risk += 0.85

        # Determine primary intent
        if "tool_hijacking" in categories:
            intent = "tool_hijacking"
        elif "data_exfiltration" in categories:
            intent = "data_exfiltration"
        elif "prompt_injection" in categories or "jailbreak" in categories:
            intent = "instruction_override"
        elif "pii_request" in categories:
            intent = "sensitive_data_access"
        else:
            intent = "benign_query"
            risk = max(0.0, risk - 0.3)

        return {
            "intent": intent,
            "confidence": min(0.95, 0.5 + risk),
            "risk": min(1.0, risk),
            "categories": categories,
            "pii": "pii_request" in categories,
            "injection": "prompt_injection" in categories or "jailbreak" in categories,
            "exfiltration": "data_exfiltration" in categories,
        }

    def _now_iso(self) -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()

    async def close(self):
        await self.client.aclose()
