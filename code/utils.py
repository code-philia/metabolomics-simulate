import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def get_series(df, col):
    """从 DataFrame 中获取列，如果不存在则返回全 0 的 Series"""
    if col in df.columns:
        return df[col]
    return pd.Series(0.0, index=df.index)

def detect_rate_oscillations(df: pd.DataFrame) -> pd.DataFrame:
    """
    分析反应速率是否存在显著震荡
    返回包含震荡检测结果的 DataFrame
    """
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

def generate_dashboard(history_list, filename="dashboard.html", concentrations=None, rates=None, dashboard_title="代谢模拟仪表盘"):
    """
    生成可定制的交互式可视化仪表盘
    
    Args:
        history_list: 包含模拟历史的列表
        filename: 输出 HTML 文件路径
        concentrations: 待显示的代谢物列表，格式为 [(name, label, color, secondary_y), ...]
        rates: 待显示的反应速率列表，格式为 [(name, label, color), ...]
        dashboard_title: 仪表盘总标题
    """
    df = pd.DataFrame(history_list)
    time_steps = df['time'].values
    
    # 默认配置
    if concentrations is None:
        concentrations = [
            ('glucose', 'Glucose(葡萄糖)', 'royalblue', False),
            ('insulin', 'Insulin(胰岛素)', 'orange', False),
            ('glucagon', 'Glucagon(胰高血糖素)', 'violet', False),
        ]
    
    if rates is None:
        rates = [
            ('rate_hexokinase', '己糖激酶 (HK/GK) 反应', 'blue'),
        ]

    # 初始化画布
    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.6, 0.4],
        specs=[[{"secondary_y": True}, {}]],
        subplot_titles=("关键代谢物浓度 (Concentrations)", "关键反应速率 (Reaction Rates)")
    )

    # 创建动画帧
    frames = []
    for t_idx in range(len(time_steps)):
        current_t = time_steps[t_idx]
        history_so_far = df.iloc[:t_idx+1]
        
        frame_data = []
        # 左图：浓度
        for name, label, color, is_secondary in concentrations:
            frame_data.append(go.Scatter(
                x=history_so_far['time'], 
                y=get_series(history_so_far, name), 
                name=label, 
                line=dict(color=color, dash='dot' if is_secondary else 'solid'),
                yaxis="y2" if is_secondary else "y1"
            ))
            
        # 右图：速率
        for name, label, color in rates:
            frame_data.append(go.Scatter(
                x=history_so_far['time'], 
                y=get_series(history_so_far, name), 
                name=label, 
                line=dict(color=color)
            ))
            
        frame = go.Frame(
            data=frame_data,
            name=str(current_t),
            traces=list(range(len(frame_data)))
        )
        frames.append(frame)

    # 添加初始轨迹
    for i, data in enumerate(frames[0].data):
        row, col = 1, 1
        if i >= len(concentrations):
            col = 2
        
        # 判断是否是次坐标轴 (针对浓度图)
        is_secondary = False
        if col == 1:
            is_secondary = concentrations[i][3]
            
        fig.add_trace(data, row=row, col=col, secondary_y=is_secondary)

    # 布局配置
    fig.update_layout(
        title=dashboard_title,
        template="plotly_dark",
        updatemenus=[{
            "type": "buttons",
            "buttons": [{
                "label": "播放",
                "method": "animate",
                "args": [None, {"frame": {"duration": 50, "redraw": True}, "fromcurrent": True}]
            }, {
                "label": "暂停",
                "method": "animate",
                "args": [[None], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}]
            }]
        }],
        sliders=[{
            "steps": [{"args": [[f.name], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}],
                       "label": f.name, "method": "animate"} for f in frames],
            "currentvalue": {"prefix": "时间: "}
        }]
    )
    
    fig.update_yaxes(title="浓度 (mmol/L)", secondary_y=False, row=1, col=1, autorange=True)
    fig.update_xaxes(title="时间 (hours)", row=1, col=1, autorange=True)
    fig.update_xaxes(title="时间 (hours)", row=1, col=2, autorange=True)
    fig.update_yaxes(title="反应速率", row=1, col=2, autorange=True)

    fig.frames = frames
    
    # 保存结果
    outdir = os.path.dirname(filename) or "."
    if outdir:
        os.makedirs(outdir, exist_ok=True)
    
    fig.write_html(filename)
    
    # 保存 CSV 数据
    base = os.path.splitext(os.path.basename(filename))[0]
    
    rate_cols = [c for c in df.columns if c.startswith("rate_")]
    pd.DataFrame({"time": df["time"], **{c: df[c] for c in rate_cols}}).to_csv(os.path.join(outdir, f"{base}_rates.csv"), index=False)
    
    signals = {"insulin", "glucagon", "epinephrine", "cortisol", "inflammation"}
    params = {"oxygen_pressure", "pH", "temperature", "is_postprandial", "insulin_degrading_enzyme_activity", "liver_function", "xenobiotic_load", "insulin_sensitivity", "aldh_activity"}
    metabolite_cols = [c for c in df.columns if c not in signals and c not in params and not c.startswith("rate_") and c != "time"]
    pd.DataFrame({"time": df["time"], **{c: df[c] for c in metabolite_cols}}).to_csv(os.path.join(outdir, f"{base}_metabolites.csv"), index=False)
    
    # 震荡检测
    osc_df = detect_rate_oscillations(df)
    osc_df.to_csv(os.path.join(outdir, f"{base}_oscillations.csv"), index=False)
    
    flagged = osc_df[osc_df["oscillatory"] == True]
    if len(flagged) > 0:
        print(f"[{base}] 检测到下列反应速率存在震荡：")
        for _, r in flagged.iterrows():
            print(f"  - {r['rate']}: 峰数={r['peaks']}, 频率/小时={r['freq_per_hour']:.2f}, 幅度范围={r['range']:.4f}")
    else:
        print(f"[{base}] 未检测到显著的反应速率震荡。")
        
    print(f"Dashboard generated: {filename}")

def run_metabolic_simulation(setup_func, hours=24):
    """
    运行代谢模拟的通用函数
    
    Args:
        setup_func: 接收 (env, system, hour, minute) 并执行自定义逻辑的函数
        hours: 模拟总时长（小时）
    """
    from simulate import MetabolicEnvironment, LiverMetabolismSystem
    env = MetabolicEnvironment()
    system = LiverMetabolismSystem(env)
    
    minutes = int(hours * 60)
    for tt in range(minutes):
        hour = tt / 60.0
        setup_func(env, system, hour, tt)
        system.step(hour)
        
    return env.history
