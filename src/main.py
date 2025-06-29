import streamlit as st
from ui.home import main_content
from ui.instruction import instruction_page
from ui.analytics import analytics_page
from core.config import settings

st.set_page_config(page_title=settings.DEMO_WEB_PAGE_TITLE, page_icon="🤖", layout="wide")

page = st.sidebar.selectbox("Choose a page", ["Lumigo", "What's New", "How to Use"])

if page == "Lumigo":
    st.title(settings.DEMO_WEB_PAGE_TITLE) 
    main_content()
elif page == "How to Use":
    instruction_page()
elif page == "What's New":
    analytics_page()
