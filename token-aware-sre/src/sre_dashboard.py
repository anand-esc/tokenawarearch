import streamlit as st
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="SRE Auto-Remediation Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Styling ---
st.markdown("""
    <style>
    .main { background-color: #F8F9FA; }
    .stButton>button {
        background-color: #2E86C1;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-weight: 600;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #1B4F72; }
    .approve-btn>button { background-color: #27AE60 !important; }
    .reject-btn>button { background-color: #E74C3C !important; }
    
    .card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border-left: 5px solid #2E86C1;
    }
    .metric-value { font-size: 24px; font-weight: bold; color: #2E86C1; }
    .metric-label { font-size: 14px; color: #7F8C8D; text-transform: uppercase; }
    </style>
""", unsafe_allow_html=True)

# --- Header ---
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🛡️ Autonomous SRE Defense Grid")
    st.markdown("Human-in-the-Loop Interception & Multi-Agent Transparency Log")
with col2:
    st.metric(label="Global Resolution Rate", value="93.0%", delta="2.1% (Post Q-Learning)")

st.divider()

# --- Interactive Log Input ---
st.markdown("### 📥 1. Incoming Telemetry (Datadog / Slack webhook)")
raw_log = st.text_area("Raw Incident Log:", value="""[CRITICAL] Database connection timeout across all production web servers.
java.net.ConnectException: Connection refused (Connection refused)
    at java.net.PlainSocketImpl.socketConnect(Native Method)
    at java.net.AbstractPlainSocketImpl.doConnect(AbstractPlainSocketImpl.java:350)
    at java.net.AbstractPlainSocketImpl.connectToAddress(AbstractPlainSocketImpl.java:206)
java.net.ConnectException: Connection refused (Connection refused)
{"alert_id": "99382", "service": "web-api-prod", "status": "down"}""", height=150)

if st.button("🚀 Process Incident via Multi-Agent Pipeline"):
    
    # Progress Simulation
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    status_text.text("Phase 1: Optimization Funnel (Semantic Pruning & Compression)...")
    time.sleep(1)
    progress_bar.progress(33)
    
    status_text.text("Phase 2: Zero-Shot Classification & Budget Allocation...")
    time.sleep(1.5)
    progress_bar.progress(66)
    
    status_text.text("Phase 3 & 4: Model Execution & Risk Assessment...")
    time.sleep(1)
    progress_bar.progress(100)
    status_text.empty()
    progress_bar.empty()

    # --- Results Layout ---
    colA, colB = st.columns([1.2, 1])
    
    with colA:
        st.markdown("### 🔍 2. Agent Transparency Trace")
        
        st.markdown("""
        <div class="card">
            <h4>⚡ Phase 1: Context Optimization</h4>
            <div style="display: flex; justify-content: space-between;">
                <div><span class="metric-label">Original Tokens</span><br><span class="metric-value" style="color: #E74C3C;">883</span></div>
                <div><span class="metric-label">Compressed Tokens</span><br><span class="metric-value" style="color: #27AE60;">241</span></div>
                <div><span class="metric-label">Reduction</span><br><span class="metric-value">72%</span></div>
            </div>
            <hr>
            <p><i>LLMLingua stripped non-essential stack trace frames based on zero-shot cosine similarity.</i></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="card" style="border-left-color: #8E44AD;">
            <h4>🧠 Phase 2: Q-Learning Routing Decision</h4>
            <p><b>Severity:</b> 8/10 | <b>Complexity:</b> 7/10</p>
            <p><b>Decision:</b> 🚀 <b>CLOUD_LLM (Gemini 1.5 Pro)</b></p>
            <p><b>Justification:</b> Allocated $1.50 budget. Q-Table determines local SLM has a high failure probability for complexity level 7.</p>
        </div>
        """, unsafe_allow_html=True)

    with colB:
        st.markdown("### 🛡️ 3. Action Layer: Human Review")
        
        st.markdown("**Cloud LLM Proposed Bash Script:**")
        st.code("""#!/bin/bash
# High-risk cache flush proposed
redis-cli flushall
systemctl restart redis
# Clear logs to free disk space
rm -rf /var/log/redis/*
""", language="bash")

        st.error("🚨 **RISK ASSESSOR: INTERCEPTED**")
        st.markdown("Score: **85/100** | Detected Pattern: `rm -rf`")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="approve-btn">', unsafe_allow_html=True)
            if st.button("APPROVE (+10 Reward)", use_container_width=True):
                pass
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c2:
            st.markdown('<div class="reject-btn">', unsafe_allow_html=True)
            if st.button("REJECT (-20 Penalty)", use_container_width=True):
                pass
            st.markdown('</div>', unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/IEEE_logo.svg/1200px-IEEE_logo.svg.png", width=150)
    st.markdown("### Real-Time Cluster Status")
    st.success("🟢 Web Servers (Healthy)")
    st.error("🔴 Database Cluster (Degraded)")
    st.success("🟢 Message Queue (Healthy)")
    
    st.divider()
    st.markdown("### Model Diagnostics")
    st.metric(label="Local SLM (Qwen) Status", value="Online", delta="0ms latency")
    st.metric(label="Cloud LLM (Gemini) Status", value="Online", delta="120ms latency")

