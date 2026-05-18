# ============================================================
# Twitter Brand Intelligence Pipeline
# Phase 6: Streamlit Dashboard
# Author: Sinazo Dyubele
#
# SETUP:
# pip install streamlit plotly pandas
# Run: streamlit run phase6_dashboard.py
# ============================================================

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# CONFIG
# ============================================================

DB_PATH = "brand_intelligence.db"

st.set_page_config(
    page_title="Brand Intelligence Dashboard",
    page_icon="📊",
    layout="wide"
)

# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    tweets  = pd.read_sql("SELECT * FROM tweets",        conn)
    brands  = pd.read_sql("SELECT * FROM brand_summary", conn)
    topics  = pd.read_sql("SELECT * FROM topic_reference", conn)
    conn.close()
    return tweets, brands, topics

tweets, brands, topics = load_data()

# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.title("🔍 Filters")

# Brand filter
all_brands = sorted(tweets["author_id"].dropna().unique().tolist())
selected_brands = st.sidebar.multiselect(
    "Filter by Brand",
    options=all_brands,
    default=["AmazonHelp", "AppleSupport", "Uber_Support", "Delta", "SpotifyCares"]
)

# Sentiment filter
sentiment_filter = st.sidebar.multiselect(
    "Filter by Sentiment",
    options=["positive", "neutral", "negative"],
    default=["positive", "neutral", "negative"]
)

# Tweet type filter
tweet_types = tweets["tweet_type"].dropna().unique().tolist()
type_filter = st.sidebar.multiselect(
    "Filter by Tweet Type",
    options=tweet_types,
    default=tweet_types
)

# Apply filters
mask = (
    tweets["author_id"].isin(selected_brands) &
    tweets["sentiment_label"].isin(sentiment_filter) &
    tweets["tweet_type"].isin(type_filter)
)
filtered = tweets[mask]

# ============================================================
# HEADER
# ============================================================

st.title("📊 Twitter Brand Intelligence Dashboard")
st.markdown("*Analysing customer support communication patterns across major brands*")
st.divider()

# ============================================================
# KPI METRICS ROW
# ============================================================

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Total Tweets",     f"{len(filtered):,}")
k2.metric("Brands Selected",  f"{filtered['author_id'].nunique()}")
k3.metric("Avg Sentiment",    f"{filtered['sentiment_score'].mean():.3f}")
k4.metric("Positive Tweets",  f"{(filtered['sentiment_label']=='positive').sum():,}")
k5.metric("Negative Tweets",  f"{(filtered['sentiment_label']=='negative').sum():,}")

st.divider()

# ============================================================
# ROW 1: SENTIMENT & INTENT
# ============================================================

col1, col2 = st.columns(2)

with col1:
    st.subheader("😊 Sentiment Distribution")
    sent_counts = filtered["sentiment_label"].value_counts().reset_index()
    sent_counts.columns = ["Sentiment", "Count"]
    color_map = {"positive": "#2ecc71", "neutral": "#95a5a6", "negative": "#e74c3c"}
    fig = px.pie(
        sent_counts, values="Count", names="Sentiment",
        color="Sentiment", color_discrete_map=color_map,
        hole=0.4
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(showlegend=False, margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("🎯 Intent Distribution")
    intent_counts = filtered["intent"].value_counts().reset_index()
    intent_counts.columns = ["Intent", "Count"]
    fig2 = px.bar(
        intent_counts, x="Count", y="Intent",
        orientation="h", color="Count",
        color_continuous_scale="Blues",
        text="Count"
    )
    fig2.update_traces(textposition="outside")
    fig2.update_layout(
        margin=dict(t=20, b=20),
        yaxis=dict(categoryorder="total ascending"),
        coloraxis_showscale=False
    )
    st.plotly_chart(fig2, use_container_width=True)

# ============================================================
# ROW 2: BRAND COMPARISON
# ============================================================

st.subheader("🏢 Brand Sentiment Comparison")

brand_filtered = brands[brands["author_id"].isin(selected_brands)].copy()

if not brand_filtered.empty:
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        name="Positive %",
        x=brand_filtered["author_id"],
        y=brand_filtered["pct_positive"].round(1),
        marker_color="#2ecc71",
        text=brand_filtered["pct_positive"].round(1),
        texttemplate="%{text}%", textposition="inside"
    ))
    fig3.add_trace(go.Bar(
        name="Neutral %",
        x=brand_filtered["author_id"],
        y=brand_filtered["pct_neutral"].round(1),
        marker_color="#95a5a6",
        text=brand_filtered["pct_neutral"].round(1),
        texttemplate="%{text}%", textposition="inside"
    ))
    fig3.add_trace(go.Bar(
        name="Negative %",
        x=brand_filtered["author_id"],
        y=brand_filtered["pct_negative"].round(1),
        marker_color="#e74c3c",
        text=brand_filtered["pct_negative"].round(1),
        texttemplate="%{text}%", textposition="inside"
    ))
    fig3.update_layout(
        barmode="stack",
        xaxis_title="Brand",
        yaxis_title="Percentage (%)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=40, b=20)
    )
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("No brand data for selected filters.")

# ============================================================
# ROW 3: HOURLY ACTIVITY & TOPIC BREAKDOWN
# ============================================================

col3, col4 = st.columns(2)

