import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from simulate import MetabolicEnvironment, LiverMetabolismSystem

def _get_series(df, col):
    if col in df.columns:
        return df[col]
    return pd.Series(0.0, index=df.index)

def _detect_rate_oscillations(df: pd.DataFrame) -> pd.DataFrame:
    time = df["time"].values if "time" in df.columns else np.arange(len(df))
    rate_cols = [c for c in df.columns if c.startswith("rate_")]
    results = []
    for col in rate_cols:
        y = df[col].astype(float).values
        if len(y) < 5:
            results.append({"rate": col, "oscillatory": False, "peaks": 0, "freq_per_hour": 0.0, "range": 0.0, "threshold": 0.0})
            continue
        rng = float(np.nanmax(y) - np.nanmin(y))
        thr = max(0.05 * rng, 1e-3)
        dy = np.diff(y)
        s = np.sign(dy)
        sign_change = s[1:] * s[:-1] < 0
        idx = np.where(sign_change)[0]
        # 过滤掉振幅很小的“噪声”拐点
        filt_idx = [i for i in idx if abs(dy[i]) > thr and abs(dy[i+1]) > thr]
        peak_count = len(filt_idx)
        duration = float(time[-1] - time[0]) if len(time) > 1 else float(len(y))
        freq = (peak_count / duration) if duration > 1e-9 else 0.0
        # 判定条件：至少出现若干显著拐点，且单位时间频率较高
        oscillatory = (peak_count >= 5) and (freq >= 0.5) and (rng > thr * 3.0)
        results.append({
            "rate": col,
            "oscillatory": bool(oscillatory),
            "peaks": int(peak_count),
            "freq_per_hour": float(freq),
            "range": float(rng),
            "threshold": float(thr),
        })
    return pd.DataFrame(results)

def generate_nafld_dashboard(history_list, filename="nafld_simulation.html"):
    df = pd.DataFrame(history_list)
    time_steps = df['time'].values
    
    # 2. Initialize Canvas (Updated: 2 columns, removed Topology)
    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.6, 0.4],
        specs=[[{"secondary_y": True}, {}]],
        subplot_titles=("关键代谢物浓度 (Concentrations)", "关键反应速率 (Reaction Rates)")
    )

    # 3. Create Frames
    frames = []
    for t_idx in range(len(time_steps)):
        current_t = time_steps[t_idx]
        history_so_far = df.iloc[:t_idx+1]
        
        frame = go.Frame(
            data=[
                # Left: Concentrations
                go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'insulin'), name="Insulin(胰岛素)", line=dict(color="orange")),
                go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'glucagon'), name="Glucagon(胰高血糖素)", line=dict(color="violet")),
                go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'glucose'), name="Glucose(葡萄糖)", line=dict(color="royalblue")),
                go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'g6p'), name="G6P", line=dict(color="cornflowerblue")),
                go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'f16bp'), name="f16bp(中间体)", line=dict(color="green", dash='dot'), yaxis="y2"),
                go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'pyruvate'), name="Pyruvate(丙酮酸)", line=dict(color="cyan")),
                go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'lactate'), name="Lactate(乳酸)", line=dict(color="teal")),
                go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'acetyl_coa'), name="Acetyl-CoA", line=dict(color="brown")),
                go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'atp'), name="ATP", line=dict(color="gold")),
                go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'adp'), name="ADP", line=dict(color="lightsalmon")),
                go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'nad_plus'), name="NAD+", line=dict(color="lightgreen")),
                go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'nadh'), name="NADH", line=dict(color="darkgrey")),
                go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'glycerol'), name="glycerol(甘油)", line=dict(color="purple")),
                go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'amino_acid'), name="amino_acid(氨基酸)", line=dict(color="darkorange")),
                
                # Right: Rates
                go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'rate_hexokinase'), name="己糖激酶 (HK/GK) 反应", line=dict(color="blue")),
                go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'rate_pfk1'), name="磷酸果糖激酶-1 (PFK-1) 反应", line=dict(color="lime")),
                go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'rate_pyruvate_kinase'), name="丙酮酸激酶 (PK) 反应", line=dict(color="red")),
                go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'rate_lactate_production'), name="乳酸脱氢酶 (LDH) / 丙酮酸去路反应", line=dict(color="cyan")),
                go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'rate_g6pase_G6P_to_Glucose'), name="G6P 释放回血糖", line=dict(color="magenta")),
                go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'rate_orchestrateGluconeogenesis'), name="糖异生", line=dict(color="purple")),
                go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'rate_glycogen_synthesis_total'), name="糖原合成", line=dict(color="lightgreen")),
                go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'rate_glycogen_breakdown_total'), name="糖原分解", line=dict(color="gold")),
            #     go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'rate_pgm_G6P_to_G1P'), name="G6P→G1P 变位", line=dict(color="blue")),
            #     go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'rate_udpGlucoseSynthesis'), name="UDP-葡萄糖合成", line=dict(color="lime")),
            #     go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'rate_glycogenSynthaseStep'), name="糖原合成酶反应", line=dict(color="red")),
            #     go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'rate_branchingEnzymeStep'), name="糖原分支酶反应", line=dict(color="cyan")),
            #     go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'rate_glycogenPhosphorylaseStep'), name="糖原磷酸化酶反应", line=dict(color="magenta")),
            #     go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'rate_debranchingEnzymeStep'), name="去分支酶反应", line=dict(color="purple")),
            #     go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'rate_g1p_to_g6p'), name="G1P→G6P 转化", line=dict(color="darkorange")),
                go.Scatter(x=history_so_far['time'], y=_get_series(history_so_far, 'rate_deNovoLipogenesis'), name="新生脂质合成", line=dict(color="darkorange")),
            ],
            name=str(current_t),
            traces=list(range(14+9)) 
        )
        frames.append(frame)

    # 4. Add Initial Traces
    for i in range(len(frames[0].data)):
        row = 1
        col = 1
        if i >= 12+2: col = 2
        
        secondary_y = False
            
        fig.add_trace(frames[0].data[i], row=row, col=col, secondary_y=secondary_y)

    # 5. Layout
    fig.update_layout(
        template="plotly_dark",
        updatemenus=[{
            "type": "buttons",
            "buttons": [{
                "label": "Play",
                "method": "animate",
                "args": [None, {"frame": {"duration": 50, "redraw": True}, "fromcurrent": True}]
            }, {
                "label": "Pause",
                "method": "animate",
                "args": [[None], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}]
            }]
        }],
        sliders=[{
            "steps": [{"args": [[f.name], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}],
                       "label": f.name, "method": "animate"} for f in frames],
            "currentvalue": {"prefix": "Time: "}
        }]
    )
    fig.layout.uirevision = "nafld"
    
    fig.update_yaxes(title="Concentration (mmol/L)", secondary_y=False, row=1, col=1, autorange=True)

    fig.update_xaxes(title="Time (hours)", row=1, col=1, autorange=True)
    
    fig.update_xaxes(title="Time (hours)", row=1, col=2, autorange=True)
    
    fig.update_yaxes(title="Rate", row=1, col=2, autorange=True)

    fig.frames = frames
    outdir = os.path.dirname(filename) or "."
    os.makedirs(outdir, exist_ok=True)
    fig.write_html(filename)
    rate_cols = [c for c in df.columns if c.startswith("rate_")]
    base = os.path.splitext(os.path.basename(filename))[0]
    csv_path = os.path.join(outdir, f"{base}_rates.csv")
    pd.DataFrame({"time": df["time"], **{c: df[c] for c in rate_cols}}).to_csv(csv_path, index=False)
    signals = {"insulin", "glucagon", "epinephrine", "cortisol", "inflammation"}
    params = {"oxygen_pressure", "pH", "temperature", "is_postprandial", "insulin_degrading_enzyme_activity", "liver_function", "xenobiotic_load", "insulin_sensitivity", "aldh_activity"}
    metabolite_cols = [c for c in df.columns if c not in signals and c not in params and not c.startswith("rate_") and c != "time"]
    csv_path2 = os.path.join(outdir, f"{base}_metabolites.csv")
    pd.DataFrame({"time": df["time"], **{c: df[c] for c in metabolite_cols}}).to_csv(csv_path2, index=False)
    # 自动检测反应速率震荡并输出报告
    osc_df = _detect_rate_oscillations(df)
    osc_path = os.path.join(outdir, f"{base}_oscillations.csv")
    osc_df.to_csv(osc_path, index=False)
    # 控制台摘要
    flagged = osc_df[osc_df["oscillatory"] == True]
    if len(flagged) > 0:
        print("检测到下列反应速率存在震荡：")
        for _, r in flagged.iterrows():
            print(f"  - {r['rate']}: 峰数={r['peaks']}, 频率/小时={r['freq_per_hour']:.2f}, 幅度范围={r['range']:.4f}")
    else:
        print("未检测到显著的反应速率震荡。")
    print(f"NAFLD Dashboard generated: {filename}")

