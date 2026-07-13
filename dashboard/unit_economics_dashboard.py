# -*- coding: utf-8 -*-
"""Дашборд юнит-экономики: pandas + plotly -> самодостаточный HTML.

Графики построены на plotly, блок поиска/фильтрации по SKU — встроенный JS
(полный набор SKU выгружается из pandas в страницу).

Запуск из корня проекта:
    python dashboard/unit_economics_dashboard.py
"""

import json

import pandas as pd
import plotly.graph_objects as go

# ----------------------------------------------------------------------------
# Палитра и пороги условного форматирования (маржинальность, %)
# ----------------------------------------------------------------------------
STATUS_COLORS = {
    "good": "#0ca30c",      # >= 40%
    "warning": "#eda100",   # 25-39%
    "serious": "#e07b39",   # 10-24%
    "critical": "#d03b3b",  # < 10%
}
STATUS_BG = {
    "good": "#e7f6e7",
    "warning": "#fdf1d9",
    "serious": "#fbe6dc",
    "critical": "#fbe2e2",
}
SERIES = {"revenue": "#2a78d6", "profit": "#1baf7a", "abc_c": "#eda100"}

FONT = "system-ui, -apple-system, 'Segoe UI', sans-serif"


def margin_status(m: float) -> str:
    if m >= 40:
        return "good"
    if m >= 25:
        return "warning"
    if m >= 10:
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
df = pd.read_csv("data/sku_unit_economics.csv")

total_revenue = df["revenue"].sum()
total_profit = df["profit"].sum()
total_units = int(df["units_sold"].sum())
total_margin = total_profit / total_revenue * 100

cat = (
    df.groupby("category", as_index=False)[["revenue", "profit"]]
    .sum()
)
cat["margin"] = cat["profit"] / cat["revenue"] * 100
cat = cat.sort_values("margin", ascending=True)  # asc: снизу вверх в hbar

brands = (
    df.groupby("brand", as_index=False)
    .agg(revenue=("revenue", "sum"), profit=("profit", "sum"),
         units=("units_sold", "sum"))
    .sort_values("revenue", ascending=False)
)
brands["margin"] = brands["profit"] / brands["revenue"] * 100

# ABC-анализ по накопленной выручке
abc_src = df.sort_values("revenue", ascending=False).copy()
abc_src["cum_share"] = abc_src["revenue"].cumsum() / abc_src["revenue"].sum()
abc_src["group"] = pd.cut(abc_src["cum_share"], [0, 0.8, 0.95, 1.0],
                          labels=["A", "B", "C"])
abc = (
    abc_src.groupby("group", observed=True)
    .agg(sku_count=("article", "count"), revenue=("revenue", "sum"))
    .reindex(["A", "B", "C"])
    .reset_index()
)
abc["share"] = abc["revenue"] / abc["revenue"].sum() * 100

top10 = df.sort_values("profit", ascending=False).head(10)
bottom10 = (
    df[df["revenue"] > 0].sort_values("margin_percent").head(10)
)

# ----------------------------------------------------------------------------
# График 1: маржинальность по категориям (горизонтальные бары со статусом)
# ----------------------------------------------------------------------------
fig_cat = go.Figure(go.Bar(
    x=cat["margin"],
    y=cat["category"],
    orientation="h",
    marker=dict(
        color=[STATUS_COLORS[margin_status(m)] for m in cat["margin"]],
        cornerradius=4,
    ),
    text=[f"{m:.1f}%" for m in cat["margin"]],
    textposition="outside",
    customdata=cat[["revenue", "profit"]],
    hovertemplate=(
        "<b>%{y}</b><br>Маржа: %{x:.1f}%<br>"
        "Выручка: %{customdata[0]:,.0f} ₽<br>"
        "Прибыль: %{customdata[1]:,.0f} ₽<extra></extra>"
    ),
))
fig_cat.update_layout(
    template="plotly_white",
    font=dict(family=FONT, size=13),
    margin=dict(l=10, r=40, t=10, b=30),
    height=300,
    xaxis=dict(range=[0, cat["margin"].max() * 1.25],
               ticksuffix="%", gridcolor="#e1e0d9"),
    yaxis=dict(title=None),
)

