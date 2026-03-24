"""
app.py — Week 10: HAI Portfolio Dashboard (Artistic Edition)

Run with:
    pip install streamlit pandas plotly
    python -m streamlit run app.py

Architecture:
    ┌─────────────┐
    │  Input Layer │  sample_data.py → client profile
    └──────┬──────┘
           ▼
    ┌─────────────┐
    │  Logic Layer │  logic.py → suitability, bucket, allocation, flags
    └──────┬──────┘
           ▼
    ┌─────────────┐
    │  HAI Layer   │  disclosure, confidence note, review trigger, override
    └──────┬──────┘
           ▼
    ┌─────────────┐
    │ Output Layer │  dashboard, assistant, memo, review log
    └─────────────┘
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Local modules
from sample_data import SAMPLE_CLIENTS
from logic import run_pipeline
from memo import build_memo
from auth import check_password, get_role, can
from utils import append_log, read_logs, clear_logs, format_weights_inline


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Page config & custom CSS (artistic styling)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title="HAI Portfolio App — Week 10",
    page_icon="🎨",
    layout="wide",
)

# Custom CSS for artistic look with high readability
st.markdown("""
<style>
    /* Import font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global body */
    .stApp {
        background: linear-gradient(135deg, #0b0b2b 0%, #1a1a3a 50%, #2a2a4a 100%);
        font-family: 'Inter', sans-serif;
    }

    /* Force all text to be white with shadow for readability */
    body, .stMarkdown, .stText, .stWrite, .stMetric, .stAlert, .stInfo, .stSuccess, .stWarning, .stError,
    .stSelectbox label, .stSlider label, .stTextArea label, .stButton, .stExpander, .stTabs,
    .stMetric label, .stMetric .stMetricValue, .stMetric .stMetricDelta {
        color: #ffffff !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.3);
    }

    /* Hide default header/footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Cards and containers - semi-transparent with blur */
    .stMarkdown, .stDataFrame, .stPlotlyChart, .stAlert, .stInfo, .stSuccess, .stWarning, .stError {
        background: rgba(0, 0, 0, 0.45) !important;
        backdrop-filter: blur(10px);
        border-radius: 24px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(255, 255, 255, 0.15);
    }
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] .stMetric {
        background: transparent;
        box-shadow: none;
        border: none;
        padding: 0;
    }

    /* Headers */
    h1, h2, h3, h4, h5, h6, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #ffffff !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em;
        text-shadow: 0 2px 4px rgba(0,0,0,0.5);
    }

    /* Metric cards */
    .stMetric {
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(8px);
        border-radius: 20px;
        padding: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.25);
        transition: transform 0.2s ease;
    }
    .stMetric:hover {
        transform: translateY(-4px);
        background: rgba(255, 255, 255, 0.2);
    }

    /* Buttons */
    .stButton button {
        background: linear-gradient(90deg, #ff6a88, #ff99ac);
        color: white !important;
        border: none;
        border-radius: 40px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .stButton button:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 20px rgba(255,105,135,0.3);
    }

    /* Selectbox and widgets */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 40px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: white !important;
    }
    .stSelectbox label {
        color: rgba(255,255,255,0.9) !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background: transparent;
        border-bottom: 2px solid rgba(255,255,255,0.1);
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: rgba(255,255,255,0.7) !important;
        font-weight: 500;
        padding: 0.5rem 1rem;
        border-radius: 40px;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #ff6a88, #ff99ac);
        color: white !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(255,255,255,0.1);
        border-radius: 20px;
        color: white !important;
    }

    /* Code blocks */
    pre, .stJson {
        background: rgba(0,0,0,0.5) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        color: #f0f0f0 !important;
    }

    /* Alert boxes */
    .stAlert p, .stInfo p, .stSuccess p, .stWarning p, .stError p {
        color: #ffffff !important;
    }
    .stAlert { background: rgba(0,0,0,0.6) !important; }
    .stInfo { background: rgba(0,100,150,0.5) !important; }
    .stSuccess { background: rgba(0,128,0,0.5) !important; }
    .stWarning { background: rgba(255,165,0,0.5) !important; }
    .stError { background: rgba(255,0,0,0.5) !important; }

    /* Sliders */
    .stSlider > div > div > div {
        background: rgba(255,255,255,0.2);
    }
    .stSlider label {
        color: white !important;
    }

    /* Text area */
    .stTextArea textarea {
        background: rgba(0,0,0,0.5);
        color: white;
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Updated title with "joki L"
st.title("📊joki L Week 10: HAI Portfolio Dashboard")
st.caption("Human-AI Interaction in Financial Products — Governed Prototype")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Auth gate
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if not check_password():
    st.stop()

role = get_role()
st.sidebar.success(f"Logged in as: **{role}**")

if st.sidebar.button("Logout"):
    for key in ["authenticated", "role"]:
        st.session_state.pop(key, None)
    st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Sidebar: client selection
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.sidebar.markdown("---")
st.sidebar.subheader("Select Client")
client_name = st.sidebar.selectbox(
    "Client profile",
    list(SAMPLE_CLIENTS.keys()),
    label_visibility="collapsed",
)
client = SAMPLE_CLIENTS[client_name]

# Run the full pipeline
pipeline = run_pipeline(client)

# Store in session state for cross-tab access
st.session_state["client"] = client
st.session_state["pipeline"] = pipeline

# Show quick status in sidebar
st.sidebar.markdown("---")
st.sidebar.metric("Risk Score", f"{client['risk_score_100']} / 100")
st.sidebar.metric("Bucket", pipeline["bucket"])
if pipeline["review_required"]:
    st.sidebar.error(f"⚠️ Review required ({len(pipeline['flags'])} flag(s))")
else:
    st.sidebar.success("✓ No review flags")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Tabs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
tab_dash, tab_asst, tab_memo, tab_log = st.tabs([
    "📊 Dashboard",
    "💬 Assistant",
    "📝 Memo Export",
    "🔍 Review Log",
])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 1: Dashboard
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_dash:
    st.subheader("Client Summary")

    # ── Metrics row ──────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Risk Score", f"{client['risk_score_100']}/100")
    m2.metric("Risk Bucket", pipeline["bucket"])
    m3.metric("Horizon", f"{client['horizon_years']} yrs")
    m4.metric("Uncertainty", pipeline["uncertainty"].upper())

    st.markdown("---")

    # ── Allocation charts ────────────────────────────────────
    col_chart, col_compare = st.columns(2)

    with col_chart:
        st.markdown("**Recommended Allocation**")
        w = pipeline["weights"]
        # 使用更鲜艳的渐变色盘 Plasma
        fig_rec = px.pie(
            names=list(w.keys()),
            values=list(w.values()),
            color_discrete_sequence=px.colors.sequential.Plasma,
            hole=0.4,
        )
        fig_rec.update_traces(
            textposition='inside',
            textinfo='percent+label',
            marker=dict(line=dict(color='rgba(255,255,255,0.3)', width=2)),
            textfont=dict(color='white', size=12),
        )
        fig_rec.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', family='Inter'),
            margin=dict(t=20, b=20, l=20, r=20),
            height=300,
            showlegend=True,
        )
        st.plotly_chart(fig_rec, use_container_width=True)

    with col_compare:
        st.markdown("**Current vs Recommended**")
        current = client.get("current_weights", {})
        compare_df = pd.DataFrame({
            "Asset": list(w.keys()),
            "Current": [current.get(k, 0) for k in w.keys()],
            "Recommended": list(w.values()),
        })

        # 柱状图使用渐变色：Current 用 Viridis，Recommended 用 Cividis
        current_vals = [current.get(k, 0) for k in w.keys()]
        rec_vals = list(w.values())

        fig_comp = go.Figure()
        # Current 系列
        fig_comp.add_trace(go.Bar(
            name="Current",
            x=compare_df["Asset"],
            y=current_vals,
            marker=dict(
                colorscale='Viridis',
                color=current_vals,
                cmin=0, cmax=1,
                showscale=False,
            ),
        ))
        # Recommended 系列
        fig_comp.add_trace(go.Bar(
            name="Recommended",
            x=compare_df["Asset"],
            y=rec_vals,
            marker=dict(
                colorscale='Cividis',
                color=rec_vals,
                cmin=0, cmax=1,
                showscale=False,
            ),
        ))

        fig_comp.update_layout(
            barmode="group",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', family='Inter'),
            margin=dict(t=20, b=20, l=20, r=20),
            height=300,
            yaxis_tickformat=".0%",
            xaxis=dict(tickfont=dict(color='white')),
            yaxis=dict(tickfont=dict(color='white')),
        )
        st.plotly_chart(fig_comp, use_container_width=True)

    # ── Warning box ──────────────────────────────────────────
    st.markdown("---")
    if pipeline["flags"]:
        flag_text = "\n".join(f"- {f}" for f in pipeline["flags"])
        st.warning(
            f"**⚠️ Review Required** "
            f"(Uncertainty: {pipeline['uncertainty'].upper()})\n\n"
            f"{flag_text}"
        )
    else:
        st.success("✓ No review flags triggered.")

    # ── Disclosure box (always visible, not hidden) ──────────
    st.info(
        "**Disclosure**\n\n"
        "This recommendation is based on questionnaire-derived risk scores "
        "and preset return assumptions. "
        "Tax status, external holdings, and recent market events are "
        "**not** considered. "
        "This content is for **educational purposes only** and does not "
        "constitute investment advice. "
        "Output is automated and has **not** been reviewed by a human advisor."
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 2: Assistant
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_asst:
    st.subheader("Ask the Assistant")
    st.caption(
        "The assistant answers from **rule-based logic anchored to this "
        "client's state** — not from free-form language generation."
    )

    question = st.selectbox(
        "Select a question",
        [
            "Why this portfolio?",
            "What are the main risks?",
            "When is human review required?",
            "Why not a more aggressive allocation?",
        ],
    )

    if st.button("Ask", type="primary"):
        st.markdown("---")

        if question == "Why this portfolio?":
            st.markdown(pipeline["explanation"])

        elif question == "What are the main risks?":
            st.markdown(pipeline["risk_description"])

        elif question == "When is human review required?":
            st.markdown("**Review is triggered when any of these occur:**")
            st.markdown(
                "- Short horizon combined with high equity recommendation\n"
                "- High liquidity need with insufficient cash allocation\n"
                "- Risk score conflicts with stated investment goal\n"
                "- Large rebalancing shift from current holdings"
            )
            st.markdown("---")
            if pipeline["flags"]:
                st.error(
                    "**For this client, review IS required:**\n\n"
                    + "\n".join(f"- {f}" for f in pipeline["flags"])
                )
            else:
                st.success(
                    "For this client, **no review flags** were triggered."
                )

        elif question == "Why not a more aggressive allocation?":
            suit = pipeline["suit"]
            st.markdown(
                f"The equity cap for this client is **{suit['equity_cap']:.0%}** "
                f"based on:\n\n"
                f"- Horizon: {client['horizon_years']} years\n"
                f"- Liquidity need: {client['liquidity_need']}\n"
                f"- Goal: {client['goal'].replace('_', ' ')}\n\n"
                f"Even though the risk score ({client['risk_score_100']}) "
                f"maps to the **{pipeline['bucket']}** bucket, "
                f"suitability constraints cap equity at {suit['equity_cap']:.0%}. "
                f"This is by design — suitability runs **before** allocation."
            )

        # Log the interaction
        append_log({
            "event": "assistant_query",
            "client": client["name"],
            "question": question,
            "role": role,
        })


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 3: Memo Export
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_memo:
    st.subheader("Investment Memo")

    memo_text = build_memo(client, pipeline)

    # Preview
    with st.expander("Preview memo", expanded=True):
        st.markdown(memo_text)

    # Download
    col_dl1, col_dl2, _ = st.columns([1, 1, 2])
    with col_dl1:
        st.download_button(
            label="⬇️ Download as Markdown",
            data=memo_text,
            file_name=f"memo_{client['client_id']}_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
        )
    with col_dl2:
        st.download_button(
            label="⬇️ Download as Text",
            data=memo_text,
            file_name=f"memo_{client['client_id']}_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
        )

    # Log the export
    if st.button("Record memo export in audit log"):
        append_log({
            "event": "memo_export",
            "client": client["name"],
            "client_id": client["client_id"],
            "bucket": pipeline["bucket"],
            "weights": pipeline["weights"],
            "flags": pipeline["flags"],
            "uncertainty": pipeline["uncertainty"],
            "role": role,
        })
        st.success("Memo export recorded in audit log.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 4: Review Log
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_log:
    st.subheader("Review & Override Log")

    # ── Override section (reviewer only) ─────────────────────
    if can("override"):
        st.markdown("### Submit an Override")
        st.caption("As a **reviewer**, you can override the recommendation.")

        with st.form("override_form"):
            override_reason = st.text_area(
                "Override reason (required)",
                placeholder="e.g., Client has near-term home purchase not captured in profile",
            )

            st.markdown("**Adjusted allocation:**")
            ov1, ov2, ov3, ov4 = st.columns(4)
            new_eq = ov1.slider("Equity %", 0, 100, int(pipeline["weights"]["Equity"] * 100))
            new_bd = ov2.slider("Bond %", 0, 100, int(pipeline["weights"]["Bond"] * 100))
            new_gd = ov3.slider("Gold %", 0, 100, int(pipeline["weights"]["Gold"] * 100))
            new_ca = ov4.slider("Cash %", 0, 100, int(pipeline["weights"]["Cash"] * 100))

            submitted = st.form_submit_button("Submit Override", type="primary")

            if submitted:
                total = new_eq + new_bd + new_gd + new_ca
                if total == 0:
                    st.error("Weights cannot all be zero.")
                elif not override_reason.strip():
                    st.error("Override reason is required.")
                else:
                    # Normalize
                    new_weights = {
                        "Equity": round(new_eq / total, 4),
                        "Bond": round(new_bd / total, 4),
                        "Gold": round(new_gd / total, 4),
                        "Cash": round(new_ca / total, 4),
                    }
                    record = {
                        "event": "override",
                        "client": client["name"],
                        "client_id": client["client_id"],
                        "original_weights": pipeline["weights"],
                        "override_weights": new_weights,
                        "override_reason": override_reason.strip(),
                        "flags_at_time": pipeline["flags"],
                        "reviewer": role,
                    }
                    append_log(record)
                    st.success(
                        f"✓ Override recorded.\n\n"
                        f"New allocation: {format_weights_inline(new_weights)}"
                    )
    else:
        st.info(
            "You are logged in as **user**. "
            "Override functionality requires **reviewer** access."
        )

    # ── Log display ──────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Audit Log")

    logs = read_logs()
    if not logs:
        st.write("No log entries yet.")
    else:
        # Filter options
        event_types = sorted(set(r.get("event", "unknown") for r in logs))
        selected_events = st.multiselect(
            "Filter by event type",
            event_types,
            default=event_types,
        )

        filtered = [r for r in logs if r.get("event") in selected_events]
        st.write(f"Showing {len(filtered)} of {len(logs)} records")

        for i, record in enumerate(reversed(filtered)):
            with st.expander(
                f"{record.get('timestamp', '?')} — "
                f"{record.get('event', '?')} — "
                f"{record.get('client', '?')}",
                expanded=(i == 0),
            ):
                st.json(record)

    # ── Clear logs (admin/demo) ──────────────────────────────
    st.markdown("---")
    if st.button("🗑️ Clear all logs (demo reset)"):
        clear_logs()
        st.success("Logs cleared.")
        st.rerun()
