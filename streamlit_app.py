from __future__ import annotations

from dataclasses import dataclass
from io import StringIO

import altair as alt
import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="AI FinOps Command Center",
    page_icon="AF",
    layout="wide",
    initial_sidebar_state="expanded",
)


BUDGET = 118_000
REQUIRED_COLUMNS = {
    "date",
    "vendor",
    "team",
    "cost_model",
    "spend",
    "actions",
}


SAMPLE_CSV = """date,vendor,team,cost_model,service,model,spend,actions,input_tokens,output_tokens,seats,active_users,owner,use_case
2025-11-01,OpenAI,Product,token,API,gpt-4.1,12800,420000,310000000,82000000,0,0,Maya,Support summaries
2025-11-01,Anthropic,Engineering,token,API,claude-sonnet,9300,240000,188000000,51000000,0,0,Yonatan,Code review automation
2025-11-01,GitHub Copilot,Engineering,seat,Coding Assistant,Business,11200,310000,0,0,420,390,Yonatan,Dev productivity
2025-11-01,Cursor,Engineering,seat,Coding Assistant,Pro,5200,86000,0,0,180,143,Yonatan,AI pair programming
2025-11-01,Gemini,Data,usage,API,gemini-pro,6400,155000,120000000,24000000,0,0,Noa,Data classification
2025-11-01,AI SaaS,Marketing,seat,SaaS,Enterprise,7800,91000,0,0,150,124,Daniel,Campaign copy
2025-12-01,OpenAI,Product,token,API,gpt-4.1,14200,460000,344000000,91000000,0,0,Maya,Support summaries
2025-12-01,Anthropic,Engineering,token,API,claude-sonnet,10300,252000,201000000,53000000,0,0,Yonatan,Code review automation
2025-12-01,GitHub Copilot,Engineering,seat,Coding Assistant,Business,11600,318000,0,0,425,396,Yonatan,Dev productivity
2025-12-01,Cursor,Engineering,seat,Coding Assistant,Pro,5900,97000,0,0,194,151,Yonatan,AI pair programming
2025-12-01,Gemini,Data,usage,API,gemini-pro,7100,166000,133000000,27000000,0,0,Noa,Data classification
2025-12-01,AI SaaS,Marketing,seat,SaaS,Enterprise,8200,96000,0,0,152,128,Daniel,Campaign copy
2026-01-01,OpenAI,Product,token,API,gpt-4.1,17100,538000,411000000,105000000,0,0,Maya,Support summaries
2026-01-01,Anthropic,Engineering,token,API,claude-sonnet,11200,276000,223000000,58000000,0,0,Yonatan,Code review automation
2026-01-01,GitHub Copilot,Engineering,seat,Coding Assistant,Business,11900,321000,0,0,431,397,Yonatan,Dev productivity
2026-01-01,Cursor,Engineering,seat,Coding Assistant,Pro,6900,108000,0,0,207,158,Yonatan,AI pair programming
2026-01-01,Gemini,Data,usage,API,gemini-pro,8500,184000,151000000,31000000,0,0,Noa,Data classification
2026-01-01,AI SaaS,Marketing,seat,SaaS,Enterprise,8700,101000,0,0,154,129,Daniel,Campaign copy
2026-02-01,OpenAI,Product,token,API,gpt-4.1,19600,594000,462000000,119000000,0,0,Maya,Support summaries
2026-02-01,Anthropic,Engineering,token,API,claude-sonnet,12400,304000,251000000,64000000,0,0,Yonatan,Code review automation
2026-02-01,GitHub Copilot,Engineering,seat,Coding Assistant,Business,12600,336000,0,0,438,401,Yonatan,Dev productivity
2026-02-01,Cursor,Engineering,seat,Coding Assistant,Pro,8600,132000,0,0,238,166,Yonatan,AI pair programming
2026-02-01,Gemini,Data,usage,API,gemini-pro,9300,201000,169000000,35000000,0,0,Noa,Data classification
2026-02-01,AI SaaS,Marketing,seat,SaaS,Enterprise,9100,108000,0,0,158,132,Daniel,Campaign copy
2026-03-01,OpenAI,Product,token,API,gpt-4.1,23100,684000,535000000,141000000,0,0,Maya,Support summaries
2026-03-01,Anthropic,Engineering,token,API,claude-sonnet,15100,361000,298000000,81000000,0,0,Yonatan,Code review automation
2026-03-01,GitHub Copilot,Engineering,seat,Coding Assistant,Business,13200,346000,0,0,443,405,Yonatan,Dev productivity
2026-03-01,Cursor,Engineering,seat,Coding Assistant,Pro,11100,155000,0,0,278,183,Yonatan,AI pair programming
2026-03-01,Gemini,Data,usage,API,gemini-pro,11200,244000,207000000,43000000,0,0,Noa,Data classification
2026-03-01,AI SaaS,Marketing,seat,SaaS,Enterprise,9800,117000,0,0,161,136,Daniel,Campaign copy
2026-04-01,OpenAI,Product,token,API,gpt-4.1,28600,781000,638000000,162000000,0,0,Maya,Support summaries
2026-04-01,Anthropic,Engineering,token,API,claude-sonnet,17900,408000,351000000,96000000,0,0,Yonatan,Code review automation
2026-04-01,GitHub Copilot,Engineering,seat,Coding Assistant,Business,13900,359000,0,0,449,407,Yonatan,Dev productivity
2026-04-01,Cursor,Engineering,seat,Coding Assistant,Pro,14400,182000,0,0,324,201,Yonatan,AI pair programming
2026-04-01,Gemini,Data,usage,API,gemini-pro,12900,269000,231000000,52000000,0,0,Noa,Data classification
2026-04-01,AI SaaS,Marketing,seat,SaaS,Enterprise,10400,123000,0,0,164,138,Daniel,Campaign copy
"""


