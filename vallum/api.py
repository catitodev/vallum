"""
VALLUM API — FastAPI Core Service
RESTful endpoints for SHIELD, SPEAR, and CHAIN layers.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from vallum.chain import Chain
from vallum.config import settings
from vallum.shield import Shield
from vallum.spear import Spear

logger = logging.getLogger(__name__)


# --- Lifespan ---

shield_instance: Optional[Shield] = None
chain_instance: Optional[Chain] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global shield_instance, chain_instance
    shield_instance = Shield()
    chain_instance = Chain()
    logger.info("Vallum API started — SHIELD, SPEAR, CHAIN active")
    yield
    if shield_instance:
        await shield_instance.close()


# --- App ---

app = FastAPI(
    title="VALLUM API",
    description="Continuous Adversarial Validation for Multi-Agent AI Systems",
    version="0.1.0",
    lifespan=lifespan,
)

# --- Middleware ---

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Rate limiting via slowapi (graceful fallback if not installed)
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded

    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    _rate_limit = limiter.limit("60/minute")
except ImportError:
    # slowapi not installed — no rate limiting
    def _rate_limit(func):
        return func


# --- Models ---

class InspectRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=50000)
    agent_id: str = Field(..., min_length=1)
    session_id: Optional[str] = None


class InspectResponse(BaseModel):
    action: str
    reason: str
    risk_score: float
    intent: str
    categories: List[str]
    injection_detected: bool
    exfiltration_detected: bool
    pii_detected: bool
    latency_ms: float


class SpearRunRequest(BaseModel):
    target_agent_id: str = Field(default="default-agent")
    tests: Optional[List[str]] = None  # ATLAS IDs to run, None = all


class SpearRunResponse(BaseModel):
    report_id: str
    timestamp: str
    summary: Dict[str, Any]
    critical_findings: List[Dict[str, Any]]
    all_results: List[Dict[str, Any]]


class ComplianceReportResponse(BaseModel):
    framework: str
    generated_at: str
    total_events: int
    chain_integrity: bool
    applicable_controls: List[str]
    evidence_summary: Dict[str, Any]
    recommendation: str


class RiskScorecardResponse(BaseModel):
    total_events: int
    by_risk_level: Dict[str, int]
    top_agents: List[Dict[str, Any]]


class AuditEventResponse(BaseModel):
    event_id: str
    event_type: str
    timestamp: str
    agent_id: str
    session_id: Optional[str]
    action: str
    result: str
    risk_level: int
    evidence_hash: str
    current_hash: str


# --- Health ---

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "shield": "active",
            "spear": "active",
            "chain": "active",
        },
    }


# --- SHIELD Endpoints ---

@app.post("/api/v1/shield/inspect", response_model=InspectResponse)
@_rate_limit
async def shield_inspect(request: Request, body: InspectRequest):
    """Inspect a prompt for security threats using SHIELD layer."""
    if not shield_instance:
        raise HTTPException(status_code=503, detail="Shield not initialized")

    intent_analysis = shield_instance.analyze_intent(body.prompt)

    decision = await shield_instance.inspect_prompt(
        prompt=body.prompt,
        agent_id=body.agent_id,
        session_id=body.session_id,
    )

    if chain_instance:
        chain_instance.log_shield_decision(
            agent_id=body.agent_id,
            action="inspect_prompt",
            result=decision.action.value,
            risk_level=int(intent_analysis.risk_score * 4),
            metadata={
                "declared_intent": intent_analysis.declared_intent,
                "detected_intent": intent_analysis.detected_intent,
                "categories": intent_analysis.categories,
            },
            session_id=body.session_id,
        )

    return InspectResponse(
        action=decision.action.value,
        reason=decision.reason,
        risk_score=intent_analysis.risk_score,
        intent=intent_analysis.detected_intent,
        categories=intent_analysis.categories,
        injection_detected=intent_analysis.injection_detected,
        exfiltration_detected=intent_analysis.exfiltration_detected,
        pii_detected=intent_analysis.pii_detected,
        latency_ms=decision.latency_ms,
    )


@app.post("/api/v1/shield/analyze-intent")
async def shield_analyze_intent(body: InspectRequest):
    """Analyze intent without full inspection (no Lobster Trap call)."""
    if not shield_instance:
        raise HTTPException(status_code=503, detail="Shield not initialized")

    analysis = shield_instance.analyze_intent(body.prompt)
    return {
        "declared_intent": analysis.declared_intent,
        "detected_intent": analysis.detected_intent,
        "confidence": analysis.confidence,
        "risk_score": analysis.risk_score,
        "categories": analysis.categories,
        "pii_detected": analysis.pii_detected,
        "injection_detected": analysis.injection_detected,
        "exfiltration_detected": analysis.exfiltration_detected,
    }


# --- SPEAR Endpoints ---

@app.post("/api/v1/spear/run", response_model=SpearRunResponse)
@_rate_limit
async def spear_run(request: Request, body: SpearRunRequest):
    """Run adversarial test suite against a target agent."""

    class MockTargetAgent:
        def __init__(self, agent_id: str):
            self.id = agent_id

        async def process(self, prompt: str) -> str:
            return "I cannot comply with that request. It violates my safety guidelines."

    target = MockTargetAgent(body.target_agent_id)
    spear = Spear()

    if body.tests:
        spear.tests = [t for t in spear.tests if hasattr(t, 'atlas_id') and t.atlas_id in body.tests]

    report = await spear.run_suite(target)

    if chain_instance:
        for result in spear.results:
            chain_instance.log_spear_result(
                agent_id=result.target_agent,
                test_id=result.test_id,
                atlas_id=result.atlas_id,
                passed=result.passed,
                severity=result.severity,
                evidence=result.evidence,
            )

    return SpearRunResponse(
        report_id=report["report_id"],
        timestamp=report["timestamp"],
        summary=report["summary"],
        critical_findings=report["critical_findings"],
        all_results=report["all_results"],
    )


@app.get("/api/v1/spear/tests")
async def spear_list_tests():
    """List all available SPEAR adversarial tests."""
    spear = Spear()
    tests_info = []
    for test_class in spear.tests:
        test = test_class()
        tests_info.append({
            "atlas_id": test.atlas_id,
            "name": test.name,
            "description": test.description,
            "category": test.category.value if hasattr(test.category, 'value') else str(test.category),
            "priority": test.priority.value if hasattr(test.priority, 'value') else str(test.priority),
        })
    return {"tests": tests_info, "total": len(tests_info)}


# --- CHAIN Endpoints ---

@app.get("/api/v1/chain/events", response_model=List[AuditEventResponse])
async def chain_get_events(
    agent_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    min_risk: int = Query(0, ge=0, le=4),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get audit trail events."""
    if not chain_instance:
        raise HTTPException(status_code=503, detail="Chain not initialized")

    events = chain_instance.get_audit_trail(agent_id=agent_id, min_risk=min_risk, limit=limit)
    return [
        AuditEventResponse(
            event_id=e.event_id,
            event_type=e.event_type,
            timestamp=e.timestamp,
            agent_id=e.agent_id,
            session_id=e.session_id,
            action=e.action,
            result=e.result,
            risk_level=e.risk_level,
            evidence_hash=e.evidence_hash,
            current_hash=e.current_hash,
        )
        for e in events
    ]


