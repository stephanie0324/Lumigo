import streamlit as st


def instruction_page():

    # --- Global Styles ---
    st.markdown("""
        <style>
            html, body, [class*="css"] {
                font-family: 'Helvetica Neue', sans-serif;
            }

            .title-shadow {
                text-align: center;
                font-size: 2.8rem;
                font-weight: 800;
                color: #222;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
                margin-bottom: 0.2rem;
            }

            .subtitle {
                text-align: center;
                font-size: 1.1rem;
                color: #666;
                margin-bottom: 2.5rem;
            }

            .quote-slider-wrapper {
                position: relative;
                width: 85%;
                max-width: 1000px;
                margin: 2rem auto;
                height: 160px;
                background: rgba(255, 249, 220, 0.5);
                border-radius: 12px;
                box-shadow: 0 6px 20px rgba(255, 223, 93, 0.2);
                overflow: hidden;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .quote-track {
                display: flex;
                width: 500%;
                animation: slideQuotes 30s ease-in-out infinite;
            }

            .quote-card {
                flex: 0 0 100%;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 1rem 2rem;
                box-sizing: border-box;
                text-align: center;
                color: #5a4a00;
                font-style: italic;
                font-size: 1.4rem;
                position: relative;
            }

            .quote-card::before {
                content: "“";
                font-size: 3.5rem;
                position: absolute;
                left: -1rem;
                top: -0.5rem;
                color: #f7d65a;
                font-family: serif;
            }

            .quote-card::after {
                content: "”";
                font-size: 3.5rem;
                position: absolute;
                right: -1rem;
                bottom: -0.5rem;
                color: #f7d65a;
                font-family: serif;
            }

            .quote-author {
                font-size: 1rem;
                font-weight: 600;
                color: #7a6f00;
                margin-top: 0.6rem;
                font-family: Arial, sans-serif;
            }

            @keyframes slideQuotes {
                0%, 10%     { transform: translateX(0); }
                20%, 30%    { transform: translateX(-100%); }
                40%, 50%    { transform: translateX(-200%); }
                60%, 70%    { transform: translateX(-300%); }
                80%, 90%    { transform: translateX(-400%); }
                100%        { transform: translateX(0); }
            }

            .step-block {
                display: flex;
                align-items: center;
                gap: 1.2rem;
                max-width: 680px;
                margin: 0 auto 1.2rem auto;
                background: #fefefe;
                padding: 1rem 1.2rem;
                border-radius: 12px;
                box-shadow: 0 1px 5px rgba(0,0,0,0.03);
            }

            .step-icon {
                width: 38px;
                height: 38px;
                background: #FFE66D;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                color: #222;
                font-size: 16px;
                box-shadow: 0 1px 4px rgba(0,0,0,0.1);
            }

            .step-text h4 {
                margin: 0 0 4px 0;
                font-size: 19px;
                color: #222;
            }

            .step-text p {
                margin: 0;
                font-size: 16px;
                color: #444;
            }
        </style>
    """, unsafe_allow_html=True)

    # --- Hero Section ---
    st.markdown('<div class="title-shadow">📘 Welcome to Lumigo</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Your calm, intelligent assistant for navigating academic papers</div>', unsafe_allow_html=True)

    # --- Quote Slider ---
    st.markdown("""
        <div class="quote-slider-wrapper" aria-label="Lumigo Feature Quotes">
            <div class="quote-track">
                <div class="quote-card">
                    Semantic Paper Search for precise results.
                    <div class="quote-author">— 💡 Feature</div>
                </div>
                <div class="quote-card">
                    RAG-Based Smart Answers with real-time reasoning.
                    <div class="quote-author">— 🧠 Feature</div>
                </div>
                <div class="quote-card">
                    Custom Reference Selection to control your context.
                    <div class="quote-author">— 📚 Feature</div>
                </div>
                <div class="quote-card">
                    Instant Markdown Summaries for easy capture.
                    <div class="quote-author">— ✍️ Feature</div>
                </div>
                <div class="quote-card">
                    Multi-Agent Reasoning Pipeline for deeper thinking.
                    <div class="quote-author">— 🚀 Feature</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- Step-by-Step Guide ---
    st.markdown("""
        <div style='text-align:center; padding-top: 2rem; padding-bottom: 1rem;'>
            <h2 style="color: #222">🪄 How to Use Lumigo</h2>
            <p style="color: #666; font-size: 15px;">Follow this simple process to explore deeply and clearly.</p>
        </div>
    """, unsafe_allow_html=True)

    steps = [
        ("1", "Ask a Question", "Type something like: What is LangGraph used for?"),
        ("2", "Add Reference Docs", "Click ➕ next to useful documents in the Source tab."),
        ("3", "Submit Your Query", "Lumigo reads and answers using selected references."),
        ("4", "Explore Follow-ups", "Click any follow-up to go deeper — no retyping needed.")
    ]

    for icon, title, desc in steps:
        st.markdown(f"""
            <div class="step-block">
                <div class="step-icon">{icon}</div>
                <div class="step-text">
                    <h4>{title}</h4>
                    <p>{desc}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # --- Footer ---
    st.markdown("""
        <hr style="margin-top:2rem; margin-bottom:1.2rem;"/>
        <div style="text-align:center; padding-top:1rem;">
            <h4>Need Help or Feedback?</h4>
            <p style="font-size:14px;">
                Submit an issue on 
                <a href="https://github.com/stephanie0324/Lumigo/issues" target="_blank">GitHub</a> 
                or leave feedback directly in the app.
            </p>
        </div>
    """, unsafe_allow_html=True)
