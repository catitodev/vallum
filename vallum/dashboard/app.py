"""
VALLUM DASHBOARD — Cybersecurity Command Center
Streamlit app with cyberpunk visual theme, connected to live backend.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timezone
import httpx
import asyncio
import json

# --- Configuration ---

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="VALLUM — Agent Security Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Styling ---

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;800&display=swap');
    .stApp { background: #0a0e27; }
    h1, h2, h3 { font-family: 'Inter', sans-serif !important; color: #e0e6ed !important; }
    .metric-card {
        background: linear-gradient(135deg, #0f1538 0%, #1a1f4e 100%);
        border: 1px solid rgba(0, 240, 255, 0.2);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
    }
    .metric-value { font-size: 2rem; font-weight: 800; color: #00f0ff; }
    .metric-label { font-size: 0.8rem; color: #8b92a8; text-transform: uppercase; letter-spacing: 0.1em; }
    .risk-critical { color: #ff2a6d; }
    .risk-high { color: #ffb800; }
    .risk-medium { color: #ffd700; }
    .risk-low { color: #05ffa1; }
    .risk-none { color: #05ffa1; }
    .status-pass { color: #05ffa1; font-weight: bold; }
    .status-fail { color: #ff2a6d; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


# --- API Helpers ---

def api_get(endpoint: str):
    """Make GET request to Vallum API."""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{API_BASE}{endpoint}")
            if response.status_code == 200:
                return response.json()
    except Exception:
        pass
    return None


def api_post(endpoint: str, data: dict):
    """Make POST request to Vallum API."""
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(f"{API_BASE}{endpoint}", json=data)
            if response.status_code == 200:
                return response.json()
    except Exception:
        pass
    return None


# --- Header ---

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
    <div style="text-align: center; padding: 1.5rem 0;">
        <h1 style="font-size: 2.5rem; font-weight: 800; letter-spacing: 0.2em; margin-bottom: 0;">
            <span style="color: #00f0ff;">V</span>ALLUM
        </h1>
        <p style="color: #8b92a8; font-size: 1rem; letter-spacing: 0.1em; margin-top: 0;">
            AGENT SECURITY COMMAND CENTER
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- Sidebar ---

st.sidebar.markdown("""
<div style="text-align: center;">
    <h2 style="color: #00f0ff;">🔱 VALLUM</h2>
    <p style="color: #8b92a8; font-size: 0.8rem;">v0.1.0 — TechEx 2026</p>