@dataclass(frozen=True)
class Recommendation:
    title: str
    owner: str
    savings: float
    rationale: str


RECOMMENDATIONS = [
    Recommendation(
        "Route repetitive classification to lower-cost models",
        "Data Platform",
        9_200,
        "Keep premium LLMs for reasoning-heavy tasks and route predictable batch work to cheaper tiers.",
    ),
    Recommendation(
        "Compress prompts for support summarization",
        "Product",
        7_400,
        "High-volume templates show avoidable input tokens and repeated context blocks.",
    ),
    Recommendation(
        "Rightsize coding assistant licenses",
        "Engineering",
        6_100,
        "Inactive paid seats should be downgraded or moved to a monthly approval workflow.",
    ),
    Recommendation(
        "Consolidate overlapping AI SaaS tools",
        "Procurement",
        4_800,
        "Two paid tools serve similar copy-generation use cases with low utilization.",
    ),
]


def money(value: float) -> str:
    return f"${value:,.0f}"


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized.columns = (
        normalized.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
    )
    return normalized


def load_data(uploaded_file) -> pd.DataFrame:
    if uploaded_file is None:
        df = pd.read_csv(StringIO(SAMPLE_CSV))
    else:
        df = pd.read_csv(uploaded_file)

    df = normalize_columns(df)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        st.error(f"Missing required columns: {', '.join(sorted(missing))}")
        st.stop()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()

    numeric_columns = [
        "spend",
        "actions",
        "input_tokens",
        "output_tokens",
        "seats",
        "active_users",
    ]
    for column in numeric_columns:
        if column not in df.columns:
            df[column] = 0
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    optional_columns = ["service", "model", "owner", "use_case"]
    for column in optional_columns:
        if column not in df.columns:
            df[column] = "Unassigned"
        df[column] = df[column].fillna("Unassigned").astype(str)

    for column in ["vendor", "team", "cost_model"]:
        df[column] = df[column].fillna("Unassigned").astype(str)

    return df


