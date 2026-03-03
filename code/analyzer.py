import pandas as pd
import numpy as np

class MetabolismTracer:
    def __init__(self, history):
        self.history = history
        self.df = pd.DataFrame(history)

    def trace_range(self, metabolite: str, t_start: float, t_end: float, top_n: int = 5):
        """
        在指定时间范围内 (t_start -> t_end) 追溯某物质变化的累计贡献原因
        """
        # 1. 筛选时间范围内的记录
        mask = (self.df['time'] >= t_start) & (self.df['time'] <= t_end)
        range_data = self.df[mask]
        
        if range_data.empty:
            print(f"❌ 未找到 {t_start}h 到 {t_end}h 之间的数据。")
            return

        # 2. 计算累计变化
        val_start = range_data.iloc[0][metabolite]
        val_end = range_data.iloc[-1][metabolite]
        total_delta = val_end - val_start
        trend = "上升 📈" if total_delta > 0 else "下降 📉"

        print(f"\n{'='*70}")
        print(f" 🔍 时段趋势报告: [{metabolite}] 在 {t_start:.2f}h ➔ {t_end:.2f}h")
        print(f" 总体趋势: {val_start:.4f} ➔ {val_end:.4f} (累计 {trend} {total_delta:.4f})")
        print(f"{'='*70}")

        # 3. 累计所有反应的贡献 (Integration)
        cumulative_impacts = {}

        # 遍历范围内每一帧的 audit 记录
        for idx in range_data.index:
            # 兼容你的字段名：可能是 'audit' 或 'step_audit'
            record = self.history[idx]
            audit = record.get('audit') or record.get('step_audit') or {}
            
            for rxn_name, outputs in audit.items():
                if metabolite in outputs:
                    val = outputs[metabolite]
                    cumulative_impacts[rxn_name] = cumulative_impacts.get(rxn_name, 0.0) + val

        # 4. 转换为 DataFrame 排序展示
        if not cumulative_impacts:
            print(f"❌ 在此时间段内，没有发现直接改变 {metabolite} 的反应记录。")
            return

        impact_list = [{"reaction": k, "total_contribution": v} for k, v in cumulative_impacts.items()]
        cdf = pd.DataFrame(impact_list).sort_values(by="total_contribution")

        print(f"\n📉 累计主要消耗源 (Total Consumption):")
        consumers = cdf[cdf['total_contribution'] < 0]
        if consumers.empty:
            print("  (无明显消耗)")
        else:
            # 计算贡献占比
            consumers = consumers.copy()
            consumers['share'] = (consumers['total_contribution'] / consumers['total_contribution'].sum() * 100).round(1)
            print(consumers.head(top_n).to_string(index=False, formatters={'share': lambda x: f"{x}%"}))

        print(f"\n📈 累计主要生产源 (Total Production):")
        producers = cdf[cdf['total_contribution'] > 0].sort_values(by="total_contribution", ascending=False)
        if producers.empty:
            print("  (无明显生产)")
        else:
            producers = producers.copy()
            producers['share'] = (producers['total_contribution'] / producers['total_contribution'].sum() * 100).round(1)
            print(producers.head(top_n).to_string(index=False, formatters={'share': lambda x: f"{x}%"}))

        # 5. 关键因素相关性分析 (Correlation)
        print(f"\n💡 关键驱动因素分析 (Potential Drivers):")
        clues = ['atp', 'insulin', 'glucagon', 'oxygen', 'nadh']
        for c in clues:
            if c in range_data.columns and c != metabolite:
                c_start = range_data.iloc[0][c]
                c_end = range_data.iloc[-1][c]
                c_delta = c_end - c_start
                if abs(c_delta) > 1e-3:
                    c_trend = "↑" if c_delta > 0 else "↓"
                    print(f"  - {c:12}: {c_start:.4f} ➔ {c_end:.4f} ({c_trend})")

    # 保留原有的单点追溯功能
    def trace_point(self, metabolite: str, time_h: float, top_n: int = 5):
        return self.trace_range(metabolite, time_h, time_h, top_n)