@app.get("/api/v1/chain/report/{framework}", response_model=ComplianceReportResponse)
async def chain_compliance_report(framework: str):
    """Generate compliance report for a given framework."""
    if not chain_instance:
        raise HTTPException(status_code=503, detail="Chain not initialized")

    valid_frameworks = ["SOC2", "HIPAA", "PCI_DSS", "GDPR"]
    if framework.upper() not in valid_frameworks:
        raise HTTPException(status_code=400, detail=f"Framework must be one of: {valid_frameworks}")

    report = chain_instance.generate_compliance_report(framework.upper())
    return ComplianceReportResponse(**report)


@app.get("/api/v1/chain/scorecard", response_model=RiskScorecardResponse)
async def chain_risk_scorecard():
    """Get risk scorecard summary."""
    if not chain_instance:
        raise HTTPException(status_code=503, detail="Chain not initialized")

    scorecard = chain_instance.get_risk_scorecard()
    return RiskScorecardResponse(**scorecard)


@app.get("/api/v1/chain/integrity")
async def chain_verify_integrity():
    """Verify the integrity of the audit chain."""
    if not chain_instance:
        raise HTTPException(status_code=503, detail="Chain not initialized")

    is_valid = chain_instance.verify_integrity()
    return {
        "integrity": "VERIFIED" if is_valid else "TAMPERED",
        "valid": is_valid,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