def filter_data(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filters")

    teams = sorted(df["team"].unique())
    vendors = sorted(df["vendor"].unique())
    cost_models = sorted(df["cost_model"].unique())
    min_month = df["month"].min().date()
    max_month = df["month"].max().date()

    selected_teams = st.sidebar.multiselect("Teams", teams, default=teams)
    selected_vendors = st.sidebar.multiselect("Vendors", vendors, default=vendors)
    selected_cost_models = st.sidebar.multiselect("Cost models", cost_models, default=cost_models)
    date_range = st.sidebar.date_input("Month range", value=(min_month, max_month))

    if len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    else:
        start_date, end_date = df["month"].min(), df["month"].max()

    return df[
        df["team"].isin(selected_teams)
        & df["vendor"].isin(selected_vendors)
        & df["cost_model"].isin(selected_cost_models)
        & (df["month"] >= start_date)
        & (df["month"] <= end_date)
    ]


def forecast_month_end(df: pd.DataFrame) -> float:
    monthly_totals = df.groupby("month")["spend"].sum().sort_index()
    if monthly_totals.empty:
        return 0
    if len(monthly_totals) == 1:
        return float(monthly_totals.iloc[-1])

    growth = monthly_totals.pct_change().replace([float("inf"), -float("inf")], 0).fillna(0)
    recent_growth = growth.tail(3).mean()
    bounded_growth = min(max(float(recent_growth), 0.04), 0.35)
    return float(monthly_totals.iloc[-1] * (1 + bounded_growth))


def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    monthly = (
        df.groupby(["month", "team", "vendor", "cost_model"], as_index=False)
        .agg(
            spend=("spend", "sum"),
            actions=("actions", "sum"),
            seats=("seats", "sum"),
            active_users=("active_users", "sum"),
        )
        .sort_values(["team", "vendor", "month"])
    )
    monthly["previous_spend"] = monthly.groupby(["team", "vendor"])["spend"].shift(1)
    monthly["spend_growth"] = (monthly["spend"] - monthly["previous_spend"]) / monthly["previous_spend"]
    monthly["inactive_seats"] = (monthly["seats"] - monthly["active_users"]).clip(lower=0)
    latest_month = monthly["month"].max()

    risks = []
    for _, row in monthly[monthly["month"] == latest_month].iterrows():
        if pd.notna(row["spend_growth"]) and row["spend_growth"] > 0.25:
            risks.append(
                {
                    "risk": "Spend grew more than 25% month over month",
                    "owner": row["team"],
                    "vendor": row["vendor"],
                    "impact": "High" if row["spend_growth"] > 0.35 else "Medium",
                    "policy_action": "Require owner review, use-case tag, and daily threshold",
                    "estimated_impact": row["spend"] - row["previous_spend"],
                }
            )

        if row["cost_model"] == "seat" and row["seats"] > 0:
            inactive_rate = row["inactive_seats"] / row["seats"]
            if inactive_rate > 0.18:
                risks.append(
                    {
                        "risk": "Seat utilization below policy target",
                        "owner": row["team"],
                        "vendor": row["vendor"],
                        "impact": "Medium",
                        "policy_action": "Auto-downgrade inactive users after 21 days",
                        "estimated_impact": row["inactive_seats"] * 30,
                    }
                )

    return pd.DataFrame(risks)


def render_kpis(df: pd.DataFrame) -> None:
    total_spend = float(df["spend"].sum())
    total_actions = float(df["actions"].sum())
    unit_cost = (total_spend / total_actions * 1_000) if total_actions else 0
    forecast = forecast_month_end(df)
    savings = sum(item.savings for item in RECOMMENDATIONS)

    latest_month = df["month"].max()
    previous_month = latest_month - pd.DateOffset(months=1)
    current_spend = df[df["month"] == latest_month]["spend"].sum()
    previous_spend = df[df["month"] == previous_month]["spend"].sum()
    trend = ((current_spend - previous_spend) / previous_spend * 100) if previous_spend else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total AI Spend", money(total_spend), f"{trend:+.1f}% vs previous month")
    c2.metric("Forecasted Month End", money(forecast), f"{money(BUDGET - forecast)} budget delta")
    c3.metric("Cost per 1K AI Actions", f"${unit_cost:,.2f}", "Blended token, seat, usage")
    c4.metric("Optimization Pipeline", money(savings), "Validated monthly savings")


def savings_opportunities_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "category": [
                "Model routing",
                "Prompt optimization",
                "License rightsizing",
                "Tool consolidation",
                "Contract negotiation",
            ],
            "monthly_savings": [9_200, 7_400, 6_100, 4_800, 3_700],
        }
    )


