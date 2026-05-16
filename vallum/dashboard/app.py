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
import json

# --- Configuration ---

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="VALLUM — Agent Security Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Enhanced Styling with Animations ---

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;800&display=swap');

    /* Base */
    .stApp {
        background: linear-gradient(180deg, #0a0e27 0%, #060918 50%, #0a0e27 100%);
        background-attachment: fixed;
    }
    h1, h2, h3 { font-family: 'Inter', sans-serif !important; color: #e0e6ed !important; }
    p, span, label, .stMarkdown { font-family: 'Inter', sans-serif !important; }

    /* Animated background grid */
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
    @keyframes gridPulse {
        0%, 100% { opacity: 0.4; }
        50% { opacity: 0.8; }
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0c1033 0%, #0a0e27 100%) !important;
        border-right: 1px solid rgba(0, 240, 255, 0.15);
    }
    [data-testid="stSidebar"] .stRadio label {
        color: #8b92a8 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem !important;
        transition: color 0.3s ease, transform 0.2s ease;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        color: #00f0ff !important;
        transform: translateX(4px);
    }

    /* Glowing header */
    .vallum-header {
        text-align: center;
        padding: 2rem 0 1rem 0;
        position: relative;
    }
    .vallum-header h1 {
        font-size: 3rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.3em !important;
        margin-bottom: 0 !important;
        text-shadow: 0 0 20px rgba(0, 240, 255, 0.5), 0 0 40px rgba(0, 240, 255, 0.2);
        animation: titleGlow 3s ease-in-out infinite;
    }
    @keyframes titleGlow {
        0%, 100% { text-shadow: 0 0 20px rgba(0, 240, 255, 0.5), 0 0 40px rgba(0, 240, 255, 0.2); }
        50% { text-shadow: 0 0 30px rgba(0, 240, 255, 0.8), 0 0 60px rgba(0, 240, 255, 0.4); }
    }
    .vallum-subtitle {
        color: #8b92a8;
        font-size: 0.9rem;
        letter-spacing: 0.15em;
        font-family: 'JetBrains Mono', monospace;
        margin-top: 0.3rem;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #0f1538 0%, #141b4d 100%);
        border: 1px solid rgba(0, 240, 255, 0.15);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    [data-testid="stMetric"]:hover {
        border-color: rgba(0, 240, 255, 0.4);
        box-shadow: 0 4px 20px rgba(0, 240, 255, 0.1);
        transform: translateY(-2px);
    }
    [data-testid="stMetric"] label {
        color: #8b92a8 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.7rem !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #00f0ff !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 800 !important;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #00f0ff 0%, #0080ff 100%) !important;
        color: #0a0e27 !important;
        font-weight: 700 !important;
        font-family: 'Inter', sans-serif !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 2rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(0, 240, 255, 0.3) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 25px rgba(0, 240, 255, 0.5) !important;
    }

    /* Form submit button */
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #00f0ff 0%, #0080ff 100%) !important;
        color: #0a0e27 !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 15px rgba(0, 240, 255, 0.3) !important;
    }

    /* Text inputs */
    .stTextArea textarea, .stTextInput input {
        background: #0c1033 !important;
        border: 1px solid rgba(0, 240, 255, 0.2) !important;
        border-radius: 8px !important;
        color: #e0e6ed !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #00f0ff !important;
        box-shadow: 0 0 10px rgba(0, 240, 255, 0.2) !important;
    }

    /* Selectbox */
    .stSelectbox > div > div {
        background: #0c1033 !important;
        border: 1px solid rgba(0, 240, 255, 0.2) !important;
        border-radius: 8px !important;
    }

    /* Dataframes */
    .stDataFrame {
        border: 1px solid rgba(0, 240, 255, 0.1) !important;
        border-radius: 8px !important;
    }

    /* Alert boxes */
    .stAlert {
        border-radius: 8px !important;
    }

    /* Success/Error/Warning/Info boxes */
    [data-testid="stNotification"] {
        border-radius: 8px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem !important;
    }

    /* Dividers */
    hr {
        border-color: rgba(0, 240, 255, 0.1) !important;
    }

    /* Status indicator */
    .status-online {
        display: inline-block;
        width: 8px; height: 8px;
        background: #05ffa1;
        border-radius: 50%;
        margin-right: 6px;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(5, 255, 161, 0.4); }
        50% { box-shadow: 0 0 0 6px rgba(5, 255, 161, 0); }
    }

    /* Severity colors */
    .sev-critical { color: #ff2a6d; font-weight: 700; }
    .sev-high { color: #ffb800; font-weight: 700; }
    .sev-medium { color: #ffd700; }
    .sev-low { color: #05ffa1; }
    .sev-none { color: #05ffa1; }

    /* Footer */
    .vallum-footer {
        text-align: center;
        padding: 2rem 0;
        border-top: 1px solid rgba(0, 240, 255, 0.08);
        margin-top: 3rem;
    }
    .vallum-footer p {
        color: #5a6178;
        font-size: 0.75rem;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 0.05em;
    }

    /* Spinner */
    .stSpinner > div {
        border-top-color: #00f0ff !important;
    }

    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
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


# --- Header with Logo ---

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
    <div class="vallum-header">
        <img src="app/static/vallum_logo.jpeg" width="80" style="border-radius: 50%; margin-bottom: 0.5rem; box-shadow: 0 0 20px rgba(0, 240, 255, 0.3);" onerror="this.style.display='none'">
        <h1><span style="color: #00f0ff;">V</span>ALLUM</h1>
        <p class="vallum-subtitle">AGENT SECURITY COMMAND CENTER</p>
    </div>
    """, unsafe_allow_html=True)

# --- Sidebar ---

st.sidebar.markdown("""
<div style="text-align: center; padding: 1rem 0;">
    <div style="font-size: 2rem; margin-bottom: 0.3rem;">🔱</div>
    <h2 style="color: #00f0ff; font-size: 1.3rem; margin: 0; letter-spacing: 0.2em;">VALLUM</h2>
    <p style="color: #5a6178; font-size: 0.7rem; font-family: 'JetBrains Mono', monospace; margin-top: 0.3rem;">
        v0.1.0 · TechEx 2026
    </p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "NAVIGATION",
    ["🏠 Overview", "🛡️ SHIELD", "⚔️ SPEAR", "⛓️ CHAIN", "📊 Reports"],
)

st.sidebar.markdown("---")

# Check API health
health = api_get("/health")
api_online = health is not None

if api_online:
    st.sidebar.markdown('<p style="color: #05ffa1; font-size: 0.8rem; font-family: JetBrains Mono, monospace;"><span class="status-online"></span> API ONLINE</p>', unsafe_allow_html=True)
else:
    st.sidebar.markdown('<p style="color: #ffb800; font-size: 0.8rem; font-family: JetBrains Mono, monospace;">⚠ API OFFLINE</p>', unsafe_allow_html=True)

# Sidebar tech stack
st.sidebar.markdown("""
<div style="margin-top: 2rem; padding: 1rem; background: rgba(0, 240, 255, 0.03); border-radius: 8px; border: 1px solid rgba(0, 240, 255, 0.08);">
    <p style="color: #5a6178; font-size: 0.65rem; font-family: 'JetBrains Mono', monospace; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.5rem;">Powered by</p>
    <p style="color: #8b92a8; font-size: 0.7rem; font-family: 'JetBrains Mono', monospace; line-height: 1.8; margin: 0;">
        Veea Lobster Trap<br>
        Google Gemini<br>
        CrewAI<br>
        MITRE ATLAS 2026
    </p>
</div>
""", unsafe_allow_html=True)


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
    col2.metric("CRITICAL ALERTS", str(critical_count))
    col3.metric("CHAIN INTEGRITY", "✅ VERIFIED" if (integrity and integrity.get("valid")) else "⚠️ CHECK")
    col4.metric("API STATUS", "ONLINE" if api_online else "OFFLINE")

    st.markdown("")

    # Architecture overview
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0c1033 0%, #0f1538 100%); border: 1px solid rgba(0, 240, 255, 0.1); border-radius: 12px; padding: 2rem; margin: 1rem 0;">
        <div style="display: flex; justify-content: space-around; text-align: center; flex-wrap: wrap; gap: 1rem;">
            <div style="flex: 1; min-width: 200px;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">🛡️</div>
                <h4 style="color: #00f0ff; margin: 0; font-size: 0.9rem;">SHIELD</h4>
                <p style="color: #8b92a8; font-size: 0.75rem; margin-top: 0.3rem;">Real-time prompt inspection<br>Gemini AI + Lobster Trap</p>
            </div>
            <div style="flex: 1; min-width: 200px;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚔️</div>
                <h4 style="color: #ff2a6d; margin: 0; font-size: 0.9rem;">SPEAR</h4>
                <p style="color: #8b92a8; font-size: 0.75rem; margin-top: 0.3rem;">11 ATLAS 2026 techniques<br>Mutation engine + CrewAI</p>
            </div>
            <div style="flex: 1; min-width: 200px;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">⛓️</div>
                <h4 style="color: #05ffa1; margin: 0; font-size: 0.9rem;">CHAIN</h4>
                <p style="color: #8b92a8; font-size: 0.75rem; margin-top: 0.3rem;">Immutable audit trails<br>SHA-256 hash-chain</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

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
            marker_line_color="rgba(0, 240, 255, 0.3)",
            marker_line_width=1,
        )])
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#8b92a8", font_family="JetBrains Mono",
            height=280, margin=dict(l=40, r=20, t=20, b=40),
            xaxis=dict(gridcolor="rgba(0, 240, 255, 0.05)"),
            yaxis=dict(gridcolor="rgba(0, 240, 255, 0.05)"),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Top agents
    if scorecard and scorecard.get("top_agents"):
        st.markdown("#### Top Agents by Activity")
        agents_df = pd.DataFrame(scorecard["top_agents"])
        st.dataframe(agents_df, use_container_width=True)


elif page == "🛡️ SHIELD":
    st.markdown("## 🛡️ SHIELD — Real-Time Defense")
    st.markdown("*Inspect prompts for security threats using Veea Lobster Trap + Google Gemini AI.*")

    st.markdown("")

    with st.form("shield_form"):
        prompt_input = st.text_area(
            "Enter prompt to inspect:",
            placeholder="Type or paste a prompt to analyze for threats...",
            height=120,
        )
        col1, col2 = st.columns([3, 1])
        with col1:
            agent_id = st.text_input("Agent ID:", value="test-agent-01")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("🔍 INSPECT")

    if submitted and prompt_input:
        if api_online:
            with st.spinner("Analyzing prompt..."):
                result = api_post("/api/v1/shield/inspect", {
                    "prompt": prompt_input,
                    "agent_id": agent_id,
                })
            if result:
                st.markdown("")
                action = result.get("action", "UNKNOWN")
                risk = result.get("risk_score", 0)

                # Result card
                if action == "ALLOW":
                    border_color = "#05ffa1"
                    bg = "rgba(5, 255, 161, 0.05)"
                elif action == "DENY":
                    border_color = "#ff2a6d"
                    bg = "rgba(255, 42, 109, 0.05)"
                else:
                    border_color = "#ffb800"
                    bg = "rgba(255, 184, 0, 0.05)"

                st.markdown(f"""
                <div style="background: {bg}; border: 1px solid {border_color}; border-radius: 12px; padding: 1.5rem; margin: 1rem 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                        <div>
                            <span style="color: {border_color}; font-size: 1.5rem; font-weight: 800; font-family: 'Inter', sans-serif;">{action}</span>
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
                if result.get("pii_detected"):
                    st.warning("⚠️ PII access pattern detected")

                with st.expander("Details"):
                    st.markdown(f"**Reason:** {result.get('reason', 'N/A')}")
                    st.markdown(f"**Latency:** {result.get('latency_ms', 0):.1f}ms")
            else:
                st.error("Failed to get response from API")
        else:
            st.warning("API offline. Cannot perform live inspection.")


elif page == "⚔️ SPEAR":
    st.markdown("## ⚔️ SPEAR — Adversarial Validation")
    st.markdown("*Run MITRE ATLAS 2026 mapped adversarial tests against AI agents.*")

    st.markdown("")

    # List available tests
    if api_online:
        tests_data = api_get("/api/v1/spear/tests")
        if tests_data:
            st.markdown(f"""
            <div style="background: rgba(255, 42, 109, 0.05); border: 1px solid rgba(255, 42, 109, 0.2); border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
                <span style="color: #ff2a6d; font-weight: 700; font-family: 'JetBrains Mono', monospace;">{tests_data['total']}</span>
                <span style="color: #8b92a8; font-size: 0.85rem;"> ATLAS 2026 techniques available</span>
            </div>
            """, unsafe_allow_html=True)

            tests_df = pd.DataFrame(tests_data["tests"])
            st.dataframe(tests_df[["atlas_id", "name", "category", "priority"]], use_container_width=True)

    st.markdown("")

    if st.button("🚀 Run Full Test Suite"):
        if api_online:
            with st.spinner("Running adversarial tests — this may take a moment..."):
                result = api_post("/api/v1/spear/run", {"target_agent_id": "demo-agent"})
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
                    display_cols = ["atlas_id", "name", "passed", "severity", "execution_time_ms"]
                    available_cols = [c for c in display_cols if c in results_df.columns]
                    st.dataframe(results_df[available_cols], use_container_width=True)
        else:
            st.warning("API offline. Cannot run tests.")


elif page == "⛓️ CHAIN":
    st.markdown("## ⛓️ CHAIN — Immutable Audit Trail")
    st.markdown("*Tamper-evident SHA-256 hash-chain audit logs with compliance reporting.*")

    st.markdown("")

    if api_online:
        integrity = api_get("/api/v1/chain/integrity")
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
    st.markdown("*Generate regulator-readable compliance reports for enterprise frameworks.*")

    st.markdown("")

    framework = st.selectbox("Select Framework", ["SOC2", "HIPAA", "PCI_DSS"])

    st.markdown("")

    if st.button("📄 Generate Report"):
        if api_online:
            with st.spinner(f"Generating {framework} report..."):
                report = api_get(f"/api/v1/chain/report/{framework}")
            if report:
                col1, col2 = st.columns(2)
                col1.metric("Total Events", report.get("total_events", 0))
                integrity_status = "✅ Verified" if report.get("chain_integrity") else "❌ Failed"
                col2.metric("Chain Integrity", integrity_status)

                st.markdown("### Applicable Controls")
                for control in report.get("applicable_controls", []):
                    st.markdown(f"- `{control}`")

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
<div class="vallum-footer">
    <p>
        VALLUM v0.1.0 · Team MycoGuard · TechEx Hackathon 2026<br>
        Veea Lobster Trap · Google Gemini · MITRE ATLAS 2026 · CrewAI
    </p>
</div>
""", unsafe_allow_html=True)
