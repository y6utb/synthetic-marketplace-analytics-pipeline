# -*- coding: utf-8 -*-
"""План/Факт дашборд: pandas + plotly -> самодостаточный HTML.

Запуск из корня проекта:
    python dashboard/plan_fact_dashboard.py
"""

import pandas as pd
import plotly.graph_objects as go

# ----------------------------------------------------------------------------
# Палитра и пороги условного форматирования (% выполнения плана)
# ----------------------------------------------------------------------------
STATUS_COLORS = {
    "good": "#0ca30c",      # >= 100%
    "warning": "#eda100",   # 80-99%
    "serious": "#e07b39",   # 50-79%
    "critical": "#d03b3b",  # < 50%
}
STATUS_BG = {
    "good": "#e7f6e7",
    "warning": "#fdf1d9",
    "serious": "#fbe6dc",
    "critical": "#fbe2e2",
}

MONTH_NAMES = ["янв", "фев", "мар", "апр", "май", "июн",
               "июл", "авг", "сен", "окт", "ноя", "дек"]

FONT = "system-ui, -apple-system, 'Segoe UI', sans-serif"


def status_of(pct: float) -> str:
    if pct >= 100:
        return "good"
    if pct >= 80:
        return "warning"
    if pct >= 50:
        return "serious"
    return "critical"


def fmt_money(v: float) -> str:
    sign = "-" if v < 0 else ""
    a = abs(v)
    if a >= 1e9:
        return f"{sign}{a / 1e9:.2f} млрд ₽"
    if a >= 1e6:
        return f"{sign}{a / 1e6:.1f} млн ₽"
    if a >= 1e3:
        return f"{sign}{a / 1e3:.0f} тыс ₽"
    return f"{sign}{a:.0f} ₽"


# ----------------------------------------------------------------------------
# Данные
# ----------------------------------------------------------------------------
df = pd.read_csv("data/plan_fact.csv")
df["month"] = pd.to_datetime(df["month"])
df["completion"] = df["fact_revenue"] / df["plan_revenue"] * 100

monthly = (
    df.groupby("month", as_index=False)[["plan_revenue", "fact_revenue"]]
    .sum()
    .sort_values("month")
)
monthly["gap"] = monthly["fact_revenue"] - monthly["plan_revenue"]
monthly["completion"] = monthly["fact_revenue"] / monthly["plan_revenue"] * 100
monthly["label"] = monthly["month"].dt.month.map(lambda m: MONTH_NAMES[m - 1])

brands = (
    df.groupby("brand", as_index=False)[["plan_revenue", "fact_revenue"]]
    .sum()
    .sort_values("fact_revenue", ascending=False)
)
brands["gap"] = brands["fact_revenue"] - brands["plan_revenue"]
brands["completion"] = brands["fact_revenue"] / brands["plan_revenue"] * 100

total_plan = df["plan_revenue"].sum()
total_fact = df["fact_revenue"].sum()
total_gap = total_fact - total_plan
total_completion = total_fact / total_plan * 100

# ----------------------------------------------------------------------------
# График 1: факт по месяцам (цвет = статус выполнения) + линия плана
# ----------------------------------------------------------------------------
bar_colors = [STATUS_COLORS[status_of(p)] for p in monthly["completion"]]

fig_monthly = go.Figure()
fig_monthly.add_trace(go.Bar(
    x=monthly["label"],
    y=monthly["fact_revenue"],
    name="Факт",
    marker=dict(color=bar_colors, cornerradius=4),
    customdata=monthly[["plan_revenue", "gap", "completion"]],
    hovertemplate=(
        "<b>%{x} 2025</b><br>"
        "Факт: %{y:,.0f} ₽<br>"
        "План: %{customdata[0]:,.0f} ₽<br>"
        "Разрыв: %{customdata[1]:,.0f} ₽<br>"
        "Выполнение: %{customdata[2]:.1f}%<extra></extra>"
    ),
))
fig_monthly.add_trace(go.Scatter(
    x=monthly["label"],
    y=monthly["plan_revenue"],
    name="План",
    mode="lines+markers",
    line=dict(color="#898781", width=2, dash="dash"),
    marker=dict(size=7, color="#898781"),
    hovertemplate="<b>%{x} 2025</b><br>План: %{y:,.0f} ₽<extra></extra>",
))
fig_monthly.update_layout(
    template="plotly_white",
    font=dict(family=FONT, size=13),
    margin=dict(l=60, r=20, t=10, b=40),
    height=380,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    yaxis=dict(title=None, tickformat="~s", gridcolor="#e1e0d9"),
    xaxis=dict(title=None),
    bargap=0.45,
)