def run_simulation(case_type="normal"):
    env = MetabolicEnvironment()
    system = LiverMetabolismSystem(env)
    
    if case_type == "nafld":
        # NAFLD Setup: High Sugar Diet + Insulin Resistance (or High Insulin)
        # print("Initializing NAFLD Case...")
        # env.setSignal("insulin", 0.8) # High insulin (hyperinsulinemia)
        # env.setSignal("glucagon", 0.2)
        # env.setParameter("insulin_sensitivity", 0.5) # Reduced sensitivity
        # # Initial high glucose
        # env.setMetabolite("glucose", 110.0) 
        env.setSignal("insulin", 0.5)
        env.setSignal("glucagon", 0.5)
        env.setMetabolite("glucose", 5.0)        
    else:
        # Normal Setup
        print("Initializing Normal Case...")
        env.setSignal("insulin", 0.5)
        env.setSignal("glucagon", 0.5)
        env.setMetabolite("glucose", 5.0)
        
    # Run for 8 hours to see accumulation
    hours = 24
    minutes = hours * 60
    
    for tt in range(minutes):
        hour = tt / 60.0
        
        # Feeding Logic
        if case_type == "nafld":
            pass
            # # Continuous high sugar or frequent meals
            # curr_g = env.getMetabolite("glucose")
            # # Maintain high glucose > 100 to trigger DNL
            # if curr_g < 110.0:
            #      env.setMetabolite("glucose", 120.0)
            # if tt % 120 == 0 and tt > 0:
            #     env.setMetabolite("glucose", env.getMetabolite("glucose") + 5.0)
        else:
            # Normal meals (every 6 hours)
            if tt % 360 == 0 and tt > 0:
                env.setMetabolite("glucose", env.getMetabolite("glucose") + 5.0)
            
        system.step(hour)
        
    return env.history

if __name__ == "__main__":
    # 1. Normal Case
    hist_normal = run_simulation("normal")
    generate_nafld_dashboard(hist_normal, "../results/results-html/nafld_normal.html")
    
    # # 2. NAFLD Case
    # hist_nafld = run_simulation("nafld")
    # generate_nafld_dashboard(hist_nafld, "../results/results-html/nafld_abnormal.html")
