import streamlit as st

def instruction_page():
    st.title("📚 How to Use KnowBot")
    st.caption("Your calm and capable AI assistant for exploring academic papers in a thoughtful way.")

    st.subheader("🧭 Quick Start Guide")

    # --- Step 1 ---
    st.warning("""#### ① Enter Your Question  
> Please type a clear and concise question to begin.  
> *e.g.,* `How does LangGraph work?`
""")

    # --- Step 2 ---
    st.warning("""#### ② Select Reference Documents  
> Kindly browse the **Source** section.  
> Click **“Add to Ref”** on papers that seem helpful.  
> *e.g.,* Select *“LangGraph Architecture Overview”*
""")

    # --- Step 3 ---
    st.warning("""#### ③ Ask and Receive Answers  
> Press the **Ask** button.  
> KnowBot will respond based on your chosen references,  
> including citations and related follow-up questions.
""")

    # --- Step 4 ---
    st.warning("""#### ④ Explore Follow-up Questions  
> Click any suggested question to continue learning  
> without typing again.
""")

    # --- Tips ---
    st.markdown("---")
    st.markdown("### 🧾 Tips for Best Experience")
    st.markdown("""
- Uses semantic vector search to find related content.  
- Answers are strictly based on selected references.  
- You may update your references to refine the results anytime.
""")

    # --- Help Section ---
    st.markdown("---")
    st.subheader("💬 Need Help?")
    st.caption("We’re here to help. Contact us via:")
    st.markdown("[GitHub Issues](https://github.com/stephanie0324/KnowBot/issues) or leave feedback in the app.")
