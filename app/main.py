import streamlit as st
from ui.home import init_state, main_content
from ui.instruction import instruction_page
from core.config import settings

st.set_page_config(page_title=settings.DEMO_WEB_PAGE_TITLE, page_icon="🤖", layout="wide")

page = st.sidebar.selectbox("Choose a page", ["KnowBot", "How to Use"])

def app_page():
    init_state()
    st.title(settings.DEMO_WEB_PAGE_TITLE) 
    main_content()

if page == "KnowBot":
    app_page()
else:
    instruction_page()