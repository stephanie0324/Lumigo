import streamlit as st
import pandas as pd
from utils.db_utils import get_query_analytics, get_total_query_count
from datetime import datetime, timedelta


def analytics_page():
    """Render the analytics page to display query analytics."""
    st.header("📊 Query Analytics Dashboard")
    st.markdown("Explore the most popular search topics and documents based on user queries.")

    # Fetch analytics data
    top_tags, top_titles = get_query_analytics(top_k=10)
    # --- Filters in Sidebar ---
    st.sidebar.subheader("Filter Analytics Data")

    col1, col2 = st.columns(2)
    today = datetime.now().date()
    default_start_date = today - timedelta(days=30) # Default to last 30 days

    with col1:
        st.subheader("Top Searched Topics")
        if top_tags:
            tags_df = pd.DataFrame(top_tags)
            tags_df.index = tags_df.index + 1
            st.dataframe(tags_df, use_container_width=True)
        else:
            st.info("No topic data available yet.")
        selected_start_date = st.sidebar.date_input("Start Date", value=default_start_date)
        selected_end_date = st.sidebar.date_input("End Date", value=today)

    with col2:
        st.subheader("Top Searched Documents")
        if top_titles:
            titles_df = pd.DataFrame(top_titles)
            titles_df.index = titles_df.index + 1
            st.dataframe(titles_df, use_container_width=True)
        else:
            st.info("No document search data available yet.")
        if selected_start_date > selected_end_date:
            st.sidebar.error("Error: End date must be after start date.")
            return

    # Optional: Add bar charts for visualization
    st.markdown("---")
    top_k_value = st.sidebar.slider("Number of Top Items to Show", min_value=5, max_value=50, value=10, step=5)

    if top_tags:
        st.subheader("Top Topics Visualization")
        tags_chart_df = pd.DataFrame(top_tags).set_index('topic')
        st.bar_chart(tags_chart_df)

        # Fetch analytics data based on filters
        top_tags, top_titles = get_query_analytics(
            top_k=top_k_value,
            start_date=selected_start_date,
            end_date=selected_end_date
        )
        total_queries = get_total_query_count(
            start_date=selected_start_date,
            end_date=selected_end_date
        )

        # --- Display Metrics ---
        st.markdown("---")
        col_total, col_unique_topics, col_unique_docs = st.columns(3)

        with col_total:
            st.metric(label="Total Queries", value=total_queries)
        with col_unique_topics:
            st.metric(label="Unique Topics", value=len(top_tags))
        with col_unique_docs:
            st.metric(label="Unique Documents", value=len(top_titles))

        st.info(f"Data last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.markdown("---")

        # --- Display Top Topics and Documents ---
        col1, col2 = st.columns(2)

        with col1:
            st.subheader(f"Top {top_k_value} Searched Topics")
            if top_tags:
                tags_df = pd.DataFrame(top_tags)
                tags_df.index = tags_df.index + 1
                st.dataframe(tags_df, use_container_width=True)
            else:
                st.info("No topic data available for the selected period.")

        with col2:
            st.subheader(f"Top {top_k_value} Searched Documents")
            if top_titles:
                titles_df = pd.DataFrame(top_titles)
                titles_df.index = titles_df.index + 1
                st.dataframe(titles_df, use_container_width=True)
            else:
                st.info("No document search data available for the selected period.")

        # --- Optional: Add bar charts for visualization ---
        st.markdown("---")

        if top_tags:
            st.subheader("Top Topics Visualization")
            tags_chart_df = pd.DataFrame(top_tags).set_index('topic')
            st.bar_chart(tags_chart_df)
        else:
            st.info("No topic data to visualize.")

        if top_titles:
            st.subheader("Top Documents Visualization")
            titles_chart_df = pd.DataFrame(top_titles).set_index('title')
            st.bar_chart(titles_chart_df)
        else:
            st.info("No document data to visualize.")

