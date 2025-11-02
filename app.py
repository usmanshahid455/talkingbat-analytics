import streamlit as st
import pandas as pd
import plotly.express as px
import os

PRIMARY = "#2E1A47"
ACCENT = "#D4AF37"
BG = "#1E1233"
CARD = "#342052"

st.set_page_config(page_title="Talking Bat Analytics", page_icon="🏏", layout="wide")

st.markdown(f"""
<style>
.stApp {{
    background-color: {BG};
}}
.tb-header {{
    background: linear-gradient(90deg, {PRIMARY} 0%, {BG} 100%);
    padding: 1.2rem 1.5rem;
    border-radius: 1rem;
    color: white;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.2rem;
}}
.tb-title {{
    font-size: 1.8rem;
    font-weight: 700;
    letter-spacing: 1px;
}}
.tb-sub {{
    font-size: 0.85rem;
    opacity: 0.7;
}}
.tb-card {{
    background: {CARD};
    border: 1px solid rgba(212,175,55,0.2);
    border-radius: 1rem;
    padding: 1rem 1.2rem;
    color: white;
}}
.metric-label {{
    font-size: 0.7rem;
    text-transform: uppercase;
    opacity: 0.8;
}}
.metric-value {{
    font-size: 1.8rem;
    font-weight: 700;
}}
.analyst-good {{
    background: rgba(66,185,131,0.08);
    border-left: 5px solid #42B983;
    padding: .6rem .9rem;
    border-radius: .5rem;
    color: white;
    margin-bottom: .4rem;
}}
.analyst-bad {{
    background: rgba(255,99,95,0.08);
    border-left: 5px solid #FF635F;
    padding: .6rem .9rem;
    border-radius: .5rem;
    color: white;
    margin-bottom: .4rem;
}}
.footer {{
    text-align:center;
    color: rgba(255,255,255,0.4);
    margin-top:2.5rem;
    font-size:.7rem;
}}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="tb-header">
  <div>
    <div class="tb-title">🏏 Talking Bat Analytics</div>
    <div class="tb-sub">Purple-Gold US-ANALYTICS Theme • Player Card Generator</div>
  </div>
  <div style="font-size:0.8rem; text-align:right;">
    MVP 1.0<br/>Streamlit Live Version
  </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.title("⚙️ Controls")
file = st.sidebar.file_uploader("Upload ball-by-ball CSV/Excel", type=["csv", "xlsx"])
analysis_type = st.sidebar.selectbox("Analysis type", ["Auto detect", "Batting card", "Bowling card"])

if file is not None:
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
else:
    sample_path = "/mnt/data/talkingbat/sample_data.csv"
    if os.path.exists(sample_path):
        df = pd.read_csv(sample_path)
    else:
        df = pd.DataFrame({
            "match_id":[1]*24,
            "innings":[1]*24,
            "over":[1,1,1,2,2,3,3,3,4,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11],
            "ball":list(range(1,25)),
            "batsman":["Babar Azam"]*12 + ["Komal Khan"]*12,
            "bowler":["Faheem Ashraf"]*24,
            "bowling_action":["RAMF"]*12 + ["OFF BREAK"]*12,
            "batsman_runs":[0,4,1,1,6,0,2,4,1,0,0,4,1,1,0,4,6,1,0,1,0,4,0,6],
            "total_runs":[0,4,1,1,6,0,2,4,1,0,0,4,1,1,0,4,6,1,0,1,0,4,0,6],
            "dismissal_kind":[None]*24,
            "player_dismissed":[None]*24,
            "batting_style":["RHB"]*24,
            "bowling_team":["South Africa"]*24,
            "batting_team":["Pakistan"]*24
        })

batters = sorted(list(df["batsman"].dropna().unique()))
bowlers = sorted(list(df["bowler"].dropna().unique())) if "bowler" in df.columns else []

col1, col2 = st.columns([2,1])
with col1:
    player = st.selectbox("Select player", batters + [b for b in bowlers if b not in batters])
with col2:
    st.metric("Balls in dataset", len(df))

def get_phase(over):
    try:
        o = int(over)
    except:
        return "Unknown"
    if o <= 5:
        return "Powerplay"
    elif o <= 14:
        return "Middle"
    return "Death"

def classify_bowler_action(action: str):
    if not isinstance(action, str):
        return "UNKNOWN"
    a = action.upper()
    if any(k in a for k in ["RAMF","LAMF","FAST","MEDIUM","RFM","LFM"]):
        return "PACE"
    if any(k in a for k in ["OFF","LEG","ORTHODOX","CHINAMAN"]):
        return "SPIN"
    return "UNKNOWN"

def render_batting_card(df, player):
    pdf = df[df["batsman"] == player].copy()
    if pdf.empty:
        st.warning("No batting data for this player.")
        return

    balls = len(pdf)
    runs = pdf["batsman_runs"].sum() if "batsman_runs" in pdf.columns else pdf["total_runs"].sum()
    fours = (pdf["batsman_runs"] == 4).sum() if "batsman_runs" in pdf.columns else 0
    sixes = (pdf["batsman_runs"] == 6).sum() if "batsman_runs" in pdf.columns else 0
    dots = (pdf["total_runs"] == 0).sum() if "total_runs" in pdf.columns else 0

    outs = df[df.get("player_dismissed","") == player]
    dismissals = len(outs)

    sr = (runs / balls * 100) if balls else 0
    avg = (runs / dismissals) if dismissals else None
    dot_pct = (dots / balls * 100) if balls else 0
    bnd_pct = ((fours + sixes) / balls * 100) if balls else 0

    pdf["phase"] = pdf["over"].apply(get_phase)
    phase_grp = pdf.groupby("phase").agg(
        Runs=("batsman_runs","sum"),
        Balls=("batsman_runs","count"),
        Dots=("total_runs", lambda x: (x==0).sum())
    ).reset_index()

    if "bowling_action" in pdf.columns:
        pdf["btype"] = pdf["bowling_action"].apply(classify_bowler_action)
        pv = pdf.groupby("btype").agg(
            Runs=("batsman_runs","sum"),
            Balls=("batsman_runs","count")
        ).reset_index()
    else:
        pv = pd.DataFrame([{"btype":"PACE","Runs":runs,"Balls":balls}])

    t1, t2, t3, t4, t5 = st.columns([1.3,1,1,1,1])
    with t1:
        st.markdown(f"""<div class="tb-card">
        <h3 style="margin-bottom:.3rem;">{player}</h3>
        <p style="margin:0;opacity:.6;">Batting Analysis</p>
        <p style="margin:0; font-size:.7rem; opacity:.5;">Talking Bat Theme</p>
        </div>""", unsafe_allow_html=True)
    with t2:
        st.markdown(f"""<div class="tb-card"><div class="metric-label">Runs</div>
        <div class="metric-value">{runs}</div></div>""", unsafe_allow_html=True)
    with t3:
        st.markdown(f"""<div class="tb-card"><div class="metric-label">Balls</div>
        <div class="metric-value">{balls}</div></div>""", unsafe_allow_html=True)
    with t4:
        st.markdown(f"""<div class="tb-card"><div class="metric-label">SR</div>
        <div class="metric-value">{sr:.1f}</div></div>""", unsafe_allow_html=True)
    with t5:
        st.markdown(f"""<div class="tb-card"><div class="metric-label">Avg</div>
        <div class="metric-value">{avg:.1f if avg else "—"}</div></div>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1.2,1,1])
    with c1:
        st.markdown("<h4 style='color:white;margin-top:1rem;'>Phase Breakdown</h4>", unsafe_allow_html=True)
        st.dataframe(phase_grp, use_container_width=True, hide_index=True)
    with c2:
        st.markdown("<h4 style='color:white;margin-top:1rem;'>Pace vs Spin</h4>", unsafe_allow_html=True)
        st.dataframe(pv, use_container_width=True, hide_index=True)
    with c3:
        st.markdown("<h4 style='color:white;margin-top:1rem;'>Key %</h4>", unsafe_allow_html=True)
        st.markdown(f"""<div class="tb-card">
        <p>Dot%: <b>{dot_pct:.1f}%</b></p>
        <p>Boundary%: <b>{bnd_pct:.1f}%</b></p>
        <p>4s / 6s: <b>{fours} / {sixes}</b></p>
        </div>""", unsafe_allow_html=True)

    st.markdown("<h4 style='color:white;margin-top:1rem;'>Analyst Insights</h4>", unsafe_allow_html=True)
    good = []
    bad = []
    if sr >= 130:
        good.append("Dominant striker vs pace — SR ≥ 130.")
    if dot_pct > 40:
        bad.append("Dot ball % is high — improve strike rotation in middle overs.")
    if not good:
        good.append("Stable middle-order option.")
    if not bad:
        bad.append("Work on spin matchups.")

    for g in good:
        st.markdown(f"<div class='analyst-good'>✅ {g}</div>", unsafe_allow_html=True)
    for b in bad:
        st.markdown(f"<div class='analyst-bad'>⚠️ {b}</div>", unsafe_allow_html=True)