def spend_chart(
    df: pd.DataFrame,
    breakdown: str = "vendor",
    show_budget: bool = True,
    display: str = "Stacked bars",
    height: int = 300,
) -> alt.Chart:
    chart_data = df.groupby(["month", breakdown], as_index=False)["spend"].sum()
    base = alt.Chart(chart_data)

    if display == "Trend lines":
        chart = base.mark_line(point=True).encode(
            x=alt.X("yearmonth(month):T", title="Month"),
            y=alt.Y("sum(spend):Q", title="Spend"),
            color=alt.Color(f"{breakdown}:N", title=breakdown.replace("_", " ").title()),
            tooltip=[
                alt.Tooltip("yearmonth(month):T", title="Month"),
                alt.Tooltip(f"{breakdown}:N", title=breakdown.replace("_", " ").title()),
                alt.Tooltip("sum(spend):Q", title="Spend", format="$,.0f"),
            ],
        )
    else:
        chart = base.mark_bar().encode(
            x=alt.X("yearmonth(month):T", title="Month"),
            y=alt.Y("sum(spend):Q", title="Spend"),
            color=alt.Color(f"{breakdown}:N", title=breakdown.replace("_", " ").title()),
            tooltip=[
                alt.Tooltip("yearmonth(month):T", title="Month"),
                alt.Tooltip(f"{breakdown}:N", title=breakdown.replace("_", " ").title()),
                alt.Tooltip("sum(spend):Q", title="Spend", format="$,.0f"),
            ],
        )

    chart = chart.properties(height=height).interactive()
    if not show_budget:
        return chart

    budget_rule = (
        alt.Chart(pd.DataFrame({"budget": [BUDGET]}))
        .mark_rule(color="#b93838", strokeDash=[6, 6])
        .encode(y="budget:Q")
    )
    return chart + budget_rule


def budget_burn_chart(df: pd.DataFrame, budget: float = BUDGET, threshold: float = 0.85, height: int = 300) -> alt.Chart:
    chart_data = df.groupby("month", as_index=False)["spend"].sum().sort_values("month")
    chart_data["budget_used"] = chart_data["spend"] / max(budget, 1)
    chart_data["budget"] = budget
    chart_data["status"] = "Below threshold"
    chart_data.loc[chart_data["budget_used"] > threshold, "status"] = "Above threshold"
    chart_data.loc[chart_data["budget_used"] > 1, "status"] = "Over budget"

    bars = (
        alt.Chart(chart_data)
        .mark_bar()
        .encode(
            x=alt.X("yearmonth(month):T", title="Month"),
            y=alt.Y("budget_used:Q", title="Budget used", axis=alt.Axis(format="%")),
            color=alt.Color(
                "status:N",
                title=None,
                scale=alt.Scale(
                    domain=["Below threshold", "Above threshold", "Over budget"],
                    range=["#1f8a5b", "#b87316", "#b93838"],
                ),
            ),
            tooltip=[
                alt.Tooltip("yearmonth(month):T", title="Month"),
                alt.Tooltip("spend:Q", title="Spend", format="$,.0f"),
                alt.Tooltip("budget:Q", title="Budget", format="$,.0f"),
                alt.Tooltip("budget_used:Q", title="Budget used", format=".0%"),
                alt.Tooltip("status:N", title="Status"),
            ],
        )
        .properties(height=height)
        .interactive()
    )
    target_line = (
        alt.Chart(pd.DataFrame({"target": [threshold]}))
        .mark_rule(color="#b87316", strokeDash=[6, 6])
        .encode(y="target:Q")
    )
    budget_line = (
        alt.Chart(pd.DataFrame({"target": [1]}))
        .mark_rule(color="#b93838", strokeDash=[6, 6])
        .encode(y="target:Q")
    )
    return bars + target_line + budget_line


