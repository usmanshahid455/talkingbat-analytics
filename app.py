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

    outs = df[df.get("player_dismissed", "") == player]
    dismissals = len(outs)

    sr = (runs / balls * 100) if balls else 0
    avg = (runs / dismissals) if dismissals else None
    dot_pct = (dots / balls * 100) if balls else 0
    bnd_pct = ((fours + sixes) / balls * 100) if balls else 0

    pdf["phase"] = pdf["over"].apply(get_phase)
    phase_grp = pdf.groupby("phase").agg(
        Runs=("batsman_runs", "sum"),
        Balls=("batsman_runs", "count"),
        Dots=("total_runs", lambda x: (x == 0).sum())
    ).reset_index()

    if "bowling_action" in pdf.columns:
        pdf["btype"] = pdf["bowling_action"].apply(classify_bowler_action)
        pv = pdf.groupby("btype").agg(
            Runs=("batsman_runs", "sum"),
            Balls=("batsman_runs", "count")
        ).reset_index()
    else:
        pv = pd.DataFrame([{"btype": "PACE", "Runs": runs, "Balls": balls}])

    t1, t2, t3, t4, t5 = st.columns([1.3, 1, 1, 1, 1])
    with t1:
        st.markdown(f"""
        <div class="tb-card">
            <h3 style="margin-bottom:.3rem;">{player}</h3>
            <p style="margin:0;opacity:.6;">Batting Analysis</p>
            <p style="margin:0; font-size:.7rem; opacity:.5;">Talking Bat Theme</p>
        </div>
        """, unsafe_allow_html=True)
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
        avg_text = f"{avg:.1f}" if avg is not None else "—"
        st.markdown(f"""<div class="tb-card"><div class="metric-label">Avg</div>
        <div class="metric-value">{avg_text}</div></div>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1.2, 1, 1])
    with c1:
        st.markdown("<h4 style='color:white;margin-top:1rem;'>Phase Breakdown</h4>", unsafe_allow_html=True)
        st.dataframe(phase_grp, use_container_width=True, hide_index=True)
    with c2:
        st.markdown("<h4 style='color:white;margin-top:1rem;'>Pace vs Spin</h4>", unsafe_allow_html=True)
        st.dataframe(pv, use_container_width=True, hide_index=True)
    with c3:
        st.markdown("<h4 style='color:white;margin-top:1rem;'>Key %</h4>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="tb-card">
            <p>Dot %   <b>{dot_pct:.1f}%</b></p>
            <p>Boundary %  <b>{bnd_pct:.1f}%</b></p>
            <p>4s / 6s  <b>{fours} / {sixes}</b></p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<h4 style='color:white;margin-top:1rem;'>Analyst Insights</h4>", unsafe_allow_html=True)
    good, bad = [], []
    if sr >= 130:
        good.append("⚡ High-impact striker (SR ≥ 130).")
    if dot_pct > 45:
        bad.append("⚠️ Too many dots — improve rotation in middle overs.")
    if bnd_pct < 10:
        bad.append("⚠️ Boundary % low — add more scoring shots in PP.")
    if not good:
        good.append("✅ Stable batter — solid base for partnerships.")
    if not bad:
        bad.append("✅ Balanced innings, no major weak zone.")

    for g in good:
        st.markdown(f"<div class='analyst-good'>{g}</div>", unsafe_allow_html=True)
    for b in bad:
        st.markdown(f"<div class='analyst-bad'>{b}</div>", unsafe_allow_html=True)