def render_bowling_card(df, player):
    bdf = df[df["bowler"] == player].copy()
    if bdf.empty:
        st.warning("No bowling data for this player.")
        return

    balls = len(bdf)
    runs = bdf["total_runs"].sum()
    wickets = bdf["player_dismissed"].notna().sum() if "player_dismissed" in bdf.columns else 0
    dots = (bdf["total_runs"] == 0).sum()
    overs = balls / 6 if balls else 0
    econ = runs / overs if overs else 0
    avg = runs / wickets if wickets else 0
    sr = balls / wickets if wickets else 0
    bpb = balls / ((bdf["batsman_runs"].isin([4,6])).sum() or 1)
    bpd = balls / (wickets or 1)

    bdf["phase"] = bdf["over"].apply(get_phase)
    phase = bdf.groupby("phase").agg(
        Balls=("total_runs","count"),
        Runs=("total_runs","sum"),
        Dots=("total_runs", lambda x: (x==0).sum()),
        Wkts=("player_dismissed", lambda x: x.notna().sum())
    ).reset_index()

    if "batting_style" in bdf.columns:
        lhr = bdf.groupby("batting_style").agg(
            Balls=("total_runs","count"),
            Runs=("total_runs","sum"),
            Wkts=("player_dismissed", lambda x: x.notna().sum())
        ).reset_index()
    else:
        lhr = pd.DataFrame([{"batting_style":"RHB","Balls":balls,"Runs":runs,"Wkts":wickets}])

    t1, t2, t3, t4, t5, t6 = st.columns([1.3,1,1,1,1,1])
    with t1:
        st.markdown(f"""<div class="tb-card">
        <h3 style="margin-bottom:.3rem;">{player}</h3>
        <p style="margin:0;opacity:.6;">Bowling Analysis</p>
        <p style="margin:0; font-size:.7rem; opacity:.5;">Talking Bat Theme</p>
        </div>""", unsafe_allow_html=True)
    with t2:
        st.markdown(f"""<div class="tb-card"><div class="metric-label">Runs</div>
        <div class="metric-value">{runs}</div></div>""", unsafe_allow_html=True)
    with t3:
        st.markdown(f"""<div class="tb-card"><div class="metric-label">Balls</div>
        <div class="metric-value">{balls}</div></div>""", unsafe_allow_html=True)
    with t4:
        st.markdown(f"""<div class="tb-card"><div class="metric-label">Wickets</div>
        <div class="metric-value">{wickets}</div></div>""", unsafe_allow_html=True)
    with t5:
        st.markdown(f"""<div class="tb-card"><div class="metric-label">Econ</div>
        <div class="metric-value">{econ:.1f}</div></div>""", unsafe_allow_html=True)
    with t6:
        dotp = (dots / balls * 100) if balls else 0
        st.markdown(f"""<div class="tb-card"><div class="metric-label">Dot%</div>
        <div class="metric-value">{dotp:.0f}%</div></div>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1.2,1,1])
    with c1:
        st.markdown("<h4 style='color:white;margin-top:1rem;'>Bowling Phase Breakdown</h4>", unsafe_allow_html=True)
        st.dataframe(phase, use_container_width=True, hide_index=True)
    with c2:
        st.markdown("<h4 style='color:white;margin-top:1rem;'>vs LHB / RHB</h4>", unsafe_allow_html=True)
        st.dataframe(lhr, use_container_width=True, hide_index=True)
    with c3:
        st.markdown("<h4 style='color:white;margin-top:1rem;'>Key Ratios</h4>", unsafe_allow_html=True)
        st.markdown(f"""<div class="tb-card">
        <p>SR: <b>{sr:.1f}</b></p>
        <p>BPB: <b>{bpb:.1f}</b></p>
        <p>BPD: <b>{bpd:.1f}</b></p>
        </div>""", unsafe_allow_html=True)

    st.markdown("<h4 style='color:white;margin-top:1rem;'>Runs Conceded (by Over)</h4>", unsafe_allow_html=True)
    over_runs = bdf.groupby("over")["total_runs"].sum().reset_index()
    fig = px.bar(over_runs, x="over", y="total_runs")
    fig.update_layout(paper_bgcolor=BG, plot_bgcolor=BG, font_color="white", height=280)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<h4 style='color:white;margin-top:1rem;'>Analyst Insights</h4>", unsafe_allow_html=True)
    if econ <= 6:
        st.markdown("<div class='analyst-good'>✅ Economical in Powerplay.</div>", unsafe_allow_html=True)
    if phase[phase["phase"]=="Death"]["Runs"].sum() > phase[phase["phase"]=="Powerplay"]["Runs"].sum():
        st.markdown("<div class='analyst-bad'>⚠️ Expensive in Death overs.</div>", unsafe_allow_html=True)
    if wickets == 0:
        st.markdown("<div class='analyst-bad'>⚠️ Needs wicket-taking options vs RHB.</div>", unsafe_allow_html=True)

if player:
    if analysis_type == "Auto detect":
        bowl_ct = (df["bowler"] == player).sum() if "bowler" in df.columns else 0
        bat_ct = (df["batsman"] == player).sum()
        if bowl_ct > bat_ct:
            render_bowling_card(df, player)
        else:
            render_batting_card(df, player)
    elif analysis_type == "Batting card":
        render_batting_card(df, player)
    else:
        render_bowling_card(df, player)

st.markdown("<div class='footer'>Powered by Talking Bat © 2025 · US-ANALYTICS</div>", unsafe_allow_html=True)