def efficiency_chart(df: pd.DataFrame, group_by: str = "vendor", basis: str = "Actions", top_n: int = 8, height: int = 300) -> alt.Chart:
    denominator_column = "actions"
    denominator_label = "actions"
    if basis == "Tokens":
        df = df.assign(total_tokens=df["input_tokens"] + df["output_tokens"])
        denominator_column = "total_tokens"
        denominator_label = "tokens"

    chart_data = (
        df.groupby(group_by, as_index=False)
        .agg(spend=("spend", "sum"), denominator=(denominator_column, "sum"))
        .assign(unit_cost=lambda data: data["spend"] / data["denominator"].clip(lower=1) * 1_000)
        .sort_values("unit_cost", ascending=False)
        .head(top_n)
    )

    return (
        alt.Chart(chart_data)
        .mark_bar()
        .encode(
            x=alt.X("unit_cost:Q", title=f"Cost per 1K {denominator_label}"),
            y=alt.Y(f"{group_by}:N", title=group_by.replace("_", " ").title(), sort="-x"),
            color=alt.value("#3159a4"),
            tooltip=[
                alt.Tooltip(f"{group_by}:N", title=group_by.replace("_", " ").title()),
                alt.Tooltip("spend:Q", title="Spend", format="$,.0f"),
                alt.Tooltip("denominator:Q", title=denominator_label.title(), format=",.0f"),
                alt.Tooltip("unit_cost:Q", title=f"Cost per 1K {denominator_label}", format="$,.2f"),
            ],
        )
        .properties(height=height)
        .interactive()
    )


def token_usage_chart(df: pd.DataFrame, group_by: str = "vendor", token_view: str = "Input vs output", height: int = 300) -> alt.Chart:
    if token_view == "Total tokens":
        chart_data = (
            df.assign(total_tokens=df["input_tokens"] + df["output_tokens"])
            .groupby(["month", group_by], as_index=False)["total_tokens"]
            .sum()
        )
        return (
            alt.Chart(chart_data)
            .mark_area(opacity=0.78)
            .encode(
                x=alt.X("yearmonth(month):T", title="Month"),
                y=alt.Y("sum(total_tokens):Q", title="Tokens"),
                color=alt.Color(f"{group_by}:N", title=group_by.replace("_", " ").title()),
                tooltip=[
                    alt.Tooltip("yearmonth(month):T", title="Month"),
                    alt.Tooltip(f"{group_by}:N", title=group_by.replace("_", " ").title()),
                    alt.Tooltip("sum(total_tokens):Q", title="Tokens", format=",.0f"),
                ],
            )
            .properties(height=height)
            .interactive()
        )

    chart_data = (
        df.groupby(["month", group_by], as_index=False)
        .agg(input_tokens=("input_tokens", "sum"), output_tokens=("output_tokens", "sum"))
        .melt(
            id_vars=["month", group_by],
            value_vars=["input_tokens", "output_tokens"],
            var_name="token_type",
            value_name="tokens",
        )
    )
    chart_data["token_type"] = chart_data["token_type"].str.replace("_", " ").str.title()
    chart_data["series"] = chart_data[group_by] + " - " + chart_data["token_type"]
    return (
        alt.Chart(chart_data[chart_data["tokens"] > 0])
        .mark_line(point=True)
        .encode(
            x=alt.X("yearmonth(month):T", title="Month"),
            y=alt.Y("sum(tokens):Q", title="Tokens"),
            color=alt.Color("series:N", title="Series"),
            tooltip=[
                alt.Tooltip("yearmonth(month):T", title="Month"),
                alt.Tooltip(f"{group_by}:N", title=group_by.replace("_", " ").title()),
                alt.Tooltip("token_type:N", title="Token type"),
                alt.Tooltip("sum(tokens):Q", title="Tokens", format=",.0f"),
            ],
        )
        .properties(height=height)
        .interactive()
    )