</div>
""", unsafe_allow_html=True)

page = st.sidebar.radio(
    "NAVIGATION",
    ["🏠 Overview", "🛡️ SHIELD", "⚔️ SPEAR", "⛓️ CHAIN", "📊 Reports"],
)

# Check API health
health = api_get("/health")
api_online = health is not None

if api_online:
    st.sidebar.success("🟢 API Online")
else:
    st.sidebar.warning("🟡 API Offline — showing cached data")

# --- Pages ---

if page == "🏠 Overview":
    st.markdown("### System Overview")

    # Fetch live data
    scorecard = api_get("/api/v1/chain/scorecard") if api_online else None
    integrity = api_get("/api/v1/chain/integrity") if api_online else None

    col1, col2, col3, col4 = st.columns(4)

    if scorecard:
        total_events = scorecard.get("total_events", 0)
        risk_levels = scorecard.get("by_risk_level", {})
        critical_count = risk_levels.get("L3", 0) + risk_levels.get("L4", 0)
    else:
        total_events = 0
        critical_count = 0

    col1.metric("TOTAL EVENTS", f"{total_events:,}")
    col2.metric("CRITICAL ALERTS", str(critical_count), delta=None)
    col3.metric("CHAIN INTEGRITY", "✅" if (integrity and integrity.get("valid")) else "⚠️")
    col4.metric("API STATUS", "ONLINE" if api_online else "OFFLINE")

    # Risk distribution chart
    if scorecard and scorecard.get("by_risk_level"):
        st.markdown("#### Risk Distribution")
        risk_data = scorecard["by_risk_level"]
        labels = list(risk_data.keys())
        values = list(risk_data.values())
        colors = ["#05ffa1", "#ffd700", "#ffb800", "#ff6b35", "#ff2a6d"]

        fig = go.Figure(data=[go.Bar(
            x=labels, y=values,
            marker_color=colors[:len(labels)],
        )])
        fig.update_layout(
            plot_bgcolor="#0a0e27", paper_bgcolor="#0a0e27",
            font_color="#8b92a8", height=300,
            xaxis_title="Risk Level", yaxis_title="Events",
        )
        st.plotly_chart(fig, use_container_width=True)

    # Top agents
    if scorecard and scorecard.get("top_agents"):
        st.markdown("#### Top Agents by Activity")
        agents_df = pd.DataFrame(scorecard["top_agents"])
        st.dataframe(agents_df, use_container_width=True)


elif page == "🛡️ SHIELD":
    st.markdown("## 🛡️ SHIELD — Real-Time Defense")
    st.markdown("Inspect prompts for security threats using Lobster Trap + Gemini AI.")

    with st.form("shield_form"):
        prompt_input = st.text_area(
            "Enter prompt to inspect:",
            placeholder="Type or paste a prompt to analyze...",
            height=100,
        )
        agent_id = st.text_input("Agent ID:", value="test-agent-01")
        submitted = st.form_submit_button("🔍 Inspect Prompt")

    if submitted and prompt_input:
        if api_online:
            result = api_post("/api/v1/shield/inspect", {
                "prompt": prompt_input,
                "agent_id": agent_id,
            })
            if result:
                col1, col2, col3 = st.columns(3)
                action = result.get("action", "UNKNOWN")
                risk = result.get("risk_score", 0)

                action_color = "#05ffa1" if action == "ALLOW" else "#ff2a6d"
                col1.markdown(f"**Action:** <span style='color:{action_color}'>{action}</span>", unsafe_allow_html=True)
                col2.markdown(f"**Risk Score:** {risk:.2f}")
                col3.markdown(f"**Intent:** {result.get('intent', 'unknown')}")

                if result.get("categories"):
                    st.warning(f"Categories detected: {', '.join(result['categories'])}")
                if result.get("injection_detected"):
                    st.error("⚠️ Prompt injection detected!")
                if result.get("exfiltration_detected"):
                    st.error("⚠️ Data exfiltration attempt detected!")
                st.info(f"Reason: {result.get('reason', 'N/A')}")
            else:
                st.error("Failed to get response from API")
        else:
            st.warning("API offline. Cannot perform live inspection.")


elif page == "⚔️ SPEAR":
    st.markdown("## ⚔️ SPEAR — Adversarial Validation")
    st.markdown("Run MITRE ATLAS 2026 mapped adversarial tests against AI agents.")

    # List available tests
    if api_online:
        tests_data = api_get("/api/v1/spear/tests")
        if tests_data:
            st.markdown(f"**Available Tests:** {tests_data['total']} ATLAS techniques")
            tests_df = pd.DataFrame(tests_data["tests"])
            st.dataframe(tests_df[["atlas_id", "name", "category", "priority"]], use_container_width=True)

    st.markdown("---")

    if st.button("🚀 Run Full Test Suite"):
        if api_online:
            with st.spinner("Running adversarial tests..."):
                result = api_post("/api/v1/spear/run", {"target_agent_id": "demo-agent"})
            if result:
                summary = result.get("summary", {})
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Tests", summary.get("total_tests", 0))
                col2.metric("Passed", summary.get("passed", 0))
                col3.metric("Failed", summary.get("failed", 0))
                col4.metric("Risk Score", f"{summary.get('risk_score', 0):.1f}")

                if result.get("critical_findings"):
                    st.markdown("### ⚠️ Critical Findings")
                    for finding in result["critical_findings"]:
                        st.error(f"**{finding['atlas_id']}** — {finding['name']} ({finding['severity']})")
                        st.markdown(f"  Remediation: {finding.get('remediation', 'N/A')}")

                st.markdown("### All Results")
                results_df = pd.DataFrame(result.get("all_results", []))
                if not results_df.empty:
                    display_cols = ["atlas_id", "name", "passed", "severity", "execution_time_ms"]
                    available_cols = [c for c in display_cols if c in results_df.columns]
                    st.dataframe(results_df[available_cols], use_container_width=True)
        else:
            st.warning("API offline. Cannot run tests.")


elif page == "⛓️ CHAIN":
    st.markdown("## ⛓️ CHAIN — Immutable Audit Trail")
    st.markdown("Tamper-evident hash-chain audit logs with compliance reporting.")

    if api_online:
        # Integrity check
        integrity = api_get("/api/v1/chain/integrity")
        if integrity:
            if integrity.get("valid"):
                st.success(f"🔒 Chain Integrity: VERIFIED — {integrity.get('timestamp', '')}")
            else:
                st.error("⚠️ Chain Integrity: TAMPERED — Investigate immediately!")

        # Recent events
        st.markdown("### Recent Audit Events")
        events = api_get("/api/v1/chain/events?limit=20")
        if events:
            events_df = pd.DataFrame(events)
            if not events_df.empty:
                display_cols = ["timestamp", "event_type", "agent_id", "action", "result", "risk_level"]
                available_cols = [c for c in display_cols if c in events_df.columns]
                st.dataframe(events_df[available_cols], use_container_width=True)
            else:
                st.info("No audit events recorded yet. Run SHIELD or SPEAR to generate events.")
        else:
            st.info("No events available.")
    else:
        st.warning("API offline. Cannot fetch audit data.")


elif page == "📊 Reports":
    st.markdown("## 📊 Compliance Reports")
    st.markdown("Generate regulator-readable compliance reports.")

    framework = st.selectbox("Select Framework", ["SOC2", "HIPAA", "PCI_DSS"])

    if st.button("📄 Generate Report"):
        if api_online:
            report = api_get(f"/api/v1/chain/report/{framework}")
            if report:
                col1, col2 = st.columns(2)
                col1.metric("Total Events", report.get("total_events", 0))
                col2.metric("Chain Integrity", "✅ Verified" if report.get("chain_integrity") else "❌ Failed")

                st.markdown("### Applicable Controls")
                for control in report.get("applicable_controls", []):
                    st.markdown(f"- {control}")

                st.markdown("### Evidence Summary")
                evidence = report.get("evidence_summary", {})
                st.json(evidence)

                st.success(f"**Recommendation:** {report.get('recommendation', 'N/A')}")
            else:
                st.error("Failed to generate report")
        else:
            st.warning("API offline. Cannot generate reports.")


# --- Footer ---

st.markdown("""
<div style="text-align: center; padding: 2rem 0; border-top: 1px solid rgba(0, 240, 255, 0.1); margin-top: 2rem;">
    <p style="color: #8b92a8; font-size: 0.8rem;">
        VALLUM v0.1.0 — Built for TechEx Hackathon 2026<br>
        Powered by Veea Lobster Trap · Google Gemini · MITRE ATLAS 2026 · CrewAI
    </p>
</div>
""", unsafe_allow_html=True)
