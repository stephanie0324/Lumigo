import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.db_utils import get_query_analytics, get_total_query_count, get_tag_trend_data

def analytics_page():
    st.header("📊 Query Analytics Dashboard")
    st.markdown("Explore the most popular search topics and documents based on user queries.")

    # Date range filter
    st.sidebar.subheader("Filter Analytics Data")
    today = datetime.now().date()
    default_start_date = today - timedelta(days=30)

    selected_start_date = st.sidebar.date_input("Start Date", value=default_start_date)
    selected_end_date = st.sidebar.date_input("End Date", value=today)
    if selected_start_date > selected_end_date:
        st.sidebar.error("Error: End date must be after start date.")
        return

    # Single top_k slider controls all top-k displays
    top_k = st.sidebar.slider("Number of Top Items to Show (Topics & Documents)", 1, 10, 10, step=1)

    # Cumulative stats (independent of top_k)
    total_queries = get_total_query_count(start_date=selected_start_date, end_date=selected_end_date)
    all_tags, all_titles = get_query_analytics(top_k=1000, start_date=selected_start_date, end_date=selected_end_date)
    unique_tags_count = len({tag['topic'] for tag in all_tags})
    unique_titles_count = len({title['title'] for title in all_titles})

    col_queries, col_topics, col_documents = st.columns(3)
    col_queries.metric("Total Queries", total_queries)
    col_topics.metric("Unique Topics (all-time)", unique_tags_count)
    col_documents.metric("Unique Documents (all-time)", unique_titles_count)

    st.markdown("---")

    # Fetch and show trend data for top_k topics
    trend_records = get_tag_trend_data(
        start_date=selected_start_date,
        end_date=selected_end_date,
        top_k=top_k
    )

    if trend_records:
        df_trend = pd.DataFrame(trend_records)
        df_trend["date"] = pd.to_datetime(df_trend["date"]).dt.date
        pivot_df = df_trend.pivot_table(
            index="date",
            columns="tag",
            values="count",
            aggfunc="sum",
            fill_value=0,
        ).sort_index()
        pivot_df.index = pivot_df.index.astype(str)
        st.subheader("📈 Top Topics Trends Over Time")
        st.line_chart(pivot_df)
    else:
        st.info("No trend data available for the selected range.")

    st.markdown("---")

    # Show top topics and documents tables, limited by the same top_k
    top_tags, top_titles = get_query_analytics(
        top_k=top_k,
        start_date=selected_start_date,
        end_date=selected_end_date
    )

    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"Top {top_k} Searched Topics")
        if top_tags:
            tags_df = pd.DataFrame(top_tags)
            tags_df.index = tags_df.index + 1
            st.dataframe(tags_df, use_container_width=True)
        else:
            st.info("No topic data available for the selected period.")

    with col2:
        st.subheader(f"Top {top_k} Searched Documents")
        if top_titles:
            titles_df = pd.DataFrame(top_titles)
            titles_df.index = titles_df.index + 1
            st.dataframe(titles_df, use_container_width=True)
        else:
            st.info("No document data available for the selected period.")
