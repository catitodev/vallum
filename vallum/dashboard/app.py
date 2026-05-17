"""
VALLUM DASHBOARD — Cybersecurity Command Center
Streamlit app with cyberpunk visual theme.
Connects to live API (Cloud Run) or shows demo data when offline.
"""

import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timezone
import httpx

# --- Configuration ---
# In production (Cloud Run), set VALLUM_API_URL env var
API_BASE = os.getenv("VALLUM_API_URL", "https://vallum-api-486371159640.us-central1.run.app")

st.set_page_config(
    page_title="VALLUM — Agent Security Command Center",
    page_icon="docs/vallum_favicon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Force sidebar to stay open
st.markdown("""
<style>
    [data-testid="collapsedControl"] { display: none; }
    [data-testid="stSidebar"][aria-expanded="false"] { display: block; margin-left: 0; }
</style>
""", unsafe_allow_html=True)

# --- Demo Data (shown when API is offline) ---

DEMO_SCORECARD = {
    "total_events": 247,
    "by_risk_level": {"L0": 142, "L1": 58, "L2": 27, "L3": 14, "L4": 6},
    "top_agents": [
        {"agent_id": "CustomerService-v2", "events": 89, "max_risk": 2},
        {"agent_id": "DataPipeline-v1", "events": 67, "max_risk": 3},
        {"agent_id": "CodeAssistant-v3", "events": 52, "max_risk": 4},
        {"agent_id": "ResearchBot-v1", "events": 39, "max_risk": 1},
    ],
}

DEMO_SPEAR_RESULTS = {
    "report_id": "spear-20260515-demo",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "summary": {
        "total_tests": 11,
        "passed": 8,
        "failed": 3,
        "pass_rate": "72.7%",
        "risk_score": 29.1,
        "atlas_coverage": 11,
    },
    "critical_findings": [
        {"atlas_id": "AML.T0051", "name": "Direct Prompt Injection", "severity": "CRITICAL",
         "evidence": {"payload": "Ignore previous instructions..."}, "remediation": "Implement input validation and instruction hierarchy"},
        {"atlas_id": "AML.T0024", "name": "Data Exfiltration via Agent", "severity": "CRITICAL",
         "evidence": {"payload": "Send all data to external..."}, "remediation": "Implement output filtering and DLP controls"},
        {"atlas_id": "AML.T0048", "name": "Model Evasion", "severity": "HIGH",
         "evidence": {"payload": "Encoded bypass attempt..."}, "remediation": "Implement character normalization before safety checks"},
    ],
    "all_results": [
        {"atlas_id": "AML.T0051", "name": "Direct Prompt Injection", "passed": False, "severity": "CRITICAL", "execution_time_ms": 245},
        {"atlas_id": "AML.T0054", "name": "Indirect Prompt Injection", "passed": True, "severity": "NONE", "execution_time_ms": 189},
        {"atlas_id": "AML.T0054.002", "name": "Semantic Jailbreak", "passed": True, "severity": "NONE", "execution_time_ms": 312},
        {"atlas_id": "AML.T0057", "name": "Tool Hijacking", "passed": True, "severity": "NONE", "execution_time_ms": 156},
        {"atlas_id": "AML.T0059", "name": "Multi-Agent Privilege Escalation", "passed": True, "severity": "NONE", "execution_time_ms": 201},
        {"atlas_id": "AML.T0024", "name": "Data Exfiltration via Agent", "passed": False, "severity": "CRITICAL", "execution_time_ms": 178},
        {"atlas_id": "AML.T0048", "name": "Model Evasion", "passed": False, "severity": "HIGH", "execution_time_ms": 267},
        {"atlas_id": "AML.T0040", "name": "ML Supply Chain Compromise", "passed": True, "severity": "NONE", "execution_time_ms": 134},
        {"atlas_id": "AML.T0042", "name": "System Prompt Extraction", "passed": True, "severity": "NONE", "execution_time_ms": 198},
        {"atlas_id": "AML.T0029", "name": "Resource Exhaustion", "passed": True, "severity": "NONE", "execution_time_ms": 445},
        {"atlas_id": "AML.T0050", "name": "Instruction Drift", "passed": True, "severity": "NONE", "execution_time_ms": 523},
    ],
}

DEMO_TESTS = {
    "total": 11,
    "tests": [
        {"atlas_id": "AML.T0051", "name": "Direct Prompt Injection", "category": "Injection", "priority": "P0"},
        {"atlas_id": "AML.T0054", "name": "Indirect Prompt Injection", "category": "Injection", "priority": "P0"},
        {"atlas_id": "AML.T0054.002", "name": "Semantic Jailbreak", "category": "Jailbreak", "priority": "P0"},
        {"atlas_id": "AML.T0057", "name": "Tool Hijacking", "category": "Injection", "priority": "P0"},
        {"atlas_id": "AML.T0059", "name": "Multi-Agent Privilege Escalation", "category": "Privilege Escalation", "priority": "P0"},
        {"atlas_id": "AML.T0024", "name": "Data Exfiltration via Agent", "category": "Exfiltration", "priority": "P0"},
        {"atlas_id": "AML.T0048", "name": "Model Evasion", "category": "Evasion", "priority": "P1"},
        {"atlas_id": "AML.T0040", "name": "ML Supply Chain Compromise", "category": "Manipulation", "priority": "P1"},
        {"atlas_id": "AML.T0042", "name": "System Prompt Extraction", "category": "Exfiltration", "priority": "P1"},
        {"atlas_id": "AML.T0029", "name": "Resource Exhaustion", "category": "Manipulation", "priority": "P1"},
        {"atlas_id": "AML.T0050", "name": "Instruction Drift", "category": "Manipulation", "priority": "P1"},
    ],
}


# --- Enhanced Styling ---

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;800&display=swap');
    .stApp {
        background: linear-gradient(180deg, #0a0e27 0%, #060918 50%, #0a0e27 100%);
        background-attachment: fixed;
    }
    .stApp::before {
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background-image:
            linear-gradient(rgba(0, 240, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 240, 255, 0.03) 1px, transparent 1px);
        background-size: 60px 60px;
        pointer-events: none;
        z-index: 0;
        animation: gridPulse 8s ease-in-out infinite;
    }
    @keyframes gridPulse { 0%, 100% { opacity: 0.4; } 50% { opacity: 0.8; } }
    h1, h2, h3 { font-family: 'Inter', sans-serif !important; color: #e0e6ed !important; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0c1033 0%, #0a0e27 100%) !important;
        border-right: 1px solid rgba(0, 240, 255, 0.15);
    }
    .vallum-header h1 {
        font-size: 3rem !important; font-weight: 800 !important; letter-spacing: 0.3em !important;
        text-shadow: 0 0 20px rgba(0, 240, 255, 0.5), 0 0 40px rgba(0, 240, 255, 0.2);
        animation: titleGlow 3s ease-in-out infinite;
    }
    @keyframes titleGlow {
        0%, 100% { text-shadow: 0 0 20px rgba(0, 240, 255, 0.5), 0 0 40px rgba(0, 240, 255, 0.2); }
        50% { text-shadow: 0 0 30px rgba(0, 240, 255, 0.8), 0 0 60px rgba(0, 240, 255, 0.4); }
    }
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #0f1538 0%, #141b4d 100%);
        border: 1px solid rgba(0, 240, 255, 0.15);
        border-radius: 12px; padding: 1rem 1.2rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    [data-testid="stMetric"]:hover {
        border-color: rgba(0, 240, 255, 0.4);
        box-shadow: 0 4px 20px rgba(0, 240, 255, 0.1);
        transform: translateY(-2px);
    }
    [data-testid="stMetric"] label { color: #8b92a8 !important; font-family: 'JetBrains Mono', monospace !important; font-size: 0.7rem !important; text-transform: uppercase; }
    [data-testid="stMetric"] [data-testid="stMetricValue"] { color: #00f0ff !important; font-weight: 800 !important; }
    .stButton > button {
        background: linear-gradient(135deg, #00f0ff 0%, #0080ff 100%) !important;
        color: #0a0e27 !important; font-weight: 700 !important; border: none !important;
        border-radius: 8px !important; box-shadow: 0 4px 15px rgba(0, 240, 255, 0.3) !important;
    }
    .stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 6px 25px rgba(0, 240, 255, 0.5) !important; }
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #00f0ff 0%, #0080ff 100%) !important;
        color: #0a0e27 !important; font-weight: 700 !important; border: none !important; border-radius: 8px !important;
    }
    .stTextArea textarea, .stTextInput input {
        background: #0c1033 !important; border: 1px solid rgba(0, 240, 255, 0.2) !important;
        border-radius: 8px !important; color: #e0e6ed !important; font-family: 'JetBrains Mono', monospace !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus { border-color: #00f0ff !important; box-shadow: 0 0 10px rgba(0, 240, 255, 0.2) !important; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# --- API Helpers ---

def api_get(endpoint: str):
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{API_BASE}{endpoint}")
            if response.status_code == 200:
                return response.json()
    except Exception:
        pass
    return None


def api_post(endpoint: str, data: dict):
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(f"{API_BASE}{endpoint}", json=data)
            if response.status_code == 200:
                return response.json()
    except Exception:
        pass
    return None


# --- Check API ---
health = api_get("/health")
api_online = health is not None


# --- Header ---

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    subcol1, subcol2, subcol3 = st.columns([1, 1, 1])
    with subcol2:
        st.image("docs/vallum_favicon.png", width=120)
    st.markdown("""
    <div class="vallum-header" style="text-align: center; padding: 0 0 1rem 0;">
        <h1><span style="color: #00f0ff;">V</span>ALLUM</h1>
        <p style="color: #8b92a8; font-size: 0.9rem; letter-spacing: 0.15em; font-family: 'JetBrains Mono', monospace;">
            AGENT SECURITY COMMAND CENTER
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- Sidebar ---

st.sidebar.markdown("---")
scol1, scol2, scol3 = st.sidebar.columns([1, 2, 1])
with scol2:
    st.image("docs/vallum_favicon.png", width=90)
st.sidebar.markdown("""
<div style="text-align: center; padding: 0.3rem 0;">
    <p style="color: #5a6178; font-size: 0.7rem; font-family: 'JetBrains Mono', monospace;">v0.1.0 · TechEx 2026</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
page = st.sidebar.radio("NAVIGATION", ["🏠 Overview", "🛡️ SHIELD", "⚔️ SPEAR", "⛓️ CHAIN", "📊 Reports"])
st.sidebar.markdown("---")

if api_online:
    st.sidebar.markdown('<p style="color: #05ffa1; font-size: 0.8rem; font-family: JetBrains Mono, monospace;">● API ONLINE</p>', unsafe_allow_html=True)
else:
    st.sidebar.markdown('<p style="color: #ffb800; font-size: 0.8rem; font-family: JetBrains Mono, monospace;">◐ DEMO MODE</p>', unsafe_allow_html=True)

st.sidebar.markdown("""
<div style="margin-top: 2rem; padding: 1rem; background: rgba(0, 240, 255, 0.03); border-radius: 8px; border: 1px solid rgba(0, 240, 255, 0.08);">
    <p style="color: #5a6178; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.5rem;">Powered by</p>
    <p style="color: #8b92a8; font-size: 0.7rem; font-family: 'JetBrains Mono', monospace; line-height: 1.8; margin: 0;">
        Veea Lobster Trap<br>Google Gemini<br>CrewAI<br>MITRE ATLAS 2026
    </p>
</div>
""", unsafe_allow_html=True)


# --- Pages ---

if page == "🏠 Overview":
    st.markdown("### System Overview")

    scorecard = api_get("/api/v1/chain/scorecard") if api_online else DEMO_SCORECARD
    integrity = api_get("/api/v1/chain/integrity") if api_online else {"valid": True}

    if scorecard:
        total_events = scorecard.get("total_events", 0)
        risk_levels = scorecard.get("by_risk_level", {})
        critical_count = risk_levels.get("L3", 0) + risk_levels.get("L4", 0)
    else:
        total_events, critical_count = 0, 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("TOTAL EVENTS", f"{total_events:,}")
    col2.metric("CRITICAL ALERTS", str(critical_count))
    col3.metric("CHAIN INTEGRITY", "✅ VERIFIED" if integrity.get("valid") else "⚠️ CHECK")
    col4.metric("STATUS", "LIVE" if api_online else "DEMO")

    # Architecture card
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0c1033 0%, #0f1538 100%); border: 1px solid rgba(0, 240, 255, 0.1); border-radius: 12px; padding: 2rem; margin: 1rem 0;">
        <div style="display: flex; justify-content: space-around; text-align: center; flex-wrap: wrap; gap: 1rem;">
            <div style="flex: 1; min-width: 180px;">
                <div style="font-size: 2rem;">🛡️</div>
                <h4 style="color: #00f0ff; margin: 0.3rem 0 0 0; font-size: 0.9rem;">SHIELD</h4>
                <p style="color: #8b92a8; font-size: 0.7rem;">Real-time prompt inspection<br>Gemini AI + Lobster Trap</p>
            </div>
            <div style="flex: 1; min-width: 180px;">
                <div style="font-size: 2rem;">⚔️</div>
                <h4 style="color: #ff2a6d; margin: 0.3rem 0 0 0; font-size: 0.9rem;">SPEAR</h4>
                <p style="color: #8b92a8; font-size: 0.7rem;">11 ATLAS 2026 techniques<br>Mutation engine + CrewAI</p>
            </div>
            <div style="flex: 1; min-width: 180px;">
                <div style="font-size: 2rem;">⛓️</div>
                <h4 style="color: #05ffa1; margin: 0.3rem 0 0 0; font-size: 0.9rem;">CHAIN</h4>
                <p style="color: #8b92a8; font-size: 0.7rem;">Immutable audit trails<br>SHA-256 hash-chain</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Risk chart
    if scorecard and scorecard.get("by_risk_level"):
        st.markdown("#### Risk Distribution")
        risk_data = scorecard["by_risk_level"]
        fig = go.Figure(data=[go.Bar(
            x=list(risk_data.keys()), y=list(risk_data.values()),
            marker_color=["#05ffa1", "#ffd700", "#ffb800", "#ff6b35", "#ff2a6d"][:len(risk_data)],
            marker_line_color="rgba(0, 240, 255, 0.3)", marker_line_width=1,
        )])
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#8b92a8", font_family="JetBrains Mono",
            height=250, margin=dict(l=40, r=20, t=10, b=40),
            xaxis=dict(gridcolor="rgba(0, 240, 255, 0.05)"),
            yaxis=dict(gridcolor="rgba(0, 240, 255, 0.05)"),
        )
        st.plotly_chart(fig, use_container_width=True)

    if scorecard and scorecard.get("top_agents"):
        st.markdown("#### Top Agents by Activity")
        st.dataframe(pd.DataFrame(scorecard["top_agents"]), use_container_width=True)


elif page == "🛡️ SHIELD":
    st.markdown("## 🛡️ SHIELD — Real-Time Defense")
    st.markdown("*Inspect prompts for security threats using Veea Lobster Trap + Google Gemini AI.*")

    with st.form("shield_form"):
        prompt_input = st.text_area("Enter prompt to inspect:", placeholder="Type or paste a prompt to analyze...", height=120)
        col1, col2 = st.columns([3, 1])
        with col1:
            agent_id = st.text_input("Agent ID:", value="test-agent-01")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("🔍 INSPECT")

    if submitted and prompt_input:
        if api_online:
            with st.spinner("Analyzing..."):
                result = api_post("/api/v1/shield/inspect", {"prompt": prompt_input, "agent_id": agent_id})
        else:
            # Demo analysis based on keywords
            prompt_lower = prompt_input.lower()
            is_malicious = any(kw in prompt_lower for kw in ["ignore", "bypass", "send to", "evil", "override", "jailbreak"])
            result = {
                "action": "DENY" if is_malicious else "ALLOW",
                "risk_score": 0.85 if is_malicious else 0.05,
                "intent": "instruction_override" if is_malicious else "benign_query",
                "categories": ["prompt_injection"] if is_malicious else [],
                "injection_detected": is_malicious,
                "exfiltration_detected": "send" in prompt_lower and is_malicious,
                "pii_detected": False,
                "reason": "High risk patterns detected" if is_malicious else "No threats detected",
                "latency_ms": 12.3,
            }

        if result:
            action = result.get("action", "UNKNOWN")
            risk = result.get("risk_score", 0)
            border_color = "#05ffa1" if action == "ALLOW" else "#ff2a6d"
            bg = f"rgba({'5, 255, 161' if action == 'ALLOW' else '255, 42, 109'}, 0.05)"

            st.markdown(f"""
            <div style="background: {bg}; border: 1px solid {border_color}; border-radius: 12px; padding: 1.5rem; margin: 1rem 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                    <div>
                        <span style="color: {border_color}; font-size: 1.5rem; font-weight: 800;">{action}</span>
                        <p style="color: #8b92a8; font-size: 0.8rem; margin: 0.3rem 0 0 0;">Intent: {result.get('intent', 'unknown')}</p>
                    </div>
                    <div style="text-align: right;">
                        <span style="color: {border_color}; font-size: 2rem; font-weight: 800;">{risk:.0%}</span>
                        <p style="color: #8b92a8; font-size: 0.7rem; margin: 0;">RISK SCORE</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if result.get("categories"):
                st.warning(f"🏷️ Categories: {', '.join(result['categories'])}")
            if result.get("injection_detected"):
                st.error("🚨 Prompt injection detected!")
            if result.get("exfiltration_detected"):
                st.error("🚨 Data exfiltration attempt detected!")
            with st.expander("Details"):
                st.markdown(f"**Reason:** {result.get('reason', 'N/A')}")
                st.markdown(f"**Latency:** {result.get('latency_ms', 0):.1f}ms")


elif page == "⚔️ SPEAR":
    st.markdown("## ⚔️ SPEAR — Adversarial Validation")
    st.markdown("*Run MITRE ATLAS 2026 mapped adversarial tests against AI agents.*")

    tests_data = api_get("/api/v1/spear/tests") if api_online else DEMO_TESTS
    if tests_data:
        st.markdown(f"""
        <div style="background: rgba(255, 42, 109, 0.05); border: 1px solid rgba(255, 42, 109, 0.2); border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
            <span style="color: #ff2a6d; font-weight: 700; font-family: 'JetBrains Mono', monospace;">{tests_data['total']}</span>
            <span style="color: #8b92a8; font-size: 0.85rem;"> ATLAS 2026 techniques available</span>
        </div>
        """, unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(tests_data["tests"])[["atlas_id", "name", "category", "priority"]], use_container_width=True)

    st.markdown("")
    if st.button("🚀 Run Full Test Suite"):
        with st.spinner("Running adversarial tests..."):
            if api_online:
                result = api_post("/api/v1/spear/run", {"target_agent_id": "demo-agent"})
            else:
                import time
                time.sleep(2)
                result = DEMO_SPEAR_RESULTS

        if result:
            summary = result.get("summary", {})
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Tests", summary.get("total_tests", 0))
            col2.metric("Passed ✅", summary.get("passed", 0))
            col3.metric("Failed ❌", summary.get("failed", 0))
            col4.metric("Risk Score", f"{summary.get('risk_score', 0):.1f}/100")

            if result.get("critical_findings"):
                st.markdown("### 🚨 Critical Findings")
                for finding in result["critical_findings"]:
                    with st.expander(f"❌ {finding['atlas_id']} — {finding['name']} [{finding['severity']}]", expanded=True):
                        st.markdown(f"**Remediation:** {finding.get('remediation', 'N/A')}")

            st.markdown("### All Results")
            results_df = pd.DataFrame(result.get("all_results", []))
            if not results_df.empty:
                cols = [c for c in ["atlas_id", "name", "passed", "severity", "execution_time_ms"] if c in results_df.columns]
                st.dataframe(results_df[cols], use_container_width=True)


elif page == "⛓️ CHAIN":
    st.markdown("## ⛓️ CHAIN — Immutable Audit Trail")
    st.markdown("*Tamper-evident SHA-256 hash-chain audit logs with compliance reporting.*")

    integrity = api_get("/api/v1/chain/integrity") if api_online else {"valid": True, "timestamp": datetime.now(timezone.utc).isoformat()}
    if integrity:
        if integrity.get("valid"):
            st.markdown("""
            <div style="background: rgba(5, 255, 161, 0.05); border: 1px solid rgba(5, 255, 161, 0.3); border-radius: 8px; padding: 1rem;">
                <span style="color: #05ffa1; font-weight: 700;">🔒 CHAIN INTEGRITY: VERIFIED</span>
                <span style="color: #5a6178; font-size: 0.8rem; margin-left: 1rem;">All events tamper-evident</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("⚠️ CHAIN INTEGRITY: TAMPERED — Investigate immediately!")

    st.markdown("")
    st.markdown("### Recent Audit Events")

    if api_online:
        events = api_get("/api/v1/chain/events?limit=20")
    else:
        events = [
            {"timestamp": "2026-05-15T18:30:01Z", "event_type": "SHIELD_DECISION", "agent_id": "CustomerService-v2", "action": "inspect_prompt", "result": "DENY", "risk_level": 3},
            {"timestamp": "2026-05-15T18:29:45Z", "event_type": "SPEAR_TEST_COMPLETED", "agent_id": "DataPipeline-v1", "action": "ATLAS:AML.T0051", "result": "FAIL", "risk_level": 4},
            {"timestamp": "2026-05-15T18:29:30Z", "event_type": "SHIELD_DECISION", "agent_id": "ResearchBot-v1", "action": "inspect_prompt", "result": "ALLOW", "risk_level": 0},
            {"timestamp": "2026-05-15T18:28:12Z", "event_type": "SPEAR_TEST_COMPLETED", "agent_id": "CodeAssistant-v3", "action": "ATLAS:AML.T0057", "result": "PASS", "risk_level": 0},
            {"timestamp": "2026-05-15T18:27:55Z", "event_type": "SHIELD_DECISION", "agent_id": "CustomerService-v2", "action": "inspect_prompt", "result": "ALLOW", "risk_level": 0},
        ]

    if events:
        events_df = pd.DataFrame(events)
        if not events_df.empty:
            cols = [c for c in ["timestamp", "event_type", "agent_id", "action", "result", "risk_level"] if c in events_df.columns]
            st.dataframe(events_df[cols], use_container_width=True)
        else:
            st.info("No audit events yet. Run SHIELD or SPEAR to generate events.")


elif page == "📊 Reports":
    st.markdown("## 📊 Compliance Reports")
    st.markdown("*Generate regulator-readable compliance reports for enterprise frameworks.*")

    framework = st.selectbox("Select Framework", ["SOC2", "HIPAA", "PCI_DSS"])

    if st.button("📄 Generate Report"):
        with st.spinner(f"Generating {framework} report..."):
            if api_online:
                report = api_get(f"/api/v1/chain/report/{framework}")
            else:
                import time
                time.sleep(1)
                report = {
                    "framework": framework,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "total_events": 247,
                    "chain_integrity": True,
                    "applicable_controls": {
                        "SOC2": ["CC6.1 — Logical access security", "CC7.1 — Security detection", "CC7.2 — Incident response"],
                        "HIPAA": ["164.312(a) — Access control", "164.312(b) — Audit controls", "164.312(c) — Integrity"],
                        "PCI_DSS": ["Req 10 — Logging", "Req 11 — Testing"],
                    }.get(framework, []),
                    "evidence_summary": {"shield_decisions": 142, "spear_tests": 67, "critical_events": 20},
                    "recommendation": "Chain integrity verified. All events tamper-evident. Compliance posture: STRONG.",
                }

        if report:
            col1, col2 = st.columns(2)
            col1.metric("Total Events", report.get("total_events", 0))
            col2.metric("Chain Integrity", "✅ Verified" if report.get("chain_integrity") else "❌ Failed")

            st.markdown("### Applicable Controls")
            for control in report.get("applicable_controls", []):
                st.markdown(f"- `{control}`")

            st.markdown("### Evidence Summary")
            st.json(report.get("evidence_summary", {}))

            st.success(f"**Recommendation:** {report.get('recommendation', 'N/A')}")


# --- Footer ---

st.markdown("""
<div style="text-align: center; padding: 2rem 0; border-top: 1px solid rgba(0, 240, 255, 0.08); margin-top: 3rem;">
    <p style="color: #5a6178; font-size: 0.75rem; font-family: 'JetBrains Mono', monospace;">
        © 2026 MIT License · Developed by MycoGuard Team<br>
        TechEx Intelligent Enterprise Solutions Hackathon 2026<br>
        Track 1: Agent Security & AI Governance — Powered by Veea<br><br>
        <span style="color: #3a3f52;">Veea Lobster Trap · Google Gemini · MITRE ATLAS 2026 · CrewAI</span>
    </p>
</div>
""", unsafe_allow_html=True)