# ----------------------------------------------------------------------------
# График 2: тепловая карта выполнения плана (бренд x месяц)
# ----------------------------------------------------------------------------
heat = df.pivot_table(index="brand", columns="month",
                      values="completion").sort_index()
heat_x = [MONTH_NAMES[m.month - 1] for m in heat.columns]

# дискретная шкала по статусам: <50 красный, 50-80 оранжевый, 80-100 жёлтый, >=100 зелёный
zmax = 130
colorscale = [
    [0.0, STATUS_BG["critical"]],
    [50 / zmax, STATUS_BG["critical"]],
    [50 / zmax, STATUS_BG["serious"]],
    [80 / zmax, STATUS_BG["serious"]],
    [80 / zmax, STATUS_BG["warning"]],
    [100 / zmax, STATUS_BG["warning"]],
    [100 / zmax, STATUS_BG["good"]],
    [1.0, STATUS_BG["good"]],
]
text_colors = heat.map(lambda v: STATUS_COLORS[status_of(v)])

fig_heat = go.Figure(go.Heatmap(
    z=heat.values,
    x=heat_x,
    y=heat.index,
    zmin=0, zmax=zmax,
    colorscale=colorscale,
    showscale=False,
    xgap=3, ygap=3,
    text=[[f"{v:.0f}%" for v in row] for row in heat.values],
    texttemplate="%{text}",
    textfont=dict(size=12),
    hovertemplate="<b>%{y}</b><br>%{x} 2025 · выполнение: %{z:.1f}%<extra></extra>",
))
fig_heat.update_layout(
    template="plotly_white",
    font=dict(family=FONT, size=13),
    margin=dict(l=10, r=10, t=10, b=10),
    height=220,
    yaxis=dict(autorange="reversed"),
)

# ----------------------------------------------------------------------------
# HTML-сборка: KPI-карточки + таблица брендов + графики plotly
# ----------------------------------------------------------------------------
def kpi_card(label: str, value: str, status: str | None = None,
             note: str | None = None) -> str:
    color = f"color:{STATUS_COLORS[status]}" if status else ""
    note_html = (
        f"<div class='note' style='{color}'>{note}</div>" if note else ""
    )
    return (
        f"<div class='kpi'><div class='label'>{label}</div>"
        f"<div class='value' style='{color}'>{value}</div>{note_html}</div>"
    )


kpis = "".join([
    kpi_card("План на год", fmt_money(total_plan)),
    kpi_card("Факт на год", fmt_money(total_fact)),
    kpi_card("Разрыв (факт − план)", fmt_money(total_gap), "critical"),
    kpi_card("Выполнение плана", f"{total_completion:.1f}%",
             status_of(total_completion),
             "план выполнен" if total_completion >= 100 else "ниже плана"),
])

brand_rows = ""
for _, r in brands.iterrows():
    s = status_of(r["completion"])
    brand_rows += (
        f"<tr><td>{r['brand']}</td>"
        f"<td class='num'>{fmt_money(r['plan_revenue'])}</td>"
        f"<td class='num'>{fmt_money(r['fact_revenue'])}</td>"
        f"<td class='num' style='color:{STATUS_COLORS['critical']}'>"
        f"{fmt_money(r['gap'])}</td>"
        f"<td class='num'><span class='badge' style='background:{STATUS_BG[s]};"
        f"color:{STATUS_COLORS[s]}'>{r['completion']:.1f}%</span></td></tr>"
    )

chart_monthly = fig_monthly.to_html(
    full_html=False, include_plotlyjs="inline",
    config={"displayModeBar": False}, div_id="chart-monthly")
chart_heat = fig_heat.to_html(
    full_html=False, include_plotlyjs=False,
    config={"displayModeBar": False}, div_id="chart-heat")

