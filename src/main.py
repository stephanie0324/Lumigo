import streamlit as st
from ui.home import main_content
from ui.instruction import instruction_page
from core.config import settings

def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(page_title=settings.DEMO_WEB_PAGE_TITLE, page_icon="🤖", layout="wide")

    PAGES = {
        "Lumigo": main_content,
        "How to Use": instruction_page,
    }

    st.sidebar.title("Navigation")
    selection = st.sidebar.radio("Choose a page", list(PAGES.keys()))

    page_function = PAGES[selection]
    page_function()

if __name__ == "__main__":
    main()