# ----------------------------------------------------------------------------
# График 2: выручка и прибыль по брендам (сгруппированные бары)
# ----------------------------------------------------------------------------
fig_brand = go.Figure()
fig_brand.add_trace(go.Bar(
    x=brands["brand"], y=brands["revenue"], name="Выручка",
    marker=dict(color=SERIES["revenue"], cornerradius=4),
    hovertemplate="<b>%{x}</b><br>Выручка: %{y:,.0f} ₽<extra></extra>",
))
fig_brand.add_trace(go.Bar(
    x=brands["brand"], y=brands["profit"], name="Прибыль",
    marker=dict(color=SERIES["profit"], cornerradius=4),
    customdata=brands[["margin"]],
    hovertemplate=("<b>%{x}</b><br>Прибыль: %{y:,.0f} ₽<br>"
                   "Маржа: %{customdata[0]:.1f}%<extra></extra>"),
))
fig_brand.update_layout(
    template="plotly_white",
    font=dict(family=FONT, size=13),
    barmode="group",
    margin=dict(l=60, r=20, t=10, b=30),
    height=300,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    yaxis=dict(tickformat="~s", gridcolor="#e1e0d9"),
    bargap=0.4, bargroupgap=0.08,
)

# ----------------------------------------------------------------------------
# График 3: ABC-анализ (стековый горизонтальный бар долей выручки)
# ----------------------------------------------------------------------------
abc_colors = {"A": SERIES["revenue"], "B": SERIES["profit"],
              "C": SERIES["abc_c"]}
fig_abc = go.Figure()
for _, r in abc.iterrows():
    fig_abc.add_trace(go.Bar(
        x=[r["share"]], y=[""],
        orientation="h",
        name=f"Группа {r['group']} — {int(r['sku_count']):,} SKU".replace(",", " "),
        marker=dict(color=abc_colors[r["group"]]),
        text=f"{r['share']:.0f}%",
        textposition="inside",
        hovertemplate=(
            f"<b>Группа {r['group']}</b><br>"
            f"SKU: {int(r['sku_count']):,}<br>".replace(",", " ") +
            f"Выручка: {r['revenue']:,.0f} ₽ ({r['share']:.1f}%)<extra></extra>"
        ),
    ))
fig_abc.update_layout(
    template="plotly_white",
    font=dict(family=FONT, size=13),
    barmode="stack",
    margin=dict(l=10, r=10, t=10, b=10),
    height=140,
    legend=dict(orientation="h", yanchor="bottom", y=1.1, x=0,
                traceorder="normal"),
    xaxis=dict(visible=False), yaxis=dict(visible=False),
)

# ----------------------------------------------------------------------------
# HTML-блоки: KPI, таблицы топ/антитоп, данные для поиска по SKU
# ----------------------------------------------------------------------------
def kpi_card(label, value, status=None):
    color = f"style='color:{STATUS_COLORS[status]}'" if status else ""
    return (f"<div class='kpi'><div class='label'>{label}</div>"
            f"<div class='value' {color}>{value}</div></div>")


kpis = "".join([
    kpi_card("Выручка", fmt_money(total_revenue)),
    kpi_card("Прибыль", fmt_money(total_profit)),
    kpi_card("Маржинальность", f"{total_margin:.1f}%",
             margin_status(total_margin)),
    kpi_card("Продано, шт.", f"{total_units:,}".replace(",", " ")),
])