def seat_utilization_chart(df: pd.DataFrame, threshold: float = 0.82, show_inactive: bool = False, height: int = 300) -> alt.Chart:
    chart_data = (
        df[df["seats"] > 0]
        .groupby(["month", "vendor"], as_index=False)
        .agg(seats=("seats", "sum"), active_users=("active_users", "sum"))
    )
    chart_data["utilization_rate"] = chart_data["active_users"] / chart_data["seats"].clip(lower=1)
    chart_data["inactive_seats"] = (chart_data["seats"] - chart_data["active_users"]).clip(lower=0)

    y_column = "inactive_seats" if show_inactive else "utilization_rate"
    y_title = "Inactive seats" if show_inactive else "Utilization"
    y_axis = alt.Axis(format="%") if not show_inactive else alt.Axis(format=",.0f")

    chart = (
        alt.Chart(chart_data)
        .mark_line(point=True)
        .encode(
            x=alt.X("yearmonth(month):T", title="Month"),
            y=alt.Y(f"{y_column}:Q", title=y_title, axis=y_axis),
            color=alt.Color("vendor:N", title="Vendor"),
            tooltip=[
                alt.Tooltip("yearmonth(month):T", title="Month"),
                alt.Tooltip("vendor:N", title="Vendor"),
                alt.Tooltip("seats:Q", title="Paid seats", format=",.0f"),
                alt.Tooltip("active_users:Q", title="Active users", format=",.0f"),
                alt.Tooltip("inactive_seats:Q", title="Inactive seats", format=",.0f"),
                alt.Tooltip("utilization_rate:Q", title="Utilization", format=".0%"),
            ],
        )
        .properties(height=height)
        .interactive()
    )

    if show_inactive:
        return chart

    target_line = (
        alt.Chart(pd.DataFrame({"target": [threshold]}))
        .mark_rule(color="#b87316", strokeDash=[6, 6])
        .encode(y="target:Q")
    )
    return chart + target_line


def cost_model_chart(df: pd.DataFrame, height: int = 300) -> alt.Chart:
    chart_data = df.groupby("cost_model", as_index=False)["spend"].sum()
    return (
        alt.Chart(chart_data)
        .mark_arc(innerRadius=70)
        .encode(
            theta=alt.Theta("spend:Q"),
            color=alt.Color("cost_model:N", title="Cost model"),
            tooltip=[
                alt.Tooltip("cost_model:N", title="Cost model"),
                alt.Tooltip("spend:Q", title="Spend", format="$,.0f"),
            ],
        )
        .properties(height=height)
    )


def team_spend_chart(df: pd.DataFrame, top_n: int = 8, height: int = 300) -> alt.Chart:
    chart_data = df.groupby("team", as_index=False)["spend"].sum().sort_values("spend", ascending=False).head(top_n)
    return (
        alt.Chart(chart_data)
        .mark_bar()
        .encode(
            x=alt.X("spend:Q", title="Spend"),
            y=alt.Y("team:N", title="Team", sort="-x"),
            color=alt.value("#1f8a5b"),
            tooltip=[
                alt.Tooltip("team:N", title="Team"),
                alt.Tooltip("spend:Q", title="Spend", format="$,.0f"),
            ],
        )
        .properties(height=height)
        .interactive()
    )


def savings_opportunities_chart(height: int = 300) -> alt.Chart:
    return (
        alt.Chart(savings_opportunities_data())
        .mark_bar()
        .encode(
            x=alt.X("monthly_savings:Q", title="Estimated monthly savings"),
            y=alt.Y("category:N", title="Category", sort="-x"),
            color=alt.value("#1f8a5b"),
            tooltip=[
                alt.Tooltip("category:N", title="Category"),
                alt.Tooltip("monthly_savings:Q", title="Monthly savings", format="$,.0f"),
            ],
        )
        .properties(height=height)
        .interactive()
    )


