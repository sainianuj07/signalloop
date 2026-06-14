"""SignalLoop dashboard — the product surface.

Run:  streamlit run app/dashboard.py

Ties the whole pipeline together: ingest -> understand -> prioritize -> act,
plus a human-in-the-loop review queue that feeds corrections back to the data.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# On Streamlit Cloud there is no .env file. Bridge st.secrets -> env vars so
# os.getenv() (used in src/llm.py) finds the API keys the same way locally and deployed.
try:
    for _k, _v in st.secrets.items():
        os.environ.setdefault(_k, str(_v))
except Exception:
    pass

from src.db import get_conn
from src.classify.prompt import FEEDBACK_TYPES

st.set_page_config(page_title="SignalLoop", page_icon="🔁", layout="wide")
conn = get_conn()

# ---- consistent colour palette + clean chart style ----
PALETTE = ["#6C5CE7", "#00B894", "#0984E3", "#E17055", "#FDCB6E",
           "#E84393", "#00CEC9", "#A29BFE"]
px.defaults.color_discrete_sequence = PALETTE
px.defaults.template = "plotly_white"

# ---- page styling: soft gradient background + polished cards/tabs ----
st.markdown(
    """
    <style>
      .stApp {
          background: linear-gradient(160deg,#efebfb 0%,#e9f1ff 50%,#eafaf4 100%);
      }
      .block-container {padding-top: 2.2rem; max-width: 1300px;}
      h1, h2, h3 {letter-spacing:-0.4px; color:#2b2350;}
      [data-testid="stMetric"] {
          background:#ffffff; border:1px solid #e7e2fb; border-radius:16px;
          padding:16px 20px; box-shadow:0 4px 14px rgba(108,92,231,0.08);
      }
      [data-testid="stMetricLabel"] {color:#6b6790; font-weight:600;}
      [data-testid="stMetricValue"] {color:#5b4bdb; font-weight:800;}
      .stTabs [data-baseweb="tab-list"] {gap:6px;}
      .stTabs [data-baseweb="tab"] {
          background:#ffffffaa; border-radius:10px 10px 0 0; padding:8px 16px;
      }
      .stTabs [aria-selected="true"] {background:#6C5CE7 !important; color:white !important;}
      [data-testid="stExpander"] {background:#ffffffcc; border-radius:12px; border:1px solid #ece8fb;}
    </style>
    """,
    unsafe_allow_html=True,
)


def q(sql: str, params: tuple = ()) -> pd.DataFrame:
    return pd.read_sql_query(sql, conn, params=params)


# ===================== HEADER + METRICS =====================
st.title("🔁 SignalLoop")
st.caption("Feedback-to-Roadmap Intelligence Engine — turn raw user feedback into a "
           "prioritized, evidence-backed roadmap.")

total = q("SELECT COUNT(*) n FROM feedback_items")["n"][0]
classified = q("SELECT COUNT(*) n FROM feedback_items WHERE status='classified'")["n"][0]
actionable = q("SELECT COUNT(*) n FROM feedback_items WHERE status='classified' AND fb_type!='praise'")["n"][0]
themed = q("SELECT COUNT(*) n FROM feedback_items WHERE theme_id IS NOT NULL")["n"][0]
opps = q("SELECT COUNT(*) n FROM opportunities")["n"][0]
themed_pct = f"{(themed/total*100):.0f}% of all feedback" if total else "0%"

c1, c2, c3, c4 = st.columns(4)
c1.metric("User reviews ingested", f"{total}", help="Raw feedback collected (Google Play + CSV).")
c2.metric("Classified by AI", f"{classified} of {total}", help="Items labelled by type, severity, sentiment.")
c3.metric("Actionable (non-praise)", f"{actionable}", help="Bugs, friction, requests, churn risk — the roadmap signal.")
c4.metric("Roadmap opportunities", f"{opps}", themed_pct, help="Themes scored and ranked by RICE.")

tab_overview, tab_road, tab_trends, tab_themes, tab_queue, tab_prd, tab_board = st.tabs(
    [":material/insights: Overview", ":material/route: Roadmap", ":material/trending_up: Trends",
     ":material/category: Themes", ":material/reviews: Review Queue",
     ":material/description: PRD", ":material/forum: Boardroom"]
)

# ===================== OVERVIEW =====================
with tab_overview:
    st.subheader("What the engine is hearing")

    # Feedback by type — horizontal bar (clear labels + counts)
    types = q("SELECT fb_type AS Type, COUNT(*) AS Count FROM feedback_items "
              "WHERE status='classified' GROUP BY fb_type ORDER BY Count")
    if not types.empty:
        fig = px.bar(types, x="Count", y="Type", orientation="h", color="Type",
                     text="Count", title="Feedback by type")
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_layout(showlegend=False, yaxis_title="", xaxis_title="Number of reviews",
                          height=380, margin=dict(l=10, r=30, t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)

    colA, colB = st.columns(2)
    sent = q("SELECT sentiment AS Sentiment, COUNT(*) AS Count FROM feedback_items "
             "WHERE status='classified' GROUP BY sentiment")
    if not sent.empty:
        fig = px.pie(sent, names="Sentiment", values="Count", hole=0.55, title="Sentiment mix",
                     color="Sentiment",
                     color_discrete_map={"positive": "#00B894", "neutral": "#FDCB6E", "negative": "#E17055"})
        fig.update_traces(textposition="inside", textinfo="percent+label")
        colA.plotly_chart(fig, use_container_width=True)

    sev = q("SELECT severity AS Severity, COUNT(*) AS Count FROM feedback_items "
            "WHERE status='classified' GROUP BY severity ORDER BY severity")
    if not sev.empty:
        sev["Severity"] = sev["Severity"].map({1: "1 · minor", 2: "2 · moderate", 3: "3 · major", 4: "4 · critical"})
        fig = px.bar(sev, x="Severity", y="Count", title="Severity distribution",
                     color="Severity", text="Count",
                     color_discrete_sequence=["#A29BFE", "#74b9ff", "#fdcb6e", "#e17055"])
        fig.update_layout(showlegend=False, height=350)
        colB.plotly_chart(fig, use_container_width=True)

    # processing funnel
    funnel = pd.DataFrame({
        "Stage": ["Ingested", "Classified", "Actionable", "Prioritized (RICE)"],
        "Count": [total, classified, actionable, themed],
    })
    fig = px.funnel(funnel, x="Count", y="Stage", title="Feedback processing funnel")
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

# ===================== ROADMAP (RICE) =====================
with tab_road:
    st.subheader("Prioritized roadmap (RICE)")
    road = q(
        """SELECT t.name AS Theme, o.reach AS Reach, o.impact AS Impact,
                  o.confidence AS Conf, o.effort AS Effort, o.rice_score AS RICE
           FROM opportunities o JOIN themes t ON t.id=o.theme_id
           ORDER BY o.rice_score DESC"""
    )
    if road.empty:
        st.info("No opportunities yet. Run: python -m src.prioritize.rice")
    else:
        # Lollipop chart — modern, clean ranking
        r = road.sort_values("RICE")
        fig = go.Figure()
        for _, row in r.iterrows():
            fig.add_shape(type="line", x0=0, x1=row["RICE"], y0=row["Theme"], y1=row["Theme"],
                          line=dict(color="#ccc2f3", width=4))
        fig.add_trace(go.Scatter(
            x=r["RICE"], y=r["Theme"], mode="markers+text",
            marker=dict(size=24, color=r["RICE"], colorscale="Purp",
                        line=dict(color="#6C5CE7", width=1.5)),
            text=[f"{v:.1f}" for v in r["RICE"]], textposition="middle right",
            textfont=dict(size=12, color="#3b3170"),
            hovertemplate="%{y}<br>RICE %{x}<extra></extra>"))
        fig.update_layout(title="Opportunities ranked by RICE", height=420,
                          xaxis_title="RICE score", yaxis_title="",
                          margin=dict(l=10, r=60, t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("##### Opportunity landscape")
        st.caption("Bubble size = RICE. Top-right = high reach **and** high severity → the obvious wins.")
        fig2 = px.scatter(road, x="Reach", y="Impact", size="RICE", color="Theme",
                          hover_name="Theme", size_max=55)
        fig2.update_layout(yaxis_title="Impact (avg severity)", height=420)
        st.plotly_chart(fig2, use_container_width=True)

        st.dataframe(road, use_container_width=True, hide_index=True)
        st.caption("RICE = (Reach × Impact × Confidence) / Effort.")

# ===================== TRENDS (drift) =====================
with tab_trends:
    st.subheader("Theme velocity — what's rising vs cooling")
    st.caption("This week vs the prior week. A static dashboard shows what feedback *is*; "
               "this shows what's *changing* — catching emerging issues before they blow up.")
    from src.drift.monitor import compute_drift
    anchor, drift = compute_drift()
    if not drift:
        st.info("No dated feedback to analyze.")
    else:
        ddf = pd.DataFrame(drift)
        ddf["Direction"] = ddf["change"].apply(
            lambda c: "Rising" if c > 0 else ("Cooling" if c < 0 else "Flat"))
        fig = px.bar(ddf.sort_values("change"), x="change", y="theme", orientation="h",
                     color="Direction", text="change",
                     color_discrete_map={"Rising": "#00B894", "Cooling": "#E17055", "Flat": "#B2BEC3"},
                     title=f"Theme change vs last week (week ending {anchor})")
        fig.update_layout(yaxis_title="", xaxis_title="Δ items vs previous week", height=400)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### 📰 Auto-generated weekly brief")
    brief_path = Path(__file__).resolve().parent.parent / "docs" / "generated" / "weekly_brief.md"
    if st.button("Generate / refresh weekly brief"):
        with st.spinner("Writing the State of Feedback brief..."):
            from src.drift.monitor import generate_brief
            generate_brief()
        st.rerun()
    if brief_path.exists():
        st.markdown(brief_path.read_text(encoding="utf-8"))
    else:
        st.info("No brief yet — click the button above.")

# ===================== THEMES =====================
with tab_themes:
    st.subheader("Themes & the feedback behind them")
    themes = q("SELECT id, name, summary FROM themes ORDER BY id")
    for _, t in themes.iterrows():
        items = q("SELECT id, fb_type, severity, body FROM feedback_items "
                  "WHERE theme_id=? ORDER BY severity DESC", (int(t["id"]),))
        with st.expander(f"**{t['name']}** — {len(items)} items"):
            st.caption(t["summary"] or "")
            st.dataframe(items, use_container_width=True, hide_index=True)

# ===================== REVIEW QUEUE (human-in-the-loop) =====================
with tab_queue:
    st.subheader("Review queue — lowest-confidence first")
    st.caption("AI handles volume; humans resolve ambiguity. Corrections set `human_corrected=1` "
               "and become ground truth for future evals.")
    queue = q(
        """SELECT id, body, fb_type, severity, confidence
           FROM feedback_items WHERE status='classified'
           ORDER BY human_corrected ASC, confidence ASC, severity DESC LIMIT 15"""
    )
    for _, r in queue.iterrows():
        iid = int(r["id"])
        with st.expander(f"#{iid} · {r['fb_type']} · sev {r['severity']} · conf {r['confidence']}"):
            st.write(r["body"])
            col1, col2, col3 = st.columns([2, 1, 1])
            new_type = col1.selectbox(
                "Type", FEEDBACK_TYPES,
                index=FEEDBACK_TYPES.index(r["fb_type"]) if r["fb_type"] in FEEDBACK_TYPES else 0,
                key=f"type_{iid}")
            new_sev = col2.number_input("Severity", 1, 4, int(r["severity"]), key=f"sev_{iid}")
            col3.write("")
            if col3.button("Save correction", key=f"save_{iid}"):
                conn.execute(
                    "UPDATE feedback_items SET fb_type=?, severity=?, human_corrected=1 WHERE id=?",
                    (new_type, int(new_sev), iid))
                conn.commit()
                st.success(f"#{iid} corrected → {new_type} sev {new_sev}")
                st.rerun()

# ===================== PRD =====================
with tab_prd:
    st.subheader("Generated PRD (citation-verified)")
    prds = q("""SELECT t.id, t.name, o.draft_prd FROM opportunities o
                JOIN themes t ON t.id=o.theme_id ORDER BY o.rice_score DESC""")
    if prds.empty:
        st.info("Run RICE first, then generate a PRD.")
    else:
        choice = st.selectbox("Opportunity", prds["name"].tolist())
        row = prds[prds["name"] == choice].iloc[0]
        if st.button("Generate / regenerate PRD"):
            with st.spinner("Drafting + verifying citations..."):
                from src.prd.generator import generate
                generate(int(row["id"]))
            st.rerun()
        if row["draft_prd"]:
            st.markdown(row["draft_prd"])
        else:
            st.info("No PRD yet for this opportunity — click Generate above.")

# ===================== BOARDROOM =====================
with tab_board:
    st.subheader("Prioritization Boardroom — multi-agent decision memo")
    st.caption("Growth, Engineering, and Finance agents debate the roadmap from their own "
               "incentives; the Head of Product synthesizes a decision with recorded dissent.")
    memo_path = Path(__file__).resolve().parent.parent / "docs" / "generated" / "boardroom_memo.md"
    if st.button("Convene / re-run the boardroom"):
        with st.spinner("Agents debating the roadmap..."):
            from src.boardroom.debate import run as run_board
            run_board()
        st.rerun()
    if memo_path.exists():
        st.markdown(memo_path.read_text(encoding="utf-8"))
    else:
        st.info("No memo yet — click 'Convene the boardroom' above.")