def sku_table_rows(frame: pd.DataFrame) -> str:
    rows = ""
    for _, r in frame.iterrows():
        s = margin_status(r["margin_percent"])
        rows += (
            f"<tr><td>{r['article']}</td><td>{r['brand']}</td>"
            f"<td class='num'>{fmt_money(r['revenue'])}</td>"
            f"<td class='num'>{fmt_money(r['profit'])}</td>"
            f"<td class='num'><span class='badge' style='background:{STATUS_BG[s]};"
            f"color:{STATUS_COLORS[s]}'>{r['margin_percent']:.1f}%</span></td></tr>"
        )
    return rows


all_sku = df[["article", "brand", "category", "units_sold",
              "revenue", "profit", "margin_percent"]].copy()
all_sku.columns = ["article", "brand", "category", "units",
                   "revenue", "profit", "margin"]
all_sku["revenue"] = all_sku["revenue"].round(0).astype(int)
all_sku["profit"] = all_sku["profit"].round(0).astype(int)
all_sku["margin"] = all_sku["margin"].round(1)
all_sku_json = json.dumps(all_sku.to_dict(orient="records"),
                          ensure_ascii=False, separators=(",", ":"))

chart_cat = fig_cat.to_html(full_html=False, include_plotlyjs="inline",
                            config={"displayModeBar": False},
                            div_id="chart-cat")
chart_brand = fig_brand.to_html(full_html=False, include_plotlyjs=False,
                                config={"displayModeBar": False},
                                div_id="chart-brand")
chart_abc = fig_abc.to_html(full_html=False, include_plotlyjs=False,
                            config={"displayModeBar": False},
                            div_id="chart-abc")

status_colors_json = json.dumps(STATUS_COLORS)
status_bg_json = json.dumps(STATUS_BG)