html = f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8" />
<title>План / Факт — выручка 2025</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    font-family: {FONT};
    background: #f9f9f7; color: #0b0b0b; margin: 0;
    padding: 32px clamp(16px, 4vw, 48px) 64px;
  }}
  .wrap {{ max-width: 1160px; margin: 0 auto; }}
  h1 {{ font-size: 22px; font-weight: 650; margin: 0 0 4px; }}
  .subtitle {{ color: #52514e; font-size: 14px; margin: 0 0 28px; }}
  .kpi-row {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 20px; }}
  .kpi {{
    flex: 1 1 220px; background: #fcfcfb; border: 1px solid rgba(11,11,11,.1);
    border-radius: 12px; padding: 18px 20px;
  }}
  .kpi .label {{ font-size: 12.5px; color: #52514e; margin-bottom: 8px; }}
  .kpi .value {{ font-size: 30px; font-weight: 650; line-height: 1.1; }}
  .kpi .note {{ font-size: 12.5px; margin-top: 6px; font-weight: 600; }}
  .card {{
    background: #fcfcfb; border: 1px solid rgba(11,11,11,.1);
    border-radius: 12px; padding: 20px 22px; margin-bottom: 20px;
  }}
  .card h2 {{ font-size: 15px; font-weight: 600; margin: 0 0 4px; }}
  .card .sub {{ font-size: 12.5px; color: #898781; margin: 0 0 14px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ text-align: left; font-weight: 600; color: #52514e; font-size: 12px;
       padding: 8px 10px; border-bottom: 1px solid rgba(11,11,11,.1); }}
  td {{ padding: 8px 10px; border-bottom: 1px solid rgba(11,11,11,.1);
       font-variant-numeric: tabular-nums; }}
  tbody tr:last-child td {{ border-bottom: none; }}
  td.num, th.num {{ text-align: right; }}
  .badge {{ display: inline-block; padding: 2px 9px; border-radius: 999px;
           font-weight: 650; font-size: 12.5px; }}
  .legend {{ display: flex; gap: 18px; flex-wrap: wrap; font-size: 12.5px;
            color: #52514e; margin-bottom: 8px; }}
  .legend .item {{ display: flex; align-items: center; gap: 6px; }}
  .legend .swatch {{ width: 10px; height: 10px; border-radius: 2px; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>План / Факт — выручка, 2025</h1>
  <p class="subtitle">Синтетические данные · 3 бренда · помесячно · построено на Python + Plotly</p>

  <div class="kpi-row">{kpis}</div>

  <div class="card">
    <h2>Выручка по месяцам: факт vs план</h2>
    <p class="sub">Столбцы окрашены по статусу выполнения плана; пунктирная линия — план</p>
    <div class="legend">
      <span class="item"><span class="swatch" style="background:{STATUS_COLORS['good']}"></span>&ge;100% плана</span>
      <span class="item"><span class="swatch" style="background:{STATUS_COLORS['warning']}"></span>80–99%</span>
      <span class="item"><span class="swatch" style="background:{STATUS_COLORS['serious']}"></span>50–79%</span>
      <span class="item"><span class="swatch" style="background:{STATUS_COLORS['critical']}"></span>&lt;50%</span>
    </div>
    {chart_monthly}
  </div>

  <div class="card">
    <h2>Итоги по брендам</h2>
    <p class="sub">Накопительно за год</p>
    <table>
      <thead><tr><th>Бренд</th><th class="num">План</th><th class="num">Факт</th>
      <th class="num">Разрыв</th><th class="num">Выполнение</th></tr></thead>
      <tbody>{brand_rows}</tbody>
    </table>
  </div>

  <div class="card">
    <h2>Выполнение плана по месяцам и брендам</h2>
    <p class="sub">% от плана; цвет ячейки — статус выполнения</p>
    {chart_heat}
  </div>
</div>
</body>
</html>
"""

out_path = "dashboard/plan_fact_dashboard.html"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"OK: {out_path}")
print(f"План: {total_plan:,.0f} | Факт: {total_fact:,.0f} | "
      f"Выполнение: {total_completion:.1f}%")