def render_main_charts(df: pd.DataFrame) -> None:
    st.subheader("Core dashboard")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Monthly AI spend by vendor**")
        st.altair_chart(spend_chart(df, height=280), use_container_width=True)
    with c2:
        st.markdown("**Budget burn rate by month**")
        st.altair_chart(budget_burn_chart(df, height=280), use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown("**Cost per 1K actions by vendor**")
        st.altair_chart(efficiency_chart(df, height=280), use_container_width=True)
    with c4:
        st.markdown("**Seat utilization by vendor**")
        if df[df["seats"] > 0].empty:
            st.info("No seat-based usage found in the selected data.")
        else:
            st.altair_chart(seat_utilization_chart(df, height=280), use_container_width=True)


def render_graph_focus(df: pd.DataFrame) -> None:
    st.subheader("Explore a graph")
    st.caption("Choose one chart to inspect in detail with dedicated controls and context.")

    graph = st.selectbox(
        "Choose graph",
        [
            "Monthly AI spend",
            "Budget burn rate",
            "Cost per 1K usage",
            "Token usage",
            "Seat utilization",
            "Spend by cost model",
            "Top teams by spend",
            "Savings opportunities",
        ],
    )

    if graph == "Monthly AI spend":
        st.caption(
            "Shows how AI spend changes over time and where cost growth is concentrated. "
            "Use it to spot vendor concentration, budget pressure, and negotiation opportunities."
        )
        c1, c2, c3 = st.columns(3)
        breakdown = c1.selectbox("Break down by", ["vendor", "team", "cost_model", "model"], key="focus_spend_breakdown")
        display = c2.selectbox("Display", ["Stacked bars", "Trend lines"], key="focus_spend_display")
        show_budget = c3.checkbox("Show budget line", value=True, key="focus_spend_budget")
        st.altair_chart(
            spend_chart(df, breakdown=breakdown, display=display, show_budget=show_budget, height=520),
            use_container_width=True,
        )

    elif graph == "Budget burn rate":
        st.caption(
            "Compares monthly AI spend against a budget and an alert threshold. "
            "Use it to decide when spending needs approval, investigation, or a revised forecast."
        )
        c1, c2 = st.columns(2)
        budget = c1.slider("Monthly budget", 25_000, 250_000, BUDGET, step=5_000)
        threshold = c2.slider("Alert threshold (%)", 50, 100, 85, step=5) / 100
        st.altair_chart(budget_burn_chart(df, budget=budget, threshold=threshold, height=520), use_container_width=True)

    elif graph == "Cost per 1K usage":
        st.caption(
            "Normalizes spend by usage volume so expensive vendors or inefficient workloads stand out. "
            "Use it to separate healthy adoption from waste."
        )
        c1, c2, c3 = st.columns(3)
        group_by = c1.selectbox("Compare by", ["vendor", "team", "model", "use_case"], key="focus_efficiency_group")
        basis = c2.selectbox("Usage basis", ["Actions", "Tokens"], key="focus_efficiency_basis")
        top_n = c3.slider("Top N", 3, 15, 8, key="focus_efficiency_top")
        st.altair_chart(efficiency_chart(df, group_by=group_by, basis=basis, top_n=top_n, height=520), use_container_width=True)

    elif graph == "Token usage":
        st.caption(
            "Shows LLM token consumption patterns. "
            "Use it to find prompt bloat, output-heavy workflows, and candidates for prompt compression."
        )
        c1, c2 = st.columns(2)
        group_by = c1.selectbox("Group by", ["vendor", "model", "team", "use_case"], key="focus_tokens_group")
        token_view = c2.selectbox("Token view", ["Input vs output", "Total tokens"], key="focus_tokens_view")
        st.altair_chart(token_usage_chart(df, group_by=group_by, token_view=token_view, height=260), use_container_width=True)

    elif graph == "Seat utilization":
        st.caption(
            "Compares paid seats with active users for AI coding tools and SaaS platforms. "
            "Use it to reclaim unused licenses and create approval rules for seat growth."
        )
        if df[df["seats"] > 0].empty:
            st.info("No seat-based usage found in the selected data.")
        else:
            c1, c2 = st.columns(2)
            threshold = c1.slider("Utilization target (%)", 50, 100, 82, step=2) / 100
            show_inactive = c2.checkbox("Show inactive seats instead of utilization", key="focus_seats_inactive")
            st.altair_chart(
                seat_utilization_chart(df, threshold=threshold, show_inactive=show_inactive, height=520),
                use_container_width=True,
            )

    elif graph == "Spend by cost model":
        st.caption(
            "Breaks AI spend into token-based, seat-based, and usage-based models. "
            "Use it to understand whether optimization should focus on prompts, licenses, or vendor contracts."
        )
        st.altair_chart(cost_model_chart(df, height=520), use_container_width=True)

    elif graph == "Top teams by spend":
        st.caption(
            "Ranks business and engineering owners by AI spend. "
            "Use it to drive budget conversations with the teams that can actually change usage behavior."
        )
        top_n = st.slider("Top N teams", 3, 15, 8, key="focus_team_top")
        st.altair_chart(team_spend_chart(df, top_n=top_n, height=520), use_container_width=True)

    else:
        st.caption(
            "Estimates monthly savings by optimization category. "
            "Use it to prioritize work that has both financial impact and clear operational ownership."
        )
        st.altair_chart(savings_opportunities_chart(height=520), use_container_width=True)


def render_risks(df: pd.DataFrame) -> None:
    st.subheader("Usage risks requiring action")
    risks = detect_anomalies(df)

    if risks.empty:
        st.success("No current risks matched the anomaly rules.")
        return

    display = risks.copy()
    display["estimated_impact"] = display["estimated_impact"].map(money)
    st.dataframe(display, use_container_width=True, hide_index=True)


def render_recommendations() -> None:
    st.subheader("Optimization backlog")
    for item in RECOMMENDATIONS:
        with st.container(border=True):
            col1, col2 = st.columns((4, 1))
            col1.markdown(f"**{item.title}**")
            col1.caption(f"{item.owner} - {item.rationale}")
            col2.metric("Savings", money(item.savings))


def render_governance() -> None:
    st.subheader("Governance guardrails")
    policies = pd.DataFrame(
        [
            {
                "domain": "LLM APIs",
                "policy": "Require use-case tags and budget owner metadata",
                "enforcement": "Reject untagged requests at gateway after grace period",
            },
            {
                "domain": "Seat-based AI tools",
                "policy": "Review inactive seats after 21 days",
                "enforcement": "Downgrade, reclaim, or require manager approval",
            },
            {
                "domain": "Model selection",
                "policy": "Route low-risk workloads to cheaper default models",
                "enforcement": "Policy-driven routing by task category",
            },
            {
                "domain": "Procurement",
                "policy": "Benchmark vendor pricing before renewals",
                "enforcement": "Use utilization and unit-cost data in negotiation",
            },
        ]
    )
    st.dataframe(policies, use_container_width=True, hide_index=True)


def render_raw_data(df: pd.DataFrame) -> None:
    with st.expander("Raw normalized data"):
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download filtered data",
            df.to_csv(index=False).encode("utf-8"),
            file_name="ai_finops_filtered_data.csv",
            mime="text/csv",
        )


def main() -> None:
    st.title("AI FinOps Command Center")
    st.caption("Cost visibility, forecasting, governance, and optimization for AI vendors and platforms.")

    with st.sidebar:
        st.markdown("### Data upload")
        uploaded_file = st.file_uploader("Upload AI usage CSV", type=["csv"])
        st.download_button(
            "Download CSV template",
            SAMPLE_CSV.encode("utf-8"),
            file_name="ai_finops_template.csv",
            mime="text/csv",
        )
        st.caption(
            "Required columns: date, vendor, team, cost_model, spend, actions. "
            "Optional: model, service, owner, use_case, tokens, seats, active_users."
        )

    df = load_data(uploaded_file)
    filtered = filter_data(df)

    if filtered.empty:
        st.warning("No rows match the selected filters.")
        st.stop()

    render_kpis(filtered)
    st.divider()
    render_main_charts(filtered)
    st.divider()
    render_graph_focus(filtered)
    st.divider()

    risk_col, recommendation_col = st.columns((1.35, 1))
    with risk_col:
        render_risks(filtered)
    with recommendation_col:
        render_recommendations()

    st.divider()
    render_governance()
    render_raw_data(filtered)


if __name__ == "__main__":
    main()