html = f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8" />
<title>Юнит-экономика — 2025</title>
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
  .card {{
    background: #fcfcfb; border: 1px solid rgba(11,11,11,.1);
    border-radius: 12px; padding: 20px 22px; margin-bottom: 20px;
  }}
  .card h2 {{ font-size: 15px; font-weight: 600; margin: 0 0 4px; }}
  .card .sub {{ font-size: 12.5px; color: #898781; margin: 0 0 14px; }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
  @media (max-width: 860px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ text-align: left; font-weight: 600; color: #52514e; font-size: 12px;
       padding: 8px 10px; border-bottom: 1px solid rgba(11,11,11,.1);
       white-space: nowrap; }}
  td {{ padding: 8px 10px; border-bottom: 1px solid rgba(11,11,11,.1);
       font-variant-numeric: tabular-nums; white-space: nowrap; }}
  tbody tr:last-child td {{ border-bottom: none; }}
  td.num, th.num {{ text-align: right; }}
  .badge {{ display: inline-block; padding: 2px 9px; border-radius: 999px;
           font-weight: 650; font-size: 12.5px; }}
  .table-scroll {{ overflow-x: auto; }}
  .filter-row {{ display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 12px; }}
  .filter-input {{
    flex: 1 1 260px; padding: 9px 12px; border-radius: 8px;
    border: 1px solid rgba(11,11,11,.1); background: #f9f9f7;
    color: #0b0b0b; font-size: 13px; font-family: inherit;
  }}
  .filter-input:focus {{ outline: 2px solid #2a78d6; outline-offset: -1px; }}
  .filter-select {{
    padding: 9px 10px; border-radius: 8px; border: 1px solid rgba(11,11,11,.1);
    background: #f9f9f7; color: #0b0b0b; font-size: 13px; font-family: inherit;
  }}
  .chip-row {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 6px; }}
  .chip {{
    display: flex; align-items: center; gap: 6px; padding: 5px 12px;
    border-radius: 999px; border: 1px solid rgba(11,11,11,.1);
    background: #f9f9f7; color: #52514e; font-size: 12.5px; font-weight: 600;
    cursor: pointer; user-select: none;
  }}
  .chip .dot {{ width: 8px; height: 8px; border-radius: 50%; }}
  .chip[data-active="false"] {{ opacity: .45; }}
  .chip-reset {{ color: #898781; text-decoration: underline; background: none;
                border: none; cursor: pointer; font-size: 12.5px;
                font-family: inherit; padding: 5px 4px; }}
  .summary {{ font-size: 12.5px; color: #52514e; margin: 4px 0 14px; }}
  .summary b {{ color: #0b0b0b; }}
  th.sortable {{ cursor: pointer; }}
  th.sortable:hover {{ color: #0b0b0b; }}
  .sort-arrow {{ display: inline-block; width: 10px; font-size: 10px; }}
  .footer-row {{ display: flex; align-items: center; gap: 14px; margin-top: 12px;
                font-size: 12.5px; color: #898781; }}
  .show-more {{ padding: 7px 14px; border-radius: 8px;
               border: 1px solid rgba(11,11,11,.1); background: #f9f9f7;
               font-size: 12.5px; font-weight: 600; cursor: pointer;
               font-family: inherit; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Юнит-экономика, 2025</h1>
  <p class="subtitle">Синтетические данные · {f"{len(df):,}".replace(",", " ")} SKU · 3 бренда · построено на Python + Plotly</p>

  <div class="kpi-row">{kpis}</div>

  <div class="grid-2">
    <div class="card">
      <h2>Маржинальность по категориям</h2>
      <p class="sub">Цвет — статус маржи (&ge;40% хорошо · 25–39% средне · 10–24% низко · &lt;10% критично)</p>
      {chart_cat}
    </div>
    <div class="card">
      <h2>Выручка и прибыль по брендам</h2>
      <p class="sub">Абсолютные значения за год</p>
      {chart_brand}
    </div>
  </div>

  <div class="card">
    <h2>ABC-анализ по выручке SKU</h2>
    <p class="sub">A — топ-80% выручки, B — следующие 15%, C — остаток 5%</p>
    {chart_abc}
  </div>

  <div class="grid-2">
    <div class="card">
      <h2>ТОП-10 SKU по прибыли</h2>
      <p class="sub">Лидеры юнит-экономики</p>
      <div class="table-scroll"><table>
        <thead><tr><th>Артикул</th><th>Бренд</th><th class="num">Выручка</th>
        <th class="num">Прибыль</th><th class="num">Маржа</th></tr></thead>
        <tbody>{sku_table_rows(top10)}</tbody>
      </table></div>
    </div>
    <div class="card">
      <h2>Проблемные SKU (низкая маржа)</h2>
      <p class="sub">Кандидаты на пересмотр цены / вывод из ассортимента</p>
      <div class="table-scroll"><table>
        <thead><tr><th>Артикул</th><th>Бренд</th><th class="num">Выручка</th>
        <th class="num">Прибыль</th><th class="num">Маржа</th></tr></thead>
        <tbody>{sku_table_rows(bottom10)}</tbody>
      </table></div>
    </div>
  </div>

  <div class="card">
    <h2>Поиск и фильтр по SKU</h2>
    <p class="sub">{f"{len(df):,}".replace(",", " ")} SKU · поиск по артикулу, фильтры по бренду, категории и статусу маржи — работают вместе</p>
    <div class="filter-row">
      <input type="text" id="skuSearch" class="filter-input"
             placeholder="Поиск по артикулу, например ДЕТ-004188" />
      <select id="brandFilter" class="filter-select"><option value="">Все бренды</option></select>
      <select id="categoryFilter" class="filter-select"><option value="">Все категории</option></select>
    </div>
    <div class="chip-row" id="statusChips"></div>
    <button class="chip-reset" id="resetFilters">Сбросить фильтры</button>
    <div class="summary" id="summary"></div>
    <div class="table-scroll"><table>
      <thead><tr>
        <th class="sortable" data-key="article">Артикул<span class="sort-arrow"></span></th>
        <th class="sortable" data-key="brand">Бренд<span class="sort-arrow"></span></th>
        <th class="sortable" data-key="category">Категория<span class="sort-arrow"></span></th>
        <th class="num sortable" data-key="units">Продано<span class="sort-arrow"></span></th>
        <th class="num sortable" data-key="revenue">Выручка<span class="sort-arrow"></span></th>
        <th class="num sortable" data-key="profit">Прибыль<span class="sort-arrow"></span></th>
        <th class="num sortable" data-key="margin">Маржа<span class="sort-arrow"></span></th>
      </tr></thead>
      <tbody id="skuTable"></tbody>
    </table></div>
    <div class="footer-row" id="footerRow"></div>
  </div>
</div>

<script>
const ALL_SKU = {all_sku_json};
const STATUS_COLORS = {status_colors_json};
const STATUS_BG = {status_bg_json};
const STATUS_META = {{
  good: "Хорошая маржа ≥40%", warning: "Средняя 25–39%",
  serious: "Низкая 10–24%", critical: "Критичная <10%"
}};

const state = {{
  search: "", brand: "", category: "",
  statuses: new Set(["good", "warning", "serious", "critical"]),
  sortKey: "profit", sortDir: "desc", visible: 50,
}};

function marginStatus(m) {{
  if (m >= 40) return "good";
  if (m >= 25) return "warning";
  if (m >= 10) return "serious";
  return "critical";
}}
function fmtMoney(v) {{
  const s = v < 0 ? "-" : "", a = Math.abs(v);
  if (a >= 1e9) return s + (a/1e9).toFixed(2) + " млрд ₽";
  if (a >= 1e6) return s + (a/1e6).toFixed(1) + " млн ₽";
  if (a >= 1e3) return s + (a/1e3).toFixed(0) + " тыс ₽";
  return s + a.toFixed(0) + " ₽";
}}
function fmtInt(v) {{ return v.toLocaleString("ru-RU"); }}

(function init() {{
  const brandSel = document.getElementById("brandFilter");
  const catSel = document.getElementById("categoryFilter");
  [...new Set(ALL_SKU.map(r => r.brand))].sort((a,b)=>a.localeCompare(b,"ru"))
    .forEach(b => brandSel.append(new Option(b, b)));
  [...new Set(ALL_SKU.map(r => r.category))].sort((a,b)=>a.localeCompare(b,"ru"))
    .forEach(c => catSel.append(new Option(c, c)));

  const chips = document.getElementById("statusChips");
  chips.innerHTML = Object.keys(STATUS_META).map(s =>
    `<div class="chip" data-status="${{s}}" data-active="true">
       <span class="dot" style="background:${{STATUS_COLORS[s]}}"></span>${{STATUS_META[s]}}
     </div>`).join("");
  chips.querySelectorAll(".chip").forEach(chip => chip.addEventListener("click", () => {{
    const s = chip.dataset.status;
    if (state.statuses.has(s)) {{ state.statuses.delete(s); chip.dataset.active = "false"; }}
    else {{ state.statuses.add(s); chip.dataset.active = "true"; }}
    state.visible = 50; render();
  }}));

  let timer = null;
  document.getElementById("skuSearch").addEventListener("input", e => {{
    clearTimeout(timer);
    timer = setTimeout(() => {{
      state.search = e.target.value.trim().toUpperCase();
      state.visible = 50; render();
    }}, 120);
  }});
  brandSel.addEventListener("change", e => {{ state.brand = e.target.value; state.visible = 50; render(); }});
  catSel.addEventListener("change", e => {{ state.category = e.target.value; state.visible = 50; render(); }});

  document.getElementById("resetFilters").addEventListener("click", () => {{
    Object.assign(state, {{ search: "", brand: "", category: "",
      statuses: new Set(["good","warning","serious","critical"]),
      sortKey: "profit", sortDir: "desc", visible: 50 }});
    document.getElementById("skuSearch").value = "";
    brandSel.value = ""; catSel.value = "";
    chips.querySelectorAll(".chip").forEach(c => c.dataset.active = "true");
    render();
  }});

  document.querySelectorAll("th.sortable").forEach(th => th.addEventListener("click", () => {{
    const key = th.dataset.key;
    if (state.sortKey === key) state.sortDir = state.sortDir === "desc" ? "asc" : "desc";
    else {{
      state.sortKey = key;
      state.sortDir = ["article","brand","category"].includes(key) ? "asc" : "desc";
    }}
    render();
  }}));
}})();

function getFiltered() {{
  let rows = ALL_SKU;
  if (state.search) rows = rows.filter(r => r.article.toUpperCase().includes(state.search));
  if (state.brand) rows = rows.filter(r => r.brand === state.brand);
  if (state.category) rows = rows.filter(r => r.category === state.category);
  rows = rows.filter(r => state.statuses.has(marginStatus(r.margin)));
  const dir = state.sortDir === "asc" ? 1 : -1, key = state.sortKey;
  return [...rows].sort((a, b) =>
    typeof a[key] === "string" ? a[key].localeCompare(b[key], "ru") * dir
                               : (a[key] - b[key]) * dir);
}}

function render() {{
  const filtered = getFiltered();
  const summary = document.getElementById("summary");
  if (!filtered.length) {{
    summary.textContent = "Ничего не найдено по текущим фильтрам";
  }} else {{
    const rev = filtered.reduce((s, r) => s + r.revenue, 0);
    const prof = filtered.reduce((s, r) => s + r.profit, 0);
    const m = rev ? prof / rev * 100 : 0;
    summary.innerHTML = `Найдено <b>${{fmtInt(filtered.length)}}</b> SKU · ` +
      `выручка <b>${{fmtMoney(rev)}}</b> · прибыль <b>${{fmtMoney(prof)}}</b> · ` +
      `средняя маржа <b>${{m.toFixed(1)}}%</b>`;
  }}

  document.querySelectorAll(".sort-arrow").forEach(el => el.textContent = "");
  const arrow = document.querySelector(`th[data-key="${{state.sortKey}}"] .sort-arrow`);
  if (arrow) arrow.textContent = state.sortDir === "asc" ? "▲" : "▼";

  const shown = filtered.slice(0, state.visible);
  document.getElementById("skuTable").innerHTML = shown.map(r => {{
    const s = marginStatus(r.margin);
    return `<tr><td>${{r.article}}</td><td>${{r.brand}}</td><td>${{r.category}}</td>
      <td class="num">${{fmtInt(r.units)}}</td>
      <td class="num">${{fmtMoney(r.revenue)}}</td>
      <td class="num">${{fmtMoney(r.profit)}}</td>
      <td class="num"><span class="badge" style="background:${{STATUS_BG[s]}};color:${{STATUS_COLORS[s]}}">${{r.margin.toFixed(1)}}%</span></td></tr>`;
  }}).join("") || `<tr><td colspan="7" style="text-align:center;color:#898781;padding:24px">Ничего не найдено</td></tr>`;

  const footer = document.getElementById("footerRow");
  footer.innerHTML = `<span>Показано ${{fmtInt(shown.length)}} из ${{fmtInt(filtered.length)}}</span>` +
    (filtered.length > shown.length
      ? `<button class="show-more" id="showMore">Показать ещё</button>` : "");
  const btn = document.getElementById("showMore");
  if (btn) btn.addEventListener("click", () => {{ state.visible += 100; render(); }});
}}

render();
</script>
</body>
</html>
"""

out_path = "dashboard/unit_economics_dashboard.html"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"OK: {out_path}")
print(f"Выручка: {total_revenue:,.0f} | Прибыль: {total_profit:,.0f} | "
      f"Маржа: {total_margin:.1f}% | SKU: {len(df)}")