with col3:
    st.subheader("⏰ Hourly Tweet Activity")
    hourly = filtered.groupby("hour").agg(
        tweet_count    = ("tweet_id",        "count"),
        avg_sentiment  = ("sentiment_score", "mean")
    ).reset_index()

    fig4 = go.Figure()
    fig4.add_trace(go.Bar(
        x=hourly["hour"], y=hourly["tweet_count"],
        name="Tweet Count", marker_color="#3498db", opacity=0.7
    ))
    fig4.add_trace(go.Scatter(
        x=hourly["hour"], y=hourly["avg_sentiment"] * 1000,
        name="Avg Sentiment (×1000)", mode="lines+markers",
        line=dict(color="#e67e22", width=2),
        yaxis="y2"
    ))
    fig4.update_layout(
        xaxis_title="Hour of Day",
        yaxis_title="Tweet Count",
        yaxis2=dict(title="Avg Sentiment", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=40, b=20)
    )
    st.plotly_chart(fig4, use_container_width=True)

with col4:
    st.subheader("🗂️ Topic Distribution")
    fig5 = px.bar(
        topics.sort_values("tweet_count", ascending=True),
        x="tweet_count", y="topic_label",
        orientation="h",
        color="avg_sentiment",
        color_continuous_scale="RdYlGn",
        text="tweet_count",
        labels={"tweet_count": "Tweets", "avg_sentiment": "Avg Sentiment"}
    )
    fig5.update_traces(textposition="outside")
    fig5.update_layout(
        margin=dict(t=20, b=20),
        coloraxis_colorbar=dict(title="Sentiment")
    )
    st.plotly_chart(fig5, use_container_width=True)

# ============================================================
# ROW 4: DAY OF WEEK & TWEET TYPE
# ============================================================

col5, col6 = st.columns(2)

with col5:
    st.subheader("📅 Activity by Day of Week")
    day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    day_data  = filtered.groupby("day_of_week").agg(
        tweet_count   = ("tweet_id",        "count"),
        avg_sentiment = ("sentiment_score", "mean")
    ).reindex(day_order).reset_index()

    fig6 = px.bar(
        day_data, x="day_of_week", y="tweet_count",
        color="avg_sentiment", color_continuous_scale="RdYlGn",
        text="tweet_count",
        labels={"day_of_week": "Day", "tweet_count": "Tweets"}
    )
    fig6.update_traces(textposition="outside")
    fig6.update_layout(margin=dict(t=20, b=20))
    st.plotly_chart(fig6, use_container_width=True)

with col6:
    st.subheader("📨 Tweet Type Breakdown")
    type_data = filtered["tweet_type"].value_counts().reset_index()
    type_data.columns = ["Tweet Type", "Count"]
    color_map2 = {
        "brand_reply":        "#3498db",
        "brand_post":         "#2980b9",
        "customer_mention":   "#e67e22",
        "customer_reply":     "#e74c3c"
    }
    fig7 = px.pie(
        type_data, values="Count", names="Tweet Type",
        color="Tweet Type", color_discrete_map=color_map2,
        hole=0.4
    )
    fig7.update_traces(textposition="inside", textinfo="percent+label")
    fig7.update_layout(showlegend=False, margin=dict(t=20, b=20))
    st.plotly_chart(fig7, use_container_width=True)

# ============================================================
# ROW 5: BRAND SUMMARY TABLE
# ============================================================

st.subheader("📋 Brand Summary Table")

display_brands = brands[brands["author_id"].isin(selected_brands)][
    ["author_id", "total_tweets", "avg_sentiment",
     "pct_positive", "pct_negative", "most_common_intent",
     "most_active_hour", "most_active_day", "top_keywords"]
].copy()

display_brands.columns = [
    "Brand", "Tweets", "Avg Sentiment",
    "% Positive", "% Negative", "Top Intent",
    "Peak Hour", "Peak Day", "Top Keywords"
]

display_brands["Avg Sentiment"] = display_brands["Avg Sentiment"].round(3)
display_brands["% Positive"]    = display_brands["% Positive"].round(1)
display_brands["% Negative"]    = display_brands["% Negative"].round(1)

st.dataframe(
    display_brands.sort_values("Avg Sentiment", ascending=False),
    use_container_width=True,
    hide_index=True
)

# ============================================================
# ROW 6: TWEET EXPLORER
# ============================================================

st.subheader("🔎 Tweet Explorer")
st.markdown("Browse individual tweets with their NLP labels")

explore_cols = ["author_id", "tweet_text", "sentiment_label",
                "sentiment_score", "intent", "topic_label", "tweet_type"]
explore_cols = [c for c in explore_cols if c in filtered.columns]

sentiment_explore = st.selectbox(
    "Filter explorer by sentiment:",
    ["All", "positive", "neutral", "negative"]
)

explore_df = filtered[explore_cols].copy()
if sentiment_explore != "All":
    explore_df = explore_df[explore_df["sentiment_label"] == sentiment_explore]

explore_df["sentiment_score"] = explore_df["sentiment_score"].round(3)
st.dataframe(
    explore_df.head(100).reset_index(drop=True),
    use_container_width=True,
    hide_index=True
)

# ============================================================
# FOOTER
# ============================================================

st.divider()
st.markdown(
    "<p style='text-align:center; color:gray; font-size:13px'>"
    "Twitter Brand Intelligence System · Built by Sinazo Dyubele · "
    "Data: Kaggle Customer Support on Twitter Dataset"
    "</p>",
    unsafe_allow_html=True
)